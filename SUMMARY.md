# Project Summary: LIMS Workflow Manager (v3)

## 1. Project Goal
To create a simple, lightweight, cross-platform GUI application to manage and execute a series of Python-based laboratory workflow scripts, with robust error handling and version control for the scripts.

## 2. Current Status
- **Phase 1 (Core Engine):** Mostly complete. All logic for parsing, state management, and snapshots is implemented and tested. A bug has been identified in the `run_step` method's pathing logic.
- **Phase 2 (GUI):** Complete. The Streamlit UI is fully featured.
- **Phase 3 (Distribution):** Complete. The script-based distribution model using Git is implemented and tested on macOS. Awaiting final Windows test.
- **Phase 4 (Workflow Implementation):** Complete. The production `workflow.yml` and user `README.md` are authored.

## 3. Key Design Decisions
- **Core Engine:** A generic engine that reads workflow definitions from a `workflow.yml` file.
- **State Management:** Workflow progress is tracked in a `workflow_state.json` file, supporting "pending", "completed", and "skipped" states.
- **Undo/Redo:** Implemented via a snapshot mechanism.
- **Error Handling:** The engine automatically restores the pre-run snapshot if any script fails.
- **Script Management (Centralized Git Repository):**
    - The application's workflow scripts are managed in a central, private Git repository and cloned into a local `scripts` folder during setup.
- **Distribution Model:** The application is distributed as a folder. A one-time `setup` script prepares the environment. A `run` script launches the app.

## 4. Next Steps (To be continued in a new task)
1.  **BUG FIX**: Correct the `run_step` method in `src/core.py`. It is currently looking for workflow scripts relative to the *project folder* instead of the application's centralized `scripts` folder. The path construction logic needs to be updated to point to the correct location.
2.  **Final Testing**: Once the bug is fixed, perform the full end-to-end test of the application on both macOS and Windows, including the step-skipping logic.
3.  **Final Documentation Review**: Give the `README.md` a final proofread.
4.  **Project Completion**.