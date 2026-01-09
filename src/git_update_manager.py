"""Unified Git-based Update Manager for both scripts and application updates."""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import re
import requests

def get_repository_config(workflow_type: str = None) -> dict:
    """
    Get repository configuration based on workflow type.
    
    Args:
        workflow_type: 'sip' or 'sps-ce' - determines which repository to use
        
    Returns:
        Repository configuration dictionary
    """
    import os
    
    # Determine workflow type from environment if not provided
    if workflow_type is None:
        workflow_type = os.environ.get('WORKFLOW_TYPE', 'sip').lower()
    
    # Validate workflow type
    if workflow_type not in ['sip', 'sps-ce']:
        workflow_type = 'sip'  # Safe fallback for git_update_manager
    
    # Repository configurations for different workflow types
    configs = {
        'sip': {
            "repo_url": "https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git",
            "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
            "update_method": "releases",
            "current_version_source": "git_tags",
            "fallback_version_source": "commit_hash"
        },
        'sps-ce': {
            "repo_url": "https://github.com/rrmalmstrom/SPS_library_creation_scripts.git",
            "api_url": "https://api.github.com/repos/rrmalmstrom/SPS_library_creation_scripts",
            "update_method": "releases",
            "current_version_source": "git_tags",
            "fallback_version_source": "commit_hash"
        }
    }
    
    return configs[workflow_type]

def detect_script_repository_config(script_path: Path) -> dict:
    """
    Detect which script repository configuration to use based on script path.
    This function is kept for backward compatibility but now uses workflow-aware logic.
    
    Args:
        script_path: Path to the script directory
        
    Returns:
        Repository configuration dictionary
    """
    script_path_str = str(script_path).lower()
    
    # Check for SPS-CE workflow indicators in path
    if any(indicator in script_path_str for indicator in ['sps', 'sps-ce', 'sps_scripts']):
        return get_repository_config('sps-ce')
    
    # Check if this is the development repository (SIP)
    if "sip_scripts_dev" in script_path_str:
        return get_repository_config('sip')
    
    # Default to SIP workflow for backward compatibility
    return get_repository_config('sip')

class GitUpdateManager:
    """Unified update manager using Git repositories and GitHub releases."""
    
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
        
        # Repository configuration - both use Git tags for unified approach
        if repo_type == "scripts":
            self.config = detect_script_repository_config(self.repo_path)
        else:
            self.config = {
                "repo_url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
                "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                "update_method": "releases",  # Use GitHub releases
                "current_version_source": "git_tags",  # Get current version from Git tags
                "fallback_version_source": "version_file"  # Fallback to config/version.json if needed
            }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid."""
        if cache_key not in self._cache:
            return False
        
        cache_entry = self._cache[cache_key]
        cache_time = cache_entry.get('timestamp', 0)
        current_time = time.time()
        
        return (current_time - cache_time) < self.cache_ttl
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store data in cache with timestamp."""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache if valid."""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        return None
    
    def get_current_version(self) -> Optional[str]:
        """Get the current version using unified Git-tag approach with fallbacks."""
        try:
            # Primary method: Get current version from Git tags
            if self.config["current_version_source"] == "git_tags":
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--abbrev=0'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    tag = result.stdout.strip()
                    # Remove 'v' prefix if present
                    return tag.lstrip('v')
                
                # If no tags found, try fallback method
                fallback_source = self.config.get("fallback_version_source")
                if fallback_source == "version_file":
                    # Fallback to config/version.json for app repository
                    version_file = self.repo_path.parent / "config" / "version.json"
                    if version_file.exists():
                        with open(version_file, 'r') as f:
                            config = json.load(f)
                            return config.get('version')
                
                elif fallback_source == "commit_hash":
                    # Fallback to commit hash for scripts repository (if no tags)
                    result = subprocess.run(
                        ['git', 'rev-parse', '--short', 'HEAD'],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        commit_hash = result.stdout.strip()
                        return f"commit-{commit_hash}"
            
            return None
        except Exception as e:
            print(f"Error getting current version: {e}")
            return None
    
    def get_latest_release(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Get latest release information from GitHub API."""
        try:
            # For private repos, we might need authentication
            # For now, try without auth (works if repo is public or has public releases)
            api_url = f"{self.config['api_url']}/releases/latest"
            
            response = requests.get(api_url, timeout=timeout)
            
            if response.status_code == 200:
                release_data = response.json()
                return {
                    'tag_name': release_data.get('tag_name', ''),
                    'name': release_data.get('name', ''),
                    'body': release_data.get('body', ''),
                    'published_at': release_data.get('published_at', ''),
                    'assets': release_data.get('assets', []),
                    'zipball_url': release_data.get('zipball_url', ''),
                    'tarball_url': release_data.get('tarball_url', '')
                }
            elif response.status_code == 404:
                # No releases found or private repo without access
                return None
            else:
                print(f"GitHub API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching latest release: {e}")
            return None
    
    def get_latest_tag_via_git(self, timeout: int = 10) -> Optional[str]:
        """
        Get the latest tag from the current branch's remote tracking branch.
        This is branch-aware to prevent feature branches from detecting newer
        tags from the main branch.
        """
        try:
            # 1. Get the remote tracking branch for the current branch
            get_remote_branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if get_remote_branch_result.returncode != 0:
                print("Could not determine remote tracking branch. Falling back to fetching all tags.")
                remote_branch = None
            else:
                remote_branch = get_remote_branch_result.stdout.strip()

            # 2. Fetch tags from the specific remote branch if possible, otherwise all tags
            if remote_branch:
                # e.g., 'origin/sip_mac_solution_no_docker'
                remote_name, branch_name = remote_branch.split('/', 1)
                subprocess.run(
                    ['git', 'fetch', remote_name, f'refs/tags/*:refs/tags/*'],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=timeout
                )
            else:
                subprocess.run(
                    ['git', 'fetch', '--tags'],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=timeout
                )

            # 3. Get the latest tag associated with the remote tracking branch
            # This lists all tags reachable from the tip of the remote branch
            cmd = ['git', 'describe', '--tags', '--abbrev=0']
            if remote_branch:
                cmd.append(remote_branch)

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()

            return None
        except Exception as e:
            print(f"Error getting latest tag via Git: {e}")
            return None
    
    def compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings (semantic versioning)."""
        try:
            # Remove 'v' prefix if present
            current = current.lstrip('v')
            latest = latest.lstrip('v')
            
            # Split versions into parts
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Pad shorter version with zeros
            max_length = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_length - len(current_parts)))
            latest_parts.extend([0] * (max_length - len(latest_parts)))
            
            # Compare each part
            for curr, lat in zip(current_parts, latest_parts):
                if lat > curr:
                    return True
                elif lat < curr:
                    return False
            
            return False  # Versions are equal
            
        except ValueError:
            # Fallback to string comparison
            return latest > current
    
    def check_for_updates(self, timeout: int = 10) -> Dict[str, Any]:
        """Check for available updates."""
        cache_key = f"check_updates_{self.repo_type}"
        
        # Check cache first
        cached_result = self._get_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        result = {
            'update_available': False,
            'current_version': None,
            'latest_version': None,
            'release_info': None,
            'error': None,
            'last_check': None,
            'repo_type': self.repo_type
        }
        
        try:
            # Get current version
            current_version = self.get_current_version()
            if not current_version:
                result['error'] = "Could not determine current version"
                return result
            
            result['current_version'] = current_version
            
            # Try to get latest release via GitHub API first
            latest_release = self.get_latest_release(timeout)
            
            if latest_release:
                # Got release info from API
                latest_version = latest_release['tag_name'].lstrip('v')
                result['latest_version'] = latest_version
                result['release_info'] = latest_release
            else:
                # Fallback to Git tags for private repos
                latest_tag = self.get_latest_tag_via_git(timeout)
                if latest_tag:
                    latest_version = latest_tag.lstrip('v')
                    result['latest_version'] = latest_version
                else:
                    result['error'] = "Could not determine latest version"
                    return result
            
            # Compare versions
            result['update_available'] = self.compare_versions(current_version, latest_version)
            
            # Set last check time
            self._last_check_time = datetime.now()
            result['last_check'] = self._last_check_time
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            result['error'] = f"Error checking for updates: {str(e)}"
            return result
    
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
                # For scripts: fetch latest tags and checkout latest
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
                # For application: this would typically involve downloading and extracting
                # a release package, but for now we'll implement a simple git pull
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
    
    def get_update_details(self, timeout: int = 10) -> Dict[str, Any]:
        """Get detailed information about available updates."""
        result = {
            'commits_behind': 0,
            'commit_messages': [],
            'release_notes': '',
            'error': None
        }
        
        try:
            # First check if updates are available
            update_check = self.check_for_updates(timeout)
            if not update_check['update_available']:
                return result
            
            # If we have release info from GitHub API, use it
            if update_check.get('release_info'):
                release_info = update_check['release_info']
                result['release_notes'] = release_info.get('body', '')
                
                # Try to extract commit count from release notes or use API
                # This is a simplified approach - in practice you might want to use
                # the GitHub API to get commit comparisons
                
            # Fallback: use Git to get commit information
            current_version = update_check['current_version']
            latest_version = update_check['latest_version']
            
            if current_version and latest_version:
                # Get commit log between versions
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', f'v{current_version}..v{latest_version}'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if log_result.returncode == 0:
                    commit_lines = log_result.stdout.strip().split('\n')
                    result['commit_messages'] = [line.strip() for line in commit_lines if line.strip()]
                    result['commits_behind'] = len(result['commit_messages'])
            
            return result
            
        except Exception as e:
            result['error'] = f"Error getting update details: {str(e)}"
            return result
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get timestamp of last update check."""
        return self._last_check_time
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
    
# Factory function for easy instantiation
def create_update_managers(base_path: Path = None, script_path: Path = None, workflow_type: str = None) -> Dict[str, GitUpdateManager]:
    """
    Create update manager instances for both the application and scripts.
    
    Args:
        base_path: Base path for the application (defaults to parent of this file).
        script_path: Path to the active scripts directory.
        workflow_type: Required workflow type ('sip' or 'sps-ce') for script path generation.
        
    Returns:
        A dictionary containing 'app' and 'scripts' GitUpdateManager instances.
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
        
    # 1. Create manager for the application
    app_repo_path = base_path
    app_manager = GitUpdateManager("application", app_repo_path.resolve())
    
    # 2. Create manager for the scripts
    if script_path:
        script_repo_path = script_path
    else:
        # Require workflow_type to be explicitly provided
        if workflow_type is None:
            raise ValueError("workflow_type must be provided when script_path is not specified")
        
        # Validate workflow type
        if workflow_type not in ['sip', 'sps-ce']:
            raise ValueError(f"Invalid workflow_type: {workflow_type}. Must be 'sip' or 'sps-ce'")
        
        # Generate workflow-specific script path
        script_dir_name = f"{workflow_type}_scripts"
        script_repo_path = Path.home() / ".sip_lims_workflow_manager" / script_dir_name
        
    script_manager = GitUpdateManager("scripts", script_repo_path.resolve())
    
    return {
        "app": app_manager,
        "scripts": script_manager
    }


# Example usage
if __name__ == "__main__":
    # Test script update manager
    print("=== Testing Script Update Manager ===")
    script_manager = create_update_manager("scripts")
    
    
    # Check for updates
    update_check = script_manager.check_for_updates()
    print(f"\nUpdate available: {update_check['update_available']}")
    print(f"Current version: {update_check['current_version']}")
    print(f"Latest version: {update_check['latest_version']}")
    
    if update_check['error']:
        print(f"Error: {update_check['error']}")