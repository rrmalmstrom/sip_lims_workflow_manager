"""Unified Git-based Update Manager for both scripts and application updates."""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import re
import requests

from .ssh_key_manager import SSHKeyManager


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
        
        # Initialize SSH key manager with appropriate key for repo type
        key_name = "scripts_deploy_key" if repo_type == "scripts" else "app_deploy_key"
        self.ssh_manager = SSHKeyManager(key_name=key_name)
        
        # Repository configuration - both use Git tags for unified approach
        self.repo_configs = {
            "scripts": {
                "repo_url": "git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git",
                "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
                "update_method": "releases",  # Use GitHub releases
                "current_version_source": "git_tags",  # Get current version from Git tags
                "fallback_version_source": "commit_hash"  # Fallback if no tags exist
            },
            "application": {
                "repo_url": "git@github.com:rrmalmstrom/sip_lims_workflow_manager.git",
                "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                "update_method": "releases",  # Use GitHub releases
                "current_version_source": "git_tags",  # Get current version from Git tags
                "fallback_version_source": "version_file"  # Fallback to config/version.json if needed
            }
        }
        
        if repo_type not in self.repo_configs:
            raise ValueError(f"Unknown repo_type: {repo_type}. Must be 'scripts' or 'application'")
        
        self.config = self.repo_configs[repo_type]
    
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
                env = self.ssh_manager.create_git_env()
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--abbrev=0'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env
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
        """Get latest tag using Git (fallback for private repos)."""
        try:
            env = self.ssh_manager.create_git_env()
            
            # Fetch latest tags
            subprocess.run(
                ['git', 'fetch', '--tags'],
                cwd=self.repo_path,
                capture_output=True,
                timeout=timeout,
                env=env
            )
            
            # Get latest tag
            result = subprocess.run(
                ['git', 'tag', '--sort=-version:refname'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                tags = result.stdout.strip().split('\n')
                if tags and tags[0]:
                    return tags[0].strip()
            
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
            
            env = self.ssh_manager.create_git_env()
            
            if self.repo_type == "scripts":
                # For scripts: fetch latest tags and checkout latest
                # Fetch all tags
                fetch_result = subprocess.run(
                    ['git', 'fetch', '--tags'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env
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
                    timeout=timeout,
                    env=env
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
                env = self.ssh_manager.create_git_env()
                
                # Get commit log between versions
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', f'v{current_version}..v{latest_version}'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env
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
    
    def validate_setup(self) -> Dict[str, Any]:
        """Validate that the update system is properly configured."""
        result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Validate SSH key setup
        ssh_validation = self.ssh_manager.validate_key_security()
        if not ssh_validation['valid']:
            result['valid'] = False
            result['issues'].extend([f"SSH: {issue}" for issue in ssh_validation['issues']])
        
        result['warnings'].extend([f"SSH: {warning}" for warning in ssh_validation['warnings']])
        
        # Validate repository setup
        if not self.repo_path.exists():
            result['valid'] = False
            result['issues'].append(f"Repository path does not exist: {self.repo_path}")
        elif not (self.repo_path / ".git").exists():
            result['valid'] = False
            result['issues'].append(f"Not a Git repository: {self.repo_path}")
        
        # Test repository access
        repo_url = self.config['repo_url']
        access_test = self.ssh_manager.test_key_access(repo_url)
        if not access_test['success']:
            result['valid'] = False
            result['issues'].append(f"Cannot access repository: {access_test['error']}")
        
        # Validate version source
        current_version = self.get_current_version()
        if not current_version:
            result['warnings'].append("Could not determine current version")
        
        return result


# Factory function for easy instantiation
def create_update_manager(repo_type: str, base_path: Path = None) -> GitUpdateManager:
    """
    Create an appropriate update manager instance.
    
    Args:
        repo_type: Either "scripts" or "application"
        base_path: Base path for the application (defaults to parent of this file)
    
    Returns:
        GitUpdateManager instance
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    if repo_type == "scripts":
        repo_path = base_path / "scripts"
    elif repo_type == "application":
        repo_path = base_path
    else:
        raise ValueError(f"Unknown repo_type: {repo_type}")
    
    return GitUpdateManager(repo_type, repo_path)


# Example usage
if __name__ == "__main__":
    # Test script update manager
    print("=== Testing Script Update Manager ===")
    script_manager = create_update_manager("scripts")
    
    validation = script_manager.validate_setup()
    print(f"Setup valid: {validation['valid']}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  ❌ {issue}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️ {warning}")
    
    # Check for updates
    update_check = script_manager.check_for_updates()
    print(f"\nUpdate available: {update_check['update_available']}")
    print(f"Current version: {update_check['current_version']}")
    print(f"Latest version: {update_check['latest_version']}")
    
    if update_check['error']:
        print(f"Error: {update_check['error']}")