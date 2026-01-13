# Troubleshooting Guide

This guide provides solutions to common issues you may encounter while using the SIP LIMS Workflow Manager.

## Installation and Setup Issues

### `docker: command not found`

-   **Cause**: This error means that Docker Desktop is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
    1.  Reinstall Docker Desktop, carefully following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
    2.  On Windows, ensure Docker Desktop is properly installed and restart your computer.
    3.  After installation, restart your computer (Windows) or close and reopen your terminal (macOS) for the changes to take effect.

### `git: command not found`

-   **Cause**: This error means that Git is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
    1.  Install Git following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
    2.  On Windows, ensure you selected "Git from the command line and also from 3rd-party software" during installation.
    3.  After installation, restart your terminal for the changes to take effect.

### `python3: command not found`

-   **Cause**: This error means that Python 3.10+ is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
    1.  Install Python 3.10+ following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
    2.  On Windows, ensure you checked "Add python.exe to PATH" during installation.
    3.  After installation, restart your terminal for the changes to take effect.

### Application Won't Start

-   **Cause**: Docker Desktop may not be running, or there may be issues with the Docker installation.
-   **Solution**:
    1.  **Check Docker Desktop**: Ensure Docker Desktop is running (look for the whale icon in your system tray/menu bar).
    2.  **Restart Docker Desktop**: Close and restart Docker Desktop if it appears to be running but not responding.
    3.  **Check your internet connection**: The application needs to download Docker images from the internet.
    4.  **Check for permission issues**: On some systems, Docker may need administrator privileges.
    5.  **Restart your computer**: Sometimes, Docker services don't start properly after installation.
    6.  **Reinstall Docker Desktop**: If problems persist, uninstall and reinstall Docker Desktop following the installation guide.

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

## Unified Python Launcher Issues

### `python3: command not found` or `python: command not found`
-   **Cause**: Python is not installed or not in PATH.
-   **Solution**:
    1.  Install Python 3.10+ following the [Quick Setup Guide](QUICK_SETUP_GUIDE.md)
    2.  Try `python run.py` instead of `python3 run.py` (common on Windows)
    3.  Restart your terminal after installation

### Import Errors when running `run.py`
-   **Cause**: Running from wrong directory or missing dependencies.
-   **Solution**:
    1.  Ensure you're running from the project root directory
    2.  Check that all required files are present (utils/, src/, etc.)
    3.  Verify Git repository is properly cloned

### Launcher Won't Start
-   **Cause**: Missing dependencies or incorrect Python version.
-   **Solution**:
    1.  Verify Python 3.10+ is installed: `python3 --version`
    2.  Ensure Docker Desktop is running
    3.  Check that Git is installed and accessible
    4.  Run from the correct directory (project root)

## Platform-Specific Issues

### macOS Issues

#### Docker Desktop Won't Start
-   **Cause**: Wrong Docker Desktop version for your Mac's processor.
-   **Solution**: Ensure you downloaded the correct version (Apple Silicon vs Intel) from the Docker website.

#### Python Command Issues
-   **Cause**: macOS typically uses `python3` for Python 3.x.
-   **Solution**: Always use `python3 run.py` on macOS instead of `python run.py`.

### Windows Issues

#### WSL 2 Issues
-   **Cause**: Windows Subsystem for Linux (WSL 2) is not properly configured.
-   **Solution**:
    1.  Run `wsl --update` in Command Prompt as Administrator
    2.  Ensure WSL 2 is enabled in Windows Features
    3.  Restart your computer after making changes

#### Antivirus Blocking Docker
-   **Cause**: Some antivirus software may block Docker operations.
-   **Solution**: Add Docker Desktop to your antivirus exceptions list.

#### Python Command Variations
-   **Cause**: Windows may have Python installed as `python` or `python3`.
-   **Solution**: Try both `python run.py` and `python3 run.py` to see which works.

#### Path Issues
-   **Cause**: Commands aren't found after installation.
-   **Solution**: Restart your terminal after installing prerequisites to refresh the PATH environment variable.

### Linux Issues

#### Docker Permission Issues
-   **Cause**: User not in docker group.
-   **Solution**:
    1.  Add user to docker group: `sudo usermod -aG docker $USER`
    2.  Log out and log back in
    3.  Verify with: `docker run hello-world`

#### Python Version Issues
-   **Cause**: System may have multiple Python versions.
-   **Solution**: Use `python3 run.py` and ensure Python 3.10+ is installed.

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

### Fatal Sync Error Detected

-   **Cause**: The repository has been updated but the Docker image has not been rebuilt, creating a dangerous mismatch between code and container environment.
-   **Error Message**:
    ```
    ❌ **FATAL SYNC ERROR DETECTED**
       Repository commit: a1b2c3d4e5f6789012345678901234567890abcd
       Docker image commit: f6e5d4c3b2a1098765432109876543210987fedc
       
       The repository has been updated but the Docker image has not been rebuilt.
       Running with this mismatch could cause serious issues.
    ```
-   **Solution**: You must resolve the sync error before proceeding:
    1.  **Build a new Docker image**: Run `./build/build_image_from_lock_files.sh`
    2.  **Push the new image**: Run `./build/push_image_to_github.sh`
    3.  **Or pull the latest image**: Run `docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main`
    4.  **Then try running the application again**

### Update Check Fails

-   **Cause**: The application cannot connect to GitHub to check for updates. This is usually due to network issues.
-   **Solution**:
    1.  Ensure you have a stable internet connection.
    2.  Ensure Git is properly installed and accessible.
    3.  You can force a new update check by restarting the application.

### Script Update Fails

-   **Cause**: The application was unable to pull the latest scripts from the Git repository, likely due to a network issue.
-   **Solution**:
    1.  Ensure you have a stable internet connection and try the update again.
    2.  Verify that Git is properly installed and accessible.
    3.  Check that your firewall isn't blocking Git access to GitHub.

## Container Issues

### Container Won't Start

-   **Cause**: Docker container may be corrupted or conflicting with existing containers.
-   **Solution**:
    1.  **Clean up containers**: Run `docker system prune` to remove old containers and images
    2.  **Restart Docker Desktop**: Close and restart Docker Desktop
    3.  **Check resources**: Ensure Docker Desktop has sufficient memory and CPU allocated

### Port Already in Use

-   **Cause**: Another application is using port 8501 (the default Streamlit port).
-   **Solution**:
    1.  **Find the conflicting process**: Run `lsof -i :8501` (macOS/Linux) or `netstat -ano | findstr :8501` (Windows)
    2.  **Stop the conflicting process**: Kill the process using the port
    3.  **Restart the application**: The application should now be able to use the port

## Getting Help

If you continue to experience issues after trying these solutions:

1.  **Verify Prerequisites**: Ensure all prerequisites (Docker Desktop, Git, Python 3.10+) are properly installed
2.  **Restart Everything**: Restart your computer after installing prerequisites
3.  **Check System Requirements**: Ensure your system meets the minimum requirements for Docker Desktop
4.  **Review Installation Steps**: Double-check that you followed all installation steps in the Quick Setup Guide
5.  **Check Application Logs**: Look for specific error messages in the terminal when running the application
6.  **Clean Installation**: If all else fails, uninstall and reinstall all prerequisites following the Quick Setup Guide