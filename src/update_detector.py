#!/usr/bin/env python3
"""
Host-based Update Detection System

This module provides functionality to detect updates for both:
1. Docker workflow manager images (from GitHub Container Registry)
2. Python scripts (from GitHub repository)

Key Features:
- Compares local vs remote commit SHAs
- Handles both production and developer modes
- Provides update recommendations
- Downloads and manages script updates
"""

import json
import subprocess
import sys
import os
import urllib.request
import urllib.error
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import tempfile
import shutil
from datetime import datetime


class UpdateDetector:
    """Detects and manages updates for the workflow manager system."""
    
    def __init__(self, repo_owner: str = "rrmalmstrom", repo_name: str = "sip_lims_workflow_manager"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_base = "https://api.github.com"
        self.ghcr_image = f"ghcr.io/{repo_owner}/{repo_name}"
        
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
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_remote_commit_sha(self, branch: str = "main") -> Optional[str]:
        """Get the latest commit SHA from GitHub for the specified branch."""
        try:
            url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{branch}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data["sha"]
        except (urllib.error.URLError, KeyError, json.JSONDecodeError):
            return None
    
    def get_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
        """Get the commit SHA embedded in a Docker image's labels."""
        try:
            # First try to pull the latest image
            subprocess.run(
                ["docker", "pull", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                check=True
            )
            
            # Inspect the image to get labels
            result = subprocess.run(
                ["docker", "inspect", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            inspect_data = json.loads(result.stdout)
            labels = inspect_data[0]["Config"]["Labels"]
            
            # Try multiple label keys for commit SHA
            for key in ["com.sip-lims.commit-sha", "org.opencontainers.image.revision"]:
                if key in labels:
                    return labels[key]
            
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
            return None
    
    def check_docker_image_update(self, tag: str = "latest") -> Dict[str, any]:
        """Check if there's a Docker image update available."""
        local_sha = self.get_local_commit_sha()
        remote_sha = self.get_docker_image_commit_sha(tag)
        
        result = {
            "update_available": False,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "error": None
        }
        
        if not local_sha:
            result["error"] = "Could not determine local commit SHA"
            return result
        
        if not remote_sha:
            result["error"] = "Could not determine remote Docker image commit SHA"
            return result
        
        result["update_available"] = local_sha != remote_sha
        return result
    
    def check_scripts_update(self, branch: str = "main") -> Dict[str, any]:
        """Check if there are script updates available."""
        local_sha = self.get_local_commit_sha()
        remote_sha = self.get_remote_commit_sha(branch)
        
        result = {
            "update_available": False,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "error": None
        }
        
        if not local_sha:
            result["error"] = "Could not determine local commit SHA"
            return result
        
        if not remote_sha:
            result["error"] = "Could not determine remote commit SHA"
            return result
        
        result["update_available"] = local_sha != remote_sha
        return result
    
    def download_scripts(self, branch: str = "main", target_dir: str = "scripts") -> bool:
        """Download the latest scripts from GitHub."""
        try:
            # Create target directory if it doesn't exist
            target_path = Path(target_dir)
            target_path.mkdir(exist_ok=True)
            
            # Download the repository as a ZIP file
            zip_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/{branch}.zip"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "repo.zip"
                
                # Download ZIP file
                with urllib.request.urlopen(zip_url, timeout=30) as response:
                    with open(zip_path, "wb") as f:
                        f.write(response.read())
                
                # Extract ZIP file
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the extracted directory
                extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir() and d.name.startswith(self.repo_name)]
                if not extracted_dirs:
                    return False
                
                extracted_dir = extracted_dirs[0]
                
                # Copy Python scripts to target directory
                for script_file in extracted_dir.rglob("*.py"):
                    # Skip test files and __pycache__
                    if "test" in script_file.name.lower() or "__pycache__" in str(script_file):
                        continue
                    
                    # Create relative path structure
                    rel_path = script_file.relative_to(extracted_dir)
                    target_file = target_path / rel_path
                    
                    # Create parent directories
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(script_file, target_file)
                
                return True
                
        except Exception as e:
            print(f"Error downloading scripts: {e}")
            return False
    
    def get_update_summary(self) -> Dict[str, any]:
        """Get a comprehensive update summary for both Docker images and scripts."""
        docker_update = self.check_docker_image_update()
        scripts_update = self.check_scripts_update()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "docker": docker_update,
            "scripts": scripts_update,
            "any_updates_available": docker_update.get("update_available", False) or scripts_update.get("update_available", False)
        }


def main():
    """Command-line interface for update detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect updates for SIP LIMS Workflow Manager")
    parser.add_argument("--check-docker", action="store_true", help="Check for Docker image updates")
    parser.add_argument("--check-scripts", action="store_true", help="Check for script updates")
    parser.add_argument("--download-scripts", action="store_true", help="Download latest scripts")
    parser.add_argument("--summary", action="store_true", help="Show complete update summary")
    parser.add_argument("--scripts-dir", default="scripts", help="Directory to download scripts to")
    parser.add_argument("--branch", default="main", help="Git branch to check/download from")
    
    args = parser.parse_args()
    
    detector = UpdateDetector()
    
    if args.check_docker:
        result = detector.check_docker_image_update()
        print(json.dumps(result, indent=2))
    
    elif args.check_scripts:
        result = detector.check_scripts_update(args.branch)
        print(json.dumps(result, indent=2))
    
    elif args.download_scripts:
        success = detector.download_scripts(args.branch, args.scripts_dir)
        print(f"Script download {'successful' if success else 'failed'}")
        sys.exit(0 if success else 1)
    
    elif args.summary:
        result = detector.get_update_summary()
        print(json.dumps(result, indent=2))
    
    else:
        # Default: show summary
        result = detector.get_update_summary()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()