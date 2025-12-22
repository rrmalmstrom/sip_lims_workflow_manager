# 10 - Documentation Updates for New Workflow

## Overview
Plan for updating all documentation to reflect the new external script repository structure and developer/production mode workflow.

## Documentation Files Requiring Updates

### 1. User-Facing Documentation
- **README.md** - Main project overview and setup instructions
- **docs/user_guide/QUICK_SETUP_GUIDE.md** - Setup process for end users
- **docs/user_guide/FEATURES.md** - Feature descriptions
- **docs/user_guide/TROUBLESHOOTING.md** - Common issues and solutions

### 2. Developer Documentation
- **docs/developer_guide/** - All developer-specific documentation
- **docs/index.md** - Main documentation index
- **New files needed** - Developer setup and workflow guides

### 3. Technical Documentation
- **docs/developer_guide/ARCHITECTURE.md** - System architecture
- **docs/developer_guide/UPDATE_SYSTEM.md** - Update system documentation
- **New files needed** - Repository structure and mode documentation

## Detailed Update Plans

### README.md Updates

#### Current Structure Analysis
- Lines 1-13: Project description and documentation links ✅ (minimal changes)
- Lines 14-32: Features list (needs mode-specific feature additions)
- Lines 33-53: Prerequisites and setup (needs mode-specific instructions)

#### Required Changes
```markdown
# SIP LIMS Workflow Manager

A simple, lightweight workflow manager for running a series of Python scripts in a SIP (Stable Isotope Probing) laboratory environment.

## 📖 Documentation

For complete and detailed documentation, please see the **[main documentation page](docs/index.md)**.

This includes:
- **[User Guide](docs/user_guide)**: For installation, setup, and usage instructions.
- **[Developer Guide](docs/developer_guide)**: For technical details and development workflow.
- **[Architecture Overview](docs/developer_guide)**: For high-level design and strategy documents.

## Features

### Core Features
- Visual, interactive checklist of workflow steps.
- One-click execution of Python scripts.
- Automatic state tracking with enhanced reliability.
- Robust error handling with automatic rollback and success marker verification.
- **Enhanced Undo functionality** with complete project state restoration.
- **Smart re-run behavior** that always prompts for new file inputs.
- **Skip to Step functionality** for starting workflows from any midway point.
- **Conditional workflow support** with Yes/No decision prompts for optional steps.
- Interactive script support with real-time terminal output.
- Cross-platform support for macOS and Windows.

### NEW: Developer/Production Mode Features
- **🔧 Developer Mode**: Choose between development and production scripts per session
- **🏭 Production Mode**: Automatic script management with production-ready scripts
- **📁 External Script Repositories**: Scripts managed in separate, sibling directories
- **🔄 Flexible Script Sources**: Easy switching between script versions for testing
- **⚙️ Mode Detection**: Automatic environment detection with manual override options

## Prerequisites

- **Miniconda or Anaconda**: This application uses the Conda package manager to ensure a consistent and reproducible environment.
- **Git**: Required for script repository management and updates.

For detailed installation instructions, see the **[Quick Setup Guide](docs/user_guide/QUICK_SETUP_GUIDE.md)**.

## Installation and Setup

### For End Users (Production Mode)
1. **Download the Application**: Download the latest release from GitHub
2. **Run Setup**: Double-click `setup.command` (macOS) or `setup.bat` (Windows)
3. **Launch Application**: Double-click `run.command` (macOS) or `run.bat` (Windows)

### For Developers (Developer Mode)
1. **Clone Repository**: `git clone https://github.com/RRMalmstrom/sip_lims_workflow_manager.git`
2. **Create Developer Marker**: Create `config/developer.marker` file
3. **Run Setup**: Execute setup script and choose online/offline mode
4. **Launch Application**: Execute run script and choose script source

For detailed developer setup, see the **[Developer Setup Guide](docs/developer_guide/DEVELOPER_SETUP.md)**.

## Quick Start

After setup is complete:

### Production Users
- **Launch**: Double-click the `run.command` or `run.bat` file
- **Automatic**: Application uses production scripts automatically
- **Browse**: Select your project folder and start your workflow

### Developers
- **Launch**: Double-click the `run.command` or `run.bat` file
- **Choose**: Select development or production scripts for this session
- **Develop**: Test with development scripts or validate with production scripts

The application interface will open in your web browser at `http://127.0.0.1:8501`.
```

### QUICK_SETUP_GUIDE.md Updates

#### New Sections to Add
```markdown
# SIP LIMS Workflow Manager - Quick Setup Guide

## Overview

This guide covers setup for both **end users** (production mode) and **developers** (development mode). The application automatically detects your environment and provides appropriate options.

## 1. Prerequisites: Install Miniconda

[Existing Miniconda installation instructions remain unchanged]

## 2. Choose Your Setup Type

### For End Users (Production Mode)
If you're using the application for regular workflow management:
- Download the latest release package
- Follow the standard setup process
- Scripts are automatically managed

### For Developers (Development Mode)
If you're developing or testing script modifications:
- Clone the repository from GitHub
- Create a developer marker file
- Choose between development and production scripts

---

## 3. End User Setup (Production Mode)

### Download and Extract
- Download the latest `sip_lims_workflow_manager.zip` from GitHub releases
- Extract to a permanent location (e.g., Desktop or Documents)

### Run Setup Script
- **macOS**: Double-click `setup.command`
- **Windows**: Double-click `setup.bat`

The setup will:
- ✅ Create conda environment
- ✅ Download production scripts automatically
- ✅ Configure update system

### Launch Application
- **macOS**: Double-click `run.command`
- **Windows**: Double-click `run.bat`

The application will:
- ✅ Use production scripts automatically
- ✅ Open in your web browser
- ✅ Be ready for project selection

---

## 4. Developer Setup (Development Mode)

### Clone Repository
```bash
git clone https://github.com/RRMalmstrom/sip_lims_workflow_manager.git
cd sip_lims_workflow_manager
```

### Create Developer Marker
```bash
mkdir -p config
touch config/developer.marker
```

### Run Setup Script
- **macOS**: Double-click `setup.command`
- **Windows**: Double-click `setup.bat`

You'll be prompted to choose:
1. **Work offline** (skip remote repository updates)
2. **Connect to remotes** (download/update both dev and prod scripts)

### Launch Application
- **macOS**: Double-click `run.command`
- **Windows**: Double-click `run.bat`

You'll be prompted to choose script source:
1. **Development scripts** (for testing new features)
2. **Production scripts** (for stable workflow execution)

---

## 5. Understanding the New Structure

### Directory Layout
```
Desktop/
├── sip_lims_workflow_manager/      # Main application
├── sip_scripts_workflow_gui/       # Development scripts (developers only)
└── sip_scripts_production/         # Production scripts (always present)
```

### Mode Detection
- **Developer Mode**: `config/developer.marker` file exists
- **Production Mode**: No marker file present

### Script Selection (Developer Mode Only)
- **Development Scripts**: Latest features, may be unstable
- **Production Scripts**: Stable, tested versions

---

## 6. Troubleshooting

### Common Issues

#### "Script directory not found"
**Solution**: Run the setup script to initialize script repositories
```bash
# macOS
./setup.command

# Windows
setup.bat
```

#### "Failed to activate conda environment"
**Solution**: Ensure Miniconda is properly installed and in PATH

#### Developer mode not detected
**Solution**: Verify `config/developer.marker` file exists
```bash
ls -la config/developer.marker  # macOS/Linux
dir config\developer.marker     # Windows
```

#### Script updates failing
**Solution**: Check internet connection and run setup script again

### Getting Help
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review the [Developer Guide](../developer_guide/) for technical details
- Ensure all prerequisites are properly installed
```

### New Developer Documentation Files

#### docs/developer_guide/DEVELOPER_SETUP.md
```markdown
# Developer Setup Guide

## Overview
This guide is specifically for developers who want to modify scripts, test new features, or contribute to the project.

## Prerequisites
- Git installed and configured
- Miniconda/Anaconda installed
- Basic familiarity with command line operations

## Setup Process

### 1. Clone and Configure
```bash
# Clone the main repository
git clone https://github.com/RRMalmstrom/sip_lims_workflow_manager.git
cd sip_lims_workflow_manager

# Create developer marker
mkdir -p config
echo "Developer: $(whoami)" > config/developer.marker
```

### 2. Run Setup
```bash
# macOS
./setup.command

# Windows
setup.bat
```

Choose option 2 (Connect to remotes) to download both script repositories.

### 3. Verify Setup
After setup, you should have:
```
Desktop/
├── sip_lims_workflow_manager/      # Main app (your working directory)
├── sip_scripts_workflow_gui/       # Development scripts
└── sip_scripts_production/         # Production scripts
```

## Development Workflow

### Daily Development
1. **Launch Application**:
   ```bash
   ./run.command  # macOS
   run.bat        # Windows
   ```

2. **Choose Script Source**:
   - Option 1: Development scripts (for testing your changes)
   - Option 2: Production scripts (for baseline comparison)

3. **Develop and Test**:
   - Modify scripts in `../sip_scripts_workflow_gui/`
   - Test changes using development script option
   - Validate against production scripts

### Script Development
- **Development Scripts**: `../sip_scripts_workflow_gui/`
  - Latest features and experimental code
  - Your testing ground for new functionality
  - May be unstable or incomplete

- **Production Scripts**: `../sip_scripts_production/`
  - Stable, tested versions
  - Used for baseline testing
  - Reference implementation

### Testing Strategy
1. **Develop** in development scripts repository
2. **Test** using development script option in app
3. **Validate** by switching to production scripts
4. **Compare** behavior between versions

## Repository Management

### Updating Repositories
```bash
# Update development scripts
cd ../sip_scripts_workflow_gui
git pull

# Update production scripts  
cd ../sip_scripts_production
git pull

# Return to main app
cd ../sip_lims_workflow_manager
```

### Working Offline
If you need to work without internet:
1. Run setup script
2. Choose option 1 (Work offline)
3. Use existing local repositories

## Troubleshooting

### Developer Mode Not Working
- Verify `config/developer.marker` exists
- Check file permissions
- Restart application

### Script Repositories Missing
- Run setup script with option 2
- Check internet connection
- Verify GitHub access

### Can't Switch Script Sources
- Ensure both repositories exist
- Check repository health with `git status`
- Re-run setup if needed
```

#### docs/developer_guide/REPOSITORY_STRUCTURE.md
```markdown
# Repository Structure and Management

## Overview
The SIP LIMS Workflow Manager uses a multi-repository structure to separate application code from script content and to support different development workflows.

## Repository Layout

### Main Application Repository
**Location**: `sip_lims_workflow_manager/`
**Purpose**: Core application, UI, and workflow management
**Repository**: `https://github.com/RRMalmstrom/sip_lims_workflow_manager.git`

Contains:
- Streamlit application (`app.py`)
- Core workflow engine (`src/`)
- Setup and run scripts
- Documentation
- Configuration templates

### Development Scripts Repository
**Location**: `../sip_scripts_workflow_gui/`
**Purpose**: Development and testing versions of workflow scripts
**Repository**: `https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git`

Contains:
- Latest script versions
- Experimental features
- Development tools
- Testing utilities

### Production Scripts Repository
**Location**: `../sip_scripts_production/`
**Purpose**: Stable, tested versions of workflow scripts
**Repository**: `https://github.com/rrmalmstrom/sip_scripts_production.git`

Contains:
- Stable script versions
- Production-ready code
- Tested configurations
- Release versions

## Mode-Based Behavior

### Production Mode (Default)
- **Detection**: No `config/developer.marker` file
- **Script Source**: Automatically uses production scripts
- **Updates**: Automatic update checks and installations
- **User Experience**: Simplified, no choices required

### Developer Mode
- **Detection**: `config/developer.marker` file exists
- **Script Source**: User chooses per session
- **Updates**: Optional, user-controlled
- **User Experience**: Flexible, choice-driven

## File Structure

### Complete Directory Layout
```
Desktop/
├── sip_lims_workflow_manager/          # Main application
│   ├── app.py                          # Streamlit application
│   ├── src/                            # Core modules
│   │   ├── core.py                     # Project management
│   │   ├── git_update_manager.py       # Update system
│   │   └── logic.py                    # Workflow logic
│   ├── config/                         # Configuration
│   │   └── developer.marker            # Developer mode marker (optional)
│   ├── setup.command / setup.bat       # Setup scripts
│   ├── run.command / run.bat           # Launch scripts
│   └── docs/                           # Documentation
├── sip_scripts_workflow_gui/           # Development scripts (dev mode)
│   ├── script1.py
│   ├── script2.py
│   └── ...
└── sip_scripts_production/             # Production scripts (always)
    ├── script1.py
    ├── script2.py
    └── ...
```

### Configuration Files
- **`config/developer.marker`**: Enables developer mode
- **`.gitignore`**: Excludes developer marker from version control
- **`environment.yml`**: Conda environment specification

## Update Management

### Application Updates
- **Source**: Main application repository
- **Frequency**: User-initiated or automatic (production mode)
- **Scope**: Core application, UI, workflow engine

### Script Updates
- **Source**: Respective script repository (dev or production)
- **Frequency**: User-controlled (dev mode) or automatic (production mode)
- **Scope**: Workflow scripts only

### Update Flow
1. **Check**: Application checks for updates
2. **Download**: Updates downloaded to appropriate repository
3. **Apply**: Changes applied without affecting user projects
4. **Verify**: Update success confirmed

## Development Workflow

### Setting Up Development Environment
1. Clone main application repository
2. Create developer marker file
3. Run setup to initialize script repositories
4. Choose script source when launching

### Making Changes
1. **Scripts**: Modify in development scripts repository
2. **Application**: Modify in main application repository
3. **Test**: Use development script option to test changes
4. **Validate**: Compare with production script behavior

### Repository Synchronization
- **Development Scripts**: Push changes to development repository
- **Production Scripts**: Promote tested changes from development
- **Application**: Standard git workflow for application changes

## Security Considerations

### Developer Marker File
- **Purpose**: Local development identification only
- **Security**: Excluded from version control
- **Content**: Optional, can contain developer information

### Repository Access
- **Public Repositories**: Read access for updates
- **Private Development**: Secure development environment
- **Production Isolation**: Production scripts isolated from development

## Troubleshooting

### Repository Issues
- **Missing Repositories**: Run setup script
- **Update Failures**: Check internet connection and repository access
- **Permission Issues**: Verify git configuration and access rights

### Mode Detection Issues
- **Wrong Mode**: Check for presence/absence of developer marker
- **Mode Switching**: Create/remove marker file and restart application
- **Permissions**: Ensure marker file is readable
```

## Implementation Strategy

### Phase 1: Update Core Documentation
- Update README.md with new features and structure
- Revise QUICK_SETUP_GUIDE.md for both user types
- Update main documentation index

### Phase 2: Create Developer Documentation
- Create DEVELOPER_SETUP.md for development workflow
- Create REPOSITORY_STRUCTURE.md for technical details
- Update existing developer guides

### Phase 3: Update Technical Documentation
- Update ARCHITECTURE.md with new repository structure
- Revise UPDATE_SYSTEM.md for external repositories
- Update troubleshooting guides

### Phase 4: Create Migration Guides
- Create migration guide for existing users
- Document transition from nested to external scripts
- Provide rollback procedures if needed

## Benefits

### For End Users
- ✅ Clear, simple setup instructions
- ✅ No confusion about developer vs production features
- ✅ Focused documentation for their use case

### For Developers
- ✅ Comprehensive development workflow documentation
- ✅ Clear repository structure explanation
- ✅ Detailed troubleshooting for development scenarios

### For Maintenance
- ✅ Organized documentation structure
- ✅ Clear separation of user vs developer content
- ✅ Comprehensive coverage of new features
- ✅ Easy to maintain and update