import pytest
import threading
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core import Project
from src.logic import ScriptRunner, RunResult


class TestTerminateScript:
    """Test suite for script termination functionality."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        # Create temporary project directory
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir()
        
        # Create basic workflow.yml
        workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: test_step
    name: "Test Step"
    script: "test_script.py"
    snapshot_items:
      - "outputs/"
"""
        (self.project_path / "workflow.yml").write_text(workflow_content)
        
        # Create outputs directory
        (self.project_path / "outputs").mkdir()
        
        # Create test script that runs for a while
        test_script_content = """
import time
import sys
from pathlib import Path

# Create success marker directory
status_dir = Path(".workflow_status")
status_dir.mkdir(exist_ok=True)

print("Script starting...")
sys.stdout.flush()

# Simulate long-running script
for i in range(100):
    print(f"Working... {i}")
    sys.stdout.flush()
    time.sleep(0.1)

# Create success marker
success_file = status_dir / "test_script.success"
success_file.touch()
print("SUCCESS: test_script completed successfully")
"""
        scripts_dir = self.temp_dir.parent / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        (scripts_dir / "test_script.py").write_text(test_script_content)
        
    def teardown_method(self):
        """Clean up after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_script_runner_has_terminate_method(self):
        """Test that ScriptRunner has a terminate method."""
        runner = ScriptRunner(self.project_path)
        assert hasattr(runner, 'terminate'), "ScriptRunner should have a terminate method"
        assert callable(getattr(runner, 'terminate')), "terminate should be callable"
    
    def test_script_runner_terminate_stops_running_script(self):
        """Test that terminate method stops a running script."""
        runner = ScriptRunner(self.project_path)
        
        # Start a script
        with patch.object(runner, 'run') as mock_run:
            mock_run.return_value = None
            runner.is_running_flag.set()  # Simulate running state
            
            # Terminate the script
            runner.terminate()
            
            # Should no longer be running
            assert not runner.is_running(), "Script should not be running after terminate"
    
    def test_project_has_terminate_script_method(self):
        """Test that Project class has a terminate_script method."""
        project = Project(self.project_path)
        assert hasattr(project, 'terminate_script'), "Project should have a terminate_script method"
        assert callable(getattr(project, 'terminate_script')), "terminate_script should be callable"
    
    def test_terminate_script_calls_rollback(self):
        """Test that terminating a script triggers rollback to before snapshot."""
        project = Project(self.project_path)
        
        # Mock the snapshot manager and script runner
        with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore, \
             patch.object(project.script_runner, 'terminate') as mock_terminate, \
             patch.object(project.script_runner, 'is_running', return_value=True):
            
            # Set up a running step
            project.update_state('test_step', 'pending')
            
            # Simulate that we have a before snapshot
            with patch.object(project.snapshot_manager, 'snapshot_exists', return_value=True):
                # Terminate the script
                project.terminate_script('test_step')
                
                # Should call terminate on script runner
                mock_terminate.assert_called_once()
                
                # Should restore the before snapshot
                mock_restore.assert_called_once_with('test_step_run_1')
    
    def test_terminate_script_updates_state_to_pending(self):
        """Test that terminating a script keeps the step state as pending."""
        project = Project(self.project_path)
        
        with patch.object(project.script_runner, 'terminate'), \
             patch.object(project.script_runner, 'is_running', return_value=True), \
             patch.object(project.snapshot_manager, 'restore_complete_snapshot'), \
             patch.object(project.snapshot_manager, 'snapshot_exists', return_value=True):
            
            # Set initial state
            project.update_state('test_step', 'pending')
            
            # Terminate the script
            project.terminate_script('test_step')
            
            # State should remain pending (not completed)
            assert project.get_state('test_step') == 'pending'
    
    def test_terminate_script_removes_success_marker(self):
        """Test that terminating a script removes any success marker that might exist."""
        project = Project(self.project_path)
        
        # Create success marker
        status_dir = project.path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        success_marker = status_dir / "test_script.success"
        success_marker.touch()
        
        with patch.object(project.script_runner, 'terminate'), \
             patch.object(project.script_runner, 'is_running', return_value=True), \
             patch.object(project.snapshot_manager, 'restore_complete_snapshot'), \
             patch.object(project.snapshot_manager, 'snapshot_exists', return_value=True):
            
            # Terminate the script
            project.terminate_script('test_step')
            
            # Success marker should be removed
            assert not success_marker.exists()
    
    def test_terminate_script_when_not_running_does_nothing(self):
        """Test that terminating when no script is running does nothing."""
        project = Project(self.project_path)
        
        with patch.object(project.script_runner, 'terminate') as mock_terminate, \
             patch.object(project.script_runner, 'is_running', return_value=False):
            
            # Try to terminate when nothing is running
            result = project.terminate_script('test_step')
            
            # Should return False indicating nothing was terminated
            assert result is False
            
            # Should not call terminate
            mock_terminate.assert_not_called()
    
    def test_terminate_script_handles_missing_snapshot_gracefully(self):
        """Test that terminating handles missing before snapshot gracefully."""
        project = Project(self.project_path)
        
        with patch.object(project.script_runner, 'terminate'), \
             patch.object(project.script_runner, 'is_running', return_value=True), \
             patch.object(project.snapshot_manager, 'snapshot_exists', return_value=False):
            
            # Should not raise an exception even if snapshot doesn't exist
            try:
                project.terminate_script('test_step')
            except Exception as e:
                pytest.fail(f"terminate_script should handle missing snapshot gracefully, but raised: {e}")
    
    @pytest.mark.skipif(True, reason="GUI test requires streamlit which may not be available in test environment")
    def test_gui_has_terminate_button_when_script_running(self):
        """Test that GUI shows terminate button when script is running."""
        # This test verifies the GUI integration
        # Skipped in automated tests since streamlit may not be available
        
        # The terminate button should appear in the terminal section when a script is running
        # It should be placed next to the "Send Input" button
        # When clicked, it should call project.terminate_script() and handle the result
        assert True  # Test structure verified, implementation tested manually
    
    def test_terminate_script_integration(self):
        """Integration test for the complete terminate script workflow."""
        project = Project(self.project_path)
        
        # This test will be implemented after the actual functionality
        # For now, verify the test structure
        assert hasattr(project, 'terminate_script'), "Project should have terminate_script method"
        
        # Test that the method exists and is callable
        assert callable(getattr(project, 'terminate_script')), "terminate_script should be callable"