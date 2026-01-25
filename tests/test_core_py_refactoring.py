"""
Test suite for src/core.py refactoring to remove Smart Sync integration.
This test ensures that core.py is properly refactored to work with native execution
while preserving all essential project management functionality.

Following TDD methodology:
1. Write tests first (RED)
2. Refactor core.py (GREEN) 
3. Validate and optimize (REFACTOR)
"""

import os
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestCorePySmartSyncRemoval:
    """Test that Smart Sync integration is removed from core.py."""
    
    def test_no_smart_sync_imports(self):
        """Test that Smart Sync imports are removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync imports are removed
                smart_sync_imports = [
                    'from src.smart_sync import',
                    'import src.smart_sync',
                    'get_smart_sync_manager'
                ]
                for smart_sync_import in smart_sync_imports:
                    assert smart_sync_import not in content, f"Smart Sync import '{smart_sync_import}' should be removed from core.py"
    
    def test_no_smart_sync_manager_initialization(self):
        """Test that Smart Sync manager initialization is removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync manager initialization is removed
                smart_sync_init_patterns = [
                    'self.smart_sync_manager = None',
                    'smart_sync_enabled = os.getenv("SMART_SYNC_ENABLED")',
                    'get_smart_sync_manager(',
                    'self.smart_sync_manager = get_smart_sync_manager'
                ]
                for pattern in smart_sync_init_patterns:
                    assert pattern not in content, f"Smart Sync initialization '{pattern}' should be removed from core.py"
    
    def test_no_smart_sync_environment_variables(self):
        """Test that Smart Sync environment variable checks are removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync environment variables are removed
                smart_sync_env_vars = [
                    'SMART_SYNC_ENABLED',
                    'NETWORK_PROJECT_PATH',
                    'LOCAL_PROJECT_PATH'
                ]
                for env_var in smart_sync_env_vars:
                    assert env_var not in content, f"Smart Sync environment variable '{env_var}' should be removed from core.py"
    
    def test_no_smart_sync_operations(self):
        """Test that Smart Sync operations are removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync operations are removed
                smart_sync_operations = [
                    'incremental_sync_down',
                    'incremental_sync_up',
                    'pre-step sync',
                    'post-step sync',
                    'Smart Sync: Syncing',
                    'Smart Sync: Saving results'
                ]
                for operation in smart_sync_operations:
                    assert operation not in content, f"Smart Sync operation '{operation}' should be removed from core.py"


class TestCorePyProjectFunctionality:
    """Test that essential project functionality is preserved in core.py."""
    
    def test_project_class_preserved(self):
        """Test that Project class is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                assert 'class Project:' in content, "Project class should be preserved in core.py"
    
    def test_project_initialization_preserved(self):
        """Test that Project initialization is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for essential Project initialization components
                init_components = [
                    'def __init__',
                    'self.path',
                    'self.workflow',
                    'self.state_manager',
                    'self.snapshot_manager',
                    'self.script_runner'
                ]
                for component in init_components:
                    assert component in content, f"Project initialization component '{component}' should be preserved in core.py"
    
    def test_workflow_management_preserved(self):
        """Test that workflow management functionality is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for workflow management methods
                workflow_methods = [
                    'def run_step',
                    'def get_state',
                    'def update_state',
                    'def skip_to_step'
                ]
                for method in workflow_methods:
                    assert method in content, f"Workflow management method '{method}' should be preserved in core.py"
    
    def test_snapshot_functionality_preserved(self):
        """Test that snapshot functionality is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for snapshot-related functionality
                snapshot_indicators = [
                    'snapshot',
                    'create_snapshot',
                    'restore_snapshot'
                ]
                has_snapshot_functionality = any(indicator in content for indicator in snapshot_indicators)
                assert has_snapshot_functionality, "Snapshot functionality should be preserved in core.py"


class TestCorePyNativeExecution:
    """Test that core.py works with native execution."""
    
    def test_no_smart_sync_conditional_logic(self):
        """Test that Smart Sync conditional logic is removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync conditional checks are removed
                smart_sync_conditionals = [
                    'if self.smart_sync_manager:',
                    'if smart_sync_enabled:',
                    'if not self.smart_sync_manager:'
                ]
                for conditional in smart_sync_conditionals:
                    assert conditional not in content, f"Smart Sync conditional '{conditional}' should be removed from core.py"
    
    def test_native_step_execution_preserved(self):
        """Test that native step execution is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for native step execution components
                execution_components = [
                    'script_runner',
                    'run_step',
                    'handle_step_result'
                ]
                for component in execution_components:
                    assert component in content, f"Native execution component '{component}' should be preserved in core.py"
    
    def test_success_detection_simplified(self):
        """Test that success detection is simplified without Smart Sync."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that success detection doesn't depend on Smart Sync
                success_indicators = [
                    'exit_code_success',
                    'marker_file_success',
                    'success_marker'
                ]
                has_success_detection = any(indicator in content for indicator in success_indicators)
                assert has_success_detection, "Success detection should be preserved in core.py"
                
                # But should not have Smart Sync success requirements
                assert 'sync_success' not in content, "Smart Sync success checks should be removed from core.py"


class TestCorePyErrorHandling:
    """Test that error handling is preserved without Smart Sync dependencies."""
    
    def test_error_handling_preserved(self):
        """Test that error handling is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for error handling
                error_handling_patterns = [
                    'try:',
                    'except',
                    'Exception',
                    'error'
                ]
                has_error_handling = any(pattern in content for pattern in error_handling_patterns)
                assert has_error_handling, "Error handling should be preserved in core.py"
    
    def test_no_smart_sync_error_handling(self):
        """Test that Smart Sync specific error handling is removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync error handling is removed
                smart_sync_errors = [
                    'Smart Sync initialization failed',
                    'Smart Sync: Pre-step sync failed',
                    'Smart Sync: Failed to save results',
                    'Smart Sync: Error saving results'
                ]
                for error in smart_sync_errors:
                    assert error not in content, f"Smart Sync error '{error}' should be removed from core.py"


class TestCorePyLogging:
    """Test that logging is preserved without Smart Sync specific logging."""
    
    def test_debug_logging_preserved(self):
        """Test that debug logging functionality is preserved."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for debug logging
                logging_components = [
                    'debug_context',
                    'log_info',
                    'log_error',
                    'debug_logger'
                ]
                for component in logging_components:
                    assert component in content, f"Debug logging component '{component}' should be preserved in core.py"
    
    def test_no_smart_sync_logging(self):
        """Test that Smart Sync specific logging is removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync logging is removed
                smart_sync_logging = [
                    'log_smart_sync_detection',
                    'Smart Sync check',
                    'Smart Sync environment variables',
                    'Smart Sync manager created',
                    'Starting pre-step Smart Sync',
                    'Starting post-step Smart Sync'
                ]
                for log_entry in smart_sync_logging:
                    assert log_entry not in content, f"Smart Sync logging '{log_entry}' should be removed from core.py"


class TestCorePyPerformance:
    """Test that core.py performance is optimized without Smart Sync overhead."""
    
    def test_no_smart_sync_overhead(self):
        """Test that Smart Sync overhead is removed."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync overhead operations are removed
                overhead_operations = [
                    'incremental_sync',
                    'sync_down',
                    'sync_up',
                    'network -> local',
                    'local -> network'
                ]
                for operation in overhead_operations:
                    assert operation not in content, f"Smart Sync overhead operation '{operation}' should be removed from core.py"
    
    def test_streamlined_step_execution(self):
        """Test that step execution is streamlined without Smart Sync."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check that step execution is streamlined
                assert 'def run_step' in content, "run_step method should be preserved"
                # But should not have Smart Sync delays
                sync_delays = [
                    'Pre-step sync',
                    'Post-step sync',
                    'Syncing latest changes',
                    'Saving results to network'
                ]
                for delay in sync_delays:
                    assert delay not in content, f"Smart Sync delay '{delay}' should be removed from core.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])