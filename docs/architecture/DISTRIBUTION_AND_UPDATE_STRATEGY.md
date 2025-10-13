# Distribution and Update Strategy

**Last Updated:** 2025-10-10

## 1. Executive Summary

This document outlines the final, simplified architectural strategy for distributing the SIP LIMS Workflow Manager and managing updates for both the core application and its associated workflow scripts.

The chosen strategy is the **"Public Repository Model"**. This model is predicated on making the application and scripts GitHub repositories public, which radically simplifies the architecture by eliminating the need for any user-side authentication (SSH keys, OAuth tokens, etc.). It provides a seamless, zero-configuration experience for the end-user while ensuring the application and its scripts can be updated independently and reliably.

This model directly supports the previously validated **"Two-Volume Docker Architecture"** by providing a robust, authentication-free mechanism for populating the centrally-managed scripts volume.

## 2. The Core Problem: Distribution & Updates

The primary challenge was to solve two distinct but related problems:

1.  **Cross-Platform Distribution:** The initial Conda-based setup was unreliable across different user environments (macOS, Windows). Docker was chosen as the solution to provide a consistent, containerized runtime environment.
2.  **Independent Updates:** A critical requirement is that the workflow scripts must be updatable via `git` without forcing a rebuild of the main application's Docker image. This allows for rapid iteration on the scientific workflows.

This led to the "Two-Volume" Docker architecture, but left a critical question unanswered: how does the application, running on a user's machine, get permission to `clone` and `pull` the scripts from a private GitHub repository?

## 3. Architectural Evolution: From Complex to Simple

### Attempt 1: SSH Key-in-Repo (INVALID)

*   **Concept:** Package a private SSH deploy key within the application's `.ssh` directory.
*   **Analysis:** This was immediately identified as a **critical security flaw**. Bundling a private key into a distributed application is unacceptable. It was never a viable option.

### Attempt 2: GitHub App & Device Flow (REJECTED)

*   **Concept:** Use a GitHub App to perform a "Device Flow". The user would be prompted to visit a URL, enter a code, and authorize the application to access the private repository on their behalf.
*   **Analysis:** While technically secure, this approach was rejected due to poor user experience.
*   **Reason for Rejection (User Feedback):** "The users should not be going to GitHub; the users don't have access to the repo." This feedback was crucial, as it invalidated the core assumption that end-users would have or use GitHub accounts.

### Final Strategy: The Public Repository Model (ACCEPTED)

*   **Concept:** Make both the application repository (`sip_lims_workflow_manager`) and the scripts repository (`sip_scripts_workflow_gui`) public on GitHub.
*   **Analysis:** This is the optimal solution.
    *   **User Experience:** It is completely seamless. The user runs the application, and all necessary data is fetched anonymously over standard HTTPS. There is no authentication and no configuration.
    *   **Security:** It is inherently secure because we are not managing any secrets. Access is read-only and anonymous.
    *   **Robustness:** It relies on standard `git` HTTPS access, which is firewall-friendly and universally available.

## 4. Final Implementation Plan

This plan details the concrete steps required to implement the Public Repository Model in conjunction with the Two-Volume Docker Architecture.

### Step 1: Make Repositories Public

*   **Task:** The repository owner must change the visibility settings on GitHub for the following repositories to "Public":
    *   `rrmalmstrom/sip_lims_workflow_manager`
    *   `rrmalmstrom/sip_scripts_workflow_gui`
*   **Status:** Prerequisite for all following steps.

### Step 2: Implement Anonymous, Auto-Cloning Git Access

*   **File to Modify:** `src/git_update_manager.py`
*   **Task:**
    1.  **Remove all SSH Logic:** Delete the `SSHKeyManager` class and all references to it. The entire concept of using SSH is now obsolete.
    2.  **Use HTTPS URLs:** Hardcode the public HTTPS URLs for the repositories.
    3.  **Implement Auto-Clone:** Add a function that checks if the central scripts directory (`~/.sip_lims_workflow_manager/scripts`) exists. If not, it will execute `git clone <public_scripts_repo_url>`. This logic should be called on application startup.
    4.  **Simplify Update Logic:** The `update` function will simply `cd` to the scripts directory and run `git pull`.

### Step 3: Implement Application Update Notification

*   **File to Modify:** `app.py` (or a new UI/notification module).
*   **Task:**
    1.  **Bake Version into Image:** The `Dockerfile` will be modified to accept a build argument `APP_VERSION` and set it as an environment variable inside the container.
    2.  **Check for Updates:** On startup, the application will make an anonymous GET request to the GitHub API for the application repository's releases/tags (`https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager/releases/latest`).
    3.  **Notify User:** If the latest release tag is newer than the `APP_VERSION` environment variable, display a clear, non-blocking message to the user with instructions on how to `docker pull` the new image.

### Step 4: Differentiating Development vs. Production (Automated)

A critical requirement is to disable the application's self-update check during local development to prevent false notifications. This is achieved via an automated, environment-aware mechanism.

*   **Mechanism:** An interactive prompt driven by an untracked `.env` file.
    *   A file named `.env` will be created in the root of the repository for development purposes. It can be empty or contain other variables. Its presence is what matters.
    *   This file will be added to `.gitignore` and will **never** be committed.
*   **Logic:** The `run.command` and `run.bat` scripts will be modified with the following logic:
    *   **If `.env` does NOT exist (End-User Case):** The script runs Docker normally. The application defaults to `production` mode, and the update check is ON.
    *   **If `.env` EXISTS (Developer Case):** The script will display an interactive prompt asking the developer to choose between "Development" (default) and "Production" mode. Based on the choice, it will set the `APP_ENV` variable accordingly before running the `docker` command.
*   **Result:** This provides the best of both worlds. It is fully automated for the end-user, while giving the developer explicit, interactive control over the application's mode for easy testing without any file manipulation.

### Step 5: Update Run Scripts for Volume Mounts & Env-Awareness

*   **Files to Modify:** `run.command` (macOS) and `run.bat` (Windows).
*   **Task:**
    *   Add logic to detect the `.env` file and add the `--env-file .env` flag to the `docker run` command if it exists.
    *   Ensure the `docker run` command includes the two required volume mounts:
        1.  **User Project Data:** `-v "<path_to_user_project>":/app`
        2.  **Central Scripts:** `-v "$HOME/.sip_lims_workflow_manager/scripts":/workflow-scripts` (with the Windows equivalent `%USERPROFILE%\\.sip_lims_workflow_manager\\scripts`).

### Step 6: Update Core Logic to Use New Script Path

*   **File to Modify:** `src/logic.py`
*   **Task:** The `ScriptRunner` class must be modified to look for scripts in the new, static container path: `/workflow-scripts`. The current logic which constructs a path relative to the application directory must be replaced.

### Step 7: Full System Test

*   **Task:** Perform an end-to-end test covering the entire user journey:
    1.  Create the `.env` file. Run the app and confirm no update notification appears.
    2.  Temporarily rename `.env`. Run the app with an older version and confirm the update notification *does* appear.
    3.  Delete the central scripts directory (`~/.sip_lims_workflow_manager/scripts`) to simulate a first run.
    4.  Launch the application. Verify it automatically clones the scripts repo.
    5.  Run a workflow to ensure the container can access and execute a script from `/workflow-scripts`.

### Step 8: Documentation

*   **Task:** Update all user-facing documentation (`README.md`, `QUICK_SETUP_GUIDE.md`) to reflect the simplified, Docker-based setup. Update the developer guide to mention the one-time creation of the `.env` file for setting up a new development environment. This document will serve as the primary internal architectural reference.