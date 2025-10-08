# SIP LIMS Workflow Manager - Detailed Design Document

**Version:** 1.2
**Date:** 2025-09-11

## 1. Introduction & Vision

### 1.1. Guiding Principles
- **Simplicity Over Complexity**: At every stage, prioritize the simplest possible solution that meets the requirements. Avoid adding features or layers of abstraction that are not immediately necessary. The goal is a lightweight, maintainable tool, not an enterprise-grade engine.
- **User-Centric Design**: The tool is for lab technicians. It must be intuitive and forgiving.
- **Robustness**: The system must be resilient to script errors and prevent data corruption.
- **Flexibility**: The design must accommodate the non-linear nature of lab work.

### 1.2. Core Vision
To create a simple, robust, and user-friendly desktop application that allows SIP (Stable Isotope Probing) lab technicians to execute, monitor, and manage multi-step Python-based workflows. The tool will be packaged as a standalone executable for both Windows and macOS, operate on project folders located on a shared drive, and provide features for undoing mistakes, handling script errors gracefully, and terminating scripts when needed.

## 2. System Architecture

### 2.1. Technology Stack
- **GUI:** Streamlit
- **Backend & Core Logic:** Python 3
- **Environment Management:** Conda
- **Configuration:** YAML (`workflow.yml`, `environment.yml`)
- **State Management:** JSON (`workflow_state.json`)

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
- `allow_rerun`: (Optional) Set to `true` to enable re-run capability for completed steps. Defaults to `false`.
- `inputs`: (Optional) A list of user input definitions for file selection or other parameters.
- `conditional`: (Optional) Configuration for conditional workflow steps that require user decisions.

### 3.1.1. Template Management
The system uses a protected template system for workflow definitions:
- **Master Template**: Stored in `templates/workflow.yml` with Git version control
- **Template Protection**: Users cannot accidentally modify the master template
- **Validation**: All workflow files are validated for syntax and structure before loading
- **Recovery**: Multiple recovery options available for corrupted workflow files

### 3.2. State Management & The "Interactive Checklist"
The system is a flexible, interactive checklist, managed by the `StateManager`.
- **`workflow_state.json`**: Tracks the status of each step `id` (e.g., "completed", "pending").
- **GUI Model**: Renders all steps as cards with "Run" or "Re-run" buttons, allowing selective execution based on step configuration.
- **Selective Re-run**: Only steps with `allow_rerun: true` display re-run buttons when completed, providing precise control over workflow execution.
- **Conditional Decisions**: Steps with `conditional` configuration can present Yes/No prompts to users, allowing workflow branching based on user decisions.

### 3.3. Snapshot & Undo/Redo Logic
- **Snapshot Trigger**: A snapshot is created **only** when a step is successfully completed for the **first time**. This is handled by the `SnapshotManager`.
- **Undo Action**: Reverts the entire project to the state before the last completed step was run.
- **Timestamp Preservation**: File modification timestamps are preserved during rollback operations to maintain chronological data integrity. This applies to both manual undo operations and automatic rollback when scripts fail.
- **Conditional Decision Snapshots**: Special snapshots are created before conditional decisions to enable undoing back to decision points rather than previous steps.

### 3.4. Error Handling & Success Marker System
A script error will never leave the project in a corrupted state. The system uses a dual-verification approach for reliable failure detection:

- **Success Marker Files**: Each script creates a `.workflow_status/{script_name}.success` file only upon successful completion
- **Exit Code Verification**: Traditional exit code checking is maintained as a secondary verification
- **Dual Verification**: The GUI checks both exit codes AND success marker presence before marking a step as completed
- **Automatic Rollback**: If either verification fails, the `Project` class instructs the `SnapshotManager` to automatically restore the pre-run snapshot

This approach solves the critical issue where Python scripts could exit with code 0 (success) even when encountering errors, ensuring reliable rollback functionality.

### 3.4.1. Workflow File Validation
The system includes comprehensive validation for workflow.yml files:
- **YAML Syntax Validation**: Ensures proper YAML structure and syntax
- **Required Field Validation**: Verifies presence of workflow_name, steps, and step fields (id, name, script)
- **Structure Validation**: Confirms proper data types and step organization
- **Proactive Error Prevention**: Validation occurs before project loading to prevent crashes
- **Recovery Options**: Multiple paths to fix corrupted workflow files

### 3.5. Distribution & Updates

#### Two-Repository Architecture
The system uses separate repositories for better version control and independent updates:

- **Main Application Repository (`sip_lims_workflow_manager`)**:
  - Contains GUI application, workflow engine, setup scripts, documentation
  - Updates include new features, bug fixes, user interface improvements
  
- **Scripts Repository (`sip_scripts_workflow_gui`)**:
  - Contains all Python workflow scripts for laboratory analysis
  - Updates include scientific workflow improvements, new analysis methods, script bug fixes
  - Automatically cloned during setup process

#### Application Updates
- **Automated Release Script (`release.py`):** A dedicated release script will automate the creation of new versions. It will:
  - Prompt for a new version number.
  - Create a Git tag for the version.
  - Run the PyInstaller build process.
  - Create a versioned release folder on a shared drive.
  - Automatically generate the `latest.json` file in the central distribution location.
- **Application Update Check:** The packaged application will check for updates on startup.
  - It reads its current version from Git tags.
  - It attempts to read `latest.json` from the central location. If this file is missing, the check fails silently.
  - If a new version is detected, a non-blocking notification is displayed to the user.

#### Script Updates
- **Independent Versioning**: Scripts can be updated without updating the main application
- **Automatic Detection**: Application checks for script updates on startup
- **Simple Update Process**: Users run `update_scripts.command` or `update_scripts.bat` to get latest scripts
- **Git-Based**: Uses standard Git pull mechanism for reliable updates

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

### 3.8. Selective Re-run Capability
The system provides granular control over which workflow steps can be re-executed after completion:

- **Default Behavior**: Steps without the `allow_rerun` property cannot be re-run once completed
- **Enabled Re-runs**: Steps with `allow_rerun: true` show re-run buttons and input widgets when completed
- **Script-Based Logic**: Re-run capability is tied to specific scripts rather than step positions for maintainability
- **Input Management**: Re-run-enabled steps automatically clear previous input selections to ensure fresh data

### 3.8.1. Template Protection Strategy
The workflow template protection system provides comprehensive safeguards:
- **Protected Location**: Templates stored in dedicated `templates/` directory
- **Git Version Control**: All template changes tracked with commit history
- **Validation System**: Comprehensive YAML validation prevents loading corrupted files
- **Recovery Mechanisms**: Dual recovery options (snapshot restoration and template replacement)
- **User Guidance**: Clear error messages with step-by-step recovery instructions
- **Backward Compatibility**: Existing projects continue to work without modification

**Example Workflow Configuration:**
```yaml
workflow_name: "Laboratory Workflow"
steps:
  - id: setup_step
    name: "1. Initial Setup"
    script: "setup.py"
    snapshot_items: ["database.db"]
    # No allow_rerun - cannot be re-run once completed
    
  - id: analysis_step
    name: "2. Data Analysis"
    script: "analyze.py"
    snapshot_items: ["results/"]
    allow_rerun: true  # Can be re-run multiple times
    inputs:
      - type: file
        name: "Input Data File"
        arg: "--input"
```

### 3.1.2. Conditional Workflow Configuration
The system supports conditional workflow steps that allow users to make Yes/No decisions during workflow execution:

```yaml
- id: rework_second_attempt
  name: "10. Third Attempt Library Creation"
  script: "emergency.third.attempt.rework.py"
  snapshot_items: ["outputs/"]
  conditional:
    trigger_script: "second.FA.output.analysis.py"
    prompt: "Do you want to run a third attempt at library creation?"
    target_step: "conclude_fa_analysis"

- id: third_fa_analysis
  name: "11. Analyze Library QC (3rd)"
  script: "emergency.third.FA.output.analysis.py"
  snapshot_items: ["outputs/Lib.info.csv"]
  conditional:
    depends_on: "rework_second_attempt"
```

**Conditional Configuration Properties:**
- `trigger_script`: The script that, when completed, triggers the conditional prompt
- `prompt`: The question displayed to the user for the Yes/No decision
- `target_step`: The step to jump to if the user chooses "No" (skips the conditional step)
- `depends_on`: Indicates this step depends on another conditional step being activated

## 4. GUI Design
- **Layout**: A two-column Streamlit application.
  - **Sidebar**: Project selection, Undo/Redo buttons, and update notifications.
  - **Main Content**: Displays workflow steps as cards.
- **Interactivity**:
  - **Folder Picker**: A "Browse..." button will use a `tkinter`-based helper script to open a native OS folder dialog.
  - **Run Buttons**: Each step card has conditional "Run" or "Re-run" buttons based on step status and `allow_rerun` configuration.
  - **Selective Display**: Re-run buttons only appear for completed steps with `allow_rerun: true` property.
  - **Interactive Terminal**: An `st.expander` will serve as a live terminal. It will display real-time script output and provide a text box for users to send input to the running script. This is managed by a `ScriptRunner` class that uses a pseudo-terminal (`pty`) to create a robust, cross-platform, two-way communication channel with the subprocess.
  - **Script Termination**: A "🛑 Terminate" button appears next to the input controls when a script is running, allowing users to stop execution and automatically rollback to the pre-execution state.

## 5. Development Plan
1.  **Core Engine**: Build and test the core logic classes (`Workflow`, `Project`, `StateManager`, `SnapshotManager`, `ScriptRunner`).
2.  **GUI Implementation**: Develop the Streamlit front-end.
3.  **Conditional Workflow System**: Implement conditional workflow functionality with automatic triggering and enhanced undo behavior.
4.  **Script Termination System**: Implement terminate button with automatic rollback functionality for user control over script execution.
5.  **Packaging**: Create the `release.py` script and test the PyInstaller builds.
