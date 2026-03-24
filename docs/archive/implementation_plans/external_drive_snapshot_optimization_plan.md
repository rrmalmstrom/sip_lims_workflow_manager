# External Drive Snapshot Performance Optimization Plan

## Problem Summary

**Issue**: Snapshot creation on external drives causes 45+ second delays before script interactive prompts appear.

**Root Cause**: The current [`SnapshotManager.take_complete_snapshot()`](../../src/logic.py:274-346) method creates a complete ZIP archive of the entire project directory synchronously before script execution. On external drives (USB/network), this involves extensive file I/O operations across slow connections.

**Performance Impact**:
- **Local drives**: ~2-5 seconds (acceptable)
- **External drives**: 45+ seconds (blocks user interaction)
- **User experience**: Cannot see script prompts until snapshot completes

## Current Implementation Analysis

### Timing Breakdown (External Drive):
```
Setup time: 0.013s
Snapshot creation time: 45.284s  ← BOTTLENECK
Script start time: 0.350s
Total workflow time: 45.761s
```

### Current Snapshot Process:
1. User clicks "Run Script"
2. **BLOCKS**: Create complete ZIP of entire project directory (45s)
3. Start script execution (0.35s)
4. User finally sees interactive prompts

### Safety Requirement:
- Snapshot **must** complete before script starts
- Enables automatic rollback if script fails
- Preserves exact project state for undo functionality

## Proposed Solution: Incremental Snapshot System

### Core Strategy (Inspired by BorgBackup):
1. **File State Cache**: Track modification time + size for each file
2. **Change Detection**: Compare current files against cached state
3. **Incremental Backup**: Only ZIP files that changed since last snapshot
4. **Complete Rollback**: Combine base + incremental snapshots for restoration

### Technical Implementation:

#### 1. File State Cache Structure:
```json
{
  "last_full_snapshot": "step_id_run_1",
  "cache_timestamp": "2026-01-25T22:31:07.719Z",
  "files": {
    "file1.py": {
      "mtime": 1706234567.123,
      "size": 1024,
      "checksum": "abc123..."
    },
    "data/results.csv": {
      "mtime": 1706234890.456,
      "size": 2048,
      "checksum": "def456..."
    }
  }
}
```

#### 2. Change Detection Algorithm:
```python
def detect_changes(project_path, cache_file):
    """Compare current files against cached state"""
    current_files = scan_directory(project_path)
    cached_state = load_cache(cache_file)
    
    changed_files = []
    for file_path, current_info in current_files.items():
        cached_info = cached_state.get(file_path)
        if not cached_info or file_changed(current_info, cached_info):
            changed_files.append(file_path)
    
    return changed_files

def file_changed(current, cached):
    """BorgBackup-style change detection"""
    return (current['mtime'] != cached['mtime'] or 
            current['size'] != cached['size'])
```

#### 3. Incremental Snapshot Creation:
```python
def take_incremental_snapshot(step_id, changed_files):
    """Create snapshot of only changed files"""
    if len(changed_files) < 10:  # Threshold for incremental
        create_incremental_zip(step_id, changed_files)  # ~2-5s
    else:
        create_full_snapshot(step_id)  # Fall back to full snapshot
```

#### 4. Restoration Strategy:
```python
def restore_from_incremental(step_id):
    """Restore by combining base + incremental snapshots"""
    base_snapshot = find_base_snapshot(step_id)
    incremental_snapshots = find_incremental_snapshots(step_id)
    
    restore_base(base_snapshot)
    for incremental in incremental_snapshots:
        apply_incremental_changes(incremental)
```

### Performance Expectations:

#### Typical Workflow Changes:
- **Modified files**: 2-5 files (scripts modify data files)
- **Incremental snapshot time**: 2-5 seconds (vs 45 seconds)
- **Performance improvement**: 90% reduction in snapshot time

#### Cache Storage:
- **Location**: Local SSD (`~/.sip_lims_cache/`)
- **Size**: ~1-10MB for typical projects
- **Access time**: <0.1 seconds for metadata operations

### Implementation Phases:

#### Phase 1: Core Infrastructure
- [ ] Implement file state cache system
- [ ] Add change detection algorithms
- [ ] Create incremental ZIP functionality

#### Phase 2: Integration
- [ ] Integrate with existing [`SnapshotManager`](../../src/logic.py:93-257)
- [ ] Add fallback to full snapshots when needed
- [ ] Update restoration logic for incremental snapshots

#### Phase 3: Optimization
- [ ] Add smart exclusion patterns (temp files, logs)
- [ ] Implement cache cleanup and maintenance
- [ ] Add performance monitoring and metrics

### Compatibility Considerations:

#### Backward Compatibility:
- Existing full snapshots remain functional
- Gradual migration to incremental system
- Fallback to full snapshots for safety

#### Edge Cases:
- First run: Always create full snapshot
- Cache corruption: Rebuild from scratch
- Large changes: Fall back to full snapshot

## Research Sources

**Context7 Documentation**:
- **fsspec**: File system abstraction with rsync functionality
- **BorgBackup**: Incremental backup strategies using mtime+size comparison
- **File modification tracking**: Using `modified()` and `created()` timestamps

**Key Insights**:
- BorgBackup uses `ctime,size,inode` or `mtime,size,inode` for change detection
- Incremental backups can reduce backup time by 90%+ for typical changes
- File state caching enables fast change detection without full directory scans

## Next Steps

1. **Complete Phase B2/B3 testing** (current priority)
2. **Document as enhancement request** for post-Phase B implementation
3. **Prototype incremental system** in separate branch
4. **Performance testing** with real laboratory projects
5. **Production deployment** after thorough validation

## Status

- **Priority**: Enhancement (not blocking Phase B completion)
- **Complexity**: Medium (2-3 days implementation)
- **Risk**: Low (backward compatible with fallbacks)
- **Impact**: High (90% performance improvement for external drives)

---

*Document created during Phase B debugging - January 25, 2026*
*Research completed using Context7 MCP server documentation*