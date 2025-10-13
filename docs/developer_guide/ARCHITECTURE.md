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

## Containerized Development and Testing

To ensure maximum consistency and reproducibility, this application operates under a **Hybrid Docker Strategy**. All application and script execution occurs inside a standardized Docker container, never directly on the host machine.

### Core Protocol for Agents and Developers

**All execution MUST be containerized.** This is the most critical rule. Do not run Python scripts, `pytest`, or the Streamlit application directly on the host. The sole entry points for any execution are the `.command` and `.bat` scripts in the root directory.

-   **Running the Application (`run.command` / `run.bat`):** Use these scripts to start the application. They launch the Docker container and mount the local source code, enabling a live-reload development workflow. Edits made locally are instantly reflected inside the container.
-   **Running Tests (`test.command` / `test.bat`):** Use these scripts to run the `pytest` suite. They launch a **new, clean Docker container** for each test run, mount the local source code, and execute the tests. This guarantees a pristine, isolated environment that perfectly mirrors the application's runtime conditions.

This approach ensures that all development and testing activities are validated against the exact same environment, eliminating "it works on my machine" issues.
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

## Two-Repository Architecture

The system uses separate Git repositories for the application and the scientific scripts, allowing for independent updates:

-   **Main Application Repository (`sip_lims_workflow_manager`)**: Contains the GUI application, workflow engine, setup scripts, and documentation. Updates to this repository include new features, bug fixes, and UI improvements.
-   **Scripts Repository (`sip_scripts_workflow_gui`)**: Contains all the Python workflow scripts used for laboratory analysis. Updates to this repository include improvements to the scientific workflows, new analysis methods, and bug fixes in the scripts.

This separation allows for a flexible and robust update system, where critical script updates can be deployed without requiring a full application update.

## Host-Managed Script Repository

A critical architectural principle is that the host machine, not the container, is responsible for managing the `sip_scripts_workflow_gui` repository.

-   **Cloning and Updating**: The `run.command` and `run.bat` scripts are responsible for cloning the script repository on the first run and running `git pull` on every subsequent run. This ensures the scripts are always present and up-to-date on the host machine *before* the container starts.
-   **Container's Role**: The Docker container is completely unaware of Git. It receives the prepared scripts via a read-only volume mount from the host (`~/.sip_lims_workflow_manager/scripts`) to the container (`/workflow-scripts`).
-   **Rationale**: This design correctly separates concerns. The host manages the stateful, dynamic environment (the scripts), while the container provides a stateless, consistent, and isolated execution environment for the application itself. Attempting to run `git clone` from within the container leads to errors, as the container's home directory is isolated and not the intended destination for the persistent script cache.