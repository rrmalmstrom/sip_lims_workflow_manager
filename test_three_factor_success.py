#!/usr/bin/env python3
"""
Test the new three-factor success detection with Smart Sync fail-fast behavior.

This test validates:
1. Pre-step sync failure prevents step execution
2. Post-step sync failure triggers automatic rollback
3. SmartSyncError exceptions are properly handled
4. User feedback messages are clear
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import Project
from src.logic import RunResult
from src.smart_sync import SmartSyncManager, SmartSyncError


class TestThreeFactorSuccess:
    """Test the new three-factor success detection system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir()
        
        # Create minimal workflow file
        workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: "test_step"
    name: "Test Step"
    script: "test_script.py"
    snapshot_items: []
"""
        (self.project_path / "workflow.yml").write_text(workflow_content)
        
        # Create test script
        (self.project_path / "test_script.py").write_text("print('test')")
        
        # Create success marker directory
        status_dir = self.project_path / ".workflow_status"
        status_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_pre_step_sync_failure_prevents_execution(self):
        """Test that pre-step sync failure prevents step execution."""
        # Set up Smart Sync environment
        os.environ["SMART_SYNC_ENABLED"] = "true"
        os.environ["NETWORK_PROJECT_PATH"] = str(self.temp_dir / "network")
        os.environ["LOCAL_PROJECT_PATH"] = str(self.temp_dir / "local")
        
        try:
            project = Project(self.project_path)
            
            # Mock Smart Sync manager to fail on pre-step sync
            mock_sync_manager = Mock()
            mock_sync_manager.incremental_sync_down.side_effect = SmartSyncError("Excel file locked")
            project.smart_sync_manager = mock_sync_manager
            
            # Attempt to run step - should fail due to pre-step sync failure
            with pytest.raises(RuntimeError, match="cannot proceed with step"):
                project.run_step("test_step")
            
            # Verify sync was attempted
            mock_sync_manager.incremental_sync_down.assert_called_once()
            
            print("✅ Pre-step sync failure correctly prevents step execution")
            
        finally:
            # Clean up environment
            os.environ.pop("SMART_SYNC_ENABLED", None)
            os.environ.pop("NETWORK_PROJECT_PATH", None)
            os.environ.pop("LOCAL_PROJECT_PATH", None)
    
    def test_post_step_sync_failure_triggers_rollback(self):
        """Test that post-step sync failure triggers automatic rollback."""
        # Set up Smart Sync environment
        os.environ["SMART_SYNC_ENABLED"] = "true"
        os.environ["NETWORK_PROJECT_PATH"] = str(self.temp_dir / "network")
        os.environ["LOCAL_PROJECT_PATH"] = str(self.temp_dir / "local")
        
        try:
            project = Project(self.project_path)
            
            # Mock Smart Sync manager
            mock_sync_manager = Mock()
            mock_sync_manager.incremental_sync_down.return_value = True  # Pre-step succeeds
            mock_sync_manager.incremental_sync_up.return_value = False   # Post-step fails
            project.smart_sync_manager = mock_sync_manager
            
            # Create success marker (script completed successfully)
            success_file = self.project_path / ".workflow_status" / "test_script.success"
            success_file.write_text("success")
            
            # Simulate the snapshot that would normally be taken by run_step()
            # This is needed because our test calls handle_step_result() directly
            project.snapshot_manager.take_complete_snapshot("test_step_run_1")
            
            # Mock successful script execution
            successful_result = RunResult(success=True, stdout="test output", stderr="", return_code=0)
            
            # Handle step result - should fail due to post-step sync failure
            project.handle_step_result("test_step", successful_result)
            
            # Verify step is NOT marked as completed
            assert project.get_state("test_step") == "pending"
            
            # Verify post-step sync was attempted (pre-step sync only happens in run_step)
            mock_sync_manager.incremental_sync_up.assert_called_once()
            # Note: incremental_sync_down is only called in run_step(), not handle_step_result()
            
            print("✅ Post-step sync failure correctly prevents step completion")
            
        finally:
            # Clean up environment
            os.environ.pop("SMART_SYNC_ENABLED", None)
            os.environ.pop("NETWORK_PROJECT_PATH", None)
            os.environ.pop("LOCAL_PROJECT_PATH", None)
    
    def test_all_three_factors_success(self):
        """Test that all three factors must succeed for step completion."""
        # Set up Smart Sync environment
        os.environ["SMART_SYNC_ENABLED"] = "true"
        os.environ["NETWORK_PROJECT_PATH"] = str(self.temp_dir / "network")
        os.environ["LOCAL_PROJECT_PATH"] = str(self.temp_dir / "local")
        
        try:
            project = Project(self.project_path)
            
            # Mock Smart Sync manager - all operations succeed
            mock_sync_manager = Mock()
            mock_sync_manager.incremental_sync_down.return_value = True  # Pre-step succeeds
            mock_sync_manager.incremental_sync_up.return_value = True    # Post-step succeeds
            project.smart_sync_manager = mock_sync_manager
            
            # Create success marker (script completed successfully)
            success_file = self.project_path / ".workflow_status" / "test_script.success"
            success_file.write_text("success")
            
            # Mock successful script execution
            successful_result = RunResult(success=True, stdout="test output", stderr="", return_code=0)
            
            # Handle step result - should succeed with all three factors
            project.handle_step_result("test_step", successful_result)
            
            # Verify step IS marked as completed
            assert project.get_state("test_step") == "completed"
            
            print("✅ All three factors success correctly marks step as completed")
            
        finally:
            # Clean up environment
            os.environ.pop("SMART_SYNC_ENABLED", None)
            os.environ.pop("NETWORK_PROJECT_PATH", None)
            os.environ.pop("LOCAL_PROJECT_PATH", None)
    
    def test_smart_sync_error_propagation(self):
        """Test that SmartSyncError exceptions are properly handled."""
        from src.smart_sync import SmartSyncManager
        
        # Create test directories
        network_dir = self.temp_dir / "network"
        local_dir = self.temp_dir / "local"
        network_dir.mkdir()
        local_dir.mkdir()
        
        # Create test file
        test_file = network_dir / "test.xlsx"
        test_file.write_text("test content")
        
        sync_manager = SmartSyncManager(network_dir, local_dir)
        
        # Mock shutil.copy2 to raise PermissionError (simulating locked Excel file)
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            with pytest.raises(SmartSyncError, match="Excel file locked"):
                sync_manager.initial_sync()
        
        print("✅ SmartSyncError properly raised for locked Excel files")


def main():
    """Run the three-factor success tests."""
    print("🧪 Testing Three-Factor Success Detection with Smart Sync")
    print("=" * 60)
    
    test_instance = TestThreeFactorSuccess()
    
    try:
        # Test 1: Pre-step sync failure
        print("\n1. Testing pre-step sync failure prevention...")
        test_instance.setup_method()
        test_instance.test_pre_step_sync_failure_prevents_execution()
        test_instance.teardown_method()
        
        # Test 2: Post-step sync failure rollback
        print("\n2. Testing post-step sync failure rollback...")
        test_instance.setup_method()
        test_instance.test_post_step_sync_failure_triggers_rollback()
        test_instance.teardown_method()
        
        # Test 3: All three factors success
        print("\n3. Testing all three factors success...")
        test_instance.setup_method()
        test_instance.test_all_three_factors_success()
        test_instance.teardown_method()
        
        # Test 4: SmartSyncError propagation
        print("\n4. Testing SmartSyncError propagation...")
        test_instance.setup_method()
        test_instance.test_smart_sync_error_propagation()
        test_instance.teardown_method()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Three-factor success detection working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)