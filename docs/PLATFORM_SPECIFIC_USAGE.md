# Platform-Specific Usage Guide

## Overview

The SIP LIMS Workflow Manager provides platform-specific run scripts to ensure optimal compatibility and user experience across different operating systems.

## Available Run Scripts

### macOS Users
- **File**: [`run.mac.command`](../run.mac.command)
- **Usage**: Double-click the file to launch
- **Features**: Full branch-aware Docker functionality with automatic updates

### Windows Users
- **File**: [`run.windows.bat`](../run.windows.bat)
- **Usage**: Double-click the file to launch
- **Features**: Full branch-aware Docker functionality with automatic updates

## Functionality

Both platform-specific scripts provide identical functionality:

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

### For macOS:
1. Open Terminal and navigate to the project directory
2. Double-click `run.mac.command`
3. Follow the prompts to select your project folder

### For Windows:
1. Open Command Prompt and navigate to the project directory
2. Double-click `run.windows.bat`
3. Follow the prompts to select your project folder

## Troubleshooting

### macOS Issues
- **Permission Denied**: Right-click `run.mac.command` and select "Open" to bypass Gatekeeper
- **Docker Not Found**: Ensure Docker Desktop is installed and running

### Windows Issues
- **Script Won't Run**: Ensure you have Python 3.10+ and Git installed
- **Docker Not Found**: Ensure Docker Desktop is installed and running

## Technical Details

### Dependencies
Both scripts require:
- Docker Desktop (running)
- Git (for branch detection)
- Python 3.10+ (for update detection and branch utilities)

### Environment Variables
The scripts automatically set these environment variables:
- `DOCKER_IMAGE`: Branch-specific image name
- `PROJECT_PATH`: Your selected project directory
- `SCRIPTS_PATH`: Location of workflow scripts
- `APP_ENV`: `production` or `development`

### Branch Detection
The scripts use the Python utilities in [`utils/branch_utils.py`](../utils/branch_utils.py) to:
- Detect the current Git branch
- Generate Docker-compatible tags
- Create branch-specific image names

## Migration from Legacy Scripts

If you were previously using:
- `run.command` → Use `run.mac.command`
- `run.bat` → Use `run.windows.bat`

The new scripts provide enhanced functionality while maintaining backward compatibility.