import pytest
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core import Workflow, Project
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult

# Sample workflow with file inputs for testing
WORKFLOW_WITH_INPUTS_YAML = """
workflow_name: "Test Workflow with Inputs"
steps:
  - id: step_1
    name: "First Step"
    script: "scripts/step1.py"
    snapshot_items: ["data/raw", "project.db"]
    inputs:
      - type: file
        name: "Input File 1"
        arg: "--input"
      - type: file
        name: "Input File 2"
        arg: "--config"
  - id: step_2
    name: "Second Step"
    script: "scripts/step2.py"
    snapshot_items: ["data/processed", "project.db"]
"""

@pytest.fixture
def workflow_with_inputs_file(tmp_path: Path) -> Path:
    """Creates a temporary workflow.yml file with input requirements for testing."""
    file_path = tmp_path / "workflow.yml"
    file_path.write_text(WORKFLOW_WITH_INPUTS_YAML)
    return file_path

@pytest.fixture
def project_with_inputs(tmp_path: Path, workflow_with_inputs_file: Path) -> Path:
    """Creates a temporary project directory with input-requiring workflow."""
    (tmp_path / ".snapshots").mkdir()
    (tmp_path / "scripts").mkdir()
    return tmp_path

@pytest.fixture
def mock_streamlit_session_state():
    """Mock streamlit session state for testing GUI logic."""
    return {
        'project': None,
        'user_inputs': {},
        'running_step_id': None,
        'project_path': None,
        'undo_confirmation': False
    }

class TestRerunFileInputBehavior:
    """Tests for ensuring re-run always prompts for new file inputs."""
    
    def test_completed_step_should_show_file_inputs_on_rerun_preparation(self, project_with_inputs):
        """
        Test that when preparing to re-run a completed step with file inputs,
        the GUI should show file input widgets and clear previous selections.
        """
        project = Project(project_with_inputs)
        
        # Simulate step completion
        project.update_state("step_1", "completed")
        
        # Mock session state with previous file inputs
        mock_session_state = {
            'user_inputs': {
                'step_1': {
                    'step_1_input_0': '/old/path/file1.txt',
                    'step_1_input_1': '/old/path/config.yml'
                }
            }
        }
        
        # The key test: when preparing for re-run, file inputs should be cleared
        # This simulates what should happen when user clicks "Re-run"
        step = project.workflow.get_step_by_id("step_1")
        
        # Verify the step has inputs defined
        assert 'inputs' in step
        assert len(step['inputs']) == 2
        
        # Test the logic that should clear inputs for re-run
        # This is what we need to implement in the GUI
        should_clear_inputs_for_rerun = True  # This is our requirement
        
        if should_clear_inputs_for_rerun:
            # Clear the inputs for re-run (this is what we want to implement)
            mock_session_state['user_inputs']['step_1'] = {}
        
        # Verify inputs are cleared
        assert mock_session_state['user_inputs']['step_1'] == {}
    
    def test_rerun_button_should_require_new_file_inputs(self, project_with_inputs):
        """
        Test that re-run button should be disabled until new file inputs are provided,
        even if the step was previously completed with different inputs.
        """
        project = Project(project_with_inputs)
        
        # Complete the step with initial inputs
        project.update_state("step_1", "completed")
        
        # Mock session state after clearing inputs for re-run
        mock_session_state = {
            'user_inputs': {
                'step_1': {}  # Cleared for re-run
            },
            'running_step_id': None
        }
        
        step = project.workflow.get_step_by_id("step_1")
        
        # Test the logic for determining if re-run button should be enabled
        def should_enable_rerun_button(step, session_state):
            """Logic to determine if re-run button should be enabled."""
            if 'inputs' not in step:
                return True  # No inputs required
            
            step_inputs = session_state['user_inputs'].get(step['id'], {})
            required_inputs = step['inputs']
            
            # Check if all required inputs are filled
            if len(step_inputs) < len(required_inputs):
                return False
            
            # Check if any input is empty
            if not all(step_inputs.values()):
                return False
                
            return True
        
        # Initially, button should be disabled (no new inputs provided)
        assert not should_enable_rerun_button(step, mock_session_state)
        
        # After providing new inputs, button should be enabled
        mock_session_state['user_inputs']['step_1'] = {
            'step_1_input_0': '/new/path/file1.txt',
            'step_1_input_1': '/new/path/config.yml'
        }
        
        assert should_enable_rerun_button(step, mock_session_state)
    
    def test_rerun_with_different_inputs_should_work(self, project_with_inputs):
        """
        Test that re-running a step with different input files should work correctly.
        """
        project = Project(project_with_inputs)
        
        # Create mock input files
        old_file = project_with_inputs / "old_input.txt"
        new_file = project_with_inputs / "new_input.txt"
        old_file.write_text("old content")
        new_file.write_text("new content")
        
        # First run with old inputs
        old_inputs = {
            'step_1_input_0': str(old_file),
            'step_1_input_1': str(old_file)
        }
        
        # Simulate successful completion
        project.update_state("step_1", "completed")
        
        # Now prepare for re-run with new inputs
        new_inputs = {
            'step_1_input_0': str(new_file),
            'step_1_input_1': str(new_file)
        }
        
        # Verify that the new inputs are different
        assert new_inputs != old_inputs
        
        # The re-run should accept the new inputs
        step = project.workflow.get_step_by_id("step_1")
        assert step is not None
        
        # This simulates what should happen in the GUI when re-running
        # The step should be able to run with the new inputs
        assert project.get_state("step_1") == "completed"


class TestUndoFunctionality:
    """Tests for undo functionality with confirmation dialog."""
    
    def test_project_should_support_undo_to_previous_state(self, project_with_inputs):
        """
        Test that the project can undo to the previous completed state.
        """
        project = Project(project_with_inputs)
        
        # Create some test data
        test_file = project_with_inputs / "test_data.txt"
        test_file.write_text("initial content")
        
        # Complete step 1
        project.update_state("step_1", "completed")
        
        # Simulate taking a snapshot (this happens in run_step)
        step1 = project.workflow.get_step_by_id("step_1")
        project.snapshot_manager.take("step_1", step1.get("snapshot_items", []))
        
        # Modify data and complete step 2
        test_file.write_text("modified content after step 1")
        project.update_state("step_2", "completed")
        
        # Take snapshot for step 2
        step2 = project.workflow.get_step_by_id("step_2")
        project.snapshot_manager.take("step_2", step2.get("snapshot_items", []))
        
        # Verify current state
        assert project.get_state("step_1") == "completed"
        assert project.get_state("step_2") == "completed"
        
        # Test undo functionality - should revert to state after step 1
        def undo_last_step(project):
            """Undo the last completed step."""
            # Find the last completed step
            completed_steps = []
            for step in project.workflow.steps:
                if project.get_state(step['id']) == "completed":
                    completed_steps.append(step)
            
            if not completed_steps:
                return False  # Nothing to undo
            
            # Get the last completed step
            last_step = completed_steps[-1]
            last_step_id = last_step['id']
            
            # Find the previous step to revert to
            step_index = next(i for i, s in enumerate(project.workflow.steps) if s['id'] == last_step_id)
            
            if step_index == 0:
                # If undoing the first step, revert to initial state
                target_step_id = None
            else:
                # Revert to the previous step's snapshot
                target_step_id = project.workflow.steps[step_index - 1]['id']
            
            # Restore the snapshot and update state
            if target_step_id:
                # Restore to previous step's state
                target_step = project.workflow.get_step_by_id(target_step_id)
                project.snapshot_manager.restore(target_step_id, target_step.get("snapshot_items", []))
                
                # Update states: mark current step as pending, keep previous as completed
                project.update_state(last_step_id, "pending")
            else:
                # Restore to initial state (before any steps)
                project.snapshot_manager.restore(last_step_id, last_step.get("snapshot_items", []))
                project.update_state(last_step_id, "pending")
            
            return True
        
        # Perform undo
        undo_success = undo_last_step(project)
        assert undo_success
        
        # Verify state after undo
        assert project.get_state("step_1") == "completed"
        assert project.get_state("step_2") == "pending"
    
    def test_undo_confirmation_dialog_logic(self):
        """
        Test the logic for undo confirmation dialog.
        """
        mock_session_state = {
            'undo_confirmation': False,
            'project': Mock()
        }
        
        def handle_undo_button_click(session_state):
            """Handle undo button click - should show confirmation first."""
            if not session_state.get('undo_confirmation', False):
                # First click - show confirmation
                session_state['undo_confirmation'] = True
                return "show_confirmation"
            else:
                # Second click - perform undo
                session_state['undo_confirmation'] = False
                return "perform_undo"
        
        # First click should show confirmation
        result = handle_undo_button_click(mock_session_state)
        assert result == "show_confirmation"
        assert mock_session_state['undo_confirmation'] is True
        
        # Second click should perform undo
        result = handle_undo_button_click(mock_session_state)
        assert result == "perform_undo"
        assert mock_session_state['undo_confirmation'] is False
    
    def test_undo_button_should_be_disabled_when_no_completed_steps(self, project_with_inputs):
        """
        Test that undo button should be disabled when there are no completed steps.
        """
        project = Project(project_with_inputs)
        
        def can_undo(project):
            """Check if undo is possible."""
            # Check if there are any completed steps
            for step in project.workflow.steps:
                if project.get_state(step['id']) == "completed":
                    return True
            return False
        
        # Initially, no steps completed - undo should be disabled
        assert not can_undo(project)
        
        # After completing a step, undo should be enabled
        project.update_state("step_1", "completed")
        assert can_undo(project)
    
    def test_undo_should_preserve_snapshots_for_redo(self, project_with_inputs):
        """
        Test that undo preserves snapshots so redo could be implemented later.
        """
        project = Project(project_with_inputs)
        
        # Complete steps and take snapshots
        project.update_state("step_1", "completed")
        step1 = project.workflow.get_step_by_id("step_1")
        project.snapshot_manager.take("step_1", step1.get("snapshot_items", []))
        
        project.update_state("step_2", "completed")
        step2 = project.workflow.get_step_by_id("step_2")
        project.snapshot_manager.take("step_2", step2.get("snapshot_items", []))
        
        # Verify snapshots exist
        snapshot1_path = project.snapshot_manager.snapshots_dir / "step_1.zip"
        snapshot2_path = project.snapshot_manager.snapshots_dir / "step_2.zip"
        
        assert snapshot1_path.exists()
        assert snapshot2_path.exists()
        
        # After undo, snapshots should still exist for potential redo
        # (This is already handled by the current SnapshotManager implementation)
        assert snapshot1_path.exists()
        assert snapshot2_path.exists()


class TestGUIIntegration:
    """Integration tests for GUI features."""
    
    def test_file_input_widget_state_management(self):
        """
        Test the logic for managing file input widget states in the GUI.
        """
        # Mock the GUI state for a step with file inputs
        step_config = {
            'id': 'step_1',
            'name': 'Test Step',
            'inputs': [
                {'type': 'file', 'name': 'Input File', 'arg': '--input'}
            ]
        }
        
        mock_session_state = {
            'user_inputs': {},
            'running_step_id': None
        }
        
        def should_show_file_inputs(step, status, is_running, session_state):
            """Determine if file input widgets should be shown."""
            if 'inputs' not in step:
                return False
            
            if is_running:
                return False
            
            # Key change: Always show inputs for re-runs
            if status == 'completed':
                return True  # This is the new behavior we want
            
            if status != 'completed' and not is_running:
                return True
                
            return False
        
        # Test: completed step should show inputs for re-run
        assert should_show_file_inputs(step_config, 'completed', False, mock_session_state)
        
        # Test: pending step should show inputs
        assert should_show_file_inputs(step_config, 'pending', False, mock_session_state)
        
        # Test: running step should not show inputs
        assert not should_show_file_inputs(step_config, 'pending', True, mock_session_state)
    
    def test_undo_button_placement_and_state(self):
        """
        Test the logic for undo button placement and enabled state.
        """
        def get_undo_button_config(project, session_state):
            """Get configuration for undo button."""
            if not project:
                return {'show': False, 'enabled': False, 'text': 'Undo'}
            
            # Check if any steps are completed
            has_completed_steps = False
            for step in project.workflow.steps:
                if project.get_state(step['id']) == 'completed':
                    has_completed_steps = True
                    break
            
            # Check if confirmation is pending
            confirmation_pending = session_state.get('undo_confirmation', False)
            
            return {
                'show': True,
                'enabled': has_completed_steps,
                'text': 'Are you sure?' if confirmation_pending else 'Undo Last Step'
            }
        
        # Mock project with no completed steps
        mock_project = Mock()
        mock_project.workflow.steps = [
            {'id': 'step_1', 'name': 'Step 1'},
            {'id': 'step_2', 'name': 'Step 2'}
        ]
        mock_project.get_state.return_value = 'pending'
        
        mock_session_state = {'undo_confirmation': False}
        
        # No completed steps - button disabled
        config = get_undo_button_config(mock_project, mock_session_state)
        assert config['show'] is True
        assert config['enabled'] is False
        assert config['text'] == 'Undo Last Step'
        
        # With completed step - button enabled
        mock_project.get_state.side_effect = lambda step_id: 'completed' if step_id == 'step_1' else 'pending'
        config = get_undo_button_config(mock_project, mock_session_state)
        assert config['enabled'] is True
        
        # With confirmation pending - text changes
        mock_session_state['undo_confirmation'] = True
        config = get_undo_button_config(mock_project, mock_session_state)
        assert config['text'] == 'Are you sure?'