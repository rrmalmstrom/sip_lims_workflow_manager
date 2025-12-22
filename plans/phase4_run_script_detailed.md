# Phase 4: Run Script Enhancement Detail

## Overview
Modify `run.command` to use branch-aware Docker image selection while preserving all existing update detection, mode selection, and container management functionality.

## Critical Requirements
- **PRESERVE** all existing update detection workflow
- **MAINTAIN** developer vs production mode logic
- **KEEP** all container management functions unchanged
- **PRESERVE** environment variable handling for docker-compose

## Current State Analysis

### Key Areas to Modify
- **Line 151**: `export DOCKER_IMAGE="ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"`
- **Line 230**: `export DOCKER_IMAGE="sip-lims-workflow-manager:latest"`
- **Lines 43, 75**: Update detection calls
- **Lines 143, 147**: Scripts path and environment setup

### Functions to Enhance
- `check_docker_updates()` (lines 39-91)
- `production_auto_update()` (lines 133-155)
- `select_development_script_path()` (lines 203-234)

## Required Changes

### 1. Add Branch Detection at Script Start

**Location**: After line 7 (after directory detection)

```bash
#!/bin/bash
# Enhanced SIP LIMS Workflow Manager Docker Runner
# Combines legacy Docker functionality with current ESP features and robust update detection

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Source branch utilities for branch-aware Docker operations
source "$DIR/utils/branch_utils.sh"

# Detect current branch early for consistent behavior
echo "🌿 Detecting current branch for Docker operations..."
CURRENT_BRANCH_TAG=$(get_current_branch_tag)
if [ $? -ne 0 ] || [ -z "$CURRENT_BRANCH_TAG" ]; then
    echo "⚠️  Warning: Branch detection failed, falling back to 'latest'"
    CURRENT_BRANCH_TAG="latest"
fi
echo "   ✅ Branch tag: $CURRENT_BRANCH_TAG"

echo "--- Starting SIP LIMS Workflow Manager (Docker) ---"
```

### 2. Enhance `check_docker_updates()` Function

**Location**: Lines 39-91

```bash
# Update Detection Functions
check_docker_updates() {
    echo "🔍 Checking for Docker image updates..."
    
    # Get branch-aware image names
    local remote_image_name
    remote_image_name=$(get_remote_image_name 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$remote_image_name" ]; then
        echo "⚠️  Warning: Failed to get branch-aware image name, using fallback"
        remote_image_name="ghcr.io/rrmalmstrom/sip_lims_workflow_manager:$CURRENT_BRANCH_TAG"
    fi
    
    echo "   🐳 Checking image: $remote_image_name"
    
    # Use the update detector to check for Docker updates with branch awareness
    local update_result
    update_result=$(python3 src/update_detector.py --check-docker --branch "$CURRENT_BRANCH_TAG" 2>/dev/null)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        # Parse the JSON result to check if update is available
        local update_available
        update_available=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('update_available', False) else 'false')
except:
    print('false')
")
        
        if [ "$update_available" = "true" ]; then
            echo "📦 Docker image update available - updating to latest version..."
            
            # Get current image ID before cleanup (using branch-specific tag)
            local old_image_id
            old_image_id=$(docker images "$remote_image_name" --format "{{.ID}}" 2>/dev/null)
            
            # Clean up old image BEFORE pulling new one (since containers are already stopped)
            if [ -n "$old_image_id" ]; then
                echo "🧹 Removing old Docker image before update..."
                # Remove by tag first, then clean up any dangling images
                docker rmi "$remote_image_name" >/dev/null 2>&1
                # Clean up dangling images to prevent disk space waste
                docker image prune -f >/dev/null 2>&1
                echo "✅ Old Docker image and dangling images cleaned up"
            fi
            
            # Pull the new image
            echo "📥 Pulling latest Docker image..."
            docker pull "$remote_image_name"
            if [ $? -eq 0 ]; then
                echo "✅ Docker image updated successfully"
                return 0
            else
                echo "❌ ERROR: Docker image update failed"
                return 1
            fi
        else
            echo "✅ Docker image is up to date"
            return 0
        fi
    else
        echo "⚠️  Warning: Could not check for Docker updates, continuing with current version"
        return 1
    fi
}
```

### 3. Enhance `production_auto_update()` Function

**Location**: Lines 133-155

```bash
production_auto_update() {
    echo "🏭 Production mode - performing automatic updates..."
    
    # Check and update Docker image
    check_docker_updates
    
    # Set up centralized scripts directory
    local scripts_dir="$HOME/.sip_lims_workflow_manager/scripts"
    
    # Check and download/update scripts
    check_and_download_scripts "$scripts_dir"
    
    # Set scripts path for production use
    SCRIPTS_PATH="$scripts_dir"
    export SCRIPTS_PATH
    export APP_ENV="production"
    
    # Use branch-aware Docker image for production
    local remote_image_name
    remote_image_name=$(get_remote_image_name 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$remote_image_name" ]; then
        echo "⚠️  Warning: Failed to get branch-aware image name, using fallback"
        remote_image_name="ghcr.io/rrmalmstrom/sip_lims_workflow_manager:$CURRENT_BRANCH_TAG"
    fi
    
    export DOCKER_IMAGE="$remote_image_name"
    
    echo "📁 Using centralized scripts: $SCRIPTS_PATH"
    echo "🐳 Using branch-aware Docker image: $DOCKER_IMAGE"
    echo "🌿 Branch tag: $CURRENT_BRANCH_TAG"
}
```

### 4. Enhance `select_development_script_path()` Function

**Location**: Lines 203-234

```bash
# Development Script Path Selection Function
select_development_script_path() {
    echo ""
    echo "Please drag and drop your development scripts folder here, then press Enter:"
    printf "> "
    read SCRIPTS_PATH
    
    # Clean up the path (removes potential quotes, trailing spaces, and control characters)
    SCRIPTS_PATH=$(echo "$SCRIPTS_PATH" | tr -d '\r\n' | sed "s/'//g" | xargs)
    
    # Exit if the path is empty
    if [ -z "$SCRIPTS_PATH" ]; then
        echo "❌ ERROR: No scripts folder provided. Exiting."
        exit 1
    fi
    
    # Validate that the scripts path exists and is a directory
    if [ ! -d "$SCRIPTS_PATH" ]; then
        echo "❌ ERROR: Scripts folder does not exist or is not a directory: $SCRIPTS_PATH"
        echo "Please provide a valid scripts folder path."
        exit 1
    fi
    
    echo "✅ Selected development scripts folder: $SCRIPTS_PATH"
    export SCRIPTS_PATH
    export APP_ENV="development"
    
    # Use branch-aware local Docker build for development mode
    local local_image_name
    local_image_name=$(get_local_image_name 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$local_image_name" ]; then
        echo "⚠️  Warning: Failed to get branch-aware local image name, using fallback"
        local_image_name="sip-lims-workflow-manager:$CURRENT_BRANCH_TAG"
    fi
    
    export DOCKER_IMAGE="$local_image_name"
    
    echo "📁 Script path: $SCRIPTS_PATH"
    echo "🐳 Using branch-aware local Docker build: $DOCKER_IMAGE"
    echo "🌿 Branch tag: $CURRENT_BRANCH_TAG"
}
```

### 5. Update Environment Variable Display

**Location**: Lines 301-307

```bash
# Launch using docker-compose with user ID mapping
echo "Launching application with Docker Compose..."
echo "--- Environment Variables ---"
echo "USER_ID: $USER_ID"
echo "GROUP_ID: $GROUP_ID"
echo "PROJECT_PATH: $PROJECT_PATH"
echo "SCRIPTS_PATH: $SCRIPTS_PATH"
echo "APP_ENV: $APP_ENV"
echo "DOCKER_IMAGE: $DOCKER_IMAGE"
echo "BRANCH_TAG: $CURRENT_BRANCH_TAG"
echo "--- Starting Container ---"
```

### 6. Add Branch Information to Script Updates

**Location**: Modify `check_and_download_scripts()` calls

```bash
check_and_download_scripts() {
    local scripts_dir="$1"
    local branch="${2:-main}"
    
    echo "🔍 Checking for script updates..."
    echo "   📁 Scripts directory: $scripts_dir"
    echo "   🌿 Branch: $branch"
    
    # Check for script updates using the new scripts updater
    local update_result
    update_result=$(python3 src/scripts_updater.py --check-scripts --scripts-dir "$scripts_dir" --branch "$branch" 2>/dev/null)
    local exit_code=$?
    
    # ... rest of function unchanged
}
```

### 7. Add Branch-Aware Error Handling

```bash
# Branch-aware fallback function
get_docker_image_with_fallback() {
    local mode="$1"  # "production" or "development"
    local image_name=""
    
    if [ "$mode" = "production" ]; then
        image_name=$(get_remote_image_name 2>/dev/null)
        if [ $? -ne 0 ] || [ -z "$image_name" ]; then
            echo "⚠️  Warning: Branch-aware remote image detection failed" >&2
            image_name="ghcr.io/rrmalmstrom/sip_lims_workflow_manager:$CURRENT_BRANCH_TAG"
        fi
    else
        image_name=$(get_local_image_name 2>/dev/null)
        if [ $? -ne 0 ] || [ -z "$image_name" ]; then
            echo "⚠️  Warning: Branch-aware local image detection failed" >&2
            image_name="sip-lims-workflow-manager:$CURRENT_BRANCH_TAG"
        fi
    fi
    
    echo "$image_name"
}
```

## Integration with Existing Workflow

### Docker Compose Integration

The existing `docker-compose.yml` already uses the `DOCKER_IMAGE` environment variable:

```yaml
services:
  sip-lims-workflow:
    image: ${DOCKER_IMAGE:-ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest}
```

**No changes needed** - the enhanced `run.command` will set `DOCKER_IMAGE` to the branch-aware value.

### Update Detector Integration

The enhanced `check_docker_updates()` function will:
1. Pass the current branch to the update detector
2. Use branch-specific image names for pulling
3. Preserve all existing SHA comparison logic
4. Maintain the same update workflow

### Mode Detection Integration

The existing mode detection logic remains unchanged:
- Developer marker file detection works as before
- User choice between production/development workflows preserved
- Only the Docker image selection becomes branch-aware

## Error Handling and Fallbacks

### Branch Detection Failures
```bash
# Robust branch detection with multiple fallbacks
detect_branch_with_comprehensive_fallback() {
    local branch_tag=""
    
    # Method 1: Use Python utilities
    branch_tag=$(get_current_branch_tag 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$branch_tag" ]; then
        echo "$branch_tag"
        return 0
    fi
    
    # Method 2: Direct git command
    local git_branch
    git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$git_branch" ] && [ "$git_branch" != "HEAD" ]; then
        # Manual sanitization
        branch_tag=$(echo "$git_branch" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
        echo "$branch_tag"
        return 0
    fi
    
    # Method 3: Check for developer marker and use appropriate default
    if [ -f "config/developer.marker" ]; then
        echo "dev"
    else
        echo "latest"
    fi
    return 0
}
```

### Docker Image Fallbacks
```bash
# Ensure Docker image is always set
ensure_docker_image_set() {
    if [ -z "$DOCKER_IMAGE" ]; then
        echo "⚠️  Warning: DOCKER_IMAGE not set, using fallback" >&2
        
        if [ "$APP_ENV" = "development" ]; then
            DOCKER_IMAGE="sip-lims-workflow-manager:$CURRENT_BRANCH_TAG"
        else
            DOCKER_IMAGE="ghcr.io/rrmalmstrom/sip_lims_workflow_manager:$CURRENT_BRANCH_TAG"
        fi
        
        export DOCKER_IMAGE
        echo "   ✅ Fallback image: $DOCKER_IMAGE" >&2
    fi
}
```

## Test Requirements

### Integration Tests: `tests/test_run_command_branch_aware.py`

```python
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestRunCommandBranchAware:
    def test_production_mode_uses_branch_image(self):
        """Test production mode uses branch-specific remote image"""
        with patch('utils.branch_utils.get_current_branch', return_value='main'):
            # Mock the run.command execution
            result = subprocess.run(['./run.command'], 
                                  input='1\n',  # Choose production mode
                                  capture_output=True, text=True)
            
            # Verify branch-specific image is used
            assert 'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main' in result.stdout

    def test_development_mode_uses_branch_image(self):
        """Test development mode uses branch-specific local image"""
        with patch('utils.branch_utils.get_current_branch', return_value='feature-test'):
            result = subprocess.run(['./run.command'], 
                                  input='2\n/tmp/test-scripts\n',  # Choose dev mode
                                  capture_output=True, text=True)
            
            # Verify branch-specific local image is used
            assert 'sip-lims-workflow-manager:feature-test' in result.stdout

    def test_branch_detection_failure_fallback(self):
        """Test fallback behavior when branch detection fails"""
        with patch('utils.branch_utils.get_current_branch', side_effect=Exception("Git error")):
            result = subprocess.run(['./run.command'], 
                                  input='1\n',  # Choose production mode
                                  capture_output=True, text=True)
            
            # Should fallback to 'latest' tag
            assert 'latest' in result.stdout

    def test_docker_compose_integration(self):
        """Test that DOCKER_IMAGE environment variable is set correctly"""
        with patch('utils.branch_utils.get_current_branch', return_value='main'):
            # Mock docker-compose execution to capture environment
            with patch('subprocess.run') as mock_run:
                subprocess.run(['./run.command'], input='1\n')
                
                # Verify docker-compose was called with correct environment
                env_calls = [call for call in mock_run.call_args_list 
                           if 'docker-compose' in str(call)]
                assert len(env_calls) > 0
```

### Manual Test Scenarios

#### Scenario 1: Main Branch Production
```bash
# Setup
git checkout main
./run.command
# Choose production mode (1)
# Verify: Uses ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main
```

#### Scenario 2: Development Branch
```bash
# Setup
git checkout analysis/esp-docker-adaptation
./run.command
# Choose production mode (1)
# Verify: Uses ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation
```

#### Scenario 3: Branch Switching
```bash
# Start on main
git checkout main
./run.command  # Should use :main image

# Switch branches
git checkout analysis/esp-docker-adaptation
./run.command  # Should use :analysis-esp-docker-adaptation image
```

## Success Criteria

- [ ] Production mode uses branch-specific remote images
- [ ] Development mode uses branch-specific local images
- [ ] Update detection works with branch-aware logic
- [ ] Docker Compose receives correct DOCKER_IMAGE environment variable
- [ ] Fallback logic handles branch detection failures
- [ ] All existing functionality preserved
- [ ] Mode selection logic unchanged
- [ ] Container management functions work correctly
- [ ] Error messages are clear and helpful

## Backward Compatibility

- All existing command-line usage patterns work unchanged
- Developer marker file detection preserved
- Mode selection workflow identical
- Environment variable handling compatible
- Docker Compose integration seamless
- Fallback to 'latest' tag when branch detection fails