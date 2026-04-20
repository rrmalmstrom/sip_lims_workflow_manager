"""
Integration tests for the undo/snapshot system — SIP workflow fixture.

Tests the full core.py -> SnapshotManager stack against a real on-disk project
folder using the SIP workflow fixture and mock scripts.

These tests do NOT use the GUI or real workflow scripts. They exercise the
complete snapshot lifecycle: manifest scan -> selective ZIP -> restore -> cleanup.

The 13 scenarios are identical in structure to the Capsule and SPS-CE integration
tests but use SIP-specific step IDs, directory names, FA archive paths, and
SNAPSHOT_ITEMS.

Run with:
    pytest tests/test_undo_system_integration_sip.py -v
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

# Import SIP fixture generator
from tests.fixtures.generate_sip_fixture import (
    SIP_STEPS,
    create_sip_fixture,
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
            prefix + "Expected file missing: " + rel + "\n"
            + "  Full path: " + str(full) + "\n"
            + "  Existing files: " + str(sorted(
                str(p.relative_to(project_path))
                for p in project_path.rglob("*") if p.is_file()
            ))
        )


def assert_files_absent(project_path: Path, rel_paths: list, label: str = ""):
    """Assert that none of the given relative paths exist under project_path."""
    prefix = f"[{label}] " if label else ""
    for rel in rel_paths:
        full = project_path / rel
        assert not full.exists(), (
            prefix + "Unexpected file present: " + rel + "\n"
            + "  Full path: " + str(full)
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
    """
    step_def = next(s for s in SIP_STEPS if s["id"] == step_id)
    snapshot_items = step_def["snapshot_items"]

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

    # 3b. Create empty dirs this step creates (folder structure)
    for rel_dir in step_def.get("creates_empty_dirs", []):
        (project.path / rel_dir).mkdir(parents=True, exist_ok=True)

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
def sip_project(tmp_path):
    """Fresh SIP project with no steps completed."""
    project_path, checkpoints = create_sip_fixture(tmp_path, steps_to_complete=0)
    project = Project(project_path, script_path=MOCK_SCRIPTS_DIR)
    return project, checkpoints


@pytest.fixture
def sip_project_3_steps(tmp_path):
    """SIP project with first 3 steps pre-completed."""
    project_path, checkpoints = create_sip_fixture(tmp_path, steps_to_complete=3)
    project = Project(project_path, script_path=MOCK_SCRIPTS_DIR)
    return project, checkpoints


# ---------------------------------------------------------------------------
# Scenario 1: Happy path — single step
# ---------------------------------------------------------------------------


def test_happy_path_single_step(sip_project):
    """
    Pre-run snapshot ZIP and manifest created; step completes;
    ZIP and manifest remain as undo record.
    """
    project, _ = sip_project
    step_id = "setup_plates"

    assert not project.snapshot_manager.snapshot_exists(step_id, 1)
    snapshots_dir = project.snapshot_manager.snapshots_dir
    assert not list(snapshots_dir.glob(f"{step_id}*"))

    simulate_step_run(project, step_id, run_number=1, success=True)

    assert project.get_state(step_id) == "completed"
    assert project.snapshot_manager.snapshot_exists(step_id, 1)
    manifest = snapshots_dir / f"{step_id}_run_1_manifest.json"
    assert manifest.exists(), "Manifest JSON must remain after successful step"
    assert_files_exist(project.path, get_step_produces(step_id), label="after step 1")


# ---------------------------------------------------------------------------
# Scenario 2: Happy path — multi-step (3 steps)
# ---------------------------------------------------------------------------


def test_happy_path_multi_step(sip_project):
    """
    Three steps complete in sequence; completion_order stack is correct;
    each step has its own ZIP + manifest.
    """
    project, _ = sip_project

    for step in SIP_STEPS[:3]:
        step_id = step["id"]
        simulate_step_run(project, step_id, run_number=1, success=True)
        assert project.get_state(step_id) == "completed"
        assert project.snapshot_manager.snapshot_exists(step_id, 1)

    completion_order = project.state_manager.get_completion_order()
    assert completion_order == [s["id"] for s in SIP_STEPS[:3]]

    for step in SIP_STEPS[:3]:
        manifest = (
            project.snapshot_manager.snapshots_dir
            / f"{step['id']}_run_1_manifest.json"
        )
        assert manifest.exists(), f"Manifest missing for {step['id']}"


# ---------------------------------------------------------------------------
# Scenario 3: Automatic rollback on failure
# ---------------------------------------------------------------------------


def test_automatic_rollback_on_failure(sip_project):
    """
    Mock script fails; newly-created files are deleted; SNAPSHOT_ITEMS files
    restored to pre-run state; manifest and ZIP deleted after rollback.
    """
    project, _ = sip_project

    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    pre_run_db = (project.path / "project_database.db").read_text()

    # ultracentrifuge_transfer has project_database.db in SNAPSHOT_ITEMS
    simulate_step_run(project, "ultracentrifuge_transfer", run_number=1, success=False)

    assert project.get_state("ultracentrifuge_transfer") == "pending"
    assert not project.snapshot_manager.snapshot_exists("ultracentrifuge_transfer", 1)

    post_rollback_db = (project.path / "project_database.db").read_text()
    assert post_rollback_db == pre_run_db, (
        "project_database.db should be restored to pre-run state after rollback"
    )


# ---------------------------------------------------------------------------
# Scenario 4: Manual undo — single step
# ---------------------------------------------------------------------------


def test_manual_undo_single_step(sip_project):
    """
    Step completes; user undoes; project folder matches pre-run state.
    """
    project, checkpoints = sip_project
    step_id = "setup_plates"

    assert not (project.path / "project_database.db").exists()

    simulate_step_run(project, step_id, run_number=1, success=True)
    assert project.get_state(step_id) == "completed"
    assert (project.path / "project_database.db").exists()

    result = perform_undo(project)
    assert result is True

    assert project.get_state(step_id) == "pending"
    assert not (project.path / "project_database.db").exists()
    assert not (project.path / "project_database.csv").exists()
    assert not project.snapshot_manager.snapshot_exists(step_id, 1)


# ---------------------------------------------------------------------------
# Scenario 5: Manual undo — multi-step (3 steps in sequence)
# ---------------------------------------------------------------------------


def test_manual_undo_multi_step(sip_project):
    """
    Three steps complete; user undoes all three in sequence;
    project folder matches initial state after all undos.
    """
    project, _ = sip_project

    for step in SIP_STEPS[:3]:
        simulate_step_run(project, step["id"], run_number=1, success=True)

    for step in SIP_STEPS[:3]:
        assert project.get_state(step["id"]) == "completed"

    result = perform_undo(project)
    assert result is True
    assert project.get_state("plot_dna_conc") == "pending"
    assert project.get_state("ultracentrifuge_transfer") == "completed"

    result = perform_undo(project)
    assert result is True
    assert project.get_state("ultracentrifuge_transfer") == "pending"
    assert project.get_state("setup_plates") == "completed"

    result = perform_undo(project)
    assert result is True
    assert project.get_state("setup_plates") == "pending"

    result = perform_undo(project)
    assert result is False

    assert not (project.path / "project_database.db").exists()
    assert not (project.path / "project_database.csv").exists()
    assert not (project.path / "lib_info.db").exists()


# ---------------------------------------------------------------------------
# Scenario 6: User-added files preserved after manual undo
# ---------------------------------------------------------------------------


def test_user_added_files_preserved_after_undo(sip_project):
    """
    User drops a file between steps; step runs and is undone;
    user file is still present after undo.
    """
    project, _ = sip_project

    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    user_file = project.path / "my_notes.txt"
    user_file.write_text("my important notes\n")

    simulate_step_run(project, "ultracentrifuge_transfer", run_number=1, success=True)

    assert user_file.exists(), "User file should still exist after step 2 completes"

    result = perform_undo(project)
    assert result is True

    assert user_file.exists(), (
        "User-added file must be preserved after undo — "
        "it was captured in the snapshot ZIP and restored"
    )


# ---------------------------------------------------------------------------
# Scenario 7: User-added files NOT deleted during automatic rollback
# ---------------------------------------------------------------------------


def test_user_added_files_not_deleted_on_rollback(sip_project):
    """
    User drops a file; step fails; rollback does not delete the user file.
    """
    project, _ = sip_project

    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    user_file = project.path / "my_notes.txt"
    user_file.write_text("my important notes\n")

    simulate_step_run(project, "ultracentrifuge_transfer", run_number=1, success=False)

    assert user_file.exists(), (
        "User-added file must NOT be deleted during automatic rollback"
    )
    assert project.get_state("ultracentrifuge_transfer") == "pending"


# ---------------------------------------------------------------------------
# Scenario 8: Re-runnable step undo (run counter decrements correctly)
# ---------------------------------------------------------------------------


def test_rerunnable_step_undo(sip_project):
    """
    ultracentrifuge_transfer (allow_rerun=True) run 3 times; undo once;
    run counter decrements correctly; correct ZIP restored.
    """
    project, _ = sip_project
    step_id = "ultracentrifuge_transfer"

    # First complete setup_plates so ultracentrifuge_transfer has a predecessor
    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    for run_num in range(1, 4):
        simulate_step_run(project, step_id, run_number=run_num, success=True)

    assert project.snapshot_manager.get_effective_run_number(step_id) == 3
    assert project.snapshot_manager.snapshot_exists(step_id, 1)
    assert project.snapshot_manager.snapshot_exists(step_id, 2)
    assert project.snapshot_manager.snapshot_exists(step_id, 3)

    result = perform_undo(project)
    assert result is True
    assert project.get_state(step_id) == "completed"
    assert project.snapshot_manager.get_effective_run_number(step_id) == 2
    assert not project.snapshot_manager.snapshot_exists(step_id, 3)

    result = perform_undo(project)
    assert result is True
    assert project.get_state(step_id) == "completed"
    assert project.snapshot_manager.get_effective_run_number(step_id) == 1
    assert not project.snapshot_manager.snapshot_exists(step_id, 2)

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
    Project folder seeded with run-numbered legacy _complete.zip files.
    restore_snapshot() must detect the legacy ZIP and use _restore_from_complete_snapshot().
    snapshot_exists() must return True for this format.
    """
    project_path, _ = create_sip_fixture(tmp_path, steps_to_complete=0)
    project = Project(project_path, script_path=MOCK_SCRIPTS_DIR)

    step_id = "setup_plates"
    run_number = 1
    snapshots_dir = project.snapshot_manager.snapshots_dir

    legacy_zip_path = snapshots_dir / f"{step_id}_run_{run_number}_complete.zip"
    sentinel_file = "project_database.db"
    sentinel_content = "legacy sip db content\n"

    with zipfile.ZipFile(legacy_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(sentinel_file, sentinel_content)

    project.update_state(step_id, "completed")
    state = project.state_manager.load()
    state["_completion_order"] = [step_id]
    project.state_manager.save(state)

    newer_file = project.path / "newer_output.csv"
    newer_file.write_text("this was created after the legacy snapshot\n")

    assert project.snapshot_manager.snapshot_exists(step_id, run_number), (
        "snapshot_exists() must return True for legacy _run_N_complete.zip format"
    )
    assert project.snapshot_manager.get_effective_run_number(step_id) == run_number

    project.snapshot_manager.restore_snapshot(step_id, run_number)

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
    project_path, _ = create_sip_fixture(tmp_path, steps_to_complete=0)

    no_items_dir = tmp_path / "no_items_scripts"
    no_items_dir.mkdir()

    src = MOCK_SCRIPTS_DIR / "first.FA.output.analysis_NO_SNAPSHOT_ITEMS.py"
    dst = no_items_dir / "first.FA.output.analysis.py"
    shutil.copy(src, dst)

    project = Project(project_path, script_path=no_items_dir)

    # Pre-complete steps 1-8 so step 9 (first_fa_analysis) is next
    for step in SIP_STEPS[:8]:
        simulate_step_run(project, step["id"], run_number=1, success=True)

    step_id = "first_fa_analysis"
    snapshots_dir = project.snapshot_manager.snapshots_dir

    before_count = len(list(snapshots_dir.glob("*")))

    project.run_step(step_id)

    after_count = len(list(snapshots_dir.glob("*")))
    assert after_count == before_count, (
        f"run_step() must not create any snapshots when SNAPSHOT_ITEMS is missing. "
        f"Before: {before_count}, After: {after_count}"
    )
    assert project.get_state(step_id) == "pending"


# ---------------------------------------------------------------------------
# Scenario 11: FA archive permanent protection during rollback
# ---------------------------------------------------------------------------


def test_fa_archive_permanent_protection(sip_project):
    """
    FA analysis step runs and fails; FA archive subfolders are NOT deleted
    during rollback (PERMANENT_EXCLUSIONS protection).

    SIP uses archived_files/FA_results_archive/first_lib_attempt_fa_results/
    as the FA archive path (new path format, distinct from SPS-CE).
    """
    project, _ = sip_project

    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    # SIP FA archive path (new format with FA_results_archive subdirectory)
    fa_archive = (
        project.path
        / "archived_files"
        / "FA_results_archive"
        / "first_lib_attempt_fa_results"
    )
    fa_archive.mkdir(parents=True, exist_ok=True)
    archive_file = fa_archive / "old_fa_results.csv"
    archive_file.write_text("archived SIP FA data — must not be deleted\n")

    misc_dir = project.path / "MISC"
    misc_dir.mkdir(exist_ok=True)
    misc_file = misc_dir / "notes.txt"
    misc_file.write_text("misc notes — must not be deleted\n")

    simulate_step_run(project, "ultracentrifuge_transfer", run_number=1, success=False)

    assert archive_file.exists(), (
        "FA archive file must NOT be deleted during automatic rollback "
        "(PERMANENT_EXCLUSIONS protection)"
    )
    assert misc_file.exists(), (
        "MISC folder contents must NOT be deleted during automatic rollback "
        "(PERMANENT_EXCLUSIONS protection)"
    )


# ---------------------------------------------------------------------------
# Scenario 12: Manifest diff correctly identifies newly-added user files
# ---------------------------------------------------------------------------


def test_manifest_diff_detects_newly_added_files(sip_project):
    """
    Manifest diff correctly identifies files added by the user between steps.
    These files are included in the snapshot ZIP so they can be restored on undo.
    """
    project, _ = sip_project

    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    user_file_1 = project.path / "user_data.csv"
    user_file_2 = project.path / "1_setup_isotope_qc_fa" / "extra_notes.txt"
    user_file_1.write_text("user data\n")
    user_file_2.parent.mkdir(parents=True, exist_ok=True)
    user_file_2.write_text("extra notes\n")

    step_id = "ultracentrifuge_transfer"
    run_number = 1

    prev_manifest_path = (
        project.snapshot_manager.snapshots_dir / "setup_plates_run_1_manifest.json"
    )
    assert prev_manifest_path.exists(), "Step 1 manifest must exist"

    project.snapshot_manager.scan_manifest(step_id, run_number)
    project.snapshot_manager.take_selective_snapshot(
        step_id, run_number,
        get_step_snapshot_items(step_id),
        prev_manifest_path,
    )

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
    assert "1_setup_isotope_qc_fa/extra_notes.txt" in names, (
        "extra_notes.txt must be in snapshot ZIP (detected via manifest diff)"
    )


# ---------------------------------------------------------------------------
# Scenario 13: Empty directories from previous steps survive rollback
# ---------------------------------------------------------------------------


def test_empty_dirs_from_previous_step_survive_rollback(sip_project):
    """
    Step 1 (setup_plates) creates empty directories as part of the SIP project
    folder structure:
      2_load_ultracentrifuge/, 3_merge_density_vol_conc_files/,
      4_make_library_analyze_fa/, 5_pooling/, archived_files/,
      DNA_vs_Density_plots/

    Step 2 fails and triggers automatic rollback.

    The empty directories created by step 1 must NOT be deleted during step 2's
    rollback — they were present before step 2 ran and are recorded in step 2's
    pre-run manifest (the "directories" field).
    """
    project, _ = sip_project

    simulate_step_run(project, "setup_plates", run_number=1, success=True)

    empty_dirs = [
        project.path / "2_load_ultracentrifuge",
        project.path / "3_merge_density_vol_conc_files",
        project.path / "4_make_library_analyze_fa",
        project.path / "5_pooling",
        project.path / "archived_files",
        project.path / "DNA_vs_Density_plots",
    ]
    for d in empty_dirs:
        assert d.exists() and d.is_dir(), (
            f"Pre-condition: {d.name} must exist before step 2"
        )

    simulate_step_run(project, "ultracentrifuge_transfer", run_number=1, success=False)

    assert project.get_state("ultracentrifuge_transfer") == "pending"
    assert not project.snapshot_manager.snapshot_exists("ultracentrifuge_transfer", 1)

    for d in empty_dirs:
        assert d.exists() and d.is_dir(), (
            f"Empty directory '{d.name}' was incorrectly deleted during step 2 rollback. "
            f"This directory was created by step 1 and must survive step 2's rollback."
        )
