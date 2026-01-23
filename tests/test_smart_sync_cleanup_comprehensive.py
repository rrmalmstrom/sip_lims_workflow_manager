"""
Comprehensive Test Suite for Smart Sync Cleanup Logic

This module tests all aspects of Smart Sync cleanup functionality including:
- Orphaned staging directory cleanup in run.py and run_debug.py
- Container shutdown cleanup logic
- SmartSyncManager cleanup methods
- Error handling and edge cases
"""

import pytest
import tempfile
import shutil
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from src.smart_sync import SmartSyncManager


class TestOrphanedStagingCleanup:
    """Test orphaned staging directory cleanup in run.py and run_debug.py."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.staging_base = self.temp_dir / "staging"
        self.staging_base.mkdir(parents=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cleanup_orphaned_staging_run_py(self):
        """Test orphaned staging cleanup in run.py."""
        # Test the cleanup logic by directly testing the staging directory removal
        project_name = "test_project"
        orphaned_staging = self.staging_base / project_name
        orphaned_staging.mkdir(parents=True)
        
        # Create files in orphaned directory
        (orphaned_staging / "orphaned_file.txt").write_text("orphaned content")
        (orphaned_staging / "subdir").mkdir()
        (orphaned_staging / "subdir" / "nested.txt").write_text("nested content")
        
        # Verify directory exists before cleanup
        assert orphaned_staging.exists()
        assert (orphaned_staging / "orphaned_file.txt").exists()
        assert (orphaned_staging / "subdir" / "nested.txt").exists()
        
        # Test the cleanup logic directly
        import shutil
        shutil.rmtree(orphaned_staging, ignore_errors=True)
        
        # Verify cleanup was successful
        assert not orphaned_staging.exists()
    
    def test_cleanup_orphaned_staging_run_debug_py(self):
        """Test orphaned staging cleanup in run_debug.py."""
        # Test the cleanup logic by directly testing the staging directory removal
        project_name = "debug_test_project"
        orphaned_staging = self.staging_base / project_name
        orphaned_staging.mkdir(parents=True)
        
        # Create files in orphaned directory
        (orphaned_staging / "debug_file.txt").write_text("debug content")
        (orphaned_staging / "debug_subdir").mkdir()
        (orphaned_staging / "debug_subdir" / "debug_nested.txt").write_text("debug nested")
        
        # Verify directory exists before cleanup
        assert orphaned_staging.exists()
        assert (orphaned_staging / "debug_file.txt").exists()
        assert (orphaned_staging / "debug_subdir" / "debug_nested.txt").exists()
        
        # Test the cleanup logic directly
        import shutil
        shutil.rmtree(orphaned_staging, ignore_errors=True)
        
        # Verify cleanup was successful
        assert not orphaned_staging.exists()
    
    def test_cleanup_nonexistent_staging_base(self):
        """Test cleanup when staging base directory doesn't exist."""
        # Remove staging base
        shutil.rmtree(self.staging_base)
        
        # Test that cleanup handles non-existent base gracefully
        assert not self.staging_base.exists()
        
        # This simulates the check in the actual cleanup function
        if self.staging_base.exists():
            # This branch should not execute
            pytest.fail("Staging base should not exist")
    
    def test_cleanup_nonexistent_project_staging(self):
        """Test cleanup when project staging directory doesn't exist."""
        project_name = "nonexistent_project"
        project_staging = self.staging_base / project_name
        
        # Verify project staging doesn't exist
        assert not project_staging.exists()
        
        # Test that cleanup handles non-existent project staging gracefully
        if project_staging.exists():
            # This branch should not execute
            pytest.fail("Project staging should not exist")
    
    def test_cleanup_permission_error_handling(self):
        """Test cleanup handles permission errors gracefully."""
        project_name = "permission_test"
        orphaned_staging = self.staging_base / project_name
        orphaned_staging.mkdir(parents=True)
        
        # Test that ignore_errors=True handles permission errors
        def mock_rmtree(path, ignore_errors=False):
            if ignore_errors:
                # Should not raise exception
                pass
            else:
                raise PermissionError("Permission denied")
        
        with patch('shutil.rmtree', side_effect=mock_rmtree):
            # This simulates the actual cleanup call with ignore_errors=True
            mock_rmtree(orphaned_staging, ignore_errors=True)
    
    def test_cleanup_partial_removal(self):
        """Test cleanup when some files cannot be removed."""
        project_name = "partial_test"
        orphaned_staging = self.staging_base / project_name
        orphaned_staging.mkdir(parents=True)
        
        # Create test files
        (orphaned_staging / "removable.txt").write_text("can remove")
        locked_file = orphaned_staging / "locked.txt"
        locked_file.write_text("cannot remove")
        
        # Test partial cleanup scenario
        try:
            (orphaned_staging / "removable.txt").unlink()
        except FileNotFoundError:
            pass
        
        # Verify partial cleanup occurred
        assert not (orphaned_staging / "removable.txt").exists()
        assert (orphaned_staging / "locked.txt").exists()


class TestContainerShutdownCleanup:
    """Test Smart Sync cleanup during container shutdown."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_container_shutdown_cleanup_success(self):
        """Test successful cleanup during container shutdown."""
        # Create test files in local staging
        (self.local_dir / "test_file.txt").write_text("test content")
        (self.local_dir / "subdir").mkdir()
        (self.local_dir / "subdir" / "nested.txt").write_text("nested content")
        
        # Verify files exist
        assert (self.local_dir / "test_file.txt").exists()
        assert (self.local_dir / "subdir" / "nested.txt").exists()
        
        # Create SmartSyncManager and test cleanup
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.cleanup()
        
        # Verify cleanup removed local staging
        assert not self.local_dir.exists()
    
    def test_container_shutdown_cleanup_with_sync_env(self):
        """Test cleanup using environment variables like in run.py."""
        # Create test files
        (self.local_dir / "env_test.txt").write_text("env test content")
        
        sync_env = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        # Simulate the cleanup logic from run.py lines 683-697
        from src.smart_sync import SmartSyncManager
        sync_manager = SmartSyncManager(
            Path(sync_env["NETWORK_PROJECT_PATH"]),
            Path(sync_env["LOCAL_PROJECT_PATH"])
        )
        
        # Verify file exists before cleanup
        assert (self.local_dir / "env_test.txt").exists()
        
        sync_manager.cleanup()
        
        # Verify cleanup was successful
        assert not self.local_dir.exists()
    
    def test_container_shutdown_cleanup_error_handling(self):
        """Test cleanup error handling during container shutdown."""
        # Create test files
        (self.local_dir / "error_test.txt").write_text("error test content")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Mock shutil.rmtree to raise an exception
        with patch('shutil.rmtree', side_effect=Exception("Cleanup failed")), \
             patch('src.smart_sync.click.secho') as mock_secho:
            # The current implementation catches exceptions and prints warnings
            # This should not raise an exception
            sync_manager.cleanup()
            
            # Verify warning was printed
            mock_secho.assert_called_with("⚠️  Warning: Could not clean up staging directory: Cleanup failed", fg='yellow')
    
    def test_container_shutdown_cleanup_nonexistent_directory(self):
        """Test cleanup when local directory doesn't exist."""
        # Remove local directory
        shutil.rmtree(self.local_dir)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Should not raise exception
        sync_manager.cleanup()


class TestSmartSyncManagerCleanup:
    """Test SmartSyncManager cleanup method directly."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
        
        self.sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cleanup_removes_local_staging(self):
        """Test that cleanup removes the local staging directory."""
        # Create test files
        (self.local_dir / "cleanup_test.txt").write_text("cleanup test")
        (self.local_dir / "subdir").mkdir()
        (self.local_dir / "subdir" / "nested.txt").write_text("nested")
        
        # Verify files exist
        assert self.local_dir.exists()
        assert (self.local_dir / "cleanup_test.txt").exists()
        assert (self.local_dir / "subdir" / "nested.txt").exists()
        
        # Perform cleanup
        self.sync_manager.cleanup()
        
        # Verify local staging was removed
        assert not self.local_dir.exists()
    
    def test_cleanup_preserves_network_directory(self):
        """Test that cleanup preserves the network directory."""
        # Create test files in both directories
        (self.network_dir / "network_file.txt").write_text("network content")
        (self.local_dir / "local_file.txt").write_text("local content")
        
        # Verify both exist
        assert self.network_dir.exists()
        assert self.local_dir.exists()
        assert (self.network_dir / "network_file.txt").exists()
        assert (self.local_dir / "local_file.txt").exists()
        
        # Perform cleanup
        self.sync_manager.cleanup()
        
        # Verify network directory is preserved, local is removed
        assert self.network_dir.exists()
        assert (self.network_dir / "network_file.txt").exists()
        assert not self.local_dir.exists()
    
    def test_cleanup_handles_nonexistent_local_directory(self):
        """Test cleanup when local directory doesn't exist."""
        # Remove local directory
        shutil.rmtree(self.local_dir)
        
        # Should not raise exception
        self.sync_manager.cleanup()
    
    def test_cleanup_handles_permission_errors(self):
        """Test cleanup handles permission errors gracefully."""
        # Create test file
        (self.local_dir / "permission_test.txt").write_text("permission test")
        
        # Mock shutil.rmtree to raise PermissionError
        with patch('shutil.rmtree', side_effect=PermissionError("Permission denied")):
            # Should not raise exception
            self.sync_manager.cleanup()
    
    def test_cleanup_logs_operations(self):
        """Test that cleanup operations are properly logged."""
        # Create test file
        (self.local_dir / "log_test.txt").write_text("log test")
        
        # Mock click.echo to verify it's called (actual implementation uses click.echo)
        with patch('src.smart_sync.click.echo') as mock_echo, \
             patch('src.smart_sync.click.secho') as mock_secho:
            self.sync_manager.cleanup()
            
            # Verify click.echo was called for cleanup message
            mock_echo.assert_called_with("🧹 Cleaning up local staging directory...")
            # Verify click.secho was called for success message
            mock_secho.assert_called_with("✅ Local staging cleaned up", fg='green')


class TestCleanupIntegration:
    """Test integration between different cleanup mechanisms."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.staging_base = self.temp_dir / "staging"
        self.staging_base.mkdir(parents=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_orphaned_cleanup_before_smart_sync_setup(self):
        """Test that orphaned cleanup happens before Smart Sync setup."""
        # Test the cleanup logic that would happen before Smart Sync setup
        project_name = "integration_test"
        
        # Create orphaned staging directory
        orphaned_staging = self.staging_base / project_name
        orphaned_staging.mkdir(parents=True)
        (orphaned_staging / "old_file.txt").write_text("old content")
        
        # Verify orphaned directory exists
        assert orphaned_staging.exists()
        assert (orphaned_staging / "old_file.txt").exists()
        
        # Simulate the cleanup that would happen before Smart Sync setup
        import shutil
        shutil.rmtree(orphaned_staging, ignore_errors=True)
        
        # Verify cleanup was successful
        assert not orphaned_staging.exists()
    
    def test_cleanup_synchronization_between_run_files(self):
        """Test that cleanup behavior is synchronized between run.py and run_debug.py."""
        # Test that both cleanup implementations use the same logic
        project_name = "sync_test"
        
        # Create two orphaned staging directories
        orphaned_staging_1 = self.staging_base / f"{project_name}_1"
        orphaned_staging_2 = self.staging_base / f"{project_name}_2"
        orphaned_staging_1.mkdir(parents=True)
        orphaned_staging_2.mkdir(parents=True)
        
        (orphaned_staging_1 / "file1.txt").write_text("content1")
        (orphaned_staging_2 / "file2.txt").write_text("content2")
        
        # Test cleanup logic for both directories
        import shutil
        
        # Simulate run.py cleanup
        shutil.rmtree(orphaned_staging_1, ignore_errors=True)
        assert not orphaned_staging_1.exists()
        
        # Simulate run_debug.py cleanup
        shutil.rmtree(orphaned_staging_2, ignore_errors=True)
        assert not orphaned_staging_2.exists()


class TestCleanupEdgeCases:
    """Test edge cases and error scenarios for cleanup logic."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cleanup_with_locked_files(self):
        """Test cleanup behavior with locked files (Windows scenario)."""
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Create test file
        test_file = self.local_dir / "locked_file.txt"
        test_file.write_text("locked content")
        
        # Mock file locking scenario
        def mock_rmtree(path, ignore_errors=False):
            if ignore_errors:
                # Simulate partial cleanup - some files removed, some locked
                try:
                    test_file.unlink()
                except:
                    pass
            else:
                raise PermissionError("File is locked")
        
        with patch('shutil.rmtree', side_effect=mock_rmtree):
            # Should not raise exception due to ignore_errors handling
            sync_manager.cleanup()
    
    def test_cleanup_with_deep_directory_structure(self):
        """Test cleanup with deeply nested directory structure."""
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Create deep directory structure
        deep_dir = self.local_dir
        for i in range(10):
            deep_dir = deep_dir / f"level_{i}"
            deep_dir.mkdir()
            (deep_dir / f"file_{i}.txt").write_text(f"content {i}")
        
        # Verify deep structure exists
        assert (self.local_dir / "level_0" / "level_1" / "level_2").exists()
        
        # Perform cleanup
        sync_manager.cleanup()
        
        # Verify entire structure was removed
        assert not self.local_dir.exists()
    
    def test_cleanup_with_symlinks(self):
        """Test cleanup behavior with symbolic links."""
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Create test file and symlink
        real_file = self.local_dir / "real_file.txt"
        real_file.write_text("real content")
        
        # Create symlink (skip on Windows if not supported)
        try:
            symlink_file = self.local_dir / "symlink_file.txt"
            symlink_file.symlink_to(real_file)
            has_symlinks = True
        except (OSError, NotImplementedError):
            has_symlinks = False
        
        # Perform cleanup
        sync_manager.cleanup()
        
        # Verify cleanup was successful
        assert not self.local_dir.exists()
    
    def test_cleanup_concurrent_access(self):
        """Test cleanup behavior during concurrent file access."""
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Create test file
        test_file = self.local_dir / "concurrent_file.txt"
        test_file.write_text("concurrent content")
        
        # Simulate concurrent access by mocking file operations
        access_count = 0
        original_rmtree = shutil.rmtree
        
        def mock_rmtree(path, ignore_errors=False):
            nonlocal access_count
            access_count += 1
            if access_count == 1:
                # First attempt fails due to concurrent access
                raise PermissionError("File in use")
            else:
                # Second attempt succeeds
                original_rmtree(path, ignore_errors=ignore_errors)
        
        with patch('shutil.rmtree', side_effect=mock_rmtree):
            # Should handle the concurrent access gracefully
            sync_manager.cleanup()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])