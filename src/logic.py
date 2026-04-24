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
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Native execution debug logging
from src.enhanced_debug_logger import (
    debug_context, log_info, log_error, log_warning,
    debug_enabled
)

# ---------------------------------------------------------------------------
# Custom exceptions for rollback failures
# ---------------------------------------------------------------------------

class RollbackError(Exception):
    """
    Raised when an automatic or manual rollback fails to restore the project
    to its pre-run state.  Carries structured context so the UI can display
    a meaningful recovery message to the user.

    Attributes:
        step_id:      The workflow step whose rollback failed.
        run_number:   The run number that was being rolled back.
        reason:       Human-readable description of why the rollback failed.
        partial_files: List of relative paths that may be in an inconsistent
                       state (newly created by the failed script but not
                       cleaned up by the failed rollback).
    """
    def __init__(self, step_id: str, run_number: int, reason: str,
                 partial_files: Optional[List[str]] = None):
        self.step_id = step_id
        self.run_number = run_number
        self.reason = reason
        self.partial_files = partial_files or []
        super().__init__(
            f"Rollback failed for step '{step_id}' run {run_number}: {reason}"
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
    "FA_results",                                   # Top-level FA results folder (all workflows)
    "Metabolomics_QC",                              # Top-level metabolomics QC folder
}

# Entry *names* (not paths) that are always excluded from scans — matched
# against entry.name so they are pruned at any depth without descending.
_SCAN_EXCLUDE_NAMES: frozenset = frozenset({
    '.snapshots',
    '.workflow_status',
    '.workflow_logs',
    'workflow.yml',
    '__pycache__',
    '.DS_Store',
})

# Relative path PREFIXES that are excluded from scans entirely.
# Combines PERMANENT_EXCLUSIONS so that FA archive and MISC subtrees are
# pruned before os.scandir() ever enters them.
#
# NOTE: Files under these prefixes are already protected from deletion
# during rollback (PERMANENT_EXCLUSIONS). Excluding them from scans is
# consistent with that intent — scripts must never modify these paths.
_SCAN_EXCLUDE_PREFIXES: frozenset = frozenset(PERMANENT_EXCLUSIONS)

# Keep _MANIFEST_EXCLUDE_PATTERNS as an alias for backward compatibility
# with any external code that references it directly.
_MANIFEST_EXCLUDE_PATTERNS = _SCAN_EXCLUDE_NAMES

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
                            log_warning(
                                "workflow_state.json is empty after all retries",
                                path=str(self.path),
                                retries=max_retries,
                            )
                            return {}
                    
                    # Parse the JSON content
                    f.seek(0)  # Reset file pointer
                    return json.load(f)
                    
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    # Temporary corruption - retry after delay
                    import time
                    log_warning(
                        "JSON decode error reading workflow_state.json — retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e),
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed - log error and return empty state
                    log_error(
                        "CRITICAL: workflow_state.json JSON corruption persists after all retries",
                        path=str(self.path),
                        retries=max_retries,
                        error=str(e),
                    )
                    return {}
            except Exception as e:
                if attempt < max_retries - 1:
                    # Other error - retry after delay
                    import time
                    log_warning(
                        "File read error reading workflow_state.json — retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e),
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed - log error and return empty state
                    log_error(
                        "CRITICAL: workflow_state.json file read error persists after all retries",
                        path=str(self.path),
                        retries=max_retries,
                        error=str(e),
                    )
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
    # Internal structured logging — writes to .workflow_logs/rollback.log
    # AND to the enhanced_debug_logger so all rollback activity is captured
    # in one place.  Never raises — logging must not break the caller.
    # -----------------------------------------------------------------------

    def _log_rollback(self, level: str, message: str, **kwargs):
        """
        Write a rollback/restore log entry to:
          1. <project>/.workflow_logs/rollback.log  (always, regardless of
             WORKFLOW_DEBUG env var — rollback events are always important)
          2. The enhanced_debug_logger (log_info / log_warning / log_error)

        level must be one of: 'INFO', 'WARNING', 'ERROR'
        """
        try:
            log_dir = self.project_path / ".workflow_logs"
            log_dir.mkdir(exist_ok=True)
            rollback_log = log_dir / "rollback.log"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            detail_str = "  ".join(f"{k}={v}" for k, v in kwargs.items())
            line = f"[{timestamp}] [{level}] {message}"
            if detail_str:
                line += f"  |  {detail_str}"
            with open(rollback_log, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
        except Exception:
            pass  # Never let logging break the caller

        # Also route to the enhanced debug logger
        try:
            if level == "ERROR":
                log_error(message, **kwargs)
            elif level == "WARNING":
                log_warning(message, **kwargs)
            else:
                log_info(message, **kwargs)
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _scan_project(self) -> tuple:
        """
        Single-pass iterative scan of the project directory using os.scandir().

        Returns (files, dirs) — both as sets of relative path strings.

        Key improvements over the old rglob-based _scan_project_paths() /
        _scan_project_dirs() pair:
          - Single pass instead of two separate rglob walks
          - Prunes _SCAN_EXCLUDE_NAMES directories before entering them
            (os.scandir never calls readdir() on excluded subtrees)
          - Prunes PERMANENT_EXCLUSIONS paths (FA archive, MISC) entirely,
            skipping hundreds of instrument files that were previously
            traversed and then discarded
          - Iterative stack — no Python recursion depth concerns
        """
        files: set = set()
        dirs: set = set()
        stack: list = [self.project_path]

        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        # Prune by name first (cheap string comparison)
                        if entry.name in _SCAN_EXCLUDE_NAMES:
                            continue
                        rel = str(Path(entry.path).relative_to(self.project_path))
                        if entry.is_dir(follow_symlinks=False):
                            # Prune PERMANENT_EXCLUSIONS paths before descending
                            if rel in _SCAN_EXCLUDE_PREFIXES:
                                continue
                            dirs.add(rel)
                            stack.append(Path(entry.path))
                        else:
                            files.add(rel)
            except PermissionError:
                pass  # Skip directories we cannot read

        return files, dirs

    def _scan_project_paths(self) -> set:
        """Thin wrapper around _scan_project() — returns files only."""
        files, _ = self._scan_project()
        return files

    def _scan_project_dirs(self) -> set:
        """Thin wrapper around _scan_project() — returns dirs only."""
        _, dirs = self._scan_project()
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

    def _safe_delete(self, path: Path, retries: int = 3, delay: float = 1.0):
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
                    self._log_rollback(
                        "WARNING",
                        f"Could not delete file after {retries} attempts",
                        path=str(path),
                        retries=retries,
                    )

    # -----------------------------------------------------------------------
    # Manifest operations
    # -----------------------------------------------------------------------

    def scan_manifest(self, step_id: str, run_number: int) -> Path:
        """
        Writes a manifest JSON file capturing the current set of file paths AND
        directories in the project directory using a single os.scandir() pass.

        Directories are recorded explicitly so that empty directories created by
        a previous step are not mistakenly treated as "newly created" during a
        subsequent step's rollback.

        Returns (manifest_path, (files, dirs)) so the caller can pass the scan
        result directly to take_selective_snapshot() without a second walk.
        """
        manifest_path = self.snapshots_dir / f"{step_id}_run_{run_number}_manifest.json"
        files, dirs = self._scan_project()          # single pass — no rglob
        current_paths = sorted(files)
        current_dirs = sorted(dirs)

        manifest = {
            "step_id": step_id,
            "run_number": run_number,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "files": current_paths,
            "directories": current_dirs,
            "excluded_patterns": sorted(_SCAN_EXCLUDE_NAMES | _SCAN_EXCLUDE_PREFIXES),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self._log_rollback(
            "INFO",
            f"Manifest written: {manifest_path.name}",
            files=len(current_paths),
            dirs=len(current_dirs),
        )
        return manifest_path, (files, dirs)

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
        prev_manifest_path,       # Path | None
        current_scan=None,        # tuple[set, set] | None  — (files, dirs) from _scan_project()
    ) -> Path:
        """
        Creates a targeted snapshot ZIP containing:
          1. Files/folders listed in snapshot_items (the script's declared outputs)
          2. Files newly added by the user since the previous completed run
             (identified by diffing current paths against the previous manifest)

        prev_manifest_path: Path to the manifest from the previous completed run,
                            or None if this is the very first run of the project
                            (in which case all current files are treated as new).

        current_scan: Optional pre-computed (files, dirs) tuple from _scan_project().
                      If provided, skips the internal scan entirely (no second walk).
                      Pass the second element of scan_manifest()'s return value.

        Returns the Path of the written ZIP file.
        """
        zip_path = self.snapshots_dir / f"{step_id}_run_{run_number}_snapshot.zip"

        if current_scan is not None:
            current_paths, _ = current_scan   # reuse — no second walk
        else:
            current_paths = self._scan_project_paths()   # fallback for direct callers
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

        self._log_rollback(
            "INFO",
            f"Selective snapshot written: {zip_path.name}",
            total_files=len(files_to_zip),
            declared=len(snapshot_item_paths),
            newly_added=len(newly_added),
        )
        return zip_path

    # -----------------------------------------------------------------------
    # Restore operations
    # -----------------------------------------------------------------------

    def restore_snapshot(self, step_id: str, run_number: int):
        """
        Primary restore entry point.  Tries the new selective format first,
        then falls back to the legacy complete ZIP.

        Raises RollbackError if no snapshot exists or if the restore itself
        fails — callers must NOT silently swallow this exception.  The UI
        layer is responsible for surfacing it to the user with recovery
        instructions.
        """
        new_zip = self.snapshots_dir / f"{step_id}_run_{run_number}_snapshot.zip"
        new_manifest = self.snapshots_dir / f"{step_id}_run_{run_number}_manifest.json"

        self._log_rollback(
            "INFO",
            "Starting snapshot restore",
            step_id=step_id,
            run_number=run_number,
            new_zip_exists=new_zip.exists(),
            new_manifest_exists=new_manifest.exists(),
        )

        if new_zip.exists() and new_manifest.exists():
            try:
                self._restore_from_selective_snapshot(new_zip, new_manifest)
                self._log_rollback(
                    "INFO",
                    "Selective snapshot restore completed successfully",
                    step_id=step_id,
                    run_number=run_number,
                )
                return
            except Exception as exc:
                self._log_rollback(
                    "ERROR",
                    "Selective snapshot restore FAILED",
                    step_id=step_id,
                    run_number=run_number,
                    error=str(exc),
                )
                raise RollbackError(
                    step_id=step_id,
                    run_number=run_number,
                    reason=f"Restore from selective snapshot failed: {exc}",
                ) from exc

        # Fall back to legacy complete ZIP
        legacy_zip = self.snapshots_dir / f"{step_id}_run_{run_number}_complete.zip"
        if legacy_zip.exists():
            try:
                self._restore_from_complete_snapshot(legacy_zip)
                self._log_rollback(
                    "INFO",
                    "Legacy complete snapshot restore completed successfully",
                    step_id=step_id,
                    run_number=run_number,
                )
                return
            except Exception as exc:
                self._log_rollback(
                    "ERROR",
                    "Legacy complete snapshot restore FAILED",
                    step_id=step_id,
                    run_number=run_number,
                    error=str(exc),
                )
                raise RollbackError(
                    step_id=step_id,
                    run_number=run_number,
                    reason=f"Restore from legacy snapshot failed: {exc}",
                ) from exc

        # No snapshot found at all
        self._log_rollback(
            "ERROR",
            "No snapshot found for restore — project state may be inconsistent",
            step_id=step_id,
            run_number=run_number,
            checked_new=str(new_zip),
            checked_legacy=str(legacy_zip),
        )
        raise RollbackError(
            step_id=step_id,
            run_number=run_number,
            reason=(
                f"No snapshot file found. Checked: {new_zip.name} and {legacy_zip.name}. "
                "The project folder may be in an inconsistent state."
            ),
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

        Performance (DEV-013): A single _scan_project() call replaces the previous
        two-walk pattern (_scan_project_paths() for files + rglob('*') for dirs).
        The rglob walk descended into FA archive and MISC subtrees (~55-60 s on
        external drives); _scan_project() prunes those subtrees before entering
        them, matching the DEV-012 optimisation applied to the creation path.
        """
        pre_run_paths = self._load_manifest_paths(manifest_path)

        # Single-pass scan: collect both files and dirs with early pruning.
        # This replaces the previous two-walk pattern:
        #   Walk 1: self._scan_project_paths()  → files only (discarded dirs)
        #   Walk 2: self.project_path.rglob('*') → dirs only (old rglob, ~55-60 s)
        # Now one _scan_project() call returns both in ~1.87 s on external drives.
        current_files, current_dirs = self._scan_project()

        newly_created_files = current_files - pre_run_paths

        # --- Delete newly-created files (skip permanently protected paths) ---
        for rel_str in newly_created_files:
            if any(rel_str.startswith(prefix) for prefix in PERMANENT_EXCLUSIONS):
                self._log_rollback(
                    "INFO",
                    f"Restore: skipping permanently protected path: {rel_str}",
                )
                continue
            full_path = self.project_path / rel_str
            if full_path.is_file():
                self._safe_delete(full_path)
                self._log_rollback("INFO", f"Restore: deleted newly-created file", path=rel_str)

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

        # current_dirs already populated by _scan_project() above —
        # no second walk needed. _scan_project() applies the same
        # _SCAN_EXCLUDE_NAMES and _SCAN_EXCLUDE_PREFIXES pruning as the
        # creation path, so FA archive and MISC subtrees are excluded
        # consistently between snapshot creation and restore.
        newly_created_dirs = current_dirs - pre_run_dirs
        for rel_str in sorted(newly_created_dirs, key=lambda p: len(Path(p).parts), reverse=True):
            if any(rel_str.startswith(prefix) for prefix in PERMANENT_EXCLUSIONS):
                continue
            full_path = self.project_path / rel_str
            if full_path.exists() and full_path.is_dir():
                try:
                    if not any(full_path.iterdir()):
                        full_path.rmdir()
                        self._log_rollback(
                            "INFO",
                            "Restore: removed newly-created empty directory",
                            path=rel_str,
                        )
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

        self._log_rollback(
            "INFO",
            f"Selective snapshot restored successfully",
            zip=zip_path.name,
        )

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
                self._log_rollback("INFO", "Legacy restore: removed file", path=str(rel_path))

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
                        self._log_rollback(
                            "INFO",
                            "Legacy restore: removed empty directory",
                            path=str(rel_dir),
                        )
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

        self._log_rollback(
            "INFO",
            "Legacy complete snapshot restored successfully",
            zip=zip_path.name,
        )

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
                self._log_rollback("INFO", "Removed snapshot file", file=f.name)
                manifest = self.snapshots_dir / f.name.replace("_snapshot.zip", "_manifest.json")
                if manifest.exists():
                    manifest.unlink()
                    self._log_rollback("INFO", "Removed manifest file", file=manifest.name)

        # Legacy-format snapshots
        pattern_legacy = re.compile(r'_run_(\d+)_complete$')
        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip")):
            m = pattern_legacy.search(f.stem)
            if m and int(m.group(1)) >= run_number:
                f.unlink()
                self._log_rollback("INFO", "Removed legacy snapshot file", file=f.name)

    def remove_all_run_snapshots(self, step_id: str):
        """
        Remove all run snapshots for a step (both new and legacy formats),
        including paired manifest files.
        """
        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_snapshot.zip")):
            try:
                f.unlink()
                self._log_rollback("INFO", "Removed snapshot file", file=f.name)
            except OSError as e:
                self._log_rollback(
                    "WARNING", "Could not remove snapshot file",
                    file=f.name, error=str(e)
                )
            manifest = self.snapshots_dir / f.name.replace("_snapshot.zip", "_manifest.json")
            if manifest.exists():
                try:
                    manifest.unlink()
                    self._log_rollback("INFO", "Removed manifest file", file=manifest.name)
                except OSError as e:
                    self._log_rollback(
                        "WARNING", "Could not remove manifest file",
                        file=manifest.name, error=str(e)
                    )

        for f in list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip")):
            try:
                f.unlink()
                self._log_rollback("INFO", "Removed legacy snapshot file", file=f.name)
            except OSError as e:
                self._log_rollback(
                    "WARNING", "Could not remove legacy snapshot file",
                    file=f.name, error=str(e)
                )

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