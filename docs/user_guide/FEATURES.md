# Application Features

This document provides a detailed overview of the key features of the SIP LIMS Workflow Manager.

## Unified Cross-Platform Launcher

The SIP LIMS Workflow Manager uses a unified Python launcher ([`run.py`](../../run.py)) that provides a consistent experience across all operating systems.

### Key Features
- **Single Command**: `python3 run.py` works on Windows, macOS, and Linux
- **Interactive Interface**: Rich CLI with colored output and user-friendly prompts
- **Command-Line Arguments**: Full support for automation and scripting
- **Enhanced Error Handling**: Clear error messages and graceful recovery
- **Platform Detection**: Automatic adaptation to host operating system features
- **Docker Integration**: Intelligent detection of Docker commands and container management

### Usage Examples
```bash
# Interactive mode (recommended for first-time users)
python3 run.py

# Skip updates for faster startup
python3 run.py --no-updates

# Automated workflow launch
python3 run.py --workflow-type sip --mode production --no-updates

# Show all available options
python3 run.py --help
```

### Migration from Legacy Scripts
The unified launcher replaces the previous platform-specific scripts:
- **Previous**: `run.mac.command` (macOS) and `run.windows.bat` (Windows)
- **Current**: `python3 run.py` (all platforms)

This change provides better reliability, enhanced features, and easier maintenance while maintaining full backward compatibility with existing workflows.

## Multi-Workflow Support

The SIP LIMS Workflow Manager now supports multiple laboratory workflow types:

### Supported Workflows

#### SIP (Stable Isotope Probing) - 21 Steps
- **Purpose**: Complete SIP fractionation and library preparation workflow
- **Steps**: 21 comprehensive steps from setup through final processing
- **Scripts Repository**: `sip_scripts_workflow_gui`
- **Template**: [`templates/sip_workflow.yml`](../../templates/sip_workflow.yml)

#### SPS-CE (SPS-Capillary Electrophoresis) - 6 Steps
- **Purpose**: SPS library creation with Fragment Analyzer integration
- **Steps**: 6 focused steps for SPS-CE workflow execution
- **Scripts Repository**: `SPS_library_creation_scripts`
- **Template**: [`templates/sps_workflow.yml`](../../templates/sps_workflow.yml)

### Workflow Selection

When starting the application, you'll be prompted to select your workflow type:

```
Select workflow type:
1) SIP (Stable Isotope Probing)
2) SPS-CE (SPS-Capillary Electrophoresis)
Enter choice (1 or 2):
```

### Backward Compatibility

- **Existing SIP workflows**: Continue to work exactly as before with zero changes
- **Default behavior**: If no workflow type is specified, defaults to SIP workflow
- **All existing features**: Undo, snapshots, state management work identically for both workflows

## Interactive Workflow Checklist

The main interface of the application is an interactive checklist that visually represents the steps of your laboratory workflow. Each step is displayed as a card with its current status.

-   **Status Indicators**: Each step is clearly marked with its status:
    -   ⚪ **Pending**: The step has not yet been run.
    -   ⏳ **Running**: The step is currently being executed.
    -   ✅ **Completed**: The step has been successfully completed.
    -   ⏩ **Skipped**: The step was marked as completed outside the workflow during project setup.
    -   ⏭️ **Skipped (conditional)**: The step was skipped as a result of a conditional decision.
    -   ❓ **Awaiting decision**: The workflow is paused pending a "Yes" or "No" decision from the user.
-   **Run/Re-run Buttons**: Each step has a "Run" or "Re-run" button, allowing you to execute or re-execute steps as needed. Re-run functionality is only available for steps that have been configured to allow it.

## Project Setup

The application provides a streamlined process for setting up new and existing projects.

-   **Automatic Detection**: The application automatically detects the state of a project folder and guides you through the setup process.
-   **Project Name Display**: The sidebar displays the actual name of your project folder for easy identification, rather than the internal Docker mount path.
-   **New Project**: If you are starting a new project, the application will initialize the workflow with all steps marked as "pending."
-   **Existing Work**: If you are working with a project that has already been partially completed outside of the workflow manager, you can use the "Skip to Step" feature to mark all previous steps as "skipped" and start the workflow from any step.

## Conditional Workflows

The workflow manager supports conditional steps that allow for branching logic in your workflow.

-   **Decision Prompts**: When a conditional step is triggered, the application will display a prompt asking for a "Yes" or "No" decision.
-   **Workflow Branching**:
    -   If you select "Yes," the conditional step will be activated and run.
    -   If you select "No," the conditional step and any dependent steps will be skipped, and the workflow will jump to the specified target step.

## Granular Undo

The application features a robust, granular undo system that allows you to roll back the project state with precision.

-   **Undo Last Step**: The "Undo Last Step" button in the sidebar allows you to revert the project to the state it was in before the last completed step was run.
-   **Multi-Run Undo**: If a step has been run multiple times, the undo function will first revert to the state after the previous run. Subsequent undos will continue to roll back through the history of runs for that step.
-   **Conditional Undo**: The undo system is fully integrated with conditional workflows, allowing you to undo back to a decision point and make a different choice.

## Interactive Terminal

When a script is running, the application displays a live, interactive terminal that provides real-time feedback and allows you to interact with the script.

-   **Real-Time Output**: The terminal displays the script's output in real-time, so you can monitor its progress.
-   **User Input**: If a script requires user input, you can type your input directly into the terminal's input box and press "Enter" or click "Send Input."
-   **Script Termination**: A "🛑 Terminate" button is available for all running scripts, allowing you to safely stop a script at any time. When a script is terminated, the application will automatically roll back to the state it was in before the script started.

## Unified Update System

The application features a unified update system that manages both application and script updates.

-   **Automatic Update Checks**: The application automatically checks for updates every 60 minutes and on page refresh.
-   **Non-Intrusive Notifications**: When updates are available, a discreet notification will appear at the top of the main content area.
-   **Expandable Details**: You can click on the notification to expand a section with details about the available updates for both the application and the scripts.
-   **User-Controlled Updates**: All updates require explicit user approval. Application updates are downloaded manually from GitHub, while script updates can be applied with a single click from within the application.

## Fragment Analyzer (FA) Results Archiving

The workflow manager includes an intelligent archiving system for Fragment Analyzer results that preserves valuable data while maintaining workflow flexibility across both SIP and SPS-CE workflows.

-   **Automatic Archiving**: When FA analysis scripts complete successfully, they automatically move FA result directories to a permanent archive location (`archived_files/`).
-   **Multi-Workflow Support**:
    -   **SIP Workflow**: Supports first, second, and emergency third attempt archiving
    -   **SPS-CE Workflow**: Supports first and second attempt archiving
-   **Persistent Archives**: Archived FA results are excluded from the undo system, ensuring that valuable experimental data is never lost during workflow operations.
-   **Smart Directory Management**:
    -   FA result directories are moved to organized archive folders (`first_lib_attempt_fa_results/`, `second_lib_attempt_fa_results/`, `third_lib_attempt_fa_results/`)
    -   Empty parent directories are automatically cleaned up after archiving
    -   Existing archives are replaced when scripts are re-run, preventing duplicate data accumulation
-   **Undo-Safe Operation**: While the workflow can be undone to previous states, archived FA results remain safely preserved and accessible in the archive folders.
-   **Transparent Process**: The archiving process provides clear console output showing which directories are being archived and cleaned up.

### Archive Structure
```
archived_files/
├── first_lib_attempt_fa_results/
│   ├── PLATE1F 10-05-53/          # SIP or SPS-CE first attempt results
│   └── PLATE2F 12-34-56/
├── second_lib_attempt_fa_results/
│   ├── PLATE1F 14-22-11/          # SIP or SPS-CE second attempt results
│   └── PLATE2F 15-45-33/
└── third_lib_attempt_fa_results/   # SIP only - emergency third attempt
    └── PLATE1F 16-12-45/
```

### Workflow-Specific Features

#### SPS-CE Workflow
- **Steps 2 & 5**: [`SPS_first_FA_output_analysis_NEW.py`](../../templates/sps_workflow.yml) and [`SPS_second_FA_output_analysis_NEW.py`](../../templates/sps_workflow.yml)
- **Archive Integration**: Automatic archiving after successful FA analysis completion
- **Directory Structure**: `B_first_attempt_fa_result/` → `first_lib_attempt_fa_results/`, `D_second_attempt_fa_result/` → `second_lib_attempt_fa_results/`

#### SIP Workflow
- **Steps 8, 11, & 14**: First, second, and emergency third FA analysis scripts
- **Archive Integration**: Complete three-tier archiving system
- **Directory Structure**: `B_first_attempt_fa_result/` → `first_lib_attempt_fa_results/`, etc.

This feature ensures that your Fragment Analyzer data is always preserved across both SIP and SPS-CE workflows, even when using the workflow manager's powerful undo capabilities to iterate on your analysis parameters.