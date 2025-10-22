#!/bin/bash
# This script runs the SIP LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager ---"

# NEW: Mode Detection Function
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# NEW: Script Path Selection Function
select_script_path() {
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        echo ""
        echo "Choose script source for this session:"
        echo "1) Development scripts (../sip_scripts_dev)"
        echo "2) Production scripts (../sip_scripts_prod)"
        echo ""
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1)
                SCRIPT_PATH="../sip_scripts_dev"
                echo "✅ Using development scripts from: $SCRIPT_PATH"
                ;;
            2)
                SCRIPT_PATH="../sip_scripts_prod"
                echo "✅ Using production scripts from: $SCRIPT_PATH"
                ;;
            *)
                echo "⚠️  Invalid choice, defaulting to production scripts"
                SCRIPT_PATH="../sip_scripts_prod"
                ;;
        esac
    else
        echo "🏭 Production mode - using production scripts"
        SCRIPT_PATH="../sip_scripts_prod"
    fi
    
    # Verify script directory exists
    if [ ! -d "$SCRIPT_PATH" ]; then
        echo "❌ ERROR: Script directory not found: $SCRIPT_PATH"
        echo "Please run setup.command first to initialize script repositories."
        exit 1
    fi
    
    echo "📁 Script path: $SCRIPT_PATH"
}

# MAIN EXECUTION FLOW

# NEW: Call script path selection
select_script_path

# Initialize conda for this script session, then activate the environment
eval "$(conda shell.bash hook)"
conda activate sip-lims

# Launch Streamlit with localhost-only configuration
echo "Launching application in 'sip-lims' environment..."
echo "--- Active Conda Environment: $CONDA_DEFAULT_ENV ---"
echo "--- Using Python from: $(which python) ---"
echo "--- Using scripts from: $SCRIPT_PATH ---"

streamlit run app.py --server.headless=true --server.address=127.0.0.1 -- --script-path="$SCRIPT_PATH"