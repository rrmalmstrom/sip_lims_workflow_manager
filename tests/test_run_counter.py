import pytest
import tempfile
import shutil
from pathlib import Path
from src.core import Project
from app import get_script_run_count

class TestRunCounter:
    """Test the get_script_run_count function."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create minimal workflow.yml
        workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: test_step
    name: "Test Step"
    script: "test_script.py"
    allow_rerun: true
"""
        workflow_file = temp_dir / "workflow.yml"
        workflow_file.write_text(workflow_content)
        
        # Create scripts directory
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test_script.py").write_text('print("test")')
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_run_count_zero_initially(self, temp_project):
        """Test that run count is 0 for steps that haven't been completed."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        count = get_script_run_count(project, "test_step")
        assert count == 0
    
    def test_run_count_after_completion(self, temp_project):
        """Test that run count increases after step completion."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Simulate step completion
        project.update_state("test_step", "completed")
        count = get_script_run_count(project, "test_step")
        assert count == 1
        
        # Simulate re-run
        project.update_state("test_step", "completed")
        count = get_script_run_count(project, "test_step")
        assert count == 2
    
    def test_run_count_after_undo(self, temp_project):
        """Test that run count decreases after undo operations."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Complete step twice
        project.update_state("test_step", "completed")
        project.update_state("test_step", "completed")
        assert get_script_run_count(project, "test_step") == 2
        
        # Simulate undo by removing last completion from order
        state = project.state_manager.load()
        completion_order = state.get("_completion_order", [])
        if completion_order and completion_order[-1] == "test_step":
            completion_order.pop()
            project.state_manager.save(state)
        
        # Count should decrease
        assert get_script_run_count(project, "test_step") == 1
    
    def test_run_count_nonexistent_step(self, temp_project):
        """Test that run count is 0 for non-existent steps."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        count = get_script_run_count(project, "nonexistent_step")
        assert count == 0