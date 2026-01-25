#!/usr/bin/env python3
"""
Git Utility Functions for Mac + VNC Workflow Manager

This module provides Docker-independent Git utilities extracted from the Docker-era
update_detector.py. These functions support native Python execution with Git operations
for repository management and update detection.

Key Features:
- Local and remote commit SHA retrieval
- Commit timestamp and ancestry checking
- GitHub API integration for remote repository data
- Enhanced debug logging integration
"""

import json
import subprocess
import urllib.request
import urllib.error
from typing import Optional
from datetime import datetime

# Enhanced debug logging for Mac + VNC workflow
try:
    from .enhanced_debug_logger import EnhancedDebugLogger
    debug_logger = EnhancedDebugLogger()
except ImportError:
    # Fallback if enhanced debug logger is not available
    debug_logger = None


class GitUtils:
    """Git utility functions for Mac + VNC workflow management."""
    
    def __init__(self, repo_owner: str = "rrmalmstrom", repo_name: str = "sip_lims_workflow_manager"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_base = "https://api.github.com"
        
        # Log Git utilities initialization
        if debug_logger:
            debug_logger.log_native_script_execution(
                script_name="git_utils",
                message=f"Initialized GitUtils for {repo_owner}/{repo_name}",
                level="INFO"
            )
    
    def get_local_commit_sha(self) -> Optional[str]:
        """Get the current local git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            sha = result.stdout.strip()
            
            # Log successful SHA retrieval
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Retrieved local commit SHA: {sha[:8]}...",
                    level="INFO"
                )
            
            return sha
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Log error
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Failed to get local commit SHA: {str(e)}",
                    level="ERROR"
                )
            return None
    
    def get_remote_commit_sha(self, branch: str = "main") -> Optional[str]:
        """Get the latest commit SHA from GitHub for the specified branch."""
        try:
            url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{branch}"
            
            # Log API request
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Requesting remote commit SHA for branch '{branch}' from GitHub API",
                    level="INFO"
                )
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                sha = data["sha"]
                
                # Log successful retrieval
                if debug_logger:
                    debug_logger.log_native_script_execution(
                        script_name="git_utils",
                        message=f"Retrieved remote commit SHA: {sha[:8]}... for branch '{branch}'",
                        level="INFO"
                    )
                
                return sha
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
            # Log error
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Failed to get remote commit SHA for branch '{branch}': {str(e)}",
                    level="ERROR"
                )
            return None
    
    def get_commit_timestamp(self, commit_sha: str) -> Optional[datetime]:
        """Get the timestamp of a specific commit from GitHub API."""
        try:
            url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{commit_sha}"
            
            # Log API request
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Requesting timestamp for commit {commit_sha[:8]}... from GitHub API",
                    level="INFO"
                )
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                timestamp_str = data["commit"]["committer"]["date"]
                # Parse ISO 8601 timestamp: "2025-12-22T03:10:38Z"
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # Log successful retrieval
                if debug_logger:
                    debug_logger.log_native_script_execution(
                        script_name="git_utils",
                        message=f"Retrieved timestamp for commit {commit_sha[:8]}...: {timestamp.isoformat()}",
                        level="INFO"
                    )
                
                return timestamp
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, ValueError) as e:
            # Log error
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Failed to get timestamp for commit {commit_sha[:8]}...: {str(e)}",
                    level="ERROR"
                )
            return None
    
    def is_commit_ancestor(self, ancestor_sha: str, descendant_sha: str) -> Optional[bool]:
        """Check if ancestor_sha is an ancestor of descendant_sha using git merge-base."""
        try:
            # Log ancestry check
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Checking if {ancestor_sha[:8]}... is ancestor of {descendant_sha[:8]}...",
                    level="INFO"
                )
            
            # Use git merge-base to check if ancestor_sha is reachable from descendant_sha
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
                capture_output=True,
                text=True
            )
            # Exit code 0 means ancestor_sha IS an ancestor of descendant_sha
            is_ancestor = result.returncode == 0
            
            # Log result
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Ancestry check result: {ancestor_sha[:8]}... {'IS' if is_ancestor else 'IS NOT'} ancestor of {descendant_sha[:8]}...",
                    level="INFO"
                )
            
            return is_ancestor
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Log error
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Failed ancestry check between {ancestor_sha[:8]}... and {descendant_sha[:8]}...: {str(e)}",
                    level="ERROR"
                )
            return None
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current Git branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            
            # Log successful branch retrieval
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Current Git branch: {branch}",
                    level="INFO"
                )
            
            return branch
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Log error
            if debug_logger:
                debug_logger.log_native_script_execution(
                    script_name="git_utils",
                    message=f"Failed to get current branch: {str(e)}",
                    level="ERROR"
                )
            return None
    
    def check_repository_updates(self, branch: Optional[str] = None) -> dict:
        """
        Check if the local repository has updates available from remote.
        
        Args:
            branch: Branch to check (defaults to current branch)
            
        Returns:
            Dictionary with update information including:
            - update_available: bool
            - local_sha: str
            - remote_sha: str
            - reason: str
            - chronology_uncertain: bool
        """
        if branch is None:
            branch = self.get_current_branch()
            if not branch:
                branch = "main"  # Fallback
        
        # Log update check start
        if debug_logger:
            debug_logger.log_native_script_execution(
                script_name="git_utils",
                message=f"Starting repository update check for branch '{branch}'",
                level="INFO"
            )
        
        local_sha = self.get_local_commit_sha()
        remote_sha = self.get_remote_commit_sha(branch)
        
        result = {
            "update_available": False,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "branch": branch,
            "reason": None,
            "error": None,
            "chronology_uncertain": False
        }
        
        # Handle missing local SHA
        if not local_sha:
            result["reason"] = "Could not determine local commit SHA"
            result["error"] = "Git repository may not be initialized or accessible"
            print("⚠️  WARNING: Cannot determine local Git version")
            print("   REASON: Git repository may not be initialized or accessible")
            print("   ACTION: Continuing with current local files")
            return result
        
        # Handle missing remote SHA
        if not remote_sha:
            result["error"] = "Could not determine remote commit SHA"
            result["reason"] = "GitHub API may be unavailable or branch does not exist"
            print(f"⚠️  WARNING: Cannot check for updates from remote branch '{branch}'")
            print("   REASON: GitHub API may be unavailable or branch does not exist")
            print("   ACTION: Continuing with current local version")
            return result
        
        # If SHAs are identical, no update needed
        if local_sha == remote_sha:
            result["reason"] = f"Local and remote SHAs match ({local_sha[:8]}...)"
            return result
        
        # SHAs are different - check chronology
        ancestry_check = self.is_commit_ancestor(local_sha, remote_sha)
        if ancestry_check is not None:
            if ancestry_check:
                # Local is ancestor of remote = remote is newer
                result["update_available"] = True
                result["reason"] = f"Remote commit {remote_sha[:8]}... is newer than local {local_sha[:8]}..."
            else:
                # Check reverse - is remote ancestor of local?
                reverse_check = self.is_commit_ancestor(remote_sha, local_sha)
                if reverse_check:
                    # Remote is ancestor of local = local is newer
                    result["update_available"] = False
                    result["reason"] = f"Local commit {local_sha[:8]}... is newer than remote {remote_sha[:8]}..."
                else:
                    # Neither is ancestor = diverged branches
                    result["update_available"] = False
                    result["reason"] = f"Local and remote commits have diverged - manual review needed"
                    print(f"⚠️  WARNING: Local and remote branches have diverged")
                    print(f"   Local:  {local_sha[:8]}...")
                    print(f"   Remote: {remote_sha[:8]}...")
                    print(f"   ACTION: Continuing with local version - manual review recommended")
        else:
            # Fallback to timestamp comparison
            print("⚠️  WARNING: Git ancestry check failed, falling back to timestamp comparison...")
            local_timestamp = self.get_commit_timestamp(local_sha)
            remote_timestamp = self.get_commit_timestamp(remote_sha)
            
            if local_timestamp and remote_timestamp:
                if remote_timestamp > local_timestamp:
                    result["update_available"] = True
                    result["reason"] = f"Remote commit {remote_sha[:8]}... is newer ({remote_timestamp.isoformat()})"
                    print(f"✓ Timestamp comparison successful: Remote version is newer")
                else:
                    result["update_available"] = False
                    result["reason"] = f"Local commit {local_sha[:8]}... is newer or same age ({local_timestamp.isoformat()})"
                    print(f"✓ Timestamp comparison successful: Local version is current")
            else:
                # Cannot determine chronology - provide clear user warning
                result["chronology_uncertain"] = True
                result["reason"] = f"Cannot determine if local ({local_sha[:8]}...) or remote ({remote_sha[:8]}...) is newer"
                result["error"] = "Both git ancestry and timestamp checks failed"
                
                # Clear terminal warning for user
                print("\n" + "="*60)
                print("⚠️  CRITICAL WARNING: VERSION COMPARISON FAILED")
                print("="*60)
                print(f"Local version:  {local_sha[:8]}...")
                print(f"Remote version: {remote_sha[:8]}...")
                print("\nPROBLEM: Cannot determine which version is newer because:")
                print("• Git ancestry check failed (may not have full git history)")
                print("• GitHub API timestamp check failed (network/API issues)")
                print("\nACTION TAKEN: Continuing with LOCAL version to avoid data loss")
                print("RECOMMENDATION: Check your internet connection and try again later")
                print("="*60 + "\n")
        
        # Log update check result
        if debug_logger:
            debug_logger.log_native_script_execution(
                script_name="git_utils",
                message=f"Repository update check complete: {'Update available' if result['update_available'] else 'No update needed'} - {result['reason']}",
                level="INFO" if not result.get('error') else "WARNING"
            )
        
        return result


# Convenience functions for direct use
def get_local_commit_sha() -> Optional[str]:
    """Convenience function to get local commit SHA."""
    git_utils = GitUtils()
    return git_utils.get_local_commit_sha()


def get_remote_commit_sha(branch: str = "main") -> Optional[str]:
    """Convenience function to get remote commit SHA."""
    git_utils = GitUtils()
    return git_utils.get_remote_commit_sha(branch)


def get_current_branch() -> Optional[str]:
    """Convenience function to get current branch."""
    git_utils = GitUtils()
    return git_utils.get_current_branch()


def check_repository_updates(branch: Optional[str] = None) -> dict:
    """Convenience function to check repository updates."""
    git_utils = GitUtils()
    return git_utils.check_repository_updates(branch)


if __name__ == "__main__":
    """Command-line interface for Git utilities."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Git utilities for Mac + VNC Workflow Manager")
    parser.add_argument("--local-sha", action="store_true", help="Get local commit SHA")
    parser.add_argument("--remote-sha", help="Get remote commit SHA for branch")
    parser.add_argument("--current-branch", action="store_true", help="Get current branch name")
    parser.add_argument("--check-updates", action="store_true", help="Check for repository updates")
    parser.add_argument("--branch", help="Branch to check (defaults to current)")
    
    args = parser.parse_args()
    
    git_utils = GitUtils()
    
    if args.local_sha:
        sha = git_utils.get_local_commit_sha()
        print(sha if sha else "Could not determine local commit SHA")
    
    elif args.remote_sha:
        sha = git_utils.get_remote_commit_sha(args.remote_sha)
        print(sha if sha else f"Could not determine remote commit SHA for branch '{args.remote_sha}'")
    
    elif args.current_branch:
        branch = git_utils.get_current_branch()
        print(branch if branch else "Could not determine current branch")
    
    elif args.check_updates:
        result = git_utils.check_repository_updates(args.branch)
        print(json.dumps(result, indent=2))
    
    else:
        # Default: show current status
        print("Git Repository Status:")
        print(f"Local SHA: {git_utils.get_local_commit_sha()}")
        print(f"Current Branch: {git_utils.get_current_branch()}")
        
        # Check updates for current branch
        result = git_utils.check_repository_updates()
        print(f"Updates Available: {result.get('update_available', 'Unknown')}")
        if result.get('reason'):
            print(f"Reason: {result['reason']}")