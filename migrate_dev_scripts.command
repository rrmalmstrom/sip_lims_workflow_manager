#!/bin/bash
# This is a ONE-TIME script to migrate the local development scripts
# from the nested 'scripts' directory to a sibling 'sip_scripts_dev' directory.

# Exit on any error
set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Development Script Migration ---"

# Check if the nested 'scripts' directory exists
if [ ! -d "scripts" ]; then
    echo "✅ No nested 'scripts' directory found. Nothing to migrate."
    exit 0
fi

# Check if the target directory already exists
if [ -d "../sip_scripts_dev" ]; then
    echo "⚠️  Warning: The target directory '../sip_scripts_dev' already exists."
    echo "Please move any valuable work from the nested 'scripts' directory manually."
    echo "This script will not overwrite the existing external directory."
    exit 1
fi

echo "Moving './scripts' to '../sip_scripts_dev'..."
mv ./scripts ../sip_scripts_dev

echo "✅ Migration complete."
echo "Your local development scripts are now located at '../sip_scripts_dev'."
echo "You can now run the main 'setup.command' to configure the production scripts."