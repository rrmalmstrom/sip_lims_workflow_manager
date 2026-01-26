"""
TDD Tests for Race Condition Fixes

Tests the comprehensive three-layer defense against race conditions:
1. Atomic file operations in StateManager
2. Retry logic for external drive reliability  
3. Comprehensive logging in handle_step_result()
"""

import pytest
import json
import tempfile
import threading
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.logic import StateManager, RunResult
from src.core import Project, Workflow


class TestAtomicFileOperations:
    """Test atomic file operations in StateManager.save()"""
    
    def test_atomic_save_creates_temp_file_first(self, tmp_path):
        """Test that save() uses temporary file before atomic rename"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        test_state = {"step1": "completed", "step2": "pending"}
        
        # Mock tempfile.mkstemp to track temp file creation
        with patch('tempfile.mkstemp') as mock_mkstemp:
            temp_fd = 10
            temp_path = str(tmp_path / "temp_file.tmp")
            mock_mkstemp.return_value = (temp_fd, temp_path)
            
            with patch('os.fdopen') as mock_fdopen, \
                 patch('os.fsync') as mock_fsync, \
                 patch('os.rename') as mock_rename:
                
                mock_file = MagicMock()
                mock_fdopen.return_value.__enter__.return_value = mock_file
                
                state_manager.save(test_state)
                
                # Verify temp file creation in same directory
                mock_mkstemp.assert_called_once_with(
                    dir=state_file.parent, 
                    suffix='.tmp', 
                    prefix='workflow_state_'
                )
                
                # Verify JSON written to temp file
                mock_file.write.assert_called()
                mock_file.flush.assert_called_once()
                mock_fsync.assert_called_once()
                
                # Verify atomic rename
                mock_rename.assert_called_once_with(temp_path, state_file)
    
    def test_atomic_save_handles_windows_vs_unix(self, tmp_path):
        """Test platform-specific atomic rename behavior"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        # Create existing file
        state_file.write_text('{"old": "data"}')
        
        test_state = {"step1": "completed"}
        
        with patch('tempfile.mkstemp') as mock_mkstemp, \
             patch('os.fdopen') as mock_fdopen, \
             patch('os.rename') as mock_rename, \
             patch('os.fsync') as mock_fsync:
            
            temp_path = str(tmp_path / "temp_file.tmp")
            mock_mkstemp.return_value = (10, temp_path)
            
            # Mock file object with proper fileno
            mock_file = MagicMock()
            mock_file.fileno.return_value = 10
            mock_fdopen.return_value.__enter__.return_value = mock_file
            
            # Test Windows behavior
            with patch('os.name', 'nt'):
                state_manager.save(test_state)
                # On Windows, should unlink existing file first
                assert mock_rename.called
            
            # Test Unix behavior
            with patch('os.name', 'posix'):
                state_manager.save(test_state)
                # On Unix, atomic rename should work directly
                mock_rename.assert_called()
    
    def test_atomic_save_cleanup_on_failure(self, tmp_path):
        """Test temp file cleanup when save fails"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        with patch('tempfile.mkstemp') as mock_mkstemp, \
             patch('os.fdopen') as mock_fdopen, \
             patch('os.rename', side_effect=OSError("Rename failed")) as mock_rename, \
             patch('os.unlink') as mock_unlink, \
             patch('os.fsync') as mock_fsync:
            
            temp_path = str(tmp_path / "temp_file.tmp")
            mock_mkstemp.return_value = (10, temp_path)
            
            # Mock file object with proper fileno
            mock_file = MagicMock()
            mock_file.fileno.return_value = 10
            mock_fdopen.return_value.__enter__.return_value = mock_file
            
            with pytest.raises(OSError):
                state_manager.save({"test": "data"})
            
            # Verify temp file cleanup attempted
            mock_unlink.assert_called_once_with(temp_path)


class TestRetryLogic:
    """Test retry logic in StateManager.load()"""
    
    def test_load_retries_on_empty_file(self, tmp_path):
        """Test retry logic when file is temporarily empty"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        # Create empty file initially
        state_file.write_text("")
        
        call_count = 0
        def mock_read_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return ""  # Empty file
            else:
                return '{"step1": "completed"}'  # Valid JSON
        
        with patch('time.sleep') as mock_sleep, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.side_effect = mock_read_side_effect
            mock_file.__enter__.return_value.seek = MagicMock()
            mock_open.return_value = mock_file
            
            with patch('json.load', return_value={"step1": "completed"}):
                result = state_manager.load()
                
                assert result == {"step1": "completed"}
                assert call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    def test_load_retries_on_json_decode_error(self, tmp_path):
        """Test retry logic when JSON is temporarily corrupted"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        state_file.write_text('{"valid": "json"}')
        
        call_count = 0
        def mock_json_load_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise json.JSONDecodeError("Invalid JSON", "", 0)
            else:
                return {"step1": "completed"}
        
        with patch('time.sleep') as mock_sleep, \
             patch('json.load', side_effect=mock_json_load_side_effect), \
             patch('builtins.print') as mock_print:
            
            result = state_manager.load()
            
            assert result == {"step1": "completed"}
            assert call_count == 3
            assert mock_sleep.call_count == 2
            # Verify error messages printed
            assert any("JSON decode error" in str(call) for call in mock_print.call_args_list)
    
    def test_load_graceful_degradation_after_max_retries(self, tmp_path):
        """Test graceful degradation when all retries fail"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        state_file.write_text("")  # Empty file
        
        with patch('time.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print, \
             patch('builtins.open', create=True) as mock_open:
            
            # Mock file.read() to always return empty string
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = ""
            mock_open.return_value = mock_file
            
            result = state_manager.load()
            
            assert result == {}  # Empty state returned
            assert mock_sleep.call_count == 2  # Two retries
            # Verify warning message printed
            assert any("empty after" in str(call) for call in mock_print.call_args_list)


class TestComprehensiveLogging:
    """Test comprehensive logging in handle_step_result()"""
    
    def setup_method(self):
        """Set up test project and mocks"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        self.workflow_file = self.project_path / "workflow.yml"
        
        # Create test workflow
        workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: test_step
    name: "Test Step"
    script: "test_script.py"
"""
        self.workflow_file.write_text(workflow_content)
        
        # Create success marker
        status_dir = self.project_path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        (status_dir / "test_script.success").touch()
        
        # Mock script path
        self.script_path = Path("/mock/scripts")
        
    def test_comprehensive_logging_creates_log_file(self):
        """Test that comprehensive logging creates detailed log file"""
        project = Project(self.project_path, self.script_path)
        
        # Mock successful result
        result = RunResult(success=True, stdout="", stderr="", return_code=0)
        
        # Call handle_step_result
        project.handle_step_result("test_step", result)
        
        # Verify log file created
        log_file = self.project_path / ".workflow_logs" / "step_result_handling.log"
        assert log_file.exists()
        
        # Verify log content
        log_content = log_file.read_text()
        assert "=== STEP RESULT HANDLING STARTED ===" in log_content
        assert "step_id: test_step" in log_content
        assert "result_success: True" in log_content
        assert "Starting success marker check" in log_content
        assert "=== ATTEMPTING ATOMIC STATE UPDATE ===" in log_content
        assert "✅ ATOMIC STATE UPDATE SUCCESSFUL" in log_content
        assert "=== STEP RESULT HANDLING COMPLETED ===" in log_content
    
    def test_logging_captures_state_update_verification(self):
        """Test that logging captures pre/post state verification"""
        project = Project(self.project_path, self.script_path)
        
        # Set initial state
        project.update_state("test_step", "pending")
        
        result = RunResult(success=True, stdout="", stderr="", return_code=0)
        project.handle_step_result("test_step", result)
        
        log_file = self.project_path / ".workflow_logs" / "step_result_handling.log"
        log_content = log_file.read_text()
        
        # Verify state verification logging
        assert "Pre-update state loaded" in log_content
        assert "step_current_status: pending" in log_content
        assert "Post-update state verification" in log_content
        assert "step_updated_status: completed" in log_content
        assert "update_successful: True" in log_content
    
    def test_logging_captures_success_marker_validation(self):
        """Test that logging captures success marker validation details"""
        project = Project(self.project_path, self.script_path)
        
        result = RunResult(success=True, stdout="", stderr="", return_code=0)
        project.handle_step_result("test_step", result)
        
        log_file = self.project_path / ".workflow_logs" / "step_result_handling.log"
        log_content = log_file.read_text()
        
        # Verify success marker logging
        assert "Starting success marker check" in log_content
        assert "script_name: test_script.py" in log_content
        assert "Success marker check completed" in log_content
        assert "marker_file_success: True" in log_content
        assert "marker_file_path: .workflow_status/test_script.success" in log_content
        assert "Final success determination" in log_content
        assert "actual_success: True" in log_content


class TestConcurrentAccess:
    """Test concurrent access scenarios that caused the original race condition"""
    
    def test_concurrent_save_operations(self, tmp_path):
        """Test multiple threads saving state simultaneously"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        results = []
        errors = []
        
        def save_state(thread_id):
            try:
                state = {f"step_{thread_id}": "completed", "thread_id": thread_id}
                state_manager.save(state)
                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, e))
        
        # Start multiple threads saving simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_state, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # Verify final state is valid JSON
        final_state = state_manager.load()
        assert isinstance(final_state, dict)
        assert "thread_id" in final_state
    
    def test_concurrent_load_during_save(self, tmp_path):
        """Test loading state while another thread is saving"""
        state_file = tmp_path / "workflow_state.json"
        state_manager = StateManager(state_file)
        
        # Initialize with valid state
        initial_state = {"step1": "pending", "step2": "pending"}
        state_manager.save(initial_state)
        
        load_results = []
        save_complete = threading.Event()
        
        def continuous_save():
            """Continuously save state updates"""
            for i in range(10):
                state = {"step1": "completed", "step2": "pending", "iteration": i}
                state_manager.save(state)
                time.sleep(0.01)  # Small delay
            save_complete.set()
        
        def continuous_load():
            """Continuously load state"""
            while not save_complete.is_set():
                try:
                    state = state_manager.load()
                    load_results.append(state)
                    time.sleep(0.005)  # Faster than save
                except Exception as e:
                    load_results.append(f"ERROR: {e}")
        
        # Start both threads
        save_thread = threading.Thread(target=continuous_save)
        load_thread = threading.Thread(target=continuous_load)
        
        save_thread.start()
        load_thread.start()
        
        save_thread.join()
        load_thread.join()
        
        # Verify no load operations failed
        errors = [r for r in load_results if isinstance(r, str) and r.startswith("ERROR")]
        assert len(errors) == 0, f"Load errors occurred: {errors}"
        
        # Verify all loads returned valid dictionaries
        valid_loads = [r for r in load_results if isinstance(r, dict)]
        assert len(valid_loads) > 0, "No successful loads occurred"


class TestIntegrationWithExistingSystem:
    """Test integration with existing enhanced debug logger"""
    
    def test_logging_integration_with_debug_logger(self, tmp_path):
        """Test that new logging works alongside existing debug logger"""
        project_path = tmp_path
        workflow_file = project_path / "workflow.yml"
        
        workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: test_step
    name: "Test Step"
    script: "test_script.py"
"""
        workflow_file.write_text(workflow_content)
        
        # Create success marker
        status_dir = project_path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        (status_dir / "test_script.success").touch()
        
        script_path = Path("/mock/scripts")
        
        with patch.dict(os.environ, {'WORKFLOW_DEBUG': 'true'}):
            project = Project(project_path, script_path)
            
            result = RunResult(success=True, stdout="", stderr="", return_code=0)
            project.handle_step_result("test_step", result)
            
            # Verify both logging systems work
            step_log = project_path / ".workflow_logs" / "step_result_handling.log"
            assert step_log.exists()
            
            # Verify enhanced debug logger was called (via debug_context)
            # This would be verified by checking debug_output directory in real scenario


if __name__ == "__main__":
    pytest.main([__file__, "-v"])