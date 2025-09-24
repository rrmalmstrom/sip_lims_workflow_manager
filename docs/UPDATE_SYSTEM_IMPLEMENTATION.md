# Update System Implementation Plan

## Overview

This document provides the complete technical specification for implementing the SIP LIMS Workflow Manager update system using Google Drive distribution.

## Architecture Components

### 1. UpdateManager Class (`src/update_manager.py`)

**Purpose**: Handle version checking and update notifications

**Key Methods**:
```python
class UpdateManager:
    def __init__(self, app_dir: Path)
    def load_local_version(self) -> str
    def set_remote_url(self, google_drive_url: str)
    def check_for_updates(self, timeout: int = 10) -> Dict
    def open_download_url(self, download_url: str)
    def _is_newer_version(self, remote_version: str, local_version: str) -> bool
```

**Version Comparison Logic**:
- Handle development versions (9.9.9 always shows updates available)
- Semantic version comparison (1.2.0 vs 1.1.5)
- Graceful fallback for invalid version formats

### 2. GUI Integration (`app.py`)

**Sidebar Notification**:
```python
# Add to sidebar after project selection
if 'update_info' in st.session_state and st.session_state.update_info.get('update_available'):
    update_info = st.session_state.update_info
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 Update Available")
    st.sidebar.markdown(f"**Version {update_info['latest_version']}**")
    
    if st.sidebar.button("📋 View Release Notes"):
        st.session_state.show_release_notes = True
    
    if st.sidebar.button("⬇️ Download Update"):
        update_manager.open_download_url(update_info['download_url'])
        st.sidebar.success("Download started in browser!")
    
    if st.sidebar.button("⏰ Remind Me Later"):
        st.session_state.update_dismissed = True
```

**Startup Check**:
```python
# Add to app startup (after imports)
@st.cache_data(ttl=3600)  # Cache for 1 hour
def check_for_updates():
    update_manager = UpdateManager(Path(__file__).parent)
    update_manager.set_remote_url("GOOGLE_DRIVE_LATEST_JSON_URL")
    return update_manager.check_for_updates()

# In main app logic
if 'update_checked' not in st.session_state:
    st.session_state.update_info = check_for_updates()
    st.session_state.update_checked = True
```

### 3. Release Script (`release.py`)

**Purpose**: Automate the release process

**Workflow**:
1. Prompt for version number with validation
2. Update `config/version.json`
3. Create Git tag
4. Build ZIP file (exclude development files)
5. Generate release notes template
6. Provide instructions for Google Drive upload

**Key Features**:
```python
def main():
    # 1. Version input and validation
    new_version = input("Enter new version (e.g., 1.2.0): ")
    validate_version_format(new_version)
    
    # 2. Update version.json
    update_version_file(new_version)
    
    # 3. Git operations
    git_commit_and_tag(new_version)
    
    # 4. Build release
    create_release_zip(new_version)
    
    # 5. Generate instructions
    print_upload_instructions(new_version)
```

**File Exclusions for ZIP**:
```python
EXCLUDE_PATTERNS = [
    '.git*',
    '__pycache__',
    '.venv',
    '*.pyc',
    '.DS_Store',
    'release.py',
    'docs/development*',
    '.benchmarks'
]
```

## Configuration

### Google Drive URLs

**Setup in app.py**:
```python
# Configuration - replace with actual Google Drive URLs
GOOGLE_DRIVE_CONFIG = {
    "latest_json_url": "https://drive.google.com/uc?id=YOUR_LATEST_JSON_FILE_ID&export=download",
    "download_folder_url": "https://drive.google.com/drive/folders/YOUR_FOLDER_ID"
}
```

### Version File Format

**config/version.json**:
```json
{
  "version": "1.0.0",
  "build_date": "2024-09-24",
  "git_commit": "abc123def"
}
```

**Google Drive latest.json**:
```json
{
  "latest_version": "1.1.0",
  "release_date": "2024-09-24",
  "release_notes": "- Fixed critical bug in workflow execution\n- Added new conditional workflow features",
  "download_url": "https://drive.google.com/uc?id=ZIP_FILE_ID&export=download",
  "filename": "sip_lims_workflow_manager.zip",
  "size_mb": 15,
  "minimum_version": "1.0.0"
}
```

## Error Handling

### Network Issues
- Timeout handling (10 second default)
- Connection error graceful fallback
- Invalid JSON response handling
- Silent failure mode (no user disruption)

### Version Parsing
- Handle malformed version strings
- Development version special cases
- Fallback to "no update available" on errors

### User Experience
- Non-blocking notifications
- Clear error messages when needed
- "Remind me later" functionality
- Browser integration for downloads

## Testing Strategy

### Unit Tests
```python
# test_update_manager.py
def test_version_comparison()
def test_update_check_success()
def test_update_check_network_error()
def test_development_version_handling()
```

### Integration Tests
```python
# test_update_integration.py
def test_gui_notification_display()
def test_download_link_opening()
def test_startup_check_caching()
```

### Manual Testing Checklist
- [ ] Update notification appears correctly
- [ ] Download link opens in browser
- [ ] Release notes display properly
- [ ] "Remind me later" works
- [ ] No updates when current
- [ ] Network failure handling

## Deployment Process

### Initial Setup
1. Create Google Drive folder structure
2. Upload initial release ZIP
3. Create and upload latest.json
4. Get direct download URLs
5. Update app configuration with URLs
6. Test update checking

### Release Workflow
1. Run `python release.py`
2. Follow prompts for version number
3. Upload generated ZIP to Google Drive
4. Update latest.json with new version info
5. Test update notification in app

## Security Considerations

### Google Drive Access
- Use "Anyone with link" permissions (view only)
- Monitor access logs periodically
- Consider dedicated Google account for releases

### Download Verification
- File size validation
- Optional checksum verification
- Clear download instructions for users

## Future Enhancements

### Potential Improvements
- Automatic ZIP upload to Google Drive via API
- In-app update installation (advanced)
- Beta/stable release channels
- Update rollback mechanism
- Usage analytics for update adoption

### API Integration Options
- Google Drive API for automated uploads
- GitHub Releases as alternative distribution
- Webhook notifications for new releases

## Implementation Priority

1. **Phase 1**: Basic update checking and notification
2. **Phase 2**: Release script automation
3. **Phase 3**: Enhanced user experience features
4. **Phase 4**: Advanced automation and API integration

This implementation provides a robust, user-friendly update system that balances simplicity with functionality.