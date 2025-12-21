# SIP LIMS Workflow Manager - Quick Setup Guide

## 1. Prerequisites: Install Docker

This application uses **Docker** with deterministic builds to ensure a consistent and reproducible environment across all platforms.

### On macOS:
1.  **Download Docker Desktop:** Go to [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) and download the installer that matches your Mac's processor:
    *   For newer Macs (M1, M2, M3), choose the **"Apple Silicon"** version.
    *   For older, Intel-based Macs, choose the **"Intel Chip"** version.
2.  **Install Docker Desktop:** Double-click the downloaded `.dmg` file and drag Docker to your Applications folder.
3.  **Start Docker Desktop:** Launch Docker Desktop from your Applications folder and follow the setup wizard.
4.  **Verify Docker is running:** Look for the Docker whale icon in your menu bar.

### Verify Installation
Open a new terminal and type:
```bash
docker --version
```
You should see output like `Docker version 24.x.x`. If you see an error, Docker is not running properly.

## Deterministic Build System

This application uses a **deterministic Docker build strategy** for maximum reliability:

- **Pinned Base Images**: Uses exact SHA hashes instead of floating tags
- **Exact Package Versions**: All dependencies locked to specific versions via `conda-lock.txt` and `requirements-lock.txt`
- **Reproducible Builds**: Identical environments regardless of when/where built
- **Scientific Reproducibility**: Ensures consistent results across all deployments
- **Compatibility Fix**: Resolves SQLAlchemy/SQLite library compatibility issues

---

## 2. Application Setup

This project uses an intelligent Docker-based update system that automatically manages both the application container and Python scripts.

### Standard User Setup (Production Mode)

This is the default, automated setup for all standard users.

1.  **Download and Extract**:
    *   Download the latest `sip_lims_workflow_manager` .zip file from GitHub.
    *   Extract it to a permanent location (e.g., your Desktop or Documents folder).

2.  **No Setup Script Required**:
    *   Docker handles all environment setup automatically
    *   The deterministic Docker image contains all dependencies with exact versions

---

## 3. Launching the Application

-   Double-click `run.command`.

### For Production Users:
-   **Automatic Docker Updates**: The application silently checks and downloads the latest deterministic Docker images from GitHub Container Registry
-   **Automatic Script Updates**: Python scripts are automatically updated from GitHub
-   **No User Prompts**: Completely automated experience
-   **Centralized Management**: Scripts are automatically managed in `~/.sip_lims_workflow_manager/scripts`
-   **Deterministic Environment**: Exact same package versions every time

### For Developers:
-   **Mode Detection**: Automatically detects `config/developer.marker` file
-   **Workflow Choice**: Choose between:
    - **Production Mode (1)**: Auto-updates enabled, uses pre-built deterministic Docker images
    - **Development Mode (2)**: Uses local Docker build with deterministic Dockerfile, drag-and-drop local script folder selection

The application will open in your web browser at `http://127.0.0.1:8501`.

### Docker Container Features:
-   **Deterministic Builds**: Same exact environment every time using pinned package versions
-   **Automatic Cleanup**: Old containers and images are automatically cleaned up
-   **Volume Mounting**: Your project data and scripts are safely mounted from your host system
-   **User ID Mapping**: Proper file permissions for shared network drives

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
-   **Deterministic Docker Images**: Automatically updated every time you run `run.command`
-   **Python Scripts**: Automatically updated every time you run `run.command`
-   **No Manual Action Required**: Updates happen silently in the background
-   **Reproducible Updates**: Each update uses exact package versions for consistency

### Manual Updates (Application Core)
1.  **Download the New Version**: When notified of an update, download the new `sip_lims_workflow_manager` .zip file.
2.  **Replace the Old Folder**: Close the application, delete your old `sip_lims_workflow_manager` folder, and replace it with the new one.
3.  **No Setup Required**: Docker handles all environment setup automatically.

### Developer Updates
-   **Production Mode**: Same automatic deterministic updates as regular users
-   **Development Mode**: Uses local deterministic Docker build - manage your local scripts manually

---

## Troubleshooting

-   **`docker: command not found`**: Docker Desktop was not installed correctly. Please reinstall it, ensuring you follow the instructions above.
-   **Docker Not Running**: If you see "Docker is not running" error, start Docker Desktop from your Applications folder.
-   **Application Won't Start**: Ensure Docker Desktop is running. The application will automatically build the deterministic Docker image if needed.
-   **Container Issues**: Run `docker system prune` to clean up old containers and images, then try again.
-   **Permission Issues**: The application automatically handles user ID mapping for proper file permissions.

### Deterministic Build Troubleshooting
-   **Build Failures**: If Docker build fails, ensure `conda-lock.txt` and `requirements-lock.txt` files are present.
-   **Package Conflicts**: The deterministic build uses exact package versions to prevent conflicts.
-   **Environment Issues**: Unlike Conda environments, Docker containers are completely isolated and reproducible.