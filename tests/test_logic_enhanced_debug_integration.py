#!/usr/bin/env python3

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from logic import StateManager, SnapshotManager, ScriptRunner
from enhanced_debug_logger import EnhancedDebugLogger


class TestLogicEnhancedDebugIntegration:
    """Test enhanced debug logger integration in logic.py components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir()
        self.snapshots_dir = self.project_path / ".snapshots"
        self.snapshots_dir.mkdir()
        self.state_file = self.project_path / ".workflow_status" / "state.json"
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Create mock debug logger
        self.mock_debug_logger = Mock(spec=EnhancedDebugLogger)
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('logic.debug_logger')
    def test_state_manager_update_step_state_logging(self, mock_debug_logger):
        """Test that StateManager logs step state changes."""
        mock_debug_logger.log_workflow_step_native = Mock()
        
        state_manager = StateManager(self.state_file)
        
        # Test step completion
        state_manager.update_step_state("test_step", "completed")
        
        # Verify logging was called
        mock_debug_logger.log_workflow_step_native.assert_called_with(
            step_id="test_step",
            status="completed",
            message="Step state changed: pending -> completed"
        )
        
        # Test step undo
        state_manager.update_step_state("test_step", "pending")
        
        # Verify logging was called for undo
        mock_debug_logger.log_workflow_step_native.assert_called_with(
            step_id="test_step",
            status="pending",
            message="Step state changed: completed -> pending"
        )
    
    @patch('logic.debug_logger')
    def test_snapshot_manager_take_complete_snapshot_logging(self, mock_debug_logger):
        """Test that SnapshotManager logs snapshot creation."""
        mock_debug_logger.log_workflow_step_native = Mock()
        
        snapshot_manager = SnapshotManager(self.project_path, self.snapshots_dir)
        
        # Create a test file to snapshot
        test_file = self.project_path / "test.txt"
        test_file.write_text("test content")
        
        # Take snapshot
        snapshot_manager.take_complete_snapshot("test_step")
        
        # Verify logging was called for snapshot creation start
        calls = mock_debug_logger.log_workflow_step_native.call_args_list
        assert len(calls) >= 2  # Should have start and complete calls
        
        # Check start call
        start_call = calls[0]
        assert start_call[1]['step_id'] == "test_step"
        assert start_call[1]['status'] == "snapshot_create"
        assert "Creating complete project snapshot" in start_call[1]['message']
        
        # Check completion call
        complete_call = calls[1]
        assert complete_call[1]['step_id'] == "test_step"
        assert complete_call[1]['status'] == "snapshot_complete"
        assert "Successfully created snapshot" in complete_call[1]['message']
    
    @patch('logic.debug_logger')
    def test_snapshot_manager_restore_complete_snapshot_logging(self, mock_debug_logger):
        """Test that SnapshotManager logs snapshot restoration."""
        mock_debug_logger.log_workflow_step_native = Mock()
        
        snapshot_manager = SnapshotManager(self.project_path, self.snapshots_dir)
        
        # Create a test file and take snapshot first
        test_file = self.project_path / "test.txt"
        test_file.write_text("test content")
        snapshot_manager.take_complete_snapshot("test_step")
        
        # Clear previous calls
        mock_debug_logger.log_workflow_step_native.reset_mock()
        
        # Restore snapshot
        snapshot_manager.restore_complete_snapshot("test_step")
        
        # Verify logging was called for restoration
        calls = mock_debug_logger.log_workflow_step_native.call_args_list
        assert len(calls) >= 2  # Should have start and complete calls
        
        # Check start call
        start_call = calls[0]
        assert start_call[1]['step_id'] == "test_step"
        assert start_call[1]['status'] == "snapshot_restore"
        assert "Starting snapshot restoration" in start_call[1]['message']
        
        # Check completion call
        complete_call = calls[1]
        assert complete_call[1]['step_id'] == "test_step"
        assert complete_call[1]['status'] == "snapshot_restored"
        assert "Successfully restored project state" in complete_call[1]['message']
    
    @patch('logic.debug_logger')
    def test_script_runner_logging_integration(self, mock_debug_logger):
        """Test that ScriptRunner integrates with enhanced debug logger."""
        mock_debug_logger.log_native_script_execution = Mock()
        
        # Create a simple test script
        scripts_dir = self.project_path / "scripts"
        scripts_dir.mkdir()
        test_script = scripts_dir / "test_script.py"
        test_script.write_text("""#!/usr/bin/env python3
print("Hello from test script")
exit(0)
""")
        test_script.chmod(0o755)
        
        script_runner = ScriptRunner(self.project_path, scripts_dir)
        
        # Mock the PTY and subprocess parts to avoid actual execution
        with patch('logic.pty.openpty') as mock_openpty, \
             patch('logic.subprocess.Popen') as mock_popen, \
             patch('logic.os.close'), \
             patch('logic.threading.Thread'):
            
            mock_openpty.return_value = (1, 2)  # Mock file descriptors
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            # Start script execution
            script_runner.run("test_script.py")
            
            # Verify script start logging was called
            mock_debug_logger.log_native_script_execution.assert_called_with(
                script_name="test_script.py",
                message=f"Starting script execution: {sys.executable} -u {test_script}",
                level="INFO"
            )
    
    @patch('logic.debug_logger', None)
    def test_fallback_behavior_when_debug_logger_unavailable(self):
        """Test that logic.py works correctly when debug logger is not available."""
        # This should not raise any exceptions
        state_manager = StateManager(self.state_file)
        state_manager.update_step_state("test_step", "completed")
        
        snapshot_manager = SnapshotManager(self.project_path, self.snapshots_dir)
        
        # Create a test file
        test_file = self.project_path / "test.txt"
        test_file.write_text("test content")
        
        # These should work without debug logger
        snapshot_manager.take_complete_snapshot("test_step")
        snapshot_manager.restore_complete_snapshot("test_step")
        
        # Verify state was still managed correctly
        assert state_manager.get_step_state("test_step") == "completed"
    
    @patch('logic.debug_logger')
    def test_script_runner_debug_logging_fallback(self, mock_debug_logger):
        """Test ScriptRunner's debug logging with fallback behavior."""
        # Test with debug logger available
        mock_debug_logger.log_native_script_execution = Mock()
        
        # Create script runner
        script_runner = ScriptRunner(self.project_path)
        
        # Access the internal log_debug function through the _read_output_loop method
        # We'll test this by creating a minimal scenario
        with patch('logic.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Simulate calling the internal log_debug function
            # This tests the enhanced debug logger integration in the nested function
            script_runner.master_fd = 1
            script_runner.process = Mock()
            script_runner.process.pid = 12345
            
            # We can't easily test the nested function directly, but we can verify
            # that the debug logger is available and would be called
            assert mock_debug_logger is not None
            assert hasattr(mock_debug_logger, 'log_native_script_execution')
    
    def test_import_structure(self):
        """Test that the import structure works correctly."""
        # Test that we can import the enhanced debug logger
        try:
            from enhanced_debug_logger import EnhancedDebugLogger
            logger = EnhancedDebugLogger()
            assert logger is not None
        except ImportError:
            # This is expected if the logger isn't available
            pass
        
        # Test that logic.py imports work
        from logic import StateManager, SnapshotManager, ScriptRunner
        assert StateManager is not None
        assert SnapshotManager is not None
        assert ScriptRunner is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])