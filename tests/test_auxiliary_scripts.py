"""
Tests for the Auxiliary Scripts feature.

Covers:
- Workflow YAML parsing: auxiliary_scripts key loaded correctly
- Workflow.get_auxiliary_script_by_id() lookup
- Project.run_auxiliary_script() — snapshot taken, script launched
- Project.handle_auxiliary_result() — success path: artifacts deleted, state unchanged
- Project.handle_auxiliary_result() — failure path: rollback fired, state unchanged
- workflow_state.json is NEVER modified during any auxiliary script operation
"""

import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from dataclasses import dataclass

import pytest
import yaml

# ---------------------------------------------------------------------------
# Minimal stubs so we can import src.core without a full environment
# ---------------------------------------------------------------------------

# Stub RunResult so we don't need the full logic module
@dataclass
class _RunResult:
    success: bool
    return_code: int = 0
    output: str = ""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_project(tmp_path):
    """
    Creates a minimal project folder with:
    - workflow.yml containing one workflow step and one auxiliary script
    - workflow_state.json with the step marked as pending
    - scripts/ directory with a mock auxiliary script
    - .workflow_status/ directory
    - .snapshots/ directory
    """
    # workflow.yml
    workflow_data = {
        "workflow_name": "Test Workflow",
        "steps": [
            {"id": "step_one", "name": "Step One", "script": "step_one.py"}
        ],
        "auxiliary_scripts": [
            {"id": "aux_tool", "name": "Aux Tool", "script": "aux_tool.py"}
        ],
    }
    workflow_file = tmp_path / "workflow.yml"
    with open(workflow_file, "w") as f:
        yaml.dump(workflow_data, f)

    # workflow_state.json
    state_file = tmp_path / "workflow_state.json"
    state_file.write_text(json.dumps({"step_one": "pending"}))

    # scripts/ directory with mock scripts
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "step_one.py").write_text(
        'SNAPSHOT_ITEMS = []\nprint("step one")\n'
    )
    (scripts_dir / "aux_tool.py").write_text(
        'print("aux tool")\n'
    )

    # .workflow_status/ and .snapshots/
    (tmp_path / ".workflow_status").mkdir()
    (tmp_path / ".snapshots").mkdir()

    return tmp_path


@pytest.fixture()
def workflow_obj(tmp_project):
    """Returns a Workflow instance loaded from the tmp_project."""
    from src.core import Workflow
    return Workflow(tmp_project / "workflow.yml")


@pytest.fixture()
def project_obj(tmp_project):
    """Returns a Project instance for the tmp_project."""
    from src.core import Project
    return Project(tmp_project, script_path=tmp_project / "scripts")


# ---------------------------------------------------------------------------
# Workflow class tests
# ---------------------------------------------------------------------------

class TestWorkflowAuxiliaryScriptsParsing:

    def test_auxiliary_scripts_attribute_populated(self, workflow_obj):
        """Workflow.auxiliary_scripts is loaded from the YAML."""
        assert len(workflow_obj.auxiliary_scripts) == 1
        assert workflow_obj.auxiliary_scripts[0]["id"] == "aux_tool"
        assert workflow_obj.auxiliary_scripts[0]["name"] == "Aux Tool"
        assert workflow_obj.auxiliary_scripts[0]["script"] == "aux_tool.py"

    def test_auxiliary_scripts_defaults_to_empty_list(self, tmp_path):
        """Workflow.auxiliary_scripts is [] when key is absent from YAML."""
        from src.core import Workflow
        workflow_data = {
            "workflow_name": "No Aux",
            "steps": [{"id": "s1", "name": "S1", "script": "s1.py"}],
        }
        wf_file = tmp_path / "workflow.yml"
        with open(wf_file, "w") as f:
            yaml.dump(workflow_data, f)
        wf = Workflow(wf_file)
        assert wf.auxiliary_scripts == []

    def test_auxiliary_scripts_empty_list_value(self, tmp_path):
        """Workflow.auxiliary_scripts is [] when key is present but empty."""
        from src.core import Workflow
        workflow_data = {
            "workflow_name": "Empty Aux",
            "steps": [{"id": "s1", "name": "S1", "script": "s1.py"}],
            "auxiliary_scripts": [],
        }
        wf_file = tmp_path / "workflow.yml"
        with open(wf_file, "w") as f:
            yaml.dump(workflow_data, f)
        wf = Workflow(wf_file)
        assert wf.auxiliary_scripts == []

    def test_steps_unaffected_by_auxiliary_scripts(self, workflow_obj):
        """Adding auxiliary_scripts does not change the steps list."""
        assert len(workflow_obj.steps) == 1
        assert workflow_obj.steps[0]["id"] == "step_one"


class TestGetAuxiliaryScriptById:

    def test_returns_correct_entry(self, workflow_obj):
        result = workflow_obj.get_auxiliary_script_by_id("aux_tool")
        assert result is not None
        assert result["id"] == "aux_tool"
        assert result["script"] == "aux_tool.py"

    def test_returns_none_for_unknown_id(self, workflow_obj):
        result = workflow_obj.get_auxiliary_script_by_id("nonexistent")
        assert result is None

    def test_returns_none_for_workflow_step_id(self, workflow_obj):
        """Workflow step IDs should not be found in auxiliary_scripts."""
        result = workflow_obj.get_auxiliary_script_by_id("step_one")
        assert result is None


# ---------------------------------------------------------------------------
# Project.run_auxiliary_script() tests
# ---------------------------------------------------------------------------

class TestRunAuxiliaryScript:

    def test_raises_for_unknown_aux_id(self, project_obj):
        with pytest.raises(ValueError, match="not found in workflow"):
            project_obj.run_auxiliary_script("nonexistent_aux")

    def test_raises_for_missing_script_file(self, project_obj, tmp_project):
        """If the script file doesn't exist in scripts/, raise FileNotFoundError."""
        # Remove the aux script file
        (tmp_project / "scripts" / "aux_tool.py").unlink()
        with pytest.raises(FileNotFoundError, match="Auxiliary script not found"):
            project_obj.run_auxiliary_script("aux_tool")

    def test_snapshot_taken_before_launch(self, project_obj, tmp_project):
        """A manifest and snapshot ZIP are created before the script runs."""
        with patch.object(project_obj.script_runner, "run") as mock_run:
            project_obj.run_auxiliary_script("aux_tool")

        snapshots_dir = tmp_project / ".snapshots"
        manifest_files = list(snapshots_dir.glob("aux_tool_run_1_manifest.json"))
        snapshot_files = list(snapshots_dir.glob("aux_tool_run_1_*.zip"))

        assert len(manifest_files) == 1, "Manifest should be written before launch"
        assert len(snapshot_files) == 1, "Snapshot ZIP should be written before launch"

    def test_script_runner_called_with_correct_script(self, project_obj):
        """ScriptRunner.run() is called with the auxiliary script filename."""
        with patch.object(project_obj.script_runner, "run") as mock_run:
            project_obj.run_auxiliary_script("aux_tool")
        mock_run.assert_called_once_with("aux_tool.py", args=[])

    def test_workflow_state_not_modified_during_run(self, project_obj, tmp_project):
        """workflow_state.json is not touched when run_auxiliary_script is called."""
        state_before = (tmp_project / "workflow_state.json").read_text()
        with patch.object(project_obj.script_runner, "run"):
            project_obj.run_auxiliary_script("aux_tool")
        state_after = (tmp_project / "workflow_state.json").read_text()
        assert state_before == state_after


# ---------------------------------------------------------------------------
# Project.handle_auxiliary_result() — success path
# ---------------------------------------------------------------------------

class TestHandleAuxiliaryResultSuccess:

    def _setup_pre_run_artifacts(self, project_obj, tmp_project):
        """Simulate the artifacts that run_auxiliary_script() creates."""
        with patch.object(project_obj.script_runner, "run"):
            project_obj.run_auxiliary_script("aux_tool")
        # Write the flat success marker (as the script would)
        status_dir = tmp_project / ".workflow_status"
        (status_dir / "aux_tool.success").write_text("")

    def test_success_deletes_snapshot_zip(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=True)
        project_obj.handle_auxiliary_result("aux_tool", result)
        zips = list((tmp_project / ".snapshots").glob("aux_tool_run_1_*.zip"))
        assert len(zips) == 0, "Snapshot ZIP should be deleted on success"

    def test_success_deletes_manifest(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=True)
        project_obj.handle_auxiliary_result("aux_tool", result)
        manifests = list((tmp_project / ".snapshots").glob("aux_tool_run_1_manifest.json"))
        assert len(manifests) == 0, "Manifest should be deleted on success"

    def test_success_deletes_success_marker(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=True)
        project_obj.handle_auxiliary_result("aux_tool", result)
        status_dir = tmp_project / ".workflow_status"
        assert not (status_dir / "aux_tool.success").exists()
        assert not (status_dir / "aux_tool.run_1.success").exists()

    def test_success_does_not_modify_workflow_state(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        state_before = (tmp_project / "workflow_state.json").read_text()
        result = _RunResult(success=True)
        project_obj.handle_auxiliary_result("aux_tool", result)
        state_after = (tmp_project / "workflow_state.json").read_text()
        assert state_before == state_after

    def test_success_step_one_state_unchanged(self, project_obj, tmp_project):
        """The workflow step state is not affected by auxiliary script success."""
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=True)
        project_obj.handle_auxiliary_result("aux_tool", result)
        state = json.loads((tmp_project / "workflow_state.json").read_text())
        assert state["step_one"] == "pending"


# ---------------------------------------------------------------------------
# Project.handle_auxiliary_result() — failure path
# ---------------------------------------------------------------------------

class TestHandleAuxiliaryResultFailure:

    def _setup_pre_run_artifacts(self, project_obj, tmp_project):
        """Simulate the artifacts that run_auxiliary_script() creates."""
        with patch.object(project_obj.script_runner, "run"):
            project_obj.run_auxiliary_script("aux_tool")
        # Simulate a file the script partially created
        (tmp_project / "partial_output.txt").write_text("partial")

    def test_failure_triggers_rollback(self, project_obj, tmp_project):
        """On failure, restore_snapshot is called to roll back partial changes."""
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=False)
        # After rollback, the partial file should be removed
        # (restore_snapshot deletes files not in the pre-run manifest)
        project_obj.handle_auxiliary_result("aux_tool", result)
        assert not (tmp_project / "partial_output.txt").exists(), \
            "Partial file should be removed by rollback"

    def test_failure_deletes_snapshot_after_rollback(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=False)
        project_obj.handle_auxiliary_result("aux_tool", result)
        zips = list((tmp_project / ".snapshots").glob("aux_tool_run_1_*.zip"))
        assert len(zips) == 0, "Snapshot ZIP should be deleted after rollback"

    def test_failure_deletes_manifest_after_rollback(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=False)
        project_obj.handle_auxiliary_result("aux_tool", result)
        manifests = list((tmp_project / ".snapshots").glob("aux_tool_run_1_manifest.json"))
        assert len(manifests) == 0, "Manifest should be deleted after rollback"

    def test_failure_does_not_modify_workflow_state(self, project_obj, tmp_project):
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        state_before = (tmp_project / "workflow_state.json").read_text()
        result = _RunResult(success=False)
        project_obj.handle_auxiliary_result("aux_tool", result)
        state_after = (tmp_project / "workflow_state.json").read_text()
        assert state_before == state_after

    def test_failure_step_one_state_unchanged(self, project_obj, tmp_project):
        """The workflow step state is not affected by auxiliary script failure."""
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        result = _RunResult(success=False)
        project_obj.handle_auxiliary_result("aux_tool", result)
        state = json.loads((tmp_project / "workflow_state.json").read_text())
        assert state["step_one"] == "pending"

    def test_failure_cleans_up_stale_markers(self, project_obj, tmp_project):
        """Any stale success markers left by the failed script are removed."""
        self._setup_pre_run_artifacts(project_obj, tmp_project)
        # Simulate a stale flat marker the script wrote before failing
        status_dir = tmp_project / ".workflow_status"
        (status_dir / "aux_tool.success").write_text("")
        result = _RunResult(success=False)
        project_obj.handle_auxiliary_result("aux_tool", result)
        assert not (status_dir / "aux_tool.success").exists()
        assert not (status_dir / "aux_tool.run_1.success").exists()


# ---------------------------------------------------------------------------
# Two-factor check: exit code 0 but no marker = failure
# ---------------------------------------------------------------------------

class TestAuxiliaryTwoFactorCheck:

    def test_exit_code_zero_no_marker_treated_as_failure(self, project_obj, tmp_project):
        """
        If the script exits with code 0 but writes no .success marker,
        handle_auxiliary_result() must treat it as a failure and roll back.
        """
        with patch.object(project_obj.script_runner, "run"):
            project_obj.run_auxiliary_script("aux_tool")
        # Simulate a partial file — no marker written
        (tmp_project / "partial_output.txt").write_text("partial")

        result = _RunResult(success=True)  # exit code 0
        # No marker file written — should trigger rollback
        project_obj.handle_auxiliary_result("aux_tool", result)

        # Snapshot and manifest should be cleaned up
        zips = list((tmp_project / ".snapshots").glob("aux_tool_run_1_*.zip"))
        assert len(zips) == 0
        # workflow_state.json must be unchanged
        state = json.loads((tmp_project / "workflow_state.json").read_text())
        assert state["step_one"] == "pending"

    def test_exit_code_nonzero_with_marker_treated_as_failure(self, project_obj, tmp_project):
        """
        If the script exits with non-zero but somehow wrote a marker,
        handle_auxiliary_result() must treat it as a failure and roll back.
        """
        with patch.object(project_obj.script_runner, "run"):
            project_obj.run_auxiliary_script("aux_tool")
        # Write a marker even though exit code is non-zero
        status_dir = tmp_project / ".workflow_status"
        (status_dir / "aux_tool.success").write_text("")

        result = _RunResult(success=False)  # non-zero exit
        project_obj.handle_auxiliary_result("aux_tool", result)

        # workflow_state.json must be unchanged
        state = json.loads((tmp_project / "workflow_state.json").read_text())
        assert state["step_one"] == "pending"


# ---------------------------------------------------------------------------
# YAML template validation
# ---------------------------------------------------------------------------

class TestWorkflowYamlTemplates:
    """Verify that all three workflow YAML templates have the auxiliary_scripts key."""

    TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

    @pytest.mark.parametrize("template_name", [
        "sip_workflow.yml",
        "sps_workflow.yml",
        "CapsuleSorting_workflow.yml",
    ])
    def test_template_has_auxiliary_scripts_key(self, template_name):
        template_path = self.TEMPLATES_DIR / template_name
        assert template_path.exists(), f"Template not found: {template_path}"
        with open(template_path) as f:
            data = yaml.safe_load(f)
        assert "auxiliary_scripts" in data, \
            f"{template_name} is missing the 'auxiliary_scripts' key"

    @pytest.mark.parametrize("template_name", [
        "sip_workflow.yml",
        "sps_workflow.yml",
        "CapsuleSorting_workflow.yml",
    ])
    def test_template_auxiliary_scripts_is_list(self, template_name):
        template_path = self.TEMPLATES_DIR / template_name
        with open(template_path) as f:
            data = yaml.safe_load(f)
        aux = data.get("auxiliary_scripts")
        assert isinstance(aux, list), \
            f"{template_name}: auxiliary_scripts must be a list, got {type(aux)}"

    @pytest.mark.parametrize("template_name", [
        "sip_workflow.yml",
        "sps_workflow.yml",
        "CapsuleSorting_workflow.yml",
    ])
    def test_template_steps_still_present(self, template_name):
        """Adding auxiliary_scripts must not remove or corrupt the steps list."""
        template_path = self.TEMPLATES_DIR / template_name
        with open(template_path) as f:
            data = yaml.safe_load(f)
        assert "steps" in data
        assert len(data["steps"]) > 0, f"{template_name}: steps list must not be empty"
