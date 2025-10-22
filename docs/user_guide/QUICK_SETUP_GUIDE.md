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

## 2. Application and Scripts Setup

This project uses a decoupled structure where the application (`sip_lims_workflow_manager`) and the scientific scripts (`sip_scripts_prod` or `sip_scripts_dev`) reside in **sibling directories**.

```
/some/path/
├── sip_lims_workflow_manager/  (The application you downloaded)
└── sip_scripts_prod/           (The scripts, automatically created by the setup script)
```

### Standard User Setup (Production Mode)

This is the default, non-interactive setup for all standard users.

1.  **Download and Extract**:
    *   Download the latest `sip_lims_workflow_manager` .zip file from GitHub.
    *   Extract it to a permanent location (e.g., your Desktop or Documents folder).

2.  **Run the Setup Script (One-time only)**:
    *   Double-click `setup.command`.
    *   This script will create the `sip-lims` Conda environment and automatically clone or update the production scripts into a **sibling directory** named `sip_scripts_prod`.

---

## 3. Launching the Application

-   Double-click `run.command`.

The application will automatically use the scripts from the `sip_scripts_prod` directory and will open in your web browser.

---

## 4. Developer Setup (Optional)

Developers can use a local, mutable set of scripts for testing and development.

### Activating Developer Mode
1.  Inside the `sip_lims_workflow_manager` directory, create a new folder named `config`.
2.  Inside the `config` folder, create an empty file named `developer.marker`.

The presence of this file activates "Developer Mode," which enables interactive prompts during setup and runtime.

### Running Setup in Developer Mode
-   With `config/developer.marker` present, run `setup.command`.
-   The script will provide an interactive prompt asking if you want to work **offline** (skipping remote updates) or **online**.
-   It will still set up the `sip_scripts_prod` repository but will also provide guidance on using the separate `migrate_dev_scripts.command` to move any existing nested `scripts` into the new `../sip_scripts_dev` directory.

### Running the Application in Developer Mode
-   When you run `run.command`, you will be prompted to choose which set of scripts to use for the session:
    *   **Development Scripts** (`../sip_scripts_dev`)
    *   **Production Scripts** (`../sip_scripts_prod`)

---

## 5. Updating the Application

The update process for the core application remains the same.

1.  **Download the New Version**: When notified of an update, download the new `sip_lims_workflow_manager` .zip file.
2.  **Replace the Old Folder**: Close the application, delete your old `sip_lims_workflow_manager` folder, and replace it with the new one.
3.  **Re-run Setup**: Run `setup.command` again to ensure all dependencies are up-to-date.

The production scripts in `../sip_scripts_prod` are updated automatically each time you run the setup script.

---

## Troubleshooting

-   **`conda: command not found`**: Miniconda was not installed correctly. Please reinstall it, ensuring you follow the instructions above.
-   **Setup Fails**: If the setup script fails, try running it again. If it fails because the `sip-lims` environment already exists, you can manually remove it by running `conda env remove --name sip-lims` in a terminal and then re-running the setup script.
-   **Application Won't Start**: Run the `setup.command` script again. It is safe to run multiple times and will ensure your environment is up to date.