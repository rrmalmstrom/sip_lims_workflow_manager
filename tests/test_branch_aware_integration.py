#!/usr/bin/env python3
"""
Integration test suite for the complete branch-aware Docker system.
Tests the end-to-end workflow from branch detection to Docker operations.
"""

import pytest
import sys
import os
import subprocess
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.branch_utils import (
    get_current_branch,
    sanitize_branch_for_docker_tag,
    get_docker_tag_for_current_branch,
    get_local_image_name_for_current_branch,
    get_remote_image_name_for_current_branch
)
from src.update_detector import UpdateDetector


class TestBranchAwareIntegration:
    """Test complete branch-aware Docker workflow integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = UpdateDetector()
    
    def test_complete_branch_to_docker_workflow(self):
        """Test the complete workflow from branch detection to Docker image names."""
        # Get current branch
        current_branch = get_current_branch()
        assert current_branch is not None
        assert len(current_branch) > 0
        
        # Generate Docker tag
        docker_tag = sanitize_branch_for_docker_tag(current_branch)
        assert docker_tag is not None
        assert "/" not in docker_tag  # Should be sanitized
        
        # Generate image names
        local_image = get_local_image_name_for_current_branch()
        remote_image = get_remote_image_name_for_current_branch()
        
        assert local_image.startswith("sip-lims-workflow-manager:")
        assert remote_image.startswith("ghcr.io/rrmalmstrom/sip_lims_workflow_manager:")
        assert docker_tag in local_image
        assert docker_tag in remote_image
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    def test_update_detector_uses_current_branch(self, mock_get_remote_sha):
        """Test that update detector automatically uses current branch."""
        mock_get_remote_sha.return_value = "test123abc"
        
        # Call without specifying branch - should auto-detect
        result = self.detector.get_remote_docker_image_commit_sha()
        
        # Should have called with current branch
        assert result == "test123abc"
        mock_get_remote_sha.assert_called_once()
        
        # Get the branch that was actually used
        called_branch = mock_get_remote_sha.call_args[0][0]
        current_branch = get_current_branch()
        assert called_branch == current_branch
    
    def test_bash_utilities_integration(self):
        """Test that bash utilities work correctly with current environment."""
        # Test bash utilities by calling them
        result = subprocess.run(
            ["bash", "-c", "source utils/branch_utils.sh && get_current_branch_tag"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        bash_tag = result.stdout.strip()
        
        # Compare with Python utilities
        python_tag = get_docker_tag_for_current_branch()
        
        assert bash_tag == python_tag
    
    def test_image_name_consistency(self):
        """Test that image names are consistent across all utilities."""
        # Get image names from Python utilities
        local_image_python = get_local_image_name_for_current_branch()
        remote_image_python = get_remote_image_name_for_current_branch()
        
        # Get image names from bash utilities
        result_local = subprocess.run(
            ["bash", "-c", "source utils/branch_utils.sh && get_local_image_name"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        result_remote = subprocess.run(
            ["bash", "-c", "source utils/branch_utils.sh && get_remote_image_name"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result_local.returncode == 0
        assert result_remote.returncode == 0
        
        local_image_bash = result_local.stdout.strip()
        remote_image_bash = result_remote.stdout.strip()
        
        # Should be identical
        assert local_image_python == local_image_bash
        assert remote_image_python == remote_image_bash
    
    def test_branch_specific_behavior(self):
        """Test that different branches would generate different image names."""
        current_branch = get_current_branch()
        current_tag = sanitize_branch_for_docker_tag(current_branch)
        
        # Test with hypothetical different branches
        test_branches = ["main", "feature/test", "analysis/esp-docker-adaptation"]
        
        for branch in test_branches:
            if branch != current_branch:  # Skip current branch
                test_tag = sanitize_branch_for_docker_tag(branch)
                assert test_tag != current_tag  # Should be different
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    def test_branch_parameter_override(self, mock_get_remote_sha):
        """Test that explicit branch parameter overrides auto-detection."""
        mock_get_remote_sha.return_value = "override123"
        
        # Call with explicit branch
        result = self.detector.get_remote_docker_image_commit_sha(branch="main")
        
        assert result == "override123"
        mock_get_remote_sha.assert_called_once_with("main")
    
    def test_error_handling_integration(self):
        """Test error handling across the integrated system."""
        # Test with invalid branch name - should raise ValueError
        with pytest.raises(ValueError, match="Branch name cannot be empty"):
            sanitize_branch_for_docker_tag("")
        
        # Test update detector error handling
        result = self.detector.get_remote_docker_image_commit_sha()
        # Should not raise exception even if remote call fails
        assert result is None or isinstance(result, str)


class TestScriptIntegration:
    """Test integration with actual script files."""
    
    def test_build_script_syntax(self):
        """Test that build script has valid syntax."""
        result = subprocess.run(
            ["bash", "-n", "build/build_image_from_lock_files.sh"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Build script syntax error: {result.stderr}"
    
    def test_push_script_syntax(self):
        """Test that push script has valid syntax."""
        result = subprocess.run(
            ["bash", "-n", "build/push_image_to_github.sh"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Push script syntax error: {result.stderr}"
    
    def test_run_script_syntax(self):
        """Test that run script has valid syntax."""
        result = subprocess.run(
            ["bash", "-n", "run.mac.command"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Run script syntax error: {result.stderr}"
    
    def test_branch_utils_script_functionality(self):
        """Test that branch utilities script functions work."""
        result = subprocess.run(
            ["bash", "utils/branch_utils.sh"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "✅ All branch utilities working correctly" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])