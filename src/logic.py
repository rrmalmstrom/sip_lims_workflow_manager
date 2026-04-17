import json
import zipfile
import shutil
import subprocess
import sys
import datetime
import pty
import os
import select
import threading
import queue
import time
import re
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

# Native execution debug logging
from src.enhanced_debug_logger import (
    debug_context, log_info, log_error, log_warning,
    debug_enabled
)

# ---------------------------------------------------------------------------
# Undo system constants — module level so every method references the same set
# ---------------------------------------------------------------------------

# FA archive subfolders that are PERMANENTLY PROTECTED from undo/rollback.
# The undo system will never delete files under these paths, even if they
# appear as "newly created" relative to a pre-run manifest.
# Add new entries here if a future workflow uses a different archive path.
PERMANENT_EXCLUSIONS = {
    "archived_files/FA_results_archive",            # All workflows going forward (universal)
    "archived_files/first_lib_attempt_fa_results",  # SIP + SPS-CE legacy projects
    "archived_files/second_lib_attempt_fa_results", # SIP + SPS-CE legacy projects
    "archived_files/third_lib_attempt_fa_results",  # SIP + SPS-CE legacy projects
    "archived_files/capsule_fa_analysis_results",   # Capsule legacy projects
    "MISC",                                         # User misc folders (case variants)
    "misc",
    "Misc",
}

# Standard patterns excluded from manifest scans and snapshot operations.
# These are never included in manifests and never deleted during undo/rollback.
_MANIFEST_EXCLUDE_PATTERNS = {
    '.snapshots',
    '.workflow_status',
    '.workflow_logs',
    'workflow.yml',
    '__pycache__',
    '.DS_Store',
}

@dataclass
class RunResult:
    """Holds the results of a script execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int

class StateManager:
    """Manages the state of a workflow."""
    def __init__(self, state_file_path: Path):
        self.path = state_file_path

    def load(self) -> Dict[str, Any]:
        """
        Loads the current state from the state file with retry logic for external drives.
        Handles temporary corruption and race conditions.
        """
        if not self.path.exists():
            return {}
        
        # Retry logic for external drive race conditions
        max_retries = 3
        retry_delay = 0.1  # 100ms delay between retries
        
        for attempt in range(max_retries):
            try:
                with self.path.open('r') as f:
                    content = f.read().strip()
                    if not content:
                        # File is empty - likely caught during write operation
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                            continue
                        else:
                            # Last attempt failed - return empty state
                            print(f"WARNING: workflow_state.json is empty after {max_retries} attempts")
                            return {}
                    
                    # Parse the JSON content
                    f.seek(0)  # Reset file pointer
                    return json.load(f)
                    
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    # Temporary corruption - retry after delay
                    import time
                    print(f"JSON decode error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed - log error and return empty state
                    print(f"CRITICAL: JSON corruption persists after {max_retries} attempts: {e}")
                    print(f"File path: {self.path}")
                    print("Returning empty state to prevent application crash")
                    return {}
            except Exception as e:
                if attempt < max_retries - 1:
                    # Other error - retry after delay
                    import time
                    print(f"File read error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed - log error and return empty state
                    print(f"CRITICAL: File read error persists after {max_retries} attempts: {e}")
                    return {}
        
        # Should never reach here, but return empty state as fallback
        return {}

    def save(self, state: Dict[str, Any]):
        """
        Saves the given state to the state file using atomic write operation.
        This prevents race conditions on external drives by using write-then-rename.
        """
        import tempfile
        import os
        
        # Create a temporary file in the same directory as the target file
        temp_dir = self.path.parent
        temp_fd, temp_path = tempfile.mkstemp(dir=temp_dir, suffix='.tmp', prefix='workflow_state_')
        
        try:
            # Write to temporary file first
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(state, f, indent=2)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force write to disk (important for external drives)
            
            # Atomically replace the original file
            if os.name == 'nt':  # Windows
                # Windows requires removing the target file first
                if self.path.exists():
                    self.path.unlink()
                os.rename(temp_path, self.path)
            else:  # Unix/macOS
                # Unix systems support atomic rename even if target exists
                os.rename(temp_path, self.path)
                
        except Exception:
            # Clean up temporary file if something went wrong
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def get_step_state(self, step_id: str) -> str:
        """Gets the status of a specific step."""
        state = self.load()
        return state.get(step_id, "pending")

    def get_completion_order(self) -> List[str]:
        """Gets the chronological completion order of steps."""
        state = self.load()
        return state.get("_completion_order", [])

    def update_step_state(self, step_id: str, status: str):
        """Updates the status of a specific step and saves it."""
        state = self.load()
        old_status = state.get(step_id, "pending")
        state[step_id] = status
        
        # Ensure completion order array exists
        if "_completion_order" not in state:
            state["_completion_order"] = []
        
        # Track completion order for chronological undo
        if status == "completed":
            # Always add to completion order when step becomes completed
            # This handles both first-time completions and re-runs
            state["_completion_order"].append(step_id)
        elif status == "pending" and old_status == "completed":
            # Step undone - remove from completion order (from the end, most recent first)
            completion_order = state["_completion_order"]
            # Remove the most recent occurrence of this step_id
            for i in range(len(completion_order) - 1, -1, -1):
                if completion_order[i] == step_id:
                    completion_order.pop(i)
                    break
        
        self.save(state)

    def get_last_completed_step_chronological(self) -> str:
        """
        Gets the most recently completed step based on chronological order.
        Returns None if no steps have been completed.
        """
        completion_order = self.get_completion_order()
        return completion_order[-1] if completion_order else None

class SnapshotManager:
    """Manages project snapshots."""
    def __init__(self, project_path: Path, snapshots_dir: Path):
        self.project_path = project_path
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(exist_ok=True)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _scan_project_paths(self) -> set:
        """
        Returns a set of relative path strings for every file currently in the
        project directory, excluding the standard manifest exclusion patterns.
        PERMANENT_EXCLUSIONS are NOT applied here — they are only applied
        during rollback when deciding what to delete.
        """
        paths = set()
        for file_path in self.project_path.rglob('*'):
            if not file_path.is_file():
                continue
            # Skip if any part of the path matches the exclude patterns
            if any(part in _MANIFEST_EXCLUDE_PATTERNS for part in file_path.parts):
                continue
            if file_path.name in _MANIFEST_EXCLUDE_PATTERNS:
                continue
            paths.add(str(file_path.relative_to(self.project_path)))
        return paths

    def _scan_project_dirs(self) -> set:
        """
        Returns a set of relative path strings for every directory currently in
        the project directory, excluding the standard manifest exclusion patterns.

        This is used by scan_manifest() to explicitly record directories so that
        empty directories created by a previous step are not mistakenly treated
        as "newly created" during a subsequent step's rollback.
        """
        dirs = set()
        for dir_path in self.project_path.rglob('*'):
            if not dir_path.is_dir():
                continue
            if any(part in _MANIFEST_EXCLUDE_PATTERNS for part in dir_path.parts):
                continue
            if dir_path.name in _MANIFEST_EXCLUDE_PATTERNS:
                continue
            dirs.add(str(dir_path.relative_to(self.project_path)))
        return dirs

    def _get_run_numbers(self, step_id: str) -> list:
        """
        Returns a sorted list of run numbers for which any snapshot file
        (new-format *_snapshot.zip OR legacy *_complete.zip) exists.
        """
        run_numbers = set()
        # New-format snapshots
        pattern_new = re.compile(r'_run_(\d+)_snapshot$')
        for f in self.snapshots_dir.glob(f"{step_id}_run_*_snapshot.zip"):
            m = pattern_new.search(f.stem)
            if m:
                run_numbers.add(int(m.group(1)))
        # Legacy snapshots
        pattern_legacy = re.compile(r'_run_(\d+)_complete$')
        for f in self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip"):
            m = pattern_legacy.search(f.stem)
            if m:
                run_numbers.add(int(m.group(1)))
        return sorted(run_numbers)

    @staticmethod
    def _safe_delete(path: Path, retries: int = 3, delay: float = 1.0):
        """
        Deletes a file with retry logic for network-drive "file in use" errors.
        Logs a warning (does not raise) if all retries are exhausted.
        """
        for attempt in range(retries):
            try:
                path.unlink()
                return
            except OSError:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    print(f"WARNING: Could not delete {path} after {retries} attempts")

    # -----------------------------------------------------------------------
    # Manifest operations
    # -----------------------------------------------------------------------

    def scan_manifest(self, step_id: str, run_number: int) -> Path:
        """
        Writes a manifest JSON file capturing the current set of file paths AND
        directories in the project directory.  This is a fast metadata-only scan
        — no file contents are read.

        Directories are recorded explicitly so that empty directories created by
        a previous step are not mistakenly treated as "newly created" during a
        subsequent step's rollback (the bug where _restore_from_selective_snapshot
        deleted empty dirs that were not represented in the files-only manifest).

        Returns the Path of the written manifest file.
        """
        manifest_path = self.snapshots_dir / f"{step_id}_run_{run_number}_manifest.json"
        current_paths = sorted(self._scan_project_paths())
        current_dirs = sorted(self._scan_project_dirs())

        manifest = {
            "step_id": step_id,
            "run_number": run_number,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "files": current_paths,
            "directories": current_dirs,
            "excluded_patterns": sorted(_MANIFEST_EXCLUDE_PATTERNS),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(
            f"MANIFEST: Written {manifest_path.name} "
            f"({len(current_paths)} files, {len(current_dirs)} dirs)"
        )
        return manifest_path

    def _load_manifest_paths(self, manifest_path: Path) -> set:
        """
        Loads a manifest JSON file and returns the set of file path strings it
        contains.  Returns an empty set if the file does not exist.
        """
        if not manifest_path.exists():
            return set()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return set(data.get("files", []))

    def _load_manifest_dirs(self, manifest_path: Path) -> set:
        """
        Loads a manifest JSON file and returns the set of directory path strings
        it contains.  Returns an empty set if the file does not exist or if the
        manifest was written by an older version that did not record directories.

        The caller falls back to deriving dirs from file parent paths when this
        returns an empty set (backward compatibility with old manifests).
        """
        if not manifest_path.exists():
            return set()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return set(data.get("directories", []))

    # -----------------------------------------------------------------------
    # Selective snapshot (new format)
    # -----------------------------------------------------------------------

    def take_selective_snapshot(
        self,
        step_id: str,
        run_number: int,
        snapshot_items: List[str],
        prev_manifest_path,   # Path | None
    ) -> Path:
        """
        Creates a targeted snapshot ZIP containing:
          1. Files/folders listed in snapshot_items (the script's declared outputs)
          2. Files newly added by the user since the previous completed run
             (identified by diffing current paths against the previous manifest)

        prev_manifest_path: Path to the manifest from the previous completed run,
                            or None if this is the very first run of the project
                            (in which case all current files are treated as new).

        Returns the Path of the written ZIP file.
        """
        zip_path = self.snapshots_dir / f"{step_id}_run_{run_number}_snapshot.zip"

        current_paths = self._scan_project_paths()
        prev_paths = self._load_manifest_paths(prev_manifest_path) if prev_manifest_path else set()

        # Resolve snapshot_items to relative path strings (normalise trailing slash)
        snapshot_item_paths = set()
        for item in snapshot_items:
            item_path = self.project_path / item.rstrip('/')
            if item_path.is_dir():
                for f in item_path.rglob('*'):
                    if f.is_file():
                        snapshot_item_paths.add(str(f.relative_to(self.project_path)))
            elif item_path.is_file():
                snapshot_item_paths.add(str(item_path.relative_to(self.project_path)))
            else:
                # Item declared but not yet present — still record the declared path
                # so we know to look for it during restore
                snapshot_item_paths.add(item.rstrip('/'))

        newly_added = current_paths - prev_paths - snapshot_item_paths

        files_to_zip = snapshot_item_paths | newly_added

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for rel_str in sorted(files_to_zip):
                full_path = self.project_path / rel_str
                if full_path.is_file():
                    zf.write(full_path, rel_str)

        print(
            f"SNAPSHOT: Selective snapshot written {zip_path.name} "
            f"({len(files_to_zip)} files: {len(snapshot_item_paths)} declared, "
            f"{len(newly_added)} newly-added)"
        )
        return zip_path

    # -----------------------------------------------------------------------
    # Restore operations
    # -----------------------------------------------------------------------

    def restore_snapshot(self, step_id: str, run_number: int):
        """
        Primary restore entry point.  Tries the new selective format first,
        then falls back to the legacy complete ZIP.

        Raises FileNotFoundError if neither format exists.
        """
        new_zip = self.snapshots_dir / f"{step_id}_run_{run_number}_snapshot.zip"
        new_manifest = self.snapshots_dir / f"{step_id}_run_{run_number}_manifest.json"

        if new_zip.exists() and new_manifest.exists():
            self._restore_from_selective_snapshot(new_zip, new_manifest)
            return

        # Fall back to legacy complete ZIP
        legacy_zip = self.snapshots_dir / f"{step_id}_run_{run_number}_complete.zip"
        if legacy_zip.exists():
            self._restore_from_complete_snapshot(legacy_zip)
            return

        raise FileNotFoundError(
            f"No snapshot found for {step_id} run {run_number} "
            f"(checked {new_zip.name} and {legacy_zip.name})"
        )

    def _restore_from_selective_snapshot(self, zip_path: Path, manifest_path: Path):
        """
        Restores the project to its pre-run state using the new selective format:
          1. Diff manifest vs current state → identify newly-created files/dirs
          2. Delete newly-created files (respecting PERMANENT_EXCLUSIONS)
          3. Delete newly-created empty directories (deepest first)
          4. Extract the snapshot ZIP to restore SNAPSHOT_ITEMS + user-added files
          5. Delete the ZIP and manifest (they are consumed by this restore)

        Directory tracking fix: pre_run_dirs is loaded directly from the manifest's
        "directories" field (written by scan_manifest since the fix).  This ensures
        that empty directories created by a *previous* step — which have no files
        and therefore no representation in the files list — are correctly recognised
        as pre-existing and are NOT deleted during rollback.

        Backward compatibility: manifests written before the fix have no
        "directories" key.  In that case we fall back to deriving pre_run_dirs
        from the file parent paths (old behaviour), which may still incorrectly
        delete empty dirs from earlier steps, but at least does not break existing
        projects.
        """
        pre_run_paths = self._load_manifest_paths(manifest_path)
        current_paths = self._scan_project_paths()

        newly_created_files = current_paths - pre_run_paths

        # --- Delete newly-created files (skip permanently protected paths) ---
        for rel_str in newly_created_files:
            if any(rel_str.startswith(prefix) for prefix in PERMANENT_EXCLUSIONS):
                print(f"RESTORE: Skipping permanently protected path: {rel_str}")
                continue
            full_path = self.project_path / rel_str
            if full_path.is_file():
                self._safe_delete(full_path)
                print(f"RESTORE: Deleted newly-created file {rel_str}")

        # --- Delete newly-created empty directories (deepest first) ---
        # Load pre-run dirs from the manifest's explicit "directories" field.
        # This correctly handles empty directories created by a previous step
        # (they have no files, so they would be invisible if we only derived
        # dirs from file parent paths).
        pre_run_dirs = self._load_manifest_dirs(manifest_path)
        if not pre_run_dirs:
            # Backward-compat fallback: manifest was written before the fix and
            # has no "directories" key — derive from file parent paths as before.
            for p in pre_run_paths:
                for parent in Path(p).parents:
                    if str(parent) != '.':
                        pre_run_dirs.add(str(parent))

        current_dirs = set()
        for file_path in self.project_path.rglob('*'):
            if file_path.is_dir():
                rel = str(file_path.relative_to(self.project_path))
                if not any(part in _MANIFEST_EXCLUDE_PATTERNS for part in file_path.parts):
                    current_dirs.add(rel)

        newly_created_dirs = current_dirs - pre_run_dirs
        for rel_str in sorted(newly_created_dirs, key=lambda p: len(Path(p).parts), reverse=True):
            if any(rel_str.startswith(prefix) for prefix in PERMANENT_EXCLUSIONS):
                continue
            full_path = self.project_path / rel_str
            if full_path.exists() and full_path.is_dir():
                try:
                    if not any(full_path.iterdir()):
                        full_path.rmdir()
                        print(f"RESTORE: Removed newly-created empty directory {rel_str}")
                except OSError:
                    pass

        # --- Extract snapshot ZIP to restore pre-run files ---
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                zf.extract(member, self.project_path)
                extracted_path = self.project_path / member.filename
                if extracted_path.exists():
                    try:
                        timestamp = time.mktime(member.date_time + (0, 0, -1))
                        os.utime(extracted_path, (timestamp, timestamp))
                    except (OSError, ValueError):
                        pass

        print(f"RESTORE: Selective snapshot restored from {zip_path.name}")

        # --- Consume the snapshot pair ---
        self._safe_delete(zip_path)
        self._safe_delete(manifest_path)

    def _restore_from_complete_snapshot(self, zip_path: Path):
        """
        Legacy restore path: extracts a complete-project ZIP, removing files
        that exist now but were not in the snapshot.

        This is the renamed version of the old restore_complete_snapshot() method,
        now accepting a Path directly instead of constructing it from a step_id.
        The old public restore_complete_snapshot(step_id) wrapper is kept below
        for backward compatibility during the Checkpoint B transition.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"Legacy snapshot not found: {zip_path}")

        preserve_patterns = {
            '.snapshots', '.workflow_status', '.workflow_logs',
            'workflow.yml', '__pycache__',
        }
        fa_archive_patterns = {
            'archived_files/first_lib_attempt_fa_results',
            'archived_files/second_lib_attempt_fa_results',
            'archived_files/third_lib_attempt_fa_results',
        }

        current_files = set()
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                if any(part in preserve_patterns for part in file_path.parts):
                    continue
                if file_path.name in preserve_patterns:
                    continue
                relative_path = file_path.relative_to(self.project_path)
                if any(str(relative_path).startswith(p) for p in fa_archive_patterns):
                    continue
                current_files.add(file_path.relative_to(self.project_path))

        snapshot_files = set()
        empty_dirs_to_preserve = set()
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if not name.endswith('/'):
                    path = Path(name)
                    if path.name == ".keep_empty_dir":
                        empty_dirs_to_preserve.add(path.parent)
                    else:
                        snapshot_files.add(path)

        for rel_path in current_files - snapshot_files:
            file_path = self.project_path / rel_path
            if file_path.exists():
                file_path.unlink()
                print(f"RESTORE: Removed {rel_path}")

        for dir_path in sorted(self.project_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and dir_path != self.project_path:
                if any(part in preserve_patterns for part in dir_path.parts):
                    continue
                if dir_path.name in preserve_patterns:
                    continue
                rel_dir = dir_path.relative_to(self.project_path)
                if any(str(rel_dir).startswith(p) for p in fa_archive_patterns):
                    continue
                if rel_dir in empty_dirs_to_preserve:
                    continue
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        print(f"RESTORE: Removed empty directory {rel_dir}")
                except OSError:
                    pass

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                zf.extract(member, self.project_path)
                extracted_path = self.project_path / member.filename
                if extracted_path.exists():
                    try:
                        timestamp = time.mktime(member.date_time + (0, 0, -1))
                        os.utime(extracted_path, (timestamp, timestamp))
                    except (OSError, ValueError):
                        pass

        for empty_dir in empty_dirs_to_preserve:
            dir_path = self.project_path / empty_dir
            placeholder_file = dir_path / ".keep_empty_dir"
            dir_path.mkdir(parents=True, exist_ok=True)
            if placeholder_file.exists():
                placeholder_file.unlink()

        print(f"RESTORE: Legacy complete snapshot restored from {zip_path.name}")

    # -----------------------------------------------------------------------
    # Run-number methods — updated to handle both new and legacy formats
    # -----------------------------------------------------------------------

    def get_next_run_number(self, step_id: str, allow_rerun: bool = False) -> int:
        """
        Gets the next run number for a step by checking existing run snapshots
        (both new *_snapshot.zip and legacy *_complete.zip formats).

        For normal steps: Returns 1 if no snapshots exist, or reuses the highest
                         existing run number if step is pending (after undo)
        For re-run allowed steps: Always increments based on existing snapshots
        """
        run_numbers = self._get_run_numbers(step_id)
        if not run_numbers:
            return 1

        max_run = max(run_numbers)

        if allow_rerun:
            return max_run + 1
        else:
            # Reuse the highest run number — handles the case where a step was
            # undone and is being run again
            return max_run

    def get_latest_run_snapshot(self, step_id: str) -> str:
        """
        Gets the snapshot name prefix for the most recent run of a step.
        Returns None if no run snapshots exist.
        Checks both new-format and legacy formats.
        """
        run_numbers = self._get_run_numbers(step_id)
        if not run_numbers:
            return None
        latest_run = max(run_numbers)
        return f"{step_id}_run_{latest_run}"

    def get_current_run_number(self, step_id: str) -> int:
        """
        Gets the current run number for a step (highest existing run).
        Returns 0 if no runs exist.
        Checks both new-format and legacy formats.
        """
        run_numbers = self._get_run_numbers(step_id)
        return max(run_numbers) if run_numbers else 0

    def snapshot_exists(self, step_id: str, run_number: int) -> bool:
        """
        Check if a snapshot exists for the given step and run number.
        Checks for both new-format *_snapshot.zip and legacy *_complete.zip.

        NOTE: Signature changed from snapshot_exists(snapshot_name: str) to
        snapshot_exists(step_id: str, run_number: int) in Stage 2.
        All callers in core.py and app.py must be updated accordingly.
        """
        new_zip = self.snapshots_dir / f"{step_id}_run_{run_number}_snapshot.zip"
        legacy_zip = self.snapshots_dir / f"{step_id}_run_{run_number}_complete.zip"
        return new_zip.exists() or legacy_zip.exists()

    def get_effective_run_number(self, step_id: str) -> int:
        """
        Gets the effective current run number by checking which snapshots exist.
        This represents how many times the step has been successfully completed.
        Checks both new-format and legacy formats.
        """
        run_numbers = self._get_run_numbers(step_id)
        return max(run_numbers) if run_numbers else 0

    def remove_run_snapshots_from(self, step_id: str, run_number: int):
        """
        Remove all run snapshots (both new and legacy formats) from the
        specified run number onwards, including paired manifest files.
        """
        # New-format snapshots
        pattern_new = re.compile(r'_run_(\d+)_snapshot$')
        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_snapshot.zip")):
            m = pattern_new.search(f.stem)
            if m and int(m.group(1)) >= run_number:
                f.unlink()
                print(f"UNDO: Removed snapshot {f.name}")
                manifest = self.snapshots_dir / f.name.replace("_snapshot.zip", "_manifest.json")
                if manifest.exists():
                    manifest.unlink()
                    print(f"UNDO: Removed manifest {manifest.name}")

        # Legacy-format snapshots
        pattern_legacy = re.compile(r'_run_(\d+)_complete$')
        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip")):
            m = pattern_legacy.search(f.stem)
            if m and int(m.group(1)) >= run_number:
                f.unlink()
                print(f"UNDO: Removed snapshot {f.name}")

    def remove_all_run_snapshots(self, step_id: str):
        """
        Remove all run snapshots for a step (both new and legacy formats),
        including paired manifest files.
        """
        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_snapshot.zip")):
            try:
                f.unlink()
                print(f"UNDO: Removed snapshot {f.name}")
            except OSError:
                pass
            manifest = self.snapshots_dir / f.name.replace("_snapshot.zip", "_manifest.json")
            if manifest.exists():
                try:
                    manifest.unlink()
                    print(f"UNDO: Removed manifest {manifest.name}")
                except OSError:
                    pass

        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip")):
            try:
                f.unlink()
                print(f"UNDO: Removed snapshot {f.name}")
            except OSError:
                pass

    def restore_complete_snapshot(self, step_id: str):
        """
        Restores the complete project directory from a snapshot.
        This will remove all files not in the snapshot and restore the exact state.
        """
        zip_path = self.snapshots_dir / f"{step_id}_complete.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Complete snapshot for step '{step_id}' not found.")
        
        # Files and directories to preserve (never delete)
        preserve_patterns = {
            '.snapshots',
            '.workflow_status',
            '.workflow_logs',
            'workflow.yml',
            '__pycache__'
        }
        
        # FA result archive directories to preserve (never delete during restore)
        # These should only match files under archived_files/ directory
        fa_archive_patterns = {
            'archived_files/first_lib_attempt_fa_results',
            'archived_files/second_lib_attempt_fa_results',
            'archived_files/third_lib_attempt_fa_results'
        }
        
        # Get list of files currently in project
        current_files = set()
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                # Skip preserved files
                if any(part in preserve_patterns for part in file_path.parts):
                    continue
                if file_path.name in preserve_patterns:
                    continue
                # Skip FA result archive files to preserve them during restore
                relative_path = file_path.relative_to(self.project_path)
                if any(str(relative_path).startswith(pattern) for pattern in fa_archive_patterns):
                    continue
                current_files.add(file_path.relative_to(self.project_path))
        
        # Get list of files in snapshot and identify empty directory placeholders
        snapshot_files = set()
        empty_dirs_to_preserve = set()
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if not name.endswith('/'):
                    path = Path(name)
                    if path.name == ".keep_empty_dir":
                        # This is a placeholder for an empty directory
                        empty_dirs_to_preserve.add(path.parent)
                    else:
                        snapshot_files.add(path)
        
        # Remove files that exist now but weren't in the snapshot
        files_to_remove = current_files - snapshot_files
        for rel_path in files_to_remove:
            file_path = self.project_path / rel_path
            if file_path.exists():
                file_path.unlink()
                print(f"RESTORE: Removed {rel_path}")
        
        # Remove empty directories that shouldn't exist (not in snapshot and not preserved)
        for dir_path in sorted(self.project_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and dir_path != self.project_path:
                # Skip preserved directories
                if any(part in preserve_patterns for part in dir_path.parts):
                    continue
                if dir_path.name in preserve_patterns:
                    continue
                
                # Skip FA result archive directories to preserve them during restore
                rel_dir = dir_path.relative_to(self.project_path)
                if any(str(rel_dir).startswith(pattern) for pattern in fa_archive_patterns):
                    continue
                
                # Skip directories that should be preserved from snapshot
                rel_dir = dir_path.relative_to(self.project_path)
                if rel_dir in empty_dirs_to_preserve:
                    continue
                
                try:
                    if not any(dir_path.iterdir()):  # Directory is empty
                        dir_path.rmdir()
                        print(f"RESTORE: Removed empty directory {rel_dir}")
                except OSError:
                    pass  # Directory not empty or other error
        
        # Extract snapshot files while preserving timestamps
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                # Extract the file or directory
                zf.extract(member, self.project_path)
                
                # Restore the original timestamp for both files and directories
                extracted_path = self.project_path / member.filename
                if extracted_path.exists():
                    try:
                        # Convert ZIP timestamp to Unix timestamp
                        timestamp = time.mktime(member.date_time + (0, 0, -1))
                        # Set both access time and modification time to the original
                        os.utime(extracted_path, (timestamp, timestamp))
                    except (OSError, ValueError):
                        # If timestamp restoration fails, continue without error
                        # This ensures rollback still works even if timestamp preservation fails
                        pass
        
        # Clean up placeholder files and ensure empty directories exist
        for empty_dir in empty_dirs_to_preserve:
            dir_path = self.project_path / empty_dir
            placeholder_file = dir_path / ".keep_empty_dir"
            
            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Remove placeholder file if it exists
            if placeholder_file.exists():
                placeholder_file.unlink()
        
        print(f"RESTORE: Complete project state restored from step {step_id}")

    def restore(self, step_id: str, items: List[str]):
        """Restores the project state from a snapshot."""
        zip_path = self.snapshots_dir / f"{step_id}.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Snapshot for step '{step_id}' not found.")

        for item_name in items:
            item_path = self.project_path / item_name
            if item_path.exists():
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()

        # Extract files while preserving timestamps
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                # Extract the file or directory
                zf.extract(member, self.project_path)
                
                # Restore the original timestamp for both files and directories
                extracted_path = self.project_path / member.filename
                if extracted_path.exists():
                    try:
                        # Convert ZIP timestamp to Unix timestamp
                        timestamp = time.mktime(member.date_time + (0, 0, -1))
                        # Set both access time and modification time to the original
                        os.utime(extracted_path, (timestamp, timestamp))
                    except (OSError, ValueError):
                        # If timestamp restoration fails, continue without error
                        pass

    def restore_file_from_latest_snapshot(self, filename: str) -> bool:
        """Finds the most recent snapshot and restores a single file from it."""
        snapshots = list(self.snapshots_dir.glob("*.zip"))
        if not snapshots:
            return False

        latest_snapshot = max(snapshots, key=lambda f: f.stat().st_mtime)
        
        with zipfile.ZipFile(latest_snapshot, 'r') as zf:
            if filename in zf.namelist():
                zf.extract(filename, self.project_path)
                return True
        return False

class ScriptRunner:
    """Executes workflow scripts using pseudo-terminal for interactive execution."""
    def __init__(self, project_path: Path, script_path: Path):
        self.project_path = project_path
        # NO FALLBACKS! script_path is REQUIRED for native execution
        if script_path is None:
            raise ValueError(
                "script_path is required for ScriptRunner. "
                "The system must know exactly where workflow scripts are located. "
                "This should be passed from Project which gets it from environment variables."
            )
        self.script_path = script_path
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.output_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.reader_thread = None
        self.is_running_flag = threading.Event()

    def is_running(self):
        return self.is_running_flag.is_set()

    def _read_output_loop(self):
        """
        Reads output from the pseudo-terminal until the process finishes,
        then puts the final result in the result queue.
        """
        # Create hidden log directory if it doesn't exist
        log_dir = self.project_path / ".workflow_logs"
        log_dir.mkdir(exist_ok=True)
        debug_log_path = log_dir / "debug_script_execution.log"
        
        def log_debug(message):
            """Log debug info to file only (not to terminal output)"""
            try:
                with open(debug_log_path, "a") as f:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {message}")
                    f.flush()
            except:
                pass  # Don't let logging errors break execution
        
        def log_to_terminal(message):
            """Log message to terminal output only"""
            self.output_queue.put(message)
        
        try:
            # Log debug info to file only (not visible to user)
            log_debug("=== SCRIPT STARTING (PTY) ===\n")
            log_debug(f"Process PID: {self.process.pid if self.process else 'None'}\n")
            log_debug(f"Master FD: {self.master_fd}\n")
            log_debug(f"Project path: {self.project_path}\n")
            
            # Read output from pseudo-terminal in real-time
            # Give the process a moment to start and produce initial output
            time.sleep(0.05)  # Small delay to let process start
            
            while self.is_running_flag.is_set() and self.master_fd is not None:
                try:
                    # Check if process is still running
                    if self.process:
                        poll_result = self.process.poll()
                        if poll_result is not None:
                            # Process finished - do one final read to get any remaining output
                            log_debug(f"=== PROCESS FINISHED WITH POLL RESULT: {poll_result} ===\n")
                            # Try to read any remaining output before breaking
                            try:
                                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                                if ready:
                                    output = os.read(self.master_fd, 4096).decode('utf-8', errors='replace')
                                    if output:
                                        self.output_queue.put(output)
                            except OSError:
                                pass
                            break
                    
                    # Use select to check if there's data to read with shorter timeout for responsiveness
                    ready, _, _ = select.select([self.master_fd], [], [], 0.02)  # Reduced from 0.1 to 0.02
                    if ready:
                        try:
                            # Read available data - try to read more at once for better performance
                            output = os.read(self.master_fd, 4096).decode('utf-8', errors='replace')
                            if output:
                                self.output_queue.put(output)
                                # Immediately check for more data without waiting
                                continue
                        except OSError:
                            # PTY closed
                            break
                    else:
                        # No data ready, small sleep to prevent busy waiting
                        time.sleep(0.01)
                    
                except Exception as e:
                    log_debug(f"Error reading PTY output: {str(e)}\n")
                    break
            
            # Get the final exit code
            if self.process:
                return_code = self.process.wait()  # Ensure process is fully finished
                success = return_code == 0
                
                # Log debug info to file only (not visible to user)
                debug_msg = f"""=== SCRIPT EXECUTION COMPLETE (PTY) ===
Exit Code: {return_code}
Success: {success}
Process Poll Result: {self.process.poll()}
Return Code Type: {type(return_code)}
=== END DEBUG INFO ===
"""
                log_debug(debug_msg)
                
                # Put the result in the queue
                result = RunResult(
                    success=success,
                    stdout="",  # We stream output in real-time, so this is empty
                    stderr="",  # PTY merges stderr into stdout
                    return_code=return_code
                )
                log_debug(f"=== PUTTING RESULT IN QUEUE: success={success}, return_code={return_code} ===\n")
                self.result_queue.put(result)
                
                # ALSO write a summary file that we can easily check
                log_dir = self.project_path / ".workflow_logs"
                log_dir.mkdir(exist_ok=True)
                summary_path = log_dir / "last_script_result.txt"
                try:
                    with open(summary_path, "w") as f:
                        f.write(f"Last Script Execution Summary\n")
                        f.write(f"Exit Code: {return_code}\n")
                        f.write(f"Success: {success}\n")
                        f.write(f"Timestamp: {datetime.datetime.now()}\n")
                except:
                    pass

        except Exception as e:
            error_msg = f"[ERROR] Exception in script runner: {str(e)}\n"
            log_debug(error_msg)
            # Show error to user since this indicates a real problem
            log_to_terminal(f"Error: {str(e)}\n")
            self.result_queue.put(RunResult(success=False, stdout="", stderr=str(e), return_code=-1))
        finally:
            self.is_running_flag.clear()
            log_debug("=== SCRIPT RUNNER THREAD ENDING ===\n")
            self.output_queue.put(None)  # Sentinel for end of output
            
            # Clean up PTY
            if self.master_fd is not None:
                try:
                    os.close(self.master_fd)
                except:
                    pass
                self.master_fd = None
            if self.slave_fd is not None:
                try:
                    os.close(self.slave_fd)
                except:
                    pass
                self.slave_fd = None

    def run(self, script_path_str: str, args: List[str] = None):
        """
        Executes a script using pseudo-terminal for interactive execution.
        This method is non-blocking.
        """
        if self.is_running():
            raise RuntimeError("A script is already running.")

        if args is None:
            args = []

        if getattr(sys, 'frozen', False):
            app_dir = Path(sys._MEIPASS).parent
        else:
            app_dir = Path(__file__).parent.parent

        script_filename = Path(script_path_str).name
        script_path = self.script_path / script_filename
        
        # CRITICAL DEBUG: Log script path resolution
        if debug_enabled():
            log_info("Script execution attempt",
                    script_filename=script_filename,
                    script_path_str=script_path_str,
                    resolved_script_path=str(script_path),
                    script_path_directory=str(self.script_path),
                    script_exists=script_path.exists())
        
        if not script_path.exists():
            # CRITICAL DEBUG: Log the failure details
            if debug_enabled():
                log_error("Script not found - CRITICAL PATH ISSUE",
                         script_filename=script_filename,
                         looking_in_directory=str(self.script_path),
                         full_resolved_path=str(script_path),
                         directory_exists=self.script_path.exists(),
                         directory_contents=list(str(f) for f in self.script_path.iterdir()) if self.script_path.exists() else "DIRECTORY_DOES_NOT_EXIST")
            raise FileNotFoundError(f"Script '{script_filename}' not found in '{self.script_path}'")

        python_executable = sys.executable
        command = [python_executable, "-u", str(script_path)] + args

        # Create pseudo-terminal
        self.master_fd, self.slave_fd = pty.openpty()

        # Start the subprocess with PTY
        self.process = subprocess.Popen(
            command,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            cwd=self.project_path,
            preexec_fn=os.setsid  # Create new session
        )

        # Start the output reading thread
        self.is_running_flag.set()
        self.reader_thread = threading.Thread(target=self._read_output_loop)
        self.reader_thread.start()

    def send_input(self, user_input: str):
        """Sends user input to the running script's stdin via PTY."""
        if self.master_fd is not None and self.is_running():
            try:
                os.write(self.master_fd, (user_input + "\n").encode('utf-8'))
            except Exception as e:
                self.output_queue.put(f"Error sending input: {str(e)}\n")

    def stop(self):
        """Forcefully stops the running script and reader thread."""
        if not self.is_running_flag.is_set():
            return

        self.is_running_flag.clear()
        
        if self.process:
            try:
                process_pid = self.process.pid
                pgid = os.getpgid(process_pid)
                log_info("Process termination starting", process_pid=process_pid, process_group_id=pgid)
                
                # Kill the process group to ensure all child processes are terminated
                log_info("Executing process group kill", pgid=pgid, signal=9)
                os.killpg(pgid, 9)
                log_info("Process group kill completed successfully", pgid=pgid)
                
            except ProcessLookupError as e:
                log_info("Process already terminated", error=str(e), error_type="ProcessLookupError")
                # Process already terminated - this is actually success
            except PermissionError as e:
                log_error("Permission denied for process group kill", error=str(e), process_pid=self.process.pid)
                try:
                    log_info("Attempting direct process terminate as fallback")
                    self.process.terminate()
                    # Give it a moment to terminate gracefully
                    try:
                        self.process.wait(timeout=2)
                        log_info("Direct process terminate succeeded")
                    except subprocess.TimeoutExpired:
                        log_warning("Process terminate timeout, attempting kill")
                        # Force kill if it doesn't terminate
                        self.process.kill()
                        self.process.wait()
                        log_info("Direct process kill succeeded")
                except Exception as fallback_e:
                    log_error("Fallback termination methods failed", error=str(fallback_e), error_type=type(fallback_e).__name__)
            except OSError as e:
                log_error("OS error during process termination", error=str(e), errno=getattr(e, 'errno', None))
                try:
                    log_info("Attempting direct process terminate as OSError fallback")
                    self.process.terminate()
                    # Give it a moment to terminate gracefully
                    try:
                        self.process.wait(timeout=2)
                        log_info("Direct process terminate succeeded after OSError")
                    except subprocess.TimeoutExpired:
                        log_warning("Process terminate timeout after OSError, attempting kill")
                        # Force kill if it doesn't terminate
                        self.process.kill()
                        self.process.wait()
                        log_info("Direct process kill succeeded after OSError")
                except Exception as fallback_e:
                    log_error("OSError fallback termination failed", error=str(fallback_e), error_type=type(fallback_e).__name__)
            except Exception as e:
                log_error("Unexpected exception during process termination", error=str(e), error_type=type(e).__name__)
                try:
                    log_info("Attempting direct process terminate as unexpected exception fallback")
                    self.process.terminate()
                    # Give it a moment to terminate gracefully
                    try:
                        self.process.wait(timeout=2)
                        log_info("Direct process terminate succeeded after unexpected exception")
                    except subprocess.TimeoutExpired:
                        log_warning("Process terminate timeout after unexpected exception, attempting kill")
                        # Force kill if it doesn't terminate
                        self.process.kill()
                        self.process.wait()
                        log_info("Direct process kill succeeded after unexpected exception")
                except Exception as fallback_e:
                    log_error("All termination methods failed", error=str(fallback_e), error_type=type(fallback_e).__name__)
        else:
            log_warning("No process to terminate", process_state="None")
        
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        # Clean up PTY file descriptors
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except:
                pass
            self.master_fd = None
        if self.slave_fd is not None:
            try:
                os.close(self.slave_fd)
            except:
                pass
            self.slave_fd = None

        # Clear the output and result queues to prevent old output from appearing
        # when the next script runs
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break

        self.process = None
        self.reader_thread = None

    def terminate(self):
        """Alias for stop() method for consistency with terminate_script functionality."""
        self.stop()