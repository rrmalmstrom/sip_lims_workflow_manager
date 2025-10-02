#!/bin/bash
# This script runs the SIP LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager ---"

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

# Activate the virtual environment and run the app
source .venv/bin/activate

# Launch Streamlit with localhost-only configuration
# Note: Script updates are now handled through the unified GUI system
streamlit run app.py --server.headless=true --server.address=127.0.0.1