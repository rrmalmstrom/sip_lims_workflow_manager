@echo off
REM
REM SIP LIMS Workflow Manager - Windows Launcher
REM 
REM This script provides a simple double-clickable launcher for Windows users.
REM It automatically launches the unified Python launcher (run.py) with proper
REM error handling and user feedback.
REM

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory to ensure relative paths work
cd /d "%SCRIPT_DIR%"

REM Clear the screen for a clean start
cls

echo 🚀 SIP LIMS Workflow Manager - Windows Launcher
echo ==============================================
echo.

REM Check if Python is available (try python3 first, then python)
python3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

echo ❌ ERROR: Python is not installed or not in PATH
echo.
echo Please install Python 3 and try again.
echo You can download Python from: https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:python_found

REM Check if run.py exists
if not exist "run.py" (
    echo ❌ ERROR: run.py not found in current directory
    echo.
    echo Please make sure you're running this script from the
    echo SIP LIMS Workflow Manager project directory.
    echo.
    pause
    exit /b 1
)

echo 🐍 Launching Python workflow manager...
echo.

REM Launch the Python script with no command line arguments (default behavior)
"%PYTHON_CMD%" run.py

REM Capture the exit code
set "EXIT_CODE=!errorlevel!"

echo.
if !EXIT_CODE! equ 0 (
    echo ✅ Workflow completed successfully
) else (
    echo ❌ Workflow exited with error code: !EXIT_CODE!
)

echo.
echo Press any key to close this window...
pause >nul

exit /b !EXIT_CODE!