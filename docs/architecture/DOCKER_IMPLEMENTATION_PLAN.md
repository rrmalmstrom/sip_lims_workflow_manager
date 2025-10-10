# Hybrid Docker Strategy: Implementation Plan

## 1. Objective

This document outlines the implementation plan for transitioning the SIP LIMS Workflow Manager to a "Hybrid Docker Strategy." The goal is to containerize the application environment for consistency and portability while retaining a seamless, local-like development and user experience.

This strategy will package the application and its Conda environment into a Docker image hosted on GitHub Packages. At runtime, the user's local `scripts` and `.ssh` folders, as well as the application source code, will be mounted into the container. This preserves the ability to dynamically update scripts and develop the application locally while ensuring the runtime environment is identical for all users and agents.

## 2. Core Components

### 2.1. The `Dockerfile`

A new `Dockerfile` will be created in the project root. It will define the build process for the application image.

**Build Sequence:**
1.  **Base Image:** The image will be based on `continuumio/miniconda3` to leverage the existing Conda-based environment management.
2.  **Working Directory:** A working directory `/app` will be created inside the image.
3.  **Dependency Installation (Cached Layer):**
    *   Copy the `environment.yml` file into the image.
    *   Run `conda env create -f environment.yml` to install all Conda and Pip dependencies. This creates a `sip-lims` environment inside the container. This step is intentionally performed *before* copying source code to leverage Docker's layer caching, speeding up subsequent builds.
4.  **Source Code:** Copy the application source code (e.g., `app.py`, `src/`, `templates/`) into the `/app` directory. This copy is primarily for the "production" version of the image; for development, this code will be overridden by live mounts.
5.  **Entrypoint:** The default command for the container will be configured to activate the `sip-lims` Conda environment and run the Streamlit application.

### 2.2. Image Hosting

-   The Docker image will be hosted in a **private GitHub Packages container registry** associated with the `RRMalmstrom/sip_lims_workflow_manager` repository.
-   Images will be tagged with semantic version numbers (e.g., `v1.1.0`) and a floating `latest` tag for easy access.

### 2.3. User-Facing Scripts

The existing `.command` (macOS) and `.bat` (Windows) scripts will be modified to be the sole entry points for interacting with the application. This provides a user-friendly abstraction over Docker commands.

-   **`run.command` / `run.bat`:**
    *   **Function:** Starts the application for regular use or development.
    *   **Action:** Will execute a `docker run` command that:
        *   Pulls the `latest` image if not present locally.
        *   Maps port `8501` from the container to the host (`-p 8501:8501`).
        *   **Mounts** the local source code (`app.py`, `src`, `templates`, `utils`) into the container's `/app` directory.
        *   **Mounts** the local `scripts` folder into the container.
        *   **Mounts** the local `.ssh` folder into the container's `/root/.ssh` directory to preserve Git functionality.
        *   Removes the container on exit (`--rm`).

-   **`test.command` / `test.bat`:**
    *   **Function:** Runs the `pytest` test suite for TDD.
    *   **Action:** Will execute a `docker run` command that is nearly identical to the `run` script, but with the final command overridden to be `pytest`. This ensures tests run against the exact same containerized environment.

-   **`update.command` / `update.bat`:**
    *   **Function:** Allows users to update the application to the latest version.
    *   **Action:** Will execute a `docker pull` command to fetch the `latest` image from the GitHub Packages registry.

-   **`setup.command` / `setup.bat`:**
    *   **Function:** The one-time setup for a new user.
    *   **Action:** Will be modified to check for Docker Desktop installation. It will no longer create a local Conda environment. Its primary role will be to ensure the user is logged into the GitHub container registry (`ghcr.io`) so they can pull the private image.

## 3. User & Developer Workflow

### 3.1. First-Time Setup
1.  User installs Docker Desktop.
2.  User runs the `setup` script, which guides them to log into GitHub's container registry via the command line.
3.  The script performs an initial `docker pull` to download the application image.

### 3.2. Running the Application
1.  User double-clicks `run.command` or `run.bat`.
2.  The script starts the Docker container, which launches the Streamlit app.
3.  The app opens in the user's browser, served from the container.

### 3.3. Developing & Testing (TDD)
1.  The developer starts the application once by running `run.command`.
2.  The developer edits any source code file (`.py`, `.yml`, etc.) on their local machine using VS Code.
3.  Streamlit, running inside the container, detects the file change via the mounted volume and automatically reloads.
4.  To run tests, the developer executes `test.command` or `test.bat`. `pytest` runs inside a new, clean container against the latest local code.

### 3.4. Updating the Application
1.  The app UI notifies the user an update is available.
2.  The user runs `update.command` or `update.bat`.
3.  Docker pulls the new `latest` image.
4.  The user runs `run.command` as usual, which now starts the new version.

## 4. Guardrails and Compliance

To ensure this new workflow is always followed by all users and agents:
-   The `run`, `test`, and `update` scripts will be the **only** supported methods for interacting with the application.
-   The `README.md` and `QUICK_SETUP_GUIDE.md` will be updated to reflect this Docker-centric workflow, removing instructions related to local Conda environment setup for running the app.
-   This `DOCKER_IMPLEMENTATION_PLAN.md` document will serve as the canonical source of truth for the architecture.