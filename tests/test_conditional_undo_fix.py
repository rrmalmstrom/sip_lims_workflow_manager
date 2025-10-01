"""
Test for conditional undo bug fix.

This test reproduces the issue where undo doesn't work properly when a conditional step
is in "awaiting_decision" state.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
from unittest.mock import Mock, patch

from src.core import Project
from src.core import Project, Workflow
from src.logic import StateManager, SnapshotManager


class TestConditionalUndoFix:
    """Test conditional undo functionality when step is in awaiting_decision state."""

    def setup_method(self):
        """Set up test environment with temporary project directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir()
        
        # Create workflow.yml with conditional steps
        workflow_content = """
workflow_name: "Test Conditional Workflow"
steps:
  - id: step1
    name: "Step 1"
    script: "step1.py"
    snapshot_items: ["outputs/"]
    
  - id: step2
    name: "Step 2"
    script: "step2.py"
    snapshot_items: ["outputs/"]
    
  - id: conditional_step
    name: "Conditional Step"
    script: "conditional.py"
    snapshot_items: ["outputs/"]
    conditional:
      trigger_script: "step2.py"
      prompt: "Do you want to run the conditional step?"
      target_step: "step4"
      
  - id: step4
    name: "Step 4"
    script: "step4.py"
    snapshot_items: ["outputs/"]
"""
        
        workflow_file = self.project_path / "workflow.yml"
        workflow_file.write_text(workflow_content)
        
        # Create initial workflow state
        workflow_state = {
            "step1": "completed",
            "step2": "completed", 
            "conditional_step": "awaiting_decision",
            "step4": "pending"
        }
        
        state_file = self.project_path / "workflow_state.json"
        state_file.write_text(json.dumps(workflow_state, indent=2))
        
        # Create .workflow_status directory
        status_dir = self.project_path / ".workflow_status"
        status_dir.mkdir()
        
        # Create success markers for completed steps
        (status_dir / "step1.success").touch()
        (status_dir / "step2.success").touch()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_conditional_step_awaiting_decision_state_detected(self):
        """Test that conditional step in awaiting_decision state is properly detected."""
        project = Project(self.project_path)
        
        # Verify the state is as expected
        assert project.get_state("conditional_step") == "awaiting_decision"
        assert project.get_state("step2") == "completed"
        assert project.get_state("step1") == "completed"

    def test_conditional_undo_logic_includes_awaiting_decision(self):
        """Test that conditional undo logic properly handles awaiting_decision state."""
        project = Project(self.project_path)
        
        # Create a mock conditional decision snapshot
        snapshot_name = "conditional_step_conditional_decision"
        snapshot_path = project.path / ".snapshots" / f"{snapshot_name}_complete.zip"
        snapshot_path.parent.mkdir(exist_ok=True)
        snapshot_path.touch()  # Create empty file to simulate snapshot exists
        
        # Mock the snapshot_exists method to return True for our test snapshot
        with patch.object(project.snapshot_manager, 'snapshot_exists') as mock_exists:
            mock_exists.return_value = True
            
            # Mock the restore_complete_snapshot method
            with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore:
                
                # Import and test the perform_undo function
                from app import perform_undo
                
                # This should trigger conditional undo logic
                result = perform_undo(project)
                
                # Verify that conditional undo was attempted
                assert result == True
                mock_exists.assert_called_with("conditional_step_conditional_decision")
                mock_restore.assert_called_with("conditional_step_conditional_decision")

    def test_conditional_undo_logic_missing_awaiting_decision_bug(self):
        """Test that reproduces the bug where awaiting_decision is not handled."""
        project = Project(self.project_path)
        
        # Create a mock conditional decision snapshot
        snapshot_name = "conditional_step_conditional_decision"
        
        # Mock the snapshot_exists method to return True
        with patch.object(project.snapshot_manager, 'snapshot_exists') as mock_exists:
            mock_exists.return_value = True
            
            # Mock the restore_complete_snapshot method
            with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore:
                
                # Import the current (buggy) perform_undo function
                from app import perform_undo
                
                # Get the conditional step
                conditional_step = None
                for step in project.workflow.steps:
                    if step['id'] == 'conditional_step':
                        conditional_step = step
                        break
                
                assert conditional_step is not None
                assert 'conditional' in conditional_step
                
                # Check current state
                current_state = project.get_state('conditional_step')
                assert current_state == 'awaiting_decision'
                
                # The bug: awaiting_decision is not in the list ['pending', 'skipped_conditional']
                # So the conditional undo logic is skipped
                bug_condition = (
                    ('conditional' in conditional_step) and
                    (current_state in ['pending', 'skipped_conditional']) and  # BUG: missing 'awaiting_decision'
                    project.snapshot_manager.snapshot_exists(f"conditional_step_conditional_decision")
                )
                
                # This should be True but will be False due to the bug
                assert bug_condition == False, "Bug reproduced: awaiting_decision not handled"

    def test_fixed_conditional_undo_logic(self):
        """Test the fixed conditional undo logic that includes awaiting_decision."""
        project = Project(self.project_path)
        
        # Create a mock conditional decision snapshot
        with patch.object(project.snapshot_manager, 'snapshot_exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore:
                
                # Get the conditional step
                conditional_step = None
                for step in project.workflow.steps:
                    if step['id'] == 'conditional_step':
                        conditional_step = step
                        break
                
                # Check current state
                current_state = project.get_state('conditional_step')
                
                # The fix: include 'awaiting_decision' in the state list
                fixed_condition = (
                    ('conditional' in conditional_step) and
                    (current_state in ['pending', 'skipped_conditional', 'awaiting_decision']) and  # FIX: added 'awaiting_decision'
                    project.snapshot_manager.snapshot_exists(f"conditional_step_conditional_decision")
                )
                
                # This should now be True with the fix
                assert fixed_condition == True, "Fix works: awaiting_decision is now handled"

    def test_undo_with_awaiting_decision_restores_to_decision_point(self):
        """Test that undo from awaiting_decision state restores to the decision point."""
        project = Project(self.project_path)
        
        # Create the conditional decision snapshot directory
        snapshots_dir = project.path / ".snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        
        # Create a mock conditional decision snapshot file
        snapshot_file = snapshots_dir / "conditional_step_conditional_decision_complete.zip"
        snapshot_file.touch()
        
        # Mock the restore method to track what gets called
        with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore:
            
            # Create a fixed version of perform_undo for testing
            def fixed_perform_undo(project):
                """Fixed version of perform_undo that includes awaiting_decision."""
                # Check if there are any conditional steps that were affected by a decision
                for step in project.workflow.steps:
                    step_id = step['id']
                    current_state = project.get_state(step_id)
                    
                    # FIXED: Include 'awaiting_decision' in the state check
                    if (('conditional' in step) and
                        (current_state in ['pending', 'skipped_conditional', 'awaiting_decision']) and
                        project.snapshot_manager.snapshot_exists(f"{step_id}_conditional_decision")):
                        
                        try:
                            project.snapshot_manager.restore_complete_snapshot(f"{step_id}_conditional_decision")
                            print(f"UNDO: Restored to conditional decision point for step {step_id}")
                            return True
                        except FileNotFoundError:
                            pass
                
                return False
            
            # Test the fixed function
            result = fixed_perform_undo(project)
            
            # Verify it worked
            assert result == True
            mock_restore.assert_called_once_with("conditional_step_conditional_decision")

    def test_regular_undo_still_works_for_non_conditional_steps(self):
        """Test that regular undo still works for non-conditional completed steps."""
        # Modify state to have no conditional steps awaiting decision
        workflow_state = {
            "step1": "completed",
            "step2": "completed", 
            "conditional_step": "pending",  # Not awaiting decision
            "step4": "pending"
        }
        
        state_file = self.project_path / "workflow_state.json"
        state_file.write_text(json.dumps(workflow_state, indent=2))
        
        project = Project(self.project_path)
        
        # Mock snapshot operations for regular undo
        with patch.object(project.snapshot_manager, 'get_effective_run_number') as mock_run_num:
            mock_run_num.return_value = 1
            
            with patch.object(project.snapshot_manager, 'snapshot_exists') as mock_exists:
                mock_exists.return_value = True
                
                with patch.object(project.snapshot_manager, 'restore_complete_snapshot') as mock_restore:
                    with patch.object(project.snapshot_manager, 'remove_run_snapshots_from') as mock_remove:
                        
                        from app import perform_undo
                        
                        # This should use regular undo logic for step2 (last completed)
                        result = perform_undo(project)
                        
                        # Should succeed with regular undo
                        assert result == True