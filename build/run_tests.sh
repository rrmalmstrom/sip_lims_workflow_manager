#!/bin/bash
# This script runs the test suite, assuming the environment is already set up.
# Ensure Docker Desktop is running before running tests.

# Exit on any error
set -e

echo "--- Activating Conda Environment for Testing ---"
eval "$(conda shell.bash hook)"
conda activate sip-lims

echo "--- Running Pytest Suite ---"
pytest -v

conda deactivate
echo "--- Test Run Complete ---"