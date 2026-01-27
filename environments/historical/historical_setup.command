#!/bin/bash
# This script sets up the Conda environment for the SIP LIMS Workflow Manager.

# Exit on any error
set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Get the environment name from the first argument, or default to 'sip-lims'
ENV_NAME=${1:-sip-lims}

echo "--- Setting up SIP LIMS Workflow Manager: $ENV_NAME ---"

# NEW: Mode Detection Function
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# NEW: Create config directory and update .gitignore
setup_config_directory() {
    mkdir -p config
    if ! grep -q "config/developer.marker" .gitignore; then
        echo "" >> .gitignore
        echo "# Developer Environment Configuration" >> .gitignore
        echo "config/developer.marker" >> .gitignore
    fi
}

# NEW: Mode-aware script repository setup
setup_script_repositories() {
    MODE=$(detect_mode)
    echo "Detected mode: $MODE"
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        
        # Give guidance on migration
        # This check is intentionally left blank.
        # The logic for handling a nested 'scripts' directory was deprecated and the
        # one-time migration script has been removed. New setups should not have this directory.
        if [ -d "scripts" ]; then
            echo "WARNING: A nested 'scripts' directory was found."
            echo "This project structure is deprecated. Please refer to the documentation on repository setup."
        fi
        
        echo "Choose setup option:"
        echo "1) Work offline (skip remote repository updates)"
        echo "2) Connect to remotes to check for updates"
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1)
                echo "Working offline - skipping repository updates"
                SKIP_REPOS=true
                ;;
            2)
                echo "Connecting to remotes for updates"
                SKIP_REPOS=false
                ;;
            *)
                echo "Invalid choice, defaulting to offline mode"
                SKIP_REPOS=true
                ;;
        esac
    else
        echo "🏭 Production mode detected - automatically updating repositories"
        SKIP_REPOS=false
    fi
    
    if [ "$SKIP_REPOS" = false ]; then
        setup_external_repositories "$MODE"
    fi
}

# NEW: External repository setup function
setup_external_repositories() {
    local mode=$1
    echo "Setting up external script repositories..."
    
    # Go to parent directory
    cd ..
    
    # Always setup production scripts
    echo "Setting up production scripts..."
    if [ -d "sip_scripts_prod" ]; then
        cd sip_scripts_prod
        git pull
        cd ..
    else
        # The production scripts are from the main 'workflow_gui' repo
        git clone https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git sip_scripts_prod
        # Set the upstream branch to ensure git pull works without extra arguments
        (cd sip_scripts_prod && git branch --set-upstream-to=origin/main main)
    fi
    
    # In developer mode, we only need to ensure the dev directory exists.
    # The migration script handles the content.
    if [ "$mode" = "developer" ]; then
        if [ ! -d "sip_scripts_dev" ]; then
             echo "NOTE: Development scripts directory '../sip_scripts_dev' not found."
             echo "Please clone it from the repository if you are a developer."
        fi
    fi
    
    # Return to app directory
    cd "$DIR"
}

# NEW: App repository setup function
setup_app_repository() {
    echo "Configuring main application repository..."
    # Check if the upstream branch is already set
    if ! git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
        echo "Upstream branch not set. Configuring for 'main' branch..."
        git branch --set-upstream-to=origin/main main
    else
        echo "Upstream branch already configured."
    fi
}

# MAIN EXECUTION FLOW

# NEW: Setup configuration
setup_config_directory

# NEW: Setup the application repository itself
setup_app_repository

# MODIFIED: Script repository setup
setup_script_repositories

# --- Conda Environment Setup ---

# 1. Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed or not in your PATH."
    echo "Please install Miniconda or Anaconda and ensure it's added to your shell's PATH."
    exit 1
fi

echo "Conda found. Proceeding with environment setup..."

# 2. Create or update the environment from the lock file
if conda env list | grep -q "^$ENV_NAME\s"; then
    echo "Environment '$ENV_NAME' already exists. Updating..."
    # The --prune option removes packages that are no longer in the lock file
    conda env update --name "$ENV_NAME" --file environment.yml --prune
else
    echo "Environment '$ENV_NAME' not found. Creating..."
    conda env create --name "$ENV_NAME" -f environment.yml
fi

echo "✅ Conda environment '$ENV_NAME' is up to date."

echo ""
echo "✅ Setup completed successfully!"
echo "You can now run the application using run.command."
