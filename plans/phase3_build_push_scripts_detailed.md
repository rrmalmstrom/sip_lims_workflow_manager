# Phase 3: Build and Push Scripts Enhancement Detail

## Overview
Modify `build_image_from_lock_files.sh` and `push_image_to_github.sh` to use branch-aware Docker tagging while preserving all existing functionality.

## Part A: Build Script Enhancement

### File: `build_image_from_lock_files.sh`

#### Current State Analysis
- **Line 60**: `docker build ... -t sip-lims-workflow-manager:latest`
- **Lines 49, 83**: Echo statements reference `:latest` tag
- **Lines 41-43**: SHA detection works correctly and must be preserved

#### Required Changes

##### 1. Add Branch Detection (after line 7)
```bash
#!/bin/bash
# Build Docker Image from Lock Files
# Uses existing conda-lock.txt and requirements-lock.txt for deterministic builds

set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Source branch utilities
source "$DIR/utils/branch_utils.sh"

echo "🔨 Building Docker Image from Lock Files"
echo "========================================"
```

##### 2. Detect Branch and Generate Tag (after line 39)
```bash
# Get build metadata
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
APP_VERSION=$(git describe --tags --always 2>/dev/null || echo "0.0.0-local")
BASE_IMAGE=$(grep "^FROM " Dockerfile | head -1 | cut -d' ' -f2)

# Get branch-aware Docker tag
echo ""
echo "🌿 Detecting branch for Docker tagging..."
BRANCH_TAG=$(get_current_branch_tag)
if [ $? -ne 0 ] || [ -z "$BRANCH_TAG" ]; then
    echo "❌ ERROR: Failed to detect current branch"
    echo "   Falling back to 'latest' tag"
    BRANCH_TAG="latest"
fi
LOCAL_IMAGE_NAME=$(get_local_image_name)
if [ $? -ne 0 ] || [ -z "$LOCAL_IMAGE_NAME" ]; then
    echo "❌ ERROR: Failed to generate local image name"
    echo "   Falling back to default naming"
    LOCAL_IMAGE_NAME="sip-lims-workflow-manager:$BRANCH_TAG"
fi

echo "   ✅ Branch tag: $BRANCH_TAG"
echo "   ✅ Local image: $LOCAL_IMAGE_NAME"
```

##### 3. Update Build Command (line 60)
```bash
echo ""
echo "🔨 Building deterministic Docker image..."
echo "   📋 Build metadata:"
echo "      - Local Image: $LOCAL_IMAGE_NAME"
echo "      - Branch Tag: $BRANCH_TAG"
echo "      - Commit: $COMMIT_SHA"
echo "      - Date: $BUILD_DATE"
echo "      - Version: $APP_VERSION"
echo "      - Base Image: $BASE_IMAGE"

# Build the deterministic image locally with branch-aware tag
docker build \
    --build-arg APP_VERSION="$APP_VERSION" \
    --build-arg COMMIT_SHA="$COMMIT_SHA" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    -t "$LOCAL_IMAGE_NAME" \
    .
```

##### 4. Update Success Messages (lines 78-91)
```bash
echo ""
echo "🎉 Build Complete!"
echo "=================="
echo "✅ Built deterministic image from lock files"
echo "✅ Local image: $LOCAL_IMAGE_NAME"
echo ""
echo "📋 Image Details:"
echo "   - Local Image: $LOCAL_IMAGE_NAME"
echo "   - Branch Tag: $BRANCH_TAG"
echo "   - Commit: $COMMIT_SHA"
echo "   - Build Date: $BUILD_DATE"
echo "   - Version: $APP_VERSION"
echo "   - Base Image: $BASE_IMAGE"
echo ""
echo "🚀 Next steps:"
echo "   - Test locally: ./run.command (choose development mode)"
echo "   - Push to remote: ./push_image_to_github.sh"
```

##### 5. Update Validation Command (line 73)
```bash
# Quick validation
echo ""
echo "🧪 Quick image validation..."
docker run --rm "$LOCAL_IMAGE_NAME" python --version
echo "   ✅ Image validation passed"
```

## Part B: Push Script Enhancement

### File: `push_image_to_github.sh`

#### Current State Analysis
- **Line 19**: Checks for `sip-lims-workflow-manager:latest`
- **Line 39**: Tags as `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest`
- **Line 53**: Pushes to `:latest` tag
- **Lines 78, 85**: Echo statements reference `:latest`

#### Required Changes

##### 1. Add Branch Detection (after line 8)
```bash
#!/bin/bash
# Push Docker Image to GitHub Container Registry
# Tags and pushes local branch-aware image to GitHub

set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Source branch utilities
source "$DIR/utils/branch_utils.sh"

echo "📤 Pushing Docker Image to GitHub Container Registry"
echo "===================================================="
```

##### 2. Detect Branch and Generate Names (after line 14)
```bash
# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Get branch-aware image names
echo ""
echo "🌿 Detecting branch for Docker operations..."
BRANCH_TAG=$(get_current_branch_tag)
if [ $? -ne 0 ] || [ -z "$BRANCH_TAG" ]; then
    echo "❌ ERROR: Failed to detect current branch"
    exit 1
fi

LOCAL_IMAGE_NAME=$(get_local_image_name)
if [ $? -ne 0 ] || [ -z "$LOCAL_IMAGE_NAME" ]; then
    echo "❌ ERROR: Failed to generate local image name"
    exit 1
fi

REMOTE_IMAGE_NAME=$(get_remote_image_name)
if [ $? -ne 0 ] || [ -z "$REMOTE_IMAGE_NAME" ]; then
    echo "❌ ERROR: Failed to generate remote image name"
    exit 1
fi

echo "   ✅ Branch tag: $BRANCH_TAG"
echo "   ✅ Local image: $LOCAL_IMAGE_NAME"
echo "   ✅ Remote image: $REMOTE_IMAGE_NAME"
```

##### 3. Update Local Image Check (line 19)
```bash
# Check if local image exists
echo ""
echo "🔍 Checking for local image..."
if ! docker images "$LOCAL_IMAGE_NAME" --format "{{.Repository}}" | grep -q "sip-lims-workflow-manager"; then
    echo "❌ ERROR: Local image '$LOCAL_IMAGE_NAME' not found"
    echo "   Run ./build_image_from_lock_files.sh first to build the image"
    exit 1
fi

echo "   ✅ Found local image: $LOCAL_IMAGE_NAME"
```

##### 4. Update Image Metadata (lines 28-34)
```bash
# Get image metadata
IMAGE_ID=$(docker images "$LOCAL_IMAGE_NAME" --format "{{.ID}}")
IMAGE_SIZE=$(docker images "$LOCAL_IMAGE_NAME" --format "{{.Size}}")
CREATED=$(docker images "$LOCAL_IMAGE_NAME" --format "{{.CreatedAt}}")

echo "   📋 Image ID: $IMAGE_ID"
echo "   📋 Size: $IMAGE_SIZE"
echo "   📋 Created: $CREATED"
```

##### 5. Add Safety Confirmation
```bash
# Safety confirmation
echo ""
echo "⚠️  CONFIRMATION REQUIRED"
echo "========================="
echo "You are about to push:"
echo "   Local:  $LOCAL_IMAGE_NAME"
echo "   Remote: $REMOTE_IMAGE_NAME"
echo "   Branch: $BRANCH_TAG"
echo ""
printf "Continue with push? (y/N): "
read -r confirmation
confirmation=$(echo "$confirmation" | tr '[:upper:]' '[:lower:]')

if [ "$confirmation" != "y" ] && [ "$confirmation" != "yes" ]; then
    echo "❌ Push cancelled by user"
    exit 0
fi
```

##### 6. Update Tagging Command (line 39)
```bash
# Tag the image for GitHub Container Registry
echo ""
echo "🏷️  Tagging image for GitHub Container Registry..."
docker tag "$LOCAL_IMAGE_NAME" "$REMOTE_IMAGE_NAME"

if [ $? -eq 0 ]; then
    echo "   ✅ Image tagged successfully"
else
    echo "   ❌ ERROR: Failed to tag image"
    exit 1
fi
```

##### 7. Update Push Command (line 53)
```bash
# Push to GitHub Container Registry
echo ""
echo "📤 Pushing to GitHub Container Registry..."
echo "   Registry: $REMOTE_IMAGE_NAME"

if ! docker push "$REMOTE_IMAGE_NAME"; then
    echo ""
    echo "❌ ERROR: Push failed. You may need to authenticate with GitHub Container Registry."
    echo ""
    echo "To authenticate, run:"
    echo "   echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
    echo ""
    echo "Or create a personal access token at:"
    echo "   https://github.com/settings/tokens"
    echo "   (Select 'write:packages' scope)"
    exit 1
fi

echo "   ✅ Image pushed successfully"
```

##### 8. Update Final Messages (lines 72-87)
```bash
# Get final metadata
REMOTE_DIGEST=$(docker inspect "$REMOTE_IMAGE_NAME" --format='{{index .RepoDigests 0}}' 2>/dev/null || echo "unknown")

echo ""
echo "🎉 Push Complete!"
echo "================="
echo "✅ Local image tagged and pushed to GitHub Container Registry"
echo "✅ Users can now pull the updated deterministic image"
echo ""
echo "📋 Registry Details:"
echo "   - Repository: $REMOTE_IMAGE_NAME"
echo "   - Branch Tag: $BRANCH_TAG"
echo "   - Image ID: $IMAGE_ID"
echo "   - Size: $IMAGE_SIZE"
echo "   - Digest: $REMOTE_DIGEST"
echo ""
echo "🔄 Users will get this image when they run:"
echo "   ./run.command (on $BRANCH_TAG branch)"
echo ""
echo "💡 The image is now available for branch-specific use with deterministic packages!"
```

## Error Handling

### Branch Detection Failures
```bash
# Robust branch detection with fallbacks
detect_branch_with_fallback() {
    local branch_tag
    branch_tag=$(get_current_branch_tag 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$branch_tag" ]; then
        echo "⚠️  Warning: Branch detection failed, attempting fallback..." >&2
        
        # Try direct git command
        local git_branch
        git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$git_branch" ] && [ "$git_branch" != "HEAD" ]; then
            # Manually sanitize branch name
            branch_tag=$(echo "$git_branch" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
            echo "   ✅ Fallback successful: $branch_tag" >&2
        else
            echo "   ❌ All branch detection methods failed" >&2
            return 1
        fi
    fi
    
    echo "$branch_tag"
    return 0
}
```

### Docker Command Failures
```bash
# Robust Docker operations with error checking
safe_docker_tag() {
    local source="$1"
    local target="$2"
    
    echo "🏷️  Tagging: $source → $target"
    
    if ! docker tag "$source" "$target"; then
        echo "❌ ERROR: Failed to tag image"
        echo "   Source: $source"
        echo "   Target: $target"
        echo "   Check if source image exists and Docker is running"
        return 1
    fi
    
    echo "   ✅ Tagged successfully"
    return 0
}
```

## Test Requirements

### Unit Tests: `tests/test_build_push_scripts.py`

```python
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestBuildScript:
    @patch('subprocess.run')
    def test_build_uses_branch_tag(self, mock_run):
        """Test that build script uses branch-specific tag"""
        # Mock successful branch detection
        with patch('utils.branch_utils.get_docker_tag_for_current_branch', return_value='main'):
            # Run build script and verify docker build command
            result = subprocess.run(['./build_image_from_lock_files.sh'], 
                                  capture_output=True, text=True)
            
            # Verify docker build was called with correct tag
            assert 'sip-lims-workflow-manager:main' in result.stdout

    def test_build_fallback_on_branch_failure(self):
        """Test build script fallback when branch detection fails"""
        with patch('utils.branch_utils.get_docker_tag_for_current_branch', side_effect=Exception("Branch detection failed")):
            result = subprocess.run(['./build_image_from_lock_files.sh'], 
                                  capture_output=True, text=True)
            
            # Should fallback to 'latest' tag
            assert 'latest' in result.stdout

class TestPushScript:
    @patch('subprocess.run')
    def test_push_uses_branch_tag(self, mock_run):
        """Test that push script uses branch-specific tag"""
        with patch('utils.branch_utils.get_docker_tag_for_current_branch', return_value='main'):
            # Mock user confirmation
            with patch('builtins.input', return_value='y'):
                result = subprocess.run(['./push_image_to_github.sh'], 
                                      capture_output=True, text=True)
                
                # Verify correct remote image name
                assert 'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main' in result.stdout

    def test_push_safety_confirmation(self):
        """Test that push script requires user confirmation"""
        with patch('utils.branch_utils.get_docker_tag_for_current_branch', return_value='main'):
            # Mock user declining confirmation
            with patch('builtins.input', return_value='n'):
                result = subprocess.run(['./push_image_to_github.sh'], 
                                      capture_output=True, text=True)
                
                assert 'cancelled by user' in result.stdout
                assert result.returncode == 0  # Should exit cleanly
```

## Success Criteria

- [ ] Build script uses branch-specific local tags
- [ ] Push script uses branch-specific remote tags
- [ ] Safety confirmation prevents accidental pushes
- [ ] Error handling works for branch detection failures
- [ ] Fallback logic maintains functionality
- [ ] All existing SHA embedding preserved
- [ ] Scripts work with both Python utilities and fallback methods
- [ ] User feedback clearly shows branch information

## Backward Compatibility Notes

- Scripts will automatically detect current branch
- Fallback to 'latest' tag if branch detection fails
- All existing functionality preserved
- No breaking changes to script interfaces
- Clear error messages guide users through issues