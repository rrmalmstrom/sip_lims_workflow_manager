# Unified Update System Implementation

## Overview

This document describes the implementation of the unified update system for the SIP LIMS Workflow Manager. The system replaces the previous dual update architecture (Google Drive for app updates, separate SSH for script updates) with a single, consistent Git-based approach.

## Architecture Migration

### Previous System (Deprecated)
- **App Updates**: Google Drive distribution with manual download
- **Script Updates**: Separate SSH-based Git system
- **Dual Interface**: Two different update notification systems
- **Inconsistent Authentication**: Google Drive vs SSH keys

### New Unified System
- **Both Updates**: Git-based with SSH authentication
- **Single Interface**: Unified expandable notification system
- **Consistent Authentication**: SSH deploy key for both repositories
- **Clean UI**: Updates only appear when available

## Core Components

### 1. GitUpdateManager Class (`src/git_update_manager.py`)

**Purpose**: Unified update management for both application and script repositories

**Key Methods**:
```python
class GitUpdateManager:
    def __init__(self, repo_type: str, ssh_key_path: str)
    def check_for_updates(self) -> Dict
    def update_to_latest(self) -> Dict
    def get_current_version(self) -> str
    def get_latest_remote_version(self) -> str
```

**Repository Types**:
- `"application"`: sip_lims_workflow_manager repository
- `"scripts"`: sip_scripts_workflow_gui repository

### 2. SSH Key Management (`src/ssh_key_manager.py`)

**Purpose**: Secure SSH key validation and management

**Security Features**:
- Ed25519 key type validation
- File permission verification (600)
- Repository access testing
- Comprehensive error reporting

### 3. Clean UI Integration (`app.py`)

**Smart Notification System**:
```python
# Only shows when updates are available
if updates_available:
    st.info("🔔 **Updates Available** - Check the expandable section below")
    
    with st.expander("📦 Available Updates", expanded=False):
        col1, col2 = st.columns(2)
        # App updates (left) | Script updates (right)
```

## Configuration

### Repository Configuration
```python
REPOSITORIES = {
    "application": {
        "ssh_url": "git@github.com:rrmalmstrom/sip_lims_workflow_manager.git",
        "github_api": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
        "local_path": "."
    },
    "scripts": {
        "ssh_url": "git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git",
        "github_api": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui", 
        "local_path": "../sip_scripts_workflow_gui"
    }
}
```

### SSH Key Setup
```bash
# Key location
~/.ssh/sip_workflow_key

# Required permissions
chmod 600 ~/.ssh/sip_workflow_key

# Recommended key type
ssh-keygen -t ed25519 -f ~/.ssh/sip_workflow_key
```

## Version Management

### Git Tag Versioning
Both repositories use semantic versioning with Git tags:
- **Application**: v1.0.2, v1.1.0, v2.0.0
- **Scripts**: v1.0.0, v1.0.1, v1.1.0

### Version Detection
```python
# GitHub API primary method
latest_version = get_latest_release_from_github_api()

# SSH Git fallback method  
if not latest_version:
    latest_version = get_latest_tag_via_ssh()
```

## User Interface

### Clean, Non-Intrusive Design

**Principles**:
- No persistent UI clutter
- Updates only appear when available
- Expandable details on demand
- Clear user control

**Interface Flow**:
1. **Automatic Detection**: Checks every 60 minutes + on page refresh
2. **Smart Notification**: "🔔 Updates Available" appears when needed
3. **Expandable Details**: Click to reveal side-by-side layout
4. **User Action**: Explicit approval required for all updates

### Update Types

**Application Updates**:
- Manual download from GitHub releases
- Requires application restart
- Contains: GUI improvements, new features, bug fixes

**Script Updates**:
- One-click in-app update
- No restart required
- Contains: Scientific workflows, analysis methods, script fixes

## Error Handling

### Comprehensive Error Management

**SSH Key Issues**:
- Missing key file detection
- Permission validation (must be 600)
- Key type verification (Ed25519 recommended)
- Repository access testing

**Network Issues**:
- GitHub API timeout handling
- SSH connection failure recovery
- DNS resolution problems
- Graceful degradation

**Git Issues**:
- Repository not found
- Invalid tag formats
- Merge conflict detection
- Authentication failures

## Testing Strategy

### Automated Testing
- **13 Integration Tests**: Complete unified system coverage
- **Mock Testing**: Simulates all update scenarios
- **Error Testing**: Validates error handling paths
- **Cache Testing**: Verifies 60-minute caching behavior

### Manual Testing
- **Interactive UI**: Test interface for user validation
- **Real Updates**: Tested with actual Git tag creation
- **Button Testing**: All interactive elements verified
- **Regression Testing**: 153/154 tests passing

## Security Considerations

### SSH Security
- **Deploy Key**: Read-only access to repositories
- **Key Validation**: Automated security checks
- **Permission Enforcement**: Strict file permission requirements
- **Access Logging**: SSH operations are logged

### Network Security
- **HTTPS API**: GitHub API uses HTTPS
- **SSH Encryption**: All Git operations over SSH
- **Timeout Protection**: All operations have timeouts
- **Error Isolation**: Update failures don't affect main app

## Migration from Previous System

### Deprecated Components
- ~~Google Drive distribution~~
- ~~Dual update interfaces~~
- ~~Manual version.json management~~ (Now uses Git tags only)
- ~~Separate authentication systems~~

### Backward Compatibility
- **SSH Keys**: Existing keys continue to work
- **Update Scripts**: Legacy files still functional
- **No User Changes**: No configuration changes required

### Migration Benefits
- **Unified Authentication**: Single SSH key for both repositories
- **Consistent Versioning**: Git tags for both repositories
- **Cleaner Interface**: No persistent update clutter
- **Better Security**: Eliminated Google Drive dependency

## Performance Optimization

### Caching Strategy
```python
@st.cache_data(ttl=3600)  # 60-minute cache
def check_for_app_updates():
    # Cached to prevent excessive API calls
    
@st.cache_data(ttl=3600)  # 60-minute cache  
def check_for_script_updates():
    # Cached to prevent excessive Git operations
```

### Efficient Operations
- **GitHub API Primary**: Fast API calls for version checking
- **SSH Fallback**: Only when API fails
- **Smart Caching**: Prevents redundant operations
- **Background Checks**: Non-blocking update detection

## Future Enhancements

### Planned Features
- **Automated Releases**: GitHub Actions for release creation
- **Update Scheduling**: User-configurable check intervals
- **Rollback Support**: Ability to revert to previous versions
- **Update History**: Log of all applied updates

### Advanced Features
- **Differential Updates**: Only download changed files
- **Background Downloads**: Pre-download updates
- **Multi-Branch Support**: Support for beta/stable channels
- **Notification System**: Email/desktop notifications

## Implementation Checklist

### Phase 1: Core Implementation ✅
- [x] GitUpdateManager class
- [x] SSH key management
- [x] Version detection via Git tags
- [x] Basic error handling

### Phase 2: UI Integration ✅
- [x] Clean notification system
- [x] Expandable update interface
- [x] User-controlled updates
- [x] Cache management

### Phase 3: Testing & Validation ✅
- [x] Comprehensive test suite
- [x] Manual UI testing
- [x] Real update verification
- [x] Regression testing

### Phase 4: Documentation ✅
- [x] Technical documentation
- [x] User guide updates
- [x] Migration notes
- [x] Security guidelines

## Conclusion

The unified update system provides a consistent, secure, and user-friendly approach to managing both application and script updates. By eliminating the Google Drive dependency and unifying on Git-based distribution, the system offers better security, reliability, and user experience while maintaining the flexibility to update components independently.

The clean, non-intrusive interface ensures users are informed about updates without cluttering the interface, and the comprehensive testing ensures reliability and backward compatibility.