@echo off
setlocal enabledelayedexpansion

REM Enhanced SIP LIMS Workflow Manager Docker Runner for Windows
REM Combines legacy Docker functionality with current ESP features and robust update detection

echo --- Starting SIP LIMS Workflow Manager (Docker) ---

REM Get the directory where the script is located
set "DIR=%~dp0"
cd /d "%DIR%"

echo 🌿 Detecting branch and generating Docker image names...

REM Source branch utilities (Windows equivalent of bash source)
REM This will validate Git repo and set CURRENT_BRANCH, LOCAL_IMAGE_NAME, REMOTE_IMAGE_NAME
call "%DIR%utils\branch_utils.bat"
if %errorlevel% neq 0 (
    echo ❌ ERROR: Branch utilities failed
    echo    Make sure you're in a valid Git repository and Python utilities are available
    pause
    exit /b 1
)

REM Verify that variables were set
if "%CURRENT_BRANCH%"=="" (
    echo ❌ ERROR: Failed to detect current branch
    echo    Make sure you're on a proper branch (not detached HEAD)
    pause
    exit /b 1
)

if "%LOCAL_IMAGE_NAME%"=="" (
    echo ❌ ERROR: Failed to generate local image name
    pause
    exit /b 1
)

if "%REMOTE_IMAGE_NAME%"=="" (
    echo ❌ ERROR: Failed to generate remote image name
    pause
    exit /b 1
)

REM Display current branch information
for /f "delims=" %%i in ('git branch --show-current 2^>nul') do set "DISPLAY_BRANCH=%%i"
echo    ✅ Current branch: %DISPLAY_BRANCH%
echo    ✅ Docker tag: %CURRENT_BRANCH%
echo    ✅ Local image: %LOCAL_IMAGE_NAME%
echo    ✅ Remote image: %REMOTE_IMAGE_NAME%

REM Container Management - Stop any running workflow manager containers
call :stop_workflow_containers

REM Handle mode detection and updates
call :handle_mode_and_updates

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Prompt user to provide the project folder path
echo.
echo Please drag and drop your project folder here, then press Enter:
set /p "PROJECT_PATH="

REM Clean up the path (remove quotes and trim)
set "PROJECT_PATH=%PROJECT_PATH:"=%"
for /f "tokens=* delims= " %%a in ("%PROJECT_PATH%") do set "PROJECT_PATH=%%a"

REM Exit if the path is empty
if "%PROJECT_PATH%"=="" (
    echo ❌ ERROR: No folder provided. Exiting.
    pause
    exit /b 1
)

REM Validate that the project path exists and is a directory
if not exist "%PROJECT_PATH%" (
    echo ❌ ERROR: Project folder does not exist or is not a directory: %PROJECT_PATH%
    echo Please provide a valid folder path.
    pause
    exit /b 1
)

echo ✅ Selected project folder: %PROJECT_PATH%

REM Extract project name from the project path (Windows equivalent of basename)
for %%f in ("%PROJECT_PATH%") do set "PROJECT_NAME=%%~nxf"
echo ✅ Project name: %PROJECT_NAME%

REM Set environment variables for docker-compose
set "USER_ID=1000"
set "GROUP_ID=1000"

REM Launch using docker-compose with user ID mapping
echo Launching application with Docker Compose...
echo --- Environment Variables ---
echo USER_ID: %USER_ID%
echo GROUP_ID: %GROUP_ID%
echo PROJECT_PATH: %PROJECT_PATH%
echo PROJECT_NAME: %PROJECT_NAME%
echo SCRIPTS_PATH: %SCRIPTS_PATH%
echo APP_ENV: %APP_ENV%
echo DOCKER_IMAGE: %DOCKER_IMAGE%
echo --- Starting Container ---

REM Use docker-compose for enhanced user ID mapping and volume management
docker-compose up

echo Application has been shut down.
pause
goto :eof

REM ============================================================================
REM FUNCTION DEFINITIONS
REM ============================================================================

:stop_workflow_containers
echo 🛑 Checking for running workflow manager containers...

REM Find containers using workflow manager images (both local and remote, branch-aware)
set "FOUND_CONTAINERS="
set "CONTAINER_IDS="

for /f "tokens=1,2,3*" %%a in ('docker ps -a --filter "ancestor=%REMOTE_IMAGE_NAME%" --filter "ancestor=%LOCAL_IMAGE_NAME%" --format "{{.ID}} {{.Names}} {{.Status}}" 2^>nul') do (
    set "FOUND_CONTAINERS=true"
    echo     - %%b (%%a): %%c %%d
    if "!CONTAINER_IDS!"=="" (
        set "CONTAINER_IDS=%%a"
    ) else (
        set "CONTAINER_IDS=!CONTAINER_IDS! %%a"
    )
)

if defined FOUND_CONTAINERS (
    echo 📋 Found workflow manager containers
    if defined CONTAINER_IDS (
        echo 🛑 Stopping workflow manager containers...
        docker stop %CONTAINER_IDS% >nul 2>&1
        echo 🗑️  Removing workflow manager containers...
        docker rm %CONTAINER_IDS% >nul 2>&1
        echo ✅ Workflow manager containers cleaned up
    )
) else (
    echo ✅ No running workflow manager containers found
)
goto :eof

:check_docker_updates
echo 🔍 Checking for Docker image updates...

REM Use the update detector to check for Docker updates with branch-aware tag
python3 -c "from src.update_detector import UpdateDetector; from utils.branch_utils import get_current_branch, sanitize_branch_for_docker_tag; import json; detector = UpdateDetector(); branch = get_current_branch(); tag = sanitize_branch_for_docker_tag(branch); result = detector.check_docker_update(tag=tag, branch=branch); print(json.dumps(result))" 2>nul > temp_update_result.json

if %errorlevel% equ 0 (
    REM Parse the JSON result to check if update is available and if chronology is uncertain
    for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_update_result.json')); print('true' if data.get('update_available', False) else 'false')" 2^>nul') do set "UPDATE_AVAILABLE=%%i"
    
    for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_update_result.json')); print('true' if data.get('chronology_uncertain', False) else 'false')" 2^>nul') do set "CHRONOLOGY_UNCERTAIN=%%i"
    
    for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_update_result.json')); print('true' if data.get('requires_user_confirmation', False) else 'false')" 2^>nul') do set "REQUIRES_CONFIRMATION=%%i"
    
    if "!UPDATE_AVAILABLE!"=="true" (
        if "!CHRONOLOGY_UNCERTAIN!"=="true" if "!REQUIRES_CONFIRMATION!"=="true" (
            REM Extract warning message and reason
            for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_update_result.json')); print(data.get('warning', 'Chronology uncertain'))" 2^>nul') do set "WARNING_MSG=%%i"
            for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_update_result.json')); print(data.get('reason', 'Unknown reason'))" 2^>nul') do set "REASON=%%i"
            
            echo ⚠️  **CHRONOLOGY WARNING**
            echo    !REASON!
            echo    !WARNING_MSG!
            echo.
            echo The system cannot determine if your local Docker image is newer or older than the remote version.
            echo Proceeding with the update might overwrite a newer local version with an older remote version.
            echo.
            set /p "USER_CHOICE=Do you want to proceed with the Docker image update? (y/N): "
            
            REM Convert to lowercase and trim
            for /f "tokens=* delims= " %%a in ("!USER_CHOICE!") do set "USER_CHOICE=%%a"
            if defined USER_CHOICE (
                for %%i in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do call set "USER_CHOICE=%%USER_CHOICE:%%i=%%i%%"
                for %%i in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do call set "USER_CHOICE=%%USER_CHOICE:%%i=%%i%%"
            )
            
            if not "!USER_CHOICE!"=="y" if not "!USER_CHOICE!"=="yes" (
                echo ❌ Docker image update cancelled by user
                echo ✅ Continuing with current local Docker image
                goto :cleanup_and_exit
            )
            echo ✅ User confirmed - proceeding with Docker image update...
        ) else (
            echo 📦 Docker image update available - updating to latest version...
        )
        
        REM Get current image ID before cleanup
        for /f "delims=" %%i in ('docker images "%REMOTE_IMAGE_NAME%" --format "{{.ID}}" 2^>nul') do set "OLD_IMAGE_ID=%%i"
        
        REM Clean up old image BEFORE pulling new one
        if defined OLD_IMAGE_ID (
            echo 🧹 Removing old Docker image before update...
            docker rmi "%REMOTE_IMAGE_NAME%" >nul 2>&1
            docker image prune -f >nul 2>&1
            echo ✅ Old Docker image and dangling images cleaned up
        )
        
        REM Pull the new image
        echo 📥 Pulling Docker image for branch: %DISPLAY_BRANCH%...
        docker pull "%REMOTE_IMAGE_NAME%"
        if %errorlevel% equ 0 (
            echo ✅ Docker image updated successfully
        ) else (
            echo ❌ ERROR: Docker image update failed
        )
    ) else (
        echo ✅ Docker image is up to date
    )
) else (
    echo ⚠️  Warning: Could not check for Docker updates, continuing with current version
)

:cleanup_and_exit
REM Clean up temporary file
if exist temp_update_result.json del temp_update_result.json
goto :eof

:check_and_download_scripts
set "SCRIPTS_DIR_ARG=%~1"
set "BRANCH_ARG=%~2"
if "%BRANCH_ARG%"=="" set "BRANCH_ARG=main"

echo 🔍 Checking for script updates...

REM Check for script updates using the scripts updater
python3 src/scripts_updater.py --check-scripts --scripts-dir "%SCRIPTS_DIR_ARG%" --branch "%BRANCH_ARG%" 2>nul > temp_scripts_result.json

if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_scripts_result.json')); print('true' if data.get('update_available', False) else 'false')" 2^>nul') do set "SCRIPTS_UPDATE_AVAILABLE=%%i"
    
    if "!SCRIPTS_UPDATE_AVAILABLE!"=="true" (
        echo 📦 Script updates available - updating scripts...
        python3 src/scripts_updater.py --update-scripts --scripts-dir "%SCRIPTS_DIR_ARG%" --branch "%BRANCH_ARG%"
        if %errorlevel% equ 0 (
            echo ✅ Scripts updated successfully
        ) else (
            echo ❌ ERROR: Failed to update scripts
        )
    ) else (
        echo ✅ Scripts are up to date
    )
) else (
    echo ⚠️  Warning: Could not check for script updates, continuing with current version
)

REM Clean up temporary file
if exist temp_scripts_result.json del temp_scripts_result.json
goto :eof

:production_auto_update
echo 🏭 Production mode - performing automatic updates...

REM Check and update Docker image
call :check_docker_updates

REM Set up centralized scripts directory
set "SCRIPTS_DIR=%USERPROFILE%\.sip_lims_workflow_manager\scripts"

REM Check and download/update scripts
call :check_and_download_scripts "%SCRIPTS_DIR%" "main"

REM Set scripts path for production use
set "SCRIPTS_PATH=%SCRIPTS_DIR%"
set "APP_ENV=production"

REM Use pre-built Docker image for production (branch-aware)
set "DOCKER_IMAGE=%REMOTE_IMAGE_NAME%"

echo 📁 Using centralized scripts: %SCRIPTS_PATH%
echo 🐳 Using pre-built Docker image: %DOCKER_IMAGE%
echo 🌿 Branch: %DISPLAY_BRANCH%
goto :eof

:detect_mode
if exist "config\developer.marker" (
    set "MODE=developer"
) else (
    set "MODE=production"
)
goto :eof

:choose_developer_mode
echo 🔧 Developer mode detected
echo.
echo Choose your workflow mode:
echo 1^) Production mode (auto-updates, centralized scripts^)
echo 2^) Development mode (local scripts, no auto-updates^)
echo.
set /p "DEV_CHOICE=Enter choice (1 or 2): "

if "%DEV_CHOICE%"=="1" (
    echo ✅ Using production mode workflow
    set "USE_PRODUCTION_WORKFLOW=true"
) else if "%DEV_CHOICE%"=="2" (
    echo ✅ Using development mode workflow
    set "USE_PRODUCTION_WORKFLOW=false"
) else (
    echo ❌ ERROR: Invalid choice '%DEV_CHOICE%'. Please enter 1 or 2.
    echo Exiting.
    pause
    exit /b 1
)
goto :eof

:select_development_script_path
echo.
echo Please drag and drop your development scripts folder here, then press Enter:
set /p "SCRIPTS_PATH="

REM Clean up the path (remove quotes and trim)
set "SCRIPTS_PATH=%SCRIPTS_PATH:"=%"
for /f "tokens=* delims= " %%a in ("%SCRIPTS_PATH%") do set "SCRIPTS_PATH=%%a"

REM Exit if the path is empty
if "%SCRIPTS_PATH%"=="" (
    echo ❌ ERROR: No scripts folder provided. Exiting.
    pause
    exit /b 1
)

REM Validate that the scripts path exists and is a directory
if not exist "%SCRIPTS_PATH%" (
    echo ❌ ERROR: Scripts folder does not exist or is not a directory: %SCRIPTS_PATH%
    echo Please provide a valid scripts folder path.
    pause
    exit /b 1
)

echo ✅ Selected development scripts folder: %SCRIPTS_PATH%
set "APP_ENV=development"

REM Use local Docker build for development mode (branch-aware)
set "DOCKER_IMAGE=%LOCAL_IMAGE_NAME%"

echo 📁 Script path: %SCRIPTS_PATH%
echo 🐳 Using local Docker build: %DOCKER_IMAGE%
echo 🌿 Branch: %DISPLAY_BRANCH%
goto :eof

:handle_mode_and_updates
call :detect_mode

if "%MODE%"=="developer" (
    REM Developer detected - ask for production vs development workflow
    call :choose_developer_mode
    
    if "%USE_PRODUCTION_WORKFLOW%"=="true" (
        REM Developer chose production workflow - use auto-updates
        call :production_auto_update
    ) else (
        REM Developer chose development workflow - use local scripts
        call :select_development_script_path
    )
) else (
    REM Regular production user - always use auto-updates
    call :production_auto_update
)
goto :eof