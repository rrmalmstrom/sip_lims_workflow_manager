#!/bin/bash
# SIP LIMS Workflow Manager Setup - Native Mac Distribution
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🧬 Setting up SIP LIMS Workflow Manager for Mac"
ENV_NAME="sip-lims"

# Check conda installation
if ! command -v conda &> /dev/null; then
    echo "❌ ERROR: Conda not found"
    echo "📥 Please install Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
    echo "💡 After installation, restart Terminal and run this script again"
    exit 1
fi

echo "✅ Conda found: $(conda --version)"

# Remove existing environment if present
if conda env list | grep -q "^$ENV_NAME\s"; then
    echo "🔄 Removing existing environment '$ENV_NAME'..."
    conda env remove --name "$ENV_NAME" --yes
fi

# Create deterministic environment from Mac lock files
echo "🏗️  Creating deterministic environment from Mac lock files..."
if conda create --name "$ENV_NAME" --file environments/mac/conda-lock-mac.txt --yes; then
    echo "✅ Conda packages installed from Mac lock file"
    
    # Activate environment and install pip packages
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
    
    if pip install -r environments/mac/requirements-lock-mac-optimized.txt; then
        echo "✅ Pip packages installed from Mac lock file"
        echo "🎉 Environment created successfully using deterministic Mac lock files"
    else
        echo "❌ ERROR: Pip package installation failed"
        exit 1
    fi
else
    echo "❌ ERROR: Conda environment creation failed"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo "🚀 Run './run.command' to launch the application"
echo "💡 Or use 'python run.py --help' for advanced options"