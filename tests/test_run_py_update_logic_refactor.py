#!/usr/bin/env python3
"""
Test suite for run.py update logic refactor.

Tests the new behavior where production mode skips core updates by default
but always performs scripts updates, with --updates flag to enable all updates.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import argparse
from pathlib import Path

# Import the classes we need to test
from run import UpdateManager, DockerLauncher, create_argument_parser


class TestUpdateLogicRefactor:
    """Test suite for update logic refactor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.branch_info = {
            'branch': 'main', 
            'tag': 'latest',
            'local_image': 'local/test:latest',
            'remote_image': 'remote/test:latest'
        }
    
    @patch('run.click')
    def test_production_mode_default_behavior(self, mock_click):
        """Test production mode skips core updates by default."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"app_env": "production", "scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.check_fatal_sync_errors = Mock()
        update_manager.check_repository_updates = Mock()
        update_manager.check_docker_updates = Mock()
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute with default behavior (perform_all_updates=False)
        update_manager.perform_updates("sip", mode_config, perform_all_updates=False)
        
        # Verify only scripts updates called
        update_manager.check_fatal_sync_errors.assert_not_called()
        update_manager.check_repository_updates.assert_not_called()
        update_manager.check_docker_updates.assert_not_called()
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
        update_manager.display_skipped_updates_message.assert_called_once()
        
        # Verify correct message displayed
        mock_click.secho.assert_called_with("🏭 Production mode - performing scripts updates only...", fg='blue', bold=True)
    
    @patch('run.click')
    def test_production_mode_with_updates_flag(self, mock_click):
        """Test production mode performs all updates with --updates flag."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"app_env": "production", "scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.check_fatal_sync_errors = Mock()
        update_manager.check_repository_updates = Mock()
        update_manager.check_docker_updates = Mock()
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute with --updates flag (perform_all_updates=True)
        update_manager.perform_updates("sip", mode_config, perform_all_updates=True)
        
        # Verify all updates called
        update_manager.check_fatal_sync_errors.assert_called_once()
        update_manager.check_repository_updates.assert_called_once()
        update_manager.check_docker_updates.assert_called_once()
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
        update_manager.display_skipped_updates_message.assert_not_called()
        
        # Verify correct message displayed
        mock_click.secho.assert_called_with("🏭 Production mode - performing all updates...", fg='blue', bold=True)
    
    @patch('run.click')
    def test_developer_mode_unchanged(self, mock_click):
        """Test developer mode behavior remains unchanged."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"app_env": "development", "scripts_path": "/test/scripts"}
        
        # Mock the production_auto_update method
        update_manager.production_auto_update = Mock()
        
        # Execute with both flag values - should behave identically
        update_manager.perform_updates("sip", mode_config, perform_all_updates=False)
        update_manager.perform_updates("sip", mode_config, perform_all_updates=True)
        
        # Verify production_auto_update never called
        update_manager.production_auto_update.assert_not_called()
        
        # Verify development message displayed both times
        expected_calls = [
            (("🔧 Development mode - skipping auto-updates",), {'fg': 'blue'}),
            (("🔧 Development mode - skipping auto-updates",), {'fg': 'blue'})
        ]
        assert mock_click.secho.call_args_list == expected_calls
    
    def test_cli_argument_parsing_updates_flag(self):
        """Test CLI argument parsing for new --updates flag."""
        parser = create_argument_parser()
        
        # Test with --updates flag
        args = parser.parse_args(['--updates'])
        assert args.updates is True
        
        # Test without --updates flag
        args = parser.parse_args([])
        assert args.updates is False
        
        # Test that --no-updates is no longer recognized
        with pytest.raises(SystemExit):
            parser.parse_args(['--no-updates'])
    
    def test_cli_argument_parsing_with_other_flags(self):
        """Test CLI argument parsing with --updates combined with other flags."""
        parser = create_argument_parser()
        
        # Test --updates with workflow type
        args = parser.parse_args(['--updates', '--workflow-type', 'sip'])
        assert args.updates is True
        assert args.workflow_type == 'sip'
        
        # Test --updates with mode
        args = parser.parse_args(['--updates', '--mode', 'production'])
        assert args.updates is True
        assert args.mode == 'production'
    
    @patch('run.click')
    def test_informational_messaging(self, mock_click):
        """Test informational message display."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        
        # Execute
        update_manager.display_skipped_updates_message()
        
        # Verify message components displayed
        calls = mock_click.echo.call_args_list + mock_click.secho.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Check for key message components
        assert any("Update Information" in text for text in call_texts)
        assert any("Core system updates are skipped" in text for text in call_texts)
        assert any("--updates flag" in text for text in call_texts)
        assert any("Scripts updates (always enabled)" in text for text in call_texts)
        
        # Verify specific calls
        mock_click.secho.assert_called_with("ℹ️  Update Information:", fg='blue', bold=True)
        
        expected_echo_calls = [
            ((),),  # Empty line
            (("   • Core system updates are skipped by default in production mode",),),
            (("   • Skipping: Fatal sync check, repository updates, Docker image updates",),),
            (("   • Performing: Scripts updates (always enabled)",),),
            (("   • To enable all updates, use the --updates flag",),),
            ((),)   # Empty line
        ]
        assert mock_click.echo.call_args_list == expected_echo_calls
    
    @patch('run.click')
    def test_production_auto_update_direct_call_default(self, mock_click):
        """Test production_auto_update method directly with default behavior."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.check_fatal_sync_errors = Mock()
        update_manager.check_repository_updates = Mock()
        update_manager.check_docker_updates = Mock()
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute with default behavior
        update_manager.production_auto_update("sip", mode_config, perform_all_updates=False)
        
        # Verify behavior
        update_manager.check_fatal_sync_errors.assert_not_called()
        update_manager.check_repository_updates.assert_not_called()
        update_manager.check_docker_updates.assert_not_called()
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
        update_manager.display_skipped_updates_message.assert_called_once()
    
    @patch('run.click')
    def test_production_auto_update_direct_call_all_updates(self, mock_click):
        """Test production_auto_update method directly with all updates enabled."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.check_fatal_sync_errors = Mock()
        update_manager.check_repository_updates = Mock()
        update_manager.check_docker_updates = Mock()
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute with all updates enabled
        update_manager.production_auto_update("sip", mode_config, perform_all_updates=True)
        
        # Verify behavior
        update_manager.check_fatal_sync_errors.assert_called_once()
        update_manager.check_repository_updates.assert_called_once()
        update_manager.check_docker_updates.assert_called_once()
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
        update_manager.display_skipped_updates_message.assert_not_called()
    
    @patch('run.get_branch_info')
    @patch('run.PlatformAdapter.validate_docker')
    def test_docker_launcher_integration(self, mock_validate_docker, mock_get_branch_info):
        """Test DockerLauncher integration with new update logic."""
        # Setup
        mock_validate_docker.return_value = True
        mock_get_branch_info.return_value = self.branch_info
        
        launcher = DockerLauncher()
        
        # Verify the launch method signature accepts perform_all_updates
        import inspect
        sig = inspect.signature(launcher.launch)
        assert 'perform_all_updates' in sig.parameters
        assert sig.parameters['perform_all_updates'].default is False
    
    def test_backward_compatibility_error_handling(self):
        """Test that removed --no-updates flag produces clear error."""
        parser = create_argument_parser()
        
        # Test that --no-updates raises SystemExit (argparse error)
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--no-updates'])
        
        # SystemExit should be raised due to unrecognized argument
        assert exc_info.value.code != 0
    
    @patch('run.click')
    def test_scripts_always_run_in_production_default(self, mock_click):
        """Test that scripts updates always run in production mode, even by default."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"app_env": "production", "scripts_path": "/test/scripts"}
        
        # Mock only the scripts update method
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute default behavior
        update_manager.perform_updates("sip", mode_config, perform_all_updates=False)
        
        # Verify scripts updates always called
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
    
    @patch('run.click')
    def test_different_workflow_types(self, mock_click):
        """Test that the refactor works with different workflow types."""
        # Setup
        update_manager = UpdateManager(self.branch_info)
        mode_config = {"app_env": "production", "scripts_path": "/test/scripts"}
        
        # Mock the scripts update method
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Test with different workflow types
        for workflow_type in ["sip", "sps-ce"]:
            update_manager.check_scripts_updates.reset_mock()
            update_manager.display_skipped_updates_message.reset_mock()
            
            update_manager.perform_updates(workflow_type, mode_config, perform_all_updates=False)
            
            update_manager.check_scripts_updates.assert_called_once_with(workflow_type, "/test/scripts")
            update_manager.display_skipped_updates_message.assert_called_once()


class TestUpdateLogicIntegration:
    """Integration tests for the complete update logic flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.branch_info = {
            'branch': 'main', 
            'tag': 'latest',
            'local_image': 'local/test:latest',
            'remote_image': 'remote/test:latest'
        }
    
    @patch('run.get_branch_info')
    @patch('run.PlatformAdapter.validate_docker')
    @patch('run.UserInterface.select_workflow_type')
    @patch('run.UserInterface.select_project_path')
    @patch('run.ContainerManager.cleanup_existing_containers')
    @patch('run.ContainerManager.launch_container')
    def test_end_to_end_default_behavior(self, mock_launch, mock_cleanup, mock_select_project, 
                                       mock_select_workflow, mock_validate_docker, mock_get_branch_info):
        """Test end-to-end flow with default behavior (scripts only)."""
        # Setup mocks
        mock_validate_docker.return_value = True
        mock_get_branch_info.return_value = self.branch_info
        mock_select_workflow.return_value = "sip"
        mock_select_project.return_value = Path("/test/project")
        
        launcher = DockerLauncher()
        
        # Mock the update manager methods
        launcher.update_manager.check_scripts_updates = Mock()
        launcher.update_manager.display_skipped_updates_message = Mock()
        launcher.update_manager.check_fatal_sync_errors = Mock()
        launcher.update_manager.check_repository_updates = Mock()
        launcher.update_manager.check_docker_updates = Mock()
        
        # Mock mode detection to return production
        launcher.detect_mode = Mock(return_value="production")
        
        # Execute with default behavior
        launcher.launch(perform_all_updates=False)
        
        # Verify only scripts updates called
        launcher.update_manager.check_scripts_updates.assert_called_once()
        launcher.update_manager.display_skipped_updates_message.assert_called_once()
        launcher.update_manager.check_fatal_sync_errors.assert_not_called()
        launcher.update_manager.check_repository_updates.assert_not_called()
        launcher.update_manager.check_docker_updates.assert_not_called()
    
    @patch('run.get_branch_info')
    @patch('run.PlatformAdapter.validate_docker')
    @patch('run.UserInterface.select_workflow_type')
    @patch('run.UserInterface.select_project_path')
    @patch('run.ContainerManager.cleanup_existing_containers')
    @patch('run.ContainerManager.launch_container')
    def test_end_to_end_with_updates_flag(self, mock_launch, mock_cleanup, mock_select_project, 
                                        mock_select_workflow, mock_validate_docker, mock_get_branch_info):
        """Test end-to-end flow with --updates flag (all updates)."""
        # Setup mocks
        mock_validate_docker.return_value = True
        mock_get_branch_info.return_value = self.branch_info
        mock_select_workflow.return_value = "sip"
        mock_select_project.return_value = Path("/test/project")
        
        launcher = DockerLauncher()
        
        # Mock the update manager methods
        launcher.update_manager.check_scripts_updates = Mock()
        launcher.update_manager.display_skipped_updates_message = Mock()
        launcher.update_manager.check_fatal_sync_errors = Mock()
        launcher.update_manager.check_repository_updates = Mock()
        launcher.update_manager.check_docker_updates = Mock()
        
        # Mock mode detection to return production
        launcher.detect_mode = Mock(return_value="production")
        
        # Execute with --updates flag
        launcher.launch(perform_all_updates=True)
        
        # Verify all updates called
        launcher.update_manager.check_scripts_updates.assert_called_once()
        launcher.update_manager.display_skipped_updates_message.assert_not_called()
        launcher.update_manager.check_fatal_sync_errors.assert_called_once()
        launcher.update_manager.check_repository_updates.assert_called_once()
        launcher.update_manager.check_docker_updates.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])