# Robust Automatic Update Detection System Design

## Overview
This document outlines the complete design for a robust automatic update detection system for the Docker-based workflow manager with dual repository structure.

## Current System Problems
1. **Repository Confusion**: Dev and prod modes point to the same GitHub repository
2. **Docker Context Issues**: Git operations fail inside container due to missing .git directories
3. **Path Problems**: Update checks try to access repositories that aren't properly mounted
4. **Network/Access Issues**: Container can't perform Git operations on host repositories

## Design Solution

### Core Architecture
- **Update Detection Location**: Host system (before container starts)
- **Update Frequency**: Check on launch only (not continuous polling)
- **Dual Repository Management**: Separate handling for workflow manager vs Python scripts
- **Platform Support**: Separate run scripts per OS (run.command for Mac, run.bat for Windows)

### User Modes

#### 1. Production Users (Regular Users)
**Workflow Manager Updates:**
- Use pre-built Docker images from GitHub Container Registry
- Auto-pull latest image during launch
- Silent updates (no user intervention required)

**Python Scripts Updates:**
- Auto-download/update to standard location: `~/.sip_lims_workflow_manager/scripts` (Mac/Linux) or `%USERPROFILE%\.sip_lims_workflow_manager\scripts` (Windows)
- Mount this location to `/workflow-scripts` in container
- Silent updates (no user intervention required)

#### 2. Developer Production Mode
- Same behavior as production users
- Auto-updates both workflow manager and scripts
- Triggered when developer chooses "Production mode" from run script prompt

#### 3. Developer Development Mode
**Workflow Manager:**
- Build from local source code (current directory)
- No auto-updates from remote

**Python Scripts:**
- User provides local development scripts path via drag-drop
- No auto-updates from remote
- Mount user-specified path to `/workflow-scripts` in container

### Update Detection Flow

#### Production Mode Flow
1. **Check Developer Marker**: Look for `config/developer.marker` file
2. **If No Marker (Regular User)**: Proceed with production flow
3. **If Marker Exists (Developer)**: Prompt for Production vs Development mode
4. **Production Mode Selected**: 
   - Check for workflow manager updates (GitHub releases/tags)
   - Check for Python scripts updates (GitHub releases/tags)
   - Auto-update both if newer versions available
   - Continue with container launch

#### Development Mode Flow
1. **Developer Marker Detected**: Prompt for mode selection
2. **Development Mode Selected**:
   - Skip all auto-updates
   - Prompt for local Python scripts path (drag-drop)
   - Build workflow manager from local source
   - Continue with container launch

### Error Handling Strategy

#### Network Failures
- **Behavior**: Show warning but continue with existing versions
- **Message**: "Unable to check for updates (network issue). Continuing with current versions."
- **Rationale**: Don't block user productivity

#### Missing Scripts Folder
- **Detection**: Check if `~/.sip_lims_workflow_manager/scripts` exists and contains Python files
- **Behavior**: Auto-download latest scripts if missing/empty
- **Applies To**: First-time users, accidental deletions, corrupted folders

#### Partial Update Failures
- **Scenario**: One update succeeds, other fails (e.g., Docker pulls but scripts download fails)
- **Behavior**: 
  - Retry failed update once
  - If retry fails, continue with mixed versions
  - Show clear warning about which component failed to update
- **Rationale**: Updates are independent; mixed versions are acceptable

### Technical Implementation Details

#### GitHub Integration
- **Workflow Manager**: Use Docker image labels with commit SHAs for version detection
- **Python Scripts**: Use commit SHA comparison via GitHub API
- **Version Detection**: Compare local commit SHA with remote latest commit SHA
- **Download Method**:
  - Docker images: Pull from GitHub Container Registry with automatic labeling
  - Scripts: Download latest commit as zip/tarball from GitHub API

#### Path Management
- **Cross-Platform**: Handle OS-specific paths in respective run scripts
- **Absolute Paths**: Use standard user directory locations to avoid relative path issues
- **Volume Mounting**: Mount host scripts directory to `/workflow-scripts` in container

#### Version Tracking
- **Local Version**: Store current commit SHA in local files and Docker image labels
- **Remote Version**: Query GitHub API for latest commit SHA on main branch
- **Comparison**: Direct SHA comparison (exact match or different)
- **Benefits**: Always accurate, automatic, no manual tagging required

### Configuration Structure

#### Developer Detection
```
config/
├── developer.marker    # Presence indicates developer machine
└── version.json       # Local version tracking (fallback)
```

#### Scripts Location (Production)
```
~/.sip_lims_workflow_manager/
├── scripts/           # Auto-managed Python scripts
│   ├── script1.py
│   ├── script2.py
│   └── ...
└── commit_sha.txt     # Current commit SHA for scripts
```

### User Experience

#### Production Users
1. Run `./run.command` (or `run.bat`)
2. System automatically checks for updates
3. Updates download silently in background
4. Container starts with latest versions
5. User sees brief status messages during update process

#### Developers
1. Run `./run.command` (or `run.bat`)
2. System detects developer marker
3. Prompt: "Production mode" or "Development mode"
4. **If Production**: Same as production users
5. **If Development**: 
   - Prompt for local scripts path
   - Build from local source
   - No auto-updates

### Benefits of This Design

1. **Reliability**: Host-based updates avoid Docker context issues
2. **Flexibility**: Supports both production and development workflows
3. **User-Friendly**: Silent updates for production users, full control for developers
4. **Robust Error Handling**: Graceful degradation when updates fail
5. **Cross-Platform**: Consistent behavior across Mac, Linux, and Windows
6. **Independent Updates**: Workflow manager and scripts can update independently
7. **Predictable Paths**: Standard locations eliminate relative path issues

### Next Steps
1. Implement GitHub Actions for automated Docker image building
2. Modify run scripts to include update detection logic
3. Update docker-compose.yml to use new scripts path
4. Test cross-platform compatibility
5. Create user documentation for new update system