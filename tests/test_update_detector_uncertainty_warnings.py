#!/usr/bin/env python3
"""
Test suite for uncertainty warning functionality in UpdateDetector.
Tests the new chronology uncertainty detection and user confirmation features.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.update_detector import UpdateDetector


class TestUpdateDetectorUncertaintyWarnings:
    """Test uncertainty warning functionality in UpdateDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = UpdateDetector()
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.is_commit_ancestor')
    @patch('src.update_detector.UpdateDetector.get_commit_timestamp')
    def test_check_docker_update_sets_uncertainty_flags_when_chronology_fails(
        self, mock_get_timestamp, mock_is_ancestor, mock_get_remote_sha, mock_get_local_sha
    ):
        """Test that uncertainty flags are set when both git ancestry and timestamp checks fail."""
        # Setup - simulate scenario where chronology cannot be determined
        mock_get_local_sha.return_value = "local123abc"
        mock_get_remote_sha.return_value = "remote456def"
        mock_is_ancestor.return_value = None  # Git ancestry check fails
        mock_get_timestamp.return_value = None  # Timestamp check fails
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify uncertainty flags are set
        assert result["chronology_uncertain"] is True
        assert result["requires_user_confirmation"] is True
        assert result["update_available"] is True  # Still suggests update but with warning
        assert "⚠️  CHRONOLOGY UNCERTAIN" in result["reason"]
        assert "warning" in result
        assert "Local version might be newer than remote" in result["warning"]
        assert "Could not determine commit chronology" in result["error"]
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.is_commit_ancestor')
    def test_check_docker_update_no_uncertainty_when_git_ancestry_works(
        self, mock_is_ancestor, mock_get_remote_sha, mock_get_local_sha
    ):
        """Test that uncertainty flags are NOT set when git ancestry check succeeds."""
        # Setup - git ancestry check succeeds
        mock_get_local_sha.return_value = "local123abc"
        mock_get_remote_sha.return_value = "remote456def"
        mock_is_ancestor.return_value = True  # Local is ancestor of remote
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify uncertainty flags are NOT set
        assert result["chronology_uncertain"] is False
        assert result["requires_user_confirmation"] is False
        assert result["update_available"] is True
        assert "newer than local" in result["reason"]
        assert "warning" not in result
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.is_commit_ancestor')
    @patch('src.update_detector.UpdateDetector.get_commit_timestamp')
    def test_check_docker_update_no_uncertainty_when_timestamp_works(
        self, mock_get_timestamp, mock_is_ancestor, mock_get_remote_sha, mock_get_local_sha
    ):
        """Test that uncertainty flags are NOT set when timestamp comparison succeeds."""
        from datetime import datetime
        
        # Setup - git ancestry fails but timestamp succeeds
        mock_get_local_sha.return_value = "local123abc"
        mock_get_remote_sha.return_value = "remote456def"
        mock_is_ancestor.return_value = None  # Git ancestry check fails
        
        # Remote is newer than local
        local_time = datetime(2024, 1, 1, 12, 0, 0)
        remote_time = datetime(2024, 1, 2, 12, 0, 0)
        mock_get_timestamp.side_effect = [local_time, remote_time]
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify uncertainty flags are NOT set
        assert result["chronology_uncertain"] is False
        assert result["requires_user_confirmation"] is False
        assert result["update_available"] is True
        assert "newer" in result["reason"]
        assert "warning" not in result
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    def test_check_docker_update_no_uncertainty_when_shas_match(
        self, mock_get_remote_sha, mock_get_local_sha
    ):
        """Test that uncertainty flags are NOT set when local and remote SHAs match."""
        # Setup - identical SHAs
        mock_get_local_sha.return_value = "same123abc"
        mock_get_remote_sha.return_value = "same123abc"
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify uncertainty flags are NOT set
        assert result["chronology_uncertain"] is False
        assert result["requires_user_confirmation"] is False
        assert result["update_available"] is False
        assert "Local and remote SHAs match" in result["reason"]
        assert "warning" not in result
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.is_commit_ancestor')
    def test_check_docker_update_no_uncertainty_when_local_is_newer(
        self, mock_is_ancestor, mock_get_remote_sha, mock_get_local_sha
    ):
        """Test that uncertainty flags are NOT set when local is determined to be newer."""
        # Setup - remote is ancestor of local (local is newer)
        mock_get_local_sha.return_value = "local123abc"
        mock_get_remote_sha.return_value = "remote456def"
        mock_is_ancestor.side_effect = [False, True]  # local not ancestor of remote, but remote is ancestor of local
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify uncertainty flags are NOT set
        assert result["chronology_uncertain"] is False
        assert result["requires_user_confirmation"] is False
        assert result["update_available"] is False
        assert "Local commit" in result["reason"] and "is newer than remote" in result["reason"]
        assert "warning" not in result
    
    @patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha')
    @patch('src.update_detector.UpdateDetector.is_commit_ancestor')
    def test_check_docker_update_no_uncertainty_when_branches_diverged(
        self, mock_is_ancestor, mock_get_remote_sha, mock_get_local_sha
    ):
        """Test that uncertainty flags are NOT set when branches have diverged."""
        # Setup - neither is ancestor of the other (diverged branches)
        mock_get_local_sha.return_value = "local123abc"
        mock_get_remote_sha.return_value = "remote456def"
        mock_is_ancestor.side_effect = [False, False]  # Neither is ancestor of the other
        
        # Execute
        result = self.detector.check_docker_update()
        
        # Verify uncertainty flags are NOT set
        assert result["chronology_uncertain"] is False
        assert result["requires_user_confirmation"] is False
        assert result["update_available"] is False
        assert "diverged" in result["reason"]
        assert "warning" not in result
    
    def test_get_update_summary_includes_uncertainty_fields(self):
        """Test that get_update_summary includes the new uncertainty fields."""
        # Mock the check_docker_update method to return uncertainty flags
        with patch.object(self.detector, 'check_docker_update') as mock_check:
            mock_check.return_value = {
                "update_available": True,
                "chronology_uncertain": True,
                "requires_user_confirmation": True,
                "local_sha": "local123",
                "remote_sha": "remote456",
                "reason": "Test reason",
                "error": None,
                "warning": "Test warning"
            }
            
            # Execute
            result = self.detector.get_update_summary()
            
            # Verify uncertainty fields are included in summary
            assert result["chronology_uncertain"] is True
            assert result["requires_user_confirmation"] is True
            assert result["any_updates_available"] is True
            assert "timestamp" in result
            assert "docker" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])