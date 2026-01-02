#!/bin/bash
# Build Docker Image from Lock Files
# Uses existing conda-lock.txt and requirements-lock.txt for deterministic builds

set -e

# Source branch utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/branch_utils.sh"

echo "🔨 Building Docker Image from Lock Files"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Verify lock files exist
echo ""
echo "🔍 Verifying deterministic lock files..."
if [ ! -f "conda-lock.txt" ]; then
    echo "❌ ERROR: conda-lock.txt not found"
    echo "   Run ./build/generate_lock_files.sh first to create lock files"
    exit 1
fi

if [ ! -f "requirements-lock.txt" ]; then
    echo "❌ ERROR: requirements-lock.txt not found"
    echo "   Run ./build/generate_lock_files.sh first to create lock files"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ ERROR: Dockerfile not found"
    exit 1
fi

echo "   ✅ conda-lock.txt ($(wc -l < conda-lock.txt) packages)"
echo "   ✅ requirements-lock.txt ($(wc -l < requirements-lock.txt) packages)"
echo "   ✅ Dockerfile (deterministic)"

# Get branch-aware metadata
echo ""
echo "🌿 Detecting branch and generating tags..."
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
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
APP_VERSION=$(git describe --tags --always 2>/dev/null || echo "0.0.0-local")
BASE_IMAGE=$(grep "^FROM " Dockerfile | head -1 | cut -d' ' -f2)

echo "   ✅ Current branch: $(git branch --show-current)"
echo "   ✅ Docker tag: $CURRENT_BRANCH"
echo "   ✅ Local image: $LOCAL_IMAGE_NAME"

echo ""
echo "🔨 Building deterministic Docker image..."
echo "   📋 Build metadata:"
echo "      - Local Tag: $LOCAL_IMAGE_NAME"
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

if [ $? -eq 0 ]; then
    echo "   ✅ Image built successfully"
else
    echo "   ❌ ERROR: Image build failed"
    exit 1
fi

# Quick validation
echo ""
echo "🧪 Quick image validation..."
docker run --rm "$LOCAL_IMAGE_NAME" python --version
echo "   ✅ Image validation passed"

echo ""
echo "🎉 Build Complete!"
echo "=================="
echo "✅ Built deterministic image from lock files"
echo "✅ Local image: $LOCAL_IMAGE_NAME"
echo ""
echo "📋 Image Details:"
echo "   - Local Tag: $LOCAL_IMAGE_NAME"
echo "   - Branch: $(git branch --show-current)"
echo "   - Docker Tag: $CURRENT_BRANCH"
echo "   - Commit: $COMMIT_SHA"
echo "   - Build Date: $BUILD_DATE"
echo "   - Version: $APP_VERSION"
echo "   - Base Image: $BASE_IMAGE"
echo ""
echo "🚀 Next steps:"
echo "   - Test locally: ./run.command (choose development mode)"
echo "   - Push to remote: ./build/push_image_to_github.sh"