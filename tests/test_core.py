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

@pytest.mark.xfail(
    reason=(
        "Stage 2 undo redesign made script_path a required argument. "
        "Project() now raises ValueError when script_path is None. "
        "The old 'default to nested scripts/ directory' behaviour was removed "
        "because the workflow manager must always know the exact script location "
        "(set via SCRIPTS_PATH env var by run.py). "
        "See plans/undo_system_redesign.md and src/core.py Project.__init__."
    ),
    strict=True,
)
def test_project_init_no_script_path(tmp_path):
    """
    XFAIL: script_path is now a required argument (Stage 2 undo redesign).
    Project() raises ValueError when called without script_path.
    The old behaviour (defaulting to project_dir/scripts/) was removed.
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

    # ACT — this now raises ValueError because script_path is required
    project = Project(project_path=project_dir)

    # ASSERT — these lines are never reached; the xfail is triggered by the ValueError above
    assert project.script_path == project_dir / "scripts"
    assert project.script_runner.script_path == project_dir / "scripts"