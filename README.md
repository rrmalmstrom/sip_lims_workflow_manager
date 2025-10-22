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
-   Support for macOS.

## Prerequisites

-   **Miniconda or Anaconda**: This application uses the Conda package manager to ensure a consistent and reproducible environment. Please see the **[Quick Setup Guide](docs/user_guide/QUICK_SETUP_GUIDE.md)** for installation instructions.

## Repository Structure

This project uses a decoupled, two-repository structure to separate the core application from the scientific scripts:

-   `sip_lims_workflow_manager/` (This repository): Contains the core application, GUI, and documentation.
-   `sip_scripts_prod/` or `sip_scripts_dev/`: Sibling directories containing the Python workflow scripts.
    -   `sip_scripts_prod/`: For production users, containing stable, version-controlled scripts.
    -   `sip_scripts_dev/`: For developers, containing local, mutable scripts for testing and development.

This structure allows the application and scripts to be updated independently, providing greater stability for production users and flexibility for developers.

## Installation and Setup

The setup process is performed only **once** per computer. For detailed instructions, see the **[Quick Setup Guide](docs/user_guide/QUICK_SETUP_GUIDE.md)**.

1.  **Download the Application**: Download and unzip the `sip_lims_workflow_manager` repository.
2.  **Run the Setup Script**: Double-click `setup.command`.

The setup script automatically detects the mode:
-   **Production Mode (Default)**: Clones or updates the production scripts into a sibling directory named `../sip_scripts_prod`.
-   **Developer Mode**: If a `config/developer.marker` file is present, the script provides interactive prompts for developers, including options for offline work and guidance on setting up a local `../sip_scripts_dev` repository.

## Running the Application

-   Double-click `run.command`.

The `run.command` script also adapts to the execution mode:
-   **Production Mode**: Automatically uses the scripts from `../sip_scripts_prod`.
-   **Developer Mode**: Prompts the developer to choose between using the development (`../sip_scripts_dev`) or production (`../sip_scripts_prod`) scripts for the session.

The application will open in your default web browser at `http://127.0.0.1:8501`.