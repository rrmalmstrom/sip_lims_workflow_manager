#!/bin/bash
# This script runs the test suite, assuming the environment is already set up.
# Run ./setup.command once first to create/update the environment.

# Exit on any error
set -e

echo "--- Activating Conda Environment for Testing ---"
eval "$(conda shell.bash hook)"
conda activate sip-lims

echo "--- Running Pytest Suite ---"
pytest -v

conda deactivate
echo "--- Test Run Complete ---"