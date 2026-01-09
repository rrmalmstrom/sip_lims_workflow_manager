#!/usr/bin/env python3
"""
Python Scripts Update System

This module provides functionality to detect and manage updates for:
- Python scripts from workflow-specific repositories (SIP or SPS-CE)

Key Features:
- Uses git clone/pull for proper repository management
- Uses git's built-in fetch/status to detect updates
- Manages workflow-specific script directories as git repositories
- Provides script update recommendations and downloads
- Supports both SIP and SPS-CE workflows
"""

import json
import subprocess
import sys
import os
import urllib.request
import urllib.error
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

# Repository mapping for different workflow types
WORKFLOW_REPOSITORIES = {
    'sip': {
        'repo_name': 'sip_scripts_workflow_gui',
        'repo_owner': 'rrmalmstrom'
    },
    'sps-ce': {
        'repo_name': 'SPS_library_creation_scripts',
        'repo_owner': 'rrmalmstrom'
    }
}


class ScriptsUpdater:
    """Detects and manages updates for workflow-specific Python scripts."""
    
    def __init__(self, workflow_type: str = None, repo_owner: str = None, scripts_repo_name: str = None):
        """
        Initialize ScriptsUpdater with workflow-aware repository configuration.
        
        Args:
            workflow_type: 'sip' or 'sps-ce' - determines which repository to use
            repo_owner: Override default repository owner
            scripts_repo_name: Override default repository name
        """
        # Determine workflow type from environment if not provided
        if workflow_type is None:
            workflow_type = os.environ.get('WORKFLOW_TYPE', 'sip').lower()
        
        # Validate workflow type
        if workflow_type not in WORKFLOW_REPOSITORIES:
            raise ValueError(f"Invalid workflow_type '{workflow_type}'. Must be one of: {list(WORKFLOW_REPOSITORIES.keys())}")
        
        self.workflow_type = workflow_type
        
        # Use provided values or get from workflow mapping
        if repo_owner and scripts_repo_name:
            self.repo_owner = repo_owner
            self.scripts_repo_name = scripts_repo_name
        else:
            repo_config = WORKFLOW_REPOSITORIES[workflow_type]
            self.repo_owner = repo_config['repo_owner']
            self.scripts_repo_name = repo_config['repo_name']
        
        self.github_api_base = "https://api.github.com"
        self.scripts_repo_url = f"https://github.com/{self.repo_owner}/{self.scripts_repo_name}.git"
        
    def check_scripts_update(self, scripts_dir: str, branch: str = "main") -> Dict[str, any]:
        """Check if there are script updates available using git."""
        result = {
            "update_available": False,
            "error": None,
            "scripts_dir": scripts_dir,
            "reason": None
        }
        
        scripts_path = Path(scripts_dir)
        
        # If scripts directory doesn't exist or isn't a git repo, we need to clone
        if not scripts_path.exists() or not (scripts_path / ".git").exists():
            result["update_available"] = True
            result["reason"] = "Scripts directory missing or not a git repository"
            return result
        
        try:
            # Fetch latest remote information
            subprocess.run(
                ["git", "fetch"],
                cwd=scripts_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if local branch is behind remote
            status_result = subprocess.run(
                ["git", "status", "-uno", "--porcelain=v1"],
                cwd=scripts_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if we're behind the remote branch
            behind_result = subprocess.run(
                ["git", "rev-list", "--count", f"HEAD..origin/{branch}"],
                cwd=scripts_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits_behind = int(behind_result.stdout.strip())
            
            if commits_behind > 0:
                result["update_available"] = True
                result["reason"] = f"Local repository is {commits_behind} commit(s) behind remote"
            else:
                result["reason"] = "Local repository is up to date"
            
            return result
            
        except subprocess.CalledProcessError as e:
            result["error"] = f"Git operation failed: {e.stderr}"
            return result
        except Exception as e:
            result["error"] = f"Error checking git status: {e}"
            return result
    
    def update_scripts(self, scripts_dir: str, branch: str = "main") -> Dict[str, any]:
        """Update or clone the scripts repository."""
        try:
            scripts_path = Path(scripts_dir)
            
            # Check if target directory exists and is a git repository
            if scripts_path.exists() and (scripts_path / ".git").exists():
                # Directory exists and is a git repo - do git pull
                print(f"Updating existing scripts repository in {scripts_path}")
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=scripts_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return {
                    "success": True,
                    "action": "updated",
                    "message": f"Scripts updated successfully: {result.stdout.strip()}",
                    "scripts_dir": scripts_dir
                }
            else:
                # Directory doesn't exist or isn't a git repo - do git clone
                print(f"Cloning scripts repository to {scripts_path}")
                
                # Remove existing directory if it exists but isn't a git repo
                if scripts_path.exists():
                    import shutil
                    shutil.rmtree(scripts_path)
                
                # Create parent directory if needed
                scripts_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Clone the scripts repository
                result = subprocess.run(
                    ["git", "clone", "-b", branch, self.scripts_repo_url, str(scripts_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return {
                    "success": True,
                    "action": "cloned",
                    "message": f"Scripts cloned successfully to {scripts_dir}",
                    "scripts_dir": scripts_dir
                }
                
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git operation failed: {e.stderr}",
                "scripts_dir": scripts_dir
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error managing scripts repository: {e}",
                "scripts_dir": scripts_dir
            }
    
    def get_scripts_summary(self, scripts_dir: str, branch: str = "main") -> Dict[str, any]:
        """Get a comprehensive update summary for scripts."""
        scripts_update = self.check_scripts_update(scripts_dir, branch)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "scripts": scripts_update,
            "update_available": scripts_update.get("update_available", False),
            "branch": branch
        }


def main():
    """Command-line interface for scripts update detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect and manage Python script updates")
    parser.add_argument("--check-scripts", action="store_true", help="Check for script updates")
    parser.add_argument("--update-scripts", action="store_true", help="Update/clone scripts")
    parser.add_argument("--summary", action="store_true", help="Show scripts update summary")
    parser.add_argument("--scripts-dir", required=True, help="Directory for scripts repository")
    parser.add_argument("--branch", default="main", help="Git branch to check/download from")
    parser.add_argument("--workflow-type", help="Workflow type (sip or sps-ce) - defaults to WORKFLOW_TYPE env var")
    
    args = parser.parse_args()
    
    try:
        updater = ScriptsUpdater(workflow_type=args.workflow_type)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.check_scripts:
        result = updater.check_scripts_update(args.scripts_dir, args.branch)
        print(json.dumps(result, indent=2))
    
    elif args.update_scripts:
        result = updater.update_scripts(args.scripts_dir, args.branch)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success", False) else 1)
    
    elif args.summary:
        result = updater.get_scripts_summary(args.scripts_dir, args.branch)
        print(json.dumps(result, indent=2))
    
    else:
        # Default: show summary
        result = updater.get_scripts_summary(args.scripts_dir, args.branch)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()