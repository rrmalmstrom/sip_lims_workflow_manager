# 04 - Setup Script Logic for Dev/Prod Mode Detection

## Overview
Design for modifying `setup.command` and `setup.bat` to support developer/production mode detection and conditional behavior while preserving all existing functionality.

## Current Setup Script Analysis

### Existing Working Components (setup.command)
- **Lines 1-9**: Standard bash setup with error handling and directory detection ✅
- **Lines 11-12**: Environment name parameter handling (defaults to 'sip-lims') ✅
- **Lines 16-24**: Script repository management (currently nested 'scripts' directory) ❌
- **Lines 28-45**: Conda environment setup (working and tested) ✅
- **Lines 47-51**: Success messaging ✅

### Components Requiring Modification
- **Lines 16-24**: Script repository cloning logic
- **Success messaging**: Add mode-specific information

## New Setup Script Design

### 1. Mode Detection Function
```bash
# NEW: Mode Detection Function (same as run script for consistency)
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}
```

### 2. Enhanced Script Repository Management
```bash
# MODIFIED: Replace lines 16-24 with mode-aware logic
setup_script_repositories() {
    MODE=$(detect_mode)
    echo "Detected mode: $MODE"
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        echo "Choose setup option:"
        echo "1) Work offline (skip remote repository updates)"
        echo "2) Connect to remotes to check for updates"
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1) 
                echo "Working offline - skipping repository updates"
                SKIP_REPOS=true
                ;;
            2) 
                echo "Connecting to remotes for updates"
                SKIP_REPOS=false
                ;;
            *) 
                echo "Invalid choice, defaulting to offline mode"
                SKIP_REPOS=true
                ;;
        esac
    else
        echo "🏭 Production mode detected - automatically updating repositories"
        SKIP_REPOS=false
    fi
    
    if [ "$SKIP_REPOS" = false ]; then
        setup_external_repositories
    fi
}
```

### 3. External Repository Setup Function
```bash
# NEW: External repository setup function
setup_external_repositories() {
    echo "Setting up external script repositories..."
    
    # Remove old nested scripts directory if it exists
    if [ -d "scripts" ]; then
        echo "Removing old nested scripts directory..."
        rm -rf scripts
    fi
    
    # Setup external script directories
    cd ..  # Go to parent directory
    
    # Always setup production scripts
    echo "Setting up production scripts..."
    if [ -d "sip_scripts_production" ]; then
        cd sip_scripts_production
        git pull
        cd ..
    else
        git clone https://github.com/rrmalmstrom/sip_scripts_production.git sip_scripts_production
    fi
    
    # Setup development scripts only in developer mode
    if [ "$MODE" = "developer" ]; then
        echo "Setting up development scripts..."
        if [ -d "sip_scripts_workflow_gui" ]; then
            cd sip_scripts_workflow_gui
            git pull
            cd ..
        else
            git clone https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git sip_scripts_workflow_gui
        fi
    fi
    
    cd sip_lims_workflow_manager  # Return to app directory
}
```

### 4. Configuration Directory Setup
```bash
# NEW: Ensure config directory exists
setup_config_directory() {
    mkdir -p config
    update_gitignore
}

# NEW: Update .gitignore if needed
update_gitignore() {
    if ! grep -q "config/developer.marker" .gitignore; then
        echo "" >> .gitignore
        echo "# Developer Environment Configuration" >> .gitignore
        echo "# Exclude developer marker file to prevent distribution" >> .gitignore
        echo "config/developer.marker" >> .gitignore
        echo "" >> .gitignore
        echo "# Exclude local development config files" >> .gitignore
        echo "config/*.local" >> .gitignore
        echo "config/*.dev" >> .gitignore
        echo "config/local_*" >> .gitignore
        echo "✅ Updated .gitignore with developer configuration exclusions"
    fi
}
```

### 5. Enhanced Success Messaging
```bash
# ENHANCED: Mode-specific success messaging
show_completion_message() {
    MODE=$(detect_mode)
    
    echo ""
    if [ "$MODE" = "developer" ]; then
        echo "✅ Developer setup completed successfully!"
        echo "📁 Script repositories are located in sibling directories:"
        echo "   - ../sip_scripts_production (production scripts)"
        if [ "$SKIP_REPOS" = false ]; then
            echo "   - ../sip_scripts_workflow_gui (development scripts)"
        fi
        echo "🚀 You can now run the application using run.command"
        echo "💡 The run script will prompt you to choose between dev/prod scripts"
    else
        echo "✅ Production setup completed successfully!"
        echo "📁 Production scripts are located at: ../sip_scripts_production"
        echo "🚀 You can now run the application using run.command"
    fi
}
```

## Complete Modified setup.command

### Integration Points
```bash
#!/bin/bash
# This script sets up the Conda environment for the SIP LIMS Workflow Manager.

# Exit on any error
set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Get the environment name from the first argument, or default to 'sip-lims'
ENV_NAME=${1:-sip-lims}

echo "--- Setting up SIP LIMS Workflow Manager: $ENV_NAME ---"

# NEW: Include all new functions here
[detect_mode function]
[setup_config_directory function]
[setup_script_repositories function]
[setup_external_repositories function]
[update_gitignore function]
[show_completion_message function]

# NEW: Setup configuration
setup_config_directory

# MODIFIED: Script repository setup (replaces lines 16-24)
setup_script_repositories

# UNCHANGED: Conda Environment Setup (lines 26-45)
[existing conda setup logic]

# MODIFIED: Success messaging (replaces lines 47-51)
show_completion_message
```

## Windows Implementation (setup.bat)

### Batch Script Equivalent
```batch
@echo off
echo --- Setting up SIP LIMS Workflow Manager ---

REM NEW: Mode Detection Function
:detect_mode
if exist "config\developer.marker" (
    set MODE=developer
) else (
    set MODE=production
)
goto :eof

REM NEW: Script Repository Setup
:setup_script_repositories
call :detect_mode
echo Detected mode: %MODE%

if "%MODE%"=="developer" (
    echo 🔧 Developer mode detected
    echo Choose setup option:
    echo 1^) Work offline ^(skip remote repository updates^)
    echo 2^) Connect to remotes to check for updates
    set /p choice="Enter choice (1 or 2): "
    
    if "%choice%"=="1" (
        echo Working offline - skipping repository updates
        set SKIP_REPOS=true
    ) else if "%choice%"=="2" (
        echo Connecting to remotes for updates
        set SKIP_REPOS=false
    ) else (
        echo Invalid choice, defaulting to offline mode
        set SKIP_REPOS=true
    )
) else (
    echo 🏭 Production mode detected - automatically updating repositories
    set SKIP_REPOS=false
)

if "%SKIP_REPOS%"=="false" call :setup_external_repositories
goto :eof

REM NEW: External Repository Setup
:setup_external_repositories
echo Setting up external script repositories...

if exist "scripts" (
    echo Removing old nested scripts directory...
    rmdir /s /q scripts
)

cd ..

echo Setting up production scripts...
if exist "sip_scripts_production" (
    cd sip_scripts_production
    git pull
    cd ..
) else (
    git clone https://github.com/rrmalmstrom/sip_scripts_production.git sip_scripts_production
)

if "%MODE%"=="developer" (
    echo Setting up development scripts...
    if exist "sip_scripts_workflow_gui" (
        cd sip_scripts_workflow_gui
        git pull
        cd ..
    ) else (
        git clone https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git sip_scripts_workflow_gui
    )
)

cd sip_lims_workflow_manager
goto :eof
```

## Test Specifications (TDD)

### Test Cases
```bash
# Test 1: Developer mode setup with offline choice
test_dev_mode_offline_setup() {
    # Given: config/developer.marker exists AND user chooses offline
    # When: setup script runs
    # Then: no git operations should be performed
    # And: conda environment should be created/updated
    # And: success message should mention offline mode
}

# Test 2: Developer mode setup with online choice  
test_dev_mode_online_setup() {
    # Given: config/developer.marker exists AND user chooses online
    # When: setup script runs
    # Then: both dev and prod script repos should be updated
    # And: conda environment should be created/updated
    # And: success message should list both repositories
}

# Test 3: Production mode automatic setup
test_prod_mode_automatic_setup() {
    # Given: no config/developer.marker exists
    # When: setup script runs
    # Then: only production scripts should be updated automatically
    # And: no user prompts should appear
    # And: conda environment should be created/updated
}

# Test 4: Existing functionality preservation
test_existing_conda_setup_preserved() {
    # Given: setup script runs with new mode detection
    # When: conda environment setup executes
    # Then: should work exactly as before
    # And: environment name parameter should still work
    # And: error handling should be preserved
}

# Test 5: .gitignore update
test_gitignore_update() {
    # Given: setup script runs
    # When: .gitignore update function executes
    # Then: developer marker should be added to .gitignore
    # And: existing .gitignore content should be preserved
}
```

## Error Handling Strategy

### Git Operation Failures
```bash
# Enhanced error handling for git operations
safe_git_clone() {
    local repo_url=$1
    local target_dir=$2
    
    if ! git clone "$repo_url" "$target_dir"; then
        echo "❌ ERROR: Failed to clone $repo_url"
        echo "Please check your internet connection and try again."
        return 1
    fi
}

safe_git_pull() {
    local repo_dir=$1
    
    cd "$repo_dir"
    if ! git pull; then
        echo "❌ ERROR: Failed to update $repo_dir"
        echo "Please check your internet connection and try again."
        cd ..
        return 1
    fi
    cd ..
}
```

### Directory Operation Failures
```bash
# Safe directory operations
safe_remove_directory() {
    local dir_path=$1
    
    if [ -d "$dir_path" ]; then
        if ! rm -rf "$dir_path"; then
            echo "❌ ERROR: Failed to remove $dir_path"
            echo "Please check file permissions and try again."
            return 1
        fi
    fi
}
```

## Migration Strategy

### Phase 1: Add Functions Without Behavior Change
- Add all new functions to setup scripts
- Keep existing behavior as default
- Test that nothing breaks

### Phase 2: Implement Mode Detection
- Add mode detection calls
- Add conditional logic
- Test both modes thoroughly

### Phase 3: External Repository Setup
- Implement external repository cloning
- Add cleanup of nested scripts
- Test repository management

### Phase 4: Enhanced Messaging and Error Handling
- Add mode-specific success messages
- Implement comprehensive error handling
- Add user guidance and troubleshooting

## Benefits

### For Developers
- ✅ Can choose to work offline when needed
- ✅ Clear feedback about what repositories are being set up
- ✅ Option to skip time-consuming git operations
- ✅ Automatic setup of both dev and prod script repositories

### For Production Users
- ✅ No changes to current workflow
- ✅ Automatic repository setup and updates
- ✅ No confusing prompts or choices
- ✅ Reliable, consistent behavior

### For Maintenance
- ✅ All existing conda logic preserved
- ✅ Clear separation between old and new functionality
- ✅ Comprehensive error handling
- ✅ Cross-platform compatibility (bash/batch)