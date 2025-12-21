# Troubleshooting Guide

This guide provides solutions to common issues you may encounter while using the SIP LIMS Workflow Manager.

## Installation and Setup Issues

### `conda: command not found`

-   **Cause**: This error means that Miniconda or Anaconda is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
    1.  Reinstall Miniconda, carefully following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
    2.  On Windows, ensure you check the box for **"Add Miniconda3 to my PATH environment variable"** during installation.
    3.  After installation, restart your computer (Windows) or close and reopen your terminal (macOS) for the changes to take effect.

### Setup Script Fails

-   **Cause**: The setup script (`setup.command` or `setup.bat`) can fail for several reasons, including network issues or a pre-existing, corrupted Conda environment.
-   **Solution**:
    1.  Try running the setup script again.
    2.  If the script fails because the `sip-lims` environment already exists, you can manually remove it. Open a terminal (or Anaconda Prompt on Windows) and run the following command:
        ```bash
        conda env remove --name sip-lims
        ```
    3.  After the environment is removed, run the setup script again.

### Application Won't Start

-   **Cause**: The application's environment may be out of date or corrupted.
-   **Solution**: Run the `setup.command` or `setup.bat` script again. It is safe to run the setup script multiple times and will ensure your environment is properly configured.

### Docker Update Issues

-   **Cause**: Docker image updates may fail due to network issues, Docker Desktop not running, or insufficient disk space.
-   **Solution**:
    1.  **Check Docker Desktop**: Ensure Docker Desktop is running
    2.  **Check internet connection**: Updates require downloading from GitHub Container Registry
    3.  **Clear Docker cache**: Run `docker system prune -f` to clean up old images
    4.  **Check disk space**: Ensure sufficient disk space for Docker images (3+ GB)
    5.  **Restart Docker**: Restart Docker Desktop if updates consistently fail

### Script Update Issues

-   **Cause**: Python script updates may fail due to network issues or git repository problems.
-   **Solution**:
    1.  **Check internet connection**: Updates require downloading from GitHub
    2.  **Clear scripts directory**: Delete `~/.sip_lims_workflow_manager/scripts` to force fresh download
    3.  **Check permissions**: Ensure write access to `~/.sip_lims_workflow_manager/` directory
    4.  **Use developer mode**: If updates fail, try running in developer mode with local scripts

### Developer Mode Issues

-   **Cause**: Developer mode script path selection may fail if paths are invalid.
-   **Solution**:
    1.  **Verify script path**: Ensure the drag-and-dropped folder contains Python (.py) files
    2.  **Check permissions**: Ensure read access to the script directory
    3.  **Use absolute paths**: Avoid relative paths that may not resolve correctly
    4.  **Fallback to production**: If local scripts fail, choose production mode instead

## Project Loading Issues

### Inconsistent State Detected

-   **Cause**: The application has detected a mismatch between the `workflow_state.json` file and the files in your project folder. This typically happens if database files (`.db`) have been manually deleted or moved after steps were marked as completed.
-   **Solution**:
    1.  Do not proceed with loading the project, as this can lead to data corruption.
    2.  Manually restore the missing `.db` files to the project folder from a backup or by rerunning the necessary steps outside of the workflow manager.
    3.  Once the files are restored, try loading the project again.

### Missing `workflow.yml` or `workflow_state.json`

-   **Cause**: The application cannot find the necessary workflow configuration files in the selected project folder.
-   **Solution**: The application will guide you through the process of restoring these files.
    1.  **Try to Restore from Snapshots**: The application will first offer to restore the missing files from the most recent project snapshot. This is the safest option and should be tried first.
    2.  **Set Up Project**: If restoration from snapshots fails, you can choose to set up the project. This will create a new `workflow.yml` from the application's template and allow you to use the "Skip to Step" feature to bring the workflow state in line with your existing work.

## Update Issues

### Update Check Fails

-   **Cause**: The application cannot connect to GitHub to check for updates. This is usually due to network issues.
-   **Solution**:
    1.  Ensure you have a stable internet connection.
    2.  You can force a new update check by clicking the "🔄 Manual Check for Updates" button in the sidebar.

### Script Update Fails

-   **Cause**: The application was unable to pull the latest scripts from the Git repository, likely due to a network issue.
-   **Solution**: Ensure you have a stable internet connection and try the update again.