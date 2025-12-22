#!/usr/bin/env python3
"""
Branch utilities for Docker image management.

This module provides functions to detect the current Git branch and generate
appropriate Docker image names and tags for branch-aware Docker operations.
"""

import subprocess
import re
from typing import Optional


# Constants
REGISTRY_BASE = "ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
LOCAL_IMAGE_BASE = "sip-lims-workflow-manager"
MAX_DOCKER_TAG_LENGTH = 128


class GitRepositoryError(Exception):
    """Raised when Git repository operations fail."""
    pass


class BranchDetectionError(Exception):
    """Raised when branch detection fails."""
    pass


def get_current_branch() -> str:
    """
    Get the current Git branch name.
    
    Returns:
        str: Branch name (e.g., "main", "analysis/esp-docker-adaptation")
             For detached HEAD, returns "detached-{short-sha}"
    
    Raises:
        GitRepositoryError: If not in a Git repository
        BranchDetectionError: If branch detection fails
    """
    try:
        # Get current branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        
        branch_name = result.stdout.strip()
        
        if not branch_name:
            raise BranchDetectionError("Git command returned empty branch name")
        
        # Handle detached HEAD state - treat as error
        if branch_name == "HEAD":
            raise BranchDetectionError(
                "Repository is in detached HEAD state. Please checkout a branch before proceeding.\n"
                "Use: git checkout <branch-name> to switch to a proper branch."
            )
        
        return branch_name
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            raise GitRepositoryError("Not in a Git repository or Git not available")
        else:
            raise BranchDetectionError(f"Git command failed: {e}")
    except FileNotFoundError:
        raise GitRepositoryError("Git command not found")
    except Exception as e:
        raise BranchDetectionError(f"Unexpected error during branch detection: {e}")


def sanitize_branch_for_docker_tag(branch_name: str) -> str:
    """
    Convert branch name to valid Docker tag.
    
    Docker tag rules:
    - Lowercase alphanumeric, periods, dashes only
    - Cannot start with period or dash
    - Max 128 characters
    
    Args:
        branch_name: Raw branch name
        
    Returns:
        str: Sanitized Docker tag
        
    Raises:
        ValueError: If branch name is empty or results in invalid tag
    """
    if not branch_name or not branch_name.strip():
        raise ValueError("Branch name cannot be empty")
    
    # Start with the branch name
    tag = branch_name.strip()
    
    # Convert to lowercase
    tag = tag.lower()
    
    # Replace invalid characters with dashes
    # Keep only: a-z, 0-9, periods, dashes
    tag = re.sub(r'[^a-z0-9.-]', '-', tag)
    
    # Collapse multiple consecutive dashes into single dash
    tag = re.sub(r'-+', '-', tag)
    
    # Remove leading and trailing periods and dashes
    tag = tag.strip('.-')
    
    # Ensure we still have content after sanitization
    if not tag:
        raise ValueError(f"Branch name '{branch_name}' contains no valid characters for Docker tag")
    
    # Truncate if too long
    if len(tag) > MAX_DOCKER_TAG_LENGTH:
        tag = tag[:MAX_DOCKER_TAG_LENGTH]
        # Remove trailing periods and dashes after truncation
        tag = tag.rstrip('.-')
    
    # Final validation - ensure we have a valid tag
    if not tag:
        raise ValueError(f"Branch name '{branch_name}' resulted in empty Docker tag after sanitization")
    
    # Ensure doesn't start with invalid characters (double-check)
    if tag.startswith('.') or tag.startswith('-'):
        raise ValueError(f"Sanitized tag '{tag}' starts with invalid character")
    
    return tag


def get_docker_tag_for_current_branch() -> str:
    """
    Get Docker tag for current branch.
    
    Returns:
        str: Sanitized Docker tag for current branch
        
    Raises:
        GitRepositoryError: If not in a Git repository
        BranchDetectionError: If branch detection fails
        ValueError: If branch name cannot be sanitized
    """
    branch_name = get_current_branch()
    return sanitize_branch_for_docker_tag(branch_name)


def get_local_image_name_for_current_branch() -> str:
    """
    Get local Docker image name with branch tag.
    
    Returns:
        str: Local image name (e.g., "sip-lims-workflow-manager:main")
        
    Raises:
        GitRepositoryError: If not in a Git repository
        BranchDetectionError: If branch detection fails
        ValueError: If branch name cannot be sanitized
    """
    tag = get_docker_tag_for_current_branch()
    return f"{LOCAL_IMAGE_BASE}:{tag}"


def get_remote_image_name_for_current_branch() -> str:
    """
    Get remote Docker image name with branch tag.
    
    Returns:
        str: Remote image name (e.g., "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main")
        
    Raises:
        GitRepositoryError: If not in a Git repository
        BranchDetectionError: If branch detection fails
        ValueError: If branch name cannot be sanitized
    """
    tag = get_docker_tag_for_current_branch()
    return f"{REGISTRY_BASE}:{tag}"


# Convenience functions for specific use cases
def get_branch_info() -> dict:
    """
    Get comprehensive branch information.
    
    Returns:
        dict: Branch information including:
            - branch: Raw branch name
            - tag: Sanitized Docker tag
            - local_image: Local image name
            - remote_image: Remote image name
    """
    try:
        branch = get_current_branch()
        tag = sanitize_branch_for_docker_tag(branch)
        
        return {
            'branch': branch,
            'tag': tag,
            'local_image': f"{LOCAL_IMAGE_BASE}:{tag}",
            'remote_image': f"{REGISTRY_BASE}:{tag}"
        }
    except Exception as e:
        raise BranchDetectionError(f"Failed to get branch information: {e}")


def validate_docker_tag(tag: str) -> bool:
    """
    Validate if a string is a valid Docker tag.
    
    Args:
        tag: Tag to validate
        
    Returns:
        bool: True if valid Docker tag, False otherwise
    """
    if not tag:
        return False
    
    # Check length
    if len(tag) > MAX_DOCKER_TAG_LENGTH:
        return False
    
    # Check for valid characters only
    if not re.match(r'^[a-z0-9.-]+$', tag):
        return False
    
    # Check doesn't start with invalid characters
    if tag.startswith('.') or tag.startswith('-'):
        return False
    
    # Check doesn't end with invalid characters
    if tag.endswith('.') or tag.endswith('-'):
        return False
    
    return True


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    
    try:
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "branch":
                print(get_current_branch())
            elif command == "tag":
                print(get_docker_tag_for_current_branch())
            elif command == "local":
                print(get_local_image_name_for_current_branch())
            elif command == "remote":
                print(get_remote_image_name_for_current_branch())
            elif command == "info":
                info = get_branch_info()
                for key, value in info.items():
                    print(f"{key}: {value}")
            else:
                print(f"Unknown command: {command}")
                print("Available commands: branch, tag, local, remote, info")
                sys.exit(1)
        else:
            # Default: show all info
            info = get_branch_info()
            print("Branch Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)