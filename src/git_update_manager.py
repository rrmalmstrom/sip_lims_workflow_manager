"""Unified Git-based Update Manager for both scripts and application updates."""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import requests


class GitUpdateManager:
    """Manages updates for public Git repositories using HTTPS."""

    def __init__(self, repo_type: str, repo_path: Path, cache_ttl: int = 1800):
        """
        Initialize Git update manager.

        Args:
            repo_type: Either "scripts" or "application".
            repo_path: Path to the local repository.
            cache_ttl: Cache time-to-live in seconds (default: 30 minutes).
        """
        self.repo_type = repo_type
        self.repo_path = Path(repo_path)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._last_check_time = None

        self.repo_configs = {
            "scripts": {
                "repo_url": "https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git",
                "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
                "current_version_source": "git_tags",
                "fallback_version_source": "commit_hash"
            },
            "application": {
                "repo_url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
                "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                "current_version_source": "env_var",
                "fallback_version_source": "git_tags"
            }
        }

        if repo_type not in self.repo_configs:
            raise ValueError(f"Unknown repo_type: {repo_type}. Must be 'scripts' or 'application'")

        self.config = self.repo_configs[repo_type]


    def _is_cache_valid(self, cache_key: str) -> bool:
        if cache_key not in self._cache:
            return False
        cache_entry = self._cache[cache_key]
        cache_time = cache_entry.get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_ttl

    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        self._cache[cache_key] = {'data': data, 'timestamp': time.time()}

    def _get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        return None

    def get_current_version(self) -> Optional[str]:
        """Get the current version of the repository."""
        source = self.config["current_version_source"]
        
        if source == "env_var":
            version = os.getenv("APP_VERSION")
            if version:
                return version

        if source == "git_tags" or self.config["fallback_version_source"] == "git_tags":
            if not self.repo_path.exists() or not (self.repo_path / ".git").exists():
                return "N/A"
            try:
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--abbrev=0'],
                    cwd=self.repo_path, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip().lstrip('v')
            except Exception as e:
                print(f"Error getting git tag version: {e}")

        if self.config["fallback_version_source"] == "commit_hash":
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=self.repo_path, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return f"commit-{result.stdout.strip()}"
            except Exception as e:
                print(f"Error getting commit hash: {e}")
        
        return None

    def get_latest_release(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Get latest release information from GitHub API."""
        try:
            api_url = f"{self.config['api_url']}/releases/latest"
            response = requests.get(api_url, timeout=timeout)
            if response.status_code == 200:
                release_data = response.json()
                return {
                    'tag_name': release_data.get('tag_name', ''),
                    'name': release_data.get('name', ''),
                    'body': release_data.get('body', ''),
                }
            return None
        except Exception as e:
            print(f"Error fetching latest release: {e}")
            return None

    def compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings (semantic versioning)."""
        try:
            from packaging import version
            return version.parse(latest) > version.parse(current)
        except (ImportError, TypeError):
            # Fallback for simple comparison if packaging is not available or versions are invalid
            return latest > current

    def check_for_updates(self, timeout: int = 10) -> Dict[str, Any]:
        """Check for available updates."""
        cache_key = f"check_updates_{self.repo_type}"
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return cached_result

        result = {'update_available': False, 'current_version': None, 'latest_version': None, 'error': None}
        
        try:
            current_version = self.get_current_version()
            if not current_version:
                result['error'] = "Could not determine current version"
                return result
            result['current_version'] = current_version

            latest_release = self.get_latest_release(timeout)
            if latest_release and latest_release['tag_name']:
                latest_version = latest_release['tag_name'].lstrip('v')
                result['latest_version'] = latest_version
                result['update_available'] = self.compare_versions(current_version, latest_version)
            else:
                result['error'] = "Could not determine latest version from GitHub"

            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            result['error'] = f"Error checking for updates: {str(e)}"
            return result


    def clear_cache(self):
        self._cache.clear()


def create_update_manager(repo_type: str) -> GitUpdateManager:
    """
    Factory function to create an update manager instance with correct paths.
    """
    if repo_type == "scripts":
        # Scripts are in a standardized central location on the host
        repo_path = Path.home() / ".sip_lims_workflow_manager" / "scripts"
    elif repo_type == "application":
        # App version is determined by env var, path is for context if needed
        repo_path = Path(__file__).parent.parent
    else:
        raise ValueError(f"Unknown repo_type: {repo_type}")
    
    return GitUpdateManager(repo_type, repo_path)