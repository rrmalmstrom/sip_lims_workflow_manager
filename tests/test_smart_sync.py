"""
Test Suite for Smart Sync Manager

This module tests the Smart Sync functionality for Windows network drive support.
Tests cover detection logic, sync operations, error handling, and platform compatibility.
"""

import pytest
import tempfile
import shutil
import platform
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.smart_sync import (
    SmartSyncManager, 
    detect_smart_sync_scenario, 
    setup_smart_sync_environment,
    get_smart_sync_manager
)


class TestSmartSyncDetection:
    """Test Smart Sync detection logic."""
    
    def test_detect_smart_sync_non_windows(self):
        """Test that Smart Sync is disabled on non-Windows platforms."""
        with patch('platform.system', return_value='Darwin'):
            result = detect_smart_sync_scenario(Path("/some/path"))
            assert result is False
        
        with patch('platform.system', return_value='Linux'):
            result = detect_smart_sync_scenario(Path("/some/path"))
            assert result is False
    
    def test_detect_smart_sync_windows_network_drives(self):
        """Test detection of Windows network drives (D: through Z:)."""
        with patch('platform.system', return_value='Windows'):
            # Test network drives that should trigger Smart Sync
            network_drives = ['D:\\project', 'Z:\\data', 'Y:\\test', 'X:\\folder']
            for drive_path in network_drives:
                result = detect_smart_sync_scenario(Path(drive_path))
                assert result is True, f"Should detect {drive_path} as network drive"
    
    def test_detect_smart_sync_windows_local_drive(self):
        """Test that C: drive (local) does not trigger Smart Sync."""
        with patch('platform.system', return_value='Windows'):
            local_paths = ['C:\\Users\\test', 'C:\\Program Files', 'C:\\temp']
            for local_path in local_paths:
                result = detect_smart_sync_scenario(Path(local_path))
                assert result is False, f"Should NOT detect {local_path} as network drive"
    
    def test_detect_smart_sync_unc_paths(self):
        """Test detection of UNC paths."""
        with patch('platform.system', return_value='Windows'):
            unc_paths = ['\\\\server\\share\\folder', '//server/share/folder']
            for unc_path in unc_paths:
                result = detect_smart_sync_scenario(Path(unc_path))
                assert result is True, f"Should detect {unc_path} as UNC path"
    
    def test_detect_smart_sync_edge_cases(self):
        """Test edge cases and invalid paths."""
        with patch('platform.system', return_value='Windows'):
            edge_cases = ['', 'relative/path', '/unix/style/path']
            for edge_case in edge_cases:
                result = detect_smart_sync_scenario(Path(edge_case))
                assert result is False, f"Should NOT detect {edge_case} as network drive"
    
    def test_detect_smart_sync_exception_handling(self):
        """Test that exceptions in detection are handled gracefully."""
        with patch('platform.system', return_value='Windows'):
            # Test with None (should not crash)
            with patch('pathlib.Path.__str__', side_effect=Exception("Test error")):
                result = detect_smart_sync_scenario(Path("Z:\\test"))
                assert result is False  # Should return False on exception


class TestSmartSyncManager:
    """Test SmartSyncManager class functionality."""
    
    def setup_method(self):
        """Set up test directories for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        
        # Create test directories
        self.network_dir.mkdir(parents=True)
        self.local_dir.mkdir(parents=True)
        
        # Initialize SmartSyncManager
        self.sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
    
    def teardown_method(self):
        """Clean up test directories after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_smart_sync_manager_initialization(self):
        """Test SmartSyncManager initialization."""
        assert self.sync_manager.network_path == self.network_dir
        assert self.sync_manager.local_path == self.local_dir
        assert self.sync_manager.local_path.exists()
        assert isinstance(self.sync_manager.ignore_patterns, set)
        assert len(self.sync_manager.ignore_patterns) > 0
    
    def test_ignore_patterns(self):
        """Test file ignore patterns."""
        # Test files that should be ignored
        ignored_files = [
            Path("__pycache__"),
            Path(".DS_Store"),
            Path("Thumbs.db"),
            Path(".sync_log.json"),
            Path("test.tmp"),
            Path("file.temp")
        ]
        
        for file_path in ignored_files:
            assert self.sync_manager._should_ignore(file_path), f"Should ignore {file_path}"
        
        # Test files that should NOT be ignored
        normal_files = [
            Path("data.csv"),
            Path("workflow.yml"),
            Path(".snapshots"),
            Path(".workflow_status"),
            Path("script.py")
        ]
        
        for file_path in normal_files:
            assert not self.sync_manager._should_ignore(file_path), f"Should NOT ignore {file_path}"
    
    def test_initial_sync_empty_directories(self):
        """Test initial sync with empty directories."""
        result = self.sync_manager.initial_sync()
        assert result is True
        assert self.sync_manager.sync_stats["files_synced"] == 0
    
    def test_initial_sync_with_files(self):
        """Test initial sync with actual files."""
        # Create test files in network directory
        test_files = {
            "data.csv": "col1,col2\n1,2\n3,4",
            "workflow.yml": "name: test\nsteps: []",
            ".hidden_file": "hidden content"
        }
        
        for filename, content in test_files.items():
            (self.network_dir / filename).write_text(content)
        
        # Create subdirectory with file
        subdir = self.network_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")
        
        # Perform initial sync
        result = self.sync_manager.initial_sync()
        assert result is True
        
        # Verify all files were copied
        for filename in test_files.keys():
            local_file = self.local_dir / filename
            assert local_file.exists(), f"File {filename} should exist in local"
            assert local_file.read_text() == test_files[filename]
        
        # Verify subdirectory and nested file
        assert (self.local_dir / "subdir" / "nested.txt").exists()
        assert (self.local_dir / "subdir" / "nested.txt").read_text() == "nested content"
        
        # Check sync stats
        assert self.sync_manager.sync_stats["files_synced"] == 4  # 3 files + 1 nested
    
    def test_incremental_sync_down_no_changes(self):
        """Test incremental sync when no changes exist."""
        # Set up identical files
        test_file = "test.txt"
        content = "test content"
        
        (self.network_dir / test_file).write_text(content)
        (self.local_dir / test_file).write_text(content)
        
        result = self.sync_manager.incremental_sync_down()
        assert result is True
    
    def test_incremental_sync_down_with_changes(self):
        """Test incremental sync with new and modified files."""
        # Create initial files
        (self.network_dir / "existing.txt").write_text("original")
        (self.local_dir / "existing.txt").write_text("original")
        
        # Add new file to network
        (self.network_dir / "new.txt").write_text("new content")
        
        # Modify existing file on network (ensure different timestamp)
        time.sleep(0.1)
        (self.network_dir / "existing.txt").write_text("modified")
        
        result = self.sync_manager.incremental_sync_down()
        assert result is True
        
        # Verify new file was copied
        assert (self.local_dir / "new.txt").exists()
        assert (self.local_dir / "new.txt").read_text() == "new content"
        
        # Verify existing file was updated
        assert (self.local_dir / "existing.txt").read_text() == "modified"
    
    def test_incremental_sync_up_with_changes(self):
        """Test incremental sync from local to network."""
        # Create initial files
        (self.network_dir / "existing.txt").write_text("original")
        (self.local_dir / "existing.txt").write_text("original")
        
        # Add new file to local
        (self.local_dir / "local_new.txt").write_text("local content")
        
        # Modify existing file locally
        time.sleep(0.1)
        (self.local_dir / "existing.txt").write_text("local modified")
        
        result = self.sync_manager.incremental_sync_up()
        assert result is True
        
        # Verify new file was copied to network
        assert (self.network_dir / "local_new.txt").exists()
        assert (self.network_dir / "local_new.txt").read_text() == "local content"
        
        # Verify existing file was updated on network
        assert (self.network_dir / "existing.txt").read_text() == "local modified"
    
    def test_file_deletion_sync(self):
        """Test that deleted files are removed during sync."""
        # Set up initial files
        (self.network_dir / "to_delete.txt").write_text("delete me")
        (self.local_dir / "to_delete.txt").write_text("delete me")
        
        # Delete file from network
        (self.network_dir / "to_delete.txt").unlink()
        
        result = self.sync_manager.incremental_sync_down()
        assert result is True
        
        # Verify file was deleted from local
        assert not (self.local_dir / "to_delete.txt").exists()
    
    def test_hidden_files_sync(self):
        """Test that hidden files (.snapshots, .workflow_status) are synced."""
        # Create hidden directories and files
        hidden_items = [
            ".snapshots/step1/data.db",
            ".workflow_status/step1.success",
            ".workflow_logs/debug.log"
        ]
        
        for item in hidden_items:
            file_path = self.network_dir / item
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"content of {item}")
        
        result = self.sync_manager.initial_sync()
        assert result is True
        
        # Verify all hidden items were synced
        for item in hidden_items:
            local_file = self.local_dir / item
            assert local_file.exists(), f"Hidden file {item} should be synced"
            assert local_file.read_text() == f"content of {item}"
    
    def test_sync_logging(self):
        """Test that sync operations are logged."""
        # Create a test file and sync
        (self.network_dir / "test.txt").write_text("test")
        
        result = self.sync_manager.initial_sync()
        assert result is True
        
        # Check that log file was created
        log_file = self.local_dir / ".sync_log.json"
        assert log_file.exists()
        
        # Verify log content
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) > 0
        assert log_data[-1]["operation"] == "initial_sync"
        assert "timestamp" in log_data[-1]
        assert "details" in log_data[-1]
    
    def test_sync_stats_tracking(self):
        """Test that sync statistics are tracked correctly."""
        # Create test files
        for i in range(3):
            (self.network_dir / f"file{i}.txt").write_text(f"content {i}")
        
        result = self.sync_manager.initial_sync()
        assert result is True
        
        stats = self.sync_manager.get_sync_stats()
        assert stats["files_synced"] == 3
        assert stats["last_sync_duration"] > 0
        assert stats["network_path"] == str(self.network_dir)
        assert stats["local_path"] == str(self.local_dir)
    
    def test_final_sync(self):
        """Test final sync functionality."""
        # Create test file locally
        (self.local_dir / "final.txt").write_text("final content")
        
        result = self.sync_manager.final_sync()
        assert result is True
        
        # Verify file was synced to network
        assert (self.network_dir / "final.txt").exists()
        assert (self.network_dir / "final.txt").read_text() == "final content"
    
    def test_cleanup(self):
        """Test cleanup functionality."""
        # Create some files
        (self.local_dir / "cleanup_test.txt").write_text("test")
        assert self.local_dir.exists()
        
        self.sync_manager.cleanup()
        
        # Verify local directory was removed
        assert not self.local_dir.exists()


class TestSmartSyncEnvironmentSetup:
    """Test Smart Sync environment setup functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_project = self.temp_dir / "test_project"
        self.network_project.mkdir(parents=True)
        
        # Create some test files
        (self.network_project / "workflow.yml").write_text("test workflow")
        (self.network_project / "data.csv").write_text("test,data")
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('tempfile.gettempdir')
    def test_setup_smart_sync_environment(self, mock_tempdir):
        """Test Smart Sync environment setup."""
        mock_tempdir.return_value = str(self.temp_dir)
        
        result = setup_smart_sync_environment(self.network_project)
        
        # Verify environment variables
        assert result["SMART_SYNC_ENABLED"] == "true"
        assert result["NETWORK_PROJECT_PATH"] == str(self.network_project)
        assert "LOCAL_PROJECT_PATH" in result
        assert "PROJECT_PATH" in result
        
        # Verify local staging was created and files synced
        local_path = Path(result["LOCAL_PROJECT_PATH"])
        assert local_path.exists()
        assert (local_path / "workflow.yml").exists()
        assert (local_path / "data.csv").exists()
        
        # Clean up
        if local_path.exists():
            shutil.rmtree(local_path.parent)
    
    def test_get_smart_sync_manager(self):
        """Test SmartSyncManager factory function."""
        manager = get_smart_sync_manager(str(self.network_project), str(self.temp_dir / "local"))
        
        assert isinstance(manager, SmartSyncManager)
        assert manager.network_path == self.network_project
        assert manager.local_path == self.temp_dir / "local"


class TestSmartSyncErrorHandling:
    """Test error handling in Smart Sync operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir(parents=True)
        self.local_dir.mkdir(parents=True)
        
        self.sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_sync_with_nonexistent_network_path(self):
        """Test sync behavior when network path doesn't exist."""
        nonexistent_network = self.temp_dir / "nonexistent"
        sync_manager = SmartSyncManager(nonexistent_network, self.local_dir)
        
        # Should handle gracefully and return True (no files to sync)
        result = sync_manager.initial_sync()
        assert result is True
    
    def test_sync_with_permission_errors(self):
        """Test sync behavior with permission errors."""
        # Create a file and make it read-only to simulate permission error
        test_file = self.network_dir / "readonly.txt"
        test_file.write_text("readonly content")
        
        # Mock permission error during copy
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            result = self.sync_manager.initial_sync()
            # Should return True but log the error
            assert result is True
    
    def test_logging_with_json_error(self):
        """Test that JSON logging errors don't break sync operations."""
        # Create test file
        (self.network_dir / "test.txt").write_text("test")
        
        # Mock JSON dump to raise an error
        with patch('json.dump', side_effect=ValueError("Test JSON error")):
            result = self.sync_manager.initial_sync()
            # Should still succeed despite logging error
            assert result is True


class TestSmartSyncIntegration:
    """Integration tests for Smart Sync with run.py functionality."""
    
    def test_run_py_integration_detection(self):
        """Test integration with run.py detection logic."""
        with patch('platform.system', return_value='Windows'):
            from run import PlatformAdapter
            
            # Test that run.py detection matches smart_sync detection
            test_paths = [
                Path("Z:\\project"),
                Path("C:\\local"),
                Path("\\\\server\\share")
            ]
            
            for path in test_paths:
                run_py_result = PlatformAdapter.detect_smart_sync_scenario(path)
                smart_sync_result = detect_smart_sync_scenario(path)
                assert run_py_result == smart_sync_result, f"Detection mismatch for {path}"
    
    def test_macos_no_smart_sync(self):
        """Test that Smart Sync is completely disabled on macOS."""
        with patch('platform.system', return_value='Darwin'):
            from run import PlatformAdapter
            
            # Even network-like paths should not trigger Smart Sync on macOS
            macos_paths = [
                Path("/Volumes/NetworkDrive/project"),
                Path("/mnt/share/project"),
                Path("Z:\\project")  # Even Windows-style paths
            ]
            
            for path in macos_paths:
                assert PlatformAdapter.detect_smart_sync_scenario(path) is False
                assert detect_smart_sync_scenario(path) is False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])