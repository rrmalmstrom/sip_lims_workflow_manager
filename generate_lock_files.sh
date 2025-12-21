#!/bin/bash
# Generate deterministic lock files from working local Docker image

echo "🔒 Generating lock files from working local Docker image..."

# Check if local image exists
if ! docker images sip-lims-workflow-manager:latest --format "{{.Repository}}" | grep -q "sip-lims-workflow-manager"; then
    echo "❌ ERROR: Local image 'sip-lims-workflow-manager:latest' not found"
    echo "Please build the local image first with: docker build -t sip-lims-workflow-manager:latest ."
    exit 1
fi

echo "✅ Found local image: sip-lims-workflow-manager:latest"

# Generate conda explicit lock file
echo "📦 Extracting conda packages with exact build hashes..."
docker run --rm sip-lims-workflow-manager:latest bash -c "
    source /opt/conda/etc/profile.d/conda.sh
    conda activate sip-lims-workflow-manager
    conda list --explicit
" > conda-lock.txt

if [ $? -eq 0 ]; then
    echo "✅ Generated conda-lock.txt ($(grep -c "^https://" conda-lock.txt) packages)"
else
    echo "❌ ERROR: Failed to generate conda lock file"
    exit 1
fi

# Generate pip freeze lock file
echo "🐍 Extracting pip packages with exact versions..."
docker run --rm sip-lims-workflow-manager:latest bash -c "
    source /opt/conda/etc/profile.d/conda.sh
    conda activate sip-lims-workflow-manager
    pip freeze
" > requirements-lock.txt

if [ $? -eq 0 ]; then
    echo "✅ Generated requirements-lock.txt ($(wc -l < requirements-lock.txt) packages)"
else
    echo "❌ ERROR: Failed to generate pip lock file"
    exit 1
fi

# Get base image information
echo "🐳 Getting base image SHA..."
BASE_SHA=$(docker inspect continuumio/miniconda3:latest --format='{{index .RepoDigests 0}}' 2>/dev/null)
if [ -n "$BASE_SHA" ]; then
    echo "Base image SHA: $BASE_SHA" > base-image-info.txt
    echo "✅ Generated base-image-info.txt"
else
    echo "⚠️  Warning: Could not get base image SHA (image may be locally built)"
    echo "Base image: continuumio/miniconda3:latest (locally built)" > base-image-info.txt
fi

echo ""
echo "🎉 Lock files generated successfully:"
echo "   📄 conda-lock.txt - Conda packages with exact build hashes"
echo "   📄 requirements-lock.txt - Pip packages with exact versions"
echo "   📄 base-image-info.txt - Base image information"
echo ""
echo "Next steps:"
echo "1. Review the generated lock files"
echo "2. Update Dockerfile to use these lock files"
echo "3. Test the new deterministic build"
echo "4. Commit lock files to git"