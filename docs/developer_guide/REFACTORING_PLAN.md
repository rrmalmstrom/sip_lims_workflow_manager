 Data harmonization component and# Refactoring and Orchestration Plan

This document outlines the definitive plan for refactoring the Python scripts related to the pooling workflow and creating a master orchestrator script.

## Phase 1: Test Environment Setup

1.  **Activate Virtual Environment:** Ensure all work is done within the project's designated Python environment (`.venv`).
    *   **Command:** `source .venv/bin/activate`

2.  **Create Test Directories:** Establish a clean, isolated testing environment.
    *   `tests/expected_output`: This directory will store the baseline output files provided by the user.
    *   `tests/actual_output`: The refactored scripts will be configured to write their output here for comparison.

## Phase 2: Git Branching

3.  **Create Development Branch:** Isolate all code changes in a new branch to protect the `main` branch.
    *   **Command:** `git checkout -b refactor-workflow`

## Phase 3: Incremental Refactoring and Validation

4.  **Refactor Script 1: `scripts/conclude.all.fa.analysis.py`**
    *   a. Encapsulate the main logic within a `main()` function.
    *   b. Add an `if __name__ == "__main__":` block to ensure it remains runnable from the command line.
    *   c. Remove the code that creates `final_lib_summary.csv`.
    *   d. **Validate:** Run the refactored script, directing its output to `tests/actual_output`. Compare the resulting `.db` file against the baseline in `tests/expected_output`.
    *   e. **Commit:** `git commit -m "refactor(conclude): Encapsulate logic and simplify output"`

5.  **Refactor Script 2: `scripts/make.clarity.summary.py`**
    *   a. Encapsulate logic in a `main()` function with an entry point.
    *   b. Remove the `compareFinalVSlibinfo()`, `updateSQLdb()`, and `makeClaritySummary()` functions.
    *   c. Modify the script to read directly from `lib_info.db`.
    *   d. **Validate:** Run the script, directing its output to `tests/actual_output`, and compare the generated `.db` file against the baseline.
    *   e. **Commit:** `git commit -m "refactor(clarity-summary): Encapsulate and streamline workflow"`

6.  **Refactor Script 3: `scripts/generate_pool_assignment_tool.py`**
    *   a. Encapsulate logic in a `main()` function with an entry point.
    *   b. **Validate:** Run the script, directing its output to `tests/actual_output`, and compare the generated `.xlsx` file against the baseline.
    *   c. **Commit:** `git commit -m "refactor(pool-tool): Encapsulate logic in main"`

## Phase 4: Orchestration and Final Validation

7.  **Create and Test Orchestrator Script (`run_workflow.py`):**
    *   a. Create the new script to call the three refactored scripts in sequence using the `subprocess` module.
    *   b. **Validate:** Run the orchestrator and ensure all files generated in `tests/actual_output` are identical to those in `tests/expected_output`.
    *   c. **Commit:** `git commit -m "feat: Add workflow orchestrator script"`

## Phase 5: Merging

8.  **Merge to Main:** After all validation steps pass successfully on the `refactor-workflow` branch, merge the changes back into the `main` branch.

## Phase 6: Post-Refactor Investigation

9.  **Investigate CSV vs. SQLite Discrepancy:**
    *   During testing, the `compareFinalVSlibinfo` function in `make.clarity.summary.py` triggered an interactive prompt, indicating a difference between `final_lib_summary.csv` and `lib_info.db`.
    *   **Action:** Investigate the root cause of this difference. It is likely due to floating-point precision or data type mismatches between the CSV and SQLite formats.
    *   **Goal:** Modify the scripts to ensure the two files are always identical, thus eliminating the interactive prompt and making the workflow fully automated.

---
## Appendix: Data Consistency Investigation

During the refactoring process, a critical data consistency issue was discovered. This section documents the problem and the validated solution for future reference.

### The Problem

The `make.clarity.summary.py` script was designed to compare `final_lib_summary.csv` and `lib_info.db`. In an automated workflow, these files should be identical. However, the `DataFrame.equals()` check consistently failed.

Our investigation revealed that this was due to subtle, non-obvious differences in data representation between the CSV and SQLite formats, specifically:

1.  **Missing Value Mismatches:** Missing numeric data was represented as `NaN` (a float concept) when read from the CSV, but as `None` (Python's null object) or an empty string `''` when read from the SQLite database.
2.  **Integer vs. Float Mismatches:** Numbers like `1` were stored as integers in the database but sometimes read as floats (`1.0`) from the CSV, causing the equality check to fail.

### The Validated Solution

A robust, two-part harmonization logic was developed and validated in a test script. This logic should be applied before any comparison to ensure data consistency.

**Example Implementation:**

```python
# Assume df_csv and df_db are loaded from their respective sources

# Ensure columns are in the same order first
df_db = df_db[df_csv.columns]

# Harmonize types column by column
for col in df_csv.columns:
    # Check if the source column is numeric
    if pd.api.types.is_numeric_dtype(df_csv[col]):
        # Convert both columns to pandas' nullable Float64 type.
        # This handles NaN, integers, and floats consistently.
        df_csv[col] = df_csv[col].astype('Float64')
        df_db[col] = pd.to_numeric(df_db[col], errors='coerce').astype('Float64')
    else:
        # For all other columns, convert to pandas' nullable string type.
        df_csv[col] = df_csv[col].astype('string').fillna(pd.NA)
        df_db[col] = df_db[col].astype('string').fillna(pd.NA)

# After this loop, df_csv.equals(df_db) will return True if the data values are truly identical.
```

This solution ensures that the comparison is based on the actual data values, not the quirks of file format representation, making automated checks reliable.