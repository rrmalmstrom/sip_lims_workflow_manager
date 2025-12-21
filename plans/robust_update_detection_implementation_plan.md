# Robust Update Detection System - Complete Implementation Plan

## Overview
This document provides a comprehensive implementation plan for the robust update detection system, including all gap analysis findings and cross-platform requirements. This plan bridges the gap between architectural design and actual code implementation.

## Critical Gaps Identified and Addressed

### Missing Windows Platform Support
**Major Gap:** Windows platform has incomplete implementation
- **setup.bat**: Referenced in docs but **DOES NOT EXIST**
- **run.bat**: Uses different architecture (direct Docker vs docker-compose)
- **Update detection**: No Windows batch script equivalent

### Architecture Inconsistencies
**Problem:** Platform-specific differences in container management
- **macOS**: Uses `docker-compose up`
- **Windows**: Uses `docker run` with manual volume mounting
- **Impact**: Different user experiences across platforms

### Setup Script Conflicts
**Issue:** Current setup.command conflicts with new centralized approach
- Still sets up external repositories (`../sip_scripts_prod`)
- No integration with new `~/.sip_lims_workflow_manager/scripts` approach

## Current System Analysis

### Existing Files Analysis

#### 1. [`run.command`](../run.command) - Current State
**Current Functionality:**
- Developer mode detection via [`config/developer.marker`](../config/developer.marker)
- Script path selection (dev vs prod)
- Docker environment setup
- Project path selection via drag-drop

**Required Changes:**
- Add host-based update detection before Docker launch
- Implement production user auto-update logic
- Add scripts download/update functionality
- Modify for new scripts path structure

#### 2. [`docker-compose.yml`](../docker-compose.yml) - Current State
**Current Functionality:**
- Mounts `${SCRIPTS_PATH}` to `/workflow-scripts`
- Uses relative script paths (`../sip_scripts_dev`, `../sip_scripts_prod`)

**Required Changes:**
- Update default scripts path to `~/.sip_lims_workflow_manager/scripts`
- Add support for production user script management
- Maintain developer mode compatibility

#### 3. [`Dockerfile`](../Dockerfile) - Current State
**Current Functionality:**
- Basic application container setup
- No version labeling system

**Required Changes:**
- Add commit SHA labeling for version tracking
- Add build-time version arguments
- Support GitHub Actions automated builds

#### 4. [`src/git_update_manager.py`](../src/git_update_manager.py) - Current State
**Current Functionality:**
- Git-based update checking for both app and scripts
- Designed for repository-based updates

**Required Changes:**
- Remove container-based update logic (move to host)
- Add Docker image update detection
- Add scripts download/extraction functionality

#### 5. [`app.py`](../app.py) - Current State
**Current Functionality:**
- Container-based update checking UI
- Script path parsing from arguments

**Required Changes:**
- Remove update checking UI (handled by host)
- Simplify to focus on workflow management
- Remove git update manager integration

## Complete File Requirements

### New Files Required (Critical Gaps)
1. **`setup.bat`** - Windows setup script (MISSING - referenced in docs but doesn't exist)
2. **`scripts/update_detection.bat`** - Windows update detection
3. **`.github/workflows/docker-build.yml`** - GitHub Actions workflow
4. **`scripts/update_detection.sh`** - macOS/Linux update detection
5. **`scripts/migrate_to_new_system.sh`** - Migration script
6. **`scripts/migrate_windows.bat`** - Windows migration script

### Major File Modifications Required
1. **[`run.bat`](../run.bat)** - Convert from `docker run` to `docker-compose` (architecture mismatch)
2. **[`setup.command`](../setup.command)** - Remove external repos, focus on Conda environment only
3. **[`run.command`](../run.command)** - Add update detection integration
4. **[`docker-compose.yml`](../docker-compose.yml)** - Update scripts path defaults
5. **[`Dockerfile`](../Dockerfile)** - Add version labeling
6. **[`app.py`](../app.py)** - Remove update UI, simplify

## Implementation Plan

### Phase 1: Windows Platform Foundation (Critical Gap)

#### 1.1 Create Missing setup.bat
**Status:** MISSING FILE - Referenced throughout documentation but doesn't exist
**Impact:** Windows users cannot set up the application
**File:** `setup.bat` (NEW)

```batch
@echo off
rem Windows equivalent of setup.command
rem Must implement:
rem - Mode detection (config\developer.marker)
rem - Conda environment setup
rem - Script repository management (transitional)
rem - Developer/production mode handling
```

#### 1.2 Fix run.bat Architecture Mismatch
**Problem:** [`run.bat`](../run.bat) uses `docker run` while [`run.command`](../run.command) uses `docker-compose`
**Impact:** Different user experiences across platforms
**Required:** Convert to docker-compose architecture

#### 1.3 Windows Update Detection
**File:** `scripts/update_detection.bat` (NEW)
**Requirements:** Windows batch equivalent of all update functions

```batch
@echo off
rem Windows equivalent of update_detection.sh
rem Must implement:
rem - GitHub API access using Windows tools
rem - Docker image management
rem - Scripts download/extraction to %USERPROFILE%\.sip_lims_workflow_manager
rem - Cross-platform path handling
```

### Phase 2: GitHub Actions Setup

#### 1.1 Create GitHub Actions Workflow
**File:** `.github/workflows/docker-build.yml`

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Get commit SHA
      id: commit
      run: echo "sha=$(git rev-parse HEAD)" >> $GITHUB_OUTPUT

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: |
          ${{ steps.meta.outputs.labels }}
          org.opencontainers.image.revision=${{ steps.commit.outputs.sha }}
          com.sip-lims.commit-sha=${{ steps.commit.outputs.sha }}
          com.sip-lims.build-date=${{ github.event.head_commit.timestamp }}
        build-args: |
          APP_VERSION=${{ github.ref_name }}
          COMMIT_SHA=${{ steps.commit.outputs.sha }}
```

#### 1.2 Update Dockerfile for Version Labeling
**File:** [`Dockerfile`](../Dockerfile)

**Changes Required:**
```dockerfile
# Add after existing ARG declarations (around line 6)
ARG COMMIT_SHA=unknown
ARG BUILD_DATE=unknown

# Add after existing ENV declarations (around line 8)
ENV COMMIT_SHA=${COMMIT_SHA}
ENV BUILD_DATE=${BUILD_DATE}

# Add labels before WORKDIR (around line 25)
LABEL org.opencontainers.image.revision="${COMMIT_SHA}" \
      com.sip-lims.commit-sha="${COMMIT_SHA}" \
      com.sip-lims.build-date="${BUILD_DATE}" \
      com.sip-lims.version="${APP_VERSION}"
```

### Phase 2: Host-Based Update Detection Scripts

#### 2.1 Create Update Detection Library
**File:** `scripts/update_detection.sh`

```bash
#!/bin/bash
# Host-based update detection for SIP LIMS Workflow Manager

# Configuration
SCRIPTS_REPO_URL="https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git"
SCRIPTS_LOCAL_PATH="$HOME/.sip_lims_workflow_manager/scripts"
SCRIPTS_COMMIT_FILE="$HOME/.sip_lims_workflow_manager/commit_sha.txt"
DOCKER_IMAGE="ghcr.io/rrmalmstrom/sip_lims_workflow_manager"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if running on macOS or Linux
detect_platform() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        *)       echo "unknown" ;;
    esac
}

# Get current Docker image commit SHA
get_current_docker_commit() {
    local image_id=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" | grep "sip-lims-workflow-manager:latest" | awk '{print $2}')
    if [ -n "$image_id" ]; then
        docker inspect "$image_id" --format '{{index .Config.Labels "com.sip-lims.commit-sha"}}' 2>/dev/null || echo "unknown"
    else
        echo "none"
    fi
}

# Get latest Docker image commit SHA from registry
get_latest_docker_commit() {
    local latest_tag=$(curl -s "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager/releases/latest" | grep '"tag_name"' | cut -d'"' -f4)
    if [ -n "$latest_tag" ]; then
        # Get commit SHA for the latest tag
        curl -s "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager/git/refs/tags/$latest_tag" | grep '"sha"' | cut -d'"' -f4
    else
        echo "unknown"
    fi
}

# Check for Docker image updates
check_docker_updates() {
    log "Checking for workflow manager updates..."
    
    local current_commit=$(get_current_docker_commit)
    local latest_commit=$(get_latest_docker_commit)
    
    if [ "$current_commit" = "none" ]; then
        log "No local Docker image found - will pull latest"
        return 0  # Update needed
    elif [ "$current_commit" = "unknown" ] || [ "$latest_commit" = "unknown" ]; then
        log "Warning: Could not determine version information"
        return 1  # No update (continue with existing)
    elif [ "$current_commit" != "$latest_commit" ]; then
        log "Update available: $current_commit -> $latest_commit"
        return 0  # Update needed
    else
        log "Workflow manager is up to date ($current_commit)"
        return 1  # No update needed
    fi
}

# Update Docker image
update_docker_image() {
    log "Updating workflow manager Docker image..."
    
    if docker pull "$DOCKER_IMAGE:latest"; then
        log "✅ Workflow manager updated successfully"
        return 0
    else
        log "❌ Failed to update workflow manager"
        return 1
    fi
}

# Get current scripts commit SHA
get_current_scripts_commit() {
    if [ -f "$SCRIPTS_COMMIT_FILE" ]; then
        cat "$SCRIPTS_COMMIT_FILE"
    else
        echo "none"
    fi
}

# Get latest scripts commit SHA
get_latest_scripts_commit() {
    curl -s "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui/commits/main" | grep '"sha"' | head -1 | cut -d'"' -f4
}

# Check for scripts updates
check_scripts_updates() {
    log "Checking for scripts updates..."
    
    local current_commit=$(get_current_scripts_commit)
    local latest_commit=$(get_latest_scripts_commit)
    
    if [ "$current_commit" = "none" ]; then
        log "No local scripts found - will download latest"
        return 0  # Update needed
    elif [ -z "$latest_commit" ]; then
        log "Warning: Could not check for scripts updates"
        return 1  # No update (continue with existing)
    elif [ "$current_commit" != "$latest_commit" ]; then
        log "Scripts update available: $current_commit -> $latest_commit"
        return 0  # Update needed
    else
        log "Scripts are up to date ($current_commit)"
        return 1  # No update needed
    fi
}

# Download and extract scripts
update_scripts() {
    log "Updating scripts..."
    
    # Create directory structure
    mkdir -p "$(dirname "$SCRIPTS_LOCAL_PATH")"
    
    # Get latest commit SHA
    local latest_commit=$(get_latest_scripts_commit)
    if [ -z "$latest_commit" ]; then
        log "❌ Could not determine latest scripts version"
        return 1
    fi
    
    # Download latest scripts as zip
    local temp_zip="/tmp/sip_scripts_${latest_commit}.zip"
    if curl -L -o "$temp_zip" "https://github.com/rrmalmstrom/sip_scripts_workflow_gui/archive/main.zip"; then
        # Remove existing scripts directory
        rm -rf "$SCRIPTS_LOCAL_PATH"
        
        # Extract to temporary location
        local temp_dir="/tmp/sip_scripts_extract_$$"
        mkdir -p "$temp_dir"
        
        if unzip -q "$temp_zip" -d "$temp_dir"; then
            # Move extracted content to final location
            mv "$temp_dir"/sip_scripts_workflow_gui-main "$SCRIPTS_LOCAL_PATH"
            
            # Save commit SHA
            echo "$latest_commit" > "$SCRIPTS_COMMIT_FILE"
            
            # Cleanup
            rm -rf "$temp_dir" "$temp_zip"
            
            log "✅ Scripts updated successfully to $latest_commit"
            return 0
        else
            log "❌ Failed to extract scripts"
            rm -rf "$temp_dir" "$temp_zip"
            return 1
        fi
    else
        log "❌ Failed to download scripts"
        return 1
    fi
}

# Main update check function
check_and_update() {
    local mode="$1"  # "production" or "development"
    local force_update="$2"  # "true" to force updates
    
    log "Starting update check (mode: $mode)"
    
    if [ "$mode" = "production" ]; then
        # Production mode: auto-update both components
        local docker_update_needed=false
        local scripts_update_needed=false
        
        # Check for updates
        if [ "$force_update" = "true" ] || check_docker_updates; then
            docker_update_needed=true
        fi
        
        if [ "$force_update" = "true" ] || check_scripts_updates; then
            scripts_update_needed=true
        fi
        
        # Perform updates
        if [ "$docker_update_needed" = "true" ]; then
            if ! update_docker_image; then
                log "Warning: Docker update failed, continuing with existing image"
            fi
        fi
        
        if [ "$scripts_update_needed" = "true" ]; then
            if ! update_scripts; then
                log "Warning: Scripts update failed, continuing with existing scripts"
                # Ensure scripts directory exists with fallback
                if [ ! -d "$SCRIPTS_LOCAL_PATH" ]; then
                    log "Creating fallback scripts directory"
                    mkdir -p "$SCRIPTS_LOCAL_PATH"
                fi
            fi
        fi
        
        # Set scripts path for production
        export SCRIPTS_PATH="$SCRIPTS_LOCAL_PATH"
        
    else
        # Development mode: no auto-updates
        log "Development mode: skipping auto-updates"
    fi
    
    log "Update check completed"
}

# Validate scripts directory
validate_scripts_directory() {
    if [ ! -d "$SCRIPTS_PATH" ]; then
        log "❌ Scripts directory not found: $SCRIPTS_PATH"
        return 1
    fi
    
    # Check for Python files
    if [ -z "$(find "$SCRIPTS_PATH" -name "*.py" -type f | head -1)" ]; then
        log "❌ No Python scripts found in: $SCRIPTS_PATH"
        return 1
    fi
    
    log "✅ Scripts directory validated: $SCRIPTS_PATH"
    return 0
}
```

#### 2.2 Update run.command
**File:** [`run.command`](../run.command)

**Complete replacement required:**

```bash
#!/bin/bash
# Enhanced SIP LIMS Workflow Manager Docker Runner with Robust Update Detection
# Implements host-based update detection as per robust_update_detection_design.md

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager (Docker) ---"

# Source update detection functions
source "$DIR/scripts/update_detection.sh"

# Auto-detect host user ID for proper file permissions on shared drives
detect_user_ids() {
    export USER_ID=$(id -u)
    export GROUP_ID=$(id -g)
    echo "Detected User ID: $USER_ID, Group ID: $GROUP_ID"
}

# Mode Detection Function
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# Developer Mode Script Path Selection
select_developer_script_path() {
    echo "🔧 Developer mode detected"
    echo ""
    echo "Choose your workflow for this session:"
    echo "1) Production mode (auto-update workflow manager and scripts)"
    echo "2) Development mode (use local development setup)"
    echo ""
    printf "Enter choice (1 or 2): "
    read choice
    choice=$(echo "$choice" | tr -d '\r\n' | xargs)
    
    case $choice in
        1)
            echo "✅ Using production mode with auto-updates"
            export DEV_MODE_CHOICE="production"
            return 0
            ;;
        2)
            echo "✅ Using development mode"
            echo ""
            echo "Choose script source for development:"
            echo "1) Development scripts (../sip_scripts_dev)"
            echo "2) Production scripts (../sip_scripts_prod)"
            echo ""
            printf "Enter choice (1 or 2): "
            read dev_choice
            dev_choice=$(echo "$dev_choice" | tr -d '\r\n' | xargs)
            
            case $dev_choice in
                1)
                    SCRIPTS_PATH="../sip_scripts_dev"
                    echo "✅ Using development scripts from: $SCRIPTS_PATH"
                    export APP_ENV="development"
                    ;;
                2)
                    SCRIPTS_PATH="../sip_scripts_prod"
                    echo "✅ Using production scripts from: $SCRIPTS_PATH"
                    export APP_ENV="production"
                    ;;
                *)
                    echo "❌ ERROR: Invalid choice '$dev_choice'. Please enter 1 or 2."
                    echo "Exiting."
                    exit 1
                    ;;
            esac
            
            # Verify script directory exists
            if [ ! -d "$SCRIPTS_PATH" ]; then
                echo "❌ ERROR: Script directory not found: $SCRIPTS_PATH"
                echo "Please run setup.command first to initialize script repositories."
                exit 1
            fi
            
            echo "📁 Script path: $SCRIPTS_PATH"
            export SCRIPTS_PATH
            export DEV_MODE_CHOICE="development"
            return 0
            ;;
        *)
            echo "❌ ERROR: Invalid choice '$choice'. Please enter 1 or 2."
            echo "Exiting."
            exit 1
            ;;
    esac
}

# Production Mode Setup
setup_production_mode() {
    echo "🏭 Production mode - checking for updates..."
    
    # Run update detection and auto-update
    check_and_update "production" "false"
    
    # Validate scripts directory was set up correctly
    if ! validate_scripts_directory; then
        echo "❌ ERROR: Scripts setup failed"
        exit 1
    fi
    
    export APP_ENV="production"
    echo "✅ Production mode ready"
}

# Main execution flow
main() {
    # Call user ID detection
    detect_user_ids
    
    # Detect mode and handle accordingly
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        select_developer_script_path
        
        # If developer chose production mode, run production setup
        if [ "$DEV_MODE_CHOICE" = "production" ]; then
            setup_production_mode
        fi
    else
        setup_production_mode
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running."
        echo "Please start Docker Desktop and try again."
        exit 1
    fi
    
    # Prompt user to provide the project folder path
    echo ""
    echo "Please drag and drop your project folder here, then press Enter:"
    printf "> "
    read PROJECT_PATH
    
    # Clean up the path
    PROJECT_PATH=$(echo "$PROJECT_PATH" | tr -d '\r\n' | sed "s/'//g" | xargs)
    
    # Exit if the path is empty
    if [ -z "$PROJECT_PATH" ]; then
        echo "❌ ERROR: No folder provided. Exiting."
        exit 1
    fi
    
    # Validate that the project path exists and is a directory
    if [ ! -d "$PROJECT_PATH" ]; then
        echo "❌ ERROR: Project folder does not exist or is not a directory: $PROJECT_PATH"
        echo "Please provide a valid folder path."
        exit 1
    fi
    
    echo "✅ Selected project folder: $PROJECT_PATH"
    export PROJECT_PATH
    
    # Launch using docker-compose with user ID mapping
    echo "Launching application with Docker Compose..."
    echo "--- Environment Variables ---"
    echo "USER_ID: $USER_ID"
    echo "GROUP_ID: $GROUP_ID"
    echo "PROJECT_PATH: $PROJECT_PATH"
    echo "SCRIPTS_PATH: $SCRIPTS_PATH"
    echo "APP_ENV: $APP_ENV"
    echo "--- Starting Container ---"
    
    # Use docker-compose for enhanced user ID mapping and volume management
    docker-compose up
    
    echo "Application has been shut down."
}

# Run main function
main "$@"
```

#### 2.3 Create scripts directory
**Directory:** `scripts/`

This directory needs to be created to house the update detection functionality.

### Phase 3: Docker Configuration Updates

#### 3.1 Update docker-compose.yml
**File:** [`docker-compose.yml`](../docker-compose.yml)

**Changes Required:**
```yaml
# Update the scripts volume mount (around line 30)
# FROM:
- type: bind
  source: ${SCRIPTS_PATH:-~/.sip_lims_workflow_manager/scripts}
  target: /workflow-scripts
  bind:
    create_host_path: true

# TO:
- type: bind
  source: ${SCRIPTS_PATH:-${HOME}/.sip_lims_workflow_manager/scripts}
  target: /workflow-scripts
  bind:
    create_host_path: true
```

### Phase 4: Application Simplification

#### 4.1 Remove Update Management from app.py
**File:** [`app.py`](../app.py)

**Lines to Remove:**
- Lines 15, 70-98: Remove git_update_manager import and check_for_updates function
- Lines 88-98: Remove update_scripts function
- Lines 100-123: Remove format_last_check_time function
- Lines 990-1042: Remove entire update status expander section
- Lines 595-601: Remove manual update check button from sidebar

**Replacement for removed update section:**
```python
# Replace the update status expander (lines 990-1042) with:
# Simple status indicator (no update functionality)
with st.expander("ℹ️ System Information", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏠 Application**")
        app_version = os.environ.get('APP_VERSION', 'Unknown')
        commit_sha = os.environ.get('COMMIT_SHA', 'Unknown')
        st.info(f"Version: {app_version}")
        if commit_sha != 'Unknown':
            st.text(f"Commit: {commit_sha[:8]}")
    
    with col2:
        st.markdown("**🔧 Scripts**")
        scripts_path = SCRIPT_PATH
        if scripts_path.exists():
            st.success("✅ Scripts loaded")
            st.text(f"Path: {scripts_path}")
        else:
            st.error("❌ Scripts not found")
    
    st.info("💡 Updates are managed automatically by the host system")
```

#### 4.2 Simplify git_update_manager.py
**File:** [`src/git_update_manager.py`](../src/git_update_manager.py)

**Action:** This file can be significantly simplified or removed entirely since update detection moves to the host. If kept for backward compatibility, remove all Docker-related functionality and focus only on local Git operations for development mode.

### Phase 5: Migration Strategy

#### 5.1 Backward Compatibility
**Approach:** Maintain support for existing developer workflows while adding new production user functionality.

**Developer Mode Changes:**
- Existing developer workflows continue to work
- Add new option for developers to use production mode
- Maintain existing script path selection for development mode

**Production User Changes:**
- New users automatically get the new system
- Existing users will see automatic migration to new scripts location

#### 5.2 Migration Script
**File:** `scripts/migrate_to_new_system.sh`

```bash
#!/bin/bash
# Migration script for existing installations

echo "Migrating to new update detection system..."

# Create new directory structure
mkdir -p "$HOME/.sip_lims_workflow_manager"

# Migrate existing scripts if they exist
if [ -d "../sip_scripts_prod" ]; then
    echo "Migrating existing production scripts..."
    cp -r "../sip_scripts_prod" "$HOME/.sip_lims_workflow_manager/scripts"
    
    # Get current commit SHA if it's a git repo
    if [ -d "../sip_scripts_prod/.git" ]; then
        cd "../sip_scripts_prod"
        git rev-parse HEAD > "$HOME/.sip_lims_workflow_manager/commit_sha.txt"
        cd - > /dev/null
    fi
fi

echo "Migration completed"
```

### Phase 6: Testing Plan

#### 6.1 Unit Tests
**File:** `tests/test_update_detection.py`

```python
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestUpdateDetection(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scripts_path = Path(self.temp_dir) / "scripts"
        self.commit_file = Path(self.temp_dir) / "commit_sha.txt"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_docker_update_detection(self, mock_run):
        """Test Docker image update detection"""
        # Mock docker inspect output
        mock_run.return_value.stdout = "abc123def456"
        mock_run.return_value.returncode = 0
        
        # Test implementation here
        pass
    
    @patch('requests.get')
    def test_scripts_update_detection(self, mock_get):
        """Test scripts update detection"""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"sha": "new_commit_sha"}
        mock_get.return_value = mock_response
        
        # Test implementation here
        pass
    
    def test_scripts_download(self):
        """Test scripts download and extraction"""
        # Test implementation here
        pass
```

#### 6.2 Integration Tests
**File:** `tests/test_integration_update_system.py`

```python
import unittest
import tempfile
import subprocess
from pathlib import Path

class TestUpdateSystemIntegration(unittest.TestCase):
    
    def test_production_mode_flow(self):
        """Test complete production mode update flow"""
        # Test full production user experience
        pass
    
    def test_developer_mode_compatibility(self):
        """Test that developer mode still works"""
        # Test existing developer workflows
        pass
    
    def test_migration_from_old_system(self):
        """Test migration from existing installations"""
        # Test migration script functionality
        pass
```

#### 6.3 User Acceptance Testing
**Scenarios:**
1. **New Production User:** Fresh installation, auto-download of scripts
2. **Existing Production User:** Migration from old system
3. **Developer Production Mode:** Developer choosing production mode
4. **Developer Development Mode:** Existing developer workflow
5. **Network Failure:** Graceful degradation when updates fail
6. **Partial Update Failure:** One component updates, other fails

### Phase 7: Rollback Procedures

#### 7.1 Rollback Strategy
**Approach:** Maintain ability to revert to current system if issues arise.

**Rollback Steps:**
1. Restore original [`run.command`](../run.command) from git history
2. Restore original [`docker-compose.yml`](../docker-compose.yml)
3. Restore original [`app.py`](../app.py) update functionality
4. Remove new scripts directory structure
5. Restore original script path handling

#### 7.2 Rollback Script
**File:** `scripts/rollback_update_system.sh`

```bash
#!/bin/bash
# Rollback script for update system changes

echo "Rolling back to previous update system..."

# Restore original files from git
git checkout HEAD~1 -- run.command
git checkout HEAD~1 -- docker-compose.yml
git checkout HEAD~1 -- app.py

# Remove new directory structure
rm -rf "$HOME/.sip_lims_workflow_manager"

# Remove new scripts
rm -rf scripts/update_detection.sh
rm -rf scripts/migrate_to_new_system.sh

echo "Rollback completed"
```

## Implementation Sequence

### Week 1: Foundation
1. **Day 1-2:** Create GitHub Actions workflow and test Docker builds
2. **Day 3-4:** Implement update detection scripts
3. **Day 5:** Create and test migration script

### Week 2: Integration
1. **Day 1-2:** Update [`run.command`](../run.command) with new logic
2. **Day 3:** Update [`docker-compose.yml`](../docker-compose.yml) and [`Dockerfile`](../Dockerfile)
3. **Day 4-5:** Simplify [`app.py`](../app.py) and test integration

### Week 3: Testing and Refinement
1. **Day 1-2:** Comprehensive testing of all scenarios
2. **Day 3-4:** Bug fixes and refinements
3. **Day 5:** Documentation and rollback procedures

### Week 4: Deployment
1. **Day 1-2:** Staged deployment to test environment
2. **Day 3-4:** Production deployment with monitoring
3. **Day 5:** Post-deployment validation and cleanup

## Success Criteria

### Technical Requirements
- ✅ Host-based update detection working
- ✅ Automatic Docker image updates for production users
- ✅ Automatic scripts download/update for production users
- ✅ Developer mode backward compatibility maintained
- ✅ Error handling for network failures
- ✅ Graceful degradation when updates fail

### User Experience Requirements
- ✅ Silent updates for production users
- ✅ Clear feedback during update process
- ✅ No disruption to existing developer workflows
- ✅ Intuitive mode selection for developers
- ✅ Reliable fallback when updates fail

### Operational Requirements
- ✅ Automated Docker builds via GitHub Actions
- ✅ Proper version labeling with commit SHAs
- ✅ Migration path for existing installations
- ✅ Rollback capability if issues arise
- ✅ Comprehensive testing coverage

## Risk Mitigation

### High-Risk Areas
1. **Docker Registry Access:** Ensure GitHub Container Registry is properly configured
2. **Network Dependencies:** Handle offline scenarios gracefully
3. **File Permissions:** Ensure proper permissions for scripts directory
4. **Migration Issues:** Test migration thoroughly with various existing setups

### Mitigation Strategies
1. **Fallback Mechanisms:** Always continue with existing versions if updates fail
2. **Comprehensive Testing:** Test all user scenarios before deployment
3. **Staged Rollout:** Deploy to test users first
4. **Quick Rollback:** Maintain ability to quickly revert changes

## Conclusion

This implementation plan provides a comprehensive roadmap for implementing the robust update detection system. The plan maintains backward compatibility while introducing significant improvements for production users. The phased approach allows for thorough testing and validation at each step, with clear rollback procedures if issues arise.

The key innovation is moving update detection from the container to the host system, which eliminates the current reliability issues while providing a much better user experience for production users through automatic updates.