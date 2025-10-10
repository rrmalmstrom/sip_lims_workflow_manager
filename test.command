#!/bin/bash
# This script runs the pytest test suite inside a Docker container.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Define the image name and tag
IMAGE_NAME="ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
TAG="latest"

echo "--- Running Test Suite in Docker Container ---"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Build the Docker image if it doesn't exist locally.
# Subsequent runs will use the cached image for speed.
if [[ "$(docker images -q ${IMAGE_NAME}:${TAG} 2> /dev/null)" == "" ]]; then
    echo "Image not found locally. Building..."
    docker build -t ${IMAGE_NAME}:${TAG} .
    if [ $? -ne 0 ]; then
        echo "Error: Docker build failed."
        exit 1
    fi
fi

# Run the test suite in a new container
# Mounts local source code and .ssh directory for a realistic test environment
docker run --rm -it \
    -v "${DIR}/app.py:/app/app.py" \
    -v "${DIR}/src:/app/src" \
    -v "${DIR}/templates:/app/templates" \
    -v "${DIR}/utils:/app/utils" \
    -v "${DIR}/scripts:/app/scripts" \
    -v "${DIR}/tests:/app/tests" \
    -v "${DIR}/.ssh:/root/.ssh" \
    ${IMAGE_NAME}:${TAG} \
    /opt/conda/envs/sip-lims/bin/python -m pytest