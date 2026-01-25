#!/usr/bin/env python3
"""
Git Repository Update Detection System

This module provides functionality to detect updates for:
- Git repositories (from GitHub API)

Key Features:
- Compares local vs remote commit SHAs for Git repositories
- Uses GitHub API for remote commit detection
- Provides Git update recommendations
- Enhanced: Determines if remote commits are actually newer (not just different)
"""

import json
import subprocess
import sys
import os
import urllib.request
import urllib.error
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from datetime import datetime


class UpdateDetector:
    """Git repository update detector with chronological checking."""
    
    def __init__(self, repo_owner: str = "rrmalmstrom", repo_name: str = "sip_lims_workflow_manager"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_base = "https://api.github.com"
        
    def get_local_commit_sha(self) -> Optional[str]:
        """Get the current local git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return None
    
    def get_remote_commit_sha(self, branch: str = "main") -> Optional[str]:
        """Get the latest commit SHA from GitHub for the specified branch."""
        try:
            url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{branch}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data["sha"]
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, Exception):
            return None
    
    def get_commit_timestamp(self, commit_sha: str) -> Optional[datetime]:
        """Get the timestamp of a specific commit from GitHub API."""
        try:
            url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{commit_sha}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                timestamp_str = data["commit"]["committer"]["date"]
                # Parse ISO 8601 timestamp: "2025-12-22T03:10:38Z"
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, ValueError):
            return None
    
    def is_commit_ancestor(self, ancestor_sha: str, descendant_sha: str) -> Optional[bool]:
        """Check if ancestor_sha is an ancestor of descendant_sha using git merge-base."""
        try:
            # Use git merge-base to check if ancestor_sha is reachable from descendant_sha
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
                capture_output=True,
                text=True
            )
            # Exit code 0 means ancestor_sha IS an ancestor of descendant_sha
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def check_repository_update(self, branch: str = "main") -> Dict[str, any]:
        """Check for Git repository updates."""
        try:
            local_sha = self.get_local_commit_sha()
            remote_sha = self.get_remote_commit_sha(branch)
            
            result = {
                "update_available": False,
                "local_sha": local_sha,
                "remote_sha": remote_sha,
                "reason": None,
                "error": None,
                "chronology_uncertain": False,
                "requires_user_confirmation": False
            }
            
            if local_sha is None:
                result["error"] = "Cannot determine local commit SHA"
                result["reason"] = "Not in a Git repository or Git not available"
                return result
            
            if remote_sha is None:
                result["error"] = "Cannot determine remote commit SHA"
                result["reason"] = "Network error or repository not accessible"
                return result
            
            if local_sha == remote_sha:
                result["reason"] = "Repository is up to date"
                return result
            
            # Check if remote commit is newer using chronological comparison
            try:
                local_timestamp = self.get_commit_timestamp(local_sha)
                remote_timestamp = self.get_commit_timestamp(remote_sha)
                
                if local_timestamp and remote_timestamp:
                    if remote_timestamp > local_timestamp:
                        result["update_available"] = True
                        result["reason"] = f"Remote commit is newer ({remote_timestamp} > {local_timestamp})"
                    else:
                        result["reason"] = f"Local commit is newer or same age ({local_timestamp} >= {remote_timestamp})"
                        result["chronology_uncertain"] = True
                else:
                    # Fallback to ancestor checking
                    is_ancestor = self.is_commit_ancestor(local_sha, remote_sha)
                    if is_ancestor is True:
                        result["update_available"] = True
                        result["reason"] = "Local commit is ancestor of remote commit"
                    elif is_ancestor is False:
                        result["reason"] = "Local and remote commits have diverged"
                        result["chronology_uncertain"] = True
                        result["requires_user_confirmation"] = True
                    else:
                        result["reason"] = "Cannot determine commit relationship"
                        result["chronology_uncertain"] = True
                        
            except Exception as e:
                result["error"] = f"Error during chronological comparison: {e}"
                result["chronology_uncertain"] = True
            
            return result
            
        except Exception as e:
            return {
                "update_available": False,
                "local_sha": None,
                "remote_sha": None,
                "reason": "Error during repository update check",
                "error": str(e),
                "chronology_uncertain": False,
                "requires_user_confirmation": False
            }
    
    def get_current_commit_sha(self) -> Optional[str]:
        """Get the current local git commit SHA."""
        return self.get_local_commit_sha()
    
    def get_update_summary(self) -> Dict[str, any]:
        """Get a comprehensive update summary for Git repositories."""
        repository_update = self.check_repository_update()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "repository": repository_update,
            "any_updates_available": repository_update.get("update_available", False),
            "chronology_uncertain": repository_update.get("chronology_uncertain", False),
            "requires_user_confirmation": repository_update.get("requires_user_confirmation", False)
        }


def main():
    """Command-line interface for Git repository update detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect Git repository updates for SIP LIMS Workflow Manager")
    parser.add_argument("--check-repository", action="store_true", help="Check for Git repository updates")
    parser.add_argument("--summary", action="store_true", help="Show Git update summary")
    parser.add_argument("--branch", default="main", help="Git branch to check from")
    
    args = parser.parse_args()
    
    detector = UpdateDetector()
    
    if args.check_repository:
        result = detector.check_repository_update(args.branch)
        print(json.dumps(result, indent=2))
    
    elif args.summary:
        result = detector.get_update_summary()
        print(json.dumps(result, indent=2))
    
    else:
        # Default: show summary
        result = detector.get_update_summary()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()