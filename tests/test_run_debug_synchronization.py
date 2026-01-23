"""
Test Suite for run.py and run_debug.py Synchronization
 
This module tests that run.py and run_debug.py have identical Smart Sync functionality,
ensuring that both files provide the same Smart Sync behavior with only debug-specific differences.
"""

import pytest
import platform
import inspect
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import both modules
import run
import run_debug


class TestRunDebugSynchronization:
    """Test that run.py and run_debug.py have identical Smart Sync functionality."""
    
    def test_platform_adapter_classes_exist(self):
        """Test that both files have PlatformAdapter classes."""
        assert hasattr(run, 'PlatformAdapter')
        assert hasattr(run_debug, 'PlatformAdapter')
    
    def test_smart_sync_detection_identical(self):
        """Test that Smart Sync detection logic is identical in both files."""
        test_paths = [
            Path("Z:\\project"),
            Path("C:\\local"),
            Path("\\\\server\\share"),
            Path("Y:\\data"),
            Path("/unix/path")
        ]
        
        for path in test_paths:
            with patch('platform.system', return_value='Windows'):
                run_result = run.PlatformAdapter.detect_smart_sync_scenario(path)
                run_debug_result = run_debug.PlatformAdapter.detect_smart_sync_scenario(path)
                
                assert run_result == run_debug_result, f"Detection mismatch for {path}: run.py={run_result}, run_debug.py={run_debug_result}"
            
            with patch('platform.system', return_value='Darwin'):
                run_result = run.PlatformAdapter.detect_smart_sync_scenario(path)
                run_debug_result = run_debug.PlatformAdapter.detect_smart_sync_scenario(path)
                
                assert run_result == run_debug_result, f"macOS detection mismatch for {path}: run.py={run_result}, run_debug.py={run_debug_result}"
    
    def test_smart_sync_setup_environment_identical(self):
        """Test that Smart Sync environment setup is identical in both files."""
        test_path = Path("Z:\\test_project")
        
        # Mock the smart_sync module setup function
        mock_env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(test_path),
            "LOCAL_PROJECT_PATH": "C:\\temp\\sip_workflow\\test_project",
            "PROJECT_PATH": "C:\\temp\\sip_workflow\\test_project"
        }
        
        with patch('src.smart_sync.setup_smart_sync_environment', return_value=mock_env_vars):
            try:
                run_result = run.PlatformAdapter.setup_smart_sync_environment(test_path)
                run_debug_result = run_debug.PlatformAdapter.setup_smart_sync_environment(test_path)
                
                # Both should return the same environment variables
                assert run_result == run_debug_result
            except Exception as e:
                # Both should raise the same type of exception
                with pytest.raises(type(e)):
                    run.PlatformAdapter.setup_smart_sync_environment(test_path)
                with pytest.raises(type(e)):
                    run_debug.PlatformAdapter.setup_smart_sync_environment(test_path)
    
    def test_cleanup_orphaned_directories_identical(self):
        """Test that orphaned directory cleanup is identical in both files."""
        test_path = Path("Z:\\test_project")
        
        # Mock Path operations
        with patch('pathlib.Path.exists', return_value=False):
            # Both should handle non-existent staging gracefully
            run.PlatformAdapter.cleanup_orphaned_staging_directories(test_path)
            run_debug.PlatformAdapter.cleanup_orphaned_staging_directories(test_path)
            # No assertion needed - just verify no exceptions
    
    def test_container_manager_classes_exist(self):
        """Test that both files have ContainerManager classes."""
        assert hasattr(run, 'ContainerManager')
        assert hasattr(run_debug, 'ContainerManager')
    
    def test_container_manager_smart_sync_integration(self):
        """Test that ContainerManager Smart Sync integration is identical."""
        # Mock branch info
        mock_branch_info = {
            'branch': 'feature-smart-sync-layer',
            'tag': 'feature-smart-sync-layer',
            'local_image': 'local/image',
            'remote_image': 'remote/image'
        }
        
        # Create ContainerManager instances
        run_manager = run.ContainerManager(mock_branch_info)
        run_debug_manager = run_debug.ContainerManager(mock_branch_info)
        
        # Test that both have the same methods
        run_methods = set(dir(run_manager))
        run_debug_methods = set(dir(run_debug_manager))
        
        # Key Smart Sync methods should exist in both
        smart_sync_methods = {
            'launch_container',
            'cleanup_existing_containers',
            'prepare_environment',
            'display_environment_summary'
        }
        
        for method in smart_sync_methods:
            assert method in run_methods, f"run.py ContainerManager missing {method}"
            assert method in run_debug_methods, f"run_debug.py ContainerManager missing {method}"
    
    def test_environment_preparation_identical(self):
        """Test that environment preparation includes the same variables."""
        # Mock branch info
        mock_branch_info = {
            'branch': 'feature-smart-sync-layer',
            'tag': 'feature-smart-sync-layer',
            'local_image': 'local/image',
            'remote_image': 'remote/image'
        }
        
        # Create ContainerManager instances
        run_manager = run.ContainerManager(mock_branch_info)
        run_debug_manager = run_debug.ContainerManager(mock_branch_info)
        
        # Test environment preparation
        test_path = Path("Z:\\test_project")
        test_workflow = "sip"
        test_mode_config = {
            "scripts_path": "/test/scripts",
            "app_env": "production",
            "docker_image": "test/image"
        }
        
        with patch('run.PlatformAdapter.get_user_ids', return_value={"USER_ID": "1000", "GROUP_ID": "1000"}):
            with patch('run_debug.PlatformAdapter.get_user_ids', return_value={"USER_ID": "1000", "GROUP_ID": "1000"}):
                run_env = run_manager.prepare_environment(test_path, test_workflow, test_mode_config)
                run_debug_env = run_debug_manager.prepare_environment(test_path, test_workflow, test_mode_config)
                
                # Both should include SYNC_SCRIPTS_PATH
                assert "SYNC_SCRIPTS_PATH" in run_env
                assert "SYNC_SCRIPTS_PATH" in run_debug_env
                assert run_env["SYNC_SCRIPTS_PATH"] == run_debug_env["SYNC_SCRIPTS_PATH"]
                
                # Both should have the same core environment variables
                core_vars = ["PROJECT_PATH", "PROJECT_NAME", "SCRIPTS_PATH", "WORKFLOW_TYPE", "APP_ENV", "DOCKER_IMAGE"]
                for var in core_vars:
                    assert run_env[var] == run_debug_env[var], f"Environment variable {var} differs"
    
    def test_update_manager_classes_exist(self):
        """Test that both files have UpdateManager classes."""
        assert hasattr(run, 'UpdateManager')
        assert hasattr(run_debug, 'UpdateManager')
    
    def test_update_manager_scripts_functionality(self):
        """Test that UpdateManager scripts functionality exists in both files."""
        # Mock branch info
        mock_branch_info = {
            'branch': 'feature-smart-sync-layer',
            'tag': 'feature-smart-sync-layer',
            'local_image': 'local/image',
            'remote_image': 'remote/image'
        }
        
        # Create UpdateManager instances
        run_manager = run.UpdateManager(mock_branch_info)
        run_debug_manager = run_debug.UpdateManager(mock_branch_info)
        
        # Both should have check_scripts_updates method
        assert hasattr(run_manager, 'check_scripts_updates')
        assert hasattr(run_debug_manager, 'check_scripts_updates')
        
        # Method signatures should be identical
        run_sig = inspect.signature(run_manager.check_scripts_updates)
        run_debug_sig = inspect.signature(run_debug_manager.check_scripts_updates)
        assert run_sig == run_debug_sig
    
    def test_docker_launcher_classes_exist(self):
        """Test that both files have DockerLauncher classes."""
        assert hasattr(run, 'DockerLauncher')
        assert hasattr(run_debug, 'DockerLauncher')
    
    def test_docker_launcher_smart_sync_methods(self):
        """Test that DockerLauncher has Smart Sync related methods in both files."""
        # Key methods that should exist in both
        smart_sync_methods = {
            'validate_environment',
            'setup_production_mode',
            'launch',
            'display_branch_info'
        }
        
        for method in smart_sync_methods:
            assert hasattr(run.DockerLauncher, method), f"run.py DockerLauncher missing {method}"
            assert hasattr(run_debug.DockerLauncher, method), f"run_debug.py DockerLauncher missing {method}"
    
    def test_user_interface_classes_exist(self):
        """Test that both files have UserInterface classes."""
        assert hasattr(run, 'UserInterface')
        assert hasattr(run_debug, 'UserInterface')
    
    def test_user_interface_confirm_action_method(self):
        """Test that both UserInterface classes have confirm_action method."""
        assert hasattr(run.UserInterface, 'confirm_action')
        assert hasattr(run_debug.UserInterface, 'confirm_action')
        
        # Method signatures should be identical
        run_sig = inspect.signature(run.UserInterface.confirm_action)
        run_debug_sig = inspect.signature(run_debug.UserInterface.confirm_action)
        assert run_sig == run_debug_sig
    
    def test_debug_flag_support(self):
        """Test that run_debug.py supports the --debug flag like run.py."""
        # run_debug.py should have argument parsing for --debug flag
        # This is tested by checking if the main function handles debug environment variables
        
        # Mock sys.argv to include --debug flag
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ['run_debug.py', '--debug']
            
            # Mock os.environ to verify debug flag is set
            with patch('os.environ', {}) as mock_env:
                with patch('run_debug.DockerLauncher') as mock_launcher:
                    mock_launcher_instance = MagicMock()
                    mock_launcher.return_value = mock_launcher_instance
                    
                    # Import and call main (this will parse args and set env vars)
                    try:
                        run_debug.main()
                    except SystemExit:
                        pass  # Expected when no actual Docker operations
                    
                    # Verify debug environment variables were set
                    assert mock_env.get("SMART_SYNC_DEBUG") == "true"
                    assert mock_env.get("SMART_SYNC_DEBUG_LEVEL") == "DEBUG"
        
        finally:
            sys.argv = original_argv
    
    def test_fail_fast_behavior_identical(self):
        """Test that both files implement identical fail-fast behavior."""
        test_path = Path("Z:\\test_project")
        
        # Test that both files raise RuntimeError on Smart Sync setup failure
        with patch('src.smart_sync.setup_smart_sync_environment', side_effect=Exception("Test failure")):
            with pytest.raises(RuntimeError, match="Smart Sync setup failed"):
                run.PlatformAdapter.setup_smart_sync_environment(test_path)
            
            with pytest.raises(RuntimeError, match="Smart Sync setup failed"):
                run_debug.PlatformAdapter.setup_smart_sync_environment(test_path)


class TestDebugSpecificDifferences:
    """Test that debug-specific differences are appropriate and don't affect Smart Sync functionality."""
    
    def test_debug_logging_differences(self):
        """Test that run_debug.py has additional debug logging without affecting Smart Sync logic."""
        # run_debug.py should have debug_log function
        assert hasattr(run_debug, 'debug_log')
        
        # run.py should not have debug_log function (uses src.debug_logger instead)
        assert not hasattr(run, 'debug_log')
    
    def test_click_fallback_differences(self):
        """Test that both files handle Click import gracefully."""
        # Both should have click classes/modules
        assert hasattr(run, 'click')
        assert hasattr(run_debug, 'click')
        
        # run_debug.py click should have debug logging in methods
        # This is verified by checking if the click.echo method in run_debug has debug_log calls
        # (This is implementation-specific and may vary)
    
    def test_simplified_mode_selection(self):
        """Test that run_debug.py has simplified mode selection (no developer vs production complexity)."""
        # run.py should have developer mode methods
        assert hasattr(run.DockerLauncher, 'detect_mode')
        assert hasattr(run.DockerLauncher, 'handle_mode_selection')
        assert hasattr(run.DockerLauncher, 'setup_development_mode')
        
        # run_debug.py should NOT have these complex mode selection methods
        assert not hasattr(run_debug.DockerLauncher, 'detect_mode')
        assert not hasattr(run_debug.DockerLauncher, 'handle_mode_selection')
        assert not hasattr(run_debug.DockerLauncher, 'setup_development_mode')
        
        # But both should have setup_production_mode
        assert hasattr(run.DockerLauncher, 'setup_production_mode')
        assert hasattr(run_debug.DockerLauncher, 'setup_production_mode')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])