# Unified Update System

This document describes the implementation and architecture of the unified, Git-based update system for the SIP LIMS Workflow Manager. This system manages both application and script updates through a consistent, secure, and user-friendly interface.

## Architecture

The unified update system replaces the previous dual-architecture approach (Google Drive for application updates, separate SSH for script updates) with a single, consistent Git-based model for both.

-   **Git-Based Updates**: Both the application and the scientific scripts are updated via Git, using Git tags for versioning.
-   **Unified Interface**: A single, non-intrusive notification system in the UI informs users of available updates for both the application and scripts.
-   **Consistent Authentication**: A single SSH deploy key is used for authentication with both the application and script repositories on GitHub.

### Core Components

-   **`GitUpdateManager` (`src/git_update_manager.py`)**: A unified class for managing updates for both the application and script repositories. It handles version checking, comparison, and updating.
-   **`SSHKeyManager` (`src/ssh_key_manager.py`)**: A security-focused class that manages the validation and use of SSH keys for secure repository access.
-   **Clean UI Integration (`app.py`)**: The Streamlit application features a smart notification system that only displays update information when updates are available, ensuring a clean and uncluttered user interface.

## Version Management

-   **Git Tag Versioning**: Both the application and script repositories use semantic versioning with Git tags (e.g., `v1.0.2`, `v1.1.0`).
-   **Version Detection**: The `GitUpdateManager` determines the latest version by:
    1.  **GitHub API**: The primary method is to query the GitHub API for the latest release.
    2.  **SSH Git Fallback**: If the GitHub API call fails (e.g., for private repositories or due to network issues), the system falls back to using Git to fetch the latest tags directly from the repository via SSH.

## User Interface

The update system is designed to be non-intrusive and user-friendly.

-   **Automatic Detection**: The application automatically checks for updates every 60 minutes and on page refresh.
-   **Smart Notifications**: A discreet "🔔 Updates Available" banner appears at the top of the main content area only when updates are found.
-   **Expandable Details**: Users can click on the notification to expand a section with a side-by-side view of available updates for the application and scripts.
-   **User Control**: All updates require explicit user approval.
    -   **Application Updates**: Are downloaded manually from the GitHub releases page. This requires a manual restart of the application.
    -   **Script Updates**: Can be applied with a single click from within the application and do not require a restart.

## Security

-   **SSH Deploy Keys**: The system uses read-only SSH deploy keys for secure access to the Git repositories.
-   **Key Validation**: The `SSHKeyManager` automatically validates SSH key security, including file permissions (must be `600`) and key type.
-   **HTTPS and SSH**: All communication with GitHub is encrypted, either via HTTPS for API calls or SSH for Git operations.

This unified, Git-based approach provides a more secure, reliable, and user-friendly update experience while simplifying the maintenance and deployment process.