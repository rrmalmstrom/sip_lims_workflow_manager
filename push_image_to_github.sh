#!/bin/bash
# Push Docker Image to GitHub Container Registry
# Tags and pushes local sip-lims-workflow-manager:latest to GitHub

set -e

echo "📤 Pushing Docker Image to GitHub Container Registry"
echo "===================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if local image exists
echo ""
echo "🔍 Checking for local image..."
if ! docker images sip-lims-workflow-manager:latest --format "{{.Repository}}" | grep -q "sip-lims-workflow-manager"; then
    echo "❌ ERROR: Local image 'sip-lims-workflow-manager:latest' not found"
    echo "   Run ./build_image_from_lock_files.sh first to build the image"
    exit 1
fi

echo "   ✅ Found local image: sip-lims-workflow-manager:latest"

# Get image metadata
IMAGE_ID=$(docker images sip-lims-workflow-manager:latest --format "{{.ID}}")
IMAGE_SIZE=$(docker images sip-lims-workflow-manager:latest --format "{{.Size}}")
CREATED=$(docker images sip-lims-workflow-manager:latest --format "{{.CreatedAt}}")

echo "   📋 Image ID: $IMAGE_ID"
echo "   📋 Size: $IMAGE_SIZE"
echo "   📋 Created: $CREATED"

# Tag the image for GitHub Container Registry
echo ""
echo "🏷️  Tagging image for GitHub Container Registry..."
docker tag sip-lims-workflow-manager:latest ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest

if [ $? -eq 0 ]; then
    echo "   ✅ Image tagged successfully"
else
    echo "   ❌ ERROR: Failed to tag image"
    exit 1
fi

# Push to GitHub Container Registry
echo ""
echo "📤 Pushing to GitHub Container Registry..."
echo "   Registry: ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"

if ! docker push ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest; then
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
REMOTE_DIGEST=$(docker inspect ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --format='{{index .RepoDigests 0}}' 2>/dev/null || echo "unknown")

echo ""
echo "🎉 Push Complete!"
echo "================="
echo "✅ Local image tagged and pushed to GitHub Container Registry"
echo "✅ Users can now pull the updated deterministic image"
echo ""
echo "📋 Registry Details:"
echo "   - Repository: ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
echo "   - Tag: latest"
echo "   - Image ID: $IMAGE_ID"
echo "   - Size: $IMAGE_SIZE"
echo "   - Digest: $REMOTE_DIGEST"
echo ""
echo "🔄 Users will get this image when they run:"
echo "   ./run.command (production mode)"
echo ""
echo "💡 The image is now available for production use with deterministic packages!"