@echo off
rem This script handles the one-time setup for the Docker-based workflow.

rem --- Configuration ---
set "IMAGE_NAME=sip-lims-workflow-manager"
rem This version will be baked into the image. For a release, this should be updated to match the Git tag.
set "APP_VERSION=1.0.0"

echo --- Docker Setup for SIP LIMS Workflow Manager ---

rem 1. Determine Version
echo Step 1: Determining application version...
echo ✅ Using version %APP_VERSION% defined in this script.

rem 2. Check if Docker is running
echo.
echo Step 2: Checking for Docker...
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running.
    echo Please install and start Docker Desktop, then run this script again.
    echo Download from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo ✅ Docker is running.

rem 3. Build the Docker image from the local Dockerfile
echo.
echo Step 3: Building the application Docker image...
echo This may take several minutes on the first run.

docker build ^
    --build-arg "APP_VERSION=%APP_VERSION%" ^
    -t "%IMAGE_NAME%:latest" ^
    .

rem Check if the build was successful
if %errorlevel% neq 0 (
    echo Error: Docker build failed.
    echo Please check the output above for errors.
    pause
    exit /b 1
)

echo ✅ Docker image '%IMAGE_NAME%:latest' built successfully with version %APP_VERSION%.

echo.
echo --- Docker Setup Complete! ---
echo You can now run the application using the 'run.bat' script.
pause