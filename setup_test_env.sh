#!/bin/bash
# This script creates or updates the test environment.
# Run this once, or whenever the environment.yml file changes.

# Exit on any error
set -e

echo "--- Preparing Test Environment ---"

# 1. Ensure the conda environment is ready by running the setup script.
if [ -f "setup.command" ]; then
    ./setup.command
else
    echo "ERROR: setup.command not found. Cannot prepare test environment."
    exit 1
fi

echo "--- Test Environment is Ready ---"
echo "You can now run tests using ./run_tests.sh"