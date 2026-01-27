#!/bin/bash
# SIP LIMS Workflow Manager Launcher - Native Mac Distribution
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🧬 Starting SIP LIMS Workflow Manager"
ENV_NAME="sip-lims"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ ERROR: Conda not found"
    echo "🔧 Please run './setup.command' first"
    exit 1
fi

# Check if environment exists
if ! conda env list | grep -q "^$ENV_NAME\s"; then
    echo "❌ ERROR: Environment '$ENV_NAME' not found"
    echo "🔧 Please run './setup.command' first to create the environment"
    exit 1
fi

# Activate environment
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

echo "✅ Environment activated: $CONDA_DEFAULT_ENV"
echo "🚀 Launching workflow manager..."
echo ""

# Delegate to the sophisticated run.py with all its features
python run.py "$@"