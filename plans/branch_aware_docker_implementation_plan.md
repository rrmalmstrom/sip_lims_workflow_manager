# Branch-Aware Docker Implementation Plan

## Overview
Transform the SIP LIMS Workflow Manager Docker system from hardcoded branch references to a fully branch-aware system where Docker image tags automatically correspond to Git branch names.

## Current State Analysis
- **Build Script**: [`build_image_from_lock_files.sh`](../build_image_from_lock_files.sh) always builds as `sip-lims-workflow-manager:latest`
- **Push Script**: [`push_image_to_github.sh`](../push_image_to_github.sh) always pushes to `:latest` tag
- **Run Script**: [`run.command`](../run.command) hardcoded to pull `:latest` for production
- **Update Detector**: [`src/update_detector.py`](../src/update_detector.py) hardcoded to check `analysis/esp-docker-adaptation` branch (line 114)
- **SHA System**: Existing robust SHA comparison logic works well and must be preserved

## Target State
- **Branch Name = Docker Tag**: `main` → `:main`, `analysis/esp-docker-adaptation` → `:analysis-esp-docker-adaptation`
- **Preserve SHA Logic**: Keep existing chronological comparison system
- **Auto-Detection**: All scripts automatically detect current branch
- **No Manual Configuration**: Zero hardcoded branch references

## Implementation Requirements

### 1. Shared Branch Utility Module
**File**: `utils/branch_utils.py` (new file)

**Functions Required**:
```python
def get_current_branch() -> str:
    """Get current Git branch name"""
    # Use: git rev-parse --abbrev-ref HEAD
    # Handle detached HEAD state
    # Return branch name or raise exception

def sanitize_branch_for_docker_tag(branch_name: str) -> str:
    """Convert branch name to valid Docker tag"""
    # Replace '/' with '-'
    # Replace '_' with '-' 
    # Convert to lowercase
    # Remove invalid characters
    # Examples:
    #   "main" → "main"
    #   "analysis/esp-docker-adaptation" → "analysis-esp-docker-adaptation"
    #   "feature/user-auth" → "feature-user-auth"

def get_docker_tag_for_current_branch() -> str:
    """Get Docker tag for current branch"""
    # Combines get_current_branch() + sanitize_branch_for_docker_tag()
    # Returns sanitized tag name

def get_full_image_name_for_current_branch() -> str:
    """Get full Docker image name with registry and tag"""
    # Returns: ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{branch-tag}
```

**Error Handling**:
- Handle detached HEAD state gracefully
- Validate Git repository exists
- Provide clear error messages for invalid states

### 2. Build Script Enhancement
**File**: [`build_image_from_lock_files.sh`](../build_image_from_lock_files.sh)

**Changes Required**:
1. **Import Branch Logic**: Source the branch utility functions
2. **Dynamic Tagging**: Replace hardcoded `:latest` with branch-based tag
3. **Preserve SHA Embedding**: Keep existing SHA labeling system
4. **Local Tag Strategy**: Build as `sip-lims-workflow-manager:{branch-tag}`

**Specific Modifications**:
- Line 60: Change from `-t sip-lims-workflow-manager:latest` to `-t sip-lims-workflow-manager:{branch-tag}`
- Add branch detection before build
- Update echo statements to show branch-specific information
- Preserve all existing build args (COMMIT_SHA, BUILD_DATE, APP_VERSION)

### 3. Push Script Enhancement  
**File**: [`push_image_to_github.sh`](../push_image_to_github.sh)

**Changes Required**:
1. **Branch Detection**: Auto-detect current branch
2. **Dynamic Tagging**: Tag and push to branch-specific tag
3. **Safety Checks**: Prevent accidental cross-branch pushes
4. **Local Image Validation**: Ensure local image exists with correct branch tag

**Specific Modifications**:
- Line 19: Check for `sip-lims-workflow-manager:{branch-tag}` instead of `:latest`
- Line 39: Tag as `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{branch-tag}`
- Line 53: Push to `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{branch-tag}`
- Add confirmation prompt showing branch and tag being pushed

### 4. Update Detector Enhancement
**File**: [`src/update_detector.py`](../src/update_detector.py)

**Critical Changes**:
1. **Remove Hardcoded Branch**: Line 114 currently hardcoded to `"analysis/esp-docker-adaptation"`
2. **Dynamic Branch Detection**: Use current branch or accept branch parameter
3. **Preserve SHA Logic**: Keep all existing chronological comparison logic
4. **Tag-Aware Image Inspection**: Look for local images with branch-specific tags

**Specific Modifications**:
- Line 114: Replace hardcoded branch with dynamic branch detection
- Update `get_local_docker_image_commit_sha()` to use branch-specific tag
- Update `get_remote_docker_image_commit_sha()` to accept branch parameter
- Preserve all ancestry checking and timestamp comparison logic

### 5. Run Script Enhancement
**File**: [`run.command`](../run.command)

**Changes Required**:
1. **Branch-Aware Image Selection**: Replace hardcoded image references
2. **Dynamic Pull Logic**: Pull branch-specific images
3. **Preserve Update Logic**: Keep existing update detection workflow
4. **Environment Variable Updates**: Set DOCKER_IMAGE based on current branch

**Specific Modifications**:
- Lines 151, 230: Replace hardcoded `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest`
- Update `check_docker_updates()` to use branch-aware detection
- Modify production_auto_update() to use branch-specific images
- Update echo statements to show branch-specific information

## Test-Driven Development Requirements

### Unit Tests
**File**: `tests/test_branch_utils.py` (new file)

**Test Cases Required**:
```python
def test_get_current_branch_main():
    """Test branch detection on main branch"""

def test_get_current_branch_development():
    """Test branch detection on development branch"""

def test_sanitize_branch_for_docker_tag():
    """Test branch name sanitization"""
    # Test cases:
    # "main" → "main"
    # "analysis/esp-docker-adaptation" → "analysis-esp-docker-adaptation"
    # "feature/user-auth" → "feature-user-auth"
    # "Feature/User_Auth" → "feature-user-auth"

def test_get_docker_tag_for_current_branch():
    """Test complete tag generation"""

def test_get_full_image_name_for_current_branch():
    """Test full image name generation"""

def test_error_handling_no_git():
    """Test behavior when not in Git repository"""

def test_error_handling_detached_head():
    """Test behavior in detached HEAD state"""
```

### Integration Tests
**File**: `tests/test_branch_aware_docker_integration.py` (new file)

**Test Cases Required**:
```python
def test_build_script_branch_awareness():
    """Test build script uses correct branch tag"""

def test_push_script_branch_awareness():
    """Test push script uses correct branch tag"""

def test_update_detector_branch_awareness():
    """Test update detector uses current branch"""

def test_run_command_branch_awareness():
    """Test run command pulls correct branch image"""

def test_cross_branch_isolation():
    """Test that switching branches uses different images"""
```

### Mock Strategy
- Mock Git commands for consistent test environments
- Mock Docker commands to avoid actual image operations
- Mock GitHub API calls for update detection tests
- Use temporary directories for file system tests

## Manual Validation Test Plan

### Test Scenario 1: Main Branch Workflow
1. **Setup**: Switch to `main` branch
2. **Build**: Run `./build_image_from_lock_files.sh`
3. **Verify**: Local image tagged as `sip-lims-workflow-manager:main`
4. **Push**: Run `./push_image_to_github.sh`
5. **Verify**: Image pushed to `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main`
6. **Pull**: Run `./run.command`
7. **Verify**: System pulls `:main` tag and compares SHA correctly

### Test Scenario 2: Development Branch Workflow
1. **Setup**: Switch to `analysis/esp-docker-adaptation` branch
2. **Build**: Run `./build_image_from_lock_files.sh`
3. **Verify**: Local image tagged as `sip-lims-workflow-manager:analysis-esp-docker-adaptation`
4. **Push**: Run `./push_image_to_github.sh`
5. **Verify**: Image pushed to `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation`
6. **Pull**: Run `./run.command`
7. **Verify**: System pulls `:analysis-esp-docker-adaptation` tag

### Test Scenario 3: Branch Switching
1. **Setup**: Start on `main` branch with local image
2. **Switch**: Change to `analysis/esp-docker-adaptation` branch
3. **Run**: Execute `./run.command`
4. **Verify**: System detects different branch and pulls appropriate image
5. **Verify**: SHA comparison works correctly for new branch

### Test Scenario 4: Update Detection
1. **Setup**: Have local image for current branch
2. **Simulate**: Remote has newer commit on same branch
3. **Run**: Execute update detection
4. **Verify**: System correctly identifies newer remote version
5. **Verify**: System pulls updated image only if newer

## Implementation Order

### Phase 1: Foundation
1. Create `utils/branch_utils.py` with comprehensive tests
2. Write unit tests for all branch utility functions
3. Ensure all tests pass before proceeding

### Phase 2: Update Detector Fix
1. Modify `src/update_detector.py` to remove hardcoded branch
2. Add integration tests for update detection
3. Verify SHA comparison logic still works

### Phase 3: Build and Push Scripts
1. Enhance `build_image_from_lock_files.sh` for branch awareness
2. Enhance `push_image_to_github.sh` for branch awareness
3. Add integration tests for build/push workflow

### Phase 4: Run Script Integration
1. Enhance `run.command` for branch-aware pulling
2. Add comprehensive integration tests
3. Test complete end-to-end workflow

### Phase 5: Manual Validation
1. Execute all manual test scenarios
2. Verify cross-branch isolation
3. Confirm SHA comparison accuracy
4. Test error handling and edge cases

### Phase 6: Documentation and Finalization
1. Update all relevant documentation
2. Update README with new branch-aware workflow
3. Create migration guide for existing users
4. Commit all changes with comprehensive commit message

## Success Criteria
- [ ] All automated tests pass
- [ ] Manual validation scenarios complete successfully
- [ ] No hardcoded branch references remain
- [ ] SHA comparison logic preserved and functional
- [ ] Cross-branch isolation verified
- [ ] Documentation updated
- [ ] Zero breaking changes for existing workflows

## Risk Mitigation
- **Backup Strategy**: Ensure existing `:latest` images remain untouched during development
- **Rollback Plan**: Keep original scripts as `.backup` files during development
- **Testing Isolation**: Use test registry or local registry for development testing
- **Gradual Rollout**: Test on development branches before touching main branch

## Files to be Modified
- `utils/branch_utils.py` (new)
- `build_image_from_lock_files.sh`
- `push_image_to_github.sh`
- `src/update_detector.py`
- `run.command`
- `tests/test_branch_utils.py` (new)
- `tests/test_branch_aware_docker_integration.py` (new)
- Documentation files (README, Docker docs, etc.)

## Dependencies
- Git repository with valid branch structure
- Docker environment for testing
- GitHub Container Registry access for integration tests
- Python 3.x for utility functions and tests