# Undo System Implementation Notes — Stage 2, 3 & Post-Stage 3 Deviation Log

**Date:** 2026-04-24
**Stage:** Post-Stage 3 — Scan performance optimization (DEV-012)
**Plan document:** [`plans/undo_system_redesign.md`](../../plans/undo_system_redesign.md)
**Status:** Complete — 43/43 snapshot manager tests passing (as of DEV-012 fix)

---

## Overview

This document records deviations from the original plan, design decisions made during implementation, and notes for future maintainers. It is intended as a companion to the plan document, not a replacement.

---

## DEV-001: Retention Policy Removed

**Section in plan:** Section 6 (Retention Policy)  
**Original plan:** Keep at most `MAX_UNDO_SNAPSHOTS = 10` snapshots per step; delete oldest when limit exceeded via `apply_retention_policy(completion_order)`.  
**What was implemented:** No retention policy. All snapshots are kept indefinitely.

**Reason:** User decision during implementation review. The new selective snapshot system produces tiny ZIPs (2–10 files vs. the entire project), so storage growth is no longer a concern. The user explicitly wants the ability to undo all steps without limit.

**Impact:**
- `MAX_UNDO_SNAPSHOTS` constant was never added to `src/logic.py`
- `apply_retention_policy()` method was never added to `SnapshotManager`
- `TestApplyRetentionPolicy` test class was never added to `tests/test_snapshot_manager.py`
- Plan document updated in Sections 6, 9.1, and 11 to document this decision

---

## DEV-002: `snapshot_exists()` Signature Breaking Change

**Section in plan:** Section 7.3  
**Original signature:** `snapshot_exists(snapshot_name: str) -> bool`  
**New signature:** `snapshot_exists(step_id: str, run_number: int) -> bool`

**Reason:** The old signature accepted a pre-formatted string like `"init_project_run_1"`, which required callers to construct the string themselves and was error-prone. The new signature takes the two logical components separately, matching the pattern of all other run-number methods.

**Callers updated:**
- [`src/core.py`](../../src/core.py) — `terminate_script()`
- [`app.py`](../../app.py) — `perform_undo()`
- [`tests/test_chronological_undo_ordering.py`](../../tests/test_chronological_undo_ordering.py) — `perform_undo_test()`
- [`tests/test_cyclical_workflow_undo.py`](../../tests/test_cyclical_workflow_undo.py) — `perform_undo_test()` and all direct `snapshot_exists()` calls

---

## DEV-003: `test_project_init_no_script_path` Marked xfail

**File:** [`tests/test_core.py`](../../tests/test_core.py)  
**Test:** `test_project_init_no_script_path`

**Reason:** `Project.__init__` now requires `script_path` as a mandatory argument and raises `ValueError` if it is `None`. The old behaviour (defaulting to `project_dir/scripts/`) was removed in a prior refactoring. The test was marked `@pytest.mark.xfail(strict=True)` rather than deleted, so it serves as documentation of the intentional breaking change.

---

## DEV-004: Legacy Fallback Format Clarification

**Section in plan:** Section 7.1  
**Plan description:** "Graceful fallback for old `_complete.zip` files"

**Clarification:** There are two distinct legacy formats:

| Format | Example | Notes |
|--------|---------|-------|
| Old legacy (pre-run-number era) | `init_project_complete.zip` | Used by `restore_complete_snapshot(step_id)` wrapper |
| Run-numbered legacy | `init_project_run_1_complete.zip` | Used by `restore_snapshot(step_id, run_number)` dispatcher |

The new `restore_snapshot()` dispatcher falls back to `{step_id}_run_{N}_complete.zip` (run-numbered legacy). The old `restore_complete_snapshot(step_id)` wrapper (kept for backward compatibility) uses `{step_id}_complete.zip` (no run number).

The integration test `test_legacy_fallback` tests the run-numbered legacy format, which is what `restore_snapshot()` actually falls back to.

---

## DEV-005: `simulate_step_run()` Helper in Integration Tests

**File:** [`tests/test_undo_system_integration.py`](../../tests/test_undo_system_integration.py)

The integration tests do **not** call `run_step()` for the happy-path scenarios. Instead, they use a `simulate_step_run()` helper that directly calls:
1. `scan_manifest()`
2. `take_selective_snapshot()`
3. Creates output files on disk
4. Creates the success marker
5. Calls `handle_step_result()`

**Reason:** `run_step()` launches scripts asynchronously via `ScriptRunner` (pseudo-terminal). Waiting for subprocess completion in tests would require polling loops, timeouts, and thread management — adding significant complexity and fragility. The `simulate_step_run()` approach tests the same code paths (manifest → ZIP → restore) without subprocess overhead.

`run_step()` itself is tested directly only in `test_missing_snapshot_items_aborts_run_step` (Scenario 10), where the abort-before-launch behaviour is what's under test.

---

## DEV-006: `PERMANENT_EXCLUSIONS` Includes MISC Variants

**Section in plan:** Section 0 (FA Archive Permanent Protection Rule)  
**Original plan:** 5 FA archive paths only.  
**What was implemented:** 8 entries — 5 FA archive paths + `MISC`, `misc`, `Misc`.

**Reason:** User request during implementation. MISC folders are used to store miscellaneous project files that should never be deleted during undo/rollback.

```python
PERMANENT_EXCLUSIONS = {
    "archived_files/FA_results_archive",
    "archived_files/first_lib_attempt_fa_results",
    "archived_files/second_lib_attempt_fa_results",
    "archived_files/third_lib_attempt_fa_results",
    "archived_files/capsule_fa_analysis_results",
    "MISC",
    "misc",
    "Misc",
}
```

---

## DEV-012: Scan Performance Optimization — `os.scandir()` Single-Pass with Early Pruning

**Date:** 2026-04-24
**Files changed:**
- [`src/logic.py`](../../src/logic.py) — `SnapshotManager`: new constants, new `_scan_project()` method, updated `scan_manifest()` return type, updated `take_selective_snapshot()` signature
- [`src/core.py`](../../src/core.py) — `run_step()`, `skip_to_step()`: updated to capture and reuse scan tuple
- [`tests/test_snapshot_manager.py`](../../tests/test_snapshot_manager.py) — updated `test_writes_manifest_json` (tuple unpack), renamed and inverted `test_manifest_excludes_permanent_exclusion_paths`

### Problem

The snapshot system performed **three separate `rglob('*')` walks** per step execution:

1. `_scan_project_paths()` → `rglob` #1 (called inside `scan_manifest()`)
2. `_scan_project_dirs()` → `rglob` #2 (called inside `scan_manifest()`)
3. `_scan_project_paths()` → `rglob` #3 (called inside `take_selective_snapshot()`)

On an external drive with large FA archive directories (hundreds of BMP/instrument files) and MISC folders, each `rglob('*')` walk took 55–60 seconds. Three walks = **~166 seconds per step execution** (measured via `utils/benchmark_scan.py`).

Additionally, `rglob('*')` has no early-exit mechanism — it descends into every subdirectory including `PERMANENT_EXCLUSIONS` paths (FA archives, MISC folders) that are never included in manifests or snapshots anyway.

### Benchmark Results (`utils/benchmark_scan.py`)

| Strategy | Average time | Speedup |
|----------|-------------|---------|
| Strategy 1: Baseline (3× `rglob`) | 166.28 s | 1× |
| Strategy 2: Single `rglob` | 58.29 s | 2.85× |
| Strategy 3: Single `rglob` + exclusions | 40.00 s | 4.16× |
| Strategy 4: `os.scandir` + early pruning | **1.87 s** | **89×** |

### Fix: Single-Pass `os.scandir()` with Early Directory Pruning

**New constants in `src/logic.py`:**

```python
_SCAN_EXCLUDE_NAMES: frozenset = frozenset({
    '.snapshots',
    '.workflow_status',
    '.workflow_logs',
    'workflow.yml',
    '__pycache__',
    '.DS_Store',
})

_SCAN_EXCLUDE_PREFIXES: frozenset = frozenset(PERMANENT_EXCLUSIONS)
```

`_SCAN_EXCLUDE_NAMES` prunes system folders/files by name at **any depth** — the scanner never descends into them.

`_SCAN_EXCLUDE_PREFIXES` prunes `PERMANENT_EXCLUSIONS` paths (FA archives, MISC variants) by their top-level relative path — the scanner never enters them. These are always top-level directories in the project folder, so prefix matching is correct and sufficient.

`workflow.yml` is excluded from scans so it never appears in manifests or snapshots (it is a workflow configuration file, not a project data file).

**New `_scan_project()` method in `SnapshotManager`:**

```python
def _scan_project(self) -> tuple:
    files: set = set()
    dirs: set = set()
    stack: list = [self.project_path]
    while stack:
        current_dir = stack.pop()
        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    if entry.name in _SCAN_EXCLUDE_NAMES:
                        continue
                    rel = str(Path(entry.path).relative_to(self.project_path))
                    if entry.is_dir(follow_symlinks=False):
                        if rel in _SCAN_EXCLUDE_PREFIXES:
                            continue
                        dirs.add(rel)
                        stack.append(Path(entry.path))
                    else:
                        files.add(rel)
        except PermissionError:
            pass
    return files, dirs
```

The key insight: `os.scandir()` with an explicit stack allows **pruning entire subtrees before entering them**. When a directory name matches `_SCAN_EXCLUDE_NAMES` or its relative path matches `_SCAN_EXCLUDE_PREFIXES`, it is skipped entirely — the scanner never descends into it. `rglob('*')` has no equivalent mechanism.

**`_scan_project_paths()` and `_scan_project_dirs()` retained as thin wrappers** for backward compatibility with any callers that use them directly.

**`scan_manifest()` return type changed** from `Path` to `tuple[Path, tuple[set, set]]`:

```python
# Before:
manifest_path = sm.scan_manifest(step_id, run_number)

# After:
manifest_path, current_scan = sm.scan_manifest(step_id, run_number)
# current_scan = (files: set, dirs: set)
```

**`take_selective_snapshot()` accepts optional `current_scan` parameter:**

```python
def take_selective_snapshot(self, step_id, run_number, snapshot_items,
                            prev_manifest_path, current_scan=None):
    if current_scan is not None:
        current_paths, _ = current_scan  # reuse — no second walk
    else:
        current_paths = self._scan_project_paths()  # fallback
```

**Callers in `src/core.py`** (`run_step()` and `skip_to_step()`) capture the scan tuple from `scan_manifest()` and pass it to `take_selective_snapshot()`, eliminating the third walk entirely.

### Why `PERMANENT_EXCLUSIONS` Are Now Also Excluded from Scans

`PERMANENT_EXCLUSIONS` previously only protected these paths from **deletion during rollback** — they were still traversed during scanning. The fix extends their protection to scanning as well: the scanner now skips them entirely. This is correct because:

1. FA archive directories contain hundreds of large BMP/instrument files — the dominant source of scan latency
2. MISC folders are user-managed and should never appear in manifests or snapshots
3. These paths are never rolled back, so there is no reason to scan them

### Test Updates

- `test_writes_manifest_json`: changed `manifest_path = sm.scan_manifest(...)` to `manifest_path, _ = sm.scan_manifest(...)` to unpack the new tuple return type
- `test_manifest_includes_permanent_exclusion_paths` → renamed to `test_manifest_excludes_permanent_exclusion_paths` and assertion **inverted**: FA archive paths must **not** appear in the manifest (previously the test incorrectly asserted they were included)

### Real-World Validation

Tested on an external drive project with FA archive and MISC folders:
- Manifest JSON + ZIP creation: **~10 seconds** (cold cache, vs. ~166 seconds before)
- The remaining latency after manifest creation is Python subprocess startup + heavy library imports (pandas, numpy, openpyxl, sqlalchemy) — a separate issue unrelated to this optimization

---

## DEV-011: Rollback Logging Was Silent — All Rollback Activity Now Logged + UI Alerts on Failure

**Date:** 2026-04-24
**Files changed:**
- [`src/logic.py`](../../src/logic.py) — `SnapshotManager`, `StateManager`, new `RollbackError` exception
- [`src/core.py`](../../src/core.py) — `handle_step_result()`, `terminate_script()`
- [`app.py`](../../app.py) — `perform_undo()`, result handler, terminate handler, critical alert display
- [`tests/test_snapshot_manager.py`](../../tests/test_snapshot_manager.py) — updated `test_raises_when_no_snapshot_exists`

### Problem

All rollback and restore activity used bare `print()` calls. In a Streamlit application, `print()` goes to the server process stdout — invisible to the user in the browser. When a rollback *failed*, the error was caught, printed to nowhere the user could see, and execution continued silently. The project folder could be left in a corrupt, partially-modified state with the user having no indication anything went wrong.

Three specific failure modes were completely silent:
1. **Automatic rollback failure** — script fails mid-run, rollback also fails → project in unknown state, UI shows nothing
2. **Terminate rollback failure** — user clicks Terminate, rollback fails → project in unknown state, UI shows nothing
3. **Manual undo failure** — user clicks Undo, restore fails → project in unknown state, UI shows "✅ Undo completed!" regardless

### Fix: Three Layers of Defense

**Layer 1 — `SnapshotManager._log_rollback()` (new method in `src/logic.py`)**

Every rollback/restore operation now writes to two destinations simultaneously:

- **`.workflow_logs/rollback.log`** inside the project folder — always written, regardless of the `WORKFLOW_DEBUG` environment variable. Plain-text timestamped entries that a developer or power user can inspect after the fact.
- **The enhanced debug logger** (`log_info` / `log_warning` / `log_error`) — which writes to the centralized `debug_output/` log files.

All `print()` calls in `scan_manifest()`, `take_selective_snapshot()`, `_restore_from_selective_snapshot()`, `_restore_from_complete_snapshot()`, `remove_run_snapshots_from()`, `remove_all_run_snapshots()`, and `_safe_delete()` were replaced with `_log_rollback()` calls.

`StateManager.load()` retry-loop `print()` calls were also replaced with `log_warning()` / `log_error()` calls.

**Layer 2 — `RollbackError`: a structured exception (new class in `src/logic.py`)**

```python
class RollbackError(Exception):
    def __init__(self, step_id: str, run_number: int, reason: str,
                 partial_files: Optional[List[str]] = None):
        self.step_id = step_id
        self.run_number = run_number
        self.reason = reason
        self.partial_files = partial_files or []
```

`restore_snapshot()` now raises `RollbackError` (not `FileNotFoundError`) in all failure cases:
- No snapshot file found (neither new-format nor legacy)
- Selective snapshot restore throws an exception mid-way
- Legacy complete snapshot restore throws an exception mid-way

This means callers cannot accidentally catch it as a generic `Exception` and silently continue — it has a specific type that must be handled explicitly.

**Layer 3 — Persistent critical alert in the UI (`app.py`)**

Three places in `app.py` can trigger a rollback. All three now catch `RollbackError` and store it in `st.session_state.critical_rollback_alert` — a **persistent** session state key that survives page reruns and stays visible until the user explicitly dismisses it.

The alert is displayed at the very top of the main content area (above all workflow steps) as a prominent `st.error()` block with:
- Which step and run number failed
- The specific reason the rollback failed
- Clear instructions: do not run further steps, check `rollback.log`, inspect `.snapshots/`, contact admin or restore from backup
- A "✅ I understand — dismiss this alert" button

`perform_undo()` was also refactored to return `(success: bool, error)` instead of just `bool`, so the undo confirmation handler can distinguish success from failure and show the appropriate UI response.

### Test update

`tests/test_snapshot_manager.py::TestRestoreSnapshotLegacyFallback::test_raises_when_no_snapshot_exists` was updated to expect `RollbackError` instead of `FileNotFoundError`, and now also asserts `step_id` and `run_number` on the exception.

### Log file location

The rollback log is written to:
```
<project_folder>/.workflow_logs/rollback.log
```

This file is in the `.workflow_logs/` directory, which is excluded from manifests and snapshots (it is never rolled back). It accumulates across all runs and is the primary diagnostic tool when a rollback failure occurs.

---

## DEV-010: Manual Undo Did Not Remove Run-Number-Specific Success Markers

**Date:** 2026-04-23
**Files changed:** [`app.py`](../../app.py), [`tests/test_chronological_undo_ordering.py`](../../tests/test_chronological_undo_ordering.py)
**New test file:** [`tests/test_undo_marker_cleanup.py`](../../tests/test_undo_marker_cleanup.py)

### Bug description

`perform_undo()` in [`app.py`](../../app.py) was only trying to delete the flat
`<script_stem>.success` marker when undoing a step.  However,
`handle_step_result()` in [`src/core.py`](../../src/core.py) **renames** that flat
marker to `<script_stem>.run_<N>.success` immediately after every successful
script exit (the run-number rename system introduced to prevent stale markers
from being mistaken for fresh ones).

By the time the user clicks "Undo Last Step", the flat marker no longer exists
on disk — only the run-specific marker does.  The `if success_marker.exists()`
check in `perform_undo()` silently returned `False`, and the run-specific marker
was left behind in `.workflow_status/` indefinitely.

There were two affected code paths:

| Case | `effective_run` | Old behaviour | Bug |
|------|----------------|---------------|-----|
| Full undo | `== 1` | Tried to delete `<stem>.success` | Flat marker gone (renamed); run-1 marker left behind |
| Granular undo | `> 1` | No marker cleanup at all | Run-N marker always left behind |

### Fix

**Case 1 — full undo (`effective_run == 1`):**
- Delete `<script_stem>.run_1.success` (current format, written by all new runs)
- Also attempt `<script_stem>.success` as a safety net for **legacy projects**
  completed before the run-number rename system was introduced (those still have
  the flat marker on disk)

**Case 2 — granular undo (`effective_run > 1`):**
- Delete `<script_stem>.run_<N>.success` for the specific run being undone
- Run markers for earlier runs (which are still valid) are left untouched

Both deletions are guarded by `if marker.exists()` so neither raises if the
marker is already absent.

### Mirror fix in test helper

[`tests/test_chronological_undo_ordering.py`](../../tests/test_chronological_undo_ordering.py)
contains a local `perform_undo_test()` helper that mirrors `app.py`'s
`perform_undo()` for use in tests without Streamlit.  This helper was updated
with the same fix so that the chronological ordering tests remain accurate
representations of the real undo logic.

### Tests added

[`tests/test_undo_marker_cleanup.py`](../../tests/test_undo_marker_cleanup.py) —
9 new tests covering:

- `TestFullUndoMarkerCleanup` (5 tests):
  - Run-1 marker removed after full undo
  - Legacy flat marker removed after full undo (backward compatibility)
  - Both markers removed if both present simultaneously
  - No error if no marker exists
  - Other steps' markers are not touched

- `TestGranularUndoMarkerCleanup` (4 tests):
  - Run-N marker removed after granular undo
  - Only the correct run's marker removed (earlier runs untouched)
  - No error if no marker exists
  - Sequential granular undos each remove the correct marker in order

All 9 tests pass. Manual verification with a real project folder confirmed the
fix resolves the stale-marker accumulation observed in `.workflow_status/`.

---

## DEV-007: `skip_to_step()` Uses Empty Selective Snapshots

**Section in plan:** Section 4.1  
**Implementation detail:** When `skip_to_step()` marks steps as skipped, it calls `scan_manifest()` + `take_selective_snapshot(step_id, 1, snapshot_items=[], prev_manifest_path=...)` for each skipped step.

`snapshot_items=[]` is intentional — no script ran for skipped steps, so there are no declared outputs to back up. The manifest still captures the folder state at the skip point, enabling undo past the skip boundary. The resulting ZIP will contain only newly-added user files (if any), or be empty.

---

## DEV-008: `parse_snapshot_items_from_script()` Uses AST Parsing

**File:** [`src/core.py`](../../src/core.py)  
**Function:** `parse_snapshot_items_from_script(script_path: Path) -> List[str]`

Uses Python's `ast` module to safely read `SNAPSHOT_ITEMS` from script files without executing them. This is safe against malicious or broken scripts — the AST parser only reads the syntax tree, never executes any code.

The function raises `ValueError` if `SNAPSHOT_ITEMS` is not found, causing `run_step()` to abort with a clear error message before the script is launched.

---

## DEV-009: Lessons Learned from Capsule Fixture Tests — Applies to SPS-CE and SIP Fixtures

**Context:** The Capsule fixture tests (13 scenarios in `tests/test_undo_system_integration.py`) were completed and validated against a real Capsule project. The following lessons must be applied when writing the SPS-CE and SIP fixture tests (Step 16 of Stage 2).

### Lesson 1: Scenario 13 (empty-dir survival) must use workflow-specific directory names

The Capsule Scenario 13 creates `2_library_creation/`, `3_FA_analysis/`, and `4_plate_selection_and_pooling/` as the empty directories that step 1 creates. These are Capsule-specific.

When writing SPS-CE and SIP fixtures, **Scenario 13 must be adapted to use the correct empty directories for each workflow's step 1 script.** Read the real step 1 script to find which directories it creates via `create_project_folder_structure()` or equivalent, then create those same dirs in the test.

The underlying fix (`_scan_project_dirs()` + `"directories"` field in manifest) is already in the core system — the test just needs to verify it for each workflow's specific structure.

### Lesson 2: Mock scripts only need SNAPSHOT_ITEMS + success marker

The `simulate_step_run()` helper (DEV-005) creates output files directly — it does not call the mock script for happy-path scenarios. Mock scripts are only executed by `run_step()` in Scenario 10 (missing `SNAPSHOT_ITEMS` abort test).

**Therefore, SPS-CE and SIP mock scripts only need:**
1. A correct `SNAPSHOT_ITEMS` block (matching the real script's actual file outputs)
2. A `create_success_marker()` call
3. A clean exit

They do not need to replicate any business logic from the real scripts.

### Lesson 3: Scenario 11 (FA archive protection) needs workflow-specific archive paths

The Capsule test uses `archived_files/capsule_fa_analysis_results/` as the FA archive path. SIP uses multiple paths:
- `archived_files/first_lib_attempt_fa_results/`
- `archived_files/second_lib_attempt_fa_results/`
- `archived_files/third_lib_attempt_fa_results/`

The SIP fixture's Scenario 11 must use the correct SIP FA archive paths. SPS-CE may have its own FA archive path — check the real script to confirm.

### Lesson 4: SNAPSHOT_ITEMS in mock scripts must accurately reflect real script outputs

Scenario 14 (manifest diff detects newly-added files) verifies that user-added files between steps are captured in the snapshot ZIP. This test is only meaningful if the mock script's `SNAPSHOT_ITEMS` accurately reflects what the real script writes. If `SNAPSHOT_ITEMS` is wrong, the manifest diff logic won't be tested against realistic data.

**Before writing mock scripts:** Read each real SPS-CE/SIP script and verify its actual file outputs. The `SNAPSHOT_ITEMS` table in Section 5.3 of the plan is a first-pass estimate — it must be verified against the actual scripts.

### Lesson 5: The 13 test scenarios themselves are fully reusable

The test logic in `tests/test_undo_system_integration.py` is workflow-agnostic. Only the fixture-specific data needs to change:
- Step IDs (from the workflow YAML)
- Directory names (from the real scripts)
- FA archive paths (from `PERMANENT_EXCLUSIONS` in `src/logic.py`)
- `SNAPSHOT_ITEMS` per step (from the real scripts)

The recommended approach is to parameterize the existing test file or create a separate `test_undo_system_integration_sps.py` and `test_undo_system_integration_sip.py` that import the same scenario functions with different fixtures.

---

## Manual Testing Checklist (from Section 14.7)

After the automated tests pass, perform these 4 manual checks with a real Capsule project:

1. **Open the GUI** with a real in-progress Capsule project
2. **Click Run** on the next pending step — verify it completes and `.snapshots/` contains a new `_snapshot.zip` and `_manifest.json`
3. **Click Undo** — verify the project folder is restored correctly
4. **Confirm legacy fallback** — if the project has old `_complete.zip` files for previously-completed steps, verify undo still works for those steps

These four checks are sufficient to validate the system end-to-end with real data.

---

## Test Coverage Summary

| Test file | Tests | Status |
|-----------|-------|--------|
| `tests/test_snapshot_manager.py` | 43 | ✅ All passing (DEV-011: `RollbackError` assertion updated) |
| `tests/test_chronological_undo_ordering.py` | 5 | ✅ All passing |
| `tests/test_cyclical_workflow_undo.py` | 5 | ✅ All passing |
| `tests/test_core.py` | 2 (1 xfail) | ✅ 1 passing, 1 xfail (expected) |
| `tests/test_rerun_success_marker.py` | 15 | ✅ All passing |
| `tests/test_undo_marker_cleanup.py` | 9 | ✅ All passing (DEV-010 fix) |
| `tests/test_undo_system_integration.py` | 13 | ✅ All passing (Capsule workflow) |
| `tests/test_undo_system_integration_sps.py` | 13 | ✅ All passing (SPS-CE workflow) |
| `tests/test_undo_system_integration_sip.py` | 13 | ✅ All passing (SIP workflow) |
| **Total** | **118** | **117 passed, 1 xfailed** |

---

## Implementation Status Summary — For Handoff

**Last updated:** 2026-04-24
**Last commit (workflow manager):** Post-Stage 3 — rollback logging & silent-failure elimination (DEV-011)
**Last commit (SPS-CE scripts):** `4f0ed0c` — pushed to `origin/main` (`SPS_library_creation_scripts/`)
**Branch:** `main`

### What is complete

**Stage 1 (Capsule workflow scripts repo — `capsule_sort_scripts/`):**
All 6 Capsule workflow scripts already had `SNAPSHOT_ITEMS` blocks added in a prior session. The Capsule workflow is fully integrated with the selective snapshot system.

**Stage 2 (Workflow manager repo — `sip_lims_workflow_manager/`) — COMPLETE:**

All workflow manager changes are done and tested. The system is workflow-agnostic — it works for any workflow whose scripts declare `SNAPSHOT_ITEMS`.

Key files changed:
- **`src/logic.py`** — `SnapshotManager`: new `scan_manifest()`, `take_selective_snapshot()`, `restore_snapshot()`, `_restore_from_selective_snapshot()`, `_scan_project_dirs()`, `_load_manifest_dirs()`, `_load_manifest_paths()`. Updated run-number methods. Manifest now records both files and directories.
- **`src/core.py`** — `parse_snapshot_items_from_script()` (AST-based); wired into `run_step()`, `handle_step_result()`, `terminate_script()`, `skip_to_step()`. `handle_step_result()` now explicitly sets step to "pending" on failure (fixes re-run state bug).
- **`app.py`** — `completed_script_success` now reads `project.get_state(step_id) == "completed"` after `handle_step_result()` runs (fixes false "completed" GUI display). `perform_undo()` granular path directly manipulates `_completion_order` to correctly decrement run counter.
- **`tests/fixtures/generate_capsule_fixture.py`** — Capsule project fixture generator
- **`tests/fixtures/mock_scripts/`** — 8 Capsule mock scripts (6 passing + 2 failure variants)
- **`tests/test_undo_system_integration.py`** — 13 integration test scenarios for Capsule (all passing)
- **`tests/test_snapshot_manager.py`** — 43 unit tests for `SnapshotManager`

Five bugs discovered during manual testing and fixed:
1. **Empty-dir rollback bug** — manifest now records directories; empty dirs from prior steps survive rollback
2. **GUI shows "completed" when script fails** — fixed in `app.py` (raw exit code → post-handle state check)
3. **Failed re-run stays "completed" in state** — fixed in `src/core.py` (`handle_step_result()` now always sets pending on failure)
4. **Run counter not decremented after granular undo** — fixed in `app.py` (`perform_undo()` directly manipulates `_completion_order`)
5. **Manual undo leaves stale run-specific success markers** — fixed in `app.py` (`perform_undo()` now deletes `<stem>.run_<N>.success` for both full and granular undo; also retains flat-marker fallback for legacy projects). See DEV-010.

Manual sanity check with a real Capsule project: **passed**.

**Stage 3 (SPS-CE and SIP fixture tests) — COMPLETE:**

**Step A — Add `SNAPSHOT_ITEMS` to SPS-CE scripts** ✅ COMPLETE (commit `4f0ed0c`, `SPS_library_creation_scripts/`):

All 9 SPS-CE scripts audited and updated. Final `SNAPSHOT_ITEMS` per script:

| Script | `SNAPSHOT_ITEMS` |
|--------|-----------------|
| `SPS_initiate_project_folder_and_make_sort_plate_labels.py` | `["project_summary.db", "sample_metadata.csv", "individual_plates.csv"]` |
| `SPS_process_WGA_results.py` | `[]` — only creates new files |
| `SPS_read_WGA_summary_and_make_SPITS.py` | `["project_summary.db"]` |
| `SPS_make_illumina_index_and_FA_files_NEW.py` | `["project_summary.db", "master_plate_data.csv"]` |
| `SPS_first_FA_output_analysis_NEW.py` | `[]` — only creates new files; FA archive is PERMANENT_EXCLUSION |
| `decision_second_attempt.py` | `[]` — only writes `workflow_state.json` |
| `SPS_rework_first_attempt_NEW.py` | `["project_summary.db", "master_plate_data.csv"]` |
| `SPS_second_FA_output_analysis_NEW.py` | `[]` — only creates new files; FA archive is PERMANENT_EXCLUSION |
| `SPS_conclude_FA_analysis_generate_ESP_smear_file.py` | `["project_summary.db", "master_plate_data.csv"]` |

**Step B — Add `SNAPSHOT_ITEMS` to SIP scripts** ✅ COMPLETE (user completed in `sip_scripts_dev/`):

All 20 SIP scripts audited and updated. See `tests/fixtures/generate_sip_fixture.py` (`SIP_STEPS`) for the verified `SNAPSHOT_ITEMS` per step.

**Step C — SPS-CE fixture tests** ✅ COMPLETE (13/13 passing):
- `tests/fixtures/generate_sps_fixture.py` — 9-step SPS-CE fixture
- `tests/fixtures/mock_scripts/SPS_*.py` — 9 passing + 2 failure variant mock scripts
- `tests/test_undo_system_integration_sps.py` — 13 scenarios, all passing on first run

**Step D — SIP fixture tests** ✅ COMPLETE (13/13 passing):
- `tests/fixtures/generate_sip_fixture.py` — 20-step SIP fixture
- `tests/fixtures/mock_scripts/*.py` (SIP scripts) — 20 passing + 2 failure variant mock scripts
- `tests/test_undo_system_integration_sip.py` — 13 scenarios, all passing on first run

Note: The SPS-CE and SIP fixture tests passed on first run with no failures. This is expected — the workflow manager code is workflow-agnostic, and the Capsule tests already validated the entire snapshot lifecycle. The fixture tests serve as executable documentation of the correct `SNAPSHOT_ITEMS` for each workflow and as a regression harness for future changes.

---

### What remains to be done

**Step E — Manual sanity checks with real SPS-CE and SIP projects:**

Perform the 4-step manual sanity check (Section 14.7 of the plan) with a real in-progress project of each workflow type:
1. Open the GUI with a real in-progress SPS-CE (or SIP) project
2. Click Run on the next pending step — verify `.snapshots/` contains a new `_snapshot.zip` and `_manifest.json`
3. Click Undo — verify the project folder is restored correctly
4. If the project has old `_complete.zip` files for previously-completed steps, verify undo still works for those steps (legacy fallback)

This is the only check that can catch issues the synthetic fixture cannot: real file sizes, network drive behaviour, actual script output paths differing from what's declared in `SNAPSHOT_ITEMS`.

**Step F — Update `plans/undo_system_redesign.md`:**

The plan document still has placeholder deviation log entries (`DEV-001: [Short title]`, `DEV-002: ...`). Update it to cross-reference this notes file as the authoritative deviation log, and mark Stage 3 as complete.

---

### How to run the tests

```bash
# Run all undo system tests (all three workflow fixtures + unit tests + marker cleanup)
python -m pytest \
  tests/test_undo_system_integration.py \
  tests/test_undo_system_integration_sps.py \
  tests/test_undo_system_integration_sip.py \
  tests/test_snapshot_manager.py \
  tests/test_chronological_undo_ordering.py \
  tests/test_cyclical_workflow_undo.py \
  tests/test_rerun_success_marker.py \
  tests/test_undo_marker_cleanup.py \
  tests/test_core.py -v

# Expected: 117 passed, 1 xfailed

# Run only the workflow fixture integration tests
python -m pytest tests/test_undo_system_integration.py tests/test_undo_system_integration_sps.py tests/test_undo_system_integration_sip.py -v

# Expected: 39 passed

# Run only the marker cleanup fix tests (DEV-010)
python -m pytest tests/test_undo_marker_cleanup.py tests/test_rerun_success_marker.py -v

# Expected: 24 passed
```
