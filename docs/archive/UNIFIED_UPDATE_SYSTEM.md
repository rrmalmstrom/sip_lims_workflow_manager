# Unified Update System Documentation

## Overview

The SIP LIMS Workflow Manager features a unified update system that manages both application and script updates through a single, clean interface. This system replaces the previous dual update architecture with a consistent Git-based approach.

## Architecture

### Unified GitUpdateManager

The system uses a single `GitUpdateManager` class that handles both repository types:

- **Application Repository**: `sip_lims_workflow_manager`
- **Scripts Repository**: `sip_scripts_workflow_gui`

Both repositories use:
- Git tag versioning (semantic versioning)
- GitHub API for update detection
- HTTPS for repository access

### Key Components

1. **`src/git_update_manager.py`**: Unified update manager for both repositories
2. **`src/ssh_key_manager.py`**: SSH key security validation and management
3. **`app.py`**: Clean UI integration with expandable update notifications

## User Interface

### Clean, Non-Intrusive Design

The update system follows a "show only when needed" philosophy:

- **No persistent UI clutter**: Update sections only appear when updates are available
- **Smart notifications**: Brief "🔔 Updates Available" message at top of main content
- **Expandable details**: Click to reveal side-by-side update information
- **Clean sidebar**: No permanent update section taking up space

### Update Workflow

1. **Automatic Detection**: System checks every 60 minutes + on page refresh
2. **User Notification**: Blue info banner appears when updates are found
3. **Expandable Interface**: Click "📦 Available Updates" to see details
4. **Two-Column Layout**: 
   - Left: Application updates (manual download)
   - Right: Script updates (one-click in-app)
5. **User Control**: All updates require explicit user approval

## Technical Implementation

### Update Frequency

- **Check Interval**: 60 minutes (configurable via TTL)
- **Cache Duration**: 60 minutes using Streamlit's `@st.cache_data(ttl=3600)`
- **Trigger Events**: 
  - Automatic timer expiration
  - Page refresh/reload
  - Manual "Force Check Updates" button

### Version Detection

```python
# Git tag-based versioning
current_version = "v1.0.2"  # From local Git tags
latest_version = "v1.1.0"   # From GitHub API/remote tags

# Update available when latest > current
update_available = compare_versions(latest_version, current_version)
```

### Security Features

- **Error Handling**: Graceful fallback when network issues occur

## Configuration


### Repository Configuration

```python
REPOSITORIES = {
    "application": {
        "url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
        "github_api": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager"
    },
    "scripts": {
        "url": "https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git",
        "github_api": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui"
    }
}
```

## Update Types

### Application Updates

- **Source**: GitHub releases page
- **Process**: Manual download and installation
- **Restart**: Required after installation
- **Content**: GUI improvements, new features, bug fixes

### Script Updates

- **Source**: Git repository via HTTPS
- **Process**: One-click in-app update
- **Restart**: Not required
- **Content**: Scientific workflows, analysis methods, script fixes

## Error Handling

The system includes comprehensive error handling:

### SSH Key Issues

### Network Issues
- GitHub API timeouts
- Git connection failures
- DNS resolution problems

### Git Issues
- Repository not found
- Invalid tags
- Merge conflicts

All errors are logged and displayed to users with clear guidance for resolution.

## Testing

### Automated Tests

- **Integration Tests**: 13 comprehensive tests in `tests/test_unified_update_integration.py`
- **Mock Testing**: Simulates various update scenarios
- **Error Testing**: Validates error handling paths
- **Cache Testing**: Verifies caching behavior

### Manual Testing

- **UI Testing**: Interactive test interface for user validation
- **Real Updates**: Tested with actual Git tag creation
- **Button Testing**: All interactive elements verified
- **Regression Testing**: Full test suite confirms no breaking changes

## Benefits

### For Users
- **Clean Interface**: No UI clutter when no updates available
- **User Control**: Explicit approval required for all updates
- **Clear Feedback**: Always know when updates are available
- **Immediate Script Updates**: No restart required for script updates

### For Developers
- **Unified Architecture**: Single codebase for all update logic
- **Consistent Authentication**: HTTPS for both repositories
- **Reliable Versioning**: Git tags provide robust version management
- **Comprehensive Testing**: Automated and manual testing ensures reliability

### For Maintenance
- **Simplified Deployment**: Single update system to maintain
- **Better Security**: Eliminated Google Drive dependency
- **Version Control**: All components tracked in Git
- **Error Visibility**: Clear logging and error reporting

## Migration Notes

### From Previous System

The unified system replaces:
- **Old App Updates**: Google Drive-based distribution
- **Old Script Updates**: Separate script-based system
- **Dual UI**: Two different update interfaces

### Backward Compatibility

- **Update Scripts**: Legacy `update_scripts.*` files still functional
- **Configuration**: No user configuration changes required

## Future Enhancements

### Planned Features
- **Automated Releases**: GitHub Actions for release creation
- **Update Scheduling**: User-configurable update times
- **Rollback Support**: Ability to revert to previous versions
- **Update History**: Log of all applied updates

### Potential Improvements
- **Differential Updates**: Only download changed files
- **Background Updates**: Download updates in background
- **Update Notifications**: Email/desktop notifications for updates
- **Multi-Repository**: Support for additional repositories