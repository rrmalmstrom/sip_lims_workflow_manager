#!/bin/bash
# Enhanced SIP LIMS Workflow Manager Docker Runner
# Combines legacy Docker functionality with current ESP features and robust update detection

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Source branch utilities
source "$DIR/utils/branch_utils.sh"

echo "--- Starting SIP LIMS Workflow Manager (Docker) ---"

# Initialize branch-aware Docker image names
echo "🌿 Detecting branch and generating Docker image names..."
if ! validate_git_repository; then
    echo "❌ ERROR: Not in a valid Git repository"
    exit 1
fi

CURRENT_BRANCH=$(get_current_branch_tag)
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to detect current branch"
    echo "   Make sure you're on a proper branch (not detached HEAD)"
    exit 1
fi

LOCAL_IMAGE_NAME=$(get_local_image_name)
REMOTE_IMAGE_NAME=$(get_remote_image_name)

echo "   ✅ Current branch: $(git branch --show-current)"
echo "   ✅ Docker tag: $CURRENT_BRANCH"
echo "   ✅ Local image: $LOCAL_IMAGE_NAME"
echo "   ✅ Remote image: $REMOTE_IMAGE_NAME"

# Container Management Functions
stop_workflow_containers() {
    echo "🛑 Checking for running workflow manager containers..."
    
    # Find containers using workflow manager images (both local and remote, branch-aware)
    local workflow_containers=$(docker ps -a --filter "ancestor=$REMOTE_IMAGE_NAME" --filter "ancestor=$LOCAL_IMAGE_NAME" --format "{{.ID}} {{.Names}} {{.Status}}" 2>/dev/null)
    
    if [ -n "$workflow_containers" ]; then
        echo "📋 Found workflow manager containers:"
        echo "$workflow_containers" | while read container_id container_name status; do
            echo "    - $container_name ($container_id): $status"
        done
        
        # Stop and remove workflow manager containers
        local container_ids=$(echo "$workflow_containers" | awk '{print $1}')
        if [ -n "$container_ids" ]; then
            echo "🛑 Stopping workflow manager containers..."
            docker stop $container_ids >/dev/null 2>&1
            echo "🗑️  Removing workflow manager containers..."
            docker rm $container_ids >/dev/null 2>&1
            echo "✅ Workflow manager containers cleaned up"
        fi
    else
        echo "✅ No running workflow manager containers found"
    fi
}

# Update Detection Functions
check_docker_updates() {
    echo "🔍 Checking for Docker image updates..."
    
    # Use the update detector to check for Docker updates with branch-aware tag
    local update_result=$(python3 -c "
from src.update_detector import UpdateDetector
from utils.branch_utils import get_current_branch, sanitize_branch_for_docker_tag
import json

detector = UpdateDetector()
branch = get_current_branch()
tag = sanitize_branch_for_docker_tag(branch)

result = detector.check_docker_update(tag=tag, branch=branch)
print(json.dumps(result))
" 2>/dev/null)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        # Parse the JSON result to check if update is available and if chronology is uncertain
        local update_available=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('update_available', False) else 'false')
except:
    print('false')
")
        
        local chronology_uncertain=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('chronology_uncertain', False) else 'false')
except:
    print('false')
")
        
        local requires_confirmation=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('requires_user_confirmation', False) else 'false')
except:
    print('false')
")
        
        if [ "$update_available" = "true" ]; then
            if [ "$chronology_uncertain" = "true" ] && [ "$requires_confirmation" = "true" ]; then
                # Extract warning message and reason
                local warning_msg=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('warning', 'Chronology uncertain'))
except:
    print('Chronology uncertain')
")
                local reason=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('reason', 'Unknown reason'))
except:
    print('Unknown reason')
")
                
                echo "⚠️  **CHRONOLOGY WARNING**"
                echo "   $reason"
                echo "   $warning_msg"
                echo ""
                echo "The system cannot determine if your local Docker image is newer or older than the remote version."
                echo "Proceeding with the update might overwrite a newer local version with an older remote version."
                echo ""
                printf "Do you want to proceed with the Docker image update? (y/N): "
                read user_choice
                user_choice=$(echo "$user_choice" | tr '[:upper:]' '[:lower:]' | xargs)
                
                if [ "$user_choice" != "y" ] && [ "$user_choice" != "yes" ]; then
                    echo "❌ Docker image update cancelled by user"
                    echo "✅ Continuing with current local Docker image"
                    return 0
                fi
                echo "✅ User confirmed - proceeding with Docker image update..."
            else
                echo "📦 Docker image update available - updating to latest version..."
            fi
            
            # Get current image ID before cleanup
            local old_image_id=$(docker images "$REMOTE_IMAGE_NAME" --format "{{.ID}}" 2>/dev/null)
            
            # Clean up old image BEFORE pulling new one (since containers are already stopped)
            if [ -n "$old_image_id" ]; then
                echo "🧹 Removing old Docker image before update..."
                # Remove by tag first, then clean up any dangling images
                docker rmi "$REMOTE_IMAGE_NAME" >/dev/null 2>&1
                # Clean up dangling images to prevent disk space waste
                docker image prune -f >/dev/null 2>&1
                echo "✅ Old Docker image and dangling images cleaned up"
            fi
            
            # Pull the new image
            echo "📥 Pulling Docker image for branch: $(git branch --show-current)..."
            docker pull "$REMOTE_IMAGE_NAME"
            if [ $? -eq 0 ]; then
                echo "✅ Docker image updated successfully"
                return 0
            else
                echo "❌ ERROR: Docker image update failed"
                return 1
            fi
        else
            echo "✅ Docker image is up to date"
            return 0
        fi
    else
        echo "⚠️  Warning: Could not check for Docker updates, continuing with current version"
        return 1
    fi
}

check_and_download_scripts() {
    local scripts_dir="$1"
    local branch="${2:-main}"
    
    echo "🔍 Checking for script updates..."
    
    # Check for script updates using the new scripts updater
    local update_result=$(python3 src/scripts_updater.py --check-scripts --scripts-dir "$scripts_dir" --branch "$branch" 2>/dev/null)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        local update_available=$(echo "$update_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('update_available', False) else 'false')
except:
    print('false')
")
        
        if [ "$update_available" = "true" ]; then
            echo "📦 Script updates available - updating scripts..."
            python3 src/scripts_updater.py --update-scripts --scripts-dir "$scripts_dir" --branch "$branch"
            if [ $? -eq 0 ]; then
                echo "✅ Scripts updated successfully"
                return 0
            else
                echo "❌ ERROR: Failed to update scripts"
                return 1
            fi
        else
            echo "✅ Scripts are up to date"
            return 0
        fi
    else
        echo "⚠️  Warning: Could not check for script updates, continuing with current version"
        return 1
    fi
}

production_auto_update() {
    echo "🏭 Production mode - performing automatic updates..."
    
    # Check and update Docker image
    check_docker_updates
    
    # Set up centralized scripts directory
    local scripts_dir="$HOME/.sip_lims_workflow_manager/scripts"
    
    # Check and download/update scripts
    check_and_download_scripts "$scripts_dir"
    
    # Set scripts path for production use
    SCRIPTS_PATH="$scripts_dir"
    export SCRIPTS_PATH
    export APP_ENV="production"
    
    # Use pre-built Docker image for production (branch-aware)
    export DOCKER_IMAGE="$REMOTE_IMAGE_NAME"
    
    echo "📁 Using centralized scripts: $SCRIPTS_PATH"
    echo "🐳 Using pre-built Docker image: $DOCKER_IMAGE"
    echo "🌿 Branch: $(git branch --show-current)"
}

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

# Developer Mode Choice Function
choose_developer_mode() {
    echo "🔧 Developer mode detected"
    echo ""
    echo "Choose your workflow mode:"
    echo "1) Production mode (auto-updates, centralized scripts)"
    echo "2) Development mode (local scripts, no auto-updates)"
    echo ""
    printf "Enter choice (1 or 2): "
    read dev_choice
    dev_choice=$(echo "$dev_choice" | tr -d '\r\n' | xargs)
    
    case $dev_choice in
        1)
            echo "✅ Using production mode workflow"
            return 0  # Production workflow
            ;;
        2)
            echo "✅ Using development mode workflow"
            return 1  # Development workflow
            ;;
        *)
            echo "❌ ERROR: Invalid choice '$dev_choice'. Please enter 1 or 2."
            echo "Exiting."
            exit 1
            ;;
    esac
}

# Development Script Path Selection Function
select_development_script_path() {
    echo ""
    echo "Please drag and drop your development scripts folder here, then press Enter:"
    printf "> "
    read SCRIPTS_PATH
    
    # Clean up the path (removes potential quotes, trailing spaces, and control characters)
    SCRIPTS_PATH=$(echo "$SCRIPTS_PATH" | tr -d '\r\n' | sed "s/'//g" | xargs)
    
    # Exit if the path is empty
    if [ -z "$SCRIPTS_PATH" ]; then
        echo "❌ ERROR: No scripts folder provided. Exiting."
        exit 1
    fi
    
    # Validate that the scripts path exists and is a directory
    if [ ! -d "$SCRIPTS_PATH" ]; then
        echo "❌ ERROR: Scripts folder does not exist or is not a directory: $SCRIPTS_PATH"
        echo "Please provide a valid scripts folder path."
        exit 1
    fi
    
    echo "✅ Selected development scripts folder: $SCRIPTS_PATH"
    export SCRIPTS_PATH
    export APP_ENV="development"
    
    # Use local Docker build for development mode (branch-aware)
    export DOCKER_IMAGE="$LOCAL_IMAGE_NAME"
    
    echo "📁 Script path: $SCRIPTS_PATH"
    echo "🐳 Using local Docker build: $DOCKER_IMAGE"
    echo "🌿 Branch: $(git branch --show-current)"
}

# Main Mode and Update Logic
handle_mode_and_updates() {
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        # Developer detected - ask for production vs development workflow
        choose_developer_mode
        use_production_workflow=$?
        
        if [ $use_production_workflow -eq 0 ]; then
            # Developer chose production workflow - use auto-updates
            production_auto_update
        else
            # Developer chose development workflow - use local scripts
            select_development_script_path
        fi
    else
        # Regular production user - always use auto-updates
        production_auto_update
    fi
}

# Call user ID detection
detect_user_ids

# Stop any running workflow manager containers first
stop_workflow_containers

# Handle mode detection and updates
handle_mode_and_updates

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

# Extract project folder name for display purposes
PROJECT_NAME=$(basename "$PROJECT_PATH")
echo "📁 Project name: $PROJECT_NAME"

export PROJECT_PATH
export PROJECT_NAME

# Launch using docker-compose with user ID mapping
echo "Launching application with Docker Compose..."
echo "--- Environment Variables ---"
echo "USER_ID: $USER_ID"
echo "GROUP_ID: $GROUP_ID"
echo "PROJECT_PATH: $PROJECT_PATH"
echo "PROJECT_NAME: $PROJECT_NAME"
echo "SCRIPTS_PATH: $SCRIPTS_PATH"
echo "APP_ENV: $APP_ENV"
echo "--- Starting Container ---"

# Use docker-compose for enhanced user ID mapping and volume management
docker-compose up

echo "Application has been shut down."