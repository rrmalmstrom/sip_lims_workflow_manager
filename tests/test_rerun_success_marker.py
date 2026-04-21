"""
Tests for the run-number-specific success marker fix and the rerun-failure
state-preservation fix.

Bug 1 (stale marker): When a step with allow_rerun=True was re-run and the
script failed, the stale .success marker from the previous successful run was
still present on disk.  _check_success_marker() found it and incorrectly
reported success, causing the workflow state to be set to "completed" even
though the rerun failed.

Fix (Option A): handle_step_result() renames the flat ``<script_stem>.success``
written by the individual script to ``<script_stem>.run_<N>.success`` immediately
after the script exits.  _check_success_marker() now looks for the run-number-
specific marker, so a stale marker from run N-1 is never confused with a fresh
marker from run N.

Bug 2 (state regression): After a failed rerun of an already-completed step,
handle_step_result() called update_state(step_id, "pending") unconditionally.
This overwrote the "completed" state that the snapshot restore had just put back,
making the step appear to have never succeeded.

Fix: update_state("pending") is now only called for first-run failures
(is_first_run is True).  For rerun failures (is_first_run is False), the
rollback already restored workflow_state.json to "completed" — we leave it alone.

These tests exercise both fixes at the unit level without launching real scripts.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core import Project
from src.logic import RunResult


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

WORKFLOW_YAML = """
workflow_name: "Test Workflow"
steps:
  - id: rerun_step
    name: "Re-runnable Step"
    script: "mock_rerun_script.py"
    allow_rerun: true
  - id: normal_step
    name: "Normal Step"
    script: "mock_normal_script.py"
    allow_rerun: false
"""

SNAPSHOT_ITEMS_SCRIPT = """\
SNAPSHOT_ITEMS = []

def main():
    pass

if __name__ == "__main__":
    main()
"""


@pytest.fixture
def project_dir():
    """Temporary project directory with a minimal workflow and mock scripts."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "workflow.yml").write_text(WORKFLOW_YAML)

    scripts_dir = tmp / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "mock_rerun_script.py").write_text(SNAPSHOT_ITEMS_SCRIPT)
    (scripts_dir / "mock_normal_script.py").write_text(SNAPSHOT_ITEMS_SCRIPT)

    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def project(project_dir):
    return Project(project_dir, script_path=project_dir / "scripts")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _place_flat_marker(project: Project, script_stem: str) -> Path:
    """Simulate a script writing its flat .success marker."""
    status_dir = project.path / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / f"{script_stem}.success"
    marker.write_text("success")
    return marker


def _place_run_marker(project: Project, script_stem: str, run_number: int) -> Path:
    """Place a run-number-specific marker directly (simulates a prior completed run)."""
    status_dir = project.path / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / f"{script_stem}.run_{run_number}.success"
    marker.write_text("success")
    return marker


def _simulate_snapshot(project: Project, step_id: str, run_number: int):
    """
    Write a minimal snapshot ZIP + manifest so get_current_run_number() returns run_number.

    The ZIP includes the current workflow_state.json (if it exists) so that
    restore_snapshot() puts it back correctly — mirroring what the real
    take_selective_snapshot() does (workflow_state.json is not excluded from
    manifest scans, so it is treated as a regular project file and included
    when it is listed in SNAPSHOT_ITEMS or detected as newly-added).
    """
    import zipfile, json, datetime
    snap_dir = project.path / ".snapshots"
    snap_dir.mkdir(exist_ok=True)

    zip_path = snap_dir / f"{step_id}_run_{run_number}_snapshot.zip"
    state_file = project.path / "workflow_state.json"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Include workflow_state.json so rollback can restore it correctly.
        # In the real system, workflow_state.json is captured in the snapshot
        # because it is a regular project file (not in _MANIFEST_EXCLUDE_PATTERNS).
        if state_file.exists():
            zf.write(state_file, "workflow_state.json")

    # Record workflow_state.json in the manifest files list so the restore
    # logic knows it was present before the run (not "newly created").
    current_files = ["workflow_state.json"] if state_file.exists() else []

    manifest = {
        "step_id": step_id,
        "run_number": run_number,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "files": current_files,
        "directories": [],
        "excluded_patterns": [],
    }
    manifest_path = snap_dir / f"{step_id}_run_{run_number}_manifest.json"
    manifest_path.write_text(json.dumps(manifest))


# ---------------------------------------------------------------------------
# _check_success_marker unit tests
# ---------------------------------------------------------------------------

class TestCheckSuccessMarker:
    """Unit tests for Project._check_success_marker()."""

    def test_returns_true_when_run_marker_exists(self, project):
        """Run-number-specific marker present → True."""
        _place_run_marker(project, "mock_rerun_script", 1)
        assert project._check_success_marker("mock_rerun_script.py", 1) is True

    def test_returns_false_when_no_marker_at_all(self, project):
        """No marker on disk → False."""
        assert project._check_success_marker("mock_rerun_script.py", 1) is False

    def test_stale_marker_from_prior_run_is_rejected(self, project):
        """Marker for run 1 must NOT satisfy a check for run 2."""
        _place_run_marker(project, "mock_rerun_script", 1)
        # Check for run 2 — should be False even though run 1 marker exists
        assert project._check_success_marker("mock_rerun_script.py", 2) is False

    def test_flat_marker_is_not_accepted(self, project):
        """A flat .success file (not yet renamed) must NOT satisfy the check."""
        _place_flat_marker(project, "mock_rerun_script")
        assert project._check_success_marker("mock_rerun_script.py", 1) is False

    def test_returns_true_when_script_name_is_empty(self, project):
        """Empty script name → True (no marker to check, assume OK)."""
        assert project._check_success_marker("", 1) is True

    def test_correct_run_marker_accepted_stale_also_present(self, project):
        """Both run 1 (stale) and run 2 (current) markers present → True for run 2."""
        _place_run_marker(project, "mock_rerun_script", 1)
        _place_run_marker(project, "mock_rerun_script", 2)
        assert project._check_success_marker("mock_rerun_script.py", 2) is True


# ---------------------------------------------------------------------------
# handle_step_result marker-rename tests
# ---------------------------------------------------------------------------

class TestHandleStepResultMarkerRename:
    """
    Tests that handle_step_result() correctly renames the flat marker to the
    run-number-specific form and uses it for success detection.
    """

    def _make_result(self, success: bool) -> RunResult:
        return RunResult(
            success=success,
            stdout="",
            stderr="",
            return_code=0 if success else 1,
        )

    def test_success_run1_renames_flat_marker(self, project, project_dir):
        """
        First run succeeds: flat marker is renamed to .run_1.success and
        step is marked completed.
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Set up: snapshot for run 1, flat marker written by script
        _simulate_snapshot(project, step_id, 1)
        _place_flat_marker(project, script_stem)

        project.handle_step_result(step_id, self._make_result(success=True))

        status_dir = project_dir / ".workflow_status"
        # Flat marker should be gone (renamed)
        assert not (status_dir / f"{script_stem}.success").exists()
        # Run-1 marker should exist
        assert (status_dir / f"{script_stem}.run_1.success").exists()
        # Step should be completed
        assert project.get_state(step_id) == "completed"

    def test_rerun_fails_stale_marker_does_not_cause_false_success(self, project, project_dir):
        """
        Core bug-1 regression test (stale marker).

        Run 1 succeeded (leaving .run_1.success on disk).
        Run 2 fails (script does NOT write a flat .success marker).
        handle_step_result() must NOT find the stale run_1 marker and must
        NOT mark the step as completed.

        With bug-2 fix: the step remains "completed" (reflecting run 1's
        success) rather than being set to "pending".
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Simulate run 1 having completed: run_1 marker exists, state=completed
        _simulate_snapshot(project, step_id, 1)
        _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Simulate run 2 starting: new snapshot written
        _simulate_snapshot(project, step_id, 2)
        # Script fails — no flat marker written

        project.handle_step_result(step_id, self._make_result(success=False))

        # Step must remain "completed" (not falsely set to "pending") because
        # run 1 succeeded and the failed run 2 is rolled back.
        assert project.get_state(step_id) == "completed", (
            "Step should remain completed after a failed rerun — "
            "the prior successful run is still valid"
        )

    def test_rerun_succeeds_new_marker_accepted(self, project, project_dir):
        """
        Run 1 succeeded (leaving .run_1.success).
        Run 2 also succeeds (script writes flat .success).
        handle_step_result() renames it to .run_2.success and marks completed.
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Simulate run 1 completed
        _simulate_snapshot(project, step_id, 1)
        _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Simulate run 2: new snapshot + script writes flat marker
        _simulate_snapshot(project, step_id, 2)
        _place_flat_marker(project, script_stem)

        project.handle_step_result(step_id, self._make_result(success=True))

        status_dir = project_dir / ".workflow_status"
        # Flat marker renamed away
        assert not (status_dir / f"{script_stem}.success").exists()
        # Run-2 marker present
        assert (status_dir / f"{script_stem}.run_2.success").exists()
        # Step completed
        assert project.get_state(step_id) == "completed"

    def test_exit_code_failure_without_marker_marks_pending(self, project, project_dir):
        """
        First-run: script exits with non-zero code and writes no marker → step pending.
        """
        step_id = "rerun_step"
        _simulate_snapshot(project, step_id, 1)
        # Step starts as pending (first run), no flat marker placed

        project.handle_step_result(step_id, self._make_result(success=False))

        assert project.get_state(step_id) == "pending"

    def test_exit_code_success_without_marker_marks_pending(self, project, project_dir):
        """
        First-run: script exits with code 0 but writes no marker → step pending.
        (Catches scripts that crash after the exit call but before marker write.)
        """
        step_id = "rerun_step"
        _simulate_snapshot(project, step_id, 1)
        # Step starts as pending (first run), no flat marker placed

        project.handle_step_result(step_id, self._make_result(success=True))

        assert project.get_state(step_id) == "pending"


# ---------------------------------------------------------------------------
# Rerun failure state-preservation tests (Bug 2 fix)
# ---------------------------------------------------------------------------

class TestRerunFailureStatePreservation:
    """
    Tests that a failed rerun of an already-completed step leaves the step
    in "completed" state (reflecting the prior successful run) rather than
    resetting it to "pending".

    Bug: handle_step_result() called update_state(step_id, "pending")
    unconditionally after any failure.  For reruns, the snapshot restore had
    already put workflow_state.json back to "completed"; the unconditional
    pending call then corrupted that restored state.

    Fix: update_state("pending") is only called when is_first_run is True.
    """

    def _make_result(self, success: bool) -> RunResult:
        return RunResult(
            success=success,
            stdout="",
            stderr="",
            return_code=0 if success else 1,
        )

    def test_rerun_failure_step_remains_completed(self, project, project_dir):
        """
        Core regression test for Bug 2.

        Step was previously completed (run 1 succeeded).
        Run 2 fails (no marker, non-zero exit).
        After rollback, step must remain "completed".
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Simulate run 1 completed: snapshot + marker + state
        _simulate_snapshot(project, step_id, 1)
        _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Simulate run 2 snapshot (written before script starts)
        _simulate_snapshot(project, step_id, 2)
        # Script fails — no flat marker written

        project.handle_step_result(step_id, self._make_result(success=False))

        assert project.get_state(step_id) == "completed", (
            "After a failed rerun, step should remain completed — "
            "the prior successful run is still valid"
        )

    def test_rerun_failure_completion_order_preserved(self, project, project_dir):
        """
        After a failed rerun, _completion_order must still contain the entry
        from the prior successful run (not be reduced).
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Run 1 completed
        _simulate_snapshot(project, step_id, 1)
        _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Verify completion order has one entry before run 2
        assert project.state_manager.get_completion_order().count(step_id) == 1

        # Run 2 fails
        _simulate_snapshot(project, step_id, 2)

        project.handle_step_result(step_id, self._make_result(success=False))

        # Completion order must still have exactly one entry (from run 1)
        order = project.state_manager.get_completion_order()
        assert order.count(step_id) == 1, (
            f"_completion_order should have 1 entry for {step_id} after failed rerun, "
            f"got: {order}"
        )

    def test_first_run_failure_still_marks_pending(self, project, project_dir):
        """
        First-run failure (step was pending) must still result in "pending".
        The fix must not change behavior for first-run failures.
        """
        step_id = "rerun_step"

        # Step starts as pending (no prior completion)
        _simulate_snapshot(project, step_id, 1)
        # Script fails — no flat marker

        project.handle_step_result(step_id, self._make_result(success=False))

        assert project.get_state(step_id) == "pending", (
            "First-run failure should leave step as pending"
        )

    def test_rerun_failure_with_exit_code_zero_remains_completed(self, project, project_dir):
        """
        Rerun where script exits 0 but writes no marker (two-factor failure).
        Step was previously completed → must remain completed after rollback.
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Run 1 completed
        _simulate_snapshot(project, step_id, 1)
        _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Run 2: exit code 0 but no marker written
        _simulate_snapshot(project, step_id, 2)

        # exit_code_success=True but marker_file_success=False → actual_success=False
        project.handle_step_result(step_id, self._make_result(success=True))

        assert project.get_state(step_id) == "completed", (
            "Rerun with exit-0 but no marker should leave step completed "
            "(prior run still valid)"
        )

    def test_rerun_success_after_prior_completion_increments_order(self, project, project_dir):
        """
        Successful rerun of an already-completed step must add another entry
        to _completion_order (not replace the existing one).
        """
        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        # Run 1 completed
        _simulate_snapshot(project, step_id, 1)
        _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        assert project.state_manager.get_completion_order().count(step_id) == 1

        # Run 2 succeeds
        _simulate_snapshot(project, step_id, 2)
        # Place flat marker (script writes it), handle_step_result renames it
        status_dir = project.path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        (status_dir / f"{script_stem}.success").write_text("success")

        project.handle_step_result(step_id, self._make_result(success=True))

        assert project.get_state(step_id) == "completed"
        order = project.state_manager.get_completion_order()
        assert order.count(step_id) == 2, (
            f"_completion_order should have 2 entries after two successful runs, got: {order}"
        )


# ---------------------------------------------------------------------------
# terminate_script marker cleanup tests
# ---------------------------------------------------------------------------

class TestTerminateScriptMarkerCleanup:
    """
    Tests that terminate_script() removes both the flat and run-number-specific
    success markers so a terminated run cannot leave a stale marker behind.
    """

    def test_terminate_removes_flat_marker(self, project, project_dir):
        """
        If the script wrote a flat marker before being killed,
        terminate_script() must remove it.
        """
        from unittest.mock import patch

        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        _simulate_snapshot(project, step_id, 1)
        flat_marker = _place_flat_marker(project, script_stem)

        # Patch is_running to return True so terminate_script proceeds,
        # and patch the actual stop() to avoid needing a real process.
        with patch.object(project.script_runner, 'is_running', return_value=True):
            with patch.object(project.script_runner, 'terminate'):
                with patch.object(project.snapshot_manager, 'snapshot_exists', return_value=False):
                    project.terminate_script(step_id)

        assert not flat_marker.exists(), "Flat marker should be removed by terminate_script()"

    def test_terminate_removes_run_specific_marker(self, project, project_dir):
        """
        If handle_step_result() already renamed the marker to .run_N.success
        before terminate was called, terminate_script() must remove it.
        """
        from unittest.mock import patch

        step_id = "rerun_step"
        script_stem = "mock_rerun_script"

        _simulate_snapshot(project, step_id, 1)
        run_marker = _place_run_marker(project, script_stem, 1)

        with patch.object(project.script_runner, 'is_running', return_value=True):
            with patch.object(project.script_runner, 'terminate'):
                with patch.object(project.snapshot_manager, 'snapshot_exists', return_value=False):
                    project.terminate_script(step_id)

        assert not run_marker.exists(), "Run-specific marker should be removed by terminate_script()"

    def test_terminate_marks_step_pending(self, project, project_dir):
        """terminate_script() must always leave the step in pending state."""
        from unittest.mock import patch

        step_id = "rerun_step"
        _simulate_snapshot(project, step_id, 1)
        project.update_state(step_id, "completed")

        with patch.object(project.script_runner, 'is_running', return_value=True):
            with patch.object(project.script_runner, 'terminate'):
                with patch.object(project.snapshot_manager, 'snapshot_exists', return_value=False):
                    project.terminate_script(step_id)

        assert project.get_state(step_id) == "pending"
