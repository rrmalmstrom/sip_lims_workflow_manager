# SIP LIMS Workflow Manager

A simple, lightweight workflow manager for running a series of Python scripts in a SIP (Stable Isotope Probing) laboratory environment.

## Features

-   Visual, interactive checklist of workflow steps.
-   One-click execution of Python scripts.
-   Automatic state tracking with enhanced reliability.
-   Robust error handling with automatic rollback and success marker verification.
-   **Enhanced Undo functionality** with complete project state restoration and timestamp preservation.
-   **Smart re-run behavior** that always prompts for new file inputs.
-   **Skip to Step functionality** for starting workflows from any midway point.
-   **Conditional workflow support** with Yes/No decision prompts for optional steps.
-   **Intelligent project setup** with automatic file scenario detection.
-   Interactive script support with real-time terminal output.
-   **Script termination capability** with automatic rollback to pre-execution state.
-   Cross-platform support for macOS and Windows.

## Prerequisites

-   **Python 3.9** or higher must be installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

## Installation and First-Time Setup

The setup process needs to be performed only **once** per computer.

1.  **Download the Application**: Download the `lims_workflow_manager` folder (as a `.zip` file) from the shared drive and unzip it to a permanent location on your computer (e.g., your Desktop or Documents folder).

2.  **Run the Setup Script**:
    -   **On macOS**: Open the `lims_workflow_manager` folder and double-click the `setup.command` file. Your computer may ask for permission to run the script; please allow it.
    -   **On Windows**: Open the `lims_workflow_manager` folder and double-click the `setup.bat` file.

    This script will perform two key actions:
    a.  **Clone the Script Repository**: It will download the central repository of workflow scripts into a `scripts` folder inside the application directory.
    b.  **Create the Environment**: It will create an isolated Python virtual environment and install all necessary dependencies. This will not affect any other Python installations on your system.

## Updating the Workflow Scripts

This application is designed so that the workflow scripts can be updated independently from the main application.

-   The application will automatically check for new script versions every time it starts.
-   If new scripts are available, a notification will appear in the sidebar.
-   To get the latest scripts, simply close the application and run the `update_scripts.command` (macOS) or `update_scripts.bat` (Windows) file.

## Running the Application

After the one-time setup is complete, you can start the application at any time:

-   **On macOS**: Double-click the `run.command` file.
-   **On Windows**: Double-click the `run.bat` file.

A terminal window will open, and after a few moments, the application's user interface will open in your default web browser.

## How to Use

1.  **Load a Project**: Click the "Browse for Project Folder" button in the sidebar and navigate to your project folder on the shared drive. The project folder must contain a `workflow.yml` file.

2.  **Project Setup**: When loading a project for the first time, you'll be prompted to choose your situation:
    -   **🆕 New Project - Start from Step 1**: Choose this for completely new projects where no work has been done.
    -   **📋 Existing Work - Some steps completed outside workflow**: Choose this when some steps were already completed outside the workflow tool, then select which step to start from.

3.  **Run Steps**: The workflow steps will be displayed in the main area. The next available step will have an active "Run" button. Click it to execute the script.

4.  **Interactive Scripts**: If a script requires your input, a prominent "🖥️ LIVE TERMINAL" section will appear at the top of the page with colored alert banners. You will see the script's output and any questions it asks. Type your response in the "Input" box and click "Send Input" to continue. The enhanced visual indicators make it impossible to miss when a script needs your input.

5.  **Skip to Step Functionality**: For projects where some work was completed outside the workflow:
    -   Select "📋 Existing Work" during project setup
    -   Choose the step you want to start from using the dropdown menu
    -   Click "Skip to This Step" to mark all previous steps as completed outside the workflow
    -   Previous steps will show as "⏩ Completed outside workflow" and won't block your progress

6.  **Undo Functionality**: Use the "↶ Undo Last Step" button in the sidebar to revert the project to the previous completed state. The system will ask for confirmation before performing the undo operation. This completely restores all files and directories to their previous state, preserving original file modification timestamps to maintain chronological data integrity.

7.  **Conditional Workflow Decisions**: Some workflow steps may present conditional prompts asking whether you want to run optional steps (like emergency third attempts). When these appear:
    -   A clear prompt will be displayed (e.g., "Do you want to run a third attempt at library creation?")
    -   Click "✅ Yes" to run the optional step, or "❌ No" to skip to the next appropriate step
    -   The system automatically manages dependent steps based on your decision
    -   You can undo conditional decisions using the undo button to return to the decision point

8.  **Re-run Steps**: You can re-run any completed step by clicking its "Re-run" button. When re-running steps that require file inputs, the system will automatically clear previous selections and prompt you to choose new input files, ensuring fresh data for each re-run.

## Creating a New Workflow

To define a new workflow for a project, create a `workflow.yml` file in the root of the project folder. The application will automatically create this file from a protected template when you start a new project. The file should follow this format. Note how the `snapshot_items` list changes for each step to include only the critical files and directories that are created or modified in that step.

### Template Protection
The workflow template is protected in the `templates/` directory and includes:
- **YAML Validation**: Automatic validation prevents loading corrupted workflow files
- **Recovery Options**: Multiple ways to restore corrupted workflow files
- **Version Control**: Template changes are tracked in Git for reliability

```yaml
workflow_name: "SIP Fractionation and Library Prep"
steps:
  - id: setup_plates
    name: "1. Setup Isotope and FA Plates"
    script: "scripts/setup.isotope.and.FA.plates.py"
    snapshot_items:
      - "Project_Database.db"
      - "outputs/"

  - id: ultracentrifuge_transfer
    name: "2. Ultracentrifuge Transfer"
    script: "scripts/ultracentrifuge.transfer.py"
    snapshot_items:
      - "Project_Database.db"
      - "outputs/"
      
  - id: make_library_creation_files
    name: "6. Make Library Creation Files"
    script: "scripts/make.library.creation.files.96.py"
    snapshot_items:
      - "outputs/FA_upload.txt"
      - "outputs/Echo_transfer.csv"
      - "outputs/Echo_barcode.txt"
      - "outputs/Lib.info.csv"
```

-   **`id`**: A unique identifier for the step. No spaces or special characters.
-   **`name`**: The name that will be displayed in the GUI.
-   **`script`**: The path to the Python script to be executed, relative to the project folder.
-   **`snapshot_items`**: A list of the specific files and directories that should be saved before this step runs. This is critical for the Undo feature to work correctly.

### Defining User Inputs

For steps that require user-provided arguments, you can add an `inputs` section. The application will automatically generate the necessary widgets in the GUI.

-   **`type`**: The type of input. Currently, only `file` is supported, which creates a file browser widget.
-   **`name`**: The label that will be displayed next to the input widget in the GUI.
-   **`arg`**: The command-line flag to precede the value (e.g., `--input-file`). If the script uses positional arguments, this can be an empty string (`""`).

### Enabling Re-run Capability

By default, completed steps cannot be re-run. To enable re-run capability for specific steps, add the `allow_rerun: true` property to the step definition.

-   **`allow_rerun`**: Set to `true` to enable the re-run button for completed steps. When `false` or omitted, completed steps will not show a re-run button.

**Example with Inputs and Re-run Capability:**
```yaml
- id: setup_plates
  name: "1. Setup Isotope and FA Plates"
  script: "scripts/setup.isotope.and.FA.plates.py"
  snapshot_items:
    - "Project_Database.db"
    - "outputs/"
  inputs:
    - type: file
      name: "Aliquot Sheet"
      arg: ""
    - type: file
      name: "SampleScan"
      arg: ""

- id: ultracentrifuge_transfer
  name: "2. Create Ultracentrifuge Tubes"
  script: "scripts/ultracentrifuge.transfer.py"
  snapshot_items:
    - "Project_Database.db"
    - "outputs/"
  allow_rerun: true
  inputs:
    - type: file
      name: "Ultracentrifuge CSV File"
      arg: ""
```

### Conditional Workflow Steps

For steps that require user decisions during workflow execution, you can add conditional configuration. This allows users to make Yes/No choices about whether to run optional steps.

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
-   **`trigger_script`**: The script that, when completed, triggers the conditional prompt for this step.
-   **`prompt`**: The question displayed to the user for the Yes/No decision.
-   **`target_step`**: The step to jump to if the user chooses "No" (skips the conditional step).
-   **`depends_on`**: Indicates this step depends on another conditional step being activated with "Yes".

**How Conditional Workflows Work:**
1. When the trigger script completes, the conditional step automatically shows a decision prompt
2. Users see the prompt with clear Yes/No buttons
3. Choosing "Yes" activates the conditional step and any dependent steps
4. Choosing "No" skips the conditional step(s) and jumps to the target step
5. Conditional decisions can be undone to return to the decision point
## A Note for Script Authors: Current Working Directory

When the LIMS Workflow Manager runs a script, it automatically sets the **current working directory (CWD)** to the root of the **project folder** you selected.

This means your scripts can be written with the assumption that they are running *inside* the project folder. You can, and should, use simple relative paths to access your input files and write your output files.

For example, if your project folder has a structure like this:

```
my_science_project/
├── inputs/
│   └── raw_data.csv
├── outputs/
└── workflow.yml
```

A script can reliably access `raw_data.csv` using the path `"inputs/raw_data.csv"` and write results to `"outputs/results.csv"` without needing to know the full path to `my_science_project`. The application handles the context for you.

## Success Marker System for Script Authors

The LIMS Workflow Manager uses a **success marker system** to ensure reliable detection of script completion and proper rollback functionality. This system is automatically handled by the workflow scripts, but script authors should be aware of how it works:

### How It Works
- When a script completes successfully, it creates a success marker file in `.workflow_status/{script_name}.success`
- The GUI checks for both the script's exit code AND the presence of this success marker file
- If a script fails or is interrupted, no success marker is created, triggering automatic rollback

### For New Script Development
If you're creating new workflow scripts, ensure they follow this pattern at the end of successful execution:

```python
import os
from pathlib import Path

# Your script logic here...

# Create success marker on successful completion
script_name = Path(__file__).stem
status_dir = Path(".workflow_status")
status_dir.mkdir(exist_ok=True)
success_file = status_dir / f"{script_name}.success"
success_file.touch()
print(f"SUCCESS: {script_name} completed successfully")
```

This ensures your scripts integrate properly with the rollback system and provide reliable completion detection.

## Workflow File Protection

The LIMS Workflow Manager includes comprehensive protection for workflow.yml files:

### Template System
- **Protected Templates**: Master templates stored in `templates/` directory
- **Automatic Creation**: New projects automatically get clean templates
- **Version Control**: All template changes tracked in Git

### Validation and Recovery
- **YAML Validation**: Comprehensive syntax and structure checking
- **Error Prevention**: Validation occurs before project loading
- **Recovery Options**:
  - Restore from project snapshots
  - Replace with clean template
- **Clear Guidance**: Detailed error messages with recovery instructions

### Best Practices
- Never modify files in the `templates/` directory unless updating the master template
- Use the application's recovery options if workflow files become corrupted
- Template updates will be distributed with application updates