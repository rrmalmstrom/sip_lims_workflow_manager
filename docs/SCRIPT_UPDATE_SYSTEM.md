# Unified Script Update System

## Overview

The SIP LIMS Workflow Manager now features a unified update system that manages both application and script updates through a single, clean interface. This document describes the script update component of the unified system.

## Evolution from Previous System

### Original Implementation (Deprecated)
- **Separate system**: Script updates used a different system than app updates
- **30-minute checks**: More frequent checking than app updates
- **Sidebar notifications**: Persistent update section in sidebar
- **Independent caching**: Separate cache management

### New Unified Implementation
- **Integrated system**: Scripts and app updates use the same GitUpdateManager
- **60-minute checks**: Consistent checking frequency for both update types
- **Clean notifications**: Updates only appear when available
- **Unified caching**: Single cache strategy for both update types

## Technical Implementation

### Unified GitUpdateManager

The script update system now uses the same `GitUpdateManager` class as application updates:

```python
# Create script update manager
script_manager = create_update_manager("scripts")

# Check for updates (cached for 60 minutes)
update_info = script_manager.check_for_updates()

# Apply updates
result = script_manager.update_to_latest()
```

### Repository Configuration

```python
SCRIPTS_REPOSITORY = {
    "ssh_url": "git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git",
    "github_api": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
    "local_path": "../sip_scripts_workflow_gui"
}
```

## User Interface Integration

### Clean, Non-Intrusive Design

**Before (Deprecated)**:
- Persistent sidebar section
- Always visible update controls
- Cluttered interface

**After (Current)**:
- Updates only appear when available
- Expandable interface for details
- Clean sidebar without permanent clutter

### Update Notification Flow

1. **Automatic Detection**: System checks every 60 minutes + on page refresh
2. **Smart Notification**: "🔔 Updates Available" appears only when needed
3. **Manual Cache Clearing**: "🔄 Manual Check for Updates" button always available in sidebar
4. **Expandable Details**: Click to reveal script update information
5. **One-Click Update**: "📥 Update Scripts Now" button applies updates instantly

### Interface Layout

```
🔔 Updates Available - Check the expandable section below

📦 Available Updates (Click to expand)
├── 🏠 Application Updates          │  🔧 Script Updates
│   Current: v1.0.2                 │  Current: v1.0.0  
│   Latest: v1.1.0                  │  Latest: v1.0.1
│   [📥 Download App Update]        │  [📥 Update Scripts Now]
```

## Update Process

### Script Update Workflow

1. **Detection**: GitHub API checks for new tags in scripts repository
2. **Notification**: Update available message appears in main content area
3. **User Action**: User clicks "📥 Update Scripts Now"
4. **Execution**: Git pull operation updates local scripts
5. **Feedback**: Success message and cache refresh
6. **Completion**: Updated scripts immediately available

### Technical Process

```python
def update_scripts():
    """Update scripts to latest version."""
    try:
        script_manager = create_update_manager("scripts")
        result = script_manager.update_to_latest()
        
        if result['success']:
            # Clear cache to refresh version info
            check_for_script_updates.clear()
            return {'success': True}
        else:
            return {'success': False, 'error': result['error']}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## Comparison: Old vs New System

| Feature | Old Script System | New Unified System |
|---------|------------------|-------------------|
| **Check Frequency** | 30 minutes | 60 minutes |
| **Interface** | Persistent sidebar | Expandable notification |
| **Update Method** | One-click in-app | One-click in-app |
| **Cache Duration** | 30 minutes | 60 minutes |
| **Restart Required** | No | No |
| **UI Clutter** | Always visible | Only when needed |
| **Integration** | Separate system | Unified with app updates |

## Benefits of Unified System

### For Users
- **Cleaner Interface**: No persistent update clutter
- **Consistent Experience**: Same interface for all updates
- **Better Organization**: Related updates grouped together
- **User Control**: Explicit approval for all updates

### For Developers
- **Single Codebase**: One update system to maintain
- **Consistent Authentication**: Same SSH key for both repositories
- **Unified Testing**: Single test suite for all update functionality
- **Simplified Architecture**: Reduced complexity

### For Maintenance
- **Easier Updates**: Single system to enhance
- **Better Security**: Consistent security model
- **Unified Logging**: All update operations logged consistently
- **Simplified Debugging**: Single code path for issues

## Error Handling

### Script-Specific Error Scenarios

**Git Repository Issues**:
- Scripts directory not a Git repository
- Remote repository not accessible
- Merge conflicts during update
- Authentication failures

**Network Issues**:
- GitHub API timeouts
- SSH connection failures
- DNS resolution problems
- Firewall blocking Git operations

**File System Issues**:
- Permission problems in scripts directory
- Disk space insufficient for updates
- File locks preventing updates
- Corrupted Git repository

### Error Recovery

```python
# Graceful error handling
try:
    result = script_manager.update_to_latest()
    if not result['success']:
        # Show clear error message to user
        st.error(f"❌ Update failed: {result['error']}")
        # Provide recovery suggestions
        st.info("💡 Try checking your network connection and SSH key setup")
except Exception as e:
    # Log error and show user-friendly message
    st.error("❌ Unexpected error during script update")
```

## Security Considerations

### SSH Key Security
- **Same Key**: Uses the same SSH deploy key as application updates
- **Read-Only Access**: Deploy key has read-only permissions
- **Key Validation**: Automated security checks before operations
- **Permission Enforcement**: Strict file permission requirements

### Update Security
- **Trusted Source**: Updates only from official repository
- **SSH Encryption**: All Git operations over encrypted SSH
- **Atomic Updates**: Updates either succeed completely or fail cleanly
- **Rollback Capability**: Failed updates don't corrupt repository

## Testing

### Automated Testing

**Integration Tests** (part of unified test suite):
- Script update detection
- Update application process
- Error handling scenarios
- Cache behavior validation

**Test Coverage**:
```python
def test_check_for_script_updates_success()
def test_check_for_script_updates_no_update()
def test_check_for_script_updates_error()
def test_update_scripts_success()
def test_update_scripts_failure()
```

### Manual Testing

**User Interface Testing**:
- Update notification appearance
- Expandable interface functionality
- Button interactions
- Error message display

**Real Update Testing**:
- Actual Git tag creation
- Update detection verification
- Update application process
- Cache refresh validation

## Performance Optimization

### Caching Strategy

```python
@st.cache_data(ttl=3600)  # 60-minute cache
def check_for_script_updates():
    """
    Cached script update checking.
    Prevents excessive Git operations while ensuring timely updates.
    """
```

### Efficient Operations
- **GitHub API Primary**: Fast version checking via API
- **SSH Fallback**: Only when API unavailable
- **Smart Caching**: Prevents redundant Git operations with 60-minute TTL
- **Manual Cache Override**: Always-available manual cache clearing button
- **Background Processing**: Non-blocking update detection

## Migration Notes

### From Previous Script System

**Deprecated Components**:
- ~~ScriptUpdateManager class~~
- ~~Separate 30-minute caching~~
- ~~Independent sidebar notifications~~
- ~~Separate error handling~~

**Maintained Functionality**:
- ✅ One-click script updates
- ✅ No restart required
- ✅ Automatic update detection
- ✅ Clear user feedback

**Improvements**:
- ✅ Cleaner interface
- ✅ Unified authentication
- ✅ Consistent error handling
- ✅ Better testing coverage

## Future Enhancements

### Planned Improvements
- **Update Details**: Show commit messages for script updates
- **Selective Updates**: Choose specific commits to apply
- **Branch Support**: Switch between script branches
- **Update History**: Track script update history

### Advanced Features
- **Rollback Capability**: Revert to previous script versions
- **Conflict Resolution**: GUI for handling merge conflicts
- **Update Scheduling**: Custom update check intervals
- **Notification Preferences**: Customizable update notifications

## Cache Management

### Streamlit Caching Issue Resolution

**Problem Identified**: The [`@st.cache_data(ttl=3600)`](../app.py:26) decorator was causing a caching catch-22 where:
- Update checks were cached for 60 minutes
- When first loaded (before new tags), it cached "no updates available"
- After new tags were created, the cached result persisted
- The original "Force Check Updates" button only appeared when updates were already detected

**Solution Implemented**: Added a permanent "🔄 Manual Check for Updates" button in the sidebar that:
- Is always visible regardless of update status
- Clears both app and script update caches when clicked
- Provides immediate feedback with success message
- Triggers automatic page refresh to show new update status

### Manual Cache Clearing

```python
# Sidebar manual update check button
if st.button("🔄 Manual Check for Updates", key="sidebar_check_updates"):
    # Clear both update caches
    check_for_app_updates.clear()
    check_for_script_updates.clear()
    st.success("✅ Update cache cleared!")
    st.rerun()
```

**Benefits**:
- ✅ Resolves caching catch-22 situation
- ✅ Always accessible to users
- ✅ Provides immediate cache refresh capability
- ✅ Maintains existing automatic update detection
- ✅ No impact on performance or user experience

### Testing Coverage

The manual cache clearing functionality is covered by comprehensive tests in [`tests/test_manual_update_check.py`](../tests/test_manual_update_check.py):

- Button existence and placement verification
- Cache clearing functionality validation
- User feedback and interaction testing
- Integration with existing update system
- Proper key assignment and caption text

## Conclusion

The unified script update system maintains all the benefits of the previous implementation while providing a cleaner, more consistent user experience. By integrating script updates with the overall update system, users get a unified interface that reduces clutter while maintaining the convenience of one-click script updates.

The system continues to provide immediate script updates without requiring application restarts, while now offering better security, consistency, and maintainability through the unified architecture.