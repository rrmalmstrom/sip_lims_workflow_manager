#!/bin/bash
# Enhanced SIP LIMS Workflow Manager Docker Runner
# Combines legacy Docker functionality with current ESP features

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager (Docker) ---"

# Auto-detect host user ID for proper file permissions on shared drives
detect_user_ids() {
    export USER_ID=$(id -u)
    export GROUP_ID=$(id -g)
    echo "Detected User ID: $USER_ID, Group ID: $GROUP_ID"
}

# Mode Detection Function (from current ESP)
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# Script Path Selection Function (adapted from current ESP for Docker)
select_script_path() {
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        echo ""
        echo "Choose script source for this session:"
        echo "1) Development scripts (../sip_scripts_dev)"
        echo "2) Production scripts (../sip_scripts_prod)"
        echo ""
        printf "Enter choice (1 or 2): "
        read choice
        choice=$(echo "$choice" | tr -d '\r\n' | xargs)
        
        case $choice in
            1)
                SCRIPTS_PATH="../sip_scripts_dev"
                echo "✅ Using development scripts from: $SCRIPTS_PATH"
                export APP_ENV="development"
                ;;
            2)
                SCRIPTS_PATH="../sip_scripts_prod"
                echo "✅ Using production scripts from: $SCRIPTS_PATH"
                export APP_ENV="production"
                ;;
            *)
                echo "❌ ERROR: Invalid choice '$choice'. Please enter 1 or 2."
                echo "Exiting."
                exit 1
                ;;
        esac
    else
        echo "🏭 Production mode - using production scripts"
        SCRIPTS_PATH="../sip_scripts_prod"
        export APP_ENV="production"
    fi
    
    # Verify script directory exists
    if [ ! -d "$SCRIPTS_PATH" ]; then
        echo "❌ ERROR: Script directory not found: $SCRIPTS_PATH"
        echo "Please run setup.command first to initialize script repositories."
        exit 1
    fi
    
    echo "📁 Script path: $SCRIPTS_PATH"
    export SCRIPTS_PATH
}

# Call user ID detection
detect_user_ids

# Call script path selection
select_script_path

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Prompt user to provide the project folder path (for shared network drives)
echo ""
echo "Please drag and drop your project folder here, then press Enter:"
printf "> "
read PROJECT_PATH

# Clean up the path (removes potential quotes, trailing spaces, and control characters)
PROJECT_PATH=$(echo "$PROJECT_PATH" | tr -d '\r\n' | sed "s/'//g" | xargs)

# Exit if the path is empty
if [ -z "$PROJECT_PATH" ]; then
    echo "❌ ERROR: No folder provided. Exiting."
    exit 1
fi

# Validate that the project path exists and is a directory
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ ERROR: Project folder does not exist or is not a directory: $PROJECT_PATH"
    echo "Please provide a valid folder path."
    exit 1
fi

echo "✅ Selected project folder: $PROJECT_PATH"
export PROJECT_PATH

# Launch using docker-compose with user ID mapping
echo "Launching application with Docker Compose..."
echo "--- Environment Variables ---"
echo "USER_ID: $USER_ID"
echo "GROUP_ID: $GROUP_ID"
echo "PROJECT_PATH: $PROJECT_PATH"
echo "SCRIPTS_PATH: $SCRIPTS_PATH"
echo "APP_ENV: $APP_ENV"
echo "--- Starting Container ---"

# Use docker-compose for enhanced user ID mapping and volume management
docker-compose up

echo "Application has been shut down."