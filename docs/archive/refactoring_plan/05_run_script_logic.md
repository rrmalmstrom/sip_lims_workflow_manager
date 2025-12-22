# 05 - Run Script Logic for Script Path Selection

## Overview
Design for modifying `run.command` and `run.bat` to support script path selection based on developer/production mode while preserving all existing functionality.

## Current Run Script Analysis

### Existing Working Components (run.command)
- **Lines 1-6**: Standard bash setup with directory detection ✅
- **Lines 8**: User-friendly startup message ✅
- **Lines 10-11**: Comments about removed old environment checks ✅
- **Lines 13-15**: Conda initialization and environment activation ✅
- **Lines 17-20**: Streamlit launch with localhost-only configuration ✅

### Components Requiring Modification
- **Line 20**: Streamlit launch command (needs script path argument)
- **Add**: Mode detection and script path selection logic
- **Add**: Script path validation

## New Run Script Design

### 1. Mode Detection Function
```bash
# NEW: Mode Detection Function (same as setup script for consistency)
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}
```

### 2. Script Path Selection Function
```bash
# NEW: Script Path Selection Function
select_script_path() {
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        echo ""
        echo "Choose script source for this session:"
        echo "1) Development scripts (../sip_scripts_workflow_gui)"
        echo "2) Production scripts (../sip_scripts_production)"
        echo ""
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1) 
                SCRIPT_PATH="../sip_scripts_workflow_gui"
                echo "✅ Using development scripts from: $SCRIPT_PATH"
                ;;
            2) 
                SCRIPT_PATH="../sip_scripts_production"
                echo "✅ Using production scripts from: $SCRIPT_PATH"
                ;;
            *) 
                echo "⚠️  Invalid choice, defaulting to production scripts"
                SCRIPT_PATH="../sip_scripts_production"
                ;;
        esac
    else
        echo "🏭 Production mode - using production scripts"
        SCRIPT_PATH="../sip_scripts_production"
    fi
    
    # Verify script directory exists
    if [ ! -d "$SCRIPT_PATH" ]; then
        echo "❌ ERROR: Script directory not found: $SCRIPT_PATH"
        echo "Please run setup.command first to initialize script repositories."
        exit 1
    fi
    
    echo "📁 Script path: $SCRIPT_PATH"
}
```

### 3. Enhanced Streamlit Launch
```bash
# MODIFIED: Launch with script path parameter (replaces line 20)
launch_application() {
    echo "Launching application in 'sip-lims' environment..."
    echo "--- Using Python from: $(which python) ---"
    echo "--- Using scripts from: $SCRIPT_PATH ---"
    
    # Pass script path to the Python application
    streamlit run app.py --server.headless=true --server.address=127.0.0.1 -- --script-path="$SCRIPT_PATH"
}
```

## Complete Modified run.command

### Integration Points
```bash
#!/bin/bash
# This script runs the SIP LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager ---"

# NEW: Mode Detection Function
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# NEW: Script Path Selection Function
select_script_path() {
    [function implementation as above]
}

# NEW: Enhanced Launch Function
launch_application() {
    [function implementation as above]
}

# NEW: Call script path selection
select_script_path

# UNCHANGED: Conda environment activation (lines 13-15)
eval "$(conda shell.bash hook)"
conda activate sip-lims

# MODIFIED: Launch application with script path
launch_application
```

## Windows Implementation (run.bat)

### Batch Script Equivalent
```batch
@echo off
echo --- Starting SIP LIMS Workflow Manager ---

REM NEW: Mode Detection Function
:detect_mode
if exist "config\developer.marker" (
    set MODE=developer
) else (
    set MODE=production
)
goto :eof

REM NEW: Script Path Selection Function
:select_script_path
call :detect_mode

if "%MODE%"=="developer" (
    echo 🔧 Developer mode detected
    echo.
    echo Choose script source for this session:
    echo 1^) Development scripts ^(../sip_scripts_workflow_gui^)
    echo 2^) Production scripts ^(../sip_scripts_production^)
    echo.
    set /p choice="Enter choice (1 or 2): "
    
    if "%choice%"=="1" (
        set SCRIPT_PATH=../sip_scripts_workflow_gui
        echo ✅ Using development scripts from: !SCRIPT_PATH!
    ) else if "%choice%"=="2" (
        set SCRIPT_PATH=../sip_scripts_production
        echo ✅ Using production scripts from: !SCRIPT_PATH!
    ) else (
        echo ⚠️ Invalid choice, defaulting to production scripts
        set SCRIPT_PATH=../sip_scripts_production
    )
) else (
    echo 🏭 Production mode - using production scripts
    set SCRIPT_PATH=../sip_scripts_production
)

REM Verify script directory exists
if not exist "%SCRIPT_PATH%" (
    echo ❌ ERROR: Script directory not found: %SCRIPT_PATH%
    echo Please run setup.bat first to initialize script repositories.
    pause
    exit /b 1
)

echo 📁 Script path: %SCRIPT_PATH%
goto :eof

REM NEW: Enhanced Launch Function
:launch_application
echo Launching application in 'sip-lims' environment...
echo --- Using Python from: ---
where python
echo --- Using scripts from: %SCRIPT_PATH% ---

REM Pass script path to the Python application
streamlit run app.py --server.headless=true --server.address=127.0.0.1 -- --script-path="%SCRIPT_PATH%"
goto :eof

REM NEW: Call script path selection
call :select_script_path

REM UNCHANGED: Conda environment activation
call conda activate sip-lims
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment 'sip-lims'.
    echo Please ensure the setup script has been run successfully.
    pause
    exit /b 1
)

REM MODIFIED: Launch application with script path
call :launch_application
```

## Script Path Passing Mechanism

### Command Line Argument Format
```bash
# The double dash (--) separates Streamlit args from app args
streamlit run app.py [streamlit-options] -- [app-options]

# Example:
streamlit run app.py --server.headless=true --server.address=127.0.0.1 -- --script-path="../sip_scripts_production"
```

### How Script Path Gets to Python App
1. **Shell Script**: Determines script path based on mode and user choice
2. **Streamlit Launch**: Passes script path via `-- --script-path="$SCRIPT_PATH"`
3. **app.py**: Receives and parses the script path argument
4. **Core Components**: Use script path for script execution

## Test Specifications (TDD)

### Test Cases
```bash
# Test 1: Developer mode script selection - development choice
test_dev_mode_script_selection_dev() {
    # Given: config/developer.marker exists AND user chooses option 1
    # When: run script executes
    # Then: should use ../sip_scripts_workflow_gui path
    # And: should pass correct argument to streamlit
}

# Test 2: Developer mode script selection - production choice
test_dev_mode_script_selection_prod() {
    # Given: config/developer.marker exists AND user chooses option 2
    # When: run script executes
    # Then: should use ../sip_scripts_production path
    # And: should pass correct argument to streamlit
}

# Test 3: Developer mode invalid choice
test_dev_mode_invalid_choice() {
    # Given: config/developer.marker exists AND user chooses invalid option
    # When: run script executes
    # Then: should default to ../sip_scripts_production path
    # And: should show warning message
}

# Test 4: Production mode automatic path
test_prod_mode_automatic_script_path() {
    # Given: no config/developer.marker exists
    # When: run script executes
    # Then: should automatically use ../sip_scripts_production path
    # And: should not show any prompts
}

# Test 5: Missing script directory error handling
test_missing_script_directory_handling() {
    # Given: selected script directory does not exist
    # When: run script executes
    # Then: should show clear error message
    # And: should suggest running setup script
    # And: should exit with error code
}

# Test 6: Existing streamlit functionality preserved
test_existing_streamlit_launch_preserved() {
    # Given: run script executes with new script path logic
    # When: streamlit launch occurs
    # Then: should work exactly as before with same parameters
    # And: should maintain localhost-only security
    # And: should maintain headless configuration
}

# Test 7: Conda environment activation preserved
test_conda_activation_preserved() {
    # Given: run script executes with new logic
    # When: conda activation occurs
    # Then: should work exactly as before
    # And: should show Python path information
    # And: should handle activation errors properly
}
```

## Error Handling Strategy

### Missing Script Directory
```bash
validate_script_path() {
    local script_path=$1
    
    if [ ! -d "$script_path" ]; then
        echo "❌ ERROR: Script directory not found: $script_path"
        echo ""
        echo "💡 SOLUTION:"
        echo "   1. Run setup.command to initialize script repositories"
        echo "   2. Ensure you have internet connection for repository cloning"
        echo "   3. Check that the setup completed successfully"
        echo ""
        return 1
    fi
    
    # Check if directory contains Python scripts
    if [ -z "$(find "$script_path" -name "*.py" -type f)" ]; then
        echo "⚠️  WARNING: No Python scripts found in: $script_path"
        echo "The directory exists but appears to be empty or incomplete."
        echo ""
        echo "💡 SOLUTION:"
        echo "   1. Run setup.command to update script repositories"
        echo "   2. Check your internet connection"
        echo ""
        return 1
    fi
    
    return 0
}
```

### Conda Environment Issues
```bash
# Enhanced conda error handling (preserve existing logic)
activate_conda_environment() {
    echo "Activating conda environment 'sip-lims'..."
    
    # Initialize conda for this script session
    eval "$(conda shell.bash hook)"
    
    # Activate the environment
    if ! conda activate sip-lims; then
        echo "❌ ERROR: Failed to activate conda environment 'sip-lims'."
        echo ""
        echo "💡 SOLUTION:"
        echo "   1. Run setup.command to create the environment"
        echo "   2. Ensure conda is properly installed"
        echo "   3. Check that the setup completed successfully"
        echo ""
        exit 1
    fi
    
    echo "✅ Conda environment activated successfully"
    echo "--- Using Python from: $(which python) ---"
}
```

### User Input Validation
```bash
get_user_choice() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1|2)
                echo "$choice"
                return 0
                ;;
            *)
                echo "⚠️  Invalid choice. Please enter 1 or 2."
                attempt=$((attempt + 1))
                ;;
        esac
    done
    
    echo "⚠️  Too many invalid attempts. Defaulting to production scripts."
    echo "2"
    return 0
}
```

## User Experience Flow

### Developer Mode Flow
1. User double-clicks `run.command`
2. Script detects developer mode (marker file exists)
3. User sees clear prompt with 2 numbered choices
4. User selects development or production scripts
5. Script validates chosen directory exists
6. Script activates conda environment
7. App launches with selected script path
8. User sees confirmation of which scripts are being used

### Production Mode Flow
1. User double-clicks `run.command`
2. Script detects production mode (no marker file)
3. Script automatically selects production scripts
4. Script validates directory exists
5. Script activates conda environment
6. App launches immediately
7. User sees confirmation of production script usage

## Integration with Setup Scripts

### Dependency on Setup
- Run script assumes setup script has been executed
- Setup script creates external script directories
- Run script validates these directories exist
- Clear error messages guide user to run setup if needed

### Shared Logic
- Both scripts use identical `detect_mode()` function
- Consistent path naming conventions
- Similar error handling patterns
- Coordinated user messaging

## Benefits

### For Developers
- ✅ Can choose script source per session
- ✅ Easy to switch between dev/prod scripts for testing
- ✅ Clear feedback about which scripts are being used
- ✅ No permanent configuration changes needed

### For Production Users
- ✅ No changes to current workflow
- ✅ No user interaction required
- ✅ Always uses stable production scripts
- ✅ Consistent behavior for end users

### For Maintenance
- ✅ All existing conda and streamlit logic preserved
- ✅ Clear separation between old and new functionality
- ✅ Comprehensive error handling with helpful solutions
- ✅ Cross-platform compatibility (bash/batch)

## Migration Strategy

### Phase 1: Add Functions Without Behavior Change
- Add mode detection and script path functions
- Keep existing streamlit launch as fallback
- Test that nothing breaks

### Phase 2: Implement Script Path Selection
- Add script path selection logic
- Add validation and error handling
- Test both developer and production modes

### Phase 3: Integrate with Streamlit Launch
- Modify streamlit command to pass script path
- Test argument passing to Python app
- Verify app receives script path correctly

### Phase 4: Enhanced Error Handling and UX
- Add comprehensive error messages
- Implement user input validation
- Add helpful troubleshooting guidance