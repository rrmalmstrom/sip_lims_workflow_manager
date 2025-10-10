@echo off
rem This script runs the pytest test suite inside a Docker container.

set "IMAGE_NAME=ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
set "TAG=latest"

echo "--- Running Test Suite in Docker Container ---"

rem Check if Docker is running
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    exit /b 1
)

rem Build the Docker image if it doesn't exist locally.
rem Subsequent runs will use the cached image for speed.
docker images -q %IMAGE_NAME%:%TAG% | findstr . > nul
if %errorlevel% neq 0 (
    echo "Image not found locally. Building..."
    docker build -t %IMAGE_NAME%:%TAG% .
    if %errorlevel% neq 0 (
        echo "Error: Docker build failed."
        exit /b 1
    )
)

rem Run the test suite in a new container
rem Mounts local source code and .ssh directory for a realistic test environment
docker run --rm -it ^
    -v "%~dp0app.py:/app/app.py" ^
    -v "%~dp0src:/app/src" ^
    -v "%~dp0templates:/app/templates" ^
    -v "%~dp0utils:/app/utils" ^
    -v "%~dp0scripts:/app/scripts" ^
    -v "%~dp0tests:/app/tests" ^
    -v "%~dp0.ssh:/root/.ssh" ^
    %IMAGE_NAME%:%TAG% ^
    /opt/conda/envs/sip-lims/bin/python -m pytest