#!/bin/bash
# This script updates the workflow scripts from the central Git repository.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/scripts"

echo "--- Updating Workflow Scripts ---"

git pull

echo "\nScripts are now up to date."
read -p "Press [Enter] to close this window."