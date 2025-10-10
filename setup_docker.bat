@echo off
rem This script handles the one-time setup for the Docker-based workflow.

set "IMAGE_NAME=ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
set "TAG=latest"

echo --- Docker Setup for SIP LIMS Workflow Manager ---

rem 1. Check if Docker is running
echo Step 1: Checking for Docker...
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running.
    echo Please install and start Docker Desktop, then run this script again.
    echo Download from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo ✅ Docker is running.

rem 2. Check if user is logged into GitHub Container Registry
echo.
echo Step 2: Checking GitHub Container Registry access...
docker pull %IMAGE_NAME%:%TAG% > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Successfully pulled image. You are already logged in.
) else (
    echo ⚠️ You are not logged into the GitHub Container Registry (ghcr.io).
    echo To pull the private application image, you need to authenticate.
    echo.
    echo Please follow these steps:
    echo   1. Create a GitHub Personal Access Token (PAT) with the 'read:packages' scope.
    echo      - Go to: https://github.com/settings/tokens/new
    echo      - Add a note (e.g., 'Docker Login').
    echo      - Under 'Select scopes', check the box for 'read:packages'.
    echo      - Click 'Generate token' and copy the token.
    echo   2. Run the following command in your terminal, replacing ^<TOKEN^> with your copied token:
    echo.
    echo      echo ^<TOKEN^> | docker login ghcr.io -u ^<YOUR_GITHUB_USERNAME^> --password-stdin
    echo.
    
    pause
    
    rem Verify login by trying to pull again
    echo Verifying access...
    docker pull %IMAGE_NAME%:%TAG%
    if %errorlevel% neq 0 (
        echo Error: Still unable to pull the Docker image.
        echo Please ensure you have generated the PAT with the correct scope and run the login command successfully.
        pause
        exit /b 1
    )
    echo ✅ Successfully authenticated and pulled the application image.
)

echo.
echo --- Docker Setup Complete! ---
echo You can now run the application using the 'run.bat' script.
pause