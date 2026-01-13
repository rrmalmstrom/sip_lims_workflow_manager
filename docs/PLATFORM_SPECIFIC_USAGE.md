# Unified Python Launcher Guide

## Overview

The SIP LIMS Workflow Manager now uses a single, unified Python launcher ([`run.py`](../run.py)) that works consistently across all operating systems, replacing the previous platform-specific scripts.

## Unified Launcher

### All Platforms (macOS, Windows, Linux)
- **File**: [`run.py`](../run.py)
- **Usage**: `python3 run.py` (or `python run.py` on Windows)
- **Features**: Full branch-aware Docker functionality with automatic updates and cross-platform compatibility

### Key Advantages
- **Single Script**: One launcher for all platforms eliminates maintenance overhead
- **Consistent Experience**: Identical functionality and interface across all operating systems
- **Enhanced Features**: Rich CLI interface with colored output and better error handling
- **Command Line Support**: Full argument parsing for automation and scripting

## Functionality

The unified Python launcher provides comprehensive functionality:

### 🌿 Branch-Aware Operation
- Automatically detects your current Git branch
- Uses branch-specific Docker images for isolation
- Supports both development and production workflows

### 🔄 Automatic Updates
- Checks for Docker image updates before launching
- Downloads and updates workflow scripts automatically
- Ensures you always have the latest features and fixes

### 🔧 Developer vs Production Modes
- **Production Mode**: Automatic updates, centralized scripts
- **Developer Mode**: Local scripts, no auto-updates, choice of workflow

### 🐳 Container Management
- Automatically stops any running workflow containers
- Cleans up old Docker images to save disk space
- Manages volume mounting for project and script directories

## Quick Start

### All Platforms:
1. Open Terminal (macOS/Linux) or Command Prompt (Windows)
2. Navigate to the project directory
3. Run: `python3 run.py` (or `python run.py` on Windows)
4. Follow the interactive prompts


## Troubleshooting

### Common Issues
- **`python3: command not found`**: Use `python run.py` instead (common on Windows)
- **Import errors**: Ensure you're running from the project root directory
- **Docker Not Found**: Ensure Docker Desktop is installed and running
- **Git errors**: Ensure Git is installed and the directory is a Git repository

### Platform-Specific Notes

#### macOS
- Use `python3 run.py` (Python 3 is typically installed as `python3`)
- No special permissions needed (unlike the old `.command` files)

#### Windows
- May use either `python run.py` or `python3 run.py` depending on installation
- Ensure Python was added to PATH during installation

#### Linux
- Use `python3 run.py`
- Ensure Docker is installed and the user is in the `docker` group

## Technical Details

### Dependencies
The unified launcher requires:
- Docker Desktop (running)
- Git (for branch detection)
- Python 3.10+ (for the launcher itself)

### Environment Variables
The launcher automatically sets these environment variables:
- `DOCKER_IMAGE`: Branch-specific image name
- `PROJECT_PATH`: Your selected project directory
- `SCRIPTS_PATH`: Location of workflow scripts
- `APP_ENV`: `production` or `development`
- `USER_ID` / `GROUP_ID`: For proper file permissions

### Cross-Platform Features
- **Path Normalization**: Handles drag-and-drop paths across all platforms
- **Docker Command Detection**: Automatically detects `docker compose` vs `docker-compose`
- **User ID Mapping**: Proper file permissions on Unix-like systems
- **Colored Output**: Rich terminal interface with fallback for systems without Click

### Branch Detection
The launcher uses the Python utilities in [`utils/branch_utils.py`](../utils/branch_utils.py) to:
- Detect the current Git branch
- Generate Docker-compatible tags
- Create branch-specific image names

## Migration from Legacy Scripts

If you were previously using platform-specific scripts:
- `run.mac.command` → Use `python3 run.py`
- `run.windows.bat` → Use `python run.py`

### Benefits of Migration:
- **Unified Experience**: Same interface across all platforms
- **Enhanced Features**: Better error handling, colored output, command-line arguments
- **Easier Maintenance**: Single script to maintain instead of multiple platform-specific versions
- **Future-Proof**: Easier to add new features and improvements

### Legacy Script Support:
The old platform-specific scripts are still available for backward compatibility, but the unified Python launcher is recommended for all new usage.