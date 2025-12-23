# Documentation Archive

This directory contains outdated documentation that has been archived for historical reference.

## Archived Documents

### Refactoring Plan (December 2025)

The `refactoring_plan/` directory contains documentation from the transition period when the application was being converted from a Conda-based local environment setup to a Docker-based containerized workflow.

**Why Archived:**
- These documents describe the old workflow that required users to install Conda/Miniconda locally
- They reference `setup.command` and `setup.bat` scripts that have been removed
- The described architecture no longer matches the current Docker-only implementation

**Current Workflow:**
- Users only need Docker Desktop, Git, and Python 3.10+ installed
- No setup script required - platform-specific run scripts handle everything automatically:
  - **macOS**: [`run.mac.command`](../run.mac.command)
  - **Windows**: [`run.windows.bat`](../run.windows.bat)
- Docker images are pulled from GitHub Container Registry
- See [`docs/user_guide/QUICK_SETUP_GUIDE.md`](../user_guide/QUICK_SETUP_GUIDE.md) for current setup instructions

**Historical Context:**
These documents were created during the architectural transition and provide valuable insight into the design decisions and implementation process that led to the current Docker-based system.