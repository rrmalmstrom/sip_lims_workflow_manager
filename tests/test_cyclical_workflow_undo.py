"""
Test cyclical workflow undo functionality for steps 16-17.

This test simulates the cyclical workflow pattern where steps 16 and 17
can be run multiple times in sequence, and tests that the undo functionality
works correctly with the simplified undo system.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
from src.core import Project
from src.logic import RunResult

def perform_undo_test(project):
    """
    Test version of perform_undo without Streamlit dependencies.
    Simplified undo operation using only "before" snapshots.
    Reverts to the state before the last completed step ran.
    Uses chronological completion order for proper cyclical workflow support.
    """
    # Get the most recently completed step using chronological order
    last_step_id = project.state_manager.get_last_completed_step_chronological()
    
    if not last_step_id:
        return False  # Nothing to undo
    
    # Get the step object
    last_step = project.workflow.get_step_by_id(last_step_id)
    if not last_step:
        print(f"UNDO ERROR: Step {last_step_id} not found in workflow")
        return False
    
    try:
        # Get the effective current run number
        effective_run = project.snapshot_manager.get_effective_run_number(last_step_id)
        print(f"DEBUG UNDO: Step {last_step_id}, effective_run={effective_run}")
        
        if effective_run > 1:
            # Granular undo - restore to before the most recent run
            before_snapshot = f"{last_step_id}_run_{effective_run}"
            print(f"DEBUG UNDO: Checking for granular snapshot: {before_snapshot}")
            if project.snapshot_manager.snapshot_exists(before_snapshot):
                project.snapshot_manager.restore_complete_snapshot(before_snapshot)
                # Remove the most recent run snapshot
                project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
                print(f"UNDO: Restored to before run {effective_run} of step {last_step_id}")
                # Step remains "completed" since previous runs still exist
                return True
        
        if effective_run >= 1:
            # Full step undo - restore to before the step ever ran
            before_snapshot = f"{last_step_id}_run_1"
            print(f"DEBUG UNDO: Checking for first run snapshot: {before_snapshot}")
            if project.snapshot_manager.snapshot_exists(before_snapshot):
                project.snapshot_manager.restore_complete_snapshot(before_snapshot)
            else:
                # Fallback to legacy snapshot naming
                print(f"DEBUG UNDO: Falling back to legacy snapshot: {last_step_id}")
                project.snapshot_manager.restore_complete_snapshot(last_step_id)
            
            # Remove all run snapshots and mark step as pending
            project.snapshot_manager.remove_all_run_snapshots(last_step_id)
            
            # Remove success marker
            script_name = last_step.get('script', '').replace('.py', '')
            success_marker = project.path / ".workflow_status" / f"{script_name}.success"
            if success_marker.exists():
                success_marker.unlink()
                print(f"UNDO: Removed success marker for {script_name}")
            
            project.update_state(last_step_id, "pending")
            print(f"UNDO: Restored to before step {last_step_id} ran - marked as pending")
            return True
        
        # No snapshots exist - fallback to legacy behavior
        print(f"DEBUG UNDO: No effective runs, trying legacy snapshot: {last_step_id}")
        project.snapshot_manager.restore_complete_snapshot(last_step_id)
        print(f"UNDO: Restored using legacy snapshot for step {last_step_id}")
        return True
        
    except FileNotFoundError as e:
        print(f"UNDO ERROR: {e}")
        print("Snapshot not found for undo operation.")
        return False
    except Exception as e:
        print(f"UNDO ERROR: Unexpected error during undo: {e}")
        return False


class TestCyclicalWorkflowUndo:
    """Test undo functionality for cyclical workflow steps 16-17."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create a minimal workflow.yml with steps 15-17
        workflow_content = """
workflow_name: "Test Cyclical Workflow"
steps:
  - id: setup_step
    name: "Setup Step"
    script: "setup.py"
    snapshot_items: ["test_file.txt"]
    
  - id: run_pooling_preparation
    name: "15. Run Pooling Preparation"
    script: "run.pooling.preparation.py"
    snapshot_items: ["outputs/pooling_prep.txt"]
    allow_rerun: true
    
  - id: pool_fa12_analysis
    name: "16. Analyze Pool QC Results"
    script: "pool.FA12.analysis.py"
    snapshot_items: ["outputs/pool_summary.csv"]
    allow_rerun: true
    
  - id: rework_pooling
    name: "17. Rework Pools & Finalize"
    script: "rework.pooling.steps.py"
    snapshot_items: ["outputs/"]
    allow_rerun: true
"""
        
        workflow_file = temp_dir / "workflow.yml"
        workflow_file.write_text(workflow_content)
        
        # Create initial project state
        state_file = temp_dir / "workflow_state.json"
        initial_state = {
            "setup_step": "completed",
            "run_pooling_preparation": "pending",
            "pool_fa12_analysis": "pending",
            "rework_pooling": "pending"
        }
        state_file.write_text(json.dumps(initial_state, indent=2))
        
        # Create test files
        (temp_dir / "test_file.txt").write_text("initial content")
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "pool_summary.csv").write_text("initial,data")
        
        # Create .workflow_status directory for success markers
        status_dir = temp_dir / ".workflow_status"
        status_dir.mkdir()
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def create_success_marker(self, project_path: Path, script_name: str):
        """Create a success marker for a script."""
        status_dir = project_path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        script_filename = Path(script_name).stem
        success_file = status_dir / f"{script_filename}.success"
        success_file.write_text("success")
    
    def simulate_step_completion(self, project: Project, step_id: str, run_number: int = 1):
        """Simulate a step completion with proper snapshots and state updates."""
        # Take a "before" snapshot (simulating what run_step does)
        project.snapshot_manager.take_complete_snapshot(f"{step_id}_run_{run_number}")
        
        # Simulate script execution result
        step = project.workflow.get_step_by_id(step_id)
        script_name = step.get('script', '')
        
        # Create success marker
        self.create_success_marker(project.path, script_name)
        
        # Handle the successful result
        result = RunResult(success=True, stdout="", stderr="", return_code=0)
        project.handle_step_result(step_id, result)
        
        # Modify some files to simulate script changes
        if step_id == "pool_fa12_analysis":
            outputs_dir = project.path / "outputs"
            outputs_dir.mkdir(exist_ok=True)
            (outputs_dir / "pool_summary.csv").write_text(f"analysis,run_{run_number}")
        elif step_id == "rework_pooling":
            outputs_dir = project.path / "outputs"
            outputs_dir.mkdir(exist_ok=True)
            (outputs_dir / "rework_results.txt").write_text(f"rework,run_{run_number}")
        elif step_id == "run_pooling_preparation":
            outputs_dir = project.path / "outputs"
            outputs_dir.mkdir(exist_ok=True)
            (outputs_dir / "pooling_prep.txt").write_text(f"prep,run_{run_number}")
    
    def test_cyclical_workflow_single_cycle(self, temp_project):
        """Test a single cycle of steps 16-17 with undo."""
        project = Project(temp_project, script_path=Path("scripts"))
        
        # Initial state: setup completed, steps 16-17 pending
        assert project.get_state("setup_step") == "completed"
        assert project.get_state("pool_fa12_analysis") == "pending"
        assert project.get_state("rework_pooling") == "pending"
        
        # Run step 16 (first time)
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=1)
        assert project.get_state("pool_fa12_analysis") == "completed"
        
        # Verify snapshot was created
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_1")
        assert project.snapshot_manager.get_effective_run_number("pool_fa12_analysis") == 1
        
        # Run step 17 (first time)
        self.simulate_step_completion(project, "rework_pooling", run_number=1)
        assert project.get_state("rework_pooling") == "completed"
        
        # Verify snapshot was created
        assert project.snapshot_manager.snapshot_exists("rework_pooling_run_1")
        assert project.snapshot_manager.get_effective_run_number("rework_pooling") == 1
        
        # Test undo step 17
        result = perform_undo_test(project)
        assert result is True
        
        # After undo, step 17 should be pending, step 16 should remain completed
        assert project.get_state("rework_pooling") == "pending"
        assert project.get_state("pool_fa12_analysis") == "completed"
        
        # Test undo step 16
        result = perform_undo_test(project)
        assert result is True
        
        # After undo, step 16 should be pending
        assert project.get_state("pool_fa12_analysis") == "pending"
        assert project.get_state("rework_pooling") == "pending"
    
    def test_cyclical_workflow_multiple_cycles(self, temp_project):
        """Test multiple cycles of steps 16-17 with undo."""
        project = Project(temp_project, script_path=Path("scripts"))
        
        # Complete the first cycle
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=1)
        self.simulate_step_completion(project, "rework_pooling", run_number=1)
        
        # Start second cycle - re-run step 16
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=2)
        
        # Verify we have 2 runs of step 16
        assert project.snapshot_manager.get_effective_run_number("pool_fa12_analysis") == 2
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_1")
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_2")
        
        # Re-run step 17
        self.simulate_step_completion(project, "rework_pooling", run_number=2)
        
        # Verify we have 2 runs of step 17
        assert project.snapshot_manager.get_effective_run_number("rework_pooling") == 2
        assert project.snapshot_manager.snapshot_exists("rework_pooling_run_1")
        assert project.snapshot_manager.snapshot_exists("rework_pooling_run_2")
        
        # Test granular undo - should undo step 17 run 2, but keep it completed
        result = perform_undo_test(project)
        assert result is True
        
        # Step 17 should remain completed (because run 1 still exists)
        assert project.get_state("rework_pooling") == "completed"
        assert project.snapshot_manager.get_effective_run_number("rework_pooling") == 1
        
        # Undo again - should undo step 16 run 2
        result = perform_undo_test(project)
        assert result is True
        
        # Step 16 should remain completed (because run 1 still exists)
        assert project.get_state("pool_fa12_analysis") == "completed"
        assert project.snapshot_manager.get_effective_run_number("pool_fa12_analysis") == 1
        
        # Undo again - should undo step 17 run 1
        result = perform_undo_test(project)
        assert result is True
        
        # Step 17 should now be pending (no more runs)
        assert project.get_state("rework_pooling") == "pending"
        assert project.snapshot_manager.get_effective_run_number("rework_pooling") == 0
        
        # Undo again - should undo step 16 run 1
        result = perform_undo_test(project)
        assert result is True
        
        # Step 16 should now be pending (no more runs)
        assert project.get_state("pool_fa12_analysis") == "pending"
        assert project.snapshot_manager.get_effective_run_number("pool_fa12_analysis") == 0
    
    def test_cyclical_workflow_with_filename_bug_fix(self, temp_project):
        """Test that the regex fix handles step IDs with 'run' in the name correctly."""
        project = Project(temp_project, script_path=Path("scripts"))
        
        # Test specifically with run_pooling_preparation (step 15) which has 'run' in the name
        # Add this step to our test workflow state
        project.update_state("run_pooling_preparation", "completed")
        
        # Simulate completion of run_pooling_preparation
        self.simulate_step_completion(project, "run_pooling_preparation", run_number=1)
        
        # Verify the snapshot was created with correct naming
        assert project.snapshot_manager.snapshot_exists("run_pooling_preparation_run_1")
        
        # Test that get_effective_run_number works correctly with the regex fix
        effective_run = project.snapshot_manager.get_effective_run_number("run_pooling_preparation")
        assert effective_run == 1
        
        # Test re-run
        self.simulate_step_completion(project, "run_pooling_preparation", run_number=2)
        effective_run = project.snapshot_manager.get_effective_run_number("run_pooling_preparation")
        assert effective_run == 2
        
        # Test undo with the regex fix
        result = perform_undo_test(project)
        assert result is True
        
        # Should remain completed due to granular undo
        assert project.get_state("run_pooling_preparation") == "completed"
        effective_run = project.snapshot_manager.get_effective_run_number("run_pooling_preparation")
        assert effective_run == 1
    
    def test_cyclical_workflow_edge_cases(self, temp_project):
        """Test edge cases in cyclical workflow undo."""
        project = Project(temp_project, script_path=Path("scripts"))
        
        # Test undo with no completed steps
        result = perform_undo_test(project)
        assert result is False  # Nothing to undo
        
        # Complete one step and test undo
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=1)
        
        # Test undo with only one completed step
        result = perform_undo_test(project)
        assert result is True
        assert project.get_state("pool_fa12_analysis") == "pending"
        
        # Test undo again (should fail - nothing to undo)
        result = perform_undo_test(project)
        assert result is False
    
    def test_snapshot_cleanup_during_undo(self, temp_project):
        """Test that snapshots are properly cleaned up during undo operations."""
        project = Project(temp_project, script_path=Path("scripts"))
        
        # Create multiple runs
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=1)
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=2)
        self.simulate_step_completion(project, "pool_fa12_analysis", run_number=3)
        
        # Verify all snapshots exist
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_1")
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_2")
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_3")
        
        # Undo run 3
        result = perform_undo_test(project)
        assert result is True
        
        # Run 3 snapshot should be removed, others should remain
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_1")
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_2")
        assert not project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_3")
        
        # Undo run 2
        result = perform_undo_test(project)
        assert result is True
        
        # Run 2 snapshot should be removed
        assert project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_1")
        assert not project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_2")
        
        # Undo run 1 (should mark step as pending and remove all snapshots)
        result = perform_undo_test(project)
        assert result is True
        
        # All snapshots should be removed, step should be pending
        assert not project.snapshot_manager.snapshot_exists("pool_fa12_analysis_run_1")
        assert project.get_state("pool_fa12_analysis") == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])