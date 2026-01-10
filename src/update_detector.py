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
    
    def get_remote_docker_image_digest(self, tag: str = "latest") -> Optional[str]:
        """
        Get the image digest from REMOTE Docker image using Docker best practices.
        
        INDUSTRY STANDARD APPROACH: Use image digests for comparison, not commit SHAs.
        This follows Docker's official recommendations for image comparison.
        """
        try:
            # Use docker buildx imagetools inspect (official Docker recommendation)
            result = subprocess.run(
                ["docker", "buildx", "imagetools", "inspect", f"{self.ghcr_image}:{tag}", "--format", "{{.Digest}}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                digest = result.stdout.strip()
                if digest.startswith('sha256:'):
                    return digest
                
        except Exception:
            pass
            
        # Fallback: Parse buildx imagetools output manually
        try:
            result = subprocess.run(
                ["docker", "buildx", "imagetools", "inspect", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse the output to find the digest
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip().startswith('Digest:') and 'sha256:' in line:
                        # Extract digest from line like "Digest:    sha256:abc123..."
                        parts = line.split('sha256:')
                        if len(parts) > 1:
                            digest_part = parts[1].strip()
                            # Take only the hash part, ignore any trailing content
                            digest_hash = digest_part.split()[0] if digest_part else ""
                            if digest_hash:
                                return f"sha256:{digest_hash}"
                
                # If we couldn't parse the digest, return the full output for debugging
                # This should be removed in production, but helps with current debugging
                return result.stdout.strip()
                            
        except Exception:
            pass
            
        return None
    
    def get_local_docker_image_digest(self, tag: str = "latest") -> Optional[str]:
        """
        Get the image digest from LOCAL Docker image using Docker best practices.
        """
        try:
            # Use docker inspect with RepoDigests (official Docker recommendation)
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{index .RepoDigests 0}}", f"{self.ghcr_image}:{tag}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                repo_digest = result.stdout.strip()
                # Extract just the digest part: "ghcr.io/user/repo@sha256:abc123" -> "sha256:abc123"
                if '@' in repo_digest:
                    return repo_digest.split('@')[-1]
                    
        except Exception:
            pass
            
        return None

    def get_remote_docker_image_commit_sha(self, tag: str = "latest", branch: Optional[str] = None) -> Optional[str]:
        """
        DEPRECATED: Get the commit SHA from REMOTE Docker image.
        
        This method is kept for backward compatibility but should be replaced
        with digest-based comparison for better reliability.
        """
        import platform
        
        # Method 1: Try buildx imagetools inspect
        commit_sha = self._try_buildx_imagetools_inspect(tag)
        if commit_sha:
            return commit_sha
            
        # Method 2: Try improved manifest inspect
        commit_sha = self._try_improved_manifest_inspect(tag)
        if commit_sha:
            return commit_sha
            
        # Method 3: Minimal pull approach (only if really needed)
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
        """
        FIXED: Enhanced Docker update check using DIGEST-BASED comparison.
        
        This method now uses Docker image digests for reliable comparison without pulling images.
        Maintains backward compatibility with the existing API used by run.mac.command.
        
        CRITICAL FIX: This replaces the broken commit SHA-based approach that was pulling
        full images during detection, causing false "up to date" results.
        """
        try:
            # Step 1: Check if local image exists using digest-based approach
            local_digest = self.get_local_docker_image_digest(tag)
            
            # Initialize result structure (maintain backward compatibility)
            result = {
                "update_available": False,
                "local_sha": None,  # Keep for backward compatibility
                "remote_sha": None,  # Keep for backward compatibility
                "repo_sha": None,
                "reason": None,
                "error": None,
                "chronology_uncertain": False,
                "requires_user_confirmation": False,
                "sync_warning": None,
                # New digest fields for debugging
                "local_digest": local_digest,
                "remote_digest": None
            }
            
            if local_digest is None:
                # No local image exists - definitely need update
                result["update_available"] = True
                result["reason"] = "No local Docker image found"
                result["repo_sha"] = self.get_current_commit_sha()
                return result
            
            # Step 2: Get remote image digest (lightweight, no pulling)
            remote_digest = self.get_remote_docker_image_digest(tag)
            result["remote_digest"] = remote_digest
            result["repo_sha"] = self.get_current_commit_sha()
            
            if remote_digest is None:
                result["error"] = "Failed to get remote Docker image digest"
                result["reason"] = "Cannot determine remote image state"
                return result
            
            # Step 3: Compare digests (this is the reliable comparison)
            if local_digest != remote_digest:
                result["update_available"] = True
                result["reason"] = f"Image content differs (local: {local_digest[:12]}... != remote: {remote_digest[:12]}...)"
                return result
            
            # Step 4: Images are identical - try to get commit SHAs for additional info
            try:
                local_commit = self.get_local_docker_image_commit_sha(tag)
                result["local_sha"] = local_commit
                
                # For backward compatibility, try to get remote commit SHA for informational purposes
                # But don't let this fail the whole operation
                try:
                    remote_commit = self.get_remote_docker_image_commit_sha(tag, branch)
                    result["remote_sha"] = remote_commit
                except:
                    # If remote commit SHA extraction fails, that's OK - we have digest comparison
                    result["remote_sha"] = "digest-based-comparison"
                
                # Check for informational warnings
                repo_sha = result["repo_sha"]
                if repo_sha and local_commit and local_commit != repo_sha:
                    result["sync_warning"] = f"Image commit ({local_commit[:8]}) != Repository commit ({repo_sha[:8]}) - but images are identical"
                    
            except Exception:
                # Ignore commit SHA extraction failures - digest comparison is what matters
                result["local_sha"] = "digest-based-comparison"
                result["remote_sha"] = "digest-based-comparison"
            
            result["update_available"] = False
            result["reason"] = "Local and remote images are identical"
            return result
            
        except Exception as e:
            return {
                "update_available": False,
                "local_sha": None,
                "remote_sha": None,
                "repo_sha": self.get_current_commit_sha(),
                "reason": "Error during Docker image update check",
                "error": str(e),
                "chronology_uncertain": False,
                "requires_user_confirmation": False,
                "sync_warning": None,
                "local_digest": None,
                "remote_digest": None
            }
    
    def check_docker_image_update(self, tag: str = "latest", branch: Optional[str] = None) -> dict:
        """
        Check if Docker image needs update using DIGEST-BASED comparison.
        
        INDUSTRY STANDARD APPROACH: Uses Docker image digests for reliable comparison
        without pulling images. This follows Docker's official best practices.
        
        Returns dict with:
        - update_available: bool
        - reason: str
        - local_digest: Optional[str]
        - remote_digest: Optional[str]
        - repo_sha: Optional[str]
        - error: Optional[str]
        - sync_warning: Optional[str]
        """
        try:
            # Step 1: Check if local image exists
            local_digest = self.get_local_docker_image_digest(tag)
            
            if local_digest is None:
                # No local image exists - definitely need update
                return {
                    "update_available": True,
                    "reason": "No local Docker image found",
                    "local_digest": None,
                    "remote_digest": None,
                    "repo_sha": self.get_current_commit_sha(),
                    "error": None,
                    "sync_warning": None
                }
            
            # Step 2: Get remote image digest (lightweight, no pulling)
            remote_digest = self.get_remote_docker_image_digest(tag)
            repo_sha = self.get_current_commit_sha()
            
            if remote_digest is None:
                return {
                    "update_available": False,
                    "reason": "Cannot determine remote image state",
                    "local_digest": local_digest,
                    "remote_digest": None,
                    "repo_sha": repo_sha,
                    "error": "Failed to get remote Docker image digest",
                    "sync_warning": None
                }
            
            # Step 3: Compare digests (this is the reliable comparison)
            if local_digest != remote_digest:
                return {
                    "update_available": True,
                    "reason": f"Image content differs (local: {local_digest[:12]}... != remote: {remote_digest[:12]}...)",
                    "local_digest": local_digest,
                    "remote_digest": remote_digest,
                    "repo_sha": repo_sha,
                    "error": None,
                    "sync_warning": None
                }
            
            # Step 4: Images are identical - check for informational warnings
            sync_warning = None
            
            # Try to get commit SHAs for informational purposes (non-critical)
            try:
                local_commit = self.get_local_docker_image_commit_sha(tag)
                if repo_sha and local_commit and local_commit != repo_sha:
                    sync_warning = f"Image commit ({local_commit[:8]}) != Repository commit ({repo_sha[:8]}) - but images are identical"
            except Exception:
                # Ignore commit SHA extraction failures - digest comparison is what matters
                pass
            
            return {
                "update_available": False,
                "reason": "Local and remote images are identical",
                "local_digest": local_digest,
                "remote_digest": remote_digest,
                "repo_sha": repo_sha,
                "error": None,
                "sync_warning": sync_warning
            }
            
        except Exception as e:
            return {
                "update_available": False,
                "reason": "Error during Docker image update check",
                "local_digest": None,
                "remote_digest": None,
                "repo_sha": self.get_current_commit_sha(),
                "error": str(e),
                "sync_warning": None
            }
    
    def get_current_commit_sha(self) -> Optional[str]:
        """Get the current local git commit SHA."""
        return self.get_local_commit_sha()
    
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