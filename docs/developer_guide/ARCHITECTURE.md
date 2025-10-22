# System Architecture

This document provides a high-level overview of the architecture, design principles, and technology stack for the SIP LIMS Workflow Manager.

## Guiding Principles

-   **Simplicity Over Complexity**: Prioritize the simplest possible solution that meets the requirements. Avoid adding features or layers of abstraction that are not immediately necessary.
-   **User-Centric Design**: The tool is designed for lab technicians and must be intuitive, forgiving, and easy to use.
-   **Robustness**: The system is designed to be resilient to script errors and to prevent data corruption through a robust snapshot and rollback system.
-   **Flexibility**: The design accommodates the non-linear nature of lab work, allowing for features like "skip to step," conditional workflows, and granular undo.

## Technology Stack

-   **GUI**: Streamlit
-   **Backend & Core Logic**: Python 3
-   **Environment Management**: Conda
-   **Configuration**: YAML (`workflow.yml`)
-   **State Management**: JSON (`workflow_state.json`)

## On-Disk Structure (Per Project)

Each project is a self-contained folder with the following structure:

```
project_folder/
├── workflow.yml
├── workflow_state.json
├── .snapshots/
├── .workflow_status/
└── .workflow_logs/
```

-   `workflow.yml`: The blueprint for the workflow, defining all steps, their properties, and any conditional logic.
-   `workflow_state.json`: Tracks the status of each step (e.g., "pending," "completed," "skipped").
-   `.snapshots/`: A hidden directory containing complete project snapshots taken before each step is run. This enables the robust undo and rollback functionality.
-   `.workflow_status/`: A hidden directory containing success marker files. A file is created in this directory only when a script completes successfully, providing a secondary verification mechanism for script success.
-   `.workflow_logs/`: A hidden directory for storing debug logs, which can be useful for troubleshooting.

## Core Logic Classes

The backend is composed of several key classes that work together to manage the workflow:

-   **`Project`**: The main coordinating class. It represents a user's project folder and orchestrates the other components.
-   **`Workflow`**: Parses and represents the `workflow.yml` file.
-   **`StateManager`**: Handles all reading and writing to the `workflow_state.json` file.
-   **`SnapshotManager`**: Manages the creation and restoration of complete project snapshots in the `.snapshots` directory.
-   **`ScriptRunner`**: Responsible for executing the individual Python workflow scripts in a pseudo-terminal, allowing for real-time, interactive execution.

## Decoupled Repository Architecture

The system uses a decoupled architecture to separate the core application from the scientific scripts, allowing for independent management and versioning. The application and scripts are stored in **sibling directories**.

-   **`sip_lims_workflow_manager/`**: The main application repository. It contains the GUI, workflow engine, setup scripts, and documentation. It is agnostic to the script location.
-   **`sip_scripts_prod/`**: A sibling directory containing the stable, version-controlled production scripts. This repository is automatically cloned and managed by the `setup.command` script for standard users.
-   **`sip_scripts_dev/`**: An optional, local-only sibling directory for developers. It is not managed by Git, allowing developers to maintain a local, mutable set of scripts for testing and development.

This structure provides stability for production users while offering flexibility for developers. The path to the active script repository is passed to the Python application at runtime via the `--script-path` command-line argument.

## Execution Modes: Production vs. Developer

The application operates in one of two modes, determined by the presence of a marker file.

-   **Production Mode (Default)**: The standard mode for end-users. The application automatically uses the scripts located in the `../sip_scripts_prod` directory.
-   **Developer Mode**: Activated by the presence of a `config/developer.marker` file. In this mode, the `setup.command` and `run.command` scripts become interactive:
    -   `setup.command` offers options for online/offline work.
    -   `run.command` prompts the developer to choose between using the `../sip_scripts_dev` or `../sip_scripts_prod` directory for the current session.

This dual-mode system ensures a standardized, stable environment for production use while providing a flexible and controlled workflow for development and testing.