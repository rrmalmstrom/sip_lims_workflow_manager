#!/bin/bash
# This script runs the SIP LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager ---"

# NOTE: The old environment checks are temporarily removed for this test.
# We will build a new check system for the conda environment later.

# Initialize conda for this script session, then activate the environment
eval "$(conda shell.bash hook)"
conda activate sip-lims

# Launch Streamlit with localhost-only configuration
echo "Launching application in 'sip-lims' environment..."
echo "--- Using Python from: $(which python) ---"
streamlit run app.py --server.headless=true --server.address=127.0.0.1