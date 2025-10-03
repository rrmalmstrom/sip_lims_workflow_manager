# SSH Key Architecture Fix Documentation

## Overview

This document describes the comprehensive fix implemented to resolve SSH key authentication issues in the SIP LIMS Workflow Manager. The solution addresses multiple problems including SSH key permissions, repository access conflicts, and update manager functionality.

## Problem Summary

### Original Issues
1. **SSH Key Permissions Error**: `permissions 0664 for '.ssh/deploy_key' are too open`
2. **Repository Access Conflicts**: Single SSH key trying to access multiple repositories
3. **GitHub Deploy Key Limitations**: One deploy key per repository restriction
4. **Update Manager Inconsistencies**: Different managers using different SSH key approaches

### Root Causes
1. **Incorrect File Permissions**: SSH keys copied with wrong permissions (0664 instead of 0600)
2. **Single Key Architecture**: One `deploy_key` attempting to access two different repositories
3. **Hardcoded Key Paths**: Update managers hardcoded to use old key names
4. **GitHub Deploy Key Conflicts**: Original key tied to deleted repository causing "key already in use" errors

## Solution Architecture

### New SSH Key Structure
```
.ssh/
├── scripts_deploy_key      # Private key for scripts repository (0600)
├── scripts_deploy_key.pub  # Public key for scripts repository (0644)
├── app_deploy_key          # Private key for app repository (0600)
├── app_deploy_key.pub      # Public key for app repository (0644)
└── deploy_key              # Legacy key (kept for compatibility)
```

### Repository Mapping
- **Scripts Repository** (`sip_scripts_workflow_gui`) → `scripts_deploy_key`
- **Application Repository** (`sip_lims_workflow_manager`) → `app_deploy_key`

## Implementation Details

### 1. SSH Key Manager Updates

**File**: `src/ssh_key_manager.py`

**Changes**:
- Added `key_name` parameter to constructor
- Dynamic key path generation based on key name
- Maintains backward compatibility with default `deploy_key`

```python
def __init__(self, ssh_dir: Path = None, key_name: str = "deploy_key"):
    self.key_name = key_name
    self.private_key_path = self.ssh_dir / key_name
    self.public_key_path = self.ssh_dir / f"{key_name}.pub"
```

### 2. Git Update Manager Updates

**File**: `src/git_update_manager.py`

**Changes**:
- Repository-specific SSH key selection
- Automatic key mapping based on repository type

```python
# Initialize SSH key manager with appropriate key for repo type
key_name = "scripts_deploy_key" if repo_type == "scripts" else "app_deploy_key"
self.ssh_manager = SSHKeyManager(key_name=key_name)
```

### 3. Setup Script Updates

**File**: `setup.command`

**Changes**:
- Updated to use `scripts_deploy_key` instead of `deploy_key`
- Automatic permission setting: `chmod 600 .ssh/scripts_deploy_key`
- Absolute path usage for reliability

```bash
echo "Setting up SSH key permissions..."
chmod 600 "$DIR/.ssh/scripts_deploy_key"
```

### 4. Deploy Key Generation

**New SSH Keys Generated**:
```bash
# Scripts repository key
ssh-keygen -t ed25519 -f .ssh/scripts_deploy_key -C "scripts-repo-deploy-key" -N ""

# Application repository key  
ssh-keygen -t ed25519 -f .ssh/app_deploy_key -C "app-repo-deploy-key" -N ""
```

**Public Keys Added to GitHub**:
- Scripts repo: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMKyZQ+gAQswdTuANYKKDSZY4DazcFifHqYJ9WEE1fzU`
- App repo: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAuSH6DHZ+wCMo/9hlQjinj8YhpirdeONueqAjPpzysE`

## Testing and Validation

### Automated Test Suite

**File**: `test_ssh_key_architecture_fix.py`

**Test Coverage**:
- SSH key manager supports multiple keys
- Git update manager uses correct keys per repository
- SSH command generation uses correct key paths
- Git environment variables point to correct keys
- Repository configuration mapping
- Real-world integration tests

**Test Results**: ✅ All 10 tests passed

### Manual Verification

**Verified Functionality**:
1. ✅ Setup process completes without SSH errors
2. ✅ "Check for App Updates" button works correctly
3. ✅ "Check for Script Updates" button works correctly
4. ✅ "Update Scripts" button successfully pulls from repository

## Security Improvements

### File Permissions
- **Private Keys**: 0600 (owner read/write only)
- **Public Keys**: 0644 (owner read/write, group/other read)
- **SSH Directory**: 0700 (owner access only)

### Key Security
- **Algorithm**: Ed25519 (modern, secure)
- **Key Separation**: Dedicated keys per repository
- **Access Control**: Deploy keys with read-only repository access

## Troubleshooting

### Common Issues

**1. Permission Denied Errors**
```bash
# Fix: Ensure correct permissions
chmod 600 .ssh/scripts_deploy_key
chmod 600 .ssh/app_deploy_key
```

**2. Repository Not Found**
```bash
# Fix: Test SSH key access
ssh -T -i .ssh/scripts_deploy_key git@github.com
```

**3. Key Already in Use**
- Remove old deploy keys from GitHub repositories
- Generate new keys if needed
- Ensure unique keys per repository

### Validation Commands

**Check SSH Key Permissions**:
```bash
ls -la .ssh/
# Should show: -rw------- for private keys
```

**Test Repository Access**:
```bash
# Test scripts repository
GIT_SSH_COMMAND="ssh -i .ssh/scripts_deploy_key" git ls-remote git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git

# Test app repository  
GIT_SSH_COMMAND="ssh -i .ssh/app_deploy_key" git ls-remote git@github.com:rrmalmstrom/sip_lims_workflow_manager.git
```

**Run Test Suite**:
```bash
python3 test_ssh_key_architecture_fix.py
```

## Migration Guide

### For New Installations
1. Run `./setup.command` - automatically uses new key architecture
2. No additional steps required

### For Existing Installations
1. Generate new SSH keys (if not already done)
2. Add deploy keys to GitHub repositories
3. Update code to latest version with SSH key fixes
4. Test functionality using validation commands

## Files Modified

### Core Changes
- `src/ssh_key_manager.py` - Added multi-key support
- `src/git_update_manager.py` - Repository-specific key selection
- `setup.command` - Updated to use new keys and fix permissions

### New Files
- `test_ssh_key_architecture_fix.py` - Comprehensive test suite
- `docs/SSH_KEY_ARCHITECTURE_FIX.md` - This documentation

### SSH Keys
- `.ssh/scripts_deploy_key` - New private key for scripts repository
- `.ssh/scripts_deploy_key.pub` - New public key for scripts repository
- `.ssh/app_deploy_key` - New private key for app repository
- `.ssh/app_deploy_key.pub` - New public key for app repository

## Future Considerations

### Maintenance
- Monitor SSH key expiration (Ed25519 keys don't expire but GitHub access tokens might)
- Regular security audits of key permissions
- Consider key rotation policies for enhanced security

### Enhancements
- Automated key rotation system
- Enhanced error reporting for SSH issues
- Integration with CI/CD pipelines for automated testing

## Conclusion

The SSH key architecture fix provides a robust, secure, and maintainable solution for repository access. The implementation follows security best practices, includes comprehensive testing, and maintains backward compatibility where possible.

**Key Benefits**:
- ✅ Resolves all SSH permission and access issues
- ✅ Provides dedicated keys per repository for better security
- ✅ Includes comprehensive test coverage
- ✅ Maintains system functionality and user experience
- ✅ Follows security best practices

The fix has been thoroughly tested and verified to work correctly across all system components.