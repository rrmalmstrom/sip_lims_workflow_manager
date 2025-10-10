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

-   **Cause**: The application cannot connect to GitHub to check for updates. This is usually due to network issues or problems with the SSH key configuration.
-   **Solution**:
    1.  Ensure you have a stable internet connection.
    2.  If the problem persists, it may be related to the SSH key. See the `SSH Key Issues` section below.
    3.  You can force a new update check by clicking the "🔄 Manual Check for Updates" button in the sidebar.

### Script Update Fails

-   **Cause**: The application was unable to pull the latest scripts from the Git repository.
-   **Solution**: This is almost always an SSH key issue. Please refer to the `SSH Key Issues` section for detailed troubleshooting steps.

## SSH Key Issues

### Host Key Verification Failed

-   **Cause**: During the first-time setup, the script was unable to automatically verify the connection to GitHub. You may see an error like `The authenticity of host 'github.com' can't be established` or `Host key verification failed`.
-   **Solution**: You must perform a simple, one-time manual authorization of GitHub. Please follow the instructions in the **[Quick Setup Guide](QUICK_SETUP_GUIDE.md)** under the section titled **"2. Important: Authorize GitHub"**.

### Permission Denied

-   **Cause**: The SSH private key file has incorrect file permissions, making it too "open" for SSH to use securely.
-   **Solution**: The application's setup script should handle this automatically. However, if you encounter this issue, you can manually fix the permissions. Open a terminal and run the following commands:
    ```bash
    chmod 600 .ssh/scripts_deploy_key
    chmod 600 .ssh/app_deploy_key
    ```

### Repository Not Found or Key Already in Use

-   **Cause**: The SSH key is not correctly configured in your GitHub account, or the key is associated with another repository.
-   **Solution**:
    1.  Ensure that the public keys (`.ssh/scripts_deploy_key.pub` and `.ssh/app_deploy_key.pub`) have been added as deploy keys to the correct GitHub repositories.
    2.  If you see a "key already in use" error, you may need to remove the old deploy key from any other repositories in your GitHub account.
    3.  You can test your SSH key access by running the following command in a terminal from the application's root directory:
        ```bash
        # Test scripts repository access
        ssh -T -i .ssh/scripts_deploy_key git@github.com

        # Test application repository access
        ssh -T -i .ssh/app_deploy_key git@github.com
        ```
    You should see a success message from GitHub for both commands.