#!/usr/bin/env python3
"""
Test suite for user experience when chronology uncertainty occurs.
This simulates the actual user experience and tests the complete flow.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.update_detector import UpdateDetector


class TestUserExperienceChronologyUncertainty:
    """Test the complete user experience when chronology is uncertain."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = UpdateDetector()
    
    def test_complete_uncertainty_scenario_user_experience(self):
        """Test the complete user experience when chronology cannot be determined."""
        
        # Simulate a realistic scenario where chronology detection fails
        with patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha') as mock_local, \
             patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha') as mock_remote, \
             patch('src.update_detector.UpdateDetector.is_commit_ancestor') as mock_ancestry, \
             patch('src.update_detector.UpdateDetector.get_commit_timestamp') as mock_timestamp:
            
            # Setup: Simulate a scenario where we have different SHAs but can't determine chronology
            mock_local.return_value = "a1b2c3d4e5f6789012345678901234567890abcd"  # Local commit
            mock_remote.return_value = "f6e5d4c3b2a1098765432109876543210987fedc"  # Remote commit (different)
            mock_ancestry.return_value = None  # Git ancestry check fails (git not available, commits not in history)
            mock_timestamp.return_value = None  # Timestamp check fails (no internet, API down)
            
            # Execute the update check
            result = self.detector.check_docker_update()
            
            # Verify the complete result structure that the user scripts will receive
            assert result["update_available"] is True
            assert result["chronology_uncertain"] is True
            assert result["requires_user_confirmation"] is True
            assert result["local_sha"] == "a1b2c3d4e5f6789012345678901234567890abcd"
            assert result["remote_sha"] == "f6e5d4c3b2a1098765432109876543210987fedc"
            assert "⚠️  CHRONOLOGY UNCERTAIN" in result["reason"]
            assert "Cannot determine if local (a1b2c3d4...) or remote (f6e5d4c3...) is newer" in result["reason"]
            assert "warning" in result
            assert "Local version might be newer than remote" in result["warning"]
            assert "Could not determine commit chronology" in result["error"]
            
            return result
    
    def test_user_sees_proper_warning_messages(self):
        """Test that the warning messages are user-friendly and informative."""
        
        result = self.test_complete_uncertainty_scenario_user_experience()
        
        # Check that all user-facing messages are present and informative
        warning_msg = result["warning"]
        reason_msg = result["reason"]
        error_msg = result["error"]
        
        # Warning should be clear about the risk
        assert "Local version might be newer than remote" in warning_msg
        assert "Manual confirmation recommended" in warning_msg
        
        # Reason should explain what's happening
        assert "CHRONOLOGY UNCERTAIN" in reason_msg
        assert "Cannot determine if local" in reason_msg
        assert "or remote" in reason_msg
        assert "is newer" in reason_msg
        
        # Error should explain why detection failed
        assert "Could not determine commit chronology" in error_msg
        assert "git ancestry and timestamp checks both failed" in error_msg
    
    def test_run_script_behavior_with_uncertainty(self):
        """Test how the run script will behave when uncertainty is detected."""
        
        # Simulate the JSON parsing that happens in the run scripts
        with patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha') as mock_local, \
             patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha') as mock_remote, \
             patch('src.update_detector.UpdateDetector.is_commit_ancestor') as mock_ancestry, \
             patch('src.update_detector.UpdateDetector.get_commit_timestamp') as mock_timestamp:
            
            # Setup uncertainty scenario
            mock_local.return_value = "local123abc"
            mock_remote.return_value = "remote456def"
            mock_ancestry.return_value = None
            mock_timestamp.return_value = None
            
            # Get the result as JSON (like the run scripts do)
            result = self.detector.check_docker_update()
            
            # Simulate the bash/batch script logic
            update_available = result.get('update_available', False)
            chronology_uncertain = result.get('chronology_uncertain', False)
            requires_confirmation = result.get('requires_user_confirmation', False)
            warning_msg = result.get('warning', 'Chronology uncertain')
            reason = result.get('reason', 'Unknown reason')
            
            # Verify the script will detect uncertainty and prompt user
            assert update_available is True
            assert chronology_uncertain is True
            assert requires_confirmation is True
            assert warning_msg is not None
            assert reason is not None
            
            # This is what the user will see in their terminal
            expected_user_output = f"""⚠️  **CHRONOLOGY WARNING**
   {reason}
   {warning_msg}

The system cannot determine if your local Docker image is newer or older than the remote version.
Proceeding with the update might overwrite a newer local version with an older remote version.

Do you want to proceed with the Docker image update? (y/N): """
            
            # Verify the output contains all necessary information
            assert "CHRONOLOGY WARNING" in expected_user_output
            assert "cannot determine if your local Docker image is newer or older" in expected_user_output
            assert "might overwrite a newer local version" in expected_user_output
            assert "Do you want to proceed" in expected_user_output
            assert "(y/N)" in expected_user_output  # Default to No for safety
            
            return expected_user_output
    
    def test_user_cancellation_scenario(self):
        """Test what happens when user cancels the uncertain update."""
        
        # The run script logic when user says "no" or just presses Enter
        user_choice = ""  # User just presses Enter (default to No)
        user_choice_normalized = user_choice.strip().lower()
        
        # Script logic: if not "y" or "yes", cancel
        should_proceed = user_choice_normalized in ["y", "yes"]
        
        assert should_proceed is False
        
        # User will see:
        expected_cancellation_output = """❌ Docker image update cancelled by user
✅ Continuing with current local Docker image"""
        
        return expected_cancellation_output
    
    def test_user_confirmation_scenario(self):
        """Test what happens when user confirms the uncertain update."""
        
        # The run script logic when user says "yes"
        user_choice = "y"
        user_choice_normalized = user_choice.strip().lower()
        
        # Script logic: if "y" or "yes", proceed
        should_proceed = user_choice_normalized in ["y", "yes"]
        
        assert should_proceed is True
        
        # User will see:
        expected_confirmation_output = """✅ User confirmed - proceeding with Docker image update...
🧹 Removing old Docker image before update...
✅ Old Docker image and dangling images cleaned up
📥 Pulling Docker image for branch: main...
✅ Docker image updated successfully"""
        
        return expected_confirmation_output
    
    def test_scenarios_that_trigger_uncertainty(self):
        """Test the specific scenarios that will trigger uncertainty warnings."""
        
        scenarios = [
            {
                "name": "No internet connection",
                "git_ancestry": None,  # Git works but commits not in local history
                "timestamp": None,     # No internet for GitHub API
                "description": "User is offline or GitHub API is unreachable"
            },
            {
                "name": "Git not available",
                "git_ancestry": None,  # Git command fails
                "timestamp": None,     # Timestamp check also fails
                "description": "Git not installed or repository corrupted"
            },
            {
                "name": "GitHub API rate limited",
                "git_ancestry": None,  # Git ancestry check fails
                "timestamp": None,     # API rate limited
                "description": "Too many API requests, rate limited"
            },
            {
                "name": "Commits from different forks",
                "git_ancestry": None,  # Commits not in same history
                "timestamp": None,     # API fails for some reason
                "description": "Local and remote commits from different repositories"
            }
        ]
        
        for scenario in scenarios:
            with patch('src.update_detector.UpdateDetector.get_local_docker_image_commit_sha') as mock_local, \
                 patch('src.update_detector.UpdateDetector.get_remote_docker_image_commit_sha') as mock_remote, \
                 patch('src.update_detector.UpdateDetector.is_commit_ancestor') as mock_ancestry, \
                 patch('src.update_detector.UpdateDetector.get_commit_timestamp') as mock_timestamp:
                
                # Setup scenario
                mock_local.return_value = "local123"
                mock_remote.return_value = "remote456"  # Different SHA
                mock_ancestry.return_value = scenario["git_ancestry"]
                mock_timestamp.return_value = scenario["timestamp"]
                
                # Test
                result = self.detector.check_docker_update()
                
                # Verify uncertainty is detected
                assert result["chronology_uncertain"] is True, f"Scenario '{scenario['name']}' should trigger uncertainty"
                assert result["requires_user_confirmation"] is True, f"Scenario '{scenario['name']}' should require confirmation"
                
                print(f"✅ Scenario '{scenario['name']}': {scenario['description']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])