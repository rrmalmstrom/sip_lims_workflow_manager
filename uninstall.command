#!/bin/bash
# SIP LIMS Workflow Manager Uninstall Script
# This script removes the virtual environment and cloned scripts
# while preserving user project data.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=== SIP LIMS Workflow Manager Uninstall ==="
echo ""
echo "This will remove:"
echo "  - Python virtual environment (.venv/)"
echo "  - Cloned workflow scripts (scripts/)"
echo "  - SSH deploy key (.ssh/)"
echo ""
echo "This will PRESERVE:"
echo "  - Your project folders and data"
echo "  - Workflow configurations"
echo "  - Database files"
echo "  - Output files"
echo ""

# Confirmation prompt
read -p "Are you sure you want to uninstall? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    read -p "Press [Enter] to close this window."
    exit 0
fi

echo ""
echo "Starting uninstall process..."

# Function to safely remove directory
safe_remove() {
    local dir_path="$1"
    local dir_name="$2"
    
    if [ -d "$dir_path" ]; then
        echo "Removing $dir_name..."
        rm -rf "$dir_path"
        if [ $? -eq 0 ]; then
            echo "✓ Successfully removed $dir_name"
        else
            echo "✗ Failed to remove $dir_name"
            return 1
        fi
    else
        echo "✓ $dir_name not found (already removed)"
    fi
    return 0
}

# Remove virtual environment
safe_remove ".venv" "virtual environment"

# Remove cloned scripts
safe_remove "scripts" "workflow scripts"

# Remove SSH deploy key directory
safe_remove ".ssh" "SSH deploy key"

# Remove any cached Python files
if [ -d "__pycache__" ]; then
    echo "Removing Python cache files..."
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    echo "✓ Python cache files removed"
fi

# Remove any .pyc files
if find . -name "*.pyc" -type f | grep -q .; then
    echo "Removing compiled Python files..."
    find . -name "*.pyc" -type f -delete 2>/dev/null
    echo "✓ Compiled Python files removed"
fi

echo ""
echo "=== Uninstall Summary ==="
echo "✓ Virtual environment removed"
echo "✓ Workflow scripts removed"
echo "✓ SSH deploy key removed"
echo "✓ Cache files cleaned up"
echo ""
echo "Your project data has been preserved."
echo "To reinstall, run setup.command again."
echo ""
echo "Uninstall complete!"
read -p "Press [Enter] to close this window."