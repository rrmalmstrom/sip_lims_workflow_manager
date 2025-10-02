# SIP LIMS Workflow Manager - Quick Setup Guide

## System Requirements

### Required Software
1. **Python 3.9 or higher** - Download from [python.org](https://www.python.org/downloads/)
2. **Git** - Required for script updates (see installation instructions below)

### Git Installation

**Git is NOT included in the Python dependencies and must be installed separately.**

#### On macOS:
```bash
# Option 1: Install via Homebrew (recommended)
brew install git

# Option 2: Download installer
# Visit https://git-scm.com/download/mac and download the installer
```

#### On Windows:
```bash
# Download Git for Windows installer
# Visit https://git-scm.com/download/win and download the installer
# During installation, accept all default settings
```

#### Verify Git Installation:
```bash
git --version
```
You should see output like `git version 2.x.x`

## Installation Steps

### 1. Download the Application
- Download the latest `sip_lims_workflow_manager` .zip file from GitHub
- Extract to a permanent location (Desktop, Documents, etc.)

### 2. Run Setup (One-time only)

#### On macOS:
- Double-click `setup.command`
- Allow permission if prompted
- Wait for setup to complete

#### On Windows:
- Double-click `setup.bat`
- Wait for setup to complete

**What setup does:**
- Downloads workflow scripts from GitHub
- Creates Python virtual environment
- Installs all required dependencies
- Configures SSH keys for script updates

### 3. Launch the Application

#### On macOS:
- Double-click `run.command`

#### On Windows:
- Double-click `run.bat`

The application will open in your web browser at `http://127.0.0.1:8501`

## Quick Start Usage

1. **Load Project**: Click "Browse for Project Folder" in sidebar
2. **Choose Setup**: Select "New Project" or "Existing Work"
3. **Run Steps**: Click "Run" buttons to execute workflow steps
4. **Interactive Scripts**: Use the terminal that appears at the top for script input
5. **Updates**: Use "🔄 Manual Check for Updates" button for script updates

## Troubleshooting

### Script Updates Not Working
- **Check Git**: Run `git --version` in terminal
- **Install Git**: Follow Git installation instructions above
- **Restart App**: Close and reopen the application after installing Git

### Setup Fails
- **Check Python**: Ensure Python 3.9+ is installed
- **Check Internet**: Setup requires internet connection to download scripts
- **Check Permissions**: Ensure you can write to the application directory

### Application Won't Start
- **Check Python**: Run `python3 --version` (macOS) or `python --version` (Windows)
- **Reinstall**: Delete `.venv` folder and run setup again

## Key Features

- **Visual Workflow**: Interactive checklist of all workflow steps
- **Smart Error Handling**: Automatic rollback if scripts fail
- **Undo Functionality**: Revert to previous workflow states
- **Script Updates**: One-click updates for workflow scripts
- **Conditional Workflows**: Yes/No decision prompts for optional steps
- **Skip to Step**: Start workflows from any midway point
- **Real-time Terminal**: Interactive script input/output

## Security

- **Localhost Only**: Application only accessible from your computer
- **Private Data**: All workflow data stays on your local machine
- **SSH Keys**: Included for secure script repository access

## Support

For issues or questions:
1. Check this guide first
2. Verify Git is installed and working
3. Try restarting the application
4. Contact your team administrator

---

**Remember**: Git installation is required for script updates but is not automatically installed with the application dependencies.