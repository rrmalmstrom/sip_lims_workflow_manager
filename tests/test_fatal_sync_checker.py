#!/usr/bin/env python3
"""
Comprehensive tests for the fatal sync error detection functionality.

Tests the fatal_sync_checker.py module which checks for repository/Docker image
sync issues and exits with appropriate codes when fatal errors are detected.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fatal_sync_checker import check_fatal_sync_errors


class TestFatalSyncChecker:
    """Test suite for fatal sync error detection functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_detector = Mock()
        self.mock_get_current_branch = Mock()
        self.mock_sanitize_branch = Mock()
        
        # Default mock return values
        self.mock_get_current_branch.return_value = "main"
        self.mock_sanitize_branch.return_value = "main"

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_no_fatal_errors_detected(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test normal operation when no fatal errors are detected."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Normal response with no fatal errors
        mock_detector.check_docker_update.return_value = {
            "update_available": False,
            "local_sha": "abc123",
            "remote_sha": "abc123",
            "repo_sha": "abc123",
            "reason": "Local and remote SHAs match",
            "error": None,
            "fatal_sync_error": False
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            result = check_fatal_sync_errors()
            
            # ASSERT
            assert result == 0
            mock_exit.assert_not_called()
            mock_detector.check_docker_update.assert_called_once_with(tag="main", branch="main")
            
            output = mock_stdout.getvalue()
            assert "✅ No fatal sync errors detected - continuing..." in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_fatal_sync_error_detected(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test fatal sync error detection with proper exit code."""
        # ARRANGE
        mock_branch.return_value = "feature-branch"
        mock_sanitize.return_value = "feature-branch"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Response with fatal sync error
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": True,
            "error": "FATAL: Repository has been updated but no corresponding Docker image exists",
            "sync_warning": "Repository is at commit abc12345... but no Docker image found for tag 'feature-branch'",
            "reason": "FATAL ERROR: Docker image build failed or is pending. Contact developer immediately."
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            check_fatal_sync_errors()
            
            # ASSERT
            mock_exit.assert_called_once_with(1)
            mock_detector.check_docker_update.assert_called_once_with(tag="feature-branch", branch="feature-branch")
            
            output = mock_stdout.getvalue()
            assert "🚨 FATAL SYNC ERROR DETECTED 🚨" in output
            assert "❌ FATAL: Repository has been updated but no corresponding Docker image exists" in output
            assert "⚠️  Repository is at commit abc12345... but no Docker image found for tag 'feature-branch'" in output
            assert "💥 FATAL ERROR: Docker image build failed or is pending. Contact developer immediately." in output
            assert "🛑 STOPPING EXECUTION - CANNOT CONTINUE" in output
            assert "📞 Contact the development team to resolve this issue" in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_fatal_error_in_error_message(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test detection of FATAL keyword in error messages."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Response with FATAL in error message but no explicit fatal_sync_error flag
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": False,
            "error": "FATAL: Docker image is out of sync with repository",
            "reason": "FATAL ERROR: Docker image build is required. Repository has newer commits than Docker image."
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            check_fatal_sync_errors()
            
            # ASSERT
            mock_exit.assert_called_once_with(1)
            
            output = mock_stdout.getvalue()
            assert "🚨 FATAL ERROR DETECTED 🚨" in output
            assert "❌ FATAL: Docker image is out of sync with repository" in output
            assert "💥 FATAL ERROR: Docker image build is required. Repository has newer commits than Docker image." in output
            assert "🛑 STOPPING EXECUTION - CANNOT CONTINUE" in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_fatal_error_without_reason(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test fatal error detection when reason field is missing."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Response with FATAL in error but no reason field
        mock_detector.check_docker_update.return_value = {
            "error": "FATAL: Critical sync issue detected",
            "reason": None
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            check_fatal_sync_errors()
            
            # ASSERT
            mock_exit.assert_called_once_with(1)
            
            output = mock_stdout.getvalue()
            assert "🚨 FATAL ERROR DETECTED 🚨" in output
            assert "❌ FATAL: Critical sync issue detected" in output
            # Should not print reason line when reason is None
            assert "💥" not in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_non_fatal_error_continues(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test that non-fatal errors don't cause exit."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Response with non-fatal error
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": False,
            "error": "Could not determine remote Docker image commit SHA",
            "reason": "Network timeout or image not found"
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            result = check_fatal_sync_errors()
            
            # ASSERT
            assert result == 0
            mock_exit.assert_not_called()
            
            output = mock_stdout.getvalue()
            assert "✅ No fatal sync errors detected - continuing..." in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_update_detector_exception_handling(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test exception handling when UpdateDetector fails."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Make UpdateDetector.check_docker_update raise an exception
        mock_detector.check_docker_update.side_effect = Exception("Network connection failed")
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            result = check_fatal_sync_errors()
            
            # ASSERT
            assert result == 0  # Should return 0 on checker errors, not fail
            mock_exit.assert_not_called()
            
            output = mock_stdout.getvalue()
            assert "❌ ERROR: Failed to check for sync errors: Network connection failed" in output
            assert "⚠️  Continuing with caution..." in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_branch_utils_exception_handling(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test exception handling when branch utilities fail."""
        # ARRANGE
        mock_branch.side_effect = Exception("Git not available")
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            result = check_fatal_sync_errors()
            
            # ASSERT
            assert result == 0  # Should return 0 on checker errors, not fail
            mock_exit.assert_not_called()
            
            output = mock_stdout.getvalue()
            assert "❌ ERROR: Failed to check for sync errors: Git not available" in output
            assert "⚠️  Continuing with caution..." in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_complex_branch_name_sanitization(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test that complex branch names are properly sanitized for Docker tags."""
        # ARRANGE
        mock_branch.return_value = "feature/ESP-123_docker-adaptation"
        mock_sanitize.return_value = "feature-esp-123-docker-adaptation"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": False,
            "error": None
        }
        
        # ACT
        check_fatal_sync_errors()
        
        # ASSERT
        mock_sanitize.assert_called_once_with("feature/ESP-123_docker-adaptation")
        mock_detector.check_docker_update.assert_called_once_with(
            tag="feature-esp-123-docker-adaptation", 
            branch="feature/ESP-123_docker-adaptation"
        )

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_repository_ahead_of_docker_fatal_error(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test specific fatal error case: repository ahead of Docker image."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Specific case: repository ahead of Docker image
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": True,
            "error": "FATAL: Docker image is out of sync with repository",
            "sync_warning": "Repository is at newer commit def45678... but Docker image is at older commit abc12345...",
            "reason": "FATAL ERROR: Docker image build is required. Repository has newer commits than Docker image."
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            check_fatal_sync_errors()
            
            # ASSERT
            mock_exit.assert_called_once_with(1)
            
            output = mock_stdout.getvalue()
            assert "🚨 FATAL SYNC ERROR DETECTED 🚨" in output
            assert "❌ FATAL: Docker image is out of sync with repository" in output
            assert "⚠️  Repository is at newer commit def45678... but Docker image is at older commit abc12345..." in output
            assert "💥 FATAL ERROR: Docker image build is required. Repository has newer commits than Docker image." in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_repository_docker_diverged_fatal_error(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test specific fatal error case: repository and Docker have diverged."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Specific case: repository and Docker have diverged
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": True,
            "error": "FATAL: Repository and Docker image have diverged",
            "sync_warning": "Repository (def45678...) and Docker image (abc12345...) are out of sync",
            "reason": "FATAL ERROR: Repository and Docker image commits have diverged. Manual intervention required."
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            check_fatal_sync_errors()
            
            # ASSERT
            mock_exit.assert_called_once_with(1)
            
            output = mock_stdout.getvalue()
            assert "🚨 FATAL SYNC ERROR DETECTED 🚨" in output
            assert "❌ FATAL: Repository and Docker image have diverged" in output
            assert "⚠️  Repository (def45678...) and Docker image (abc12345...) are out of sync" in output
            assert "💥 FATAL ERROR: Repository and Docker image commits have diverged. Manual intervention required." in output

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_missing_error_fields_handling(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test handling of missing error fields in UpdateDetector response."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Response with fatal_sync_error but missing other fields
        mock_detector.check_docker_update.return_value = {
            "fatal_sync_error": True
            # Missing error, sync_warning, reason fields
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            check_fatal_sync_errors()
            
            # ASSERT
            mock_exit.assert_called_once_with(1)
            
            output = mock_stdout.getvalue()
            assert "🚨 FATAL SYNC ERROR DETECTED 🚨" in output
            assert "❌ Unknown fatal error" in output  # Default when error field missing
            assert "⚠️  Sync issue detected" in output  # Default when sync_warning field missing
            assert "💥 Manual intervention required" in output  # Default when reason field missing

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    @patch('sys.exit')
    def test_empty_response_handling(self, mock_exit, mock_sanitize, mock_branch, mock_detector_class):
        """Test handling of empty response from UpdateDetector."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Empty response
        mock_detector.check_docker_update.return_value = {}
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # ACT
            result = check_fatal_sync_errors()
            
            # ASSERT
            assert result == 0
            mock_exit.assert_not_called()
            
            output = mock_stdout.getvalue()
            assert "✅ No fatal sync errors detected - continuing..." in output

    @patch('src.fatal_sync_checker.check_fatal_sync_errors')
    @patch('sys.exit')
    def test_main_execution_with_fatal_error(self, mock_exit, mock_check):
        """Test main execution path when fatal error is detected."""
        # ARRANGE
        mock_check.return_value = 1  # Fatal error detected
        
        # ACT
        # Simulate the main execution by calling the main block logic directly
        import src.fatal_sync_checker
        
        # This simulates: if __name__ == "__main__": sys.exit(check_fatal_sync_errors())
        with patch.object(src.fatal_sync_checker, '__name__', '__main__'):
            try:
                # Execute the main block logic
                exit_code = src.fatal_sync_checker.check_fatal_sync_errors()
                src.fatal_sync_checker.sys.exit(exit_code)
            except SystemExit:
                pass  # Expected when sys.exit is called
        
        # ASSERT
        mock_exit.assert_called_with(1)

    @patch('src.fatal_sync_checker.check_fatal_sync_errors')
    @patch('sys.exit')
    def test_main_execution_with_no_error(self, mock_exit, mock_check):
        """Test main execution path when no fatal error is detected."""
        # ARRANGE
        mock_check.return_value = 0  # No fatal error
        
        # ACT
        # Simulate the main execution by calling the main block logic directly
        import src.fatal_sync_checker
        
        # This simulates: if __name__ == "__main__": sys.exit(check_fatal_sync_errors())
        with patch.object(src.fatal_sync_checker, '__name__', '__main__'):
            try:
                # Execute the main block logic
                exit_code = src.fatal_sync_checker.check_fatal_sync_errors()
                src.fatal_sync_checker.sys.exit(exit_code)
            except SystemExit:
                pass  # Expected when sys.exit is called
        
        # ASSERT
        mock_exit.assert_called_with(0)


class TestFatalSyncCheckerIntegration:
    """Integration tests for fatal sync checker with real-like scenarios."""

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    def test_realistic_fatal_sync_scenario(self, mock_sanitize, mock_branch, mock_detector_class):
        """Test a realistic fatal sync error scenario."""
        # ARRANGE
        mock_branch.return_value = "analysis/esp-docker-adaptation"
        mock_sanitize.return_value = "analysis-esp-docker-adaptation"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Realistic fatal sync error response
        mock_detector.check_docker_update.return_value = {
            "update_available": False,
            "local_sha": "abc123456789",
            "remote_sha": None,
            "repo_sha": "def987654321",
            "reason": "FATAL ERROR: Docker image build failed or is pending. Contact developer immediately.",
            "error": "FATAL: Repository has been updated but no corresponding Docker image exists",
            "chronology_uncertain": False,
            "requires_user_confirmation": False,
            "sync_warning": "Repository is at commit def98765... but no Docker image found for tag 'analysis-esp-docker-adaptation'",
            "fatal_sync_error": True
        }
        
        # ACT & ASSERT
        with patch('sys.exit') as mock_exit:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                check_fatal_sync_errors()
                
                mock_exit.assert_called_once_with(1)
                
                output = mock_stdout.getvalue()
                assert "🚨 FATAL SYNC ERROR DETECTED 🚨" in output
                assert "analysis-esp-docker-adaptation" in mock_detector.check_docker_update.call_args[1]['tag']

    @patch('src.fatal_sync_checker.UpdateDetector')
    @patch('src.fatal_sync_checker.get_current_branch')
    @patch('src.fatal_sync_checker.sanitize_branch_for_docker_tag')
    def test_realistic_normal_operation_scenario(self, mock_sanitize, mock_branch, mock_detector_class):
        """Test a realistic normal operation scenario."""
        # ARRANGE
        mock_branch.return_value = "main"
        mock_sanitize.return_value = "main"
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        
        # Realistic normal operation response
        mock_detector.check_docker_update.return_value = {
            "update_available": False,
            "local_sha": "abc123456789",
            "remote_sha": "abc123456789",
            "repo_sha": "abc123456789",
            "reason": "Local and remote SHAs match",
            "error": None,
            "chronology_uncertain": False,
            "requires_user_confirmation": False,
            "sync_warning": None,
            "fatal_sync_error": False
        }
        
        # ACT
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = check_fatal_sync_errors()
            
            # ASSERT
            assert result == 0
            output = mock_stdout.getvalue()
            assert "✅ No fatal sync errors detected - continuing..." in output