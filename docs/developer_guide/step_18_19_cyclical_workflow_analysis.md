# Analysis of the Cyclical Workflow Between Step 18 and Step 19

This document summarizes the analysis of the iterative relationship between Step 18 (`pool_fa12_analysis`) and Step 19 (`rework_pooling`) in the SIP LIMS Workflow Manager.

## 1. Overview of the Cyclical Process

The interaction between Step 18 and Step 19 is not a simple linear progression but an intentional, iterative QC (Quality Control) loop. The purpose of this loop is to rework and re-test pools until they meet the required quality standards.

The process is as follows:

1.  **Run Step 18 (`pool.FA12.analysis.py`):** The user runs this script to analyze the latest QC data from the lab. The script finds the most recent `Attempt_X` directory and updates the master `pool_summary.csv` with the pass/fail results.
2.  **Run Step 19 (`rework.pooling.steps.py`):** The user runs this script, which reads the updated `pool_summary.csv`. It then makes a decision:
    *   **Outcome A (Workflow Complete):** If all pools pass QC, the script generates final output files and prints a `"WORKFLOW COMPLETE"` message to the console.
    *   **Outcome B (Rework Required):** If any pools fail QC, the script creates a new `Attempt_X+1` directory, generates files with instructions for the lab rework, and prints a `"REWORK NEEDED"` message to the console.
3.  **Lab Rework:** The lab user performs the rework based on the files generated in Outcome B.
4.  **Repeat Cycle:** The user returns to Step 1, running Step 18 again to analyze the new QC data from the reworked pools. The cycle continues until Outcome A is achieved.

## 2. Technical Implementation and State Management

Our analysis of the application's source code (`app.py`, `src/logic.py`) and the relevant scripts reveals the following:

*   **Scripts as the Source of Truth:** The scripts use explicit print statements (`"WORKFLOW COMPLETE"` and `"REWORK NEEDED"`) to signal the outcome of Step 19.
*   **Application's Role:** The main application (`app.py`) uses a `ScriptRunner` class (from `src/logic.py`) that executes scripts in a pseudo-terminal. This `ScriptRunner` captures all console output in real-time and makes it available to the application.
*   **The Gap:** The application currently displays this output but does not act on it. It marks Step 19 as "completed" regardless of the outcome, forcing the user to mentally track the true state of the iterative loop.

## 3. Proposed Solution for State Management

To make the UI accurately reflect the workflow's state, the application should be modified to parse the script's output and manage the state accordingly.

**Proposed Logic (to be implemented in `app.py`):**

1.  After Step 19 (`rework_pooling`) finishes, the application should inspect the captured console output.
2.  **If `"WORKFLOW COMPLETE"` is found:**
    *   Mark Step 19 as **`completed`** (✅). The workflow is finished.
3.  **If `"REWORK NEEDED"` is found:**
    *   Introduce a new state, **`rework_required`** (e.g., displayed with a 🔄 icon).
    *   Mark Step 19 with this new `rework_required` status.
    *   Automatically reset the status of Step 18 (`pool_fa12_analysis`) to **`pending`** (⚪).

This change would make the application's state machine aware of the iterative loop, providing clear visual guidance to the user on the required next step and removing ambiguity.