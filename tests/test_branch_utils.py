#!/usr/bin/env python3
"""
Test suite for branch utilities module.
Tests branch detection, Docker tag sanitization, and image name generation.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the module we're testing (will be created)
from utils.branch_utils import (
    get_current_branch,
    sanitize_branch_for_docker_tag,
    get_docker_tag_for_current_branch,
    get_local_image_name_for_current_branch,
    get_remote_image_name_for_current_branch,
    GitRepositoryError,
    BranchDetectionError,
    REGISTRY_BASE,
    LOCAL_IMAGE_BASE,
    MAX_DOCKER_TAG_LENGTH
)


class TestGetCurrentBranch:
    """Test branch detection functionality."""
    
    @patch('subprocess.run')
    def test_main_branch(self, mock_run):
        """Test detection of main branch."""
        mock_run.return_value = MagicMock(
            stdout="main\n",
            returncode=0
        )
        
        result = get_current_branch()
        
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        assert result == "main"

    @patch('subprocess.run')
    def test_development_branch(self, mock_run):
        """Test detection of development branch."""
        mock_run.return_value = MagicMock(
            stdout="analysis/esp-docker-adaptation\n",
            returncode=0
        )
        
        result = get_current_branch()
        assert result == "analysis/esp-docker-adaptation"

    @patch('subprocess.run')
    def test_feature_branch(self, mock_run):
        """Test detection of feature branch."""
        mock_run.return_value = MagicMock(
            stdout="feature/user-auth\n",
            returncode=0
        )
        
        result = get_current_branch()
        assert result == "feature/user-auth"

    @patch('subprocess.run')
    def test_detached_head(self, mock_run):
        """Test detached HEAD state handling - should raise error."""
        mock_run.return_value = MagicMock(
            stdout="HEAD\n",
            returncode=0
        )
        
        with pytest.raises(BranchDetectionError) as exc_info:
            get_current_branch()
        
        assert "detached HEAD" in str(exc_info.value)
        assert "checkout a branch" in str(exc_info.value)

    @patch('subprocess.run')
    def test_git_repository_error(self, mock_run):
        """Test Git command failure (not in repository)."""
        mock_run.side_effect = subprocess.CalledProcessError(128, 'git')
        
        with pytest.raises(GitRepositoryError) as exc_info:
            get_current_branch()
        
        assert "Git repository" in str(exc_info.value)

    @patch('subprocess.run')
    def test_empty_output(self, mock_run):
        """Test empty Git output."""
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=0
        )
        
        with pytest.raises(BranchDetectionError) as exc_info:
            get_current_branch()
        
        assert "empty" in str(exc_info.value).lower()

    @patch('subprocess.run')
    def test_whitespace_handling(self, mock_run):
        """Test that whitespace is properly stripped."""
        mock_run.return_value = MagicMock(
            stdout="  main  \n\t",
            returncode=0
        )
        
        result = get_current_branch()
        assert result == "main"


class TestSanitizeBranch:
    """Test Docker tag sanitization functionality."""
    
    def test_main_branch_unchanged(self):
        """Test main branch passes through unchanged."""
        result = sanitize_branch_for_docker_tag("main")
        assert result == "main"

    def test_slash_replacement(self):
        """Test slash replacement with dashes."""
        result = sanitize_branch_for_docker_tag("analysis/esp-docker-adaptation")
        assert result == "analysis-esp-docker-adaptation"

    def test_underscore_replacement(self):
        """Test underscore replacement with dashes."""
        result = sanitize_branch_for_docker_tag("feature_auth")
        assert result == "feature-auth"

    def test_case_conversion(self):
        """Test uppercase to lowercase conversion."""
        result = sanitize_branch_for_docker_tag("Feature/User_Auth")
        assert result == "feature-user-auth"

    def test_multiple_slashes(self):
        """Test multiple slash replacement."""
        result = sanitize_branch_for_docker_tag("feature/sub/branch")
        assert result == "feature-sub-branch"

    def test_invalid_characters_removed(self):
        """Test invalid character removal."""
        result = sanitize_branch_for_docker_tag("feature@#$%auth")
        assert result == "feature-auth"

    def test_leading_invalid_chars_removed(self):
        """Test removal of leading periods and dashes."""
        assert sanitize_branch_for_docker_tag(".feature") == "feature"
        assert sanitize_branch_for_docker_tag("-feature") == "feature"
        assert sanitize_branch_for_docker_tag(".-feature") == "feature"

    def test_trailing_invalid_chars_removed(self):
        """Test removal of trailing periods and dashes."""
        assert sanitize_branch_for_docker_tag("feature.") == "feature"
        assert sanitize_branch_for_docker_tag("feature-") == "feature"
        assert sanitize_branch_for_docker_tag("feature.-") == "feature"

    def test_length_limit_enforced(self):
        """Test length truncation to Docker tag limits."""
        long_name = "a" * 150
        result = sanitize_branch_for_docker_tag(long_name)
        assert len(result) <= MAX_DOCKER_TAG_LENGTH

    def test_empty_string_handling(self):
        """Test empty string input."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_branch_for_docker_tag("")
        assert "empty" in str(exc_info.value).lower()

    def test_only_invalid_chars(self):
        """Test string with only invalid characters."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_branch_for_docker_tag("@#$%")
        assert "valid" in str(exc_info.value).lower()

    def test_complex_branch_name(self):
        """Test complex real-world branch name."""
        result = sanitize_branch_for_docker_tag("Feature/User_Auth-v2.1@hotfix")
        assert result == "feature-user-auth-v2.1-hotfix"

    def test_hyphenated_branch_name(self):
        """Test branch name that already contains hyphens."""
        result = sanitize_branch_for_docker_tag("feature-branch-name")
        assert result == "feature-branch-name"


class TestDockerTagGeneration:
    """Test Docker tag generation functions."""
    
    @patch('utils.branch_utils.get_current_branch')
    def test_get_docker_tag_for_current_branch(self, mock_get_branch):
        """Test complete tag generation for current branch."""
        mock_get_branch.return_value = "analysis/esp-docker-adaptation"
        
        result = get_docker_tag_for_current_branch()
        
        mock_get_branch.assert_called_once()
        assert result == "analysis-esp-docker-adaptation"

    @patch('utils.branch_utils.get_current_branch')
    def test_get_docker_tag_error_propagation(self, mock_get_branch):
        """Test error propagation from branch detection."""
        mock_get_branch.side_effect = GitRepositoryError("Not in repo")
        
        with pytest.raises(GitRepositoryError):
            get_docker_tag_for_current_branch()


class TestImageNameGeneration:
    """Test Docker image name generation functions."""
    
    @patch('utils.branch_utils.get_docker_tag_for_current_branch')
    def test_get_local_image_name(self, mock_get_tag):
        """Test local image name generation."""
        mock_get_tag.return_value = "main"
        
        result = get_local_image_name_for_current_branch()
        
        mock_get_tag.assert_called_once()
        assert result == f"{LOCAL_IMAGE_BASE}:main"

    @patch('utils.branch_utils.get_docker_tag_for_current_branch')
    def test_get_remote_image_name(self, mock_get_tag):
        """Test remote image name generation."""
        mock_get_tag.return_value = "analysis-esp-docker-adaptation"
        
        result = get_remote_image_name_for_current_branch()
        
        mock_get_tag.assert_called_once()
        assert result == f"{REGISTRY_BASE}:analysis-esp-docker-adaptation"

    @patch('utils.branch_utils.get_docker_tag_for_current_branch')
    def test_image_name_error_propagation(self, mock_get_tag):
        """Test error propagation in image name generation."""
        mock_get_tag.side_effect = BranchDetectionError("Branch detection failed")
        
        with pytest.raises(BranchDetectionError):
            get_local_image_name_for_current_branch()
        
        with pytest.raises(BranchDetectionError):
            get_remote_image_name_for_current_branch()


class TestConstants:
    """Test module constants are properly defined."""
    
    def test_registry_base_defined(self):
        """Test registry base constant."""
        assert REGISTRY_BASE == "ghcr.io/rrmalmstrom/sip_lims_workflow_manager"

    def test_local_image_base_defined(self):
        """Test local image base constant."""
        assert LOCAL_IMAGE_BASE == "sip-lims-workflow-manager"

    def test_max_tag_length_defined(self):
        """Test max tag length constant."""
        assert MAX_DOCKER_TAG_LENGTH == 128
        assert isinstance(MAX_DOCKER_TAG_LENGTH, int)


class TestErrorClasses:
    """Test custom exception classes."""
    
    def test_git_repository_error(self):
        """Test GitRepositoryError exception."""
        error = GitRepositoryError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)

    def test_branch_detection_error(self):
        """Test BranchDetectionError exception."""
        error = BranchDetectionError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)


# Integration tests that work with actual Git repository
class TestIntegration:
    """Integration tests with real Git repository."""
    
    def test_real_git_repository(self):
        """Test with actual Git repository (if available)."""
        try:
            # This test only runs if we're in a Git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # If we get here, we're in a Git repo
            branch = get_current_branch()
            assert isinstance(branch, str)
            assert len(branch) > 0
            
            # Test tag generation
            tag = get_docker_tag_for_current_branch()
            assert isinstance(tag, str)
            assert len(tag) > 0
            
            # Verify it's a valid Docker tag
            assert tag.islower()
            assert not tag.startswith('.')
            assert not tag.startswith('-')
            assert len(tag) <= MAX_DOCKER_TAG_LENGTH
            
        except subprocess.CalledProcessError:
            # Not in a Git repository, skip this test
            pytest.skip("Not in a Git repository")

    def test_docker_tag_validity(self):
        """Test that generated tags are valid Docker tags."""
        test_branches = [
            "main",
            "analysis/esp-docker-adaptation",
            "feature/user-auth",
            "Feature/User_Auth",
            "hotfix/bug-123"
        ]
        
        for branch in test_branches:
            tag = sanitize_branch_for_docker_tag(branch)
            
            # Docker tag validation rules
            assert tag.islower(), f"Tag '{tag}' should be lowercase"
            assert not tag.startswith('.'), f"Tag '{tag}' should not start with period"
            assert not tag.startswith('-'), f"Tag '{tag}' should not start with dash"
            assert len(tag) <= MAX_DOCKER_TAG_LENGTH, f"Tag '{tag}' too long"
            
            # Should only contain valid characters
            import re
            assert re.match(r'^[a-z0-9.-]+$', tag), f"Tag '{tag}' contains invalid characters"


if __name__ == "__main__":
    pytest.main([__file__])