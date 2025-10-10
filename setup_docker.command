#!/bin/bash
# This script handles the one-time setup for the Docker-based workflow.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Define the image name and tag
IMAGE_NAME="ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
TAG="latest"

echo "--- Docker Setup for SIP LIMS Workflow Manager ---"

# 1. Check if Docker is running
echo "Step 1: Checking for Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    echo "Please install and start Docker Desktop, then run this script again."
    echo "Download from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi
echo "✅ Docker is running."

# 2. Check if user is logged into GitHub Container Registry
echo -e "\nStep 2: Checking GitHub Container Registry access..."
if docker pull ${IMAGE_NAME}:${TAG} > /dev/null 2>&1; then
    echo "✅ Successfully pulled image. You are already logged in."
else
    echo "⚠️ You are not logged into the GitHub Container Registry (ghcr.io)."
    echo "To pull the private application image, you need to authenticate."
    echo -e "\nPlease follow these steps:"
    echo "  1. Create a GitHub Personal Access Token (PAT) with the 'read:packages' scope."
    echo "     - Go to: https://github.com/settings/tokens/new"
    echo "     - Add a note (e.g., 'Docker Login')."
    echo "     - Under 'Select scopes', check the box for 'read:packages'."
    echo "     - Click 'Generate token' and copy the token."
    echo "  2. Run the following command in your terminal, replacing <TOKEN> with your copied token:"
    echo -e "\n     echo <TOKEN> | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin\n"
    
    read -p "Press [Enter] after you have successfully run the login command."
    
    # Verify login by trying to pull again
    echo "Verifying access..."
    if ! docker pull ${IMAGE_NAME}:${TAG}; then
        echo "Error: Still unable to pull the Docker image."
        echo "Please ensure you have generated the PAT with the correct scope and run the login command successfully."
        exit 1
    fi
    echo "✅ Successfully authenticated and pulled the application image."
fi

echo -e "\n--- Docker Setup Complete! ---"
echo "You can now run the application using the 'run.command' script."