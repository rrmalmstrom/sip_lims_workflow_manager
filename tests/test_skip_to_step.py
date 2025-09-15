"""
Test suite for "Skip to Step" functionality.
Tests the ability to start a workflow from a midway point by marking previous steps as "skipped".
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import yaml

from src.core import Project
from src.logic import StateManager, SnapshotManager
from src.core import Workflow


class TestSkipToStepFunctionality:
    """Test suite for Skip to Step feature"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_workflow_yml(self, temp_project_dir):
        """Create a sample workflow.yml file"""
        workflow_content = {
            'workflow_name': 'Test Workflow',
            'steps': [
                {
                    'id': 'step1',
                    'name': '1. First Step',
                    'script': 'scripts/step1.py',
                    'snapshot_items': ['outputs/step1/']
                },
                {
                    'id': 'step2',
                    'name': '2. Second Step',
                    'script': 'scripts/step2.py',
                    'snapshot_items': ['outputs/step2/']
                },
                {
                    'id': 'step3',
                    'name': '3. Third Step',
                    'script': 'scripts/step3.py',
                    'snapshot_items': ['outputs/step3/']
                },
                {
                    'id': 'step4',
                    'name': '4. Fourth Step',
                    'script': 'scripts/step4.py',
                    'snapshot_items': ['outputs/step4/']
                },
                {
                    'id': 'step5',
                    'name': '5. Fifth Step',
                    'script': 'scripts/step5.py',
                    'snapshot_items': ['outputs/step5/']
                }
            ]
        }
        
        workflow_file = temp_project_dir / 'workflow.yml'
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow_content, f)
        
        return workflow_file

    @pytest.fixture
    def project_with_existing_files(self, temp_project_dir, sample_workflow_yml):
        """Create a project with some existing files (simulating work done outside workflow)"""
        # Create some output directories and files to simulate existing work
        (temp_project_dir / 'outputs' / 'step1').mkdir(parents=True)
        (temp_project_dir / 'outputs' / 'step2').mkdir(parents=True)
        (temp_project_dir / 'outputs' / 'step3').mkdir(parents=True)
        
        (temp_project_dir / 'outputs' / 'step1' / 'result1.txt').write_text('Step 1 output')
        (temp_project_dir / 'outputs' / 'step2' / 'result2.txt').write_text('Step 2 output')
        (temp_project_dir / 'outputs' / 'step3' / 'result3.txt').write_text('Step 3 output')
        
        return Project(temp_project_dir)

    def test_skip_to_step_basic_functionality(self, project_with_existing_files):
        """Test basic skip to step functionality"""
        project = project_with_existing_files
        
        # Initially, no workflow state should exist
        assert not project.has_workflow_state()
        
        # Skip to step 4 (should mark steps 1-3 as skipped)
        result = project.skip_to_step('step4')
        
        # Verify return message
        assert 'step4' in result.lower() or 'fourth step' in result.lower()
        
        # Verify workflow state was created
        assert project.has_workflow_state()
        
        # Verify steps 1-3 are marked as skipped
        assert project.get_state('step1') == 'skipped'
        assert project.get_state('step2') == 'skipped'
        assert project.get_state('step3') == 'skipped'
        
        # Verify step 4 and 5 remain pending
        assert project.get_state('step4') == 'pending'
        assert project.get_state('step5') == 'pending'

    def test_skip_to_first_step_no_effect(self, project_with_existing_files):
        """Test that skipping to the first step has no effect"""
        project = project_with_existing_files
        
        # Skip to step 1 (first step)
        result = project.skip_to_step('step1')
        
        # Verify workflow state was created
        assert project.has_workflow_state()
        
        # Verify all steps remain pending (no steps should be skipped)
        assert project.get_state('step1') == 'pending'
        assert project.get_state('step2') == 'pending'
        assert project.get_state('step3') == 'pending'
        assert project.get_state('step4') == 'pending'
        assert project.get_state('step5') == 'pending'

    def test_skip_to_last_step(self, project_with_existing_files):
        """Test skipping to the last step"""
        project = project_with_existing_files
        
        # Skip to step 5 (last step)
        result = project.skip_to_step('step5')
        
        # Verify steps 1-4 are marked as skipped
        assert project.get_state('step1') == 'skipped'
        assert project.get_state('step2') == 'skipped'
        assert project.get_state('step3') == 'skipped'
        assert project.get_state('step4') == 'skipped'
        
        # Verify step 5 remains pending
        assert project.get_state('step5') == 'pending'

    def test_skip_to_invalid_step_raises_error(self, project_with_existing_files):
        """Test that skipping to an invalid step raises an error"""
        project = project_with_existing_files
        
        # Try to skip to a non-existent step
        with pytest.raises(ValueError, match="Step invalid_step not found"):
            project.skip_to_step('invalid_step')
        
        # Verify no workflow state was created
        assert not project.has_workflow_state()

    def test_skip_creates_safety_snapshot(self, project_with_existing_files):
        """Test that skip operation creates a safety snapshot for undo"""
        project = project_with_existing_files
        
        # Skip to step 3
        project.skip_to_step('step3')
        
        # Verify safety snapshot was created
        snapshots_dir = project.path / '.snapshots'
        assert snapshots_dir.exists()
        
        # Look for the skip safety snapshot
        snapshot_files = list(snapshots_dir.glob('*skip*initial*.zip'))
        assert len(snapshot_files) > 0, "Safety snapshot should be created"

    def test_skip_with_existing_workflow_state(self, project_with_existing_files):
        """Test skip behavior when workflow state already exists"""
        project = project_with_existing_files
        
        # Create initial workflow state with some completed steps
        project.update_state('step1', 'completed')
        project.update_state('step2', 'pending')
        
        # Skip to step 4 (should still work)
        result = project.skip_to_step('step4')
        
        # Verify steps 1-3 are marked as skipped (overriding previous state)
        assert project.get_state('step1') == 'skipped'
        assert project.get_state('step2') == 'skipped'
        assert project.get_state('step3') == 'skipped'
        assert project.get_state('step4') == 'pending'

    def test_state_manager_handles_skipped_state(self, temp_project_dir):
        """Test that StateManager properly handles the 'skipped' state"""
        state_manager = StateManager(temp_project_dir / "workflow_state.json")
        
        # Set a step as skipped
        state_manager.update_step_state('step1', 'skipped')
        
        # Verify it can be retrieved
        assert state_manager.get_step_state('step1') == 'skipped'
        
        # Verify it persists to file
        state_file = temp_project_dir / 'workflow_state.json'
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        assert state_data['step1'] == 'skipped'

    def test_has_workflow_state_detection(self, temp_project_dir, sample_workflow_yml):
        """Test the has_workflow_state() method works correctly"""
        project = Project(temp_project_dir)
        
        # Initially should have no workflow state
        assert not project.has_workflow_state()
        
        # After creating state, should detect it
        project.update_state('step1', 'pending')
        assert project.has_workflow_state()

    def test_get_next_available_step_with_skipped_steps(self, project_with_existing_files):
        """Test that get_next_available_step works correctly with skipped steps"""
        project = project_with_existing_files
        
        # Skip to step 3
        project.skip_to_step('step3')
        
        # Next available step should be step3 (first pending step)
        next_step = project.get_next_available_step()
        assert next_step is not None
        assert next_step['id'] == 'step3'

    def test_workflow_integration_with_skipped_steps(self, project_with_existing_files):
        """Test that the workflow system integrates properly with skipped steps"""
        project = project_with_existing_files
        
        # Skip to step 4
        project.skip_to_step('step4')
        
        # Verify workflow can identify step states correctly
        workflow_steps = project.workflow.steps
        
        # Check that we can iterate through steps and get correct states
        for i, step in enumerate(workflow_steps):
            expected_state = 'skipped' if i < 3 else 'pending'
            actual_state = project.get_state(step['id'])
            assert actual_state == expected_state, f"Step {step['id']} should be {expected_state}, got {actual_state}"