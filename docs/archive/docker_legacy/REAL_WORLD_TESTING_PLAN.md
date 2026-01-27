# Real-World Testing Plan - Branch-Aware Docker Implementation

## Overview

This plan tests the actual Docker workflow by building, pushing, and running images to validate the branch-aware system works in real scenarios.

## Test Scenario 1: Fresh Build and SHA Validation

**Objective:** Build a new Docker image with branch-aware system and verify it has correct branch-specific tags and SHA labels

### Step 1.1: Check Current State
```bash
# Check existing images (old system may have created :latest images)
echo "Existing Docker images:"
docker images | grep sip-lims-workflow-manager

# Verify we're on the right branch and note current commit
echo "Current Git state:"
echo "  Branch: $(git branch --show-current)"
echo "  Commit SHA: $(git rev-parse HEAD)"
```

**Expected Results:**
- Should show we're on `analysis/esp-docker-adaptation` branch
- May show existing `sip-lims-workflow-manager:latest` images from old system
- Should NOT show any `sip-lims-workflow-manager:analysis-esp-docker-adaptation` images yet

### Step 1.2: Build New Image with Branch-Aware System
```bash
# Build using our enhanced script
./build/build_image_from_lock_files.sh
```

**Expected Results:**
- Script should detect branch: `analysis/esp-docker-adaptation`
- Should create image: `sip-lims-workflow-manager:analysis-esp-docker-adaptation`
- Should show current commit SHA in build metadata
- Should show branch information in build output

### Step 1.3: Verify Branch-Aware Image was Created
```bash
# Check the new branch-specific image was created
echo "New branch-aware image:"
docker images sip-lims-workflow-manager:analysis-esp-docker-adaptation

# Compare with old images
echo "All workflow manager images:"
docker images | grep sip-lims-workflow-manager

# Inspect image labels to verify SHA and metadata
docker inspect sip-lims-workflow-manager:analysis-esp-docker-adaptation --format='{{json .Config.Labels}}' | python -m json.tool

# Get the commit SHA from the image
DOCKER_SHA=$(docker inspect sip-lims-workflow-manager:analysis-esp-docker-adaptation --format='{{index .Config.Labels "com.sip-lims.commit-sha"}}')
GIT_SHA=$(git rev-parse HEAD)

echo "SHA Validation:"
echo "  Docker image SHA: $DOCKER_SHA"
echo "  Git commit SHA: $GIT_SHA"
echo "  Match: $([ "$DOCKER_SHA" = "$GIT_SHA" ] && echo "✅ YES" || echo "❌ NO")"
```

**Expected Results:**
- New image `sip-lims-workflow-manager:analysis-esp-docker-adaptation` should exist
- Old `:latest` images should still exist (unchanged)
- New image should have branch-specific tag
- Image labels should contain current commit SHA
- Docker SHA should match Git SHA exactly
- Should see clear distinction between old `:latest` and new branch-specific images

## Test Scenario 2: Update Detection with Missing Remote Image

**Objective:** Test how the update detector handles the case where we have a local branch-specific image but no corresponding remote image has been pushed yet

**Context:** After Scenario 1, we have a local `sip-lims-workflow-manager:analysis-esp-docker-adaptation` image, but we haven't pushed any branch-specific images to the remote registry yet.

### Step 2.1: Verify Current State
```bash
# Confirm we have the local branch-specific image (from Scenario 1)
echo "Local branch-specific image:"
docker images sip-lims-workflow-manager:analysis-esp-docker-adaptation

# Confirm no remote branch-specific image exists locally
echo "Remote branch-specific image (should not exist locally):"
docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation || echo "None found (expected)"
```

**Expected Results:**
- Should show local `sip-lims-workflow-manager:analysis-esp-docker-adaptation` image exists
- Should show no remote branch-specific image cached locally

### Step 2.2: Test Update Detection Logic
```bash
# Test the update detector with our current state
conda activate sip-lims
python -c "
from src.update_detector import UpdateDetector
detector = UpdateDetector()

# Test with branch-aware tag (our new system)
print('Testing branch-aware update detection:')
result = detector.check_docker_update(tag='analysis-esp-docker-adaptation')
print('Update check result:')
for key, value in result.items():
    print(f'  {key}: {value}')
print()
print(f'Update available: {result.get(\"update_available\", False)}')
print(f'Error: {result.get(\"error\", \"None\")}')
print(f'Reason: {result.get(\"reason\", \"None\")}')
"
```

**Expected Results:**
- Should find local SHA from the branch-specific image
- Should get remote SHA from GitHub API (current branch commit)
- Should compare local image SHA vs current Git commit SHA
- If they match: `update_available: False, reason: "Local and remote SHAs match"`
- If they differ: Should determine which is newer using Git ancestry

### Step 2.3: Test Run Command Update Check
```bash
# Test how run.command handles this scenario
echo "Testing run.command update detection..."

# The run.command calls check_docker_updates() which uses the update detector
# Let's see what it would do:
python3 src/update_detector.py --check-docker
```

**Expected Results:**
- Should return valid JSON with update status
- Should not crash or show errors
- Should use branch-aware detection (not hardcoded branch)
- Should provide clear reason for update decision

### Step 2.4: Verify Branch-Aware Behavior
```bash
# Confirm the system is using the correct branch for remote comparison
echo "Verifying branch-aware remote detection:"
python -c "
from utils.branch_utils import get_current_branch
from src.update_detector import UpdateDetector

current_branch = get_current_branch()
print(f'Current branch: {current_branch}')

detector = UpdateDetector()
remote_sha = detector.get_remote_docker_image_commit_sha()
print(f'Remote SHA from branch {current_branch}: {remote_sha}')

# Compare with what we'd get from main branch
main_sha = detector.get_remote_commit_sha('main')
print(f'Main branch SHA: {main_sha}')
print(f'Using current branch (not main): {remote_sha != main_sha}')
"
```

**Expected Results:**
- Should show current branch: `analysis/esp-docker-adaptation`
- Should get remote SHA from current branch (not main)
- Should demonstrate branch-aware behavior (different SHA than main if branches differ)

## Test Scenario 3: Push and Verify Remote Image

**Objective:** Push local branch-specific image to remote registry and verify it's accessible for future update detection

**Context:** After Scenarios 1 and 2, we have a local `sip-lims-workflow-manager:analysis-esp-docker-adaptation` image. Now we push it to make it available for the branch-aware update system.

### Step 3.1: Execute Branch-Aware Push
```bash
# Push using our enhanced script
echo "Pushing with branch-aware script..."
./build/push_image_to_github.sh
```

**Expected Results:**
- Script should detect branch: `analysis/esp-docker-adaptation`
- Should show: "Current branch: analysis/esp-docker-adaptation"
- Should tag as: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation`
- Should successfully push to GitHub Container Registry
- Should show branch information throughout the process
- Should NOT reference `:latest` or hardcoded branches

### Step 3.2: Verify Remote Image Accessibility (Without Removing Local)
```bash
# Test that remote image is accessible by attempting to pull it
# (This tests registry accessibility without affecting our local setup)
echo "Testing remote image accessibility..."
docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation

echo "✅ Remote image successfully accessible"

# Verify we now have both local and remote images
echo "Current image status:"
echo "Local image:"
docker images sip-lims-workflow-manager:analysis-esp-docker-adaptation
echo "Remote image (cached locally):"
docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation
```

**Expected Results:**
- Remote image should be pullable without errors
- Should now have both local and remote versions of the same image
- Both should have identical content (same image ID)

### Step 3.3: Verify Image Integrity
```bash
# Compare SHAs between local and remote images
echo "Verifying image integrity..."

LOCAL_SHA=$(docker inspect sip-lims-workflow-manager:analysis-esp-docker-adaptation --format='{{index .Config.Labels "com.sip-lims.commit-sha"}}')
REMOTE_SHA=$(docker inspect ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation --format='{{index .Config.Labels "com.sip-lims.commit-sha"}}')
GIT_SHA=$(git rev-parse HEAD)

echo "SHA Verification:"
echo "  Git commit SHA: $GIT_SHA"
echo "  Local image SHA: $LOCAL_SHA"
echo "  Remote image SHA: $REMOTE_SHA"

# Verify all SHAs match
if [ "$LOCAL_SHA" = "$REMOTE_SHA" ] && [ "$LOCAL_SHA" = "$GIT_SHA" ]; then
    echo "✅ All SHAs match - push/pull integrity verified"
else
    echo "❌ SHA mismatch detected"
    exit 1
fi
```

**Expected Results:**
- All three SHAs (Git, local image, remote image) should be identical
- Confirms the push → pull cycle maintains integrity
- Sets up the scenario for update detection testing

## Test Scenario 4: No Update Needed (SHA Match)

**Objective:** Test update detection when local remote image SHA matches current Git commit SHA

**Context:** After Scenario 3, we have a local copy of the remote image `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation` that was built from the current Git commit. The update detector should find no update is needed.

### Step 4.1: Verify Current State
```bash
# Confirm we have the remote image locally (from Scenario 3)
echo "Current remote image (cached locally):"
docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation

# Verify the image SHA matches current Git commit
REMOTE_IMAGE_SHA=$(docker inspect ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation --format='{{index .Config.Labels "com.sip-lims.commit-sha"}}')
GIT_SHA=$(git rev-parse HEAD)

echo "SHA Comparison:"
echo "  Current Git commit: $GIT_SHA"
echo "  Remote image SHA: $REMOTE_IMAGE_SHA"
echo "  Match: $([ "$REMOTE_IMAGE_SHA" = "$GIT_SHA" ] && echo "✅ YES" || echo "❌ NO")"
```

**Expected Results:**
- Should have remote image cached locally
- Remote image SHA should match current Git commit SHA
- Sets up the "no update needed" scenario

### Step 4.2: Test Update Detection Logic
```bash
# Test the update detector (this is what run.command calls)
conda activate sip-lims
python -c "
from src.update_detector import UpdateDetector
detector = UpdateDetector()
result = detector.check_docker_update()
print('Update check result:')
for key, value in result.items():
    print(f'  {key}: {value}')
print()
print(f'Update available: {result.get(\"update_available\", False)}')
print(f'Reason: {result.get(\"reason\", \"None\")}')
"
```

**Expected Results:**
- Should find local remote image SHA matches current Git commit SHA
- Should report: `update_available: False`
- Should show reason: `"Local and remote SHAs match"`
- Demonstrates the system correctly identifies no update is needed

### Step 4.3: Test Run Command Update Check
```bash
# Test the actual command that run.command uses
echo "Testing run.command update detection..."
python3 src/update_detector.py --check-docker
```

**Expected Results:**
- Should return JSON with `update_available: false`
- Should show that run.command would proceed without updating
- Should display "✅ Docker image is up to date" when run.command executes this

## Test Scenario 5: Simulate Update Available

**Objective:** Test update detection when remote image is newer

### Step 5.1: Create a "Newer" Remote Image
```bash
# Make a small change to trigger new build
echo "# Test comment for update simulation" >> README.md
git add README.md
git commit -m "Test commit to simulate newer remote image"

# Build new local image with new SHA
./build/build_image_from_lock_files.sh

# Push this new image to remote
./build/push_image_to_github.sh

# Now revert the change and build old local image
git reset --hard HEAD~1
./build/build_image_from_lock_files.sh
```

**Expected Results:**
- Should create scenario where remote image has newer SHA than local
- Local and remote images should have different commit SHAs

### Step 5.2: Test Update Detection with Different SHAs
```bash
# Test update detection with different SHAs
conda activate sip-lims
python -c "
from src.update_detector import UpdateDetector
detector = UpdateDetector()
result = detector.check_docker_update()
print('Update check result with different SHAs:')
for key, value in result.items():
    print(f'  {key}: {value}')
print(f'Update available: {result.get(\"update_available\", False)}')
"
```

**Expected Results:**
- Should detect different SHAs between local and remote
- Should determine which is newer using Git ancestry
- Should report appropriate update status

## Test Scenario 6: Branch Switching Validation

**Objective:** Test system behavior when switching branches

### Step 6.1: Switch to Main Branch
```bash
# Switch to main branch
git checkout main

# Test branch detection
python utils/branch_utils.py info

# Test what images would be used
echo "Expected local image: $(python -c 'from utils.branch_utils import get_local_image_name_for_current_branch; print(get_local_image_name_for_current_branch())')"
echo "Expected remote image: $(python -c 'from utils.branch_utils import get_remote_image_name_for_current_branch; print(get_remote_image_name_for_current_branch())')"
```

### Step 6.2: Test Update Detection on Main Branch
```bash
# Test update detection on main branch
conda activate sip-lims
python -c "
from src.update_detector import UpdateDetector
detector = UpdateDetector()
result = detector.check_docker_update()
print('Update check result on main branch:')
for key, value in result.items():
    print(f'  {key}: {value}')
"
```

### Step 6.3: Switch Back and Verify
```bash
# Switch back to development branch
git checkout analysis/esp-docker-adaptation

# Verify detection switches back
python utils/branch_utils.py info
```

**Expected Results:**
- On main branch: Should generate `main` tags and look for `main` images
- On development branch: Should generate `analysis-esp-docker-adaptation` tags
- Branch switching should be immediate and seamless

## Test Scenario 7: Developer vs Production Mode

**Objective:** Test different behaviors in developer vs production modes

### Step 7.1: Test Developer Mode
```bash
# Ensure developer marker exists
mkdir -p config
touch config/developer.marker

# Test run command in developer mode (choose development workflow)
echo "Testing developer mode - choose option 2 (Development mode) when prompted"
# ./run.command
# (This will be interactive)
```

### Step 7.2: Test Production Mode
```bash
# Remove developer marker
rm -f config/developer.marker

# Test run command in production mode
echo "Testing production mode - should automatically use production workflow"
# ./run.command
# (This will be interactive)
```

**Expected Results:**
- Developer mode: Should offer choice, use local images when choosing development
- Production mode: Should automatically use remote images and auto-update

## Execution Order

**Important:** These tests should be run in order as they build upon each other:

1. **Scenario 1:** Build fresh image and verify SHA
2. **Scenario 2:** Test missing remote image handling
3. **Scenario 3:** Push image and verify remote
4. **Scenario 4:** Test no update needed
5. **Scenario 5:** Test update available detection
6. **Scenario 6:** Test branch switching
7. **Scenario 7:** Test developer vs production modes

## Success Criteria

- ✅ All Docker images created with correct branch-specific tags
- ✅ SHA labels in images match Git commit SHAs
- ✅ Update detection correctly compares local vs remote SHAs
- ✅ Missing remote images handled gracefully
- ✅ Branch switching immediately affects image selection
- ✅ Developer and production modes use appropriate image sources
- ✅ No hardcoded branch references in any output
- ✅ All error conditions handled gracefully

## Cleanup After Testing

```bash
# Clean up test images
docker rmi sip-lims-workflow-manager:analysis-esp-docker-adaptation 2>/dev/null || true
docker rmi ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation 2>/dev/null || true
docker rmi sip-lims-workflow-manager:main 2>/dev/null || true
docker rmi ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main 2>/dev/null || true

# Reset any test commits
git reset --hard HEAD

# Ensure we're on the right branch
git checkout analysis/esp-docker-adaptation
```

---

This testing plan focuses on real Docker operations and validates the complete workflow from build to run, ensuring the branch-aware system works correctly in practice.