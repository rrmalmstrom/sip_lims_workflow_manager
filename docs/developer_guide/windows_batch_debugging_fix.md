# Windows Batch Script Fix Documentation

## Problem Summary

The [`run.windows.bat`](../run.windows.bat) script was failing to prompt users for project folder input and closing immediately on Windows systems, while the equivalent [`run.mac.command`](../run.mac.command) worked perfectly on macOS.

## Root Cause Analysis

### Issue Identified
The original [`run.windows.bat`](../run.windows.bat) attempted to replicate the functionality of [`run.mac.command`](../run.mac.command) but had a critical architectural difference:

- **macOS version** uses [`utils/branch_utils.sh`](../utils/branch_utils.sh) with proper bash functions and error handling
- **Windows version** used direct Python calls without the robust wrapper functions and error handling

### Specific Failure Points
1. **Direct Python calls** in Windows batch were fragile and error-prone
2. **Missing error handling** that exists in the bash utilities
3. **No fallback mechanisms** when Python utilities failed
4. **Complex function dispatch logic** that doesn't work reliably in Windows batch

## Solution Implemented

### 1. Created Windows Batch Utilities
Created [`utils/branch_utils.bat`](../utils/branch_utils.bat) as the Windows equivalent of [`utils/branch_utils.sh`](../utils/branch_utils.sh):

- **Git repository validation**
- **Python utilities with error handling**
- **Fallback logic using pure git commands**
- **Variable export to parent script**

### 2. Simplified Function Architecture
Instead of complex function dispatch, used a simple approach:
- Single script execution that sets all required variables
- Proper variable export using `endlocal & (set "VAR=value")`
- Robust error handling at each step

### 3. Updated run.windows.bat
Modified [`run.windows.bat`](../run.windows.bat) to:
- Call [`utils/branch_utils.bat`](../utils/branch_utils.bat) once to set all variables
- Validate that variables were set correctly
- Proceed with the same logic as [`run.mac.command`](../run.mac.command)

## Key Files Modified

### [`utils/branch_utils.bat`](../utils/branch_utils.bat)
- **New file** - Windows equivalent of bash utilities
- Provides Git validation, Python utilities, and fallback logic
- Exports variables: `CURRENT_BRANCH`, `LOCAL_IMAGE_NAME`, `REMOTE_IMAGE_NAME`

### [`run.windows.bat`](../run.windows.bat)
- **Modified** - Updated to use the new batch utilities
- Simplified branch detection logic
- Added proper error checking for variable setting

## Testing Approach

### Cross-Platform Validation
Created [`test_windows_batch_logic.py`](../archive/deprecated_2026/test_windows_batch_logic.py) to simulate Windows batch logic on macOS:

- **Git repository validation** using same commands
- **Python utilities testing** with same imports and functions
- **Fallback logic simulation** with same string operations
- **Variable compatibility testing** for docker-compose

### Test Results
```
✅ Git repository validated
✅ Current branch: main
✅ Docker tag: main
✅ Local image: sip-lims-workflow-manager:main
✅ Remote image: ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main
✅ ALL TESTS PASSED
```

## Technical Details

### Windows Batch Function Pattern
```batch
REM Call utilities and set variables
call "%DIR%utils\branch_utils.bat"
if %errorlevel% neq 0 (
    echo ❌ ERROR: Branch utilities failed
    pause
    exit /b 1
)

REM Variables are now available: CURRENT_BRANCH, LOCAL_IMAGE_NAME, REMOTE_IMAGE_NAME
```

### Variable Export Pattern
```batch
REM In utils/branch_utils.bat
endlocal & (
    set "CURRENT_BRANCH=%CURRENT_BRANCH%"
    set "LOCAL_IMAGE_NAME=%LOCAL_IMAGE_NAME%"
    set "REMOTE_IMAGE_NAME=%REMOTE_IMAGE_NAME%"
)
```

### Fallback Logic
```batch
REM Try Python utilities first
for /f "delims=" %%i in ('python3 -c "..." 2^>nul') do set "CURRENT_BRANCH=%%i"
if "%CURRENT_BRANCH%"=="" (
    REM Fallback to git command
    for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "FALLBACK_BRANCH=%%i"
    REM Simple sanitization
    set "CURRENT_BRANCH=%FALLBACK_BRANCH: =-%"
    set "CURRENT_BRANCH=%CURRENT_BRANCH:/=-%"
)
```

## Expected Behavior

After this fix, [`run.windows.bat`](../run.windows.bat) should:

1. **Validate Git repository** without early exit
2. **Detect branch and generate Docker image names** using Python utilities or fallback
3. **Proceed to project folder prompt** (the critical missing step)
4. **Launch docker-compose** with proper environment variables
5. **Work identically** to [`run.mac.command`](../run.mac.command)

## Verification Steps

To verify the fix works on Windows:

1. Run [`run.windows.bat`](../run.windows.bat) in a Git repository
2. Verify it shows branch detection messages
3. Verify it prompts for project folder (this was the missing step)
4. Verify it launches the Docker container successfully

## Compatibility

- **Windows 10/11** with Command Prompt or PowerShell
- **Git for Windows** installed
- **Python 3** available in PATH
- **Docker Desktop** running
- **Same requirements** as macOS version