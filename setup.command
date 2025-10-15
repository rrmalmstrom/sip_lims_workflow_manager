#!/bin/bash
# This script sets up the Conda environment for the SIP LIMS Workflow Manager.

# Exit on any error
set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Get the environment name from the first argument, or default to 'sip-lims'
ENV_NAME=${1:-sip-lims}

echo "--- Setting up SIP LIMS Workflow Manager: $ENV_NAME ---"

echo "Cloning or updating the script repository..."
if [ -d "scripts" ]; then
    cd scripts
    git pull
    cd ..
else
    # Use the HTTPS URL for the repository
    git clone https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git scripts
fi

# --- Conda Environment Setup ---

# 1. Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed or not in your PATH."
    echo "Please install Miniconda or Anaconda and ensure it's added to your shell's PATH."
    exit 1
fi

echo "Conda found. Proceeding with environment setup..."

# 2. Create or update the environment from the lock file
if conda env list | grep -q "^$ENV_NAME\s"; then
    echo "Environment '$ENV_NAME' already exists. Updating..."
    # The --prune option removes packages that are no longer in the lock file
    conda env update --name "$ENV_NAME" --file environment.yml --prune
else
    echo "Environment '$ENV_NAME' not found. Creating..."
    conda env create --name "$ENV_NAME" -f environment.yml
fi

echo "✅ Conda environment '$ENV_NAME' is up to date."

echo ""
echo "✅ Setup completed successfully!"
echo "You can now run the application using run.command."
