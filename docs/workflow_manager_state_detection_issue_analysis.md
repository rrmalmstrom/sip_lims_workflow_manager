# Workflow Manager Step Detection Issue Analysis

## The Problem
The workflow manager uses a **dual-state system** to determine the current step, which can lead to inconsistencies:

1. **Primary State**: `workflow_state.json` file tracks step states (`pending`, `completed`, `skipped`, etc.)
2. **Validation State**: `.workflow_status/*.success` files confirm actual script completion

## How It Should Work
- [`get_next_available_step()`](../src/core.py:101) finds the first step with `'pending'` status
- [`_check_success_marker()`](../src/core.py:417) validates that scripts actually completed successfully
- Both must align for proper step detection

## Potential Issues
1. **State File Corruption**: If `workflow_state.json` is missing entries or corrupted, steps may default to `'pending'`
2. **Inconsistent States**: Success markers exist but state file shows different status
3. **Race Conditions**: State file updated but success marker not yet created (or vice versa)
4. **Manual Intervention**: Users copying projects or manually editing files can break synchronization

## Current Symptoms (Observed Issue)
- Project has success markers for steps 1-12 (indicating completion)
- Workflow manager shows step 1 as current (indicating state file thinks all steps are `'pending'`)
- This suggests the `workflow_state.json` file is not properly reflecting the completed steps

## Code References
- **Step Detection Logic**: `src/core.py` lines 101-106
- **Success Marker Validation**: `src/core.py` lines 417-429
- **State Management**: `src/logic.py` lines 25-51

## Recommended Future Investigation
1. **Audit the dual-state system** - Determine if both mechanisms are necessary
2. **Add state validation** - Automatically sync state file with success markers on project load
3. **Improve error handling** - Better detection and recovery from state inconsistencies
4. **Consider single source of truth** - Potentially use only success markers or only state file
5. **Add diagnostic tools** - Create utilities to detect and report state inconsistencies

## Impact on FA Archiving Project
- This issue is **unrelated** to our FA archiving implementation
- Our changes to `logic.py` exclusion patterns are correct and should not affect step detection
- Testing should proceed with a fresh project to avoid state inconsistencies

## Date
November 3, 2025

## Context
This issue was discovered while testing FA result archiving functionality. The workflow manager was incorrectly showing step 1 as current despite having success markers for steps 1-12, preventing proper testing of the archiving implementation.