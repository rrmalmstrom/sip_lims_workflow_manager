from pathlib import Path
import sys
import pytest

# Add src to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import Project

def test_project_init_with_external_script_path(tmp_path):
    """
    Tests that the Project class correctly initializes with an external script path.
    """
    # ARRANGE
    project_dir = tmp_path / "my_project"
    project_dir.mkdir()
    scripts_dir = tmp_path / "external_scripts"
    scripts_dir.mkdir()
    (scripts_dir / "test_script.py").touch()
    workflow_content = """
workflow_name: Test Workflow
steps:
- id: step1
name: Test Step 1
script: test_script.py
"""
    (project_dir / "workflow.yml").write_text(workflow_content)


    # ACT
    project = Project(project_path=project_dir, script_path=scripts_dir)

    # ASSERT
    assert project.script_path == scripts_dir
    assert project.script_runner.script_path == scripts_dir
    assert project.script_runner.project_path == project_dir

def test_project_init_no_script_path(tmp_path):
    """
    Tests that the Project class defaults to the nested 'scripts' directory
    when no script_path is provided.
    """
    # ARRANGE
    project_dir = tmp_path / "my_project"
    project_dir.mkdir()
    (project_dir / "scripts").mkdir()
    workflow_content = """
workflow_name: Test Workflow
steps:
- id: step1
name: Test Step 1
script: test_script.py
"""
    (project_dir / "workflow.yml").write_text(workflow_content)

    # ACT
    project = Project(project_path=project_dir)

    # ASSERT
    assert project.script_path == project_dir / "scripts"
    assert project.script_runner.script_path == project_dir / "scripts"