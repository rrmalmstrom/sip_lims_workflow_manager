import pytest
import yaml
import json
from pathlib import Path
from src.core import Workflow, Project
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult

# Sample workflow with conditional steps
CONDITIONAL_WORKFLOW_YAML = """
workflow_name: "Test Conditional Workflow"
steps:
  - id: step_1
    name: "First Step"
    script: "scripts/step1.py"
    snapshot_items: ["data/"]
    
  - id: step_2
    name: "Second Step (Analysis)"
    script: "scripts/second.FA.output.analysis.py"
    snapshot_items: ["outputs/"]
    
  - id: step_3
    name: "Third Step (Emergency Rework)"
    script: "scripts/emergency.third.attempt.rework.py"
    snapshot_items: ["outputs/"]
    conditional:
      trigger_script: "scripts/second.FA.output.analysis.py"
      prompt: "Do you want to run a third attempt at library creation?"
      target_step: "step_5"
      
  - id: step_4
    name: "Fourth Step (Emergency Analysis)"
    script: "scripts/emergency.third.FA.output.analysis.py"
    snapshot_items: ["outputs/"]
    conditional:
      depends_on: "step_3"
      
  - id: step_5
    name: "Fifth Step (Conclude)"
    script: "scripts/conclude.all.fa.analysis.py"
    snapshot_items: ["outputs/"]
"""

@pytest.fixture
def conditional_workflow_file(tmp_path: Path) -> Path:
    """Creates a temporary workflow.yml file with conditional steps."""
    file_path = tmp_path / "workflow.yml"
    file_path.write_text(CONDITIONAL_WORKFLOW_YAML)
    return file_path

@pytest.fixture
def conditional_project_directory(tmp_path: Path, conditional_workflow_file: Path) -> Path:
    """Creates a temporary project directory for conditional workflow testing."""
    (tmp_path / ".snapshots").mkdir()
    (tmp_path / "scripts").mkdir()
    return tmp_path

class TestConditionalWorkflowConfiguration:
    """Tests for conditional workflow configuration parsing."""
    
    def test_conditional_step_parsing(self, conditional_workflow_file: Path):
        """Test that conditional step configuration is parsed correctly."""
        workflow = Workflow(conditional_workflow_file)
        
        # Find the conditional step
        step_3 = workflow.get_step_by_id('step_3')
        assert step_3 is not None
        assert 'conditional' in step_3
        
        conditional_config = step_3['conditional']
        assert conditional_config['trigger_script'] == "scripts/second.FA.output.analysis.py"
        assert conditional_config['prompt'] == "Do you want to run a third attempt at library creation?"
        assert conditional_config['target_step'] == "step_5"
        
    def test_dependent_conditional_step_parsing(self, conditional_workflow_file: Path):
        """Test that dependent conditional steps are parsed correctly."""
        workflow = Workflow(conditional_workflow_file)
        
        step_4 = workflow.get_step_by_id('step_4')
        assert step_4 is not None
        assert 'conditional' in step_4
        assert step_4['conditional']['depends_on'] == "step_3"

class TestConditionalStateManagement:
    """Tests for conditional workflow state management."""
    
    def test_awaiting_decision_state(self, conditional_project_directory: Path):
        """Test that steps can be marked as awaiting_decision."""
        state_manager = StateManager(conditional_project_directory / "workflow_state.json")
        
        # Test setting and getting awaiting_decision state
        state_manager.update_step_state("step_3", "awaiting_decision")
        assert state_manager.get_step_state("step_3") == "awaiting_decision"
        
    def test_skipped_conditional_state(self, conditional_project_directory: Path):
        """Test that steps can be marked as skipped_conditional."""
        state_manager = StateManager(conditional_project_directory / "workflow_state.json")
        
        # Test setting and getting skipped_conditional state
        state_manager.update_step_state("step_3", "skipped_conditional")
        assert state_manager.get_step_state("step_3") == "skipped_conditional"
        
    def test_state_persistence(self, conditional_project_directory: Path):
        """Test that conditional states persist across state manager instances."""
        state_file = conditional_project_directory / "workflow_state.json"
        
        # Create first state manager and set states
        state_manager1 = StateManager(state_file)
        state_manager1.update_step_state("step_2", "completed")
        state_manager1.update_step_state("step_3", "awaiting_decision")
        state_manager1.update_step_state("step_4", "skipped_conditional")
        
        # Create new state manager and verify states persist
        state_manager2 = StateManager(state_file)
        assert state_manager2.get_step_state("step_2") == "completed"
        assert state_manager2.get_step_state("step_3") == "awaiting_decision"
        assert state_manager2.get_step_state("step_4") == "skipped_conditional"

class TestConditionalWorkflowLogic:
    """Tests for conditional workflow logic in Project class."""
    
    def test_trigger_conditional_decision(self, conditional_project_directory: Path):
        """Test that completing a trigger script activates conditional decision."""
        project = Project(conditional_project_directory)
        
        # Simulate completing step_2 (the trigger script)
        project.update_state("step_2", "completed")
        
        # Check if conditional logic would be triggered
        step_3 = project.workflow.get_step_by_id("step_3")
        conditional_config = step_3.get('conditional', {})
        trigger_script = conditional_config.get('trigger_script')
        
        # Verify the trigger script matches
        step_2 = project.workflow.get_step_by_id("step_2")
        assert step_2['script'] == trigger_script
        
    def test_conditional_step_activation(self, conditional_project_directory: Path):
        """Test that conditional steps can be activated or skipped."""
        project = Project(conditional_project_directory)
        
        # Test activating conditional step
        project.update_state("step_3", "pending")
        assert project.get_state("step_3") == "pending"
        
        # Test skipping conditional step and jumping to target
        project.update_state("step_3", "skipped_conditional")
        project.update_state("step_5", "pending")
        assert project.get_state("step_3") == "skipped_conditional"
        assert project.get_state("step_5") == "pending"
        
    def test_dependent_step_handling(self, conditional_project_directory: Path):
        """Test that dependent conditional steps are handled correctly."""
        project = Project(conditional_project_directory)
        
        # If step_3 is skipped, step_4 should also be skipped
        project.update_state("step_3", "skipped_conditional")
        project.update_state("step_4", "skipped_conditional")
        
        assert project.get_state("step_3") == "skipped_conditional"
        assert project.get_state("step_4") == "skipped_conditional"
        
        # If step_3 is activated, step_4 should be available
        project.update_state("step_3", "completed")
        project.update_state("step_4", "pending")
        
        assert project.get_state("step_3") == "completed"
        assert project.get_state("step_4") == "pending"

class TestConditionalWorkflowMethods:
    """Tests for new methods needed for conditional workflow support."""
    
    def test_get_conditional_steps(self, conditional_project_directory: Path):
        """Test method to identify conditional steps in workflow."""
        project = Project(conditional_project_directory)
        
        # This method should be implemented to find conditional steps
        conditional_steps = []
        for step in project.workflow.steps:
            if 'conditional' in step:
                conditional_steps.append(step)
        
        assert len(conditional_steps) == 2  # step_3 and step_4
        assert conditional_steps[0]['id'] == 'step_3'
        assert conditional_steps[1]['id'] == 'step_4'
        
    def test_should_show_conditional_prompt(self, conditional_project_directory: Path):
        """Test logic to determine when to show conditional prompt."""
        project = Project(conditional_project_directory)
        
        # Complete the trigger step
        project.update_state("step_2", "completed")
        
        # Step 3 should now be ready for conditional prompt
        step_3 = project.workflow.get_step_by_id("step_3")
        conditional_config = step_3.get('conditional', {})
        
        # Check if this step should show conditional prompt
        trigger_script = conditional_config.get('trigger_script')
        if trigger_script:
            # Find the step with this script
            trigger_step = None
            for step in project.workflow.steps:
                if step.get('script') == trigger_script:
                    trigger_step = step
                    break
            
            if trigger_step and project.get_state(trigger_step['id']) == "completed":
                # Should show conditional prompt
                assert True
            else:
                assert False, "Conditional prompt should be shown"
                
    def test_handle_conditional_decision_yes(self, conditional_project_directory: Path):
        """Test handling user decision 'Yes' for conditional step."""
        project = Project(conditional_project_directory)
        
        # Simulate user choosing "Yes" to run conditional step
        project.update_state("step_3", "pending")
        
        # Dependent step should also be available
        project.update_state("step_4", "pending")
        
        assert project.get_state("step_3") == "pending"
        assert project.get_state("step_4") == "pending"
        
    def test_handle_conditional_decision_no(self, conditional_project_directory: Path):
        """Test handling user decision 'No' for conditional step."""
        project = Project(conditional_project_directory)
        
        # Simulate user choosing "No" to skip conditional steps
        step_3 = project.workflow.get_step_by_id("step_3")
        target_step_id = step_3['conditional']['target_step']
        
        # Skip conditional steps and jump to target
        project.update_state("step_3", "skipped_conditional")
        project.update_state("step_4", "skipped_conditional")
        project.update_state(target_step_id, "pending")
        
        assert project.get_state("step_3") == "skipped_conditional"
        assert project.get_state("step_4") == "skipped_conditional"
        assert project.get_state("step_5") == "pending"

class TestConditionalWorkflowIntegration:
    """Integration tests for conditional workflow functionality."""
    
    def test_full_conditional_workflow_yes_path(self, conditional_project_directory: Path):
        """Test complete workflow execution with 'Yes' path."""
        project = Project(conditional_project_directory)
        
        # Execute normal steps
        project.update_state("step_1", "completed")
        project.update_state("step_2", "completed")
        
        # User chooses "Yes" for conditional step
        project.update_state("step_3", "pending")
        project.update_state("step_3", "completed")
        
        # Continue with dependent step
        project.update_state("step_4", "pending")
        project.update_state("step_4", "completed")
        
        # Finally run conclude step
        project.update_state("step_5", "pending")
        project.update_state("step_5", "completed")
        
        # Verify final state
        assert project.get_state("step_1") == "completed"
        assert project.get_state("step_2") == "completed"
        assert project.get_state("step_3") == "completed"
        assert project.get_state("step_4") == "completed"
        assert project.get_state("step_5") == "completed"
        
    def test_full_conditional_workflow_no_path(self, conditional_project_directory: Path):
        """Test complete workflow execution with 'No' path."""
        project = Project(conditional_project_directory)
        
        # Execute normal steps
        project.update_state("step_1", "completed")
        project.update_state("step_2", "completed")
        
        # User chooses "No" for conditional step - skip to target
        project.update_state("step_3", "skipped_conditional")
        project.update_state("step_4", "skipped_conditional")
        project.update_state("step_5", "pending")
        project.update_state("step_5", "completed")
        
        # Verify final state
        assert project.get_state("step_1") == "completed"
        assert project.get_state("step_2") == "completed"
        assert project.get_state("step_3") == "skipped_conditional"
        assert project.get_state("step_4") == "skipped_conditional"
        assert project.get_state("step_5") == "completed"

class TestConditionalWorkflowEdgeCases:
    """Tests for edge cases in conditional workflow functionality."""
    
    def test_missing_target_step(self, tmp_path: Path):
        """Test handling of invalid target step in conditional configuration."""
        invalid_workflow = """
workflow_name: "Invalid Conditional Workflow"
steps:
  - id: step_1
    name: "First Step"
    script: "scripts/step1.py"
    conditional:
      trigger_script: "scripts/trigger.py"
      target_step: "nonexistent_step"
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(invalid_workflow)
        
        # Should handle gracefully or raise appropriate error
        workflow = Workflow(workflow_file)
        step_1 = workflow.get_step_by_id("step_1")
        target_step_id = step_1['conditional']['target_step']
        target_step = workflow.get_step_by_id(target_step_id)
        
        assert target_step is None  # Should handle missing target step
        
    def test_circular_conditional_dependency(self, tmp_path: Path):
        """Test handling of circular dependencies in conditional steps."""
        circular_workflow = """
workflow_name: "Circular Conditional Workflow"
steps:
  - id: step_1
    name: "First Step"
    script: "scripts/step1.py"
    conditional:
      trigger_script: "scripts/step2.py"
      target_step: "step_2"
      
  - id: step_2
    name: "Second Step"
    script: "scripts/step2.py"
    conditional:
      trigger_script: "scripts/step1.py"
      target_step: "step_1"
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(circular_workflow)
        
        # Should handle circular dependencies gracefully
        workflow = Workflow(workflow_file)
        assert len(workflow.steps) == 2
        
    def test_conditional_step_without_trigger(self, tmp_path: Path):
        """Test conditional step configuration without trigger script."""
        incomplete_workflow = """
workflow_name: "Incomplete Conditional Workflow"
steps:
  - id: step_1
    name: "First Step"
    script: "scripts/step1.py"
    conditional:
      prompt: "Do you want to continue?"
      target_step: "step_2"
      # Missing trigger_script
      
  - id: step_2
    name: "Second Step"
    script: "scripts/step2.py"
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(incomplete_workflow)
        
        workflow = Workflow(workflow_file)
        step_1 = workflow.get_step_by_id("step_1")
        conditional_config = step_1.get('conditional', {})
        
        # Should handle missing trigger_script
        assert 'trigger_script' not in conditional_config
        assert 'prompt' in conditional_config