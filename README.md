# SIP LIMS Workflow Manager

A simple, lightweight workflow manager for running a series of Python scripts in a SIP (Stable Isotope Probing) laboratory environment.

## 📖 Documentation

For complete and detailed documentation, please see the **[main documentation page](docs/index.md)**.

This includes:
- **[User Guide](docs/user_guide)**: For installation, setup, and usage instructions.
- **[Developer Guide](docs/developer_guide)**: For technical details on implementation and contribution guidelines.
- **[Architecture Overview](docs/architecture)**: For high-level design and strategy documents.

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
-   Interactive script support with real-time terminal output and responsive single-click interaction.
-   **Enhanced pseudo-terminal buffering** - real-time output updates with optimized polling for immediate script prompt visibility.
-   **Script termination capability** with automatic rollback to pre-execution state.
-   **Application shutdown button** - cleanly terminate the application from within the GUI.
-   **Safe uninstall system** - complete removal of application while preserving user data.
-   **Localhost-only security** - application is only accessible from your computer, not from the network.
-   Cross-platform support for macOS and Windows.

## Prerequisites

-   **Docker Desktop**: The application runs in a container to ensure consistency.
-   **Git**: Used to automatically download and update the scientific workflow scripts.

## Installation and First-Time Setup

The setup process needs to be performed only **once** per computer.

1.  **Download the Application**: Download the `sip_lims_workflow_manager` folder (as a `.zip` file) from the latest GitHub release and unzip it to a permanent location on your computer (e.g., your Desktop or Documents folder).
2.  **Run the Setup Script**: This script builds the application's Docker image on your computer.
    -   **On macOS**: Open the `sip_lims_workflow_manager` folder and double-click the `setup_docker.command` file.
    -   **On Windows**: Open the `sip_lims_workflow_manager` folder and double-click the `setup_docker.bat` file.

## Running the Application

After the one-time setup is complete, you can start the application at any time:

-   **On macOS**: Double-click the `run.command` file.
-   **On Windows**: Double-click the `run.bat` file.

The first time you run the application, it will automatically download the necessary scientific workflow scripts. On subsequent runs, it will check for and apply any available script updates. A terminal window will open, and the application's user interface will open in your default web browser.