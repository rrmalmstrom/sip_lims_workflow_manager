# Troubleshooting Guide

This guide provides solutions to common issues you may encounter while using the SIP LIMS Workflow Manager.

## Installation and Setup Issues

### `git: command not found`

-   **Cause**: This error means that Git is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
     1.  Install Git following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
     2.  On Windows, ensure you selected "Git from the command line and also from 3rd-party software" during installation.
     3.  After installation, restart your terminal for the changes to take effect.

### `python3: command not found` or `python: command not found`

-   **Cause**: This error means that Python 3.10+ is not installed correctly or was not added to your system's PATH environment variable.
-   **Solution**:
     1.  Install Python 3.10+ following the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)**.
     2.  On Windows, ensure you checked "Add python.exe to PATH" during installation.
     3.  After installation, restart your terminal for the changes to take effect.
     4.  Try both `python run.py` and `python3 run.py` to see which works on your system.

### Conda Environment Issues

-   **Cause**: The conda environment may not be properly activated or dependencies may be missing.
-   **Solution**:
     1.  **Verify conda installation**: Run `conda --version` to ensure conda is installed
     2.  **Check environment**: Ensure you're in the correct conda environment for the project
     3.  **Reinstall dependencies**: Run `conda install --file requirements-lock.txt` if dependencies are missing
     4.  **Environment conflicts**: Create a fresh conda environment if there are package conflicts

### Application Won't Start

-   **Cause**: Missing dependencies, incorrect Python version, or environment issues.
-   **Solution**:
     1.  **Check Python version**: Ensure Python 3.10+ is installed: `python3 --version`
     2.  **Verify dependencies**: Ensure all required packages are installed in your conda environment
     3.  **Check working directory**: Ensure you're running from the project root directory
     4.  **Check file permissions**: Ensure you have read/write access to the project directory
     5.  **Restart your terminal**: Sometimes environment variables need to be refreshed

## Native Python Launcher Issues

### Import Errors when running `run.py`

-   **Cause**: Running from wrong directory, missing dependencies, or Python path issues.
-   **Solution**:
     1.  Ensure you're running from the project root directory (where `run.py` is located)
     2.  Check that all required files are present (`src/`, `utils/`, etc.)
     3.  Verify your conda environment has all required packages installed
     4.  Try running with `python3 -m run` if direct execution fails

### Launcher Won't Start

-   **Cause**: Missing dependencies, incorrect Python version, or environment configuration issues.
-   **Solution**:
     1.  **Verify Python version**: Run `python3 --version` (should be 3.10+)
     2.  **Check conda environment**: Ensure you're in the correct environment
     3.  **Verify Git access**: Run `git --version` to ensure Git is accessible
     4.  **Check project structure**: Ensure all required directories and files are present
     5.  **Run from correct directory**: Must be executed from the project root

### Module Not Found Errors

-   **Cause**: Python cannot find required modules or packages.
-   **Solution**:
     1.  **Check PYTHONPATH**: Ensure the project root is in your Python path
     2.  **Verify conda environment**: Make sure all dependencies are installed
     3.  **Reinstall packages**: Run `pip install -r requirements-lock.txt` if needed
     4.  **Check imports**: Verify that all import statements in the code are correct

## Platform-Specific Issues

### macOS Issues

#### Python Command Issues
-   **Cause**: macOS typically uses `python3` for Python 3.x installations.
-   **Solution**: Always use `python3 run.py` on macOS instead of `python run.py`.

#### Permission Issues
-   **Cause**: macOS security restrictions may prevent file access.
-   **Solution**:
     1.  Grant Terminal full disk access in System Preferences > Security & Privacy
     2.  Ensure you have write permissions to the project directory
     3.  Use `chmod +x run.py` to make the launcher executable if needed

#### Conda Path Issues
-   **Cause**: Conda may not be in the system PATH.
-   **Solution**:
     1.  Run `conda init` to configure your shell
     2.  Restart your terminal after conda initialization
     3.  Verify conda is accessible with `conda --version`

### Windows Issues

#### Python Command Variations
-   **Cause**: Windows may have Python installed as `python` or `python3`.
-   **Solution**: Try both `python run.py` and `python3 run.py` to see which works.

#### Path Issues
-   **Cause**: Commands aren't found after installation.
-   **Solution**: Restart your terminal after installing prerequisites to refresh the PATH environment variable.

#### Conda Environment Activation
-   **Cause**: Conda environments may not activate properly on Windows.
-   **Solution**:
     1.  Use `conda activate environment_name` to manually activate
     2.  Ensure conda is properly initialized: `conda init cmd.exe`
     3.  Restart Command Prompt after initialization

#### Network Drive Issues
-   **Cause**: Windows network drives may have permission or access issues.
-   **Solution**:
     1.  **Map network drive**: Ensure network drives are properly mapped with drive letters
     2.  **Check permissions**: Verify you have read/write access to the network location
     3.  **Use local staging**: Consider copying project to local drive if network issues persist
     4.  **UNC path issues**: Use mapped drive letters instead of UNC paths (\\server\share)

### Linux Issues

#### Python Version Issues
-   **Cause**: System may have multiple Python versions or missing packages.
-   **Solution**: 
     1.  Use `python3 run.py` and ensure Python 3.10+ is installed
     2.  Install required packages: `sudo apt-get install python3-pip python3-venv` (Ubuntu/Debian)
     3.  Consider using conda for package management

#### Permission Issues
-   **Cause**: File permissions or user access restrictions.
-   **Solution**:
     1.  Ensure you have read/write permissions to the project directory
     2.  Use `chmod +x run.py` to make the launcher executable
     3.  Check that your user has access to required system resources

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

### Project Path Issues

-   **Cause**: Invalid project paths or inaccessible directories.
-   **Solution**:
     1.  **Verify path exists**: Ensure the project directory actually exists and is accessible
     2.  **Check permissions**: Verify you have read/write access to the project directory
     3.  **Use absolute paths**: Avoid relative paths that may not resolve correctly
     4.  **Network drive issues**: For network drives, ensure they are properly mounted and accessible

## Update Issues

### Update Check Fails

-   **Cause**: The application cannot connect to GitHub to check for updates. This is usually due to network issues.
-   **Solution**:
     1.  Ensure you have a stable internet connection.
     2.  Ensure Git is properly installed and accessible.
     3.  Check firewall settings that might block Git access to GitHub.
     4.  You can force a new update check by restarting the application.

### Script Update Fails

-   **Cause**: The application was unable to pull the latest scripts from the Git repository, likely due to a network issue.
-   **Solution**:
     1.  Ensure you have a stable internet connection and try the update again.
     2.  Verify that Git is properly installed and accessible.
     3.  Check that your firewall isn't blocking Git access to GitHub.
     4.  Clear local git cache if needed: `git clean -fd` in the project directory

### Repository Update Issues

-   **Cause**: Git repository conflicts or network connectivity problems.
-   **Solution**:
     1.  **Check internet connection**: Ensure stable connection to GitHub
     2.  **Verify Git configuration**: Run `git config --list` to check settings
     3.  **Clear Git cache**: Remove `.git/index.lock` if it exists
     4.  **Reset repository**: Use `git reset --hard` if local changes are causing conflicts

## Performance Issues

### Slow Startup

-   **Cause**: Large conda environments or slow disk access.
-   **Solution**:
     1.  **Use SSD storage**: Move project to SSD if using traditional hard drive
     2.  **Optimize conda**: Clean conda cache with `conda clean --all`
     3.  **Reduce environment size**: Remove unnecessary packages from conda environment
     4.  **Check antivirus**: Exclude project directory from real-time scanning

### Memory Issues

-   **Cause**: Large datasets or insufficient system memory.
-   **Solution**:
     1.  **Close other applications**: Free up system memory
     2.  **Increase virtual memory**: Configure system swap/page file
     3.  **Process data in chunks**: For large datasets, consider processing in smaller batches
     4.  **Monitor memory usage**: Use system tools to identify memory bottlenecks

### External Drive Performance

-   **Cause**: Network drives or external storage may have slower access times.
-   **Solution**:
     1.  **Use local staging**: Copy project to local drive for processing
     2.  **Optimize network settings**: Ensure stable network connection for network drives
     3.  **Check drive health**: Verify external drive is functioning properly
     4.  **Use faster connection**: USB 3.0+ or Thunderbolt for external drives

## Application Runtime Issues

### Streamlit Port Issues

-   **Cause**: Port 8501 (default Streamlit port) may be in use by another application.
-   **Solution**:
     1.  **Find conflicting process**: Run `lsof -i :8501` (macOS/Linux) or `netstat -ano | findstr :8501` (Windows)
     2.  **Stop conflicting process**: Kill the process using the port
     3.  **Use different port**: Modify application to use alternative port if needed
     4.  **Restart application**: The application should now be able to use the port

### Browser Access Issues

-   **Cause**: Web browser cannot connect to the local Streamlit server.
-   **Solution**:
     1.  **Check URL**: Ensure you're accessing `http://127.0.0.1:8501` or `http://localhost:8501`
     2.  **Firewall settings**: Check that firewall allows local connections
     3.  **Browser cache**: Clear browser cache and cookies
     4.  **Try different browser**: Test with a different web browser

### Session State Issues

-   **Cause**: Streamlit session state corruption or conflicts.
-   **Solution**:
     1.  **Refresh browser**: Use Ctrl+F5 or Cmd+Shift+R to hard refresh
     2.  **Clear browser data**: Clear cookies and local storage for localhost
     3.  **Restart application**: Stop and restart the workflow manager
     4.  **Check for conflicts**: Ensure no other Streamlit apps are running

## Getting Help

If you continue to experience issues after trying these solutions:

1.  **Verify Prerequisites**: Ensure Python 3.10+, Git, and conda are properly installed
2.  **Restart Everything**: Restart your computer after installing prerequisites
3.  **Check System Requirements**: Ensure your system meets the minimum requirements
4.  **Review Installation Steps**: Double-check that you followed all installation steps in the Quick Setup Guide
5.  **Check Application Logs**: Look for specific error messages in the terminal when running the application
6.  **Clean Installation**: If all else fails, create a fresh conda environment and reinstall dependencies
7.  **Check Debug Output**: Look in the `debug_output/` directory for detailed error logs and diagnostic information