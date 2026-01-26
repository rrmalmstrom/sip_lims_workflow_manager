"""
Test script termination functionality for the workflow manager.

This test validates that the script termination button functionality works correctly
by testing the underlying termination logic without launching Streamlit.

Following TDD approach as specified in the implementation plan.
"""

import pytest
import os
import sys
import time
import tempfile
import subprocess
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import Project
from logic import ScriptRunner, RunResult
from enhanced_debug_logger import log_info, log_error, debug_enabled

# Enable debug logging for tests
os.environ['WORKFLOW_DEBUG'] = 'true'


class TestScriptTerminationFunctionality:
    """Test suite for script termination functionality."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with workflow files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create workflow.yml
            workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: "test_step"
    name: "Test Long Running Script"
    script: "long_running_test.py"
"""
            (project_path / "workflow.yml").write_text(workflow_content)
            
            # Create a long-running test script
            script_content = """
import time
import sys

print("Script starting...")
sys.stdout.flush()

# Simulate long-running process
for i in range(100):
    print(f"Working... {i}")
    sys.stdout.flush()
    time.sleep(0.1)  # 10 seconds total

print("Script completed normally")
"""
            scripts_dir = project_path / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "long_running_test.py").write_text(script_content)
            
            yield project_path
    
    @pytest.fixture
    def project(self, temp_project_dir):
        """Create a Project instance for testing."""
        scripts_path = temp_project_dir / "scripts"
        project = Project(temp_project_dir, script_path=scripts_path)
        
        # Initialize workflow state
        project.update_state("test_step", "pending")
        
        return project
    
    def test_script_runner_termination_basic(self, project):
        """Test basic script runner termination functionality."""
        log_info("Starting basic script runner termination test")
        
        # Start a long-running script
        script_runner = project.script_runner
        
        # Verify script runner is not initially running
        assert not script_runner.is_running(), "Script runner should not be running initially"
        
        # Start the script in a separate thread to avoid blocking
        def start_script():
            script_runner.run("long_running_test.py", [])
        
        script_thread = threading.Thread(target=start_script)
        script_thread.start()
        
        # Wait for script to start
        max_wait = 5  # seconds
        start_time = time.time()
        while not script_runner.is_running() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Verify script is running
        assert script_runner.is_running(), "Script should be running after start"
        log_info("Script started successfully", is_running=script_runner.is_running())
        
        # Test termination
        log_info("Attempting script termination")
        script_runner.stop()
        
        # Wait for termination to complete
        max_wait = 3  # seconds
        start_time = time.time()
        while script_runner.is_running() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Verify script is no longer running
        assert not script_runner.is_running(), "Script should not be running after termination"
        log_info("Script termination completed", is_running=script_runner.is_running())
        
        # Clean up thread
        script_thread.join(timeout=1)
    
    def test_project_terminate_script_method(self, project):
        """Test the Project.terminate_script() method that the UI button calls."""
        log_info("Starting Project.terminate_script() method test")
        
        # Start a script
        script_runner = project.script_runner
        
        def start_script():
            script_runner.run("long_running_test.py", [])
        
        script_thread = threading.Thread(target=start_script)
        script_thread.start()
        
        # Wait for script to start
        max_wait = 5
        start_time = time.time()
        while not script_runner.is_running() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        assert script_runner.is_running(), "Script should be running before termination test"
        log_info("Script running, testing terminate_script method", step_id="test_step")
        
        # Test the terminate_script method (this is what the UI button calls)
        result = project.terminate_script("test_step")
        
        # Verify termination was successful
        assert result is True, "terminate_script() should return True on successful termination"
        log_info("terminate_script method result", result=result)
        
        # Wait for termination to complete
        max_wait = 3
        start_time = time.time()
        while script_runner.is_running() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Verify script is no longer running
        assert not script_runner.is_running(), "Script should not be running after terminate_script()"
        log_info("Script termination verification", is_running=script_runner.is_running())
        
        # Clean up
        script_thread.join(timeout=1)
    
    def test_terminate_script_when_not_running(self, project):
        """Test terminate_script() behavior when no script is running."""
        log_info("Testing terminate_script when no script is running")
        
        # Ensure no script is running
        assert not project.script_runner.is_running(), "No script should be running initially"
        
        # Call terminate_script when nothing is running
        result = project.terminate_script("test_step")
        
        # Should return False when no script is running
        assert result is False, "terminate_script() should return False when no script is running"
        log_info("terminate_script with no running script", result=result)
    
    def test_terminate_script_invalid_step(self, project):
        """Test terminate_script() with invalid step ID."""
        log_info("Testing terminate_script with invalid step ID")
        
        # Start a script first
        script_runner = project.script_runner
        
        def start_script():
            script_runner.run("long_running_test.py", [])
        
        script_thread = threading.Thread(target=start_script)
        script_thread.start()
        
        # Wait for script to start
        max_wait = 5
        start_time = time.time()
        while not script_runner.is_running() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        assert script_runner.is_running(), "Script should be running for invalid step test"
        
        # Test with invalid step ID
        with pytest.raises(ValueError, match="Step 'invalid_step' not found in workflow"):
            project.terminate_script("invalid_step")
        
        log_info("Invalid step ID test completed")
        
        # Clean up - terminate the running script
        project.script_runner.stop()
        script_thread.join(timeout=1)
    
    def test_process_group_termination_exceptions(self, project):
        """Test that process group termination handles exceptions correctly."""
        log_info("Testing process group termination exception handling")
        
        script_runner = project.script_runner
        
        # Mock the process to simulate different exception scenarios
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        
        # Test ProcessLookupError scenario
        with patch('os.getpgid', side_effect=ProcessLookupError("Process not found")):
            with patch.object(script_runner, 'process', mock_process):
                with patch.object(script_runner, 'is_running_flag') as mock_flag:
                    mock_flag.is_set.return_value = True
                    mock_flag.clear = Mock()
                    
                    # This should not raise an exception
                    script_runner.stop()
                    
                    # Verify the flag was cleared
                    mock_flag.clear.assert_called_once()
        
        log_info("ProcessLookupError handling test completed")
        
        # Test PermissionError scenario
        with patch('os.getpgid', return_value=12345):
            with patch('os.killpg', side_effect=PermissionError("Permission denied")):
                with patch.object(script_runner, 'process', mock_process):
                    with patch.object(script_runner, 'is_running_flag') as mock_flag:
                        mock_flag.is_set.return_value = True
                        mock_flag.clear = Mock()
                        
                        # Mock the fallback terminate method
                        mock_process.terminate = Mock()
                        mock_process.wait = Mock()
                        
                        # This should not raise an exception and should use fallback
                        script_runner.stop()
                        
                        # Verify fallback was called
                        mock_process.terminate.assert_called_once()
                        mock_flag.clear.assert_called_once()
        
        log_info("PermissionError handling test completed")
    
    def test_debug_logging_during_termination(self, project):
        """Test that debug logging is working during termination."""
        log_info("Testing debug logging during termination")
        
        # Verify debug logging is enabled
        assert debug_enabled(), "Debug logging should be enabled for tests"
        
        # Start and terminate a script to generate debug logs
        script_runner = project.script_runner
        
        def start_script():
            script_runner.run("long_running_test.py", [])
        
        script_thread = threading.Thread(target=start_script)
        script_thread.start()
        
        # Wait for script to start
        max_wait = 5
        start_time = time.time()
        while not script_runner.is_running() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        if script_runner.is_running():
            # Terminate and check that debug logs are generated
            log_info("About to call terminate_script for debug logging test")
            result = project.terminate_script("test_step")
            log_info("terminate_script completed for debug logging test", result=result)
            
            # Wait for termination
            max_wait = 3
            start_time = time.time()
            while script_runner.is_running() and (time.time() - start_time) < max_wait:
                time.sleep(0.1)
        
        # Clean up
        script_thread.join(timeout=1)
        
        # Check that debug output directory exists and has log files
        debug_dir = Path.cwd() / "debug_output"
        assert debug_dir.exists(), "Debug output directory should exist"
        
        log_files = list(debug_dir.glob("workflow_debug_*.log"))
        assert len(log_files) > 0, "Debug log files should be created"
        
        log_info("Debug logging test completed", debug_files_found=len(log_files))


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])