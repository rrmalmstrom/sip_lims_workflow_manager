# 🤝 Coding Agent Handoff: Smart Sync Implementation

## 📋 Mission Brief

**Objective**: Implement Smart Sync Layer to solve Windows Docker network drive permission issues for the SIP LIMS Workflow Manager.

**Problem**: Windows users cannot run the workflow manager on network drives (Z:\) due to Docker Desktop permission limitations. The container can mount but fails write validation.

**Solution**: Transparent sync layer that copies projects to local staging, runs Docker locally, and syncs changes back to network drive.

---

## 🎯 Implementation Overview

### **What You're Building**

A **Smart Sync Layer** that:
1. **Detects** Windows + network drive scenarios automatically
2. **Syncs** project data: Network → Local → Docker → Network
3. **Integrates** seamlessly with existing workflow manager
4. **Preserves** all functionality including snapshots and hidden files
5. **Handles** errors gracefully with network disconnection recovery

### **Key Files to Modify**

| File | Purpose | Changes |
|------|---------|---------|
| `src/smart_sync.py` | **NEW** - Core sync logic | Create SmartSyncManager class |
| `run.py` | Launcher with sync detection | Add detection + setup methods |
| `src/core.py` | Workflow execution | Add pre/post-step sync triggers |
| `docker-compose.yml` | Container config | Add sync script volumes |
| `Dockerfile` | Container setup | Add sync mount points |
| `sync_scripts/` | **NEW** - Sync scripts | Create Python sync scripts |

---

## 🔧 Technical Architecture

### **Sync Flow**
```
1. User runs: python run.py
2. Detect: Windows + Z:\ drive?
3. Setup: Create C:\temp\project, sync Z:\ → C:\temp\
4. Launch: Docker with C:\temp\ (not Z:\)
5. Execute: Each workflow step triggers sync
6. Cleanup: Final sync C:\temp\ → Z:\
```

### **Integration Points**

#### **run.py Integration**
- **Line 267**: Add `detect_smart_sync_scenario()` and `setup_smart_sync_environment()`
- **Line 431**: Modify `launch_container()` to use local staging when needed

#### **core.py Integration**  
- **Line 112**: Add `self._trigger_pre_step_sync()` in `run_step()`
- **Line 192**: Add `self._trigger_post_step_sync(step_id)` in `handle_step_result()`

#### **Docker Integration**
- **docker-compose.yml**: Mount sync scripts to `/opt/sync`
- **Dockerfile**: Create `/opt/sync` directory with proper permissions

---

## 📁 File Structure

```
sip_lims_workflow_manager/
├── src/
│   ├── smart_sync.py          # NEW - SmartSyncManager class
│   └── core.py                # MODIFY - Add sync triggers
├── sync_scripts/              # NEW - Container sync scripts
│   ├── pre_step_sync.py       # NEW - Pre-step sync
│   └── post_step_sync.py      # NEW - Post-step sync
├── run.py                     # MODIFY - Add sync detection
├── docker-compose.yml         # MODIFY - Add sync volumes
├── Dockerfile                 # MODIFY - Add sync mount points
└── tests/
    └── test_smart_sync.py     # NEW - Sync tests
```

---

## 🚀 Implementation Phases

### **Phase 1: Core Sync Infrastructure** ⭐ **START HERE**

#### **1.1 Create SmartSyncManager** 
**File**: `src/smart_sync.py` (NEW)

**Key Methods**:
- `initial_sync()` - Full network → local copy
- `incremental_sync_down()` - Fast network → local updates  
- `incremental_sync_up()` - Fast local → network updates
- `_detect_changes()` - Compare file timestamps/existence
- `_should_ignore()` - Skip `__pycache__`, `.DS_Store`, etc.

**Critical Requirements**:
- ✅ Handle **hidden files** (`.snapshots/`, `.workflow_status/`)
- ✅ Preserve **file timestamps** with `shutil.copy2()`
- ✅ **Error handling** - don't crash workflow if sync fails
- ✅ **Performance** - incremental sync should be <10 seconds

#### **1.2 Modify run.py**
**Location**: After line 267 (end of PlatformAdapter class)

**Add Methods**:
```python
@staticmethod
def detect_smart_sync_scenario(project_path: Path) -> bool:
    """Detect Windows + network drive (D: through Z:, exclude C:)"""

@staticmethod  
def setup_smart_sync_environment(network_path: Path) -> Dict[str, str]:
    """Create C:\temp\staging, perform initial sync, return env vars"""
```

**Location**: Line 431 - Modify `launch_container()`
- Check if sync needed with `detect_smart_sync_scenario()`
- If yes, call `setup_smart_sync_environment()` 
- Use local staging path for Docker instead of network path
- Add sync environment variables

### **Phase 2: Container Integration**

#### **2.1 Create Sync Scripts**
**Directory**: `sync_scripts/` (NEW)

**Files**:
- `pre_step_sync.py` - Called before each workflow step
- `post_step_sync.py` - Called after successful step completion

**Key Points**:
- Scripts run **inside container** with mounted sync logic
- Use environment variables: `NETWORK_PROJECT_PATH`, `LOCAL_PROJECT_PATH`
- Import `SmartSyncManager` from `/opt/app/src/smart_sync`
- Handle errors gracefully (print warnings, don't crash)

#### **2.2 Modify core.py**
**Add Methods**:
```python
def _trigger_pre_step_sync(self):
    """Call pre_step_sync.py before step execution"""

def _trigger_post_step_sync(self, step_id: str):
    """Call post_step_sync.py after successful step"""
```

**Integration Points**:
- `run_step()` line 112: Add `self._trigger_pre_step_sync()`
- `handle_step_result()` line 192: Add `self._trigger_post_step_sync(step_id)`

#### **2.3 Update Docker Configuration**
**docker-compose.yml**: Add sync script volume and environment variables
**Dockerfile**: Create `/opt/sync` mount point with proper permissions

### **Phase 3: Testing & Validation**

#### **3.1 Create Test Suite**
**File**: `tests/test_smart_sync.py` (NEW)

**Test Cases**:
- Initial full sync
- Incremental sync (both directions)
- Hidden file preservation
- Error handling
- Performance benchmarks

#### **3.2 Integration Testing**
- Test on Windows with actual Z: drive
- Verify workflow steps trigger sync correctly
- Test network disconnection scenarios
- Validate snapshot system preservation

---

## ⚠️ Critical Implementation Notes

### **Must-Have Features**

1. **Hidden File Support**: `.snapshots/`, `.workflow_status/`, `.workflow_logs/` must sync
2. **Timestamp Preservation**: Use `shutil.copy2()` to maintain file modification times
3. **Error Resilience**: Sync failures should warn but not crash workflow
4. **Performance**: Incremental sync must be fast (<10 seconds typical)
5. **Backward Compatibility**: No impact on macOS/Linux users

### **Environment Variables**

When Smart Sync is active, these environment variables are set:
```bash
SMART_SYNC_ENABLED=true
NETWORK_PROJECT_PATH=Z:\original\project\path
LOCAL_PROJECT_PATH=C:\temp\sip_workflow\project_name
PROJECT_PATH=C:\temp\sip_workflow\project_name  # Docker sees this
```

### **Sync Triggers**

| Event | Sync Direction | Purpose |
|-------|---------------|---------|
| Container start | Network → Local | Get latest project state |
| Before each step | Network → Local | Check for external changes |
| After successful step | Local → Network | Save step results |
| Container shutdown | Local → Network | Final save |

### **Files to Sync vs Ignore**

**✅ Sync These**:
- All `.db` files (SQLite databases)
- `workflow_state.json` (workflow progress)
- `.snapshots/` (complete project history)
- `.workflow_status/` (step completion markers)  
- `.workflow_logs/` (execution logs)
- All user data files and directories
- **All hidden files and directories**

**❌ Ignore These**:
- `__pycache__/` (Python cache)
- `.DS_Store` (macOS metadata)
- `Thumbs.db` (Windows thumbnails)
- `.sync_log.json` (sync metadata)

---

## 🧪 Testing Strategy

### **Development Testing**

1. **Unit Tests**: Test `SmartSyncManager` methods individually
2. **Integration Tests**: Test full sync workflow with real directories
3. **Performance Tests**: Measure sync times with various project sizes
4. **Error Tests**: Test network disconnection, permission errors

### **Windows Testing Requirements**

**You MUST test on Windows with**:
- Actual mapped network drive (Z:\)
- Docker Desktop in WSL2 mode
- Real project data including hidden files
- Network disconnection scenarios

### **Success Criteria**

- ✅ Windows user can run `python run.py` with Z:\ project
- ✅ Workflow executes normally with transparent sync
- ✅ All files including `.snapshots/` preserved
- ✅ Sync time <10 seconds for typical steps
- ✅ Graceful handling of network errors
- ✅ No impact on macOS/Linux workflows

---

## 🔍 Debugging & Troubleshooting

### **Common Issues**

1. **Permission Errors**: Ensure `C:\temp\` is writable
2. **Network Timeouts**: Add timeout handling in sync operations
3. **Large Files**: Consider progress indicators for big syncs
4. **Path Issues**: Handle Windows path separators correctly

### **Debug Logging**

Add debug output to track sync operations:
```python
click.echo(f"📥 Syncing {len(changes)} files from network...")
click.echo(f"📤 Step {step_id} synced to network drive")
```

### **Validation Commands**

Test sync detection:
```python
from src.smart_sync import SmartSyncManager
from run import PlatformAdapter

# Test detection
result = PlatformAdapter.detect_smart_sync_scenario(Path("Z:\\test"))
print(f"Smart Sync needed: {result}")
```

---

## 📋 Implementation Checklist

### **Phase 1: Core Infrastructure**
- [ ] Create `src/smart_sync.py` with `SmartSyncManager` class
- [ ] Implement `initial_sync()`, `incremental_sync_down()`, `incremental_sync_up()`
- [ ] Add Windows detection to `run.py` 
- [ ] Modify `launch_container()` for sync support
- [ ] Test basic sync functionality

### **Phase 2: Container Integration**  
- [ ] Create `sync_scripts/` with Python sync scripts
- [ ] Update `docker-compose.yml` and `Dockerfile`
- [ ] Add sync triggers to `core.py`
- [ ] Test end-to-end workflow with sync

### **Phase 3: Testing & Polish**
- [ ] Create comprehensive test suite
- [ ] Test on Windows with real network drives
- [ ] Add error handling and recovery
- [ ] Performance optimization
- [ ] Documentation updates

---

## 🎯 Success Metrics

**When implementation is complete**:

1. **Functionality**: Windows users can run workflows on Z:\ drives
2. **Performance**: Sync operations complete in <10 seconds  
3. **Reliability**: Graceful handling of network issues
4. **Transparency**: Users don't know sync is happening
5. **Compatibility**: No impact on existing macOS/Linux workflows

---

## 🤝 Handoff Complete

**You now have**:
- ✅ Complete architecture design
- ✅ Detailed implementation plan  
- ✅ Specific code changes with line numbers
- ✅ Test strategy and success criteria
- ✅ Error handling requirements

**Next Steps**:
1. Start with Phase 1 (Core Infrastructure)
2. Test each phase before proceeding
3. Focus on Windows network drive scenarios
4. Ensure backward compatibility

**Questions?** Refer to:
- [`plans/smart_sync_architecture_design.md`](plans/smart_sync_architecture_design.md) - Complete technical design
- [`plans/smart_sync_implementation_plan.md`](plans/smart_sync_implementation_plan.md) - Detailed implementation steps
- [`plans/windows_network_drive_comprehensive_analysis.md`](plans/windows_network_drive_comprehensive_analysis.md) - Original problem analysis

Good luck! This solution will enable seamless Windows network drive support while preserving all existing functionality.