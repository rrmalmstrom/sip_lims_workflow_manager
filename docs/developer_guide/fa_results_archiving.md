# Fragment Analyzer Results Archiving Implementation

## Overview

The FA Results Archiving system provides automatic preservation of Fragment Analyzer experimental data during workflow operations. This feature ensures that valuable FA results are never lost when using the workflow manager's undo functionality.

## Architecture

### Core Components

1. **Archive Functions in FA Scripts**: Each FA analysis script contains an `archive_fa_results()` function
2. **Workflow Manager Exclusions**: The workflow manager's snapshot system excludes archive directories
3. **Directory Tracking**: FA scripts track result directories during processing for selective archiving

### Archive Directory Structure

```
archived_files/
├── first_lib_attempt_fa_results/     # First attempt FA results
├── second_lib_attempt_fa_results/    # Second attempt FA results
└── third_lib_attempt_fa_results/     # Emergency third attempt FA results
```

## Implementation Details

### FA Script Modifications

Each FA analysis script (`first.FA.output.analysis.py`, `second.FA.output.analysis.py`, `emergency.third.FA.output.analysis.py`) has been modified with:

#### 1. Enhanced `getFAfiles()` Function
```python
def getFAfiles(crnt_dir):
    fa_files = []
    fa_result_dirs_to_archive = []  # Track directories for archiving
    
    # Process FA directories and track them
    for direct in os.scandir(crnt_dir):
        if direct.is_dir():
            nxt_dir = os.path.abspath(direct)
            for fa in os.scandir(nxt_dir):
                if fa.is_dir():
                    # Track this directory for archiving
                    fa_result_dirs_to_archive.append(Path(fa.path))
                    # ... existing processing logic
    
    return fa_files, fa_result_dirs_to_archive
```

#### 2. Archive Function
```python
def archive_fa_results(fa_result_dirs, archive_subdir_name):
    """Archive FA result directories to permanent storage"""
    if not fa_result_dirs:
        return
    
    # Create archive directory
    archive_base = PROJECT_DIR / "archived_files"
    archive_dir = archive_base / archive_subdir_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for result_dir in fa_result_dirs:
        if result_dir.exists():
            dest_path = archive_dir / result_dir.name
            
            # Handle existing archives (prevent nesting)
            if dest_path.exists():
                shutil.rmtree(dest_path)
                print(f"Removing existing archive: {result_dir.name}")
            
            # Move directory to archive
            shutil.move(str(result_dir), str(dest_path))
            print(f"Archived: {result_dir.name}")
            
            # Clean up empty parent directories
            parent_dir = result_dir.parent
            if parent_dir.exists():
                # Check if directory is empty (ignoring .DS_Store files)
                remaining_files = [f for f in parent_dir.iterdir() if f.name != '.DS_Store']
                if not remaining_files:
                    # Remove any .DS_Store files first
                    for ds_store in parent_dir.glob('.DS_Store'):
                        ds_store.unlink()
                    # Now remove the empty directory
                    parent_dir.rmdir()
                    print(f"Cleaned up empty directory: {parent_dir.name}")
```

#### 3. Main Program Integration
```python
# Archive FA results before creating success marker
if fa_result_dirs_to_archive:
    archive_fa_results(fa_result_dirs_to_archive, "first_lib_attempt_fa_results")

# Create success marker
success_file = status_dir / "first.FA.output.analysis.success"
success_file.touch()
```

### Workflow Manager Integration

#### Snapshot Exclusion Patterns

In `src/logic.py`, the snapshot functions exclude FA archive directories:

```python
def take_complete_snapshot(step_name):
    # FA archive exclusion patterns
    fa_archive_patterns = {
        'archived_files/first_lib_attempt_fa_results',
        'archived_files/second_lib_attempt_fa_results', 
        'archived_files/third_lib_attempt_fa_results'
    }
    
    # Combine with other exclusions
    exclusions = base_exclusions | fa_archive_patterns
    # ... snapshot logic with exclusions

def restore_complete_snapshot(snapshot_path):
    # Same FA archive exclusion patterns
    fa_archive_patterns = {
        'archived_files/first_lib_attempt_fa_results',
        'archived_files/second_lib_attempt_fa_results',
        'archived_files/third_lib_attempt_fa_results'
    }
    
    # Preserve archives during restore
    exclusions = base_exclusions | fa_archive_patterns
    # ... restore logic with exclusions
```

## Key Features

### 1. Nested Directory Prevention
- Checks for existing archives before moving
- Removes existing archives to prevent nested folder structures
- Ensures clean archive organization on script re-runs

### 2. Smart Cleanup
- Removes empty parent directories after archiving
- Handles macOS `.DS_Store` files correctly
- Only removes truly empty directories

### 3. Undo Safety
- Archives are excluded from workflow snapshots
- FA data persists through undo operations
- Original FA directories are restored from snapshots when needed

### 4. Transparent Operation
- Clear console output during archiving process
- Shows which directories are being archived
- Reports cleanup operations

## Testing Verification

The implementation has been thoroughly tested with:

1. **Multiple script runs**: Verified nested directory prevention
2. **Undo operations**: Confirmed archives persist during rollbacks
3. **Directory cleanup**: Verified empty parent directory removal
4. **Cross-platform compatibility**: Tested `.DS_Store` handling on macOS

## Error Handling

- Graceful handling of missing directories
- Safe file operations with existence checks
- Robust cleanup logic that handles edge cases
- Clear error reporting in console output

## Future Considerations

- Archive size management for long-running projects
- Optional archive compression for storage efficiency
- Archive browsing interface in workflow manager UI
- Automated archive cleanup policies