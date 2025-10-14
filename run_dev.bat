@echo off
echo --- Starting SIP LIMS Workflow Manager (DEV MODE) ---

set "IMAGE_NAME=sip-lims-workflow-manager:latest"

rem Check if Docker is running
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    pause
    exit /b 1
)

echo.
echo Please drag and drop your project folder here, then press Enter:
set /p "PROJECT_PATH="

rem Exit if the path is empty
if not defined PROJECT_PATH (
    echo "No folder provided. Exiting."
    pause
    exit /b
)

rem Remove quotes if present
set "PROJECT_PATH=%PROJECT_PATH:"=%"

echo "Selected project folder: %PROJECT_PATH%"

rem --- Environment Mode Selection ---
set "ENV_FLAG=-e APP_ENV=production"
if exist ".env" (
    echo.
    echo Development environment detected (.env file found).
    echo Please choose a run mode:
    echo   1. Development (Default - Update checks disabled)
    echo   2. Production (Update checks enabled)
    set /p "mode_choice=Enter choice [1]: "

    if "%mode_choice%"=="2" (
        echo Running in PRODUCTION mode.
        set "ENV_FLAG=-e APP_ENV=production"
    ) else (
        echo Running in DEVELOPMENT mode.
        set "ENV_FLAG=--env-file .env"
    )
)
rem --- End Environment Mode Selection ---

rem --- Script Repository Management ---
set "SCRIPT_REPO_URL=https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git"

rem Check if the scripts directory is a git repository.
if exist "%SCRIPTS_DIR%\.git" (
    echo "Scripts repository found. Checking for updates..."
    rem Temporarily change to the scripts directory to run git pull
    pushd "%SCRIPTS_DIR%"
    git pull
    popd
) else (
    echo "Scripts repository not found. Cloning..."
    rem Clone the repository into the scripts directory
    git clone %SCRIPT_REPO_URL% "%SCRIPTS_DIR%"
)
echo "--- End Script Repository Management ---"
echo.

rem Define the central scripts directory on the host
set "SCRIPTS_DIR=%USERPROFILE%\.sip_lims_workflow_manager\scripts"

rem Create the directory if it doesn't exist
if not exist "%SCRIPTS_DIR%" (
    mkdir "%SCRIPTS_DIR%"
)

rem Run the application in a new container, mounting the correct volumes
echo "Launching application..."
docker run --rm -it ^
    -p 8501:8501 ^
    %ENV_FLAG% ^
    -v "%PROJECT_PATH%:/data" ^
    -v "%SCRIPTS_DIR%:/workflow-scripts" ^
    -w "/data" ^
    "%IMAGE_NAME%"

echo "Application has been shut down."
pause