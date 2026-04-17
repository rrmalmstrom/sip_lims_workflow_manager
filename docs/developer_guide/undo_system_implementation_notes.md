# Undo System Implementation Notes — Stage 2 Deviation Log

**Date:** 2026-04-17
**Stage:** Stage 2 — Workflow Manager Repo
**Plan document:** [`plans/undo_system_redesign.md`](../../plans/undo_system_redesign.md)
**Status:** Complete — 67 tests passing, 1 xfailed (as of commit f38cc57)

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
| `tests/test_snapshot_manager.py` | 43 | ✅ All passing |
| `tests/test_chronological_undo_ordering.py` | 5 | ✅ All passing |
| `tests/test_cyclical_workflow_undo.py` | 5 | ✅ All passing |
| `tests/test_core.py` | 2 (1 xfail) | ✅ 1 passing, 1 xfail (expected) |
| `tests/test_undo_system_integration.py` | 13 | ✅ All passing |
| **Total** | **68** | **67 passed, 1 xfailed** |

---

## Implementation Status Summary — For Handoff

**Last updated:** 2026-04-17
**Last commit (workflow manager):** `f38cc57` — pushed to `origin/main`
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
- **`tests/fixtures/mock_scripts/`** — 8 mock scripts (6 passing + 2 failure variants)
- **`tests/test_undo_system_integration.py`** — 13 integration test scenarios (all passing)
- **`tests/test_snapshot_manager.py`** — 43 unit tests for `SnapshotManager`

Four bugs discovered during manual testing and fixed:
1. **Empty-dir rollback bug** — manifest now records directories; empty dirs from prior steps survive rollback
2. **GUI shows "completed" when script fails** — fixed in `app.py` (raw exit code → post-handle state check)
3. **Failed re-run stays "completed" in state** — fixed in `src/core.py` (`handle_step_result()` now always sets pending on failure)
4. **Run counter not decremented after granular undo** — fixed in `app.py` (`perform_undo()` directly manipulates `_completion_order`)

Manual sanity check with a real Capsule project: **passed**.

---

### What remains to be done

**Stage 3 — SPS-CE and SIP rollout:**

The workflow manager needs no further changes. All remaining work is in the workflow script repos.

**Step A — Add `SNAPSHOT_ITEMS` to SPS-CE scripts** ✅ COMPLETE (commit `4f0ed0c`, `SPS_library_creation_scripts/`):

All 9 SPS-CE scripts have been audited and updated. Final `SNAPSHOT_ITEMS` per script:

| Script | `SNAPSHOT_ITEMS` |
|--------|-----------------|
| `SPS_initiate_project_folder_and_make_sort_plate_labels.py` | `["project_summary.db", "sample_metadata.csv", "individual_plates.csv"]` |
| `SPS_process_WGA_results.py` | `[]` — only creates new files; manifest diff handles cleanup |
| `SPS_read_WGA_summary_and_make_SPITS.py` | `["project_summary.db"]` |
| `SPS_make_illumina_index_and_FA_files_NEW.py` | `["project_summary.db", "master_plate_data.csv"]` |
| `SPS_first_FA_output_analysis_NEW.py` | `[]` — only creates new files; FA archive is PERMANENT_EXCLUSION |
| `decision_second_attempt.py` | `[]` — only writes `workflow_state.json` (workflow manager internal state) |
| `SPS_rework_first_attempt_NEW.py` | `["project_summary.db", "master_plate_data.csv"]` |
| `SPS_second_FA_output_analysis_NEW.py` | `[]` — only creates new files; FA archive is PERMANENT_EXCLUSION |
| `SPS_conclude_FA_analysis_generate_ESP_smear_file.py` | `["project_summary.db", "master_plate_data.csv"]` |

**Step B — Add `SNAPSHOT_ITEMS` to SIP scripts** (in `sip_scripts_dev/` repo):
20 scripts need `SNAPSHOT_ITEMS` blocks. Scripts are at `/Users/RRMalmstrom/Desktop/Programming/sip_scripts_dev/`. The workflow is defined in `templates/sip_workflow.yml` (20 steps). Section 5.3 of `plans/undo_system_redesign.md` has a first-pass estimate of `SNAPSHOT_ITEMS` per script — **verify each entry against the actual script before using it.**

**Step C — SPS-CE fixture tests** (back in this repo, after Step A):
- Create `tests/fixtures/generate_sps_fixture.py`
- Create SPS-CE mock scripts in `tests/fixtures/mock_scripts/` (9 scripts + failure variants)
- Run the 13 integration test scenarios against the SPS-CE fixture
- See DEV-009 for lessons learned from the Capsule fixture tests

**Step D — SIP fixture tests** (back in this repo, after Step B):
- Create `tests/fixtures/generate_sip_fixture.py`
- Create SIP mock scripts in `tests/fixtures/mock_scripts/` (20 scripts + failure variants)
- Run the 13 integration test scenarios against the SIP fixture
- SIP has FA archive interactions (steps 9, 11, 13) — Scenario 11 must use SIP-specific FA archive paths

**Step E — Manual sanity checks:**
After each workflow's fixture tests pass, perform the 4-step manual sanity check (Section 14.7 of the plan) with a real project of that workflow type.

**Step F — Update the plan document:**
Review the deviation log (this file) and update `plans/undo_system_redesign.md` to reflect the actual implementation. The updated document becomes the authoritative reference.

---

### How to run the tests

```bash
# Run all undo system tests
python -m pytest tests/test_undo_system_integration.py tests/test_snapshot_manager.py tests/test_chronological_undo_ordering.py tests/test_cyclical_workflow_undo.py tests/test_core.py -v

# Expected: 67 passed, 1 xfailed
```
