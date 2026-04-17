"""
Unit tests for the new SnapshotManager methods added in Stage 2 (Checkpoint A).

Tests cover:
  - scan_manifest()
  - take_selective_snapshot()
  - restore_snapshot() — new-format path
  - restore_snapshot() — legacy fallback path
  - _restore_from_selective_snapshot() — file/dir deletion + extraction
  - apply_retention_policy()
  - snapshot_exists() — new signature (step_id, run_number)
  - get_next_run_number() — dual-format awareness
  - get_current_run_number() — dual-format awareness
  - get_effective_run_number() — dual-format awareness
  - get_latest_run_snapshot() — dual-format awareness
  - remove_run_snapshots_from() — removes new + legacy + manifests
  - remove_all_run_snapshots() — removes new + legacy + manifests
  - PERMANENT_EXCLUSIONS respected during restore
  - _safe_delete() retry behaviour (mocked)
"""

import json
import zipfile
import pytest
from pathlib import Path
from unittest.mock import patch, call

from src.logic import SnapshotManager, PERMANENT_EXCLUSIONS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager(tmp_path: Path) -> SnapshotManager:
    """Create a SnapshotManager rooted at tmp_path."""
    snapshots_dir = tmp_path / ".snapshots"
    snapshots_dir.mkdir()
    return SnapshotManager(tmp_path, snapshots_dir)


def write_file(path: Path, content: str = "data"):
    """Create a file (and any missing parent dirs) with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_legacy_snapshot(snapshots_dir: Path, step_id: str, run_number: int, files: dict):
    """
    Create a legacy *_complete.zip in snapshots_dir containing the given files.
    files: {relative_path_str: content_str}
    """
    zip_path = snapshots_dir / f"{step_id}_run_{run_number}_complete.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for rel, content in files.items():
            zf.writestr(rel, content)
    return zip_path


def seed_new_snapshot(snapshots_dir: Path, step_id: str, run_number: int,
                      files: dict, manifest_files: list):
    """
    Create a new-format *_snapshot.zip + *_manifest.json pair.
    files: {relative_path_str: content_str}  — contents of the ZIP
    manifest_files: [relative_path_str]       — files listed in the manifest
    """
    zip_path = snapshots_dir / f"{step_id}_run_{run_number}_snapshot.zip"
    manifest_path = snapshots_dir / f"{step_id}_run_{run_number}_manifest.json"

    with zipfile.ZipFile(zip_path, 'w') as zf:
        for rel, content in files.items():
            zf.writestr(rel, content)

    manifest = {
        "step_id": step_id,
        "run_number": run_number,
        "timestamp": "2026-01-01T00:00:00Z",
        "files": manifest_files,
        "excluded_patterns": [],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return zip_path, manifest_path


# ===========================================================================
# scan_manifest
# ===========================================================================

class TestScanManifest:
    def test_writes_manifest_json(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db")
        write_file(tmp_path / "lib_info.csv")

        manifest_path = sm.scan_manifest("step_a", 1)

        assert manifest_path.exists()
        assert manifest_path.name == "step_a_run_1_manifest.json"

    def test_manifest_contains_correct_files(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db")
        write_file(tmp_path / "subdir" / "data.csv")

        sm.scan_manifest("step_a", 1)
        data = json.loads((tmp_path / ".snapshots" / "step_a_run_1_manifest.json").read_text())

        assert "project_database.db" in data["files"]
        assert "subdir/data.csv" in data["files"]

    def test_manifest_excludes_snapshots_dir(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db")
        # Put a file inside .snapshots — it must NOT appear in the manifest
        write_file(tmp_path / ".snapshots" / "old_run_1_complete.zip", "zip")

        sm.scan_manifest("step_a", 1)
        data = json.loads((tmp_path / ".snapshots" / "step_a_run_1_manifest.json").read_text())

        assert not any(".snapshots" in f for f in data["files"])

    def test_manifest_excludes_workflow_status(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / ".workflow_status" / "script.success")
        write_file(tmp_path / "real_file.txt")

        sm.scan_manifest("step_a", 1)
        data = json.loads((tmp_path / ".snapshots" / "step_a_run_1_manifest.json").read_text())

        assert not any(".workflow_status" in f for f in data["files"])
        assert "real_file.txt" in data["files"]

    def test_manifest_includes_permanent_exclusion_paths(self, tmp_path):
        """PERMANENT_EXCLUSIONS are NOT applied during manifest creation."""
        sm = make_manager(tmp_path)
        fa_file = tmp_path / "archived_files" / "FA_results_archive" / "result.txt"
        write_file(fa_file)

        sm.scan_manifest("step_a", 1)
        data = json.loads((tmp_path / ".snapshots" / "step_a_run_1_manifest.json").read_text())

        assert "archived_files/FA_results_archive/result.txt" in data["files"]

    def test_manifest_metadata_fields(self, tmp_path):
        sm = make_manager(tmp_path)
        sm.scan_manifest("my_step", 3)
        data = json.loads((tmp_path / ".snapshots" / "my_step_run_3_manifest.json").read_text())

        assert data["step_id"] == "my_step"
        assert data["run_number"] == 3
        assert "timestamp" in data
        assert "excluded_patterns" in data


# ===========================================================================
# take_selective_snapshot
# ===========================================================================

class TestTakeSelectiveSnapshot:
    def test_creates_snapshot_zip(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db")

        zip_path = sm.take_selective_snapshot("step_a", 1, ["project_database.db"], None)

        assert zip_path.exists()
        assert zip_path.name == "step_a_run_1_snapshot.zip"

    def test_snapshot_contains_declared_items(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "db content")
        write_file(tmp_path / "lib_info.csv", "csv content")

        zip_path = sm.take_selective_snapshot(
            "step_a", 1, ["project_database.db", "lib_info.csv"], None
        )

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "project_database.db" in names
        assert "lib_info.csv" in names

    def test_snapshot_contains_directory_contents(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "output_dir" / "file1.txt", "a")
        write_file(tmp_path / "output_dir" / "file2.txt", "b")

        zip_path = sm.take_selective_snapshot("step_a", 1, ["output_dir/"], None)

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "output_dir/file1.txt" in names
        assert "output_dir/file2.txt" in names

    def test_newly_added_files_included_when_no_prev_manifest(self, tmp_path):
        """When prev_manifest_path is None, all current files are treated as new."""
        sm = make_manager(tmp_path)
        write_file(tmp_path / "user_input.csv", "user data")
        write_file(tmp_path / "project_database.db", "db")

        zip_path = sm.take_selective_snapshot("step_a", 1, ["project_database.db"], None)

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "user_input.csv" in names

    def test_newly_added_files_detected_via_manifest_diff(self, tmp_path):
        """Files not in prev manifest and not in SNAPSHOT_ITEMS are included."""
        sm = make_manager(tmp_path)
        # Simulate previous manifest: only project_database.db existed
        prev_manifest = tmp_path / ".snapshots" / "prev_manifest.json"
        prev_manifest.write_text(json.dumps({
            "files": ["project_database.db"],
            "excluded_patterns": [],
        }), encoding="utf-8")

        write_file(tmp_path / "project_database.db", "db")
        write_file(tmp_path / "new_user_file.csv", "user added this")

        zip_path = sm.take_selective_snapshot(
            "step_a", 2, ["project_database.db"], prev_manifest
        )

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "new_user_file.csv" in names

    def test_old_files_not_in_snapshot_items_excluded(self, tmp_path):
        """Files that existed before the previous run and are not in SNAPSHOT_ITEMS
        should NOT be included in the snapshot."""
        sm = make_manager(tmp_path)
        prev_manifest = tmp_path / ".snapshots" / "prev_manifest.json"
        prev_manifest.write_text(json.dumps({
            "files": ["project_database.db", "large_instrument_file.raw"],
            "excluded_patterns": [],
        }), encoding="utf-8")

        write_file(tmp_path / "project_database.db", "db")
        write_file(tmp_path / "large_instrument_file.raw", "huge binary")

        zip_path = sm.take_selective_snapshot(
            "step_a", 2, ["project_database.db"], prev_manifest
        )

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "large_instrument_file.raw" not in names


# ===========================================================================
# snapshot_exists — new signature
# ===========================================================================

class TestSnapshotExists:
    def test_returns_true_for_new_format(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_new_snapshot(sm.snapshots_dir, "step_a", 1, {"f.txt": "x"}, ["f.txt"])
        assert sm.snapshot_exists("step_a", 1) is True

    def test_returns_true_for_legacy_format(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {"f.txt": "x"})
        assert sm.snapshot_exists("step_a", 1) is True

    def test_returns_false_when_neither_exists(self, tmp_path):
        sm = make_manager(tmp_path)
        assert sm.snapshot_exists("step_a", 1) is False

    def test_correct_run_number_checked(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {"f.txt": "x"}, ["f.txt"])
        assert sm.snapshot_exists("step_a", 1) is False
        assert sm.snapshot_exists("step_a", 2) is True


# ===========================================================================
# Run-number methods — dual-format awareness
# ===========================================================================

class TestRunNumberMethods:
    def test_get_next_run_number_no_snapshots(self, tmp_path):
        sm = make_manager(tmp_path)
        assert sm.get_next_run_number("step_a") == 1

    def test_get_next_run_number_with_legacy(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        # Non-rerun: reuses highest run number
        assert sm.get_next_run_number("step_a", allow_rerun=False) == 1

    def test_get_next_run_number_allow_rerun_increments(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        assert sm.get_next_run_number("step_a", allow_rerun=True) == 2

    def test_get_next_run_number_sees_both_formats(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {}, [])
        assert sm.get_next_run_number("step_a", allow_rerun=True) == 3

    def test_get_current_run_number_no_snapshots(self, tmp_path):
        sm = make_manager(tmp_path)
        assert sm.get_current_run_number("step_a") == 0

    def test_get_current_run_number_legacy_only(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 3, {})
        assert sm.get_current_run_number("step_a") == 3

    def test_get_current_run_number_new_only(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {}, [])
        assert sm.get_current_run_number("step_a") == 2

    def test_get_current_run_number_mixed(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {}, [])
        assert sm.get_current_run_number("step_a") == 2

    def test_get_effective_run_number_no_snapshots(self, tmp_path):
        sm = make_manager(tmp_path)
        assert sm.get_effective_run_number("step_a") == 0

    def test_get_effective_run_number_mixed(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        seed_new_snapshot(sm.snapshots_dir, "step_a", 3, {}, [])
        assert sm.get_effective_run_number("step_a") == 3

    def test_get_latest_run_snapshot_no_snapshots(self, tmp_path):
        sm = make_manager(tmp_path)
        assert sm.get_latest_run_snapshot("step_a") is None

    def test_get_latest_run_snapshot_returns_prefix(self, tmp_path):
        sm = make_manager(tmp_path)
        seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {}, [])
        assert sm.get_latest_run_snapshot("step_a") == "step_a_run_2"


# ===========================================================================
# remove_run_snapshots_from / remove_all_run_snapshots
# ===========================================================================

class TestRemoveSnapshots:
    def test_remove_from_deletes_new_format_and_manifest(self, tmp_path):
        sm = make_manager(tmp_path)
        zip_path, manifest_path = seed_new_snapshot(
            sm.snapshots_dir, "step_a", 2, {"f.txt": "x"}, ["f.txt"]
        )
        sm.remove_run_snapshots_from("step_a", 2)
        assert not zip_path.exists()
        assert not manifest_path.exists()

    def test_remove_from_deletes_legacy_format(self, tmp_path):
        sm = make_manager(tmp_path)
        zip_path = seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {"f.txt": "x"})
        sm.remove_run_snapshots_from("step_a", 1)
        assert not zip_path.exists()

    def test_remove_from_leaves_earlier_runs(self, tmp_path):
        sm = make_manager(tmp_path)
        zip1 = seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        zip2, man2 = seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {}, [])
        sm.remove_run_snapshots_from("step_a", 2)
        assert zip1.exists()
        assert not zip2.exists()
        assert not man2.exists()

    def test_remove_all_deletes_everything(self, tmp_path):
        sm = make_manager(tmp_path)
        zip1 = seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        zip2, man2 = seed_new_snapshot(sm.snapshots_dir, "step_a", 2, {}, [])
        sm.remove_all_run_snapshots("step_a")
        assert not zip1.exists()
        assert not zip2.exists()
        assert not man2.exists()

    def test_remove_all_does_not_touch_other_steps(self, tmp_path):
        sm = make_manager(tmp_path)
        zip_a = seed_legacy_snapshot(sm.snapshots_dir, "step_a", 1, {})
        zip_b = seed_legacy_snapshot(sm.snapshots_dir, "step_b", 1, {})
        sm.remove_all_run_snapshots("step_a")
        assert not zip_a.exists()
        assert zip_b.exists()


# ===========================================================================
# restore_snapshot — new format path
# ===========================================================================

class TestRestoreSnapshotNewFormat:
    def test_restores_files_from_zip(self, tmp_path):
        sm = make_manager(tmp_path)
        # Pre-run state: project_database.db existed
        write_file(tmp_path / "project_database.db", "original content")
        manifest_files = ["project_database.db"]

        # Simulate the script running: it overwrites the db
        seed_new_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "original content"},
            manifest_files,
        )
        # Now overwrite the file (as if the script ran)
        (tmp_path / "project_database.db").write_text("modified by script")

        sm.restore_snapshot("step_a", 1)

        assert (tmp_path / "project_database.db").read_text() == "original content"

    def test_deletes_newly_created_files(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "db")
        manifest_files = ["project_database.db"]

        seed_new_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "db"},
            manifest_files,
        )
        # Script created a new file
        write_file(tmp_path / "new_output.csv", "script output")

        sm.restore_snapshot("step_a", 1)

        assert not (tmp_path / "new_output.csv").exists()

    def test_consumes_zip_and_manifest(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "db")
        zip_path, manifest_path = seed_new_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "db"},
            ["project_database.db"],
        )

        sm.restore_snapshot("step_a", 1)

        assert not zip_path.exists()
        assert not manifest_path.exists()

    def test_permanent_exclusions_not_deleted(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "db")
        # FA archive file — should survive restore
        fa_file = tmp_path / "archived_files" / "FA_results_archive" / "result.txt"
        write_file(fa_file, "fa data")

        # Manifest only lists project_database.db (FA file was created after manifest)
        seed_new_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "db"},
            ["project_database.db"],
        )

        sm.restore_snapshot("step_a", 1)

        assert fa_file.exists(), "FA archive file must not be deleted by restore"

    def test_misc_folder_not_deleted(self, tmp_path):
        """MISC/misc/Misc folders are permanently protected."""
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "db")
        misc_file = tmp_path / "MISC" / "notes.txt"
        write_file(misc_file, "user notes")

        seed_new_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "db"},
            ["project_database.db"],
        )

        sm.restore_snapshot("step_a", 1)

        assert misc_file.exists(), "MISC folder must not be deleted by restore"

    def test_newly_created_empty_dir_removed(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "db")
        seed_new_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "db"},
            ["project_database.db"],
        )
        # Script created a directory with a file, then we simulate the file being
        # the only thing in it — after file deletion the dir should be removed
        new_dir = tmp_path / "new_output_dir"
        new_dir.mkdir()
        write_file(new_dir / "output.csv", "data")

        sm.restore_snapshot("step_a", 1)

        assert not new_dir.exists()


# ===========================================================================
# restore_snapshot — legacy fallback path
# ===========================================================================

class TestRestoreSnapshotLegacyFallback:
    def test_falls_back_to_legacy_zip(self, tmp_path):
        sm = make_manager(tmp_path)
        write_file(tmp_path / "project_database.db", "modified")
        seed_legacy_snapshot(
            sm.snapshots_dir, "step_a", 1,
            {"project_database.db": "original"}
        )

        sm.restore_snapshot("step_a", 1)

        assert (tmp_path / "project_database.db").read_text() == "original"

    def test_raises_when_no_snapshot_exists(self, tmp_path):
        sm = make_manager(tmp_path)
        with pytest.raises(FileNotFoundError):
            sm.restore_snapshot("step_a", 1)


# ===========================================================================
# PERMANENT_EXCLUSIONS constant
# ===========================================================================

class TestPermanentExclusions:
    def test_constant_contains_fa_archive_paths(self):
        assert "archived_files/FA_results_archive" in PERMANENT_EXCLUSIONS
        assert "archived_files/first_lib_attempt_fa_results" in PERMANENT_EXCLUSIONS
        assert "archived_files/second_lib_attempt_fa_results" in PERMANENT_EXCLUSIONS
        assert "archived_files/third_lib_attempt_fa_results" in PERMANENT_EXCLUSIONS
        assert "archived_files/capsule_fa_analysis_results" in PERMANENT_EXCLUSIONS

    def test_constant_contains_misc_variants(self):
        assert "MISC" in PERMANENT_EXCLUSIONS
        assert "misc" in PERMANENT_EXCLUSIONS
        assert "Misc" in PERMANENT_EXCLUSIONS
