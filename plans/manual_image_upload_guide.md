# Manual Docker Image Upload Guide

## Current Image Location

Your system is already configured to use: **`ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest`**

**Evidence from your files:**
- [`docker-compose.yml` line 6](../docker-compose.yml): `image: ${DOCKER_IMAGE:-ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest}`
- [`run.command` line 151](../run.command): `export DOCKER_IMAGE="ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"`
- [`run.command` line 75](../run.command): `docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest`

## Step-by-Step Upload Process

### Step 1: Authenticate with GitHub Container Registry

```bash
# Create a GitHub Personal Access Token with 'write:packages' permission
# Go to: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Create token with 'write:packages' and 'read:packages' permissions

# Login to GitHub Container Registry (one-time setup)
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u rrmalmstrom --password-stdin
```

### Step 2: Build Your Deterministic Image

```bash
# Build the image locally using your current Dockerfile
docker build -t ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest .

# Verify the build succeeded
docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
```

### Step 3: Test the Image Locally

```bash
# Test that your built image works
docker run --rm -p 8501:8501 ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest &
sleep 10
curl -f http://localhost:8501/_stcore/health
docker stop $(docker ps -q --filter ancestor=ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest)
```

### Step 4: Push to Registry

```bash
# Push your tested image to GitHub Container Registry
docker push ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest

# Verify the push succeeded
echo "✅ Image uploaded to: ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"
```

## What Your Users Do

**Users run your existing [`run.command`](../run.command) script - NO CHANGES NEEDED**

The script already:
1. Pulls from `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest` (line 75)
2. Uses that image in docker-compose (line 151)
3. Handles updates automatically

## Code Changes Required

### 1. Remove GitHub Actions Build (CRITICAL)

**File to DELETE**: `.github/workflows/docker-build.yml`

```bash
# Remove the entire file
rm .github/workflows/docker-build.yml
```

### 2. Update Docker Compose (OPTIONAL - for clarity)

**File**: [`docker-compose.yml`](../docker-compose.yml)

**Current line 6:**
```yaml
image: ${DOCKER_IMAGE:-ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest}
```

**Change to (remove build section since you're pushing pre-built images):**
```yaml
version: '3.8'

services:
  sip-lims-workflow:
    # Use pre-built deterministic image (manually uploaded)
    image: ${DOCKER_IMAGE:-ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest}
    
    # REMOVE these lines (no more local building):
    # build:
    #   context: .
    #   dockerfile: Dockerfile
    #   args:
    #     USER_ID: ${USER_ID:-1000}
    #     GROUP_ID: ${GROUP_ID:-1000}
    #     APP_VERSION: ${APP_VERSION:-0.0.0-local}
    
    container_name: sip-lims-workflow-manager
    # ... rest stays the same
```

### 3. Create Upload Script

**File**: `build_and_push.sh`

```bash
#!/bin/bash
# Manual Build and Push Script for SIP LIMS Workflow Manager

set -e  # Exit on any error

# Configuration
IMAGE_NAME="ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
TAG="latest"
FULL_IMAGE="$IMAGE_NAME:$TAG"

echo "🔨 Building deterministic Docker image..."

# Build the image
docker build -t "$FULL_IMAGE" .

echo "🧪 Testing the built image..."

# Test the image works
docker run --rm -d --name test-container -p 8502:8501 "$FULL_IMAGE" >/dev/null
sleep 15

# Check if the health endpoint responds
if curl -f http://localhost:8502/_stcore/health >/dev/null 2>&1; then
    echo "✅ Image test passed"
    docker stop test-container >/dev/null
else
    echo "❌ Image test failed"
    docker stop test-container >/dev/null 2>&1 || true
    exit 1
fi

echo "📤 Pushing to GitHub Container Registry..."

# Push the image
docker push "$FULL_IMAGE"

echo "✅ Successfully uploaded: $FULL_IMAGE"
echo ""
echo "🎉 Your users can now run ./run.command to get the updated image!"
```

**Make it executable:**
```bash
chmod +x build_and_push.sh
```

## Your New Workflow

### Development Process:
1. Make code changes
2. Test locally: `docker-compose up`
3. When ready to release: `./build_and_push.sh`
4. Tell users to run `./run.command` (they get your new image automatically)

### User Process (UNCHANGED):
1. Run `./run.command`
2. Script automatically pulls your latest image
3. Everything works exactly as before

## No Changes Needed in Existing Code

**These files work perfectly as-is:**
- [`run.command`](../run.command) - already pulls from the right location
- [`src/update_detector.py`](../src/update_detector.py) - already checks the right registry
- [`src/scripts_updater.py`](../src/scripts_updater.py) - works independently

**The beauty of this approach:** Your existing system already expects images from `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest` - you're just changing WHO builds them (you instead of GitHub Actions).