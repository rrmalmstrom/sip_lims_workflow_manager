# SIP LIMS Workflow Manager - Quick Setup Guide

## Prerequisites

This application requires three components to be installed on your system:

1. **Docker Desktop** - For running the containerized application
2. **Git** - For update detection and version management
3. **Python 3.10+** - For running update detection scripts

---

## 1. Install Docker Desktop

This application uses **Docker** with deterministic builds to ensure a consistent and reproducible environment across all platforms.

### On macOS:
1.  **Download Docker Desktop:**
    - Go to [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
    - Click **"Download for Mac"**
    - Choose the version that matches your Mac's processor:
        * For newer Macs (M1, M2, M3, M4): **"Apple Silicon"**
        * For older Intel-based Macs: **"Intel Chip"**

2.  **Install Docker Desktop:**
    - Double-click the downloaded `Docker.dmg` file
    - Drag the Docker icon to your **Applications** folder
    - Wait for the copy to complete

3.  **Start Docker Desktop:**
    - Open **Applications** folder and double-click **Docker.app**
    - Accept the service agreement when prompted
    - Docker will start and may ask for system permissions - click **"OK"**
    - Wait for Docker to finish starting (you'll see "Docker Desktop is running" message)

4.  **Verify Docker is running:**
    - Look for the Docker whale icon in your menu bar (top-right corner)
    - The icon should be solid (not animated) when Docker is ready

### On Windows:
1.  **Download Docker Desktop:**
    - Go to [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
    - Click **"Download for Windows"**
    - Save the `Docker Desktop Installer.exe` file

2.  **Install Docker Desktop:**
    - Double-click `Docker Desktop Installer.exe` to run the installer
    - When prompted, ensure **"Use WSL 2 instead of Hyper-V"** is **checked** (recommended)
    - Click **"OK"** to proceed with installation
    - Follow the installation wizard prompts
    - Click **"Close"** when installation completes

3.  **Start Docker Desktop:**
    - Docker Desktop should start automatically after installation
    - If not, search for "Docker Desktop" in the Start menu and launch it
    - Accept the service agreement when prompted
    - Wait for Docker to finish starting

4.  **Verify Docker is running:**
    - Look for the Docker whale icon in your system tray (bottom-right corner)
    - The icon should be solid when Docker is ready

### Verify Docker Installation
Open a terminal (macOS: Terminal app, Windows: Command Prompt or PowerShell) and type:
```bash
docker --version
```
You should see output like `Docker version 24.x.x`. If you see an error, Docker is not running properly.

---

## 2. Install Git

Git is required for the application's update detection system.

### On macOS:
1.  **Check if Git is already installed:**
    - Open **Terminal** (found in Applications > Utilities)
    - Type: `git --version`
    - If you see a version number, Git is already installed - skip to verification

2.  **Install Git (if needed):**
    
    **Option A: Install Xcode Command Line Tools (Recommended)**
    - In Terminal, type: `xcode-select --install`
    - Click **"Install"** when the popup appears
    - Click **"Agree"** to accept the license
    - Wait for installation to complete (may take several minutes)
    
    **Option B: Download Git Installer**
    - Go to [https://git-scm.com/download/mac](https://git-scm.com/download/mac)
    - Download the installer for your Mac type (Intel or Apple Silicon)
    - Double-click the downloaded `.pkg` file and follow the installer

### On Windows:
1.  **Check if Git is already installed:**
    - Open **Command Prompt** (search "cmd" in Start menu)
    - Type: `git --version`
    - If you see a version number, Git is already installed - skip to verification

2.  **Install Git (if needed):**
    - Go to [https://git-scm.com/download/win](https://git-scm.com/download/win)
    - Click **"Download for Windows"** - this will download `Git-x.x.x-64-bit.exe`
    - Double-click the downloaded installer
    - **Important installation choices:**
        * **Default editor:** Choose "Use Visual Studio Code" or "Use Notepad++" (avoid Vim unless you're familiar with it)
        * **PATH environment:** Select **"Git from the command line and also from 3rd-party software"**
        * **Line ending conversions:** Select **"Checkout Windows-style, commit Unix-style line endings"**
        * **Terminal emulator:** Select **"Use Windows' default console window"**
        * **Git Credential Manager:** Select **"Git Credential Manager"**
    - Click **"Install"** and wait for completion

### Verify Git Installation
Open a new terminal/command prompt and type:
```bash
git --version
```
You should see output like `git version 2.x.x`.

---

## 3. Install Python 3.10+

Python 3.10 or higher is required for the application's setup and update detection system. While the workflow itself runs inside Docker containers, Python is needed on your local system to manage Docker image updates and script synchronization.

### On macOS:
1.  **Check if Python 3.10+ is already installed:**
    - Open **Terminal**
    - Type: `python3 --version`
    - If you see `Python 3.10.x` or higher, you're all set - skip to verification

2.  **Install Python (if needed):**
    
    **Option A: Download from Python.org (Recommended)**
    - Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
    - Click **"Download Python 3.x.x"** (ensure it's 3.10 or higher)
    - Double-click the downloaded `.pkg` file
    - Follow the installer prompts:
        * Click **"Continue"** through the introduction screens
        * Click **"Install"** (may require your password)
        * **Important:** Check **"Add Python to PATH"** if prompted
    - Click **"Close"** when installation completes
    
    **Option B: Install via Homebrew (Advanced users)**
    - First install Homebrew: [https://brew.sh](https://brew.sh)
    - Then run: `brew install python@3.11`

### On Windows:
1.  **Check if Python 3.10+ is already installed:**
    - Open **Command Prompt**
    - Type: `python --version` or `python3 --version`
    - If you see `Python 3.10.x` or higher, you're all set - skip to verification

2.  **Install Python (if needed):**
    
    **Option A: Download from Python.org (Recommended)**
    - Go to [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
    - Click **"Download Python 3.x.x"** (ensure it's 3.10 or higher)
    - Double-click the downloaded `python-3.x.x-amd64.exe` file
    - **CRITICAL:** Check **"Add python.exe to PATH"** at the bottom of the first screen
    - Choose **"Install Now"** for standard installation
    - Click **"Yes"** if Windows asks for permission
    - Wait for installation to complete
    - Click **"Close"** when finished
    
    **Option B: Microsoft Store (Alternative)**
    - Open **Microsoft Store**
    - Search for "Python 3.11" or "Python 3.12"
    - Click **"Get"** to install

### Verify Python Installation
Open a new terminal/command prompt and type:
```bash
python3 --version
```
Or on Windows, you might need:
```bash
python --version
```
You should see `Python 3.10.x` or higher.

---

## 4. Application Setup

This project uses an intelligent Docker-based update system that automatically manages both the application container and Python scripts.

### Download the Application

1.  **Download the Application**:
    *   Download the latest `sip_lims_workflow_manager` .zip file from GitHub
    *   Extract it to a permanent location (e.g., your Desktop or Documents folder)

2.  **Automatic Setup Handled by Docker**:
    *   All environment setup is handled automatically by Docker
    *   The deterministic Docker image contains all dependencies with exact versions
    *   No manual environment configuration needed

---

## 5. Launching the Application

### Easy-Click Launchers (Recommended)
For the easiest experience, use the platform-specific launchers that you can simply double-click:

**macOS Users:**
- Double-click **`run.mac.command`** in the project folder
- This will automatically launch the workflow with default settings

**Windows Users:**
- Double-click **`run.windows.bat`** in the project folder
- This will automatically launch the workflow with default settings

### Advanced: Command Line Launcher
For advanced users or automation, you can use the Python launcher directly:

**All Platforms (macOS, Windows, Linux):**
```bash
python3 run.py
```

Or on Windows, you might use:
```cmd
python run.py
```

**Command Line Options:**
- `python3 run.py` - Default behavior (scripts updates only)
- `python3 run.py --updates` - Enable all updates (fatal sync, repository, Docker, scripts)
- `python3 run.py --help` - Show all available options

### Step 1: Choose Workflow Type
When you run the application, you'll first be asked to select your workflow type:

**Workflow Selection:**
```
🧪 Select workflow type:
1) SIP (Stable Isotope Probing) - 21 step comprehensive workflow
2) SPS-CE (SPS-Capillary Electrophoresis) - 6 step focused workflow
Enter choice (1 or 2):
```

### Step 2: Choose Execution Mode
After selecting your workflow type, choose how to run:

- **Production Mode**: Uses pre-built Docker images and automatically managed scripts
- **Development Mode**: Uses local script directories for development and testing

### Step 3: Project Folder Selection
You'll be prompted to drag and drop your project folder:
```
📁 Project Folder Selection
Please drag and drop your project folder here, then press Enter:
Project path:
```

### Step 4: Application Launch
The application will start with your chosen workflow template loaded and ready for use.


### First-Time Experience:
- The application automatically downloads the latest Docker image from GitHub Container Registry
- You'll be prompted to drag and drop your project folder
- The application opens in your web browser at `http://127.0.0.1:8501`

### Automatic Features:
-   **Automatic Docker Updates**: Checks and downloads the latest Docker images automatically
-   **Automatic Script Updates**: Python scripts are automatically updated from GitHub
-   **Centralized Management**: Scripts are managed in `~/.sip_lims_workflow_manager/scripts`
-   **Deterministic Environment**: Exact same package versions every time


### Docker Container Features:
-   **Deterministic Builds**: Same exact environment every time using pinned package versions
-   **Automatic Cleanup**: Old containers and images are automatically cleaned up
-   **Volume Mounting**: Your project data and scripts are safely mounted from your host system
-   **User ID Mapping**: Proper file permissions for shared network drives

---

## 6. Updating the Application

### New Update Behavior (v1.1.0+)
Starting with version 1.1.0, the update behavior has been optimized for production users:

**Default Behavior (Recommended):**
- **Scripts Updates**: Always performed automatically (safe and fast)
- **Core System Updates**: Skipped by default (Docker images, repository updates, fatal sync checks)
- **User-Friendly**: Clear messaging about what updates are being performed

**Full Updates (When Needed):**
- Use `python3 run.py --updates` to enable all updates
- Or use the `--updates` flag when you want the latest Docker images and system updates

### Automatic Updates (Production Users)
-   **Python Scripts**: Always updated automatically for latest workflow improvements
-   **Docker Images**: Updated only when using `--updates` flag (prevents unnecessary downloads)
-   **Smart Updates**: Only downloads what you need, when you need it
-   **Reproducible Updates**: Each update uses exact package versions for consistency


---

## 7. Troubleshooting

### Installation Issues
-   **`docker: command not found`**: Docker Desktop was not installed correctly. Please reinstall following the instructions above
-   **`git: command not found`**: Git was not installed correctly. Please reinstall following the instructions above  
-   **`python3: command not found`**: Python was not installed correctly. Please reinstall following the instructions above

### Runtime Issues
-   **Docker Not Running**: If you see "Docker is not running" error, start Docker Desktop from your Applications folder (macOS) or Start menu (Windows)
-   **Application Won't Start**: Ensure Docker Desktop is running. The application will automatically download the Docker image if needed
-   **Container Issues**: Run `docker system prune` to clean up old containers and images, then try again
-   **Permission Issues**: The application automatically handles user ID mapping for proper file permissions

### Update Issues
-   **Update Detection Fails**: Ensure you have internet connection and Git is properly installed
-   **Docker Image Download Fails**: Check your internet connection and ensure Docker Desktop is running
-   **Script Update Fails**: Verify internet connection and that Git can access GitHub

### Platform-Specific Issues

**macOS:**
-   **Docker Desktop Won't Start**: Check that you downloaded the correct version (Apple Silicon vs Intel)
-   **Python Command Issues**: Use `python3 run.py` instead of `python run.py` on macOS

**Windows:**
-   **WSL 2 Issues**: Ensure WSL 2 is enabled and updated. Run `wsl --update` in Command Prompt as Administrator
-   **Antivirus Blocking**: Some antivirus software may block Docker. Add Docker Desktop to your antivirus exceptions
-   **Path Issues**: If commands aren't found, restart your terminal after installation to refresh the PATH

### Getting Help
If you continue to experience issues:
1. Ensure all prerequisites (Docker, Git, Python 3.10+) are properly installed
2. Restart your computer after installing prerequisites
3. Try running the application again
4. Check the application logs for specific error messages

---

## Deterministic Build System

This application uses a **deterministic Docker build strategy** for maximum reliability:

- **Pinned Base Images**: Uses exact SHA hashes instead of floating tags
- **Exact Package Versions**: All dependencies locked to specific versions via `conda-lock.txt` and `requirements-lock.txt`
- **Reproducible Builds**: Identical environments regardless of when/where built
- **Scientific Reproducibility**: Ensures consistent results across all deployments
- **Compatibility Fix**: Resolves SQLAlchemy/SQLite library compatibility issues