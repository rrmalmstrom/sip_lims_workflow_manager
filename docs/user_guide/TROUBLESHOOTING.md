# SIP LIMS Workflow Manager - Troubleshooting Guide

This guide helps you resolve common issues with the Native Mac Distribution of the SIP LIMS Workflow Manager.

## Installation and Setup Issues

### `conda: command not found`

-   **Cause**: This error means that Miniconda is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
     1.  Install Miniconda following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
     2.  After installation, restart your terminal for the changes to take effect.
     3.  Run `conda init` to configure your shell if needed.

### `git: command not found`

-   **Cause**: This error means that Git is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
     1.  Install Git following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
     2.  After installation, restart your terminal for the changes to take effect.

### Setup Command Won't Run

-   **Cause**: The `setup.command` file may not have execute permissions or macOS security is blocking it.
-   **Solution**:
     1.  **Right-click `setup.command`** and select **"Open"** to bypass Gatekeeper
     2.  If that doesn't work, open Terminal and run: `chmod +x setup.command`
     3.  Try double-clicking `setup.command` again

### Conda Environment Issues

-   **Cause**: The conda environment may not be properly created or dependencies may be missing.
-   **Solution**:
     1.  **Verify conda installation**: Run `conda --version` to ensure conda is installed
     2.  **Re-run setup**: Try running `./setup.command` again
     3.  **Check environment**: Run `conda env list` to see if `sip-lims` environment exists
     4.  **Manual environment creation**: If setup fails, try creating manually:
         ```bash
         conda create -n sip-lims python=3.11
         conda activate sip-lims
         conda install --file environments/mac/conda-lock-mac.txt
         pip install -r environments/mac/requirements-lock-mac.txt
         ```

## Application Runtime Issues

### Application Won't Start

-   **Cause**: Missing dependencies, conda environment not activated, or file permissions.
-   **Solution**:
     1.  **Try right-clicking `run.command`** and select **"Open"** to bypass Gatekeeper
     2.  **Verify setup completed**: Ensure you see "Setup completed successfully!" message from setup
     3.  **Check conda environment**: Run `conda env list` to verify `sip-lims` environment exists
     4.  **Check file permissions**: Ensure you have read/write access to the project directory
     5.  **Restart your terminal**: Sometimes environment variables need to be refreshed

### Import Errors when running the application

-   **Cause**: Missing dependencies or conda environment not properly activated.
-   **Solution**:
     1.  **Re-run setup**: Try running `./setup.command` again
     2.  **Check conda environment**: Ensure the `sip-lims` environment was created successfully
     3.  **Verify project structure**: Ensure all required files are present (`src/`, `launcher/`, etc.)
     4.  **Manual activation**: Try manually activating the environment:
         ```bash
         conda activate sip-lims
         python launcher/run.py
         ```

### Launcher Won't Start

-   **Cause**: Missing dependencies, conda environment issues, or file permissions.
-   **Solution**:
     1.  **Check conda environment**: Run `conda activate sip-lims` manually
     2.  **Verify dependencies**: Ensure all required packages are installed
     3.  **Check project structure**: Ensure all required directories and files are present
     4.  **Run from correct directory**: Must be executed from the project root

## macOS-Specific Issues

### Gatekeeper Blocking Execution

-   **Cause**: macOS security features prevent unsigned applications from running.
-   **Solution**:
     1.  **Right-click the `.command` file** and select **"Open"** instead of double-clicking
     2.  **Click "Open"** when macOS asks for confirmation
     3.  **Alternative**: Go to System Preferences > Security & Privacy > General and click "Open Anyway"

### Permission Issues

-   **Cause**: macOS security restrictions may prevent file access.
-   **Solution**:
     1.  **Grant Terminal full disk access**: System Preferences > Security & Privacy > Privacy > Full Disk Access
     2.  **Check file permissions**: Ensure you have write permissions to the project directory
     3.  **Fix permissions**: Run `chmod +x *.command` to make command files executable

### Conda Path Issues

-   **Cause**: Conda may not be in the system PATH after installation.
-   **Solution**:
     1.  **Initialize conda**: Run `conda init` to configure your shell
     2.  **Restart terminal**: Close and reopen Terminal after conda initialization
     3.  **Check PATH**: Run `echo $PATH` to verify conda is in your PATH

### External Drive Issues

-   **Cause**: Projects on external drives may have permission or access issues.
-   **Solution**:
     1.  **Ensure drive is mounted**: Verify the external drive appears in Finder
     2.  **Check permissions**: Ensure you have read/write access to the external drive
     3.  **Try local copy**: Copy project to local drive temporarily to test

## Update and Network Issues

### Update Detection Fails

-   **Cause**: Network connectivity issues or Git configuration problems.
-   **Solution**:
     1.  **Check internet connection**: Ensure you can access GitHub.com
     2.  **Verify Git access**: Run `git --version` to ensure Git is accessible
     3.  **Test Git connectivity**: Run `git ls-remote https://github.com/RRMalmstrom/sip_lims_workflow_manager.git`

### Script Update Fails

-   **Cause**: Network issues or Git repository access problems.
-   **Solution**:
     1.  **Check internet connection**: Verify connectivity to GitHub
     2.  **Clear Git cache**: Run `git config --global --unset credential.helper` if authentication fails
     3.  **Manual update**: Try running `./run.command --updates` to force updates

## Performance Issues

### Slow Application Startup

-   **Cause**: External drive latency or conda environment loading.
-   **Solution**:
     1.  **Use local storage**: Copy project to local drive for better performance
     2.  **Check available space**: Ensure sufficient disk space on your Mac
     3.  **Restart application**: Close and reopen the application

### High Memory Usage

-   **Cause**: Large datasets or multiple workflow instances.
-   **Solution**:
     1.  **Close other applications**: Free up system memory
     2.  **Restart the application**: Close and reopen to clear memory
     3.  **Check Activity Monitor**: Monitor memory usage in macOS Activity Monitor

## Getting Help

### Diagnostic Information

If you need to report an issue, please gather this information:

1.  **macOS version**: Run `sw_vers` in Terminal
2.  **Conda version**: Run `conda --version`
3.  **Environment status**: Run `conda env list`
4.  **Git version**: Run `git --version`
5.  **Error messages**: Copy any error messages you see

### Common Solutions Summary

1.  **Right-click `.command` files** and select "Open" to bypass Gatekeeper
2.  **Re-run `./setup.command`** if you encounter dependency issues
3.  **Restart Terminal** after installing new software
4.  **Check internet connectivity** for update-related issues
5.  **Ensure sufficient disk space** for conda environments and project data

### Still Having Issues?

If you continue to experience problems:

1.  Try creating a new conda environment manually
2.  Verify all prerequisites are properly installed
3.  Check that you have administrator privileges on your Mac
4.  Consider running the application from a local drive instead of external storage