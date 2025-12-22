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
-   **Environment Management**: Docker with Deterministic Builds
-   **Package Management**: Conda + Pip with exact version lock files
-   **Configuration**: YAML (`workflow.yml`)
-   **State Management**: JSON (`workflow_state.json`)
-   **Container Registry**: GitHub Container Registry (ghcr.io)
-   **CI/CD**: GitHub Actions with deterministic Docker builds

## Deterministic Build System

The application uses a **deterministic Docker build strategy** to ensure 100% reproducible environments:

### Key Components:
-   **Pinned Base Image**: `continuumio/miniconda3@sha256:...` (exact SHA, not floating tags)
-   **Exact Package Lock Files**:
    -   `conda-lock.txt`: Exact conda package versions with build hashes
    -   `requirements-lock.txt`: Exact pip package versions
-   **Docker-Only Workflow**: No local Conda installation required for end users
-   **Automatic Updates**: Docker images and scripts updated automatically via [`run.command`](../../run.command)
-   **Pinned System Dependencies**: All system packages use exact version numbers
-   **Reproducible Builds**: Same exact environment every time, regardless of when/where built

### Benefits:
-   **Scientific Reproducibility**: Ensures consistent results across all deployments
-   **Compatibility Fix**: Resolves SQLAlchemy/SQLite library compatibility issues
-   **Cross-Platform Consistency**: Same environment on all Docker-supported platforms
-   **Version Control**: Lock files are committed to git for full traceability

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

## Docker-Based Architecture

The system uses a Docker-based architecture to ensure consistent, reproducible environments across all platforms.

### Container Structure:
-   **Application Container**: Contains the GUI, workflow engine, and all dependencies
-   **Volume Mounts**: Project data and scripts are mounted from the host system
-   **User ID Mapping**: Proper file permissions for shared network drives
-   **Network Isolation**: Application only accessible from localhost (127.0.0.1:8501)

### Script Management:
-   **Production Scripts**: Automatically downloaded to `~/.sip_lims_workflow_manager/scripts`
-   **Development Scripts**: Local scripts mounted via drag-and-drop selection
-   **Version Control**: Scripts are independently versioned and updated

## Execution Modes: Production vs. Developer

The application operates in one of two modes, determined by the presence of a marker file.

### Production Mode (Default)
-   **Docker Image**: Uses pre-built deterministic images from GitHub Container Registry
-   **Script Management**: Automatically downloads and updates scripts from GitHub
-   **Environment**: Completely automated, no user intervention required
-   **Updates**: Both Docker images and scripts are automatically updated

### Developer Mode
Activated by the presence of a `config/developer.marker` file:

-   **Docker Build**: Can use either pre-built images or local deterministic builds
-   **Script Choice**: Interactive prompts to choose between:
    -   **Production Mode**: Uses centralized scripts with auto-updates
    -   **Development Mode**: Uses local scripts with drag-and-drop selection
-   **Flexibility**: Allows testing with local script modifications
-   **Isolation**: Docker ensures no interference with host system

### Docker Image Management:
-   **Automatic Cleanup**: Old containers and images are automatically removed
-   **Update Detection**: Intelligent update system checks for new deterministic images
-   **Build Caching**: Docker layer caching optimizes build times
-   **Multi-Platform**: Supports both Intel and ARM architectures

## Development Workflow Scripts

The project includes specialized scripts for managing the deterministic Docker build workflow:

### Core Build Scripts:
-   **`generate_lock_files.sh`**: Creates deterministic lock files from `environment.yml`
-   **`validate_lock_files.sh`**: Validates integrity of existing lock files
-   **`build_image_from_lock_files.sh`**: Builds Docker image using existing lock files
-   **`push_image_to_github.sh`**: Pushes built image to GitHub Container Registry

### Development Workflow:
1. **Development**: Modify dependencies in `environment.yml`
2. **Lock Generation**: Run `generate_lock_files.sh` to create new lock files
3. **Validation**: Run `validate_lock_files.sh` to ensure integrity
4. **Local Build**: Run `build_image_from_lock_files.sh` for testing
5. **Deployment**: Run `push_image_to_github.sh` to publish to registry

### Testing Infrastructure:
-   **TDD Test Suite**: Comprehensive tests for all workflow scripts
-   **Integration Tests**: End-to-end validation of build and push processes
-   **Remote Validation**: Tests for GitHub Container Registry functionality

For detailed workflow instructions, see [`DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md`](../Docker_docs/DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md).

For technical details about the Docker Compose configuration, see [`DOCKER_COMPOSE_CONFIGURATION.md`](../Docker_docs/DOCKER_COMPOSE_CONFIGURATION.md).

This Docker-based system ensures a standardized, reproducible environment for production use while providing complete flexibility for development and testing.