# System Architecture

This document provides a high-level overview of the architecture, design principles, and technology stack for the SIP LIMS Workflow Manager.

## Guiding Principles

-   **Simplicity Over Complexity**: Prioritize the simplest possible solution that meets the requirements. Avoid adding features or layers of abstraction that are not immediately necessary.
-   **User-Centric Design**: The tool is designed for lab technicians and must be intuitive, forgiving, and easy to use.
-   **Robustness**: The system is designed to be resilient to script errors and to prevent data corruption through a robust snapshot and rollback system.
-   **Flexibility**: The design accommodates the non-linear nature of lab work, allowing for features like "skip to step," conditional workflows, and granular undo.
-   **Native Performance**: Direct Python execution eliminates container overhead for optimal performance and debugging capabilities.

## Technology Stack

-   **GUI**: Streamlit
-   **Backend & Core Logic**: Python 3.10+
-   **Environment Management**: Conda with exact version lock files
-   **Package Management**: Conda + Pip with deterministic lock files
-   **Configuration**: YAML (workflow templates: [`sip_workflow.yml`](../../templates/sip_workflow.yml), [`sps_workflow.yml`](../../templates/sps_workflow.yml))
-   **State Management**: JSON (`workflow_state.json`)
-   **Version Control**: Git-based repository and script management
-   **Native Launcher**: [`launcher/run.py`](../../launcher/run.py) - Native Mac Python launcher

## Native Execution Architecture

The application uses a **native Python execution model** to ensure optimal performance and simplified deployment:

### Key Components:
-   **Native Python Launcher**: [`run.py`](../../run.py) - Direct Python execution without container overhead
-   **Conda Environment**: Deterministic package management with exact version lock files
-   **Lock Files**:
    -   `conda-lock.txt`: Exact conda package versions with build hashes
    -   `requirements-lock.txt`: Exact pip package versions
-   **Git-Based Updates**: Repository and script updates via Git operations
-   **Native Mac Support**: Optimized execution for macOS systems

### Benefits:
-   **Performance**: 83% startup time reduction (30s → 5s)
-   **Simplified Deployment**: No container runtime required
-   **Native Debugging**: Standard Python debugging tools work directly
-   **Resource Efficiency**: Lower memory and CPU usage
-   **Direct File Access**: No volume mounting or file system translation
-   **Scientific Reproducibility**: Deterministic environments via lock files

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
-   **`ScriptRunner`**: Responsible for executing the individual Python workflow scripts in a native subprocess, allowing for real-time, interactive execution.

## Native Python Architecture

The system uses a native Python execution model for optimal performance and simplified deployment.

### Execution Environment:
-   **Native Python Process**: Direct subprocess execution without container overhead
-   **Conda Environment**: Isolated package environment with deterministic dependencies
-   **Process Management**: Native process control with proper signal handling
-   **File System Access**: Direct file system operations without volume mounting

### Script Management:
-   **Production Scripts**: Automatically downloaded to `~/.sip_lims_workflow_manager/scripts`
-   **Development Scripts**: Local scripts via direct file system access
-   **Version Control**: Scripts are independently versioned and updated via Git
-   **Native Path Resolution**: Optimized path handling for macOS systems

## Execution Modes: Production vs. Developer

The application operates in one of two modes, determined by the presence of a marker file.

### Production Mode (Default)
-   **Native Execution**: Direct Python execution with conda environment
-   **Script Management**: Automatically downloads and updates scripts from GitHub
-   **Environment**: Completely automated, no user intervention required
-   **Updates**: Scripts are automatically updated via Git operations

### Developer Mode
Activated by the presence of a `config/developer.marker` file:

-   **Local Development**: Uses local conda environment for development
-   **Script Choice**: Interactive prompts to choose between:
    -   **Production Mode**: Uses centralized scripts with auto-updates
    -   **Development Mode**: Uses local scripts with direct file system access
-   **Flexibility**: Allows testing with local script modifications
-   **Native Debugging**: Full access to Python debugging tools

### Environment Management:
-   **Conda Integration**: Seamless integration with conda package management
-   **Lock File Validation**: Ensures consistent package versions across deployments
-   **Native Mac Support**: Optimized for macOS host operating system
-   **Performance Optimization**: Native execution eliminates container startup overhead

## Development Workflow

The project includes tools for managing the deterministic conda environment:

### Core Management:
-   **Lock Files**: `conda-lock.txt` and `requirements-lock.txt` ensure reproducible environments
-   **Environment Validation**: Automated checks for package consistency
-   **Git Integration**: Version control for both code and environment specifications
-   **Native Mac Testing**: Validation on macOS systems

### Development Workflow:
1. **Development**: Modify dependencies in environment files
2. **Lock Generation**: Generate new lock files for reproducibility
3. **Validation**: Ensure environment integrity and package compatibility
4. **Testing**: Local testing with native Python execution
5. **Deployment**: Git-based deployment with automatic script updates

### Testing Infrastructure:
-   **TDD Test Suite**: Comprehensive tests for all workflow components
-   **Integration Tests**: End-to-end validation of native execution
-   **Native Mac Tests**: Validation on macOS systems

## Workflow-Aware Architecture

### Environment Variable Propagation

The system uses the `WORKFLOW_TYPE` environment variable to determine which workflow to load:

```
User Selection → Native Python Launcher → Application Logic
```

**Flow:**
1. **Native Python Launcher** ([`run.py`](../../run.py)): Interactive workflow selection and environment setup
2. **Application Logic** ([`app.py`](../../app.py)): Reads `WORKFLOW_TYPE` for template selection
3. **Repository Management** ([`src/scripts_updater.py`](../../src/scripts_updater.py)): Uses `WORKFLOW_TYPE` for script repository selection

### Native Python Launcher Features

The [`launcher/run.py`](../../launcher/run.py) script provides:
- **Native Mac Compatibility**: Optimized script for macOS systems
- **Interactive Workflow Selection**: Rich CLI interface with colored output
- **Command-Line Arguments**: Support for automation and scripting
- **Enhanced Error Handling**: Graceful error messages and recovery
- **Platform Detection**: Automatic adaptation to host operating system
- **Native Process Management**: Direct subprocess control and signal handling
- **Performance Optimization**: Fast startup and efficient resource usage

### Template System

**Template Selection Logic:**
- `WORKFLOW_TYPE=sip` → [`templates/sip_workflow.yml`](../../templates/sip_workflow.yml)
- `WORKFLOW_TYPE=sps-ce` → [`templates/sps_workflow.yml`](../../templates/sps_workflow.yml)
- **Fallback**: Defaults to SIP workflow for invalid or missing workflow types

**Template Structure:**
Both templates follow the same YAML structure but contain different workflow steps appropriate for their respective laboratory processes.

### Repository Management

**Workflow-Specific Repositories:**
- **SIP**: `sip_scripts_workflow_gui` (existing repository)
- **SPS-CE**: `SPS_library_creation_scripts` (enhanced with success markers)

**Script Paths:**
- **SIP**: `~/.sip_lims_workflow_manager/sip_scripts`
- **SPS-CE**: `~/.sip_lims_workflow_manager/sps-ce_scripts`

### Success Marker Integration

All workflow scripts create success markers in `.workflow_status/{script_name}.success` for workflow manager integration:

**SIP Scripts**: Already had success markers
**SPS-CE Scripts**: Enhanced with robust success marker pattern:
- `SPS_make_illumina_index_and_FA_files_NEW.py`
- `SPS_first_FA_output_analysis_NEW.py`
- `SPS_rework_first_attempt_NEW.py`
- `SPS_second_FA_output_analysis_NEW.py`
- `SPS_conclude_FA_analysis_generate_ESP_smear_file.py`
- `decision_second_attempt.py` (new decision script)

## Enhanced Reliability Features

### Race Condition Protection
The system includes comprehensive protection against race conditions, especially important for external drive operations:

-   **Atomic File Operations**: Write-then-rename pattern ensures data integrity
-   **Retry Logic**: Exponential backoff for handling temporary file system issues
-   **External Drive Optimization**: Special handling for network drives and external storage
-   **Enhanced Logging**: Comprehensive debug output in `debug_output/` directory

### Session Persistence
-   **State Management**: Workflow state persists across application restarts
-   **Project Memory**: Automatic restoration of project settings and progress
-   **Crash Recovery**: Robust recovery from unexpected application termination

### Performance Optimization
-   **Native Execution**: Direct Python execution eliminates container overhead
-   **Efficient File I/O**: Optimized file operations for large datasets
-   **Memory Management**: Improved memory usage for long-running workflows
-   **External Drive Performance**: Optimized for laboratory environments with network storage

This native Python architecture ensures optimal performance, simplified deployment, and enhanced reliability while maintaining the scientific reproducibility and robustness required for laboratory environments.