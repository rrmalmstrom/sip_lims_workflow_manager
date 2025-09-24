#!/bin/bash
# This script runs the LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting LIMS Workflow Manager ---"

# Check if the environment is up to date
if [ -f ".venv/install_receipt.txt" ]; then
    # Found a receipt, compare it to the current requirements
    shasum -a 256 -c .venv/install_receipt.txt --status
    if [ $? -ne 0 ]; then
        echo "ERROR: Dependencies have changed. Please run setup.command again."
        read -p "Press [Enter] to close this window."
        exit 1
    fi
else
    # No receipt found, means setup was never run
    echo "ERROR: Application has not been set up. Please run setup.command."
    read -p "Press [Enter] to close this window."
    exit 1
fi

# Check for script updates
echo "Checking for script updates..."
cd scripts
git fetch
UPDATE_STATUS=$(git status -uno)
cd ..

# Activate the virtual environment and run the app
source .venv/bin/activate

# Pass update status to the streamlit app
if [[ $UPDATE_STATUS == *"Your branch is behind"* ]]; then
    streamlit run app.py --server.headless=true --server.address=127.0.0.1 -- --scripts-update-available
else
    streamlit run app.py --server.headless=true --server.address=127.0.0.1
fi