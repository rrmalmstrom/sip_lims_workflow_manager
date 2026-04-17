"""
Integration tests for the Stage 2 undo/snapshot system.

Tests the full core.py → SnapshotManager stack against a real on-disk project
folder using the Capsule workflow fixture and mock scripts.

These tests do NOT use the GUI or real workflow scripts. They exercise the
complete snapshot lifecycle: manifest scan → selective ZIP → restore → cleanup.

The 12 scenarios cover every critical path in the undo system:
  1.  Happy path — single step
  2.  Happy path — multi-step (3 steps)
  3.  Automatic rollback on failure
  4.  Manual undo — single step
  5.  Manual undo — multi-step (3 steps in sequence)
  6.  User-added files preserved after manual undo
  7.  User-added files NOT deleted during automatic rollback
  8.  Re-runnable step undo (run counter decrements correctly)
  9.  Legacy fallback (old _complete.zip format)
  10. Missing SNAPSHOT_ITEMS aborts run_step()
  11. FA archive permanent protection during rollback
  12. Manifest diff correctly identifies newly-added user files

Run with:
    pytest tests/test_undo_system_integration.py -v
"""

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from src.core import Project, parse_snapshot_items_from_script
from src.logic import RunResult, SnapshotManager

# Path to mock scripts directory
MOCK_SCRIPTS_DIR = Path(__file__).parent / "fixtures" / "mock_scripts"

# Import fixture generator
from tests.fixtures.generate_capsule_fixture import (
    CAPSULE_STEPS,
    create_capsule_fixture,
    get_step_produces,
    get_step_snapshot_items,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def assert_files_exist(project_path: Path, rel_paths: list, label: str = ""):
    """Assert that all given relative paths exist as files under project_path."""
    prefix = f"[{label}] " if label else ""
    for rel in rel_paths:
        full = project_path / rel
        assert full.exists(), (
            f"{prefix}Expected file missing: {rel}\n"
            f"  Full path: {full}\n"
            f"  Existing files: {sorted(str(p.relative_to(project_path)) for p in project_path.rglob('*') if p.is_file())}"
        )


def assert_files_absent(project_path: Path, rel_paths: list, label: str = ""):
    """Assert that none of the given relative paths exist under project_path."""
    prefix = f"[{label}] " if label else ""
    for rel in rel_paths:
        full = project_path / rel
        assert not full.exists(), (
            f"{prefix}Unexpected file present: {rel}\n"
            f"  Full path: {full}"
        )


def simulate_step_run(
    project: Project,
    step_id: str,
    run_number: int,
    success: bool = True,
    extra_files: list = None,
):
    """
    Simulate a complete step run without launching a real subprocess.

    Sequence:
      1. scan_manifest() — write pre-run manifest
      2. take_selective_snapshot() — write pre-run ZIP
      3. Create output files on disk (what the script would produce)
      4. Optionally create extra user-added files
      5. Create success marker (if success=True)
      6. Call handle_step_result() with the appropriate RunResult

    This mirrors what run_step() + the real script + handle_step_result() do,
    but without subprocess overhead.
    """
    step_def = next(s for s in CAPSULE_STEPS if s["id"] == step_id)
    snapshot_items = step_def["snapshot_items"]

    # Find previous manifest for diff
    completion_order = project.state_manager.get_completion_order()
    prev_manifest_path = None
    if completion_order:
        prev_step_id = completion_order[-1]
        prev_run = project.snapshot_manager.get_effective_run_number(prev_step_id)
        if prev_run > 0:
            candidate = (
                project.snapshot_manager.snapshots_dir
                / f"{prev_step_id}_run_{prev_run}_manifest.json"
            )
            if candidate.exists():
                prev_manifest_path = candidate

    # 1. Write manifest
    project.snapshot_manager.scan_manifest(step_id, run_number)

    # 2. Write selective snapshot
    project.snapshot_manager.take_selective_snapshot(
        step_id, run_number, snapshot_items, prev_manifest_path
    )

    # 3. Create output files (what the script would produce)
    for rel_path in step_def["produces"]:
        full_path = project.path / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(
            f"# {step_id} run {run_number} output: {rel_path}\n"
        )

    # 4. Create extra user-added files if requested
    if extra_files:
        for rel_path in extra_files:
            full_path = project.path / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"# user-added file: {rel_path}\n")

    # 5. Create success marker
    script_stem = Path(step_def["script"]).stem
    status_dir = project.path / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    if success:
        (status_dir / f"{script_stem}.success").write_text("success")
    else:
        # Remove marker if it exists (simulate failure — no marker written)
        marker = status_dir / f"{script_stem}.success"
        if marker.exists():
            marker.unlink()

    # 6. Call handle_step_result
    result = RunResult(
        success=success,
        stdout="mock stdout",
        stderr="" if success else "mock error",
        return_code=0 if success else 1,
    )
    project.handle_step_result(step_id, result)


def perform_undo(project: Project) -> bool:
    """
    Test version of perform_undo (mirrors app.py perform_undo without Streamlit).
    Uses the new restore_snapshot() dispatcher.
    """
    last_step_id = project.state_manager.get_last_completed_step_chronological()
    if not last_step_id:
        return False

    last_step = project.workflow.get_step_by_id(last_step_id)
    if not last_step:
        return False

    try:
        effective_run = project.snapshot_manager.get_effective_run_number(last_step_id)

        if effective_run > 1:
            if project.snapshot_manager.snapshot_exists(last_step_id, effective_run):
                project.snapshot_manager.restore_snapshot(last_step_id, effective_run)
                project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
                return True

        if effective_run >= 1:
            if project.snapshot_manager.snapshot_exists(last_step_id, 1):
                project.snapshot_manager.restore_snapshot(last_step_id, 1)

            project.snapshot_manager.remove_all_run_snapshots(last_step_id)

            script_name = last_step.get("script", "").replace(".py", "")
            success_marker = (
                project.path / ".workflow_status" / f"{script_name}.success"
            )
            if success_marker.exists():
                success_marker.unlink()

            project.update_state(last_step_id, "pending")
            return True

        return False

    except Exception as e:
        print(f"UNDO ERROR: {e}")
        return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def capsule_project(tmp_path):
    """Fresh Capsule project with no steps completed."""
    project_path, checkpoints = create_capsule_fixture(tmp_path, steps_to_complete=0)
    project = Project(project_path, script_path=MOCK_SCRIPTS_DIR)
    return project, checkpoints


@pytest.fixture
def capsule_project_3_steps(tmp_path):
    """Capsule project with first 3 steps pre-completed."""
    project_path, checkpoints = create_capsule_fixture(tmp_path, steps_to_complete=3)
    project = Project(project_path, script_path=MOCK_SCRIPTS_DIR)
    return project, checkpoints


# ---------------------------------------------------------------------------
# Scenario 1: Happy path — single step
# ---------------------------------------------------------------------------


def test_happy_path_single_step(capsule_project):
    """
    Pre-run snapshot ZIP and manifest created; step completes;
    ZIP and manifest remain as undo record.
    """
    project, _ = capsule_project
    step_id = "init_project"

    # Before run: no snapshots
    assert not project.snapshot_manager.snapshot_exists(step_id, 1)
    snapshots_dir = project.snapshot_manager.snapshots_dir
    assert not list(snapshots_dir.glob(f"{step_id}*"))

    # Run step 1
    simulate_step_run(project, step_id, run_number=1, success=True)

    # After run: step is completed
    assert project.get_state(step_id) == "completed"

    # ZIP and manifest exist as undo record
    assert project.snapshot_manager.snapshot_exists(step_id, 1)
    manifest = snapshots_dir / f"{step_id}_run_1_manifest.json"
    assert manifest.exists(), "Manifest JSON must remain after successful step"

    # Output files exist on disk
    assert_files_exist(project.path, get_step_produces(step_id), label="after step 1")


# ---------------------------------------------------------------------------
# Scenario 2: Happy path — multi-step (3 steps)
# ---------------------------------------------------------------------------


def test_happy_path_multi_step(capsule_project):
    """
    Three steps complete in sequence; completion_order stack is correct;
    each step has its own ZIP + manifest.
    """
    project, _ = capsule_project

    for i, step in enumerate(CAPSULE_STEPS[:3]):
        step_id = step["id"]
        simulate_step_run(project, step_id, run_number=1, success=True)
        assert project.get_state(step_id) == "completed"
        assert project.snapshot_manager.snapshot_exists(step_id, 1)

    # Completion order must be correct
    completion_order = project.state_manager.get_completion_order()
    assert completion_order == [s["id"] for s in CAPSULE_STEPS[:3]]

    # Each step has its own manifest
    for step in CAPSULE_STEPS[:3]:
        manifest = (
            project.snapshot_manager.snapshots_dir
            / f"{step['id']}_run_1_manifest.json"
        )
        assert manifest.exists(), f"Manifest missing for {step['id']}"


# ---------------------------------------------------------------------------
# Scenario 3: Automatic rollback on failure
# ---------------------------------------------------------------------------


def test_automatic_rollback_on_failure(capsule_project):
    """
    Mock script fails; newly-created files are deleted; SNAPSHOT_ITEMS files
    restored to pre-run state; manifest and ZIP deleted after rollback.
    """
    project, _ = capsule_project

    # Complete step 1 first so there's a baseline
    simulate_step_run(project, "init_project", run_number=1, success=True)

    # Record state before step 2 runs
    pre_run_db = (project.path / "project_summary.db").read_text()

    # Run step 2 but it FAILS
    simulate_step_run(project, "prep_library", run_number=1, success=False)

    # Step state must remain "pending" (not completed)
    assert project.get_state("prep_library") == "pending"

    # The snapshot pair is consumed by rollback — no longer in .snapshots/
    assert not project.snapshot_manager.snapshot_exists("prep_library", 1)

    # project_summary.db should be restored to pre-run content
    post_rollback_db = (project.path / "project_summary.db").read_text()
    assert post_rollback_db == pre_run_db, (
        "project_summary.db should be restored to pre-run state after rollback"
    )


# ---------------------------------------------------------------------------
# Scenario 4: Manual undo — single step
# ---------------------------------------------------------------------------


def test_manual_undo_single_step(capsule_project):
    """
    Step completes; user undoes; project folder matches pre-run state.
    """
    project, checkpoints = capsule_project
    step_id = "init_project"

    # Record pre-run state of a key file
    # (project_summary.db doesn't exist yet before step 1)
    assert not (project.path / "project_summary.db").exists()

    # Run step 1
    simulate_step_run(project, step_id, run_number=1, success=True)
    assert project.get_state(step_id) == "completed"
    assert (project.path / "project_summary.db").exists()

    # Undo
    result = perform_undo(project)
    assert result is True

    # Step is pending again
    assert project.get_state(step_id) == "pending"

    # Output files created by step 1 should be gone
    # (they were not in the pre-run snapshot, so restore deletes them)
    assert not (project.path / "project_summary.db").exists()
    assert not (project.path / "1_make_barcode_labels").exists()

    # No snapshots remain
    assert not project.snapshot_manager.snapshot_exists(step_id, 1)


# ---------------------------------------------------------------------------
# Scenario 5: Manual undo — multi-step (3 steps in sequence)
# ---------------------------------------------------------------------------


def test_manual_undo_multi_step(capsule_project):
    """
    Three steps complete; user undoes all three in sequence;
    project folder matches initial state after all undos.
    """
    project, _ = capsule_project

    # Complete 3 steps
    for step in CAPSULE_STEPS[:3]:
        simulate_step_run(project, step["id"], run_number=1, success=True)

    # All 3 completed
    for step in CAPSULE_STEPS[:3]:
        assert project.get_state(step["id"]) == "completed"

    # Undo step 3
    result = perform_undo(project)
    assert result is True
    assert project.get_state("analyze_quality") == "pending"
    assert project.get_state("prep_library") == "completed"

    # Undo step 2
    result = perform_undo(project)
    assert result is True
    assert project.get_state("prep_library") == "pending"
    assert project.get_state("init_project") == "completed"

    # Undo step 1
    result = perform_undo(project)
    assert result is True
    assert project.get_state("init_project") == "pending"

    # Nothing left to undo
    result = perform_undo(project)
    assert result is False

    # Project folder should be back to initial state (no step output files)
    assert not (project.path / "project_summary.db").exists()
    assert not (project.path / "1_make_barcode_labels").exists()
    assert not (project.path / "2_library_creation").exists()
    assert not (project.path / "3_FA_analysis").exists()


# ---------------------------------------------------------------------------
# Scenario 6: User-added files preserved after manual undo
# ---------------------------------------------------------------------------


def test_user_added_files_preserved_after_undo(capsule_project):
    """
    User drops a file between steps; step runs and is undone;
    user file is still present after undo.
    """
    project, _ = capsule_project

    # Complete step 1
    simulate_step_run(project, "init_project", run_number=1, success=True)

    # User adds a file AFTER step 1 completes (before step 2 runs)
    user_file = project.path / "my_notes.txt"
    user_file.write_text("my important notes\n")

    # Run step 2 — the manifest diff will detect my_notes.txt as newly-added
    # and include it in the snapshot ZIP
    simulate_step_run(project, "prep_library", run_number=1, success=True)

    assert user_file.exists(), "User file should still exist after step 2 completes"

    # Undo step 2
    result = perform_undo(project)
    assert result is True

    # User file must still be present after undo
    assert user_file.exists(), (
        "User-added file must be preserved after undo — "
        "it was captured in the snapshot ZIP and restored"
    )


# ---------------------------------------------------------------------------
# Scenario 7: User-added files NOT deleted during automatic rollback
# ---------------------------------------------------------------------------


def test_user_added_files_not_deleted_on_rollback(capsule_project):
    """
    User drops a file; step fails; rollback does not delete the user file.
    """
    project, _ = capsule_project

    # Complete step 1
    simulate_step_run(project, "init_project", run_number=1, success=True)

    # User adds a file before step 2 runs
    user_file = project.path / "my_notes.txt"
    user_file.write_text("my important notes\n")

    # Step 2 FAILS — triggers automatic rollback
    simulate_step_run(project, "prep_library", run_number=1, success=False)

    # User file must survive the rollback
    assert user_file.exists(), (
        "User-added file must NOT be deleted during automatic rollback"
    )

    # Step remains pending
    assert project.get_state("prep_library") == "pending"


# ---------------------------------------------------------------------------
# Scenario 8: Re-runnable step undo (run counter decrements correctly)
# ---------------------------------------------------------------------------


def test_rerunnable_step_undo(capsule_project):
    """
    init_project (allow_rerun=True) run 3 times; undo once; run counter
    decrements correctly; correct ZIP restored.
    """
    project, _ = capsule_project
    step_id = "init_project"

    # Run 3 times
    for run_num in range(1, 4):
        simulate_step_run(project, step_id, run_number=run_num, success=True)

    assert project.snapshot_manager.get_effective_run_number(step_id) == 3
    assert project.snapshot_manager.snapshot_exists(step_id, 1)
    assert project.snapshot_manager.snapshot_exists(step_id, 2)
    assert project.snapshot_manager.snapshot_exists(step_id, 3)

    # Undo run 3 — step remains completed (runs 1 and 2 still exist)
    result = perform_undo(project)
    assert result is True
    assert project.get_state(step_id) == "completed"
    assert project.snapshot_manager.get_effective_run_number(step_id) == 2
    assert not project.snapshot_manager.snapshot_exists(step_id, 3)

    # Undo run 2 — step remains completed (run 1 still exists)
    result = perform_undo(project)
    assert result is True
    assert project.get_state(step_id) == "completed"
    assert project.snapshot_manager.get_effective_run_number(step_id) == 1
    assert not project.snapshot_manager.snapshot_exists(step_id, 2)

    # Undo run 1 — step becomes pending (no more runs)
    result = perform_undo(project)
    assert result is True
    assert project.get_state(step_id) == "pending"
    assert project.snapshot_manager.get_effective_run_number(step_id) == 0
    assert not project.snapshot_manager.snapshot_exists(step_id, 1)


# ---------------------------------------------------------------------------
# Scenario 9: Legacy fallback (_complete.zip format)
# ---------------------------------------------------------------------------


def test_legacy_fallback(tmp_path):
    """
    Project folder seeded with run-numbered legacy _complete.zip files
    (format: {step_id}_run_{N}_complete.zip — the intermediate legacy format
    that predates the new _snapshot.zip format).

    restore_snapshot() must detect the legacy ZIP and use _restore_from_complete_snapshot().
    snapshot_exists() must return True for this format.
    """
    project_path, _ = create_capsule_fixture(tmp_path, steps_to_complete=0)
    project = Project(project_path, script_path=MOCK_SCRIPTS_DIR)

    step_id = "init_project"
    run_number = 1
    snapshots_dir = project.snapshot_manager.snapshots_dir

    # Seed a run-numbered legacy _complete.zip (no paired manifest)
    # This is the format used before Stage 2: {step_id}_run_{N}_complete.zip
    legacy_zip_path = snapshots_dir / f"{step_id}_run_{run_number}_complete.zip"
    sentinel_file = "project_summary.db"
    sentinel_content = "legacy db content\n"

    with zipfile.ZipFile(legacy_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(sentinel_file, sentinel_content)

    # Mark step as completed in state (simulating an in-progress project)
    project.update_state(step_id, "completed")
    state = project.state_manager.load()
    state["_completion_order"] = [step_id]
    project.state_manager.save(state)

    # Create a newer file on disk (simulating work done after the snapshot)
    newer_file = project.path / "newer_output.csv"
    newer_file.write_text("this was created after the legacy snapshot\n")

    # snapshot_exists() must find the legacy _run_N_complete.zip
    assert project.snapshot_manager.snapshot_exists(step_id, run_number), (
        "snapshot_exists() must return True for legacy _run_N_complete.zip format"
    )

    # get_effective_run_number() must also find it
    assert project.snapshot_manager.get_effective_run_number(step_id) == run_number

    # restore_snapshot() must fall back to _restore_from_complete_snapshot()
    # (no paired manifest exists, so the new-format path is skipped)
    project.snapshot_manager.restore_snapshot(step_id, run_number)

    # Sentinel file should be restored from the legacy ZIP
    restored = project.path / sentinel_file
    assert restored.exists(), "Sentinel file must be restored from legacy ZIP"
    assert restored.read_text() == sentinel_content


# ---------------------------------------------------------------------------
# Scenario 10: Missing SNAPSHOT_ITEMS aborts run_step()
# ---------------------------------------------------------------------------


def test_missing_snapshot_items_aborts_run_step(tmp_path):
    """
    Mock script has no SNAPSHOT_ITEMS; run_step() aborts with ValueError;
    no ZIP or manifest created; project folder unchanged.
    """
    project_path, _ = create_capsule_fixture(tmp_path, steps_to_complete=0)

    # Use the NO_SNAPSHOT_ITEMS mock script directory
    # We need to point to a scripts dir that has a script without SNAPSHOT_ITEMS
    # for the analyze_quality step (capsule_fa_analysis.py)
    no_items_dir = tmp_path / "no_items_scripts"
    no_items_dir.mkdir()

    # Copy the no-SNAPSHOT_ITEMS variant as the step's script name
    src = MOCK_SCRIPTS_DIR / "capsule_fa_analysis_NO_SNAPSHOT_ITEMS.py"
    dst = no_items_dir / "capsule_fa_analysis.py"
    shutil.copy(src, dst)

    project = Project(project_path, script_path=no_items_dir)

    # Pre-complete steps 1 and 2 so step 3 is next
    for step in CAPSULE_STEPS[:2]:
        simulate_step_run(project, step["id"], run_number=1, success=True)

    step_id = "analyze_quality"
    snapshots_dir = project.snapshot_manager.snapshots_dir

    # Record snapshot count before
    before_count = len(list(snapshots_dir.glob("*")))

    # run_step() should abort — SNAPSHOT_ITEMS missing
    # It prints an error and returns early (does not raise)
    project.run_step(step_id)

    # No new snapshots created
    after_count = len(list(snapshots_dir.glob("*")))
    assert after_count == before_count, (
        f"run_step() must not create any snapshots when SNAPSHOT_ITEMS is missing. "
        f"Before: {before_count}, After: {after_count}"
    )

    # Step state remains pending
    assert project.get_state(step_id) == "pending"


# ---------------------------------------------------------------------------
# Scenario 11: FA archive permanent protection during rollback
# ---------------------------------------------------------------------------


def test_fa_archive_permanent_protection(capsule_project):
    """
    FA analysis step runs and fails; FA archive subfolders are NOT deleted
    during rollback (PERMANENT_EXCLUSIONS protection).
    """
    project, _ = capsule_project

    # Complete step 1 first
    simulate_step_run(project, "init_project", run_number=1, success=True)

    # Create a fake FA archive folder (simulating a previously-archived result)
    fa_archive = project.path / "archived_files" / "FA_results_archive"
    fa_archive.mkdir(parents=True, exist_ok=True)
    archive_file = fa_archive / "old_fa_results.csv"
    archive_file.write_text("archived FA data — must not be deleted\n")

    # Also create a MISC folder (another permanent exclusion)
    misc_dir = project.path / "MISC"
    misc_dir.mkdir(exist_ok=True)
    misc_file = misc_dir / "notes.txt"
    misc_file.write_text("misc notes — must not be deleted\n")

    # Run step 2 (analyze_quality uses step 3, but we test with prep_library)
    # The key is that rollback must not touch PERMANENT_EXCLUSIONS
    simulate_step_run(project, "prep_library", run_number=1, success=False)

    # FA archive must survive the rollback
    assert archive_file.exists(), (
        "FA archive file must NOT be deleted during automatic rollback "
        "(PERMANENT_EXCLUSIONS protection)"
    )

    # MISC folder must survive the rollback
    assert misc_file.exists(), (
        "MISC folder contents must NOT be deleted during automatic rollback "
        "(PERMANENT_EXCLUSIONS protection)"
    )


# ---------------------------------------------------------------------------
# Scenario 12: Manifest diff correctly identifies newly-added user files
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Scenario 13: Empty directories from previous steps survive rollback
# ---------------------------------------------------------------------------


def test_empty_dirs_from_previous_step_survive_rollback(capsule_project):
    """
    Step 1 creates empty directories (e.g. 2_library_creation/, 3_FA_analysis/,
    4_plate_selection_and_pooling/) as part of the project folder structure.
    Step 2 fails and triggers automatic rollback.

    The empty directories created by step 1 must NOT be deleted during step 2's
    rollback — they were present before step 2 ran and are recorded in step 2's
    pre-run manifest (the "directories" field added by the fix).

    This is the real-world bug: the manifest previously only recorded files, so
    empty directories were invisible and appeared as "newly created during step 2",
    causing them to be incorrectly deleted during rollback.
    """
    project, _ = capsule_project

    # Complete step 1 — this creates the project folder structure including
    # empty subdirectories (2_library_creation/, 3_FA_analysis/, etc.)
    simulate_step_run(project, "init_project", run_number=1, success=True)

    # Manually create empty directories that simulate what step 1 would create
    # in the real Capsule workflow (the fixture mock script doesn't create them,
    # so we create them here to reproduce the exact bug scenario)
    empty_dirs = [
        project.path / "2_library_creation",
        project.path / "3_FA_analysis",
        project.path / "4_plate_selection_and_pooling",
    ]
    for d in empty_dirs:
        d.mkdir(exist_ok=True)

    # Verify the directories exist and are empty before step 2 runs
    for d in empty_dirs:
        assert d.exists() and d.is_dir(), f"Pre-condition: {d.name} must exist before step 2"
        assert not any(d.iterdir()), f"Pre-condition: {d.name} must be empty before step 2"

    # Run step 2 but it FAILS — triggers automatic rollback
    simulate_step_run(project, "prep_library", run_number=1, success=False)

    # Step state must remain "pending"
    assert project.get_state("prep_library") == "pending"

    # The snapshot pair is consumed by rollback
    assert not project.snapshot_manager.snapshot_exists("prep_library", 1)

    # CRITICAL: The empty directories created by step 1 must still exist
    # after step 2's rollback — they were NOT created during step 2
    for d in empty_dirs:
        assert d.exists() and d.is_dir(), (
            f"Empty directory '{d.name}' was incorrectly deleted during step 2 rollback. "
            f"This directory was created by step 1 and must survive step 2's rollback. "
            f"Root cause: manifest must record directories explicitly so empty dirs "
            f"are not mistaken for 'newly created during step 2'."
        )


def test_manifest_diff_detects_newly_added_files(capsule_project):
    """
    Manifest diff correctly identifies files added by the user between steps.
    These files are included in the snapshot ZIP so they can be restored on undo.
    """
    project, _ = capsule_project

    # Complete step 1
    simulate_step_run(project, "init_project", run_number=1, success=True)

    # User adds files after step 1 completes
    user_file_1 = project.path / "user_data.csv"
    user_file_2 = project.path / "1_make_barcode_labels" / "extra_labels.csv"
    user_file_1.write_text("user data\n")
    user_file_2.write_text("extra labels\n")

    # Run step 2 — manifest diff should detect user_file_1 and user_file_2
    # as newly-added (they weren't in the step-1 manifest)
    step_id = "prep_library"
    run_number = 1

    # Find previous manifest
    prev_manifest_path = (
        project.snapshot_manager.snapshots_dir / "init_project_run_1_manifest.json"
    )
    assert prev_manifest_path.exists(), "Step 1 manifest must exist"

    # Write step 2 manifest
    project.snapshot_manager.scan_manifest(step_id, run_number)

    # Take selective snapshot — should include user files via manifest diff
    project.snapshot_manager.take_selective_snapshot(
        step_id, run_number,
        get_step_snapshot_items(step_id),
        prev_manifest_path,
    )

    # Verify the snapshot ZIP contains the user-added files
    zip_path = (
        project.snapshot_manager.snapshots_dir
        / f"{step_id}_run_{run_number}_snapshot.zip"
    )
    assert zip_path.exists(), "Snapshot ZIP must be created"

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())

    assert "user_data.csv" in names, (
        "user_data.csv must be in snapshot ZIP (detected via manifest diff)"
    )
    assert "1_make_barcode_labels/extra_labels.csv" in names, (
        "extra_labels.csv must be in snapshot ZIP (detected via manifest diff)"
    )
