# Local Build + Push Implementation Plan

## Strategy Overview

**Approved Solution**: Local build + push strategy for guaranteed dev/prod parity
- You build deterministic Docker images locally on your ARM64 Mac
- You test the exact image you built
- You push that tested image to GitHub Container Registry
- Users pull and run the exact same image you tested
- Cross-platform compatibility handled automatically by Docker

## Benefits

✅ **Perfect Dev/Prod Parity**: Users get exactly what you tested
✅ **Prevents Hash Drift**: Your deterministic lock files prevent conda-forge surprises
✅ **Cross-Platform Compatible**: ARM64 images run on AMD64 via Docker emulation
✅ **Simple Workflow**: No complex CI/CD build processes
✅ **Full Control**: You control when and what gets released

## Implementation Steps

### 1. Modify GitHub Actions Workflow

**Current Issue**: GitHub Actions tries to build multi-platform images but fails due to ARM64 lock files

**Solution**: Remove the build process, keep only the container registry setup for manual pushes

**Changes to `.github/workflows/docker-build.yml`**:
- Remove the build and push steps
- Keep registry login for manual pushes
- Optionally add validation/testing steps for pushed images

### 2. Create Local Build Script

**Purpose**: Standardize your local build and push process

**Script**: `build_and_push.sh`
```bash
#!/bin/bash
set -e

# Build deterministic image locally
echo "🔨 Building deterministic Docker image..."
docker build -t ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest .

# Test the image locally
echo "🧪 Testing image locally..."
docker run --rm ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --version

# Push to registry
echo "📤 Pushing to GitHub Container Registry..."
docker push ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest

echo "✅ Build and push complete!"
```

### 3. Update Documentation

**User Instructions**: Update README and user guides to reflect the new workflow:
- Users pull pre-built images instead of building locally
- Remove references to local building for end users
- Add troubleshooting for cross-platform compatibility

### 4. Workflow Process

**Your Development Workflow**:
1. Make code changes
2. Test locally with volume mounts: `docker-compose up`
3. When ready to release:
   ```bash
   ./build_and_push.sh
   ```
4. Verify the pushed image works:
   ```bash
   docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
   docker run --rm -p 8501:8501 ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
   ```

**User Workflow**:
1. Pull your pre-built image:
   ```bash
   docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
   ```
2. Run with their data:
   ```bash
   docker run -p 8501:8501 -v /path/to/data:/data ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
   ```

## Technical Details

### Cross-Platform Compatibility

**How ARM64 → AMD64 Works**:
- Docker Desktop includes QEMU emulation
- ARM64 images automatically run on AMD64 systems
- Performance impact is minimal for Python/Streamlit applications
- Users don't need to know or care about architecture differences

### Deterministic Build Preservation

**Your Current Setup Works Perfectly**:
- [`Dockerfile`](../Dockerfile) with pinned base image SHA ✅
- [`conda-lock.txt`](../conda-lock.txt) with exact package URLs ✅
- [`requirements-lock.txt`](../requirements-lock.txt) with exact versions ✅
- No changes needed to the deterministic build process

### Registry Authentication

**GitHub Container Registry Setup**:
```bash
# One-time setup for pushing
echo $GITHUB_TOKEN | docker login ghcr.io -u rrmalmstrom --password-stdin
```

## Migration Steps

### Step 1: Disable GitHub Actions Build
```yaml
# Comment out or remove the build step in .github/workflows/docker-build.yml
# - name: Build and push Docker image
#   uses: docker/build-push-action@v5
```

### Step 2: Test Local Build
```bash
# Verify your current setup builds successfully
docker build -t test-image .
docker run --rm test-image --version
```

### Step 3: Push First Image
```bash
# Build and push your first image
docker build -t ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest .
docker push ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
```

### Step 4: Test Cross-Platform
Ask a Windows/Linux user to test:
```bash
docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
docker run -p 8501:8501 ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest
```

## Success Criteria

- ✅ You can build images locally without errors
- ✅ Local testing works perfectly
- ✅ Push to registry succeeds
- ✅ Users on different platforms can pull and run the image
- ✅ No "works on my machine" issues
- ✅ Hash drift prevented by deterministic lock files

## Rollback Plan

If issues arise, you can always:
1. Revert to the [`archive/environment-docker-final-validated.yml`](../archive/environment-docker-final-validated.yml) approach
2. Re-enable GitHub Actions builds with platform-specific lock generation
3. Use the original pinned environment.yml strategy

## Next Steps

1. Implement the GitHub Actions workflow changes
2. Create the local build script
3. Test the complete workflow end-to-end
4. Update user documentation
5. Announce the new deployment process to your users