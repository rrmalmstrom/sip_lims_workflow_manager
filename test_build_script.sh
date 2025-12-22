#!/bin/bash
# Test version of build_and_push.sh that stops before pushing
# This allows us to test the build process without pushing to registry

set -e

echo "🧪 Testing Build Script (No Push)"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Step 1: Generate fresh lock files from environment.yml
echo ""
echo "📦 Step 1: Generating fresh lock files for deterministic build..."
echo "   Using: archive/environment-docker-final-validated.yml"

# Extract base image from current Dockerfile
BASE_IMAGE=$(grep "^FROM " Dockerfile | head -1 | cut -d' ' -f2)
echo "   📋 Base image from Dockerfile: $BASE_IMAGE"

# Build temporary image to generate lock files using current base image
echo "   🔨 Building temporary environment..."
docker build -f - -t temp-lock-generator . <<EOF
FROM $BASE_IMAGE
COPY archive/environment-docker-final-validated.yml ./environment.yml
RUN conda env create -f environment.yml
EOF

# Extract fresh lock files
echo "   📋 Extracting conda lock file..."
docker run --rm temp-lock-generator bash -c "conda list --explicit -n sip-lims-workflow-manager" > conda-lock-test.txt

echo "   📋 Extracting pip lock file..."
docker run --rm temp-lock-generator bash -c "/opt/conda/envs/sip-lims-workflow-manager/bin/pip freeze" > requirements-lock-test.txt

# Clean up temporary image
docker rmi temp-lock-generator > /dev/null

echo "   ✅ Lock files generated:"
echo "      - conda-lock-test.txt ($(wc -l < conda-lock-test.txt) packages)"
echo "      - requirements-lock-test.txt ($(wc -l < requirements-lock-test.txt) packages)"

# Step 2: Build deterministic image
echo ""
echo "🔨 Step 2: Building deterministic Docker image..."
echo "   Image: sip-lims-workflow-manager:build-test"

# Get build metadata
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
APP_VERSION=$(git describe --tags --always 2>/dev/null || echo "0.0.0-local")

echo "   📋 Build metadata:"
echo "      - Commit: $COMMIT_SHA"
echo "      - Date: $BUILD_DATE"
echo "      - Version: $APP_VERSION"
echo "      - Base Image: $BASE_IMAGE"

# Temporarily replace lock files for test build
cp conda-lock.txt conda-lock-backup.txt
cp requirements-lock.txt requirements-lock-backup.txt
cp conda-lock-test.txt conda-lock.txt
cp requirements-lock-test.txt requirements-lock.txt

# Build the image using current Dockerfile
docker build \
    --build-arg APP_VERSION="$APP_VERSION" \
    --build-arg COMMIT_SHA="$COMMIT_SHA" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    -t sip-lims-workflow-manager:build-test \
    .

# Restore original lock files
cp conda-lock-backup.txt conda-lock.txt
cp requirements-lock-backup.txt requirements-lock.txt
rm conda-lock-backup.txt requirements-lock-backup.txt

if [ $? -eq 0 ]; then
    echo "   ✅ Image built successfully"
else
    echo "   ❌ ERROR: Image build failed"
    exit 1
fi

# Step 3: Test the image locally
echo ""
echo "🧪 Step 3: Image validation..."
docker run --rm sip-lims-workflow-manager:build-test python --version
echo "   ✅ Image validation passed"

# Step 4: Compare with existing lock files
echo ""
echo "🔍 Step 4: Comparing generated vs existing lock files..."
echo "   Conda packages:"
if diff conda-lock.txt conda-lock-test.txt > /dev/null; then
    echo "      ✅ IDENTICAL - Lock files are deterministic"
else
    echo "      ⚠️  DIFFERENT - Lock files have changed"
    echo "         This could indicate package updates or environment drift"
fi

echo "   Pip packages:"
if diff requirements-lock.txt requirements-lock-test.txt > /dev/null; then
    echo "      ✅ IDENTICAL - Lock files are deterministic"
else
    echo "      ⚠️  DIFFERENT - Lock files have changed"
    echo "         This could indicate package updates or environment drift"
fi

# Cleanup test files
rm conda-lock-test.txt requirements-lock-test.txt

echo ""
echo "🎉 Build Script Test Complete!"
echo "=============================="
echo "✅ Fresh lock files generated successfully"
echo "✅ Deterministic image built successfully"
echo "✅ Image validation passed"
echo ""
echo "📋 Test Image: sip-lims-workflow-manager:build-test"
echo "💡 Ready for production push when needed"