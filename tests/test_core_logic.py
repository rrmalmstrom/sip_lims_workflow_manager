import pytest
import yaml
import json
import zipfile
from pathlib import Path
from src.core import Workflow, Project
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult

# A sample valid workflow configuration
SAMPLE_WORKFLOW_YAML = """
workflow_name: "Test Workflow"
steps:
  - id: step_1
    name: "First Step"
    script: "scripts/step1.py"
    snapshot_items: ["data/raw", "project.db"]
  - id: step_2
    name: "Second Step"
    script: "scripts/step2.py"
    snapshot_items: ["data/processed", "project.db"]
"""

@pytest.fixture
def workflow_file(tmp_path: Path) -> Path:
    """Creates a temporary workflow.yml file for testing."""
    file_path = tmp_path / "workflow.yml"
    file_path.write_text(SAMPLE_WORKFLOW_YAML)
    return file_path

@pytest.fixture
def project_directory(tmp_path: Path, workflow_file: Path) -> Path:
    """Creates a temporary project directory structure."""
    (tmp_path / ".snapshots").mkdir()
    (tmp_path / "scripts").mkdir() # This is for the project-level scripts folder
    return tmp_path

def test_workflow_loading_and_parsing(workflow_file: Path):
    """
    Tests that the Workflow class can correctly load and parse a valid
    workflow.yml file.
    """
    workflow = Workflow(workflow_file)

    assert workflow.name == "Test Workflow"
    assert len(workflow.steps) == 2
    
    step1 = workflow.steps[0]
    assert step1['id'] == 'step_1'
    assert step1['name'] == 'First Step'
    assert step1['script'] == 'scripts/step1.py'
    assert step1['snapshot_items'] == ['data/raw', 'project.db']

    step2 = workflow.get_step_by_id('step_2')
    assert step2 is not None
    assert step2['name'] == 'Second Step'

def test_project_initialization(project_directory: Path):
    """
    Tests that the Project class initializes correctly, identifying key files.
    """
    project = Project(project_directory)

    assert project.path == project_directory
    assert project.workflow is not None
    assert project.workflow.name == "Test Workflow"
    assert isinstance(project.state_manager, StateManager)
    assert isinstance(project.snapshot_manager, SnapshotManager)
    assert project.state_manager.path == project_directory / "workflow_state.json"
    assert project.snapshot_manager.snapshots_dir == project_directory / ".snapshots"

def test_state_manager(project_directory: Path):
    """
    Tests that the StateManager can correctly read, update, and write
    the workflow_state.json file.
    """
    state_file = project_directory / "workflow_state.json"
    state_manager = StateManager(state_file)

    assert not state_file.exists()
    assert state_manager.get_step_state("step_1") == "pending"

    state_manager.update_step_state("step_1", "completed")

    assert state_file.exists()
    with open(state_file, 'r') as f:
        state_data = json.load(f)
    assert state_data == {"step_1": "completed"}
    assert state_manager.get_step_state("step_1") == "completed"
    assert state_manager.get_step_state("step_2") == "pending"

    state_manager.update_step_state("step_2", "completed")

    with open(state_file, 'r') as f:
        state_data = json.load(f)
    assert state_data == {"step_1": "completed", "step_2": "completed"}
    assert state_manager.get_step_state("step_2") == "completed"

def test_snapshot_manager(project_directory: Path):
    """
    Tests that the SnapshotManager can correctly take and restore a snapshot.
    """
    snapshots_dir = project_directory / ".snapshots"
    snapshot_manager = SnapshotManager(project_directory, snapshots_dir)
    
    (project_directory / "data").mkdir()
    (project_directory / "data" / "raw").mkdir()
    db_file = project_directory / "project.db"
    raw_file = project_directory / "data" / "raw" / "data.txt"
    
    original_db_content = "original db content"
    original_raw_content = "original raw content"
    db_file.write_text(original_db_content)
    raw_file.write_text(original_raw_content)

    snapshot_items = ["project.db", "data/raw"]
    snapshot_manager.take("step_1", snapshot_items)

    snapshot_zip = snapshots_dir / "step_1.zip"
    assert snapshot_zip.exists()

    with zipfile.ZipFile(snapshot_zip, 'r') as zf:
        assert "project.db" in zf.namelist()
        assert "data/raw/data.txt" in zf.namelist()

    db_file.write_text("modified db content")
    raw_file.write_text("modified raw content")
    assert db_file.read_text() == "modified db content"

    snapshot_manager.restore("step_1", snapshot_items)

    assert db_file.read_text() == original_db_content
    assert raw_file.read_text() == original_raw_content

def test_script_runner_success(project_directory: Path):
    """Tests that the ScriptRunner can successfully execute a script."""
    # The new logic finds the scripts folder relative to the src directory,
    # so we need to put the dummy script there.
    app_scripts_dir = Path(__file__).parent.parent / "scripts"
    app_scripts_dir.mkdir(exist_ok=True)
    script_file = app_scripts_dir / "step1.py"
    script_file.write_text("print('Success!'); import sys; sys.exit(0)")
    
    runner = ScriptRunner(project_directory)
    
    # Start the script asynchronously
    runner.run("scripts/step1.py")
    
    # Wait for the script to complete and get the result
    import time
    timeout = 10  # 10 second timeout
    start_time = time.time()
    result = None
    
    while time.time() - start_time < timeout:
        try:
            result = runner.result_queue.get_nowait()
            break
        except:
            time.sleep(0.1)
    
    # Clean up
    runner.stop()
    
    assert result is not None, "Script did not complete within timeout"
    assert result.success is True
    assert result.return_code == 0

def test_project_run_step_integration_success(project_directory: Path):
    """
    Tests the full integration of the Project class for a successful step run.
    """
    app_scripts_dir = Path(__file__).parent.parent / "scripts"
    app_scripts_dir.mkdir(exist_ok=True)
    script_file = app_scripts_dir / "step1.py"
    script_file.write_text("print('Success!')")

    project = Project(project_directory)
    snapshot_file = project.snapshot_manager.snapshots_dir / "step_1.zip"

    assert project.get_state("step_1") == "pending"
    assert not snapshot_file.exists()

    # Start the script asynchronously
    project.run_step("step_1")
    
    # Wait for the script to complete and get the result
    import time
    timeout = 10  # 10 second timeout
    start_time = time.time()
    result = None
    
    while time.time() - start_time < timeout:
        try:
            result = project.script_runner.result_queue.get_nowait()
            break
        except:
            time.sleep(0.1)
    
    assert result is not None, "Script did not complete within timeout"
    
    # Handle the result using the new method
    project.handle_step_result("step_1", result)
    
    assert result.success is True
    assert snapshot_file.exists()
    assert project.get_state("step_1") == "completed"

def test_project_run_step_integration_failure(project_directory: Path):
    """
    Tests the full integration of the Project class for a failed step run,
    ensuring rollback occurs.
    """
    db_file = project_directory / "project.db"
    original_db_content = "original content"
    db_file.write_text(original_db_content)

    app_scripts_dir = Path(__file__).parent.parent / "scripts"
    app_scripts_dir.mkdir(exist_ok=True)
    script_file = app_scripts_dir / "step1.py"
    script_file.write_text("""
import sys
from pathlib import Path
Path("project.db").write_text("modified content")
print("Failing script", file=sys.stderr)
sys.exit(1)
""")

    project = Project(project_directory)
    snapshot_file = project.snapshot_manager.snapshots_dir / "step_1.zip"

    assert project.get_state("step_1") == "pending"
    assert not snapshot_file.exists()

    # Start the script asynchronously
    project.run_step("step_1")
    
    # Wait for the script to complete and get the result
    import time
    timeout = 10  # 10 second timeout
    start_time = time.time()
    result = None
    
    while time.time() - start_time < timeout:
        try:
            result = project.script_runner.result_queue.get_nowait()
            break
        except:
            time.sleep(0.1)
    
    assert result is not None, "Script did not complete within timeout"
    
    # Handle the result using the new method (this should trigger rollback)
    project.handle_step_result("step_1", result)

    assert result.success is False
    assert snapshot_file.exists()
    assert project.get_state("step_1") == "pending"
    assert db_file.read_text() == original_db_content  # This should be restored!


def test_project_initialization_no_workflow(project_directory: Path):
    """
    Tests that the Project class can be initialized without a workflow file
    if `load_workflow` is False.
    """
    # Remove the workflow file created by the fixture
    (project_directory / "workflow.yml").unlink()

    project = Project(project_directory, load_workflow=False)
    assert project.path == project_directory
    assert project.workflow is None
    assert isinstance(project.state_manager, StateManager)
    assert isinstance(project.snapshot_manager, SnapshotManager)


def test_snapshot_manager_restore_latest_file(project_directory: Path):
    """
    Tests that the SnapshotManager can restore a single file from the
    most recent snapshot.
    """
    snapshot_manager = SnapshotManager(project_directory, project_directory / ".snapshots")
    
    # Create a dummy file and take a snapshot
    workflow_content_v1 = "version: 1"
    (project_directory / "workflow.yml").write_text(workflow_content_v1)
    snapshot_manager.take("step_1", ["workflow.yml"])
    
    # Modify the file and take another snapshot
    workflow_content_v2 = "version: 2"
    (project_directory / "workflow.yml").write_text(workflow_content_v2)
    snapshot_manager.take("step_2", ["workflow.yml"])

    # "Delete" the file
    (project_directory / "workflow.yml").unlink()
    assert not (project_directory / "workflow.yml").exists()

    # Restore from the latest snapshot (step_2)
    restored = snapshot_manager.restore_file_from_latest_snapshot("workflow.yml")
    assert restored is True
    assert (project_directory / "workflow.yml").read_text() == workflow_content_v2


def test_snapshot_manager_restore_latest_file_not_found(project_directory: Path):
    """
    Tests that restore_file_from_latest_snapshot returns False if the
    file is not in the snapshot.
    """
    snapshot_manager = SnapshotManager(project_directory, project_directory / ".snapshots")
    (project_directory / "some_other_file.txt").write_text("some data")
    snapshot_manager.take("step_1", ["some_other_file.txt"])

    restored = snapshot_manager.restore_file_from_latest_snapshot("workflow.yml")
    assert restored is False


def test_snapshot_manager_restore_latest_no_snapshots(project_directory: Path):
    """
    Tests that restore_file_from_latest_snapshot returns False if there
    are no snapshots.
    """
    snapshot_manager = SnapshotManager(project_directory, project_directory / ".snapshots")
    restored = snapshot_manager.restore_file_from_latest_snapshot("workflow.yml")
    assert restored is False