# LIMS Workflow Manager - Development Progress

**Last Updated:** 2025-09-09

This document tracks the development progress of the LIMS Workflow Manager application.

## Current Status

We have successfully completed a major refactoring of the application's core logic and fixed a critical bug related to script execution.

### Key Accomplishments:
1.  **Initial Analysis**: Reviewed `README.md` and `plan.md` to understand the project's architecture and goals.
2.  **Test Suite Overhaul**: Created a new, robust test suite (`tests/test_core_logic.py`) using a Test-Driven Development (TDD) approach. This provides a solid baseline for future development.
3.  **Core Logic Refactoring**: The monolithic `Project` class in `src/core.py` was refactored into smaller, more focused components, which now reside in `src/logic.py`:
    *   `StateManager`: For handling `workflow_state.json`.
    *   `SnapshotManager`: For managing snapshots.
    *   `ScriptRunner`: For executing workflow scripts.
4.  **Bug Fix: Script Execution**: Identified and fixed a critical bug where the application was unreliably locating the `scripts` folder. The logic was updated to be independent of the current working directory, ensuring scripts run correctly regardless of how the application is launched.
5.  **Documentation Updates**:
    *   `README.md`: Updated with a new section explaining to script authors that the script's working directory is always the project folder.
    *   `plan.md`: The technical design document was updated to reflect the new refactored architecture and the script execution context.

## Next Steps (To-Do List)

### Session 2: Interactive Debugging & Feature Enhancement
1.  **Project Loading Logic**: Implemented robust error handling for project loading.
    *   The application now detects when a `workflow.yml` file is missing.
    *   If a project database (`.db`) exists, it offers to restore the `workflow.yml` from the latest snapshot.
    *   If no database exists, it offers to create a new `workflow.yml` from a centralized, correct template file, preventing the use of outdated or incorrect workflow definitions.
2.  **Core Logic Testing**: Added a comprehensive set of `pytest` tests for the new project loading and snapshot restoration logic, ensuring the backend is stable and correct.
3.  **Interactive Script Execution Debugging**: Undertook a major debugging and refactoring effort to resolve a persistent deadlock issue where interactive scripts would hang.
    *   Refactored the `ScriptRunner` and `Project` core classes multiple times to address complex threading and process management issues.
    *   The final, stable implementation uses a non-blocking background thread to run the script and a polling mechanism in the main UI thread to safely check for completion, resolving all deadlocks and race conditions.
4.  **GUI Enhancements**: Implemented several user-requested UI improvements.
    *   The "Run" button for a step is now disabled until all required file inputs for that step have been provided by the user.
    *   The input box in the pseudo-terminal now automatically clears after input is sent.

## Next Steps (To-Do List)

-   [ ] **Investigate and fix terminal auto-scrolling**: The JavaScript-based auto-scrolling is still not working reliably and needs further investigation.
-   [ ] **Enhance the GUI to provide more detailed feedback and logging**: Improve the Streamlit front-end to give users better real-time information.
-   [ ] **Write tests for the script update mechanism**: Create tests to validate the current script update process.
-   [ ] **Implement a more robust script update mechanism**: Improve the reliability and user experience of updating workflow scripts.
-   [ ] **Write tests for `workflow.yml` validation**: Develop tests for a new feature that will validate the syntax and structure of `workflow.yml` files.
-   [ ] **Add a feature to validate the `workflow.yml` file for correctness**: Implement the validation logic to prevent users from loading malformed workflow files.
-   [ ] **Create comprehensive documentation for developers and end-users**: Finalize all documentation.