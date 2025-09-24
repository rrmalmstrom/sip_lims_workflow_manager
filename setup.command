#!/bin/bash
# This script sets up the virtual environment for the LIMS Workflow Manager.
# It should only be run once.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Setting up LIMS Workflow Manager ---"

# Check for Python 3.9+
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "Cloning or updating the script repository..."
# Set the command to use our specific deploy key
export GIT_SSH_COMMAND="ssh -i .ssh/deploy_key -o IdentitiesOnly=yes"

if [ -d "scripts" ]; then
    cd scripts
    git pull
    cd ..
else
    # Use the SSH URL for the repository
    git clone git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git scripts
fi

# Unset the variable so it doesn't interfere with other git operations
unset GIT_SSH_COMMAND

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

echo "Creating installation receipt..."
shasum -a 256 requirements.txt > .venv/install_receipt.txt

echo "\nSetup complete. You can now run the application using run.command."
read -p "Press [Enter] to close this window."