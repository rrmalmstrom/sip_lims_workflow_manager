import pytest
import subprocess
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import shutil

from src.script_update_manager import ScriptUpdateManager


class TestScriptUpdateManager:
    """Test cases for ScriptUpdateManager core functionality."""
    
    @pytest.fixture
    def temp_scripts_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_git_repo(self, temp_scripts_dir):
        """Create a mock Git repository structure."""
        # Create .git directory to simulate Git repo
        git_dir = temp_scripts_dir / ".git"
        git_dir.mkdir()
        return temp_scripts_dir
    
    def test_script_update_manager_initialization(self, temp_scripts_dir):
        """Test ScriptUpdateManager can be initialized with scripts directory."""
        manager = ScriptUpdateManager(temp_scripts_dir)
        assert manager.scripts_dir == temp_scripts_dir
        assert manager.cache_ttl == 1800  # 30 minutes default
    
    def test_script_update_manager_initialization_with_custom_ttl(self, temp_scripts_dir):
        """Test ScriptUpdateManager initialization with custom cache TTL."""
        manager = ScriptUpdateManager(temp_scripts_dir, cache_ttl=3600)
        assert manager.cache_ttl == 3600
    
    @patch('subprocess.run')
    def test_check_for_script_updates_when_behind(self, mock_run, mock_git_repo):
        """Test detection when local scripts are behind remote."""
        # Mock git fetch success
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git fetch
            Mock(returncode=0, stdout="Your branch is behind 'origin/main' by 3 commits", stderr="")  # git status
        ]
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.check_for_updates()
        
        assert result['update_available'] is True
        assert result['error'] is None
        assert 'behind' in result['status_message']
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_check_for_script_updates_when_up_to_date(self, mock_run, mock_git_repo):
        """Test detection when local scripts are current."""
        # Mock git commands success with up-to-date status
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git fetch
            Mock(returncode=0, stdout="Your branch is up to date with 'origin/main'", stderr="")  # git status
        ]
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.check_for_updates()
        
        assert result['update_available'] is False
        assert result['error'] is None
        assert 'up to date' in result['status_message']
    
    def test_check_for_script_updates_with_no_git_repo(self, temp_scripts_dir):
        """Test graceful handling when scripts directory has no Git repo."""
        manager = ScriptUpdateManager(temp_scripts_dir)
        result = manager.check_for_updates()
        
        assert result['update_available'] is False
        assert result['error'] is not None
        assert 'not a git repository' in result['error'].lower()
    
    @patch('subprocess.run')
    def test_check_for_script_updates_with_network_error(self, mock_run, mock_git_repo):
        """Test handling of network failures during git fetch."""
        # Mock git fetch failure
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="fatal: unable to access 'https://github.com/': Could not resolve host")
        ]
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.check_for_updates()
        
        assert result['update_available'] is False
        assert result['error'] is not None
        assert 'network' in result['error'].lower() or 'fetch failed' in result['error'].lower()
    
    @patch('subprocess.run')
    def test_check_for_script_updates_with_timeout(self, mock_run, mock_git_repo):
        """Test handling of command timeouts."""
        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired('git', 10)
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.check_for_updates(timeout=1)
        
        assert result['update_available'] is False
        assert result['error'] is not None
        assert 'timeout' in result['error'].lower()
    
    @patch('subprocess.run')
    def test_update_scripts_success(self, mock_run, mock_git_repo):
        """Test successful script update via git pull."""
        # Mock successful git pull
        mock_run.return_value = Mock(
            returncode=0, 
            stdout="Updating abc123..def456\nFast-forward\n script1.py | 2 +-\n 1 file changed, 1 insertion(+), 1 deletion(-)",
            stderr=""
        )
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.update_scripts()
        
        assert result['success'] is True
        assert result['error'] is None
        assert 'updated successfully' in result['message'].lower()
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_update_scripts_failure(self, mock_run, mock_git_repo):
        """Test handling of failed script updates."""
        # Mock failed git pull
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="error: Your local changes to the following files would be overwritten by merge"
        )
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.update_scripts()
        
        assert result['success'] is False
        assert result['error'] is not None
        assert 'overwritten' in result['error']
    
    @patch('subprocess.run')
    def test_get_update_details(self, mock_run, mock_git_repo):
        """Test retrieval of update details (commits behind, etc.)."""
        # Mock git commands for getting details
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git fetch
            Mock(returncode=0, stdout="Your branch is behind 'origin/main' by 3 commits", stderr=""),  # git status
            Mock(returncode=0, stdout="abc123 Fix critical bug\ndef456 Add new feature\nghi789 Update documentation", stderr="")  # git log
        ]
        
        manager = ScriptUpdateManager(mock_git_repo)
        result = manager.get_update_details()
        
        assert result['commits_behind'] == 3
        assert len(result['commit_messages']) == 3
        assert 'Fix critical bug' in result['commit_messages'][0]
    
    def test_cache_behavior(self, mock_git_repo):
        """Test that results are properly cached for performance."""
        manager = ScriptUpdateManager(mock_git_repo, cache_ttl=3600)
        
        # First call should execute and cache
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=0, stdout="Your branch is up to date", stderr="")
            ]
            
            result1 = manager.check_for_updates()
            result2 = manager.check_for_updates()  # Should use cache
            
            # Should only call subprocess once due to caching
            assert mock_run.call_count == 2  # Only first call
            assert result1 == result2
    
    def test_cache_expiration(self, mock_git_repo):
        """Test that cache expires after TTL."""
        manager = ScriptUpdateManager(mock_git_repo, cache_ttl=0.1)  # Very short TTL
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=0, stdout="Your branch is up to date", stderr=""),
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=0, stdout="Your branch is behind", stderr="")
            ]
            
            result1 = manager.check_for_updates()
            
            # Wait for cache to expire
            import time
            time.sleep(0.2)
            
            result2 = manager.check_for_updates()
            
            # Should call subprocess twice due to cache expiration
            assert mock_run.call_count == 4
    
    def test_cache_invalidation(self, mock_git_repo):
        """Test that cache can be manually cleared."""
        manager = ScriptUpdateManager(mock_git_repo)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=0, stdout="Your branch is up to date", stderr=""),
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=0, stdout="Your branch is behind", stderr="")
            ]
            
            result1 = manager.check_for_updates()
            manager.clear_cache()
            result2 = manager.check_for_updates()
            
            # Should call subprocess twice due to manual cache clear
            assert mock_run.call_count == 4
    
    def test_get_last_check_time(self, mock_git_repo):
        """Test retrieval of last check timestamp."""
        manager = ScriptUpdateManager(mock_git_repo)
        
        # Initially should be None
        assert manager.get_last_check_time() is None
        
        # After check, should have timestamp
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=0, stdout="Your branch is up to date", stderr="")
            ]
            
            before_check = datetime.now()
            manager.check_for_updates()
            after_check = datetime.now()
            
            last_check = manager.get_last_check_time()
            assert last_check is not None
            assert before_check <= last_check <= after_check