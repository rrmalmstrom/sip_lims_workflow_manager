#!/bin/bash
# This script handles the one-time setup for the Docker-based workflow.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# --- Configuration ---
# This is the name of the Docker image we will build and run.
IMAGE_NAME="sip-lims-workflow-manager"

echo "--- Docker Setup for SIP LIMS Workflow Manager ---"

# --- Dynamic Versioning ---
# Attempt to get the version from the latest Git tag.
echo "Step 1: Determining application version..."
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
    if [ -n "$LATEST_TAG" ]; then
        APP_VERSION=${LATEST_TAG//v/} # Remove 'v' prefix if it exists
        echo "✅ Found Git tag: Using version ${APP_VERSION}"
    else
        APP_VERSION="0.1.0-local"
        echo "⚠️ No Git tags found. Using default development version: ${APP_VERSION}"
    fi
else
    APP_VERSION="0.1.0-detached"
    echo "⚠️ Not a Git repository. Using default detached version: ${APP_VERSION}"
fi
# --- End Dynamic Versioning ---

# 2. Check if Docker is running
echo -e "\nStep 2: Checking for Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    echo "Please install and start Docker Desktop, then run this script again."
    echo "Download from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi
echo "✅ Docker is running."

# 3. Build the Docker image from the local Dockerfile
echo -e "\nStep 3: Building the application Docker image..."
echo "This may take several minutes on the first run."

docker build \
    --build-arg "APP_VERSION=${APP_VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    .

# Check if the build was successful
if [ $? -ne 0 ]; then
    echo "Error: Docker build failed."
    echo "Please check the output above for errors."
    exit 1
fi

echo "✅ Docker image '${IMAGE_NAME}:latest' built successfully with version ${APP_VERSION}."

echo -e "\n--- Docker Setup Complete! ---"
echo "You can now run the application using the 'run.command' script."