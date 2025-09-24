"""Script Update Manager for SIP LIMS Workflow Manager."""

import subprocess
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import time


class ScriptUpdateManager:
    """Manages checking and updating workflow scripts from Git repository."""
    
    def __init__(self, scripts_dir: Path, cache_ttl: int = 1800):
        """Initialize the ScriptUpdateManager."""
        self.scripts_dir = Path(scripts_dir)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._last_check_time = None
    
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
    
    def check_for_updates(self, timeout: int = 10) -> Dict[str, Any]:
        """Check if script repository has updates available."""
        cache_key = "check_updates"
        
        # Check cache first
        cached_result = self._get_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        result = {
            'update_available': False,
            'error': None,
            'status_message': 'Unknown status',
            'last_check': None
        }
        
        try:
            # Check if it's a Git repository
            git_dir = self.scripts_dir / ".git"
            if not (git_dir.exists() and git_dir.is_dir()):
                result['error'] = "Scripts directory is not a Git repository"
                result['status_message'] = "Error: Not a Git repository"
                return result
            
            # Fetch latest changes from remote
            fetch_result = subprocess.run(
                ['git', 'fetch'],
                cwd=self.scripts_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if fetch_result.returncode != 0:
                result['error'] = "Network error: Unable to check for updates"
                result['status_message'] = "Error checking for updates"
                return result
            
            # Check status to see if we're behind
            status_result = subprocess.run(
                ['git', 'status', '-uno'],
                cwd=self.scripts_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if status_result.returncode != 0:
                result['error'] = f"Git status failed: {status_result.stderr.strip()}"
                result['status_message'] = "Error checking status"
                return result
            
            status_output = status_result.stdout.strip()
            
            # Parse status output
            if 'Your branch is behind' in status_output:
                result['update_available'] = True
                result['status_message'] = status_output
            else:
                result['update_available'] = False
                result['status_message'] = "Your branch is up to date"
            
            # Set last check time
            self._last_check_time = datetime.now()
            result['last_check'] = self._last_check_time
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            return result
            
        except subprocess.TimeoutExpired:
            result['error'] = f"Git operation timeout after {timeout} seconds"
            result['status_message'] = "Timeout checking for updates"
            return result
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            result['status_message'] = "Error checking for updates"
            return result
    
    def update_scripts(self, timeout: int = 30) -> Dict[str, Any]:
        """Update scripts by pulling from remote repository."""
        result = {
            'success': False,
            'error': None,
            'message': 'Update not attempted'
        }
        
        try:
            # Check if it's a Git repository
            git_dir = self.scripts_dir / ".git"
            if not (git_dir.exists() and git_dir.is_dir()):
                result['error'] = "Scripts directory is not a Git repository"
                result['message'] = "Error: Not a Git repository"
                return result
            
            # Perform git pull
            pull_result = subprocess.run(
                ['git', 'pull'],
                cwd=self.scripts_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if pull_result.returncode == 0:
                result['success'] = True
                result['message'] = "Scripts updated successfully"
                
                # Clear cache after successful update
                self.clear_cache()
                
                # Update last check time
                self._last_check_time = datetime.now()
            else:
                result['error'] = pull_result.stderr.strip()
                result['message'] = "Failed to update scripts"
            
            return result
            
        except subprocess.TimeoutExpired:
            result['error'] = f"Git pull timed out after {timeout} seconds"
            result['message'] = "Update timed out"
            return result
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            result['message'] = "Update failed"
            return result
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get timestamp of last update check."""
        return self._last_check_time
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
    
    def get_update_details(self, timeout: int = 10) -> Dict[str, Any]:
        """Get details about available updates."""
        result = {
            'commits_behind': 0,
            'commit_messages': [],
            'error': None
        }
        
        try:
            update_check = self.check_for_updates(timeout)
            if not update_check['update_available']:
                return result
            
            # Get number of commits behind
            status_output = update_check['status_message']
            if 'behind' in status_output:
                words = status_output.split()
                for i, word in enumerate(words):
                    if word == 'by' and i + 1 < len(words):
                        try:
                            result['commits_behind'] = int(words[i + 1])
                            break
                        except ValueError:
                            pass
            
            # Get commit messages
            if result['commits_behind'] > 0:
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', f'-{result["commits_behind"]}', 'origin/main'],
                    cwd=self.scripts_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if log_result.returncode == 0:
                    commit_lines = log_result.stdout.strip().split('\n')
                    result['commit_messages'] = [line.strip() for line in commit_lines if line.strip()]
            
            return result
            
        except Exception as e:
            result['error'] = f"Error getting update details: {str(e)}"
            return result