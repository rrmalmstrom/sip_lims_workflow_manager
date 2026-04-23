"""
Tests for the manual undo success-marker cleanup fix.

Bug: perform_undo() in app.py only tried to delete the flat
``<script_stem>.success`` marker.  However, handle_step_result() renames
that flat marker to ``<script_stem>.run_<N>.success`` immediately after the
script exits, so the flat marker no longer exists at undo time.  The result
was that run-number-specific markers were never cleaned up during manual undo,
leaving stale markers in .workflow_status/ that could confuse future runs.

Fix (both cases):
  Case 1 — effective_run == 1 (full undo):
    Delete ``<script_stem>.run_1.success`` (current format).
    Also attempt ``<script_stem>.success`` as a safety net for legacy projects
    completed before the run-number rename system was introduced.

  Case 2 — effective_run > 1 (granular undo of a rerun):
    Delete ``<script_stem>.run_<N>.success`` for the run being undone.
    Previously no marker cleanup was attempted at all in this branch.

These tests use the same perform_undo_test() helper defined in
test_chronological_undo_ordering.py, imported here to avoid duplication.
"""

import pytest
import tempfile
import shutil
import zipfile
import json
import datetime
from pathlib import Path

from src.core import Project
from src.logic import RunResult

# Re-use the Streamlit-free undo helper from the chronological ordering tests.
from tests.test_chronological_undo_ordering import perform_undo_test


# ---------------------------------------------------------------------------
# Shared workflow YAML and helpers
# ---------------------------------------------------------------------------

WORKFLOW_YAML = """
workflow_name: "Undo Marker Cleanup Test Workflow"
steps:
  - id: step_a
    name: "Step A (rerunnable)"
    script: "script_a.py"
    allow_rerun: true
  - id: step_b
    name: "Step B (non-rerunnable)"
    script: "script_b.py"
    allow_rerun: false
"""

SNAPSHOT_ITEMS_SCRIPT = """\
SNAPSHOT_ITEMS = []
"""


@pytest.fixture
def project_dir():
    """Temporary project directory with a minimal workflow and mock scripts."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "workflow.yml").write_text(WORKFLOW_YAML)

    scripts_dir = tmp / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "script_a.py").write_text(SNAPSHOT_ITEMS_SCRIPT)
    (scripts_dir / "script_b.py").write_text(SNAPSHOT_ITEMS_SCRIPT)

    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def project(project_dir):
    return Project(project_dir, script_path=project_dir / "scripts")


def _make_snapshot(project: Project, step_id: str, run_number: int):
    """
    Write a minimal snapshot ZIP + manifest so the snapshot manager
    recognises run_number as existing.  Includes workflow_state.json
    so restore_snapshot() can put it back correctly.
    """
    snap_dir = project.path / ".snapshots"
    snap_dir.mkdir(exist_ok=True)

    state_file = project.path / "workflow_state.json"
    zip_path = snap_dir / f"{step_id}_run_{run_number}_snapshot.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        if state_file.exists():
            zf.write(state_file, "workflow_state.json")

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


def _place_run_marker(project: Project, script_stem: str, run_number: int) -> Path:
    """Place a run-number-specific success marker (simulates a completed run)."""
    status_dir = project.path / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / f"{script_stem}.run_{run_number}.success"
    marker.write_text("success")
    return marker


def _place_flat_marker(project: Project, script_stem: str) -> Path:
    """Place a legacy flat success marker (simulates an old-format completed run)."""
    status_dir = project.path / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / f"{script_stem}.success"
    marker.write_text("success")
    return marker


# ---------------------------------------------------------------------------
# Case 1: full undo (effective_run == 1)
# ---------------------------------------------------------------------------

class TestFullUndoMarkerCleanup:
    """
    perform_undo() with effective_run == 1 must remove the run-1 marker
    (current format) and also the flat marker (legacy format safety net).
    """

    def test_full_undo_removes_run1_marker(self, project, project_dir):
        """
        Core regression test for Case 1.

        A step completed once → run-1 marker exists on disk.
        After perform_undo(), the run-1 marker must be gone.
        """
        step_id = "step_a"
        script_stem = "script_a"

        # Simulate run 1 completing successfully
        _make_snapshot(project, step_id, 1)
        run_marker = _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Perform undo
        result = perform_undo_test(project)

        assert result is True
        assert not run_marker.exists(), (
            "perform_undo() must remove the run-1 success marker "
            f"({run_marker.name}) — it was left behind before the fix"
        )
        assert project.get_state(step_id) == "pending"

    def test_full_undo_removes_flat_marker_legacy(self, project, project_dir):
        """
        Legacy safety net: if a flat marker exists (old project format),
        perform_undo() must remove it even when no run-1 marker is present.
        """
        step_id = "step_b"
        script_stem = "script_b"

        # Simulate old-format completion: flat marker, no run-specific marker
        _make_snapshot(project, step_id, 1)
        flat_marker = _place_flat_marker(project, script_stem)
        project.update_state(step_id, "completed")

        result = perform_undo_test(project)

        assert result is True
        assert not flat_marker.exists(), (
            "perform_undo() must remove the legacy flat success marker "
            f"({flat_marker.name}) as a safety net for old projects"
        )
        assert project.get_state(step_id) == "pending"

    def test_full_undo_removes_both_markers_if_both_present(self, project, project_dir):
        """
        Edge case: both a flat marker and a run-1 marker exist simultaneously.
        perform_undo() must remove both.
        """
        step_id = "step_a"
        script_stem = "script_a"

        _make_snapshot(project, step_id, 1)
        run_marker = _place_run_marker(project, script_stem, 1)
        flat_marker = _place_flat_marker(project, script_stem)
        project.update_state(step_id, "completed")

        result = perform_undo_test(project)

        assert result is True
        assert not run_marker.exists(), "Run-1 marker must be removed"
        assert not flat_marker.exists(), "Flat marker must be removed"
        assert project.get_state(step_id) == "pending"

    def test_full_undo_no_marker_does_not_error(self, project, project_dir):
        """
        If no marker exists at all (e.g. step was skipped or marker already
        cleaned up), perform_undo() must still succeed without raising.
        """
        step_id = "step_a"

        _make_snapshot(project, step_id, 1)
        project.update_state(step_id, "completed")
        # No marker placed

        result = perform_undo_test(project)

        assert result is True
        assert project.get_state(step_id) == "pending"

    def test_full_undo_does_not_remove_other_steps_markers(self, project, project_dir):
        """
        Undoing step_a must not touch step_b's success marker.
        """
        step_id_a = "step_a"
        step_id_b = "step_b"
        script_stem_a = "script_a"
        script_stem_b = "script_b"

        # Both steps completed
        _make_snapshot(project, step_id_a, 1)
        _place_run_marker(project, script_stem_a, 1)
        project.update_state(step_id_a, "completed")

        _make_snapshot(project, step_id_b, 1)
        b_marker = _place_run_marker(project, script_stem_b, 1)
        project.update_state(step_id_b, "completed")

        # Undo step_b (most recent)
        result = perform_undo_test(project)

        assert result is True
        # step_b's marker must be gone
        assert not b_marker.exists(), "step_b's run-1 marker must be removed"
        # step_a's marker must be untouched
        a_marker = project.path / ".workflow_status" / f"{script_stem_a}.run_1.success"
        assert a_marker.exists(), "step_a's run-1 marker must NOT be touched"


# ---------------------------------------------------------------------------
# Case 2: granular undo (effective_run > 1)
# ---------------------------------------------------------------------------

class TestGranularUndoMarkerCleanup:
    """
    perform_undo() with effective_run > 1 must remove the run-N marker for
    the run being undone.  Previously no marker cleanup was done in this branch.
    """

    def test_granular_undo_removes_run_n_marker(self, project, project_dir):
        """
        Core regression test for Case 2.

        Step ran twice (run 1 and run 2 both succeeded).
        Undoing run 2 must remove the run-2 marker and leave run-1 marker intact.
        """
        step_id = "step_a"
        script_stem = "script_a"

        # Simulate run 1 completing
        _make_snapshot(project, step_id, 1)
        run1_marker = _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Simulate run 2 completing
        _make_snapshot(project, step_id, 2)
        run2_marker = _place_run_marker(project, script_stem, 2)
        project.update_state(step_id, "completed")

        # Undo run 2 (granular undo — step stays "completed" after)
        result = perform_undo_test(project)

        assert result is True
        assert not run2_marker.exists(), (
            "perform_undo() must remove the run-2 success marker "
            f"({run2_marker.name}) — it was left behind before the fix"
        )
        # Run-1 marker must be untouched (run 1 is still valid)
        assert run1_marker.exists(), (
            "Run-1 marker must NOT be removed during a granular undo of run 2"
        )
        # Step remains completed (run 1 still exists)
        assert project.get_state(step_id) == "completed"

    def test_granular_undo_run3_removes_only_run3_marker(self, project, project_dir):
        """
        Three runs completed; undoing run 3 must remove only the run-3 marker.
        Run-1 and run-2 markers must remain.
        """
        step_id = "step_a"
        script_stem = "script_a"

        for run in (1, 2, 3):
            _make_snapshot(project, step_id, run)
            _place_run_marker(project, script_stem, run)
            project.update_state(step_id, "completed")

        result = perform_undo_test(project)

        assert result is True
        status_dir = project.path / ".workflow_status"
        assert not (status_dir / f"{script_stem}.run_3.success").exists(), \
            "Run-3 marker must be removed"
        assert (status_dir / f"{script_stem}.run_2.success").exists(), \
            "Run-2 marker must remain"
        assert (status_dir / f"{script_stem}.run_1.success").exists(), \
            "Run-1 marker must remain"

    def test_granular_undo_no_marker_does_not_error(self, project, project_dir):
        """
        If the run-N marker doesn't exist (already cleaned up or never written),
        perform_undo() must still succeed without raising.
        """
        step_id = "step_a"

        _make_snapshot(project, step_id, 1)
        project.update_state(step_id, "completed")
        _make_snapshot(project, step_id, 2)
        project.update_state(step_id, "completed")
        # No markers placed

        result = perform_undo_test(project)

        assert result is True
        # Step remains completed (run 1 still exists)
        assert project.get_state(step_id) == "completed"

    def test_sequential_granular_undos_clean_markers_in_order(self, project, project_dir):
        """
        Two sequential granular undos must each remove the correct marker.
        After undoing run 2 then run 1, both markers must be gone and the
        step must be pending.
        """
        step_id = "step_a"
        script_stem = "script_a"

        # Run 1
        _make_snapshot(project, step_id, 1)
        run1_marker = _place_run_marker(project, script_stem, 1)
        project.update_state(step_id, "completed")

        # Run 2
        _make_snapshot(project, step_id, 2)
        run2_marker = _place_run_marker(project, script_stem, 2)
        project.update_state(step_id, "completed")

        # First undo: removes run-2 marker, step stays completed
        result1 = perform_undo_test(project)
        assert result1 is True
        assert not run2_marker.exists(), "Run-2 marker must be removed after first undo"
        assert run1_marker.exists(), "Run-1 marker must remain after first undo"
        assert project.get_state(step_id) == "completed"

        # Second undo: removes run-1 marker, step becomes pending
        result2 = perform_undo_test(project)
        assert result2 is True
        assert not run1_marker.exists(), "Run-1 marker must be removed after second undo"
        assert project.get_state(step_id) == "pending"
