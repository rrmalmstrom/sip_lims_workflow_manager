#!/bin/bash
#
# SIP LIMS Workflow Manager - macOS Launcher
# 
# This script provides a simple double-clickable launcher for macOS users.
# It automatically launches the unified Python launcher (run.py) with proper
# error handling and user feedback.
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory to ensure relative paths work
cd "$SCRIPT_DIR"

# Clear the screen for a clean start
clear

echo "🚀 SIP LIMS Workflow Manager - macOS Launcher"
echo "=============================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed or not in PATH"
    echo ""
    echo "Please install Python 3 and try again."
    echo "You can download Python from: https://www.python.org/downloads/"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Check if run.py exists
if [ ! -f "run.py" ]; then
    echo "❌ ERROR: run.py not found in current directory"
    echo ""
    echo "Please make sure you're running this script from the"
    echo "SIP LIMS Workflow Manager project directory."
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo "🐍 Launching Python workflow manager..."
echo ""

# Launch the Python script with no command line arguments (default behavior)
python3 run.py

# Capture the exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Workflow completed successfully"
else
    echo "❌ Workflow exited with error code: $EXIT_CODE"
fi

echo ""
echo "Press any key to close this window..."
read -n 1

exit $EXIT_CODE