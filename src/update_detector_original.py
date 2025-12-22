#!/usr/bin/env python3
"""
Docker Image Update Detection System

This module provides functionality to detect updates for:
- Docker workflow manager images (from GitHub Container Registry)

Key Features:
- Compares local vs remote commit SHAs for Docker images
- Uses Docker image labels and GitHub API
- Provides Docker update recommendations
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
    
    def get_local_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
        """Get the commit SHA from a LOCAL Docker image's labels (no pulling)."""
        try:
            # Inspect the LOCAL image only - do NOT pull
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
    
    def get_remote_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
        """Get the commit SHA from REMOTE Docker image without pulling."""
        try:
            # Use GitHub API to get the latest commit SHA from the branch that builds the image
            # This assumes the remote image is built from the latest commit on analysis/esp-docker-adaptation
            return self.get_remote_commit_sha("analysis/esp-docker-adaptation")
        except Exception:
            return None
    
    def get_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
        """DEPRECATED: Get the commit SHA embedded in a Docker image's labels."""
        # This method is deprecated because it pulls images
        # Use get_local_docker_image_commit_sha() or get_remote_docker_image_commit_sha() instead
        return self.get_local_docker_image_commit_sha(tag)
    
    def check_docker_update(self, tag: str = "latest") -> Dict[str, any]:
        """Check if there's a Docker image update available (local vs remote)."""
        local_sha = self.get_local_docker_image_commit_sha(tag)
        remote_sha = self.get_remote_docker_image_commit_sha(tag)
        
        result = {
            "update_available": False,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "reason": None,
            "error": None
        }
        
        if not local_sha:
            result["reason"] = "No local Docker image found"
            result["update_available"] = True  # Need to pull if no local image
            return result
        
        if not remote_sha:
            result["error"] = "Could not determine remote Docker image commit SHA"
            return result
        
        if local_sha != remote_sha:
            result["update_available"] = True
            result["reason"] = f"Local SHA {local_sha[:8]}... != Remote SHA {remote_sha[:8]}..."
        else:
            result["reason"] = "Local and remote SHAs match"
        
        return result
    
    def check_docker_image_update(self, tag: str = "latest") -> Dict[str, any]:
        """DEPRECATED: Use check_docker_update() instead."""
        return self.check_docker_update(tag)
    
    
    def get_update_summary(self) -> Dict[str, any]:
        """Get a comprehensive update summary for Docker images."""
        docker_update = self.check_docker_update()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "docker": docker_update,
            "any_updates_available": docker_update.get("update_available", False)
        }


def main():
    """Command-line interface for Docker image update detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect Docker image updates for SIP LIMS Workflow Manager")
    parser.add_argument("--check-docker", action="store_true", help="Check for Docker image updates")
    parser.add_argument("--summary", action="store_true", help="Show Docker update summary")
    parser.add_argument("--branch", default="main", help="Git branch to check from")
    
    args = parser.parse_args()
    
    detector = UpdateDetector()
    
    if args.check_docker:
        result = detector.check_docker_update()
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