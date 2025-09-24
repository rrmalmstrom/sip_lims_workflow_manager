# Script Update System Implementation

## Overview

The SIP LIMS Workflow Manager now includes a comprehensive script update notification system that addresses the limitation where users would only see script updates when restarting the application.

## Problem Solved

### Original Issue
- **Script updates only checked at startup**: Users had to restart the entire application to see new script versions
- **Long-running sessions missed updates**: Users who kept the app open for extended periods never saw script update notifications
- **Browser refresh didn't help**: Refreshing the browser page didn't trigger script update checks
- **Manual restart required**: Users had to remember to periodically restart the app to check for script updates

### Solution Implemented
- **Persistent in-app notifications**: Script updates are now checked every 30 minutes during app runtime
- **Sidebar integration**: Update notifications appear prominently in the sidebar
- **One-click updates**: Users can update scripts directly from the GUI without restarting
- **Manual refresh capability**: Users can force immediate update checks
- **Cache management**: Intelligent caching prevents excessive Git operations

## Technical Implementation

### Core Components

#### 1. ScriptUpdateManager Class (`src/script_update_manager.py`)
- **Git Integration**: Uses subprocess to run Git commands safely
- **Caching System**: 30-minute cache TTL to balance responsiveness with performance
- **Error Handling**: Graceful handling of network issues, missing Git repos, timeouts
- **Cross-Platform**: Works on both macOS and Windows

**Key Methods:**
- `check_for_updates()`: Checks if script repository has updates available
- `update_scripts()`: Updates scripts by pulling from remote repository
- `get_update_details()`: Gets details about available updates (commits behind, etc.)
- `get_last_check_time()`: Returns timestamp of last update check
- `clear_cache()`: Manually clears cached results

#### 2. GUI Integration (`app.py`)
- **Cached Function**: `check_for_script_updates()` with 30-minute cache
- **Update Function**: `update_scripts()` with automatic cache clearing
- **Timestamp Formatting**: `format_last_check_time()` for user-friendly display

### User Interface

#### Sidebar Notification
When script updates are available, users see:
- **Clear heading**: "🔄 Script Updates Available"
- **Status message**: "New workflow scripts available!"
- **Last checked timestamp**: Shows when updates were last verified
- **Two action buttons**:
  - **"📥 Update Scripts"**: Performs the update with progress indicator
  - **"🔄 Check Now"**: Forces immediate cache refresh

#### User Experience Features
- **Visual prominence**: Update notifications are clearly visible in sidebar
- **Progress feedback**: Spinner shows during update operations
- **Success/error messages**: Clear feedback on update results
- **Automatic refresh**: Page refreshes after successful updates to clear notification
- **Non-intrusive**: Notifications only appear when updates are actually available

## Comparison: App Updates vs Script Updates

| Feature | App Updates | Script Updates |
|---------|-------------|----------------|
| **Check Frequency** | Every hour | Every 30 minutes |
| **Update Source** | Google Drive | Git repository |
| **Update Method** | Manual download | One-click in-app |
| **Cache Duration** | 60 minutes | 30 minutes |
| **Restart Required** | Yes | No |

## Technical Benefits

### Performance
- **Efficient caching**: Prevents excessive Git operations
- **Background operations**: Updates don't block the UI
- **Minimal overhead**: Git operations are fast and lightweight
- **Smart cache invalidation**: Cache cleared after successful updates

### Reliability
- **Comprehensive error handling**: Network failures, timeouts, missing repos
- **Graceful degradation**: App continues working even if script updates fail
- **Transaction-like updates**: Updates either succeed completely or fail cleanly
- **Rollback capability**: Failed updates don't leave repository in inconsistent state

### User Experience
- **No interruption**: Users don't need to restart the app
- **Immediate awareness**: Updates are visible as soon as they're available
- **One-click convenience**: Updates can be applied instantly
- **Clear feedback**: Users always know the status of their scripts

## Implementation Details

### Caching Strategy
```python
@st.cache_data(ttl=1800)  # 30-minute cache
def check_for_script_updates():
    # Git operations are cached to prevent excessive calls
    # Cache is automatically cleared after successful updates
```

### Error Handling
- **Network timeouts**: 10-second timeout for Git operations
- **Missing Git repository**: Clear error message if scripts directory isn't a Git repo
- **Permission issues**: Graceful handling of Git permission problems
- **Merge conflicts**: Clear error messages for update conflicts

### Security Considerations
- **Local operations only**: All Git operations are local to the scripts directory
- **No remote execution**: Only standard Git commands (fetch, status, pull) are used
- **Timeout protection**: All Git operations have configurable timeouts
- **Error isolation**: Script update failures don't affect main application

## Testing

### Test Coverage
- **14 core functionality tests**: Complete coverage of ScriptUpdateManager
- **11 GUI integration tests**: Testing of all user interface components
- **Mock-based testing**: No dependency on actual Git repositories for unit tests
- **Error scenario testing**: Comprehensive testing of failure modes

### Test Categories
1. **Initialization and configuration**
2. **Update detection (behind, up-to-date, errors)**
3. **Network error handling and timeouts**
4. **Script update operations (success and failure)**
5. **Caching behavior and invalidation**
6. **GUI integration and user interactions**

## Future Enhancements

### Potential Improvements
1. **Update details**: Show commit messages and change summaries
2. **Selective updates**: Allow users to choose which commits to pull
3. **Update scheduling**: Allow users to set custom check intervals
4. **Notification preferences**: Allow users to disable/customize notifications
5. **Update history**: Track and display update history

### Advanced Features
1. **Branch switching**: Allow users to switch between script branches
2. **Rollback capability**: Allow reverting to previous script versions
3. **Conflict resolution**: GUI for resolving merge conflicts
4. **Update notifications**: Desktop/email notifications for critical updates

## Conclusion

The script update system transforms the SIP LIMS Workflow Manager from a restart-dependent application into a continuously updated, self-maintaining system. Users now receive timely notifications about script updates and can apply them instantly without interrupting their workflow.

This implementation follows the project's established patterns for reliability, user experience, and maintainability while providing the persistent update checking that was missing from the original system.