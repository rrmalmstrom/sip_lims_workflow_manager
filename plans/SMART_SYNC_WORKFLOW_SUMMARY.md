# Smart Sync Layer - Complete Workflow Summary

## 🎯 **Overview**
Smart Sync is a fail-fast bidirectional synchronization system that solves Windows Docker network drive permission issues by automatically creating local staging and maintaining data integrity through three-factor success detection. The system includes comprehensive cleanup logic and enhanced debug logging for robust operation.

## 🔍 **Detection Phase**

### 1. Smart Sync Scenario Detection
**Location**: [`run.py`](run.py) → `detect_smart_sync_scenario()`

**Triggers When**:
- Platform is Windows (`platform.system() == "Windows"`)
- Project path is on network drive (D: through Z:) or UNC path (\\server\share)
- Local C: drive paths are excluded

**Detection Logic**:
```python
# Network drives: D:, E:, F:, ..., Z:
if drive_letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
    return True

# UNC paths: \\server\share or //server/share  
if path_str.startswith(('\\\\', '//')):
    return True
```

## 🚀 **Initialization Phase**

### 2. Smart Sync Environment Setup
**Location**: [`run.py`](run.py) → `setup_smart_sync_environment()`

**Process**:
1. **Create Local Staging**: `C:\temp\sip_workflow\{project_name}`
2. **Initialize SmartSyncManager**: Network path ↔ Local path mapping
3. **Perform Initial Sync**: Complete copy from network to local
4. **Set Environment Variables**:
   ```bash
   SMART_SYNC_ENABLED=true
   NETWORK_PROJECT_PATH=Z:\original\path
   LOCAL_PROJECT_PATH=C:\temp\sip_workflow\project
   PROJECT_PATH=C:\temp\sip_workflow\project  # Docker uses local
   ```

### 3. Initial Sync (Network → Local)
**Location**: [`src/smart_sync.py`](src/smart_sync.py) → `initial_sync()`

**Process**:
1. **Detect Changes**: Compare network vs local (full scan)
2. **Copy Files**: All files from network to local staging
3. **Preserve Metadata**: Timestamps, permissions maintained
4. **Handle Errors**: **FAIL-FAST** - Any permission error raises `SmartSyncError`
5. **Log Operations**: Comprehensive debug logging if enabled

**Failure Behavior**:
- **Permission Error**: Raises `SmartSyncError` → Workflow launch fails
- **Network Error**: Raises `SmartSyncError` → Workflow launch fails
- **No graceful degradation** - data integrity is paramount

## 🔄 **Workflow Execution Phase**

### 4. Pre-Step Sync (Before Each Workflow Step)
**Location**: [`src/core.py`](src/core.py) → `run_step()` → Pre-step sync

**Process**:
1. **Trigger**: Called automatically before every workflow step execution
2. **Direction**: Network → Local (get latest changes)
3. **Method**: `incremental_sync_down()`
4. **Change Detection**: Compare timestamps and file sizes
5. **Sync Operations**: Copy modified/new files, delete removed files

**Failure Behavior**:
- **Sync Error**: Raises `RuntimeError` → Step execution prevented
- **Permission Error**: Raises `SmartSyncError` → Step execution prevented
- **Network Error**: Raises `RuntimeError` → Step execution prevented

**User Feedback**:
```
Smart Sync: Syncing latest changes before step 'step_name'...
Smart Sync: Pre-step sync completed successfully
```

### 5. Workflow Step Execution
**Location**: [`src/core.py`](src/core.py) → `run_step()`

**Process**:
1. **Pre-step sync completes** (or step is prevented)
2. **Snapshot Creation**: Complete project snapshot for rollback
3. **Script Execution**: Run workflow script in Docker container
4. **Docker Environment**: Uses local staging path (`LOCAL_PROJECT_PATH`)

### 6. Three-Factor Success Detection
**Location**: [`src/core.py`](src/core.py) → `handle_step_result()`

**Three Factors Required for Step Success**:

#### Factor 1: Script Exit Code Success
- Script must exit with code 0
- Checked via `RunResult.success`

#### Factor 2: Success Marker File
- Script must create `.workflow_status/{script_name}.success`
- Checked via `_check_success_marker()`

#### Factor 3: Post-Step Sync Success
- Local → Network sync must complete successfully
- Checked via `_perform_post_step_sync()`

**Success Logic**:
```python
actual_success = exit_code_success AND marker_file_success AND sync_success
```

### 7. Post-Step Sync (After Each Workflow Step)
**Location**: [`src/core.py`](src/core.py) → `_perform_post_step_sync()`

**Process**:
1. **Trigger**: Called automatically after script execution (regardless of script success)
2. **Direction**: Local → Network (save results)
3. **Method**: `incremental_sync_up()`
4. **Change Detection**: Compare local vs network
5. **Sync Operations**: Copy modified/new files, delete removed files

**Failure Behavior**:
- **Sync Failure**: Step marked as failed → Automatic rollback triggered
- **Permission Error**: Step marked as failed → Automatic rollback triggered
- **Network Error**: Step marked as failed → Automatic rollback triggered

**User Feedback**:
```
Smart Sync: Saving results to network drive after step 'step_name'...
Smart Sync: Results successfully saved to network drive
```

## ⚠️ **Error Handling & Recovery**

### 8. Automatic Rollback System
**Location**: [`src/core.py`](src/core.py) → `handle_step_result()` failure path

**Triggers When**:
- Script fails (exit code ≠ 0)
- Success marker missing
- Post-step sync fails

**Rollback Process**:
1. **Restore Snapshot**: Complete project state restored to pre-step state
2. **Clean Snapshots**: Remove failed run snapshots
3. **Reset Step State**: Mark step as "pending" (not completed)
4. **User Notification**: Clear error messages with guidance

**User Feedback**:
```
❌ STEP FAILED: 'Step Name' - Smart Sync failed to save results to network drive
   The script completed successfully but results could not be synchronized.
   This step will be automatically rolled back to prevent data corruption.
   Please check for locked files (Excel, etc.) and try again.
ROLLBACK: Restoring snapshot for failed step 'step_name'
ROLLBACK COMPLETE: Restored to before state (run 1) for step 'step_name'
```

### 9. Critical Error Types

#### SmartSyncError (Critical Failures)
- **Excel files locked**: "Excel file locked (likely open in Excel): filename.xlsx"
- **Permission denied**: "File permission denied: filename. Error: Permission denied"
- **Copy failures**: "Could not copy source to dest: error"

#### RuntimeError (Workflow Prevention)
- **Pre-step sync failure**: "Smart Sync: Pre-step sync error: {error} - cannot proceed with step"

#### Graceful Failures (Non-Critical)
- **Network disconnection**: Returns `False` but doesn't crash
- **Logging errors**: Continue operation despite logging failures

## 🏁 **Cleanup Phase**

### 10. Comprehensive Cleanup System

Smart Sync includes multiple cleanup mechanisms to ensure no orphaned staging directories remain:

#### **A. Orphaned Staging Directory Cleanup**
**Location**: [`run.py`](run.py) lines 352-380, [`run_debug.py`](run_debug.py) (synchronized)

**When**: Before Smart Sync setup (every launch)

**Process**:
1. **Check Staging Base**: `C:\temp\sip_workflow\`
2. **Identify Project Staging**: `C:\temp\sip_workflow\{project_name}`
3. **Remove Orphaned Directory**: `shutil.rmtree(project_staging, ignore_errors=True)`

**User Feedback**:
```
🧹 Cleaned up orphaned staging: C:\temp\sip_workflow\old_project
```

#### **B. Container Shutdown Cleanup**
**Location**: [`run.py`](run.py) lines 675-697

**When**: During KeyboardInterrupt (Ctrl+C) or container shutdown

**Process**:
1. **Detect Smart Sync Environment**: Check `SMART_SYNC_ENABLED=true`
2. **Create Sync Manager**: Using environment variables
3. **Final Sync**: Local → Network (save any pending changes)
4. **Cleanup Local Staging**: Remove local staging directory

**User Feedback**:
```
🔄 Smart Sync: Performing final sync before shutdown...
📤 Smart Sync: Final sync completed
🧹 Smart Sync: Cleanup completed
```

#### **C. SmartSyncManager Cleanup**
**Location**: [`src/smart_sync.py`](src/smart_sync.py) lines 648-661

**When**: Called by container shutdown or explicit cleanup

**Process**:
1. **Check Local Path Exists**: Verify staging directory exists
2. **Remove Directory**: `shutil.rmtree(self.local_path)`
3. **Handle Errors Gracefully**: Print warnings but don't crash

**User Feedback**:
```
🧹 Cleaning up local staging directory...
✅ Local staging cleaned up
```

**Error Handling**:
```
⚠️ Warning: Could not clean up staging directory: [error details]
```

### 11. Final Sync & Cleanup (Legacy)
**Location**: [`src/core.py`](src/core.py) → `finalize_smart_sync()` (removed in current implementation)

**Note**: This method was removed in favor of the comprehensive cleanup system above. Cleanup now happens automatically during container shutdown via the mechanisms described in sections 10A-10C.

## 🔧 **Debug & Monitoring**

### 11. Debug Logging System
**Activation**: `python run.py --debug` or `SMART_SYNC_DEBUG=true`

**Debug Output Location**: `.workflow_logs/debug_output/`

**Logged Information**:
- **Sync Operations**: File copy/delete operations with timestamps
- **Performance Metrics**: Sync duration, file counts, transfer rates
- **Error Details**: Complete error traces and context
- **Environment Info**: Paths, settings, detection results

### 12. Performance Monitoring
**Metrics Tracked**:
- **Files Synced**: Total count of files processed
- **Sync Duration**: Time taken for each sync operation
- **Transfer Rates**: Files per second, data throughput
- **Error Rates**: Failed operations vs successful operations

## 🎯 **Key Design Principles**

### Fail-Fast Philosophy
- **No graceful degradation** for critical operations
- **Data integrity over convenience**
- **Clear error messages** with actionable guidance
- **Automatic rollback** prevents partial state corruption

### Three-Factor Validation
- **Script success alone is insufficient**
- **Sync success required** for step completion
- **Marker files provide** script-level confirmation
- **All factors must succeed** or step fails

### Comprehensive Logging
- **Debug information** for troubleshooting
- **Performance metrics** for optimization
- **Error context** for problem resolution
- **User feedback** for operational awareness

## 📊 **Success Scenarios**

### Perfect Execution
1. ✅ Pre-step sync succeeds
2. ✅ Script executes successfully (exit code 0)
3. ✅ Success marker created
4. ✅ Post-step sync succeeds
5. ✅ Step marked as completed

### Failure with Recovery
1. ✅ Pre-step sync succeeds
2. ✅ Script executes successfully (exit code 0)
3. ✅ Success marker created
4. ❌ Post-step sync fails (Excel file locked)
5. 🔄 Automatic rollback triggered
6. ✅ Project restored to pre-step state
7. ⚠️ Step remains pending with clear error message

This fail-fast approach ensures data integrity while providing clear feedback for issue resolution.