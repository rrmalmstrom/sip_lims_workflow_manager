#!/bin/bash
# Branch utilities for bash scripts
# Provides wrapper functions that call Python utilities for branch detection and Docker tag generation

# Get the directory where this script is located
UTILS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$(dirname "$UTILS_DIR")"

# Error handling function
handle_python_error() {
    local exit_code=$1
    local function_name="$2"
    
    if [ $exit_code -ne 0 ]; then
        echo "Error: $function_name failed (exit code: $exit_code)" >&2
        return $exit_code
    fi
    return 0
}

# Get current branch name
get_current_branch() {
    local result
    result=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from utils.branch_utils import get_current_branch
    print(get_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    local exit_code=$?
    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        echo "$result"
        return 0
    else
        handle_python_error $exit_code "get_current_branch"
        return $exit_code
    fi
}

# Get Docker tag for current branch
get_current_branch_tag() {
    local result
    result=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from utils.branch_utils import get_docker_tag_for_current_branch
    print(get_docker_tag_for_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    local exit_code=$?
    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        echo "$result"
        return 0
    else
        handle_python_error $exit_code "get_current_branch_tag"
        return $exit_code
    fi
}

# Get local Docker image name with branch tag
get_local_image_name() {
    local result
    result=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from utils.branch_utils import get_local_image_name_for_current_branch
    print(get_local_image_name_for_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    local exit_code=$?
    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        echo "$result"
        return 0
    else
        handle_python_error $exit_code "get_local_image_name"
        return $exit_code
    fi
}

# Get remote Docker image name with branch tag
get_remote_image_name() {
    local result
    result=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from utils.branch_utils import get_remote_image_name_for_current_branch
    print(get_remote_image_name_for_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    local exit_code=$?
    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        echo "$result"
        return 0
    else
        handle_python_error $exit_code "get_remote_image_name"
        return $exit_code
    fi
}

# Get comprehensive branch information
get_branch_info() {
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from utils.branch_utils import get_branch_info
    info = get_branch_info()
    for key, value in info.items():
        print(f'{key}={value}')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Validate if we're in a Git repository
validate_git_repository() {
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "Error: Not in a Git repository" >&2
        return 1
    fi
    return 0
}

# Fallback function for branch detection using pure bash
get_current_branch_fallback() {
    local branch
    
    # Try git command directly
    if branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); then
        if [ "$branch" = "HEAD" ]; then
            # Detached HEAD - get short SHA
            local sha
            if sha=$(git rev-parse --short HEAD 2>/dev/null); then
                echo "detached-$sha"
                return 0
            fi
        else
            echo "$branch"
            return 0
        fi
    fi
    
    echo "Error: Could not detect branch" >&2
    return 1
}

# Fallback function for tag sanitization using pure bash
sanitize_branch_for_docker_tag_fallback() {
    local branch="$1"
    
    if [ -z "$branch" ]; then
        echo "Error: Branch name cannot be empty" >&2
        return 1
    fi
    
    # Convert to lowercase and replace invalid characters
    local tag
    tag=$(echo "$branch" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9.-]/-/g')
    
    # Remove leading and trailing periods and dashes
    tag=$(echo "$tag" | sed 's/^[.-]*//; s/[.-]*$//')
    
    # Truncate if too long (128 chars)
    if [ ${#tag} -gt 128 ]; then
        tag="${tag:0:128}"
        # Remove trailing periods and dashes after truncation
        tag=$(echo "$tag" | sed 's/[.-]*$//')
    fi
    
    if [ -z "$tag" ]; then
        echo "Error: Branch name resulted in empty tag" >&2
        return 1
    fi
    
    echo "$tag"
    return 0
}

# Robust branch tag function with fallback
get_current_branch_tag_robust() {
    local tag
    
    # Try Python utilities first
    if tag=$(get_current_branch_tag 2>/dev/null); then
        echo "$tag"
        return 0
    fi
    
    echo "Warning: Python utilities failed, using fallback method" >&2
    
    # Fallback to bash implementation
    local branch
    if branch=$(get_current_branch_fallback); then
        if tag=$(sanitize_branch_for_docker_tag_fallback "$branch"); then
            echo "$tag"
            return 0
        fi
    fi
    
    echo "Error: All branch detection methods failed" >&2
    return 1
}

# Test function to verify utilities work
test_branch_utils() {
    echo "Testing branch utilities..."
    
    # Test Git repository validation
    if ! validate_git_repository; then
        echo "❌ Not in a Git repository"
        return 1
    fi
    echo "✅ Git repository validated"
    
    # Test branch detection
    local branch
    if branch=$(get_current_branch); then
        echo "✅ Current branch: $branch"
    else
        echo "❌ Branch detection failed"
        return 1
    fi
    
    # Test tag generation
    local tag
    if tag=$(get_current_branch_tag); then
        echo "✅ Docker tag: $tag"
    else
        echo "❌ Tag generation failed"
        return 1
    fi
    
    # Test image name generation
    local local_image remote_image
    if local_image=$(get_local_image_name) && remote_image=$(get_remote_image_name); then
        echo "✅ Local image: $local_image"
        echo "✅ Remote image: $remote_image"
    else
        echo "❌ Image name generation failed"
        return 1
    fi
    
    echo "✅ All branch utilities working correctly"
    return 0
}

# If script is run directly, run tests
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    test_branch_utils
fi