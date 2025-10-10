@echo off
echo --- Starting SIP LIMS Workflow Manager in Docker ---

set "IMAGE_NAME=ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
set "TAG=latest"

rem Check if Docker is running
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    pause
    exit /b 1
)

rem Pull the latest image to ensure we are up to date
echo "Pulling latest application image..."
docker pull %IMAGE_NAME%:%TAG%

rem Run the application in a new container
echo "Launching application..."
docker run --rm -it ^
    -p 8501:8501 ^
    -v "%~dp0app.py:/app/app.py" ^
    -v "%~dp0src:/app/src" ^
    -v "%~dp0templates:/app/templates" ^
    -v "%~dp0utils:/app/utils" ^
    -v "%~dp0scripts:/app/scripts" ^
    -v "%~dp0.ssh:/root/.ssh" ^
    %IMAGE_NAME%:%TAG% ^
    /opt/conda/envs/sip-lims/bin/python -m streamlit run app.py --server.headless=true --server.address=0.0.0.0