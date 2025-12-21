# SIP LIMS Workflow Manager - Quick Setup Guide

## 1. Prerequisites: Install Miniconda

This application requires **Miniconda** to manage its Python environment and all dependencies.

### On macOS:
1.  **Download the installer:** Go to the [Miniconda for macOS documentation](https://docs.conda.io/en/latest/miniconda.html#macos-installers) and download the installer that matches your Mac's processor:
    *   For newer Macs (M1, M2, M3), choose the **"Apple M1 (and later) .pkg"** installer.
    *   For older, Intel-based Macs, choose the **"Intel x86 .pkg"** installer.
2.  **Run the installer:** Double-click the downloaded `.pkg` file and follow the on-screen instructions, accepting all defaults. The installer will automatically configure your shell to use Conda.
3.  **Close and reopen your Terminal** application for the changes to take effect.

### Verify Installation
Open a new terminal and type:
```bash
conda --version
```
You should see output like `conda 24.x.x`. If you see an error, the installation was not successful.

---

## 2. Application Setup

This project uses an intelligent update system that automatically manages both the application and Python scripts.

### Standard User Setup (Production Mode)

This is the default, automated setup for all standard users.

1.  **Download and Extract**:
    *   Download the latest `sip_lims_workflow_manager` .zip file from GitHub.
    *   Extract it to a permanent location (e.g., your Desktop or Documents folder).

2.  **Run the Setup Script (One-time only)**:
    *   Double-click `setup.command`.
    *   This script will create the `sip-lims` Conda environment.

---

## 3. Launching the Application

-   Double-click `run.command`.

### For Production Users:
-   **Automatic Updates**: The application silently checks and downloads the latest Docker images and Python scripts from GitHub
-   **No User Prompts**: Completely automated experience
-   **Centralized Management**: Scripts are automatically managed in `~/.sip_lims_workflow_manager/scripts`

### For Developers:
-   **Mode Detection**: Automatically detects `config/developer.marker` file
-   **Workflow Choice**: Choose between:
    - **Production Mode (1)**: Auto-updates enabled, uses centralized scripts
    - **Development Mode (2)**: No auto-updates, drag-and-drop local script folder selection

The application will open in your web browser at `http://127.0.0.1:8501`.

---

## 4. Developer Setup (Optional)

Developers can use a local, mutable set of scripts for testing and development.

### Activating Developer Mode
1.  Inside the `sip_lims_workflow_manager` directory, create a new folder named `config`.
2.  Inside the `config` folder, create an empty file named `developer.marker`.

The presence of this file activates "Developer Mode," which enables interactive prompts during setup and runtime.

### Running the Application in Developer Mode
-   When you run `run.command`, you will be prompted to choose your workflow:
    *   **Production Mode (1)**: Auto-updates enabled, uses centralized scripts from GitHub
    *   **Development Mode (2)**: No auto-updates, drag-and-drop selection of local script folder

---

## 5. Updating the Application

### Automatic Updates (Production Users)
-   **Docker Images**: Automatically updated every time you run `run.command`
-   **Python Scripts**: Automatically updated every time you run `run.command`
-   **No Manual Action Required**: Updates happen silently in the background

### Manual Updates (Application Core)
1.  **Download the New Version**: When notified of an update, download the new `sip_lims_workflow_manager` .zip file.
2.  **Replace the Old Folder**: Close the application, delete your old `sip_lims_workflow_manager` folder, and replace it with the new one.
3.  **Re-run Setup**: Run `setup.command` again to ensure all dependencies are up-to-date.

### Developer Updates
-   **Production Mode**: Same automatic updates as regular users
-   **Development Mode**: No automatic updates - manage your local scripts manually

---

## Troubleshooting

-   **`conda: command not found`**: Miniconda was not installed correctly. Please reinstall it, ensuring you follow the instructions above.
-   **Setup Fails**: If the setup script fails, try running it again. If it fails because the `sip-lims` environment already exists, you can manually remove it by running `conda env remove --name sip-lims` in a terminal and then re-running the setup script.
-   **Application Won't Start**: Run the `setup.command` script again. It is safe to run multiple times and will ensure your environment is up to date.