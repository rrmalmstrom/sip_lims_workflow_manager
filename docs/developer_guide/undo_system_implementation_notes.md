# Undo System Implementation Notes — Stage 2 Deviation Log

**Date:** 2026-04-17  
**Stage:** Stage 2 — Workflow Manager Repo  
**Plan document:** [`plans/undo_system_redesign.md`](../../plans/undo_system_redesign.md)  
**Status:** Complete — 66 tests passing, 1 xfailed

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
| `tests/test_snapshot_manager.py` | 43 | ✅ All passing |
| `tests/test_chronological_undo_ordering.py` | 5 | ✅ All passing |
| `tests/test_cyclical_workflow_undo.py` | 5 | ✅ All passing |
| `tests/test_core.py` | 2 (1 xfail) | ✅ 1 passing, 1 xfail (expected) |
| `tests/test_undo_system_integration.py` | 12 | ✅ All passing |
| **Total** | **67** | **66 passed, 1 xfailed** |
