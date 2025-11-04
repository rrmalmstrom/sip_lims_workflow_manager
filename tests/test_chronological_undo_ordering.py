import pytest
import tempfile
import shutil
from pathlib import Path
from src.core import Project
from src.logic import StateManager

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

class TestChronologicalUndoOrdering:
    """Test chronological undo ordering for cyclical workflows."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create workflow.yml with cyclical steps (16 -> 17 -> 16 -> 17)
        workflow_content = """
workflow_name: "Cyclical Workflow Test"
steps:
  - id: "step_16"
    name: "Step 16 - Pool FA Analysis"
    script: "dummy_script.py"
    allow_rerun: true
  - id: "step_17"
    name: "Step 17 - Rework Pooling"
    script: "dummy_script.py"
    allow_rerun: true
"""
        
        workflow_file = temp_dir / "workflow.yml"
        with open(workflow_file, 'w') as f:
            f.write(workflow_content)
        
        # Create scripts directory and dummy script
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        dummy_script = scripts_dir / "dummy_script.py"
        with open(dummy_script, 'w') as f:
            f.write('print("Dummy script executed")\n')
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def simulate_step_completion(self, project, step_id, run_number=None):
        """Simulate step completion by updating state, creating snapshots, and success marker."""
        # Get the next run number if not specified
        if run_number is None:
            step = project.workflow.get_step_by_id(step_id)
            allow_rerun = step.get('allow_rerun', False)
            run_number = project.snapshot_manager.get_next_run_number(step_id, allow_rerun)
        
        # Create a "before" snapshot (simulating what happens before step runs)
        project.snapshot_manager.take_complete_snapshot(f"{step_id}_run_{run_number}")
        
        # Update state to completed
        project.update_state(step_id, "completed")
        
        # Create success marker
        status_dir = project.path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        success_file = status_dir / "dummy_script.success"
        success_file.touch()

    def test_chronological_completion_order_tracking(self, temp_project):
        """Test that completion order is tracked chronologically."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Initially no completions
        assert project.state_manager.get_completion_order() == []
        assert project.state_manager.get_last_completed_step_chronological() is None
        
        # Complete step 16
        self.simulate_step_completion(project, "step_16")
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16"]
        assert project.state_manager.get_last_completed_step_chronological() == "step_16"
        
        # Complete step 17
        self.simulate_step_completion(project, "step_17")
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_17"]
        assert project.state_manager.get_last_completed_step_chronological() == "step_17"
        
        # Complete step 16 again (cyclical)
        self.simulate_step_completion(project, "step_16")
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_17", "step_16"]
        assert project.state_manager.get_last_completed_step_chronological() == "step_16"

    def test_chronological_undo_ordering_cyclical_workflow(self, temp_project):
        """Test that undo follows chronological order in cyclical workflows."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Simulate the problematic scenario: 16 -> 17 -> 16 -> 17
        self.simulate_step_completion(project, "step_16")  # First completion
        self.simulate_step_completion(project, "step_17")  # Second completion
        self.simulate_step_completion(project, "step_16")  # Third completion (cyclical)
        self.simulate_step_completion(project, "step_17")  # Fourth completion (cyclical)
        
        # Verify completion order
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_17", "step_16", "step_17"]
        
        # Test chronological undo - should undo step_17 (most recent)
        # First undo should target step_17 (most recent completion)
        last_step = project.state_manager.get_last_completed_step_chronological()
        assert last_step == "step_17"
        
        result = perform_undo_test(project)
        assert result is True
        
        # After granular undo, step_17 should remain completed (run 1 still exists)
        assert project.get_state("step_17") == "completed"  # Still completed due to granular undo
        assert project.get_state("step_16") == "completed"  # Still completed
        
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_17", "step_16"]  # Last step_17 removed
        
        # Second undo should target step_16 (now most recent)
        last_step = project.state_manager.get_last_completed_step_chronological()
        assert last_step == "step_16"
        
        result = perform_undo_test(project)
        assert result is True
        
        # After second granular undo, step_16 should still be completed (first completion remains)
        assert project.get_state("step_16") == "completed"  # Still completed due to granular undo
        assert project.get_state("step_17") == "completed"  # Still completed
        
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_17"]  # Second step_16 removed

    def test_completion_order_persistence(self, temp_project):
        """Test that completion order persists across project reloads."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Complete steps in order
        self.simulate_step_completion(project, "step_16")
        self.simulate_step_completion(project, "step_17")
        self.simulate_step_completion(project, "step_16")
        
        # Verify completion order
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_17", "step_16"]
        
        # Reload project
        project2 = Project(temp_project, script_path=temp_project / "scripts")
        
        # Verify completion order persists
        completion_order2 = project2.state_manager.get_completion_order()
        assert completion_order2 == ["step_16", "step_17", "step_16"]
        assert project2.state_manager.get_last_completed_step_chronological() == "step_16"

    def test_backward_compatibility_no_completion_order(self, temp_project):
        """Test that projects without completion order still work."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Manually create old-style state file without completion order
        state_data = {
            "step_16": "completed",
            "step_17": "completed"
        }
        project.state_manager.save(state_data)
        
        # Should handle missing completion order gracefully
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == []  # Empty list for backward compatibility
        
        last_step = project.state_manager.get_last_completed_step_chronological()
        assert last_step is None  # No chronological info available
        
        # Undo should fail gracefully
        result = perform_undo_test(project)
        assert result is False  # Nothing to undo without chronological info

    def test_completion_order_with_mixed_states(self, temp_project):
        """Test completion order with various step states."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Complete step 16
        self.simulate_step_completion(project, "step_16")
        
        # Mark step 17 as skipped (not completed)
        project.update_state("step_17", "skipped")
        
        # Complete step 16 again
        self.simulate_step_completion(project, "step_16")
        
        # Only completed steps should be in completion order
        completion_order = project.state_manager.get_completion_order()
        assert completion_order == ["step_16", "step_16"]
        assert project.state_manager.get_last_completed_step_chronological() == "step_16"
        
        # Verify states
        assert project.get_state("step_16") == "completed"
        assert project.get_state("step_17") == "skipped"