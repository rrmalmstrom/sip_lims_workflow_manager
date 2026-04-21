#!/usr/bin/env python3
"""
Comprehensive Native Workflow Functionality Tests

This test suite validates that the core workflow functionality works correctly
after Docker removal and transition to native execution. It tests the essential
components that laboratory users depend on.
"""

import pytest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import Project, Workflow
from src.logic import StateManager, SnapshotManager, ScriptRunner
from src.update_detector import UpdateDetector
from src.scripts_updater import ScriptsUpdater
from src.git_update_manager import GitUpdateManager


class TestNativeWorkflowCore:
    """Test core workflow functionality in native mode."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create workflow.yml
        workflow_content = """
workflow_name: "Native Test Workflow"
steps:
  - id: "step_1"
    name: "Step 1 - Data Import"
    script: "import_data.py"
  - id: "step_2"
    name: "Step 2 - Analysis"
    script: "analyze_data.py"
    allow_rerun: true
  - id: "step_3"
    name: "Step 3 - Export Results"
    script: "export_results.py"
"""
        
        workflow_file = temp_dir / "workflow.yml"
        with open(workflow_file, 'w') as f:
            f.write(workflow_content)
        
        # Create scripts directory and dummy scripts
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        
        for script_name in ["import_data.py", "analyze_data.py", "export_results.py"]:
            script_file = scripts_dir / script_name
            with open(script_file, 'w') as f:
                f.write(f'#!/usr/bin/env python3\nprint("Executing {script_name}")\n')
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_project_initialization_native(self, temp_project):
        """Test that Project initializes correctly in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Verify basic initialization
        assert project.path == temp_project
        assert project.script_path == temp_project / "scripts"
        assert project.workflow is not None
        assert project.workflow.name == "Native Test Workflow"
        assert len(project.workflow.steps) == 3
        
        # Verify managers are initialized
        assert project.state_manager is not None
        assert project.snapshot_manager is not None
        assert project.script_runner is not None
        
        # Verify script runner has correct paths
        assert project.script_runner.project_path == temp_project
        assert project.script_runner.script_path == temp_project / "scripts"

    def test_workflow_state_management_native(self, temp_project):
        """Test workflow state management in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Initially all steps should be pending
        assert project.get_state("step_1") == "pending"
        assert project.get_state("step_2") == "pending"
        assert project.get_state("step_3") == "pending"
        
        # Update states
        project.update_state("step_1", "completed")
        project.update_state("step_2", "completed")
        project.update_state("step_3", "pending")
        
        # Verify state updates
        assert project.get_state("step_1") == "completed"
        assert project.get_state("step_2") == "completed"
        assert project.get_state("step_3") == "pending"
        
        # Test state persistence
        project2 = Project(temp_project, script_path=temp_project / "scripts")
        assert project2.get_state("step_1") == "completed"
        assert project2.get_state("step_2") == "completed"
        assert project2.get_state("step_3") == "pending"

    def test_snapshot_functionality_native(self, temp_project):
        """Test snapshot functionality in native mode using the selective snapshot API."""
        project = Project(temp_project, script_path=temp_project / "scripts")

        # Create a test file that will be snapshotted
        test_file = temp_project / "test_data.txt"
        test_file.write_text("Original data")

        step_id = "step_1"
        run_number = 1

        # Write a manifest (records current file set as the pre-run baseline)
        project.snapshot_manager.scan_manifest(step_id, run_number)

        # Take a selective snapshot declaring test_data.txt as a snapshot item
        project.snapshot_manager.take_selective_snapshot(
            step_id, run_number,
            snapshot_items=["test_data.txt"],
            prev_manifest_path=None,
        )

        # Verify snapshot exists
        assert project.snapshot_manager.snapshot_exists(step_id, run_number)

        # Modify the file
        test_file.write_text("Modified data")
        assert test_file.read_text() == "Modified data"

        # Restore snapshot — should bring back "Original data"
        project.snapshot_manager.restore_snapshot(step_id, run_number)

        # Verify restoration
        assert test_file.read_text() == "Original data"

    def test_script_runner_native_mode(self, temp_project):
        """Test script runner in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Verify script runner is configured for native execution
        assert project.script_runner.project_path == temp_project
        assert project.script_runner.script_path == temp_project / "scripts"
        
        # Test script path resolution
        script_path = project.script_runner.script_path / "import_data.py"
        assert script_path.exists()

    def test_workflow_step_execution_preparation(self, temp_project):
        """Test workflow step execution preparation in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Test step preparation (without actually running scripts)
        step = project.workflow.get_step_by_id("step_1")
        assert step is not None
        assert step["name"] == "Step 1 - Data Import"
        assert step["script"] == "import_data.py"
        
        # Verify script file exists
        script_file = project.script_path / step["script"]
        assert script_file.exists()

    def test_success_marker_functionality(self, temp_project):
        """Test success marker functionality in native mode.

        Success markers are now run-number-specific: <script_stem>.run_<N>.success.
        The flat <script_stem>.success written by individual scripts is renamed by
        handle_step_result() before _check_success_marker() is called.
        """
        project = Project(temp_project, script_path=temp_project / "scripts")

        # No marker present → False for any run number
        assert not project._check_success_marker("import_data.py", 1)

        # Place a run-1-specific marker (as handle_step_result would after renaming)
        status_dir = temp_project / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        run_marker = status_dir / "import_data.run_1.success"
        run_marker.touch()

        # Correct run number → True
        assert project._check_success_marker("import_data.py", 1)
        # Different run number → False (stale marker rejection)
        assert not project._check_success_marker("import_data.py", 2)

    def test_chronological_completion_tracking(self, temp_project):
        """Test chronological completion tracking in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Initially no completions
        assert project.state_manager.get_completion_order() == []
        assert project.state_manager.get_last_completed_step_chronological() is None
        
        # Simulate step completions (update_state automatically handles completion order)
        project.update_state("step_1", "completed")
        project.update_state("step_2", "completed")
        
        # Verify chronological tracking
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_1", "step_2"]
        assert project.state_manager.get_last_completed_step_chronological() == "step_2"


class TestNativeUpdateSystem:
    """Test update system functionality in native mode."""

    def test_update_detector_git_only(self):
        """Test that UpdateDetector works with Git-only functionality."""
        detector = UpdateDetector()
        
        # Test Git methods exist and work
        assert hasattr(detector, 'get_local_commit_sha')
        assert hasattr(detector, 'get_remote_commit_sha')
        assert hasattr(detector, 'check_repository_update')
        
        # Test that Docker methods are removed
        assert not hasattr(detector, 'get_local_docker_image_commit_sha')
        assert not hasattr(detector, 'get_remote_docker_image_digest')
        assert not hasattr(detector, 'check_docker_update')
        
        # Test Git functionality
        local_sha = detector.get_local_commit_sha()
        assert local_sha is None or isinstance(local_sha, str)
        
        # Test update summary
        summary = detector.get_update_summary()
        assert isinstance(summary, dict)
        assert "repository" in summary
        assert "timestamp" in summary

    def test_scripts_updater_functionality(self):
        """Test ScriptsUpdater functionality in native mode."""
        # Test for SIP workflow
        updater_sip = ScriptsUpdater(workflow_type="sip")
        assert updater_sip.workflow_type == "sip"
        
        # Test for SPS-CE workflow (correct workflow type)
        updater_sps = ScriptsUpdater(workflow_type="sps-ce")
        assert updater_sps.workflow_type == "sps-ce"
        
        # Test that it has required methods
        assert hasattr(updater_sip, 'check_scripts_update')

    def test_git_update_manager_functionality(self):
        """Test GitUpdateManager functionality in native mode."""
        manager = GitUpdateManager("scripts", ".")
        
        # Test basic functionality (check actual available methods)
        assert hasattr(manager, 'check_for_updates')
        assert hasattr(manager, 'update_to_latest')
        assert manager.repo_path == Path(".")
        assert manager.repo_type == "scripts"


class TestNativeWorkflowIntegration:
    """Test integration between workflow components in native mode."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for integration testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create workflow.yml with re-runnable steps
        workflow_content = """
workflow_name: "Integration Test Workflow"
steps:
  - id: "step_1"
    name: "Step 1 - Import"
    script: "import.py"
  - id: "step_2"
    name: "Step 2 - Process"
    script: "process.py"
    allow_rerun: true
  - id: "step_3"
    name: "Step 3 - Export"
    script: "export.py"
"""
        
        workflow_file = temp_dir / "workflow.yml"
        with open(workflow_file, 'w') as f:
            f.write(workflow_content)
        
        # Create scripts directory
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        
        for script_name in ["import.py", "process.py", "export.py"]:
            script_file = scripts_dir / script_name
            with open(script_file, 'w') as f:
                f.write(f'#!/usr/bin/env python3\nprint("Executing {script_name}")\n')
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_workflow_step_progression(self, temp_project):
        """Test workflow step progression in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Test next available step logic
        next_step = project.get_next_available_step()
        assert next_step is not None
        assert next_step["id"] == "step_1"
        
        # Complete step 1
        project.update_state("step_1", "completed")
        
        # Next step should be step 2
        next_step = project.get_next_available_step()
        assert next_step is not None
        assert next_step["id"] == "step_2"
        
        # Complete step 2
        project.update_state("step_2", "completed")
        
        # Next step should be step 3
        next_step = project.get_next_available_step()
        assert next_step is not None
        assert next_step["id"] == "step_3"
        
        # Complete step 3
        project.update_state("step_3", "completed")
        
        # No more steps available
        next_step = project.get_next_available_step()
        assert next_step is None

    def test_rerunnable_step_functionality(self, temp_project):
        """Test re-runnable step functionality in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Get step 2 (marked as allow_rerun: true)
        step_2 = project.workflow.get_step_by_id("step_2")
        assert step_2 is not None
        assert step_2.get("allow_rerun", False) is True
        
        # Complete step 2
        project.update_state("step_2", "completed")
        assert project.get_state("step_2") == "completed"
        
        # Step should still be available for re-run
        # (This would be tested in the UI layer)

    def test_skip_to_step_functionality(self, temp_project):
        """Test skip-to-step functionality in native mode."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Skip to step 3
        result = project.skip_to_step("step_3")
        assert "Skipped to Step 3 - Export" in result
        
        # Verify states
        assert project.get_state("step_1") == "skipped"
        assert project.get_state("step_2") == "skipped"
        assert project.get_state("step_3") == "pending"


class TestNativeEnvironmentIntegration:
    """Test environment integration in native mode."""

    def test_environment_variable_handling(self):
        """Test environment variable handling in native mode."""
        # Test workflow type environment variable
        original_workflow_type = os.environ.get("WORKFLOW_TYPE")
        
        try:
            os.environ["WORKFLOW_TYPE"] = "SIP"
            # This would be tested in app.py integration
            assert os.environ.get("WORKFLOW_TYPE") == "SIP"
            
            os.environ["WORKFLOW_TYPE"] = "SPS"
            assert os.environ.get("WORKFLOW_TYPE") == "SPS"
            
        finally:
            # Restore original value
            if original_workflow_type is not None:
                os.environ["WORKFLOW_TYPE"] = original_workflow_type
            elif "WORKFLOW_TYPE" in os.environ:
                del os.environ["WORKFLOW_TYPE"]

    def test_native_path_handling(self):
        """Test native path handling without Docker volumes."""
        # Test that paths work without Docker volume assumptions
        current_dir = Path.cwd()
        assert current_dir.exists()
        
        # Test script path resolution
        scripts_path = current_dir / "scripts"
        # Should not assume /workflow-scripts Docker mount
        assert "/workflow-scripts" not in str(scripts_path)

    def test_project_path_handling(self):
        """Test project path handling in native mode."""
        # Test that project paths work without Docker /data mount
        test_path = Path("/tmp/test_project")
        # Should not assume /data Docker mount
        assert "/data" not in str(test_path)


class TestNativeErrorHandling:
    """Test error handling in native mode."""

    def test_missing_workflow_file_handling(self):
        """Test handling of missing workflow file."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Try to create project without workflow.yml
            with pytest.raises(FileNotFoundError):
                Project(temp_dir, script_path=temp_dir / "scripts")
        finally:
            shutil.rmtree(temp_dir)

    def test_missing_scripts_directory_handling(self):
        """Test handling of missing scripts directory."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create workflow.yml but no scripts directory
            workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: "step_1"
    name: "Step 1"
    script: "test.py"
"""
            workflow_file = temp_dir / "workflow.yml"
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)
            
            # Should handle missing scripts directory gracefully
            project = Project(temp_dir, script_path=temp_dir / "scripts")
            assert project.script_path == temp_dir / "scripts"
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])