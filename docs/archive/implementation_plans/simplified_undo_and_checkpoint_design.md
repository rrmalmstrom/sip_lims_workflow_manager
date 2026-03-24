# Design Specification: Simplified Undo and Checkpoint Steps

This document outlines the final design for a fundamental refactoring of the Undo and conditional logic systems. This new architecture simplifies the application by making user decisions a formal, trackable part of the workflow, which in turn dramatically simplifies the Undo mechanism and removes previously identified bugs.

## 1. Core Concept: The "Checkpoint" Step

The primary innovation is the introduction of a new step `type` in the `workflow.yml` specification: `type: "decision"`.

### 1.1. Purpose
A "checkpoint" or "decision" step does not run a Python script. Its sole purpose is to pause the workflow and present the user with a question (defined by a `prompt` key). Based on their "Yes" or "No" answer, the system will execute a series of pre-defined state changes.

This decouples the act of *making a decision* from the act of *running a script*.

### 1.2. Example `workflow.yml` Implementation
The existing conditional logic will be refactored to use a checkpoint step.

**Old `workflow.yml`:**
```yaml
  - id: rework_second_attempt # Step 10
    ...
    conditional:
      trigger_script: "second.FA.output.analysis.py"
      prompt: "Do you want to run a third attempt...?"
      target_step: "conclude_fa_analysis"
```

**New `workflow.yml` with Checkpoint:**
```yaml
  - id: second_fa_analysis # Step 9
    name: "9. Analyze Library QC (2nd)"
    script: "second.FA.output.analysis.py"

  - id: step_9a_rework_decision # <-- NEW CHECKPOINT STEP
    name: "Decision: Third Rework"
    type: "decision"
    prompt: "Do you want to run a third attempt at library creation?"
    on_yes:
      - set_state: { step_id: "rework_second_attempt", status: "pending" }
    on_no:
      - set_state: { step_id: "rework_second_attempt", status: "skipped" }
      - set_state: { step_id: "third_fa_analysis", status: "skipped" }
      - set_state: { step_id: "conclude_fa_analysis", status: "pending" }

  - id: rework_second_attempt # Step 10 (Now a normal step)
    name: "10. Third Attempt Library Creation"
    script: "emergency.third.attempt.rework.py"
```

### 1.3. Benefits
-   **Eliminates "Weird" States**: The problematic `"awaiting_decision"` status is completely removed from script-based steps. All steps now have a simple, predictable lifecycle (`pending`, `completed`, `skipped`).
-   **Decisions are Traceable**: The act of making a decision becomes a formal, completed step in the workflow history, which can be undone like any other step.

## 2. Snapshot Philosophy: "Before" Snapshots Only

To support this simplification, the snapshot system is streamlined.

-   **Elimination of `_after` Snapshots**: The creation of snapshots *after* a script completes is removed. They are no longer needed and were a source of complexity in the old Undo logic.
-   **"Before" Snapshot is King**: A single snapshot, named `_run_X_complete.zip`, is created by the `run_step` method immediately before a script executes. This is the only snapshot type needed for rollbacks.
-   **Snapshot Deletion**: The "before" snapshot for a specific run (e.g., `..._run_2.zip`) is deleted **only** when that specific run is undone. This correctly manages the run count.

## 3. The New Undo: A Simple, Predictable "Do-Over"

The concepts of "Soft" and "Hard" Undo are removed. There is now only one "Undo" button with one consistent behavior.

### 3.1. Undo Logic
1.  Find the last step in the workflow with a status of `"completed"`. This can be a script step or a decision step.
2.  Identify the most recent run number for that step by finding the highest-numbered `_run_X_complete.zip` snapshot.
3.  Restore that snapshot.
4.  Delete that same snapshot file.
5.  Re-calculate the number of remaining `_run_X` snapshots for that step.
    -   If the count is `> 0`, the step's status **remains `"completed"`**. This correctly handles undoing a re-run.
    -   If the count is `0`, the step's status is changed to `"pending"`.

### 3.2. User Experience
The user experience is now simple and predictable:
-   Clicking "Undo" always reverses the last single action taken.
-   If they undo the 3rd run of a step, the system reverts to the state before that 3rd run, and the step remains "completed" (reflecting the 2nd successful run).
-   If they undo a decision at a checkpoint, they are returned to the Yes/No prompt for that decision.

This design is more robust, easier to maintain, and eliminates the entire class of bugs we discovered related to the fragile, complex `perform_undo` function.