# Plan: Docker-Based Distribution Strategy

This document outlines the technical plan to package the SIP LIMS Workflow Manager into a Docker container for robust, cross-platform distribution.

## 1. Core Principles

-   **Environment Consistency:** The application and all its dependencies will run inside a single, controlled Docker container, eliminating platform-specific issues.
-   **Dynamic Project Mounting:** The user will select their project folder on their local machine *before* the application starts. This folder will be mounted as a volume into the container.
-   **Simplified User Interaction:** The initial project selection will be handled by a native OS dialog, and all subsequent file operations will occur safely within the mounted project folder.

## 2. Implementation Steps

This plan involves changes to four key areas: the `Dockerfile`, the run scripts, the application code, and the user documentation.

### Step 1: `Dockerfile` Enhancement

The `Dockerfile` will be updated to create a self-contained environment for the application.

-   **Base Image:** Continue using `continuumio/miniconda3` for Conda support.
-   **Dependencies:** Copy `environment.yml` and run `conda env create` to install all Python and system dependencies.
-   **Application Code:** Copy the entire `src` directory into the container at `/app/src`.
-   **Working Directory:** Set the default working directory to a neutral location like `/app`. The actual project directory will be mounted over this at runtime.
-   **Entrypoint:** Define an `entrypoint.sh` script that activates the Conda environment and executes the Streamlit application. This ensures the environment is correctly configured on container start.
-   **Port Exposure:** Expose port `8501` for the Streamlit application.

### Step 2: Dynamic Run Scripts (`run.command` & `run.bat`)

These scripts are the primary user entrypoint and will be responsible for dynamically mounting the project folder.

-   **`run.command` (macOS):**
    1.  Use an AppleScript command (`osascript`) to display a native "Choose Folder" dialog.
    2.  Capture the selected folder path.
    3.  Execute a `docker run` command, using the `-v` flag to mount the selected path to `/app/project` and the `-w` flag to set `/app/project` as the working directory.
-   **`run.bat` (Windows):**
    1.  Use a PowerShell script snippet to display a native "Browse For Folder" dialog.
    2.  Capture the selected folder path.
    3.  Execute a `docker run` command with the same `-v` and `-w` flags, ensuring correct path syntax for Windows.

### Step 3: Application Refactoring (`app.py`)

The main application file will be simplified to remove the initial project selection logic.

1.  **Remove Initial File Browser:** Delete the UI elements and associated logic (e.g., calls to `file_browser_agent`) that ask the user to select a project folder at the start.
2.  **Assume Project Context:** Modify the application to assume that its current working directory *is* the project directory. The `Project` class should be initialized with the current directory (`.`) as its path.
3.  **Preserve In-Workflow Browsing:** The file browsing functionality used *within* workflow steps will remain. It will now be naturally "jailed" to the mounted project directory, improving safety and usability.

### Step 4: Documentation Update (`QUICK_SETUP_GUIDE.md`)

The user guide must be updated to reflect the new workflow.

1.  **Docker as Prerequisite:** Clearly state that Docker Desktop is the only required dependency.
2.  **New Setup Process:** Detail the one-time `setup_docker` script.
3.  **New Run Process:** Explain the new application launch process:
    -   User double-clicks `run.command` or `run.bat`.
    -   A folder selection dialog appears.
    -   User selects their project folder.
    -   The application opens in their web browser.

## 3. Mermaid Diagram: New Workflow

```mermaid
sequenceDiagram
    participant User
    participant Run Script
    participant Docker
    participant App

    User->>Run Script: Double-clicks run.command/run.bat
    Run Script->>User: Shows native "Choose Folder" dialog
    User->>Run Script: Selects Project Folder
    Run Script->>Docker: Executes `docker run` with volume mount
    Docker->>App: Starts Streamlit App
    App->>User: Displays GUI in browser