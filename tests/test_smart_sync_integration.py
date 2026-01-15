"""
Test Suite for Smart Sync Integration with Core Workflow

This module tests the integration of Smart Sync functionality with the core workflow
execution system, including pre-step and post-step sync triggers.
"""

import pytest
import tempfile
import shutil
import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from src.core import Project, Workflow
from src.smart_sync import SmartSyncManager


class TestSmartSyncWorkflowIntegration:
    """Test Smart Sync integration with workflow execution."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        
        # Create directories
        self.project_dir.mkdir(parents=True)
        self.network_dir.mkdir(parents=True)
        self.local_dir.mkdir(parents=True)
        
        # Create a test workflow
        self.workflow_content = {
            "workflow_name": "Test Workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "Test Step 1",
                    "script": "test_script.py",
                    "snapshot_items": ["data.csv"]
                },
                {
                    "id": "step2", 
                    "name": "Test Step 2",
                    "script": "test_script2.py",
                    "allow_rerun": True
                }
            ]
        }
        
        workflow_file = self.project_dir / "workflow.yml"
        with open(workflow_file, 'w') as f:
            yaml.dump(self.workflow_content, f)
        
        # Create scripts directory
        scripts_dir = self.project_dir / "scripts"
        scripts_dir.mkdir()
        
        # Create test scripts
        (scripts_dir / "test_script.py").write_text("print('Test script 1')")
        (scripts_dir / "test_script2.py").write_text("print('Test script 2')")
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_project_initialization_without_smart_sync(self):
        """Test that Project initializes normally without Smart Sync environment."""
        project = Project(self.project_dir)
        
        assert project.smart_sync_manager is None
        assert project.path == self.project_dir
        assert project.workflow is not None
    
    def test_project_initialization_with_smart_sync(self):
        """Test that Project initializes Smart Sync when environment variables are set."""
        # Set Smart Sync environment variables
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Verify Smart Sync manager was created
                assert project.smart_sync_manager is not None
                mock_get_manager.assert_called_once_with(str(self.network_dir), str(self.local_dir))
    
    def test_run_step_with_smart_sync_pre_sync(self):
        """Test that run_step triggers pre-step sync when Smart Sync is enabled."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_manager.incremental_sync_down.return_value = True
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Mock the script runner to avoid actual execution
                with patch.object(project.script_runner, 'run'):
                    project.run_step("step1")
                
                # Verify pre-step sync was called
                mock_manager.incremental_sync_down.assert_called_once()
    
    def test_run_step_without_smart_sync_no_sync_calls(self):
        """Test that run_step doesn't call sync methods when Smart Sync is disabled."""
        project = Project(self.project_dir)
        
        # Mock the script runner to avoid actual execution
        with patch.object(project.script_runner, 'run'):
            project.run_step("step1")
        
        # No sync calls should be made since smart_sync_manager is None
        assert project.smart_sync_manager is None
    
    def test_handle_step_result_success_with_smart_sync_post_sync(self):
        """Test that successful step completion triggers post-step sync."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_manager.incremental_sync_up.return_value = True
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Create success marker for the script
                status_dir = self.project_dir / ".workflow_status"
                status_dir.mkdir(exist_ok=True)
                success_file = status_dir / "test_script.success"
                success_file.write_text("success")
                
                # Mock successful script result
                from src.logic import RunResult
                result = RunResult(success=True, stdout="Test output", stderr="", return_code=0)
                
                project.handle_step_result("step1", result)
                
                # Verify post-step sync was called
                mock_manager.incremental_sync_up.assert_called_once()
                
                # Verify step was marked as completed
                assert project.get_state("step1") == "completed"
    
    def test_handle_step_result_failure_no_post_sync(self):
        """Test that failed step completion doesn't trigger post-step sync."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Mock the snapshot manager to avoid FileNotFoundError during rollback
                with patch.object(project.snapshot_manager, 'restore') as mock_restore:
                    with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore_complete:
                        with patch.object(project.snapshot_manager, 'snapshot_exists', return_value=False):
                            with patch.object(project.snapshot_manager, 'get_current_run_number', return_value=0):
                                # Mock failed script result (no success marker)
                                from src.logic import RunResult
                                result = RunResult(success=False, stdout="Test output", stderr="Error occurred", return_code=1)
                                
                                project.handle_step_result("step1", result)
                                
                                # Verify post-step sync was NOT called
                                mock_manager.incremental_sync_up.assert_not_called()
                                
                                # Verify step remains pending
                                assert project.get_state("step1") == "pending"
    
    def test_sync_error_handling_pre_step(self):
        """Test that sync errors during pre-step don't break workflow execution."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_manager.incremental_sync_down.side_effect = Exception("Sync error")
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Mock the script runner to avoid actual execution
                with patch.object(project.script_runner, 'run') as mock_run:
                    # Should not raise exception despite sync error
                    project.run_step("step1")
                    
                    # Script should still be executed
                    mock_run.assert_called_once()
    
    def test_sync_error_handling_post_step(self):
        """Test that sync errors during post-step don't affect step completion status."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_manager.incremental_sync_up.side_effect = Exception("Sync error")
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Create success marker for the script
                status_dir = self.project_dir / ".workflow_status"
                status_dir.mkdir(exist_ok=True)
                success_file = status_dir / "test_script.success"
                success_file.write_text("success")
                
                # Mock successful script result
                from src.logic import RunResult
                result = RunResult(success=True, stdout="Test output", stderr="", return_code=0)
                
                # Should not raise exception despite sync error
                project.handle_step_result("step1", result)
                
                # Step should still be marked as completed
                assert project.get_state("step1") == "completed"
    
    def test_finalize_smart_sync(self):
        """Test the finalize_smart_sync method."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_manager.final_sync.return_value = True
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Call finalize
                project.finalize_smart_sync()
                
                # Verify final sync and cleanup were called
                mock_manager.final_sync.assert_called_once()
                mock_manager.cleanup.assert_called_once()
    
    def test_finalize_smart_sync_without_manager(self):
        """Test that finalize_smart_sync handles case where no Smart Sync manager exists."""
        project = Project(self.project_dir)
        
        # Should not raise exception
        project.finalize_smart_sync()
        
        assert project.smart_sync_manager is None
    
    def test_finalize_smart_sync_error_handling(self):
        """Test that finalize_smart_sync handles errors gracefully."""
        # Set up Smart Sync environment
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": str(self.network_dir),
            "LOCAL_PROJECT_PATH": str(self.local_dir)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock(spec=SmartSyncManager)
                mock_manager.final_sync.side_effect = Exception("Final sync error")
                mock_get_manager.return_value = mock_manager
                
                project = Project(self.project_dir)
                
                # Should not raise exception despite error
                project.finalize_smart_sync()
                
                # Verify final sync was attempted
                mock_manager.final_sync.assert_called_once()


class TestSmartSyncEnvironmentVariables:
    """Test Smart Sync environment variable handling."""
    
    def test_smart_sync_disabled_by_default(self):
        """Test that Smart Sync is disabled when environment variables are not set."""
        # Ensure Smart Sync environment variables are not set
        env_vars_to_unset = ["SMART_SYNC_ENABLED", "NETWORK_PROJECT_PATH", "LOCAL_PROJECT_PATH"]
        
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_unset:
                os.environ.pop(var, None)
            
            temp_dir = Path(tempfile.mkdtemp())
            try:
                project_dir = temp_dir / "test_project"
                project_dir.mkdir(parents=True)
                
                # Create minimal workflow
                workflow_file = project_dir / "workflow.yml"
                workflow_file.write_text("workflow_name: Test\nsteps: []")
                
                project = Project(project_dir, load_workflow=False)
                assert project.smart_sync_manager is None
            finally:
                shutil.rmtree(temp_dir)
    
    def test_smart_sync_enabled_with_partial_environment(self):
        """Test that Smart Sync is not enabled with incomplete environment variables."""
        # Set only some environment variables
        env_vars = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "/some/path"
            # Missing LOCAL_PROJECT_PATH
        }
        
        with patch.dict(os.environ, env_vars):
            temp_dir = Path(tempfile.mkdtemp())
            try:
                project_dir = temp_dir / "test_project"
                project_dir.mkdir(parents=True)
                
                # Create minimal workflow
                workflow_file = project_dir / "workflow.yml"
                workflow_file.write_text("workflow_name: Test\nsteps: []")
                
                project = Project(project_dir, load_workflow=False)
                assert project.smart_sync_manager is None
            finally:
                shutil.rmtree(temp_dir)
    
    def test_smart_sync_disabled_when_flag_false(self):
        """Test that Smart Sync is disabled when SMART_SYNC_ENABLED is false."""
        env_vars = {
            "SMART_SYNC_ENABLED": "false",
            "NETWORK_PROJECT_PATH": "/some/path",
            "LOCAL_PROJECT_PATH": "/other/path"
        }
        
        with patch.dict(os.environ, env_vars):
            temp_dir = Path(tempfile.mkdtemp())
            try:
                project_dir = temp_dir / "test_project"
                project_dir.mkdir(parents=True)
                
                # Create minimal workflow
                workflow_file = project_dir / "workflow.yml"
                workflow_file.write_text("workflow_name: Test\nsteps: []")
                
                project = Project(project_dir, load_workflow=False)
                assert project.smart_sync_manager is None
            finally:
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])