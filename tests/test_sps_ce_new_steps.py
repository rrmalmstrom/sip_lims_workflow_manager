"""
TDD Tests for SPS-CE Workflow New Steps (Steps 1–3)

These tests are written BEFORE the implementation and should FAIL against the
current 6-step templates/sps_workflow.yml. They will PASS once the implementation
agent prepends the 3 new steps to that YAML file.

New steps to be added:
  1. initiate_project       -> SPS_initiate_project_folder_and_make_sort_plate_labels.py  (allow_rerun: true)
  2. process_wga_results    -> SPS_process_WGA_results.py                                 (no allow_rerun)
  3. read_wga_and_make_spits-> SPS_read_WGA_summary_and_make_SPITS.py                    (no allow_rerun)
  4–9. (existing 6 steps unchanged)
"""

from pathlib import Path
import sys
import pytest
import yaml

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import Workflow

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "sps_workflow.yml"


@pytest.fixture(scope="module")
def sps_workflow():
    """Load the SPS-CE workflow from the real template file."""
    return Workflow(TEMPLATE_PATH)


@pytest.fixture(scope="module")
def sps_raw_yaml():
    """Return the raw parsed YAML dict for low-level structure assertions."""
    with open(TEMPLATE_PATH, "r") as f:
        return yaml.safe_load(f)


# ===========================================================================
# 1. YAML Structure Tests
# ===========================================================================

class TestYAMLStructure:
    """Verify the template file loads correctly and has the right top-level shape."""

    def test_template_file_exists(self):
        """The template file must exist on disk."""
        assert TEMPLATE_PATH.exists(), f"Template not found at {TEMPLATE_PATH}"

    def test_workflow_loads_without_error(self, sps_workflow):
        """Workflow object must be constructable without raising."""
        assert sps_workflow is not None

    def test_workflow_name(self, sps_workflow):
        """workflow_name must equal the canonical string."""
        assert sps_workflow.name == "SPS-CE Library Creation Workflow"

    def test_total_step_count_is_nine(self, sps_workflow):
        """After adding 3 new steps the total must be exactly 9."""
        steps = sps_workflow.steps
        assert len(steps) == 9, (
            f"Expected 9 steps, got {len(steps)}. "
            "The 3 new steps (initiate_project, process_wga_results, "
            "read_wga_and_make_spits) may not have been added yet."
        )

    def test_all_step_ids_are_unique(self, sps_workflow):
        """No two steps may share the same id."""
        ids = [step["id"] for step in sps_workflow.steps]
        assert len(ids) == len(set(ids)), f"Duplicate step IDs found: {ids}"


# ===========================================================================
# 2. New Step Presence and Order Tests
# ===========================================================================

class TestNewStepOrder:
    """Verify the 3 new steps appear at positions 0–2 and the first legacy step
    is pushed to position 3."""

    def test_index_0_is_initiate_project(self, sps_workflow):
        steps = sps_workflow.steps
        assert steps[0]["id"] == "initiate_project", (
            f"Expected steps[0].id == 'initiate_project', got '{steps[0]['id']}'"
        )

    def test_index_1_is_process_wga_results(self, sps_workflow):
        steps = sps_workflow.steps
        assert steps[1]["id"] == "process_wga_results", (
            f"Expected steps[1].id == 'process_wga_results', got '{steps[1]['id']}'"
        )

    def test_index_2_is_read_wga_and_make_spits(self, sps_workflow):
        steps = sps_workflow.steps
        assert steps[2]["id"] == "read_wga_and_make_spits", (
            f"Expected steps[2].id == 'read_wga_and_make_spits', got '{steps[2]['id']}'"
        )

    def test_index_3_is_make_library_input_files(self, sps_workflow):
        """The first legacy step must now be at position 3 (0-indexed)."""
        steps = sps_workflow.steps
        assert steps[3]["id"] == "make_library_input_files", (
            f"Expected steps[3].id == 'make_library_input_files', got '{steps[3]['id']}'"
        )


# ===========================================================================
# 3. New Step Script Name Tests
# ===========================================================================

class TestNewStepScriptNames:
    """Each new step must reference the correct script filename."""

    def test_initiate_project_script(self, sps_workflow):
        step = sps_workflow.get_step_by_id("initiate_project")
        assert step is not None, "Step 'initiate_project' not found in workflow"
        assert step["script"] == "SPS_initiate_project_folder_and_make_sort_plate_labels.py", (
            f"Unexpected script: {step.get('script')}"
        )

    def test_process_wga_results_script(self, sps_workflow):
        step = sps_workflow.get_step_by_id("process_wga_results")
        assert step is not None, "Step 'process_wga_results' not found in workflow"
        assert step["script"] == "SPS_process_WGA_results.py", (
            f"Unexpected script: {step.get('script')}"
        )

    def test_read_wga_and_make_spits_script(self, sps_workflow):
        step = sps_workflow.get_step_by_id("read_wga_and_make_spits")
        assert step is not None, "Step 'read_wga_and_make_spits' not found in workflow"
        assert step["script"] == "SPS_read_WGA_summary_and_make_SPITS.py", (
            f"Unexpected script: {step.get('script')}"
        )


# ===========================================================================
# 4. allow_rerun Tests
# ===========================================================================

class TestAllowRerun:
    """Verify allow_rerun flags on the new steps."""

    def test_initiate_project_allow_rerun_is_true(self, sps_workflow):
        step = sps_workflow.get_step_by_id("initiate_project")
        assert step is not None, "Step 'initiate_project' not found in workflow"
        assert step.get("allow_rerun") is True, (
            f"Expected allow_rerun=True for 'initiate_project', got {step.get('allow_rerun')!r}"
        )

    def test_process_wga_results_allow_rerun_is_not_true(self, sps_workflow):
        """process_wga_results must NOT have allow_rerun set to True."""
        step = sps_workflow.get_step_by_id("process_wga_results")
        assert step is not None, "Step 'process_wga_results' not found in workflow"
        assert step.get("allow_rerun") is not True, (
            "Expected allow_rerun to be absent or False for 'process_wga_results', "
            f"got {step.get('allow_rerun')!r}"
        )

    def test_read_wga_and_make_spits_allow_rerun_is_not_true(self, sps_workflow):
        """read_wga_and_make_spits must NOT have allow_rerun set to True."""
        step = sps_workflow.get_step_by_id("read_wga_and_make_spits")
        assert step is not None, "Step 'read_wga_and_make_spits' not found in workflow"
        assert step.get("allow_rerun") is not True, (
            "Expected allow_rerun to be absent or False for 'read_wga_and_make_spits', "
            f"got {step.get('allow_rerun')!r}"
        )


# ===========================================================================
# 5. Existing Steps Preserved Tests
# ===========================================================================

ORIGINAL_STEP_IDS = [
    "make_library_input_files",
    "first_fa_analysis",
    "second_attempt_decision",
    "rework_first_attempt",
    "second_fa_analysis",
    "conclude_fa_analysis",
]


class TestExistingStepsPreserved:
    """All 6 original step IDs must still be present and unchanged."""

    @pytest.mark.parametrize("step_id", ORIGINAL_STEP_IDS)
    def test_original_step_id_present(self, sps_workflow, step_id):
        step = sps_workflow.get_step_by_id(step_id)
        assert step is not None, (
            f"Original step '{step_id}' is missing from the workflow after adding new steps."
        )

    def test_make_library_input_files_script_unchanged(self, sps_workflow):
        """The first legacy step must still point to its original script."""
        step = sps_workflow.get_step_by_id("make_library_input_files")
        assert step is not None
        assert step["script"] == "SPS_make_illumina_index_and_FA_files_NEW.py", (
            f"Script changed unexpectedly: {step.get('script')}"
        )

    def test_first_fa_analysis_script_unchanged(self, sps_workflow):
        step = sps_workflow.get_step_by_id("first_fa_analysis")
        assert step is not None
        assert step["script"] == "SPS_first_FA_output_analysis_NEW.py"

    def test_second_attempt_decision_script_unchanged(self, sps_workflow):
        step = sps_workflow.get_step_by_id("second_attempt_decision")
        assert step is not None
        assert step["script"] == "decision_second_attempt.py"

    def test_rework_first_attempt_script_unchanged(self, sps_workflow):
        step = sps_workflow.get_step_by_id("rework_first_attempt")
        assert step is not None
        assert step["script"] == "SPS_rework_first_attempt_NEW.py"

    def test_second_fa_analysis_script_unchanged(self, sps_workflow):
        step = sps_workflow.get_step_by_id("second_fa_analysis")
        assert step is not None
        assert step["script"] == "SPS_second_FA_output_analysis_NEW.py"

    def test_conclude_fa_analysis_script_unchanged(self, sps_workflow):
        step = sps_workflow.get_step_by_id("conclude_fa_analysis")
        assert step is not None
        assert step["script"] == "SPS_conclude_FA_analysis_generate_ESP_smear_file.py"


# ===========================================================================
# 6. Success Marker Filename Tests
# ===========================================================================

class TestSuccessMarkerFilenames:
    """
    The success marker is derived via Path(script_name).stem + '.success'.
    Verify each new script produces the expected marker filename.
    """

    def test_initiate_project_marker_filename(self, sps_workflow):
        step = sps_workflow.get_step_by_id("initiate_project")
        assert step is not None, "Step 'initiate_project' not found"
        script = step["script"]
        marker = Path(script).stem + ".success"
        assert marker == "SPS_initiate_project_folder_and_make_sort_plate_labels.success", (
            f"Unexpected marker filename: {marker!r}"
        )

    def test_process_wga_results_marker_filename(self, sps_workflow):
        step = sps_workflow.get_step_by_id("process_wga_results")
        assert step is not None, "Step 'process_wga_results' not found"
        script = step["script"]
        marker = Path(script).stem + ".success"
        assert marker == "SPS_process_WGA_results.success", (
            f"Unexpected marker filename: {marker!r}"
        )

    def test_read_wga_and_make_spits_marker_filename(self, sps_workflow):
        step = sps_workflow.get_step_by_id("read_wga_and_make_spits")
        assert step is not None, "Step 'read_wga_and_make_spits' not found"
        script = step["script"]
        marker = Path(script).stem + ".success"
        assert marker == "SPS_read_WGA_summary_and_make_SPITS.success", (
            f"Unexpected marker filename: {marker!r}"
        )


# ===========================================================================
# 7. Workflow Class Integration Tests
# ===========================================================================

class TestWorkflowClassIntegration:
    """Verify the Workflow class API behaves correctly with the updated YAML."""

    def test_get_step_by_id_initiate_project(self, sps_workflow):
        """get_step_by_id must return the correct dict for the new step."""
        step = sps_workflow.get_step_by_id("initiate_project")
        assert step is not None
        assert step["id"] == "initiate_project"
        assert step["script"] == "SPS_initiate_project_folder_and_make_sort_plate_labels.py"

    def test_get_step_by_id_nonexistent_returns_none(self, sps_workflow):
        """get_step_by_id must return None for an unknown step ID."""
        result = sps_workflow.get_step_by_id("nonexistent_id")
        assert result is None

    def test_get_all_steps_returns_nine_items(self, sps_workflow):
        """get_all_steps() must return a list of exactly 9 step dicts.

        NOTE: This also requires the implementation agent to add a
        get_all_steps() method to src/core.py Workflow class that returns
        self.steps.
        """
        steps = sps_workflow.get_all_steps()
        assert isinstance(steps, list)
        assert len(steps) == 9, (
            f"get_all_steps() returned {len(steps)} items; expected 9."
        )

    def test_get_all_steps_returns_dicts(self, sps_workflow):
        """Every item returned by get_all_steps() must be a dict with at least 'id'.

        NOTE: Requires get_all_steps() method on Workflow (see above).
        """
        for step in sps_workflow.get_all_steps():
            assert isinstance(step, dict), f"Step is not a dict: {step!r}"
            assert "id" in step, f"Step dict missing 'id' key: {step!r}"
