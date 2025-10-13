#!/bin/bash
# This script runs the SIP LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager ---"

# Define the image name
IMAGE_NAME="sip-lims-workflow-manager:latest"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Prompt user to provide the project folder path
echo ""
echo "Please drag and drop your project folder here, then press Enter:"
read -r PROJECT_PATH

# Clean up the path (removes potential quotes and trailing spaces)
PROJECT_PATH=$(echo "$PROJECT_PATH" | sed "s/'//g" | xargs)

# Exit if the path is empty
if [ -z "$PROJECT_PATH" ]; then
    echo "No folder provided. Exiting."
    exit 0
fi

echo "Selected project folder: $PROJECT_PATH"

# --- Environment Mode Selection ---
ENV_FLAG=""
if [ -f ".env" ]; then
    echo ""
    echo "Development environment detected (.env file found)."
    echo "Please choose a run mode:"
    echo "  1. Development (Default - Update checks disabled)"
    echo "  2. Production (Update checks enabled)"
    read -p "Enter choice [1]: " mode_choice

    if [[ "$mode_choice" == "2" ]]; then
        echo "Running in PRODUCTION mode."
        ENV_FLAG="-e APP_ENV=production"
    else
        echo "Running in DEVELOPMENT mode."
        ENV_FLAG="--env-file .env"
    fi
else
    # For end-users, no .env file, default to production
    ENV_FLAG="-e APP_ENV=production"
fi
# --- End Environment Mode Selection ---

# Define the central scripts directory on the host
SCRIPTS_DIR="$HOME/.sip_lims_workflow_manager/scripts"

# --- Script Repository Management ---
# This logic ensures the scripts are cloned on first run and updated on subsequent runs.
# This must happen on the HOST, not in the container.
SCRIPT_REPO_URL="https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git"

if [ -d "$SCRIPTS_DIR/.git" ]; then
    echo "Scripts repository found. Checking for updates..."
    (cd "$SCRIPTS_DIR" && git pull)
else
    echo "Scripts repository not found. Cloning..."
    # Remove the directory if it's just an empty folder to ensure clean clone
    rm -rf "$SCRIPTS_DIR"
    git clone "$SCRIPT_REPO_URL" "$SCRIPTS_DIR"
fi
# --- End Script Repository Management ---

# Run the application in a new container, mounting the correct volumes
echo "Launching application..."
docker run --rm -it -p 8501:8501 $ENV_FLAG -v "$PROJECT_PATH:/data" -v "$SCRIPTS_DIR:/workflow-scripts" -w "/data" "$IMAGE_NAME"

echo "Application has been shut down."