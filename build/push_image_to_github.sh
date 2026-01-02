#!/bin/bash
# Push Docker Image to GitHub Container Registry
# Tags and pushes local branch-specific image to GitHub

set -e

# Source branch utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/branch_utils.sh"

echo "📤 Pushing Docker Image to GitHub Container Registry"
echo "===================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Get branch-aware image names
echo ""
echo "🌿 Detecting branch and generating image names..."
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

# Check if local image exists
echo ""
echo "🔍 Checking for local image..."
if ! docker images "$LOCAL_IMAGE_NAME" --format "{{.Repository}}" | grep -q "sip-lims-workflow-manager"; then
    echo "❌ ERROR: Local image '$LOCAL_IMAGE_NAME' not found"
    echo "   Run ./build/build_image_from_lock_files.sh first to build the image"
    exit 1
fi

echo "   ✅ Found local image: $LOCAL_IMAGE_NAME"

# Get image metadata
IMAGE_ID=$(docker images "$LOCAL_IMAGE_NAME" --format "{{.ID}}")
IMAGE_SIZE=$(docker images "$LOCAL_IMAGE_NAME" --format "{{.Size}}")
CREATED=$(docker images "$LOCAL_IMAGE_NAME" --format "{{.CreatedAt}}")

echo "   📋 Image ID: $IMAGE_ID"
echo "   📋 Size: $IMAGE_SIZE"
echo "   📋 Created: $CREATED"

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

# Get final metadata
REMOTE_DIGEST=$(docker inspect "$REMOTE_IMAGE_NAME" --format='{{index .RepoDigests 0}}' 2>/dev/null || echo "unknown")

echo ""
echo "🎉 Push Complete!"
echo "================="
echo "✅ Local image tagged and pushed to GitHub Container Registry"
echo "✅ Users can now pull the updated deterministic image"
echo ""
echo "📋 Registry Details:"
echo "   - Repository: ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
echo "   - Tag: $CURRENT_BRANCH"
echo "   - Branch: $(git branch --show-current)"
echo "   - Image ID: $IMAGE_ID"
echo "   - Size: $IMAGE_SIZE"
echo "   - Digest: $REMOTE_DIGEST"
echo ""
echo "🔄 Users will get this image when they run:"
echo "   ./run.command (and are on the same branch)"
echo ""
echo "💡 The image is now available with deterministic packages for branch: $(git branch --show-current)"