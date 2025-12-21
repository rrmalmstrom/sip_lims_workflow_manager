# SIP LIMS Workflow Manager
# Test comment for Docker update testing

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
-   Support for macOS.

## Prerequisites

-   **Miniconda or Anaconda**: This application uses the Conda package manager to ensure a consistent and reproducible environment. Please see the **[Quick Setup Guide](docs/user_guide/QUICK_SETUP_GUIDE.md)** for installation instructions.

## Repository Structure

This project uses an intelligent update system that automatically manages both the application and Python scripts:

-   `sip_lims_workflow_manager/` (This repository): Contains the core application, GUI, and documentation.
-   **Production Scripts**: Automatically downloaded and updated to `~/.sip_lims_workflow_manager/scripts` from GitHub.
-   **Developer Scripts**: Optional local development scripts for testing and development.

This structure provides automatic updates for production users while maintaining flexibility for developers.

## Installation and Setup

The setup process is performed only **once** per computer. For detailed instructions, see the **[Quick Setup Guide](docs/user_guide/QUICK_SETUP_GUIDE.md)**.

1.  **Download the Application**: Download and unzip the `sip_lims_workflow_manager` repository.
2.  **Run the Setup Script**: Double-click `setup.command`.

## Running the Application

-   Double-click `run.command`.

The `run.command` script provides intelligent workflow management:

### For Production Users:
-   **Automatic Updates**: Silently checks and downloads latest Docker images and Python scripts from GitHub
-   **No User Prompts**: Completely automated experience
-   **Centralized Management**: Scripts stored in `~/.sip_lims_workflow_manager/scripts`

### For Developers:
-   **Mode Detection**: Automatically detects `config/developer.marker` file
-   **Workflow Choice**: Choose between:
    - **Production Mode**: Same auto-update behavior as regular users
    - **Development Mode**: Use local development scripts with no auto-updates
-   **Flexible Script Paths**: Drag-and-drop selection of local script directories

The application will open in your default web browser at `http://127.0.0.1:8501`.