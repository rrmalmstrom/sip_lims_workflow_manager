# LIMS Workflow Manager - Detailed Design Document

**Version:** 1.1
**Date:** 2025-09-10

## 1. Introduction & Vision

### 1.1. Guiding Principles
- **Simplicity Over Complexity**: At every stage, prioritize the simplest possible solution that meets the requirements. Avoid adding features or layers of abstraction that are not immediately necessary. The goal is a lightweight, maintainable tool, not an enterprise-grade engine.
- **User-Centric Design**: The tool is for lab technicians. It must be intuitive and forgiving.
- **Robustness**: The system must be resilient to script errors and prevent data corruption.
- **Flexibility**: The design must accommodate the non-linear nature of lab work.

### 1.2. Core Vision
To create a simple, robust, and user-friendly desktop application that allows lab technicians to execute, monitor, and manage multi-step Python-based workflows. The tool will be packaged as a standalone executable for both Windows and macOS, operate on project folders located on a shared drive, and provide features for undoing mistakes and handling script errors gracefully.

## 2. System Architecture

### 2.1. Technology Stack
- **GUI:** Streamlit
- **Backend & Core Logic:** Python 3
- **Configuration:** YAML (`workflow.yml`)
- **State Management:** JSON (`workflow_state.json`)
- **Packaging:** PyInstaller

### 2.2. On-Disk Structure (Per Project)
Each project will be a self-contained folder on the shared drive with the following structure:
```
project_folder/
├── workflow.yml
├── workflow_state.json
├── script_managed.db
├── inputs/
├── outputs/
├── .snapshots/
└── .workflow_status/
    ├── script1.success
    ├── script2.success
    └── ...
```

### 2.3. Core Logic Classes
The backend is composed of several key classes:
- **`Project`**: The main coordinating class. It represents a user's project folder and orchestrates the other components.
- **`Workflow`**: Parses and represents the `workflow.yml` file.
- **`StateManager`**: Handles all reading and writing to the `workflow_state.json` file.
- **`SnapshotManager`**: Manages the creation and restoration of snapshots in the `.snapshots` directory.
- **`ScriptRunner`**: Responsible for finding and executing the individual Python workflow scripts.

## 3. Detailed Feature Design

### 3.1. Workflow Definition (`workflow.yml`)
This YAML file is the blueprint for a workflow. Each step is a dictionary with the following keys:
- `id`: A unique machine-readable string.
- `name`: A human-readable string for the GUI.
- `script`: The relative path to the Python script to execute.
- `snapshot_items`: A list of files and directories to be included in this step's snapshot.

### 3.2. State Management & The "Interactive Checklist"
The system is a flexible, interactive checklist, managed by the `StateManager`.
- **`workflow_state.json`**: Tracks the status of each step `id` (e.g., "completed", "pending").
- **GUI Model**: Renders all steps as cards with "Run" or "Re-run" buttons, allowing the user to execute any step at any time to handle partial rework.

### 3.3. Snapshot & Undo/Redo Logic
- **Snapshot Trigger**: A snapshot is created **only** when a step is successfully completed for the **first time**. This is handled by the `SnapshotManager`.
- **Undo Action**: Reverts the entire project to the state before the last completed step was run.

### 3.4. Error Handling & Success Marker System
A script error will never leave the project in a corrupted state. The system uses a dual-verification approach for reliable failure detection:

- **Success Marker Files**: Each script creates a `.workflow_status/{script_name}.success` file only upon successful completion
- **Exit Code Verification**: Traditional exit code checking is maintained as a secondary verification
- **Dual Verification**: The GUI checks both exit codes AND success marker presence before marking a step as completed
- **Automatic Rollback**: If either verification fails, the `Project` class instructs the `SnapshotManager` to automatically restore the pre-run snapshot

This approach solves the critical issue where Python scripts could exit with code 0 (success) even when encountering errors, ensuring reliable rollback functionality.

### 3.5. Distribution & Updates
- **Automated Release Script (`release.py`):** A dedicated release script will automate the creation of new versions. It will:
  - Prompt for a new version number.
  - Update an internal `version.json` file.
  - Run the PyInstaller build process.
  - Create a versioned release folder on a shared drive.
  - Automatically generate the `latest.json` file in the central distribution location.
- **Application Update Check:** The packaged application will check for updates on startup.
  - It reads its internal `version.json`.
  - It attempts to read `latest.json` from the central location. If this file is missing, the check fails silently.
  - If a new version is detected, a non-blocking notification is displayed to the user.

### 3.6. Script Execution Context
A critical feature of the system is how it provides a consistent environment for the executed scripts.
- **Working Directory**: The `ScriptRunner` class explicitly sets the current working directory (CWD) of the script being executed to the path of the user's selected **project folder**.
- **Benefit**: This allows script authors to use simple, reliable relative paths (e.g., `inputs/data.csv`) without needing to know the absolute path of the project folder or the location of the main application.
- **Success Marker Integration**: Scripts automatically create success marker files in `.workflow_status/` upon successful completion, enabling reliable failure detection and rollback functionality.

### 3.7. Script Development Guidelines
For new workflow scripts, developers should follow this pattern for success marker integration:

```python
import os
from pathlib import Path

# Script logic here...

# Create success marker on successful completion
script_name = Path(__file__).stem
status_dir = Path(".workflow_status")
status_dir.mkdir(exist_ok=True)
success_file = status_dir / f"{script_name}.success"
success_file.touch()
print(f"SUCCESS: {script_name} completed successfully")
```

## 4. GUI Design
- **Layout**: A two-column Streamlit application.
  - **Sidebar**: Project selection, Undo/Redo buttons, and update notifications.
  - **Main Content**: Displays workflow steps as cards.
- **Interactivity**:
  - **Folder Picker**: A "Browse..." button will use a `tkinter`-based helper script to open a native OS folder dialog.
  - **Run Buttons**: Each step card has a "Run" or "Re-run" button that triggers the `Project.run_step()` method.
  - **Interactive Terminal**: An `st.expander` will serve as a live terminal. It will display real-time script output and provide a text box for users to send input to the running script. This is managed by a `ScriptRunner` class that uses a pseudo-terminal (`pty`) to create a robust, cross-platform, two-way communication channel with the subprocess.

## 5. Development Plan
1.  **Core Engine**: Build and test the core logic classes (`Workflow`, `Project`, `StateManager`, `SnapshotManager`, `ScriptRunner`).
2.  **GUI Implementation**: Develop the Streamlit front-end.
3.  **Packaging**: Create the `release.py` script and test the PyInstaller builds.
