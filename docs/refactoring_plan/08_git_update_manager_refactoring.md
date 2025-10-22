# 08 - Git Update Manager Refactoring for External Scripts

## Overview
Plan for refactoring `src/git_update_manager.py` to support external script repositories while maintaining all existing functionality for application updates.

## Current Git Update Manager Analysis

### Key Areas Requiring Modification
- **Line 473**: `repo_path = base_path / "scripts"` - Hardcoded nested path
- **Line 33**: Hardcoded repository URL for scripts
- **Line 458**: `create_update_manager()` factory function needs script_path parameter
- **Lines 32-37**: Repository configuration for scripts needs to be dynamic

### Current Repository Configuration
```python
# Current hardcoded configuration (Lines 32-37)
"scripts": {
    "repo_url": "https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git",
    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
    "update_method": "releases",
    "current_version_source": "git_tags",
    "fallback_version_source": "commit_hash"
}
```

## Required Modifications

### 1. Modify Factory Function to Accept Script Path
```python
# MODIFIED: create_update_manager function (Line 458)
def create_update_manager(repo_type: str, base_path: Path = None, script_path: Path = None) -> GitUpdateManager:
    """
    Create an appropriate update manager instance.
    
    Args:
        repo_type: Either "scripts" or "application"
        base_path: Base path for the application (defaults to parent of this file)
        script_path: Path to scripts directory (for script updates only)
    
    Returns:
        GitUpdateManager instance
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    if repo_type == "scripts":
        if script_path:
            repo_path = script_path
        else:
            # Default to external production scripts
            repo_path = base_path.parent / "sip_scripts_production"
    elif repo_type == "application":
        repo_path = base_path
    else:
        raise ValueError(f"Unknown repo_type: {repo_type}")
    
    return GitUpdateManager(repo_type, repo_path)
```

### 2. Dynamic Repository Configuration
```python
# NEW: Add repository detection function
def detect_script_repository_config(script_path: Path) -> dict:
    """
    Detect which script repository configuration to use based on script path.
    
    Args:
        script_path: Path to the script directory
        
    Returns:
        Repository configuration dictionary
    """
    script_path_str = str(script_path).lower()
    
    # Check if this is the development repository
    if "workflow_gui" in script_path_str or "sip_scripts_workflow_gui" in script_path_str:
        return {
            "repo_url": "https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git",
            "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
            "update_method": "releases",
            "current_version_source": "git_tags",
            "fallback_version_source": "commit_hash"
        }
    
    # Default to production repository
    return {
        "repo_url": "https://github.com/rrmalmstrom/sip_scripts_production.git",
        "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_production",
        "update_method": "releases",
        "current_version_source": "git_tags",
        "fallback_version_source": "commit_hash"
    }

# MODIFIED: GitUpdateManager constructor
class GitUpdateManager:
    def __init__(self, repo_type: str, repo_path: Path, cache_ttl: int = 1800):
        """
        Initialize Git update manager.
        
        Args:
            repo_type: Either "scripts" or "application"
            repo_path: Path to the local repository
            cache_ttl: Cache time-to-live in seconds (default: 30 minutes)
        """
        self.repo_type = repo_type
        self.repo_path = Path(repo_path)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._last_check_time = None
        
        # MODIFIED: Dynamic repository configuration
        if repo_type == "scripts":
            # Detect configuration based on actual script path
            script_config = detect_script_repository_config(self.repo_path)
            self.repo_configs = {
                "scripts": script_config,
                "application": {
                    "repo_url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "version_file"
                }
            }
        else:
            # Application updates use static configuration
            self.repo_configs = {
                "scripts": {
                    "repo_url": "https://github.com/rrmalmstrom/sip_scripts_production.git",
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_production",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "commit_hash"
                },
                "application": {
                    "repo_url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "version_file"
                }
            }
        
        if repo_type not in self.repo_configs:
            raise ValueError(f"Unknown repo_type: {repo_type}. Must be 'scripts' or 'application'")
        
        self.config = self.repo_configs[repo_type]
```

### 3. Enhanced Script Repository Detection
```python
# NEW: Add more sophisticated repository detection
def get_repository_info_from_path(script_path: Path) -> dict:
    """
    Get repository information by examining the actual git repository.
    
    Args:
        script_path: Path to the script directory
        
    Returns:
        Dictionary with repository information
    """
    try:
        # Check if this is a git repository
        git_dir = script_path / ".git"
        if not git_dir.exists():
            # Not a git repo, use path-based detection
            return detect_script_repository_config(script_path)
        
        # Get remote URL from git
        import subprocess
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=script_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            
            # Parse repository information from URL
            if "sip_scripts_workflow_gui" in remote_url:
                return {
                    "repo_url": remote_url,
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "commit_hash"
                }
            elif "sip_scripts_production" in remote_url:
                return {
                    "repo_url": remote_url,
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_production",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "commit_hash"
                }
        
        # Fallback to path-based detection
        return detect_script_repository_config(script_path)
        
    except Exception as e:
        print(f"Warning: Could not detect repository info: {e}")
        return detect_script_repository_config(script_path)
```

### 4. Update Script Update Logic for External Repositories
```python
# MODIFIED: update_to_latest method for scripts (Line 331)
def update_to_latest(self, timeout: int = 60) -> Dict[str, Any]:
    """Update to the latest version."""
    result = {
        'success': False,
        'error': None,
        'message': 'Update not attempted',
        'old_version': None,
        'new_version': None
    }
    
    try:
        # Get current version before update
        result['old_version'] = self.get_current_version()
        
        # Check if repository exists and is a Git repo
        if not self.repo_path.exists():
            result['error'] = f"Repository path does not exist: {self.repo_path}"
            return result
        
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            result['error'] = f"Not a Git repository: {self.repo_path}"
            return result
        
        if self.repo_type == "scripts":
            # ENHANCED: For scripts, handle external repository updates
            # Fetch all tags
            fetch_result = subprocess.run(
                ['git', 'fetch', '--tags'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if fetch_result.returncode != 0:
                result['error'] = f"Git fetch failed: {fetch_result.stderr}"
                return result
            
            # Get latest tag
            latest_tag = self.get_latest_tag_via_git()
            if not latest_tag:
                result['error'] = "No tags found in repository"
                return result
            
            # Checkout latest tag
            checkout_result = subprocess.run(
                ['git', 'checkout', latest_tag],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if checkout_result.returncode == 0:
                result['success'] = True
                result['new_version'] = latest_tag.lstrip('v')
                result['message'] = f"Updated scripts to version {result['new_version']}"
            else:
                result['error'] = f"Git checkout failed: {checkout_result.stderr}"
        
        elif self.repo_type == "application":
            # UNCHANGED: Application update logic remains the same
            pull_result = subprocess.run(
                ['git', 'pull'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if pull_result.returncode == 0:
                result['success'] = True
                result['new_version'] = self.get_current_version()
                result['message'] = f"Updated application to version {result['new_version']}"
            else:
                result['error'] = f"Git pull failed: {pull_result.stderr}"
        
        # Clear cache after successful update
        if result['success']:
            self.clear_cache()
            self._last_check_time = datetime.now()
        
        return result
        
    except subprocess.TimeoutExpired:
        result['error'] = f"Update operation timed out after {timeout} seconds"
        return result
    except Exception as e:
        result['error'] = f"Unexpected error during update: {str(e)}"
        return result
```

## Test Specifications (TDD)

### Test Cases
```python
# Test 1: Factory function with script path
def test_create_update_manager_with_script_path():
    # Given: script_path points to external directory
    # When: create_update_manager("scripts", script_path=external_path) is called
    # Then: should create manager with external path
    # And: should detect correct repository configuration

def test_create_update_manager_default_script_path():
    # Given: no script_path provided
    # When: create_update_manager("scripts") is called
    # Then: should default to ../sip_scripts_production

# Test 2: Repository detection
def test_repository_detection_workflow_gui():
    # Given: script_path contains "workflow_gui"
    # When: repository config is detected
    # Then: should use workflow_gui repository URL

def test_repository_detection_production():
    # Given: script_path contains "production" or is default
    # When: repository config is detected
    # Then: should use production repository URL

def test_repository_detection_from_git():
    # Given: script_path is a git repository
    # When: repository info is detected from git remote
    # Then: should use actual remote URL for configuration

# Test 3: Update operations
def test_script_update_external_repository():
    # Given: update manager configured for external script repository
    # When: update_to_latest() is called
    # Then: should update external repository correctly
    # And: should not affect application repository

def test_application_update_unchanged():
    # Given: application update manager
    # When: update_to_latest() is called
    # Then: should work exactly as before (no changes)

# Test 4: Error handling
def test_missing_external_repository():
    # Given: script_path points to non-existent directory
    # When: update operations are attempted
    # Then: should provide clear error messages
    # And: should not crash the application
```

## Integration Points

### With App.py
- App.py calls `create_update_manager("scripts", script_path=SCRIPT_PATH)`
- Update manager uses provided script_path for all operations
- Application update manager unchanged

### With Setup Scripts
- Setup scripts create external script repositories
- Update manager operates on these external repositories
- No changes needed to setup script update logic

### With UI Components
- Update UI shows correct repository information
- Version information reflects external repository state
- Update buttons trigger external repository updates

## Error Handling Strategy

### Missing External Repository
```python
def validate_script_repository(self) -> bool:
    """
    Validate that the script repository is properly configured.
    
    Returns:
        True if repository is valid, False otherwise
    """
    if not self.repo_path.exists():
        print(f"Error: Script repository not found: {self.repo_path}")
        return False
    
    git_dir = self.repo_path / ".git"
    if not git_dir.exists():
        print(f"Error: Not a git repository: {self.repo_path}")
        return False
    
    return True

def get_fallback_update_info(self) -> dict:
    """
    Provide fallback update information when repository is not available.
    
    Returns:
        Update info dictionary with appropriate error message
    """
    return {
        'update_available': False,
        'current_version': 'Unknown',
        'latest_version': 'Unknown',
        'error': f"Script repository not available: {self.repo_path}",
        'repo_type': self.repo_type
    }
```

### Repository Configuration Errors
```python
def handle_repository_config_error(self, error: Exception) -> dict:
    """
    Handle errors in repository configuration detection.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Safe fallback configuration
    """
    print(f"Warning: Repository configuration error: {error}")
    print("Using default production repository configuration")
    
    return {
        "repo_url": "https://github.com/rrmalmstrom/sip_scripts_production.git",
        "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_production",
        "update_method": "releases",
        "current_version_source": "git_tags",
        "fallback_version_source": "commit_hash"
    }
```

## Backward Compatibility

### Legacy Support
```python
# Ensure backward compatibility for existing calls
def create_update_manager(repo_type: str, base_path: Path = None, script_path: Path = None) -> GitUpdateManager:
    """
    Create update manager with backward compatibility.
    
    Legacy calls without script_path will continue to work.
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    if repo_type == "scripts" and script_path is None:
        # Legacy behavior: check for nested scripts first
        nested_scripts = base_path / "scripts"
        if nested_scripts.exists():
            script_path = nested_scripts
        else:
            # New behavior: default to external production scripts
            script_path = base_path.parent / "sip_scripts_production"
    
    # ... rest of function
```

### Migration Support
```python
def get_update_source_info(self) -> dict:
    """
    Get information about update source for debugging.
    
    Returns:
        Dictionary with update source information
    """
    return {
        'repo_type': self.repo_type,
        'repo_path': str(self.repo_path),
        'repo_url': self.config.get('repo_url', 'Unknown'),
        'is_external': not str(self.repo_path).endswith('/scripts'),
        'config_source': 'dynamic' if self.repo_type == 'scripts' else 'static'
    }
```

## Benefits

### For Developers
- ✅ Can update different script repositories independently
- ✅ Clear visibility into which repository is being updated
- ✅ Automatic detection of repository configuration
- ✅ Support for both development and production script repositories

### For Production Users
- ✅ Automatic updates from production script repository
- ✅ No changes to update user experience
- ✅ Reliable, consistent update behavior
- ✅ Clear error messages if update issues occur

### For Maintenance
- ✅ Dynamic repository configuration
- ✅ Backward compatibility preserved
- ✅ Clear separation between script and application updates
- ✅ Comprehensive error handling and fallbacks

## Implementation Strategy

### Phase 1: Modify Factory Function
- Add script_path parameter to create_update_manager
- Test with both provided and default script paths
- Ensure backward compatibility

### Phase 2: Implement Dynamic Configuration
- Add repository detection functions
- Test configuration detection for different script paths
- Verify correct repository URLs are used

### Phase 3: Update Script Update Logic
- Modify update operations for external repositories
- Test script updates from external locations
- Ensure application updates unchanged

### Phase 4: Enhanced Error Handling
- Add comprehensive validation and error handling
- Implement fallback mechanisms
- Test error scenarios and recovery

This refactoring enables the update system to work with external script repositories while maintaining all existing functionality for application updates and providing clear error handling for various scenarios.