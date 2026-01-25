#!/usr/bin/env python3

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import urllib.error
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_utils import GitUtils


class TestGitUtilsErrorHandling:
    """Test error handling and timeout behavior in GitUtils."""
    
    def setup_method(self):
        """Set up test environment."""
        self.git_utils = GitUtils("test_owner", "test_repo")
    
    def test_get_local_commit_sha_git_not_found(self):
        """Test behavior when git command is not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("git command not found")
            
            result = self.git_utils.get_local_commit_sha()
            
            assert result is None
            mock_run.assert_called_once()
    
    def test_get_local_commit_sha_git_error(self):
        """Test behavior when git command fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            result = self.git_utils.get_local_commit_sha()
            
            assert result is None
            mock_run.assert_called_once()
    
    def test_get_remote_commit_sha_network_timeout(self):
        """Test behavior when GitHub API times out."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection timeout")
            
            result = self.git_utils.get_remote_commit_sha("main")
            
            assert result is None
            mock_urlopen.assert_called_once()
    
    def test_get_remote_commit_sha_invalid_json(self):
        """Test behavior when GitHub API returns invalid JSON."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b"invalid json"
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            result = self.git_utils.get_remote_commit_sha("main")
            
            assert result is None
    
    def test_get_remote_commit_sha_missing_sha_field(self):
        """Test behavior when GitHub API response is missing SHA field."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({"message": "Not Found"}).encode()
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            result = self.git_utils.get_remote_commit_sha("nonexistent-branch")
            
            assert result is None
    
    def test_get_commit_timestamp_network_error(self):
        """Test behavior when timestamp request fails."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="test", code=404, msg="Not Found", hdrs=None, fp=None
            )
            
            result = self.git_utils.get_commit_timestamp("abc123")
            
            assert result is None
    
    def test_get_commit_timestamp_invalid_timestamp_format(self):
        """Test behavior when timestamp format is invalid."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "commit": {
                    "committer": {
                        "date": "invalid-timestamp-format"
                    }
                }
            }).encode()
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            result = self.git_utils.get_commit_timestamp("abc123")
            
            assert result is None
    
    def test_is_commit_ancestor_git_not_available(self):
        """Test behavior when git merge-base command is not available."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            
            result = self.git_utils.is_commit_ancestor("abc123", "def456")
            
            assert result is None
    
    def test_is_commit_ancestor_git_error(self):
        """Test behavior when git merge-base fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git merge-base")
            
            result = self.git_utils.is_commit_ancestor("abc123", "def456")
            
            assert result is None
    
    def test_get_current_branch_git_error(self):
        """Test behavior when getting current branch fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git branch")
            
            result = self.git_utils.get_current_branch()
            
            assert result is None
    
    def test_check_repository_updates_no_local_sha(self):
        """Test repository update check when local SHA cannot be determined."""
        with patch.object(self.git_utils, 'get_local_commit_sha', return_value=None):
            result = self.git_utils.check_repository_updates("main")
            
            assert result["update_available"] is False
            assert result["local_sha"] is None
            assert "Could not determine local commit SHA" in result["reason"]
            assert result["error"] is not None
    
    def test_check_repository_updates_no_remote_sha(self):
        """Test repository update check when remote SHA cannot be determined."""
        with patch.object(self.git_utils, 'get_local_commit_sha', return_value="abc123"), \
             patch.object(self.git_utils, 'get_remote_commit_sha', return_value=None):
            
            result = self.git_utils.check_repository_updates("main")
            
            assert result["update_available"] is False
            assert result["remote_sha"] is None
            assert "Could not determine remote commit SHA" in result["error"]
    
    def test_check_repository_updates_ancestry_check_fails(self):
        """Test repository update check when ancestry check fails but timestamps work."""
        with patch.object(self.git_utils, 'get_local_commit_sha', return_value="abc123"), \
             patch.object(self.git_utils, 'get_remote_commit_sha', return_value="def456"), \
             patch.object(self.git_utils, 'is_commit_ancestor', return_value=None), \
             patch.object(self.git_utils, 'get_commit_timestamp') as mock_timestamp:
            
            from datetime import datetime, timezone
            # Remote is newer
            mock_timestamp.side_effect = [
                datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),  # local
                datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)   # remote
            ]
            
            result = self.git_utils.check_repository_updates("main")
            
            assert result["update_available"] is True
            assert "newer" in result["reason"]
            assert result["chronology_uncertain"] is False
    
    def test_check_repository_updates_all_checks_fail(self):
        """Test repository update check when all chronology checks fail."""
        with patch.object(self.git_utils, 'get_local_commit_sha', return_value="abc123"), \
             patch.object(self.git_utils, 'get_remote_commit_sha', return_value="def456"), \
             patch.object(self.git_utils, 'is_commit_ancestor', return_value=None), \
             patch.object(self.git_utils, 'get_commit_timestamp', return_value=None):
            
            result = self.git_utils.check_repository_updates("main")
            
            assert result["chronology_uncertain"] is True
            assert "Cannot determine if local" in result["reason"]
            assert "Both git ancestry and timestamp checks failed" in result["error"]
    
    def test_check_repository_updates_diverged_branches(self):
        """Test repository update check when branches have diverged."""
        with patch.object(self.git_utils, 'get_local_commit_sha', return_value="abc123"), \
             patch.object(self.git_utils, 'get_remote_commit_sha', return_value="def456"), \
             patch.object(self.git_utils, 'is_commit_ancestor') as mock_ancestor:
            
            # Neither is ancestor of the other (diverged branches)
            mock_ancestor.return_value = False
            
            result = self.git_utils.check_repository_updates("main")
            
            assert result["update_available"] is False
            assert "diverged" in result["reason"]
            assert "manual review needed" in result["reason"]
    
    def test_check_repository_updates_local_newer(self):
        """Test repository update check when local is newer than remote."""
        with patch.object(self.git_utils, 'get_local_commit_sha', return_value="abc123"), \
             patch.object(self.git_utils, 'get_remote_commit_sha', return_value="def456"), \
             patch.object(self.git_utils, 'is_commit_ancestor') as mock_ancestor:
            
            # First call: local is NOT ancestor of remote
            # Second call: remote IS ancestor of local (local is newer)
            mock_ancestor.side_effect = [False, True]
            
            result = self.git_utils.check_repository_updates("main")
            
            assert result["update_available"] is False
            assert "Local commit abc123... is newer than remote def456..." in result["reason"]
    
    def test_check_repository_updates_no_branch_fallback(self):
        """Test repository update check with branch detection failure."""
        with patch.object(self.git_utils, 'get_current_branch', return_value=None), \
             patch.object(self.git_utils, 'get_local_commit_sha', return_value="abc123"), \
             patch.object(self.git_utils, 'get_remote_commit_sha', return_value="abc123"):
            
            result = self.git_utils.check_repository_updates()
            
            assert result["branch"] == "main"  # Should fallback to main
            assert result["update_available"] is False
            assert "Local and remote SHAs match" in result["reason"]
    
    @patch('git_utils.debug_logger', None)
    def test_error_handling_without_debug_logger(self):
        """Test that error handling works when debug logger is not available."""
        git_utils = GitUtils()
        
        # These should not raise exceptions even without debug logger
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = git_utils.get_local_commit_sha()
            assert result is None
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("test")):
            result = git_utils.get_remote_commit_sha()
            assert result is None
    
    def test_convenience_functions_error_handling(self):
        """Test that convenience functions handle errors properly."""
        from git_utils import get_local_commit_sha, get_remote_commit_sha, get_current_branch, check_repository_updates
        
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            assert get_local_commit_sha() is None
            assert get_current_branch() is None
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("test")):
            assert get_remote_commit_sha() is None
        
        # check_repository_updates should return a valid dict even with errors
        with patch('git_utils.GitUtils.get_local_commit_sha', return_value=None):
            result = check_repository_updates()
            assert isinstance(result, dict)
            assert "error" in result or "reason" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])