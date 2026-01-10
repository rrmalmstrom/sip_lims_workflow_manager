#!/usr/bin/env python3
"""
Enhanced Docker Image Update Detection System with Chronological Checking

This module provides functionality to detect updates for:
- Docker workflow manager images (from GitHub Container Registry)

Key Features:
- Compares local vs remote commit SHAs for Docker images
- Uses Docker image labels and GitHub API
- Provides Docker update recommendations
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
import tempfile
import shutil
from datetime import datetime


class UpdateDetector:
    """Enhanced update detector that checks chronological order of commits."""
    
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
    
    def get_remote_docker_image_commit_sha(self, tag: str = "latest", branch: Optional[str] = None) -> Optional[str]:
        """
        Get the commit SHA from REMOTE Docker image using improved detection.
        
        Strategy:
        1. Check if image already exists locally (no additional download)
        2. Try buildx imagetools inspect (lightweight)
        3. Try improved manifest inspect with better architecture handling
        4. Fall back to minimal pull approach if needed
        """
        import platform
        
        # Method 1: Check if image already exists locally (no additional download)
        commit_sha = self._try_local_image_check(tag)
        if commit_sha:
            return commit_sha
            
        # Method 2: Try buildx imagetools inspect
        commit_sha = self._try_buildx_imagetools_inspect(tag)
        if commit_sha:
            return commit_sha
            
        # Method 3: Try improved manifest inspect
        commit_sha = self._try_improved_manifest_inspect(tag)
        if commit_sha:
            return commit_sha
            
        # Method 4: Minimal pull approach (only if really needed)
        commit_sha = self._try_minimal_pull_approach(tag)
        if commit_sha:
            return commit_sha
            
        return None
    
    def _try_local_image_check(self, tag: str) -> Optional[str]:
        """Check if we already have the image locally."""
        try:
            result = subprocess.run(
                ["docker", "inspect", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
                
            inspect_data = json.loads(result.stdout)
            labels = inspect_data[0]["Config"]["Labels"]
            
            # Try multiple label keys for commit SHA
            for key in ["com.sip-lims.commit-sha", "org.opencontainers.image.revision"]:
                if key in labels:
                    return labels[key]
                    
            return None
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError, Exception):
            return None
    
    def _try_buildx_imagetools_inspect(self, tag: str) -> Optional[str]:
        """Try to get commit SHA using docker buildx imagetools inspect."""
        try:
            import platform
            
            # First, get the multi-arch manifest
            result = subprocess.run(
                ["docker", "buildx", "imagetools", "inspect", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
                
            # Parse the output to find platform-specific manifests
            lines = result.stdout.split('\n')
            current_arch = platform.machine().lower()
            
            # Look for our architecture or arm64/amd64
            target_digest = None
            for i, line in enumerate(lines):
                if "Platform:" in line:
                    platform_info = line.strip()
                    if current_arch in platform_info.lower() or "arm64" in platform_info or "amd64" in platform_info:
                        # Look for the digest in previous lines
                        for j in range(i-1, max(i-5, 0), -1):
                            if "sha256:" in lines[j]:
                                target_digest = lines[j].split("@")[-1].strip()
                                break
                        if target_digest:
                            break
            
            if not target_digest:
                return None
                
            # Now inspect the specific platform manifest
            return self._inspect_platform_manifest(target_digest)
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
            return None
    
    def _try_improved_manifest_inspect(self, tag: str) -> Optional[str]:
        """Try improved manifest inspection with better architecture handling."""
        try:
            import platform
            
            # Get the multi-arch manifest
            result = subprocess.run(
                ["docker", "manifest", "inspect", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
                
            manifest_data = json.loads(result.stdout)
            
            if "manifests" not in manifest_data:
                # Single-arch image
                return self._extract_labels_from_manifest(manifest_data)
            
            # Multi-arch image - find the best platform
            current_arch = platform.machine().lower()
            arch_priority = [current_arch, "arm64", "amd64", "x86_64"]
            
            selected_manifest = None
            for arch in arch_priority:
                for manifest in manifest_data["manifests"]:
                    platform_info = manifest.get("platform", {})
                    if platform_info.get("architecture", "").lower() == arch:
                        selected_manifest = manifest
                        break
                if selected_manifest:
                    break
            
            if not selected_manifest:
                # Fallback to first non-attestation manifest
                for manifest in manifest_data["manifests"]:
                    if "attestation" not in manifest.get("annotations", {}).get("vnd.docker.reference.type", ""):
                        selected_manifest = manifest
                        break
            
            if not selected_manifest:
                return None
                
            # Inspect the selected platform manifest
            return self._inspect_platform_manifest(selected_manifest["digest"])
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, Exception):
            return None
    
    def _inspect_platform_manifest(self, digest: str) -> Optional[str]:
        """Inspect a specific platform manifest to extract labels."""
        try:
            result = subprocess.run(
                ["docker", "manifest", "inspect", f"{self.ghcr_image}@{digest}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
                
            manifest_data = json.loads(result.stdout)
            return self._extract_labels_from_manifest(manifest_data)
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, Exception):
            return None
    
    def _extract_labels_from_manifest(self, manifest_data: dict) -> Optional[str]:
        """Extract commit SHA from manifest config labels."""
        try:
            config_digest = manifest_data.get("config", {}).get("digest")
            if not config_digest:
                return None
                
            # Try to get the config blob (this might not work without pulling)
            result = subprocess.run(
                ["docker", "manifest", "inspect", f"{self.ghcr_image}@{config_digest}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
                
            config_data = json.loads(result.stdout)
            labels = config_data.get("config", {}).get("Labels", {})
            
            # Try multiple label keys for commit SHA
            for key in ["com.sip-lims.commit-sha", "org.opencontainers.image.revision"]:
                if key in labels:
                    return labels[key]
                    
            return None
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, Exception):
            return None
    
    def _try_minimal_pull_approach(self, tag: str) -> Optional[str]:
        """
        Minimal pull approach - only pull if we really need to and don't have it locally.
        This is the fallback when lightweight methods fail.
        """
        try:
            # Pull the image (Docker will only download layers we don't have)
            result = subprocess.run(
                ["docker", "pull", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for pull
            )
            
            if result.returncode != 0:
                return None
                
            # Now inspect the pulled image
            return self._try_local_image_check(tag)
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
            return None
    
    def get_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
        """DEPRECATED: Get the commit SHA embedded in a Docker image's labels."""
        # This method is deprecated because it pulls images
        # Use get_local_docker_image_commit_sha() or get_remote_docker_image_commit_sha() instead
        return self.get_local_docker_image_commit_sha(tag)
    
    def check_docker_update(self, tag: str = "latest", branch: Optional[str] = None) -> Dict[str, any]:
        """Enhanced Docker update check with chronological validation and repository sync verification."""
        local_sha = self.get_local_docker_image_commit_sha(tag)
        remote_sha = self.get_remote_docker_image_commit_sha(tag, branch)
        
        # Also get the current repository commit SHA to check for sync issues
        repo_sha = self.get_remote_commit_sha(branch or "main")
        
        result = {
            "update_available": False,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "repo_sha": repo_sha,
            "reason": None,
            "error": None,
            "chronology_uncertain": False,
            "requires_user_confirmation": False,
            "sync_warning": None
        }
        
        # Handle missing local image
        if not local_sha:
            result["reason"] = "No local Docker image found"
            result["update_available"] = True  # Need to pull if no local image
            return result
        
        # Check for repository/Docker image sync issues - FATAL ERRORS
        if repo_sha and not remote_sha:
            # Repository has commits but no corresponding Docker image - FATAL
            result["error"] = "FATAL: Repository has been updated but no corresponding Docker image exists"
            result["sync_warning"] = f"Repository is at commit {repo_sha[:8]}... but no Docker image found for tag '{tag}'"
            result["reason"] = "FATAL ERROR: Docker image build failed or is pending. Contact developer immediately."
            result["requires_user_confirmation"] = False  # No confirmation - just fail
            result["fatal_sync_error"] = True
            return result
        
        # Handle missing remote SHA (both repo and image)
        if not remote_sha:
            result["error"] = "Could not determine remote Docker image commit SHA"
            return result
        
        # Check if repository and Docker image are out of sync - FATAL ERROR
        if repo_sha and remote_sha and repo_sha != remote_sha:
            # Check if Docker image is behind repository (most common case)
            ancestry_check = self.is_commit_ancestor(remote_sha, repo_sha)
            if ancestry_check:
                # Docker image is behind repository - FATAL
                result["error"] = "FATAL: Docker image is out of sync with repository"
                result["sync_warning"] = f"Repository is at newer commit {repo_sha[:8]}... but Docker image is at older commit {remote_sha[:8]}..."
                result["reason"] = "FATAL ERROR: Docker image build is required. Repository has newer commits than Docker image."
                result["fatal_sync_error"] = True
                return result
            else:
                # Docker image might be ahead or diverged - still fatal but different message
                result["error"] = "FATAL: Repository and Docker image have diverged"
                result["sync_warning"] = f"Repository ({repo_sha[:8]}...) and Docker image ({remote_sha[:8]}...) are out of sync"
                result["reason"] = "FATAL ERROR: Repository and Docker image commits have diverged. Manual intervention required."
                result["fatal_sync_error"] = True
                return result
        
        # If SHAs are identical, no update needed
        if local_sha == remote_sha:
            result["reason"] = "Local and remote SHAs match"
            return result
        
        # SHAs are different - now check chronology using enhanced logic
        # Method 1: Try git ancestry check (most reliable if we have git history)
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
            return result
        
        # Method 2: Fallback to timestamp comparison
        local_timestamp = self.get_commit_timestamp(local_sha)
        remote_timestamp = self.get_commit_timestamp(remote_sha)
        
        if local_timestamp and remote_timestamp:
            if remote_timestamp > local_timestamp:
                result["update_available"] = True
                result["reason"] = f"Remote commit {remote_sha[:8]}... is newer ({remote_timestamp.isoformat()})"
            else:
                result["update_available"] = False
                result["reason"] = f"Local commit {local_sha[:8]}... is newer or same age ({local_timestamp.isoformat()})"
        else:
            # Enhanced fallback behavior with uncertainty warnings
            result["update_available"] = True
            result["chronology_uncertain"] = True
            result["requires_user_confirmation"] = True
            result["reason"] = f"⚠️  CHRONOLOGY UNCERTAIN: Cannot determine if local ({local_sha[:8]}...) or remote ({remote_sha[:8]}...) is newer"
            result["error"] = "Could not determine commit chronology - git ancestry and timestamp checks both failed"
            result["warning"] = "Local version might be newer than remote. Manual confirmation recommended before updating."
        
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
            "any_updates_available": docker_update.get("update_available", False),
            "chronology_uncertain": docker_update.get("chronology_uncertain", False),
            "requires_user_confirmation": docker_update.get("requires_user_confirmation", False)
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