#!/usr/bin/env python3
"""
Test Enhanced Debug Logger Integration

Tests to verify the enhanced debug logger works correctly and can be integrated
into the Mac + VNC baseline without breaking existing functionality.
"""

import pytest
import tempfile
import json
import os
import time
from pathlib import Path
from unittest.mock import patch

# Import the enhanced debug logger
from src.enhanced_debug_logger import (
    EnhancedDebugLogger, 
    LogLevel, 
    get_debug_logger, 
    close_debug_logger,
    debug_enabled,
    get_debug_level,
    debug_context,
    log_error,
    log_info,
    log_warning
)


class TestEnhancedDebugLoggerIntegration:
    """Test the enhanced debug logger integration with baseline system."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = Path(self.temp_dir) / "test_debug.log"
        
        # Reset global logger
        close_debug_logger()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Reset global logger
        close_debug_logger()
    
    def test_enhanced_debug_logger_imports_successfully(self):
        """Test that enhanced debug logger can be imported without errors."""
        # This test verifies the import works (already passed in command line)
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.DEBUG
        )
        
        assert logger is not None
        assert isinstance(logger, EnhancedDebugLogger)
        assert logger.log_file == self.test_log_file
        assert logger.console_output == False
        assert logger.log_level == LogLevel.DEBUG
        
        logger.close()
    
    def test_enhanced_debug_logger_basic_functionality(self):
        """Test basic debug logging functionality."""
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.DEBUG
        )
        
        # Test all log levels
        logger.debug("Test debug message")
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.critical("Test critical message")
        
        logger.close()
        
        # Verify log file was created and contains entries
        assert self.test_log_file.exists()
        
        with open(self.test_log_file, 'r') as f:
            log_content = f.read()
            
        # Should contain all log levels plus session start/end
        assert "SESSION_START" in log_content
        assert "DEBUG" in log_content
        assert "INFO" in log_content
        assert "WARNING" in log_content
        assert "ERROR" in log_content
        assert "CRITICAL" in log_content
        assert "SESSION_END" in log_content
    
    def test_mac_vnc_specific_logging_functions(self):
        """Test Mac + VNC specific logging functions."""
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.INFO
        )
        
        # Test VNC session logging
        logger.log_vnc_session_start("vnc_test_123", "testuser", "192.168.1.100")
        
        # Test native script execution logging
        logger.log_native_script_execution("/path/to/test_script.py", ["arg1", "arg2"], "/test/working/dir")
        
        # Test workflow step logging
        logger.log_workflow_step_native("test_step_1", True, 2.5, "Step completed successfully")
        logger.log_workflow_step_native("test_step_2", False, 1.2, "Step failed with error")
        
        logger.close()
        
        # Verify VNC sessions were tracked
        assert len(logger.performance_stats["vnc_sessions"]) == 1
        vnc_session = logger.performance_stats["vnc_sessions"][0]
        assert vnc_session["vnc_session_id"] == "vnc_test_123"
        assert vnc_session["user"] == "testuser"
        assert vnc_session["client_ip"] == "192.168.1.100"
        
        # Verify script executions were tracked
        assert len(logger.performance_stats["script_executions"]) == 1
        script_exec = logger.performance_stats["script_executions"][0]
        assert script_exec["script_path"] == "/path/to/test_script.py"
        assert script_exec["execution_method"] == "native_python"
        assert script_exec["arguments"] == ["arg1", "arg2"]
    
    def test_operation_timer_context_manager(self):
        """Test the operation timer context manager."""
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.DEBUG
        )
        
        # Test successful operation
        with logger.operation_timer("test_operation", param1="value1") as operation_id:
            assert operation_id.startswith("test_operation_")
            # Simulate some work
            time.sleep(0.1)
        
        # Test failed operation
        with pytest.raises(ValueError):
            with logger.operation_timer("failing_operation") as operation_id:
                raise ValueError("Test error")
        
        logger.close()
        
        # Verify performance tracking
        assert len(logger.performance_stats["workflow_operations"]) == 1
        operation = logger.performance_stats["workflow_operations"][0]
        assert operation["operation"] == "test_operation"
        assert operation["duration"] >= 0.1
        assert operation["context"]["param1"] == "value1"
        
        # Verify error tracking
        assert len(logger.performance_stats["errors"]) == 1
        error = logger.performance_stats["errors"][0]
        assert "failing_operation" in error["message"]
    
    def test_performance_summary_generation(self):
        """Test performance summary generation."""
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.INFO
        )
        
        # Add some test data
        logger.log_vnc_session_start("vnc_1", "user1")
        logger.log_native_script_execution("/script1.py", [])
        logger.error("Test error")
        
        with logger.operation_timer("test_op"):
            time.sleep(0.05)
        
        summary = logger.get_performance_summary()
        
        assert summary["session_id"] == logger.session_id
        assert summary["total_vnc_sessions"] == 1
        assert summary["total_script_executions"] == 1
        assert summary["total_errors"] == 1
        assert summary["total_workflow_operations"] == 1
        assert summary["session_duration"] > 0
        assert summary["average_operation_duration"] >= 0.05
        
        logger.close()
    
    def test_global_logger_functions(self):
        """Test global logger convenience functions."""
        # Test debug_enabled with environment variable
        with patch.dict(os.environ, {"WORKFLOW_DEBUG": "true"}):
            assert debug_enabled() == True
        
        with patch.dict(os.environ, {"WORKFLOW_DEBUG": "false"}):
            assert debug_enabled() == False
        
        # Test debug level detection
        with patch.dict(os.environ, {"WORKFLOW_DEBUG_LEVEL": "DEBUG"}):
            assert get_debug_level() == LogLevel.DEBUG
        
        with patch.dict(os.environ, {"WORKFLOW_DEBUG_LEVEL": "invalid"}):
            assert get_debug_level() == LogLevel.INFO  # Default fallback
    
    def test_convenience_logging_functions(self):
        """Test convenience logging functions."""
        with patch.dict(os.environ, {"WORKFLOW_DEBUG": "true"}):
            # These should not raise errors
            log_info("Test info message", param="value")
            log_warning("Test warning message")
            log_error("Test error message", error_code=500)
    
    def test_debug_context_manager(self):
        """Test debug context manager."""
        with patch.dict(os.environ, {"WORKFLOW_DEBUG": "true", "WORKFLOW_DEBUG_LEVEL": "DEBUG"}):
            with debug_context("test_context_operation", param="test") as logger:
                assert logger is not None
                assert isinstance(logger, EnhancedDebugLogger)
        
        # Test with debug disabled
        with patch.dict(os.environ, {"WORKFLOW_DEBUG": "false"}):
            with debug_context("test_context_operation") as logger:
                assert logger is None
    
    def test_export_debug_data(self):
        """Test debug data export functionality."""
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.INFO
        )
        
        # Add some test data
        logger.info("Test message")
        logger.log_vnc_session_start("vnc_1", "user1")
        
        # Export data
        export_file = logger.export_debug_data()
        
        assert export_file.exists()
        assert export_file.name.startswith("workflow_debug_export_")
        assert export_file.suffix == ".json"
        
        # Verify export content
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        
        assert "session_info" in export_data
        assert "performance_stats" in export_data
        assert "performance_summary" in export_data
        assert export_data["session_info"]["session_id"] == logger.session_id
        
        logger.close()
    
    def test_thread_safety(self):
        """Test that the logger is thread-safe."""
        import threading
        
        logger = EnhancedDebugLogger(
            log_file=self.test_log_file,
            console_output=False,
            log_level=LogLevel.INFO
        )
        results = []
        
        def log_messages(thread_id):
            for i in range(5):
                logger.info(f"Thread {thread_id} message {i}")
                time.sleep(0.01)
            results.append(f"thread_{thread_id}_complete")
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        logger.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])