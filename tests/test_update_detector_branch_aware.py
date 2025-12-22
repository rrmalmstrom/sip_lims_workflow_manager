#!/usr/bin/env python3
"""
Test suite for branch-aware update detector functionality.
Tests the enhanced update detection that uses current branch instead of hardcoded branch.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.update_detector import UpdateDetector


class TestBranchAwareUpdateDetector:
    """Test branch-aware functionality in UpdateDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = UpdateDetector()
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    @patch('utils.branch_utils.get_current_branch')
    def test_get_remote_docker_image_commit_sha_uses_current_branch(self, mock_get_branch, mock_get_remote_sha):
        """Test that remote SHA detection uses current branch when no branch specified."""
        # Setup
        mock_get_branch.return_value = "analysis/esp-docker-adaptation"
        mock_get_remote_sha.return_value = "abc123def456"
        
        # Execute
        result = self.detector.get_remote_docker_image_commit_sha()
        
        # Verify
        assert result == "abc123def456"
        mock_get_branch.assert_called_once()
        mock_get_remote_sha.assert_called_once_with("analysis/esp-docker-adaptation")
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    def test_get_remote_docker_image_commit_sha_uses_specified_branch(self, mock_get_remote_sha):
        """Test that remote SHA detection uses specified branch when provided."""
        # Setup
        mock_get_remote_sha.return_value = "xyz789abc123"
        
        # Execute
        result = self.detector.get_remote_docker_image_commit_sha(branch="main")
        
        # Verify
        assert result == "xyz789abc123"
        mock_get_remote_sha.assert_called_once_with("main")
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    @patch('utils.branch_utils.get_current_branch')
    def test_get_remote_docker_image_commit_sha_fallback_to_main_on_import_error(self, mock_get_branch, mock_get_remote_sha):
        """Test fallback to main branch when branch utils import fails."""
        # Setup - simulate ImportError
        mock_get_branch.side_effect = ImportError("Module not found")
        mock_get_remote_sha.return_value = "fallback123"
        
        # Execute
        result = self.detector.get_remote_docker_image_commit_sha()
        
        # Verify
        assert result == "fallback123"
        mock_get_remote_sha.assert_called_once_with("main")
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    @patch('utils.branch_utils.get_current_branch')
    def test_get_remote_docker_image_commit_sha_fallback_to_main_on_exception(self, mock_get_branch, mock_get_remote_sha):
        """Test fallback to main branch when branch detection fails."""
        # Setup - simulate general exception
        mock_get_branch.side_effect = Exception("Git error")
        mock_get_remote_sha.return_value = "fallback456"
        
        # Execute
        result = self.detector.get_remote_docker_image_commit_sha()
        
        # Verify
        assert result == "fallback456"
        mock_get_remote_sha.assert_called_once_with("main")
    
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    def test_get_remote_docker_image_commit_sha_returns_none_on_error(self, mock_get_remote_sha):
        """Test that method returns None when remote SHA retrieval fails."""
        # Setup
        mock_get_remote_sha.side_effect = Exception("API error")
        
        # Execute
        result = self.detector.get_remote_docker_image_commit_sha()
        
        # Verify
        assert result is None
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    def test_check_docker_update_passes_branch_parameter(self, mock_get_remote_sha, mock_get_local_sha):
        """Test that check_docker_update passes branch parameter to remote SHA method."""
        # Setup
        mock_get_local_sha.return_value = "local123"
        mock_get_remote_sha.return_value = "remote456"
        
        # Execute
        result = self.detector.check_docker_update(branch="feature/test")
        
        # Verify
        mock_get_remote_sha.assert_called_once_with("latest", "feature/test")
        assert result["local_sha"] == "local123"
        assert result["remote_sha"] == "remote456"
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    def test_check_docker_update_auto_detects_branch_when_none_specified(self, mock_get_remote_sha, mock_get_local_sha):
        """Test that check_docker_update auto-detects branch when none specified."""
        # Setup
        mock_get_local_sha.return_value = "local789"
        mock_get_remote_sha.return_value = "remote789"
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify
        mock_get_remote_sha.assert_called_once_with("latest", None)
        assert result["local_sha"] == "local789"
        assert result["remote_sha"] == "remote789"
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.is_commit_ancestor')
    def test_check_docker_update_preserves_existing_logic(self, mock_is_ancestor, mock_get_remote_sha, mock_get_local_sha):
        """Test that branch-aware changes preserve existing SHA comparison logic."""
        # Setup
        mock_get_local_sha.return_value = "local123"
        mock_get_remote_sha.return_value = "remote456"
        mock_is_ancestor.return_value = True  # local is ancestor of remote
        
        # Execute
        result = self.detector.check_docker_update(branch="main")
        
        # Verify existing logic is preserved
        assert result["update_available"] is True
        assert "newer than local" in result["reason"]
        mock_is_ancestor.assert_called_once_with("local123", "remote456")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])