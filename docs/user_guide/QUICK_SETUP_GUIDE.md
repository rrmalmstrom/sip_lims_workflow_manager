# SIP LIMS Workflow Manager - Quick Setup Guide

## 🍎 Native Mac Distribution

**Simple, one-click setup for Mac users!**

### Prerequisites
- **macOS** (Intel or Apple Silicon)
- **Miniconda** - For Python environment management

### Setup Steps

#### 1. Install Miniconda (if not already installed)
- Download from: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- Choose the installer for your Mac (Intel x86 or Apple Silicon M1/M2/M3/M4)
- Run the installer and follow the prompts
- Restart Terminal after installation

#### 2. Download and Setup
- Download the `sip_lims_workflow_manager.zip` from GitHub releases
- Extract to a permanent location (Desktop or Documents)
- **Double-click `setup.command`** (one-time setup, 2-3 minutes)
- Wait for "Setup completed successfully!" message

#### 3. Daily Usage
- **Double-click `run.command`** to launch the application
- Select your workflow type when prompted
- Start managing your laboratory workflow!

### Advanced Usage
For advanced users who want full control:
```bash
./run.command --help          # See all options
./run.command --updates       # Perform updates
./run.command --version       # Check version
```

---

## Application Features

### Workflow Types
When you run the application, you'll first be asked to select your workflow type:

**Workflow Selection:**
```
🧪 Select workflow type:
1) SIP (Stable Isotope Probing) - 21 step comprehensive workflow
2) SPS-CE (SPS-Capillary Electrophoresis) - 6 step focused workflow
Enter choice (1 or 2):
```

### Project Folder Selection
You'll be prompted to drag and drop your project folder:
```
📁 Project Folder Selection
Please drag and drop your project folder here, then press Enter:
Project path:
```

### Application Launch
The application will start with your chosen workflow template loaded and ready for use.

---

## Updating the Application

### Update Behavior
The application has an intelligent update system:

**Default Behavior (Recommended):**
- **Scripts Updates**: Always performed automatically (safe and fast)
- **Core System Updates**: Performed when using `--updates` flag
- **User-Friendly**: Clear messaging about what updates are being performed

**Full Updates (When Needed):**
- Use `./run.command --updates` to perform core system updates and get restart instructions
- After updates complete, restart with `./run.command` to launch with the latest version

### Automatic Features
- **Automatic Script Updates**: Python scripts are automatically updated from GitHub
- **Centralized Management**: Scripts are managed in `~/.sip_lims_workflow_manager/scripts`
- **Deterministic Environment**: Exact same package versions every time

---

## Troubleshooting

### Installation Issues
- **`conda: command not found`**: Miniconda was not installed correctly. Please reinstall following the instructions above
- **Setup fails**: Ensure you have internet connection and sufficient disk space

### Runtime Issues
- **Application Won't Start**: Ensure Miniconda is properly installed and the `sip-lims` environment was created successfully
- **Permission Issues**: Make sure `run.command` and `setup.command` have execute permissions

### Update Issues
- **Update Detection Fails**: Ensure you have internet connection and Git is properly installed
- **Script Update Fails**: Verify internet connection and that Git can access GitHub

### macOS-Specific Issues
- **Command files won't run**: Right-click the `.command` file and select "Open" to bypass Gatekeeper
- **Python Command Issues**: The native launcher handles all Python execution automatically

### Getting Help
If you continue to experience issues:
1. Ensure Miniconda is properly installed
2. Restart Terminal after installing prerequisites
3. Try running `./setup.command` again
4. Check that you have internet connectivity

---

## Environment Management

This application uses a **deterministic conda environment** for maximum reliability:

- **Exact Package Versions**: All dependencies locked to specific versions via `conda-lock-mac.txt` and `requirements-lock-mac.txt`
- **Reproducible Builds**: Identical environments regardless of when/where built
- **Scientific Reproducibility**: Ensures consistent results across all deployments
- **Native Performance**: Direct Python execution for optimal speed and debugging capabilities

The `sip-lims` conda environment contains all necessary dependencies and is automatically managed by the setup and run scripts.