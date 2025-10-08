# SIP LIMS Workflow Manager - Quick Setup Guide

## 1. Prerequisites: Install Miniconda

This application requires **Miniconda** (a minimal version of Anaconda) to manage its Python environment and all dependencies.

### On Windows:
1.  **Download the installer:** Go to the [Miniconda for Windows documentation](https://docs.conda.io/en/latest/miniconda.html#windows-installers) and download the latest **64-bit (exe)** installer.
2.  **Run the installer:**
    *   When prompted, choose to install for **"Just Me"**.
    *   Accept the default installation location.
    *   **Crucially**, on the "Advanced Installation Options" screen, ensure the box for **"Add Miniconda3 to my PATH environment variable"** is **checked**. While not recommended by the installer, it is the most reliable way to ensure the setup scripts can find Conda.
3.  **Restart your computer** after installation to ensure the PATH changes take effect.

### On macOS:
1.  **Download the installer:** Go to the [Miniconda for macOS documentation](https://docs.conda.io/en/latest/miniconda.html#macos-installers) and download the installer that matches your Mac's processor:
    *   For newer Macs (M1, M2, M3), choose the **"Apple M1 (and later) .pkg"** installer.
    *   For older, Intel-based Macs, choose the **"Intel x86 .pkg"** installer.
2.  **Run the installer:** Double-click the downloaded `.pkg` file and follow the on-screen instructions, accepting all defaults. The installer will automatically configure your shell to use Conda.
3.  **Close and reopen your Terminal** application for the changes to take effect.

### Verify Installation
Open a new terminal (Terminal on macOS, or "Anaconda Prompt" from the Start Menu on Windows) and type:
```bash
conda --version
```
You should see output like `conda 24.x.x`. If you see an error, the installation was not successful.

---

## 2. Application Setup

Once Miniconda is installed and verified, you can set up the application.

### Download and Extract
-   Download the latest `sip_lims_workflow_manager` .zip file from GitHub.
-   Extract to a permanent location (e.g., your Desktop or Documents folder).

### Run the Setup Script (One-time only)
This step will create a self-contained Conda environment named `sip-lims` with all the necessary dependencies. It may take several minutes.

-   **On macOS:** Double-click `setup.command`.
-   **On Windows:** Double-click `setup.bat`.

---

## 3. Launch the Application

-   **On macOS:** Double-click `run.command`.
-   **On Windows:** Double-click `run.bat`.

The application will open in your web browser. The terminal window will show which Python environment is being used and provide the URL.

---

## 4. Updating the Application

When a new version of the application is released, follow these steps:

1.  **Download the New Version**: The application will notify you when an update is available. Use the link provided to download the new `.zip` file from GitHub.
2.  **Replace the Old Folder**: Close the running application, delete your old `sip_lims_workflow_manager` folder, and replace it with the new one you just extracted.
3.  **Re-run the Setup Script (Recommended)**: After replacing the folder, it is a best practice to run the `setup.command` or `setup.bat` script **one more time**. This ensures that:
    *   Any new dependencies are added to your Conda environment.
    *   SSH key permissions are correctly set, which is required for the update-checking feature to work.
4.  **Launch the New Version**: Run the application as usual with `run.command` or `run.bat`.

---

## Troubleshooting

-   **`conda: command not found`**: Miniconda was not installed correctly or was not added to your system's PATH. Please reinstall it, ensuring you follow the OS-specific instructions above.
-   **Setup Fails**: If the setup script fails, try running it again. If it fails because the `sip-lims` environment already exists, you can manually remove it by running `conda env remove --name sip-lims` in a terminal and then re-running the setup script.
-   **Application Won't Start**: Run the `setup.command` or `setup.bat` script again. It is safe to run multiple times and will ensure your environment is up to date.