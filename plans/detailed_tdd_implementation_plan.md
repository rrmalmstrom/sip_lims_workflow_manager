# Detailed TDD Implementation Plan: Local Build + Push Strategy

## Overview for Coding Agent

This plan implements the approved "Local Build + Push" strategy using Test-Driven Development (TDD). The goal is to modify the current deterministic Docker build system to support local building and pushing while maintaining the existing workflow manager functionality.

## Critical Workflow Clarification

**IMPORTANT**: This strategy completely separates code management from image deployment:

### What You Push to GitHub (Code Repository):
- Source code changes ([`app.py`](../app.py), [`src/`](../src/), etc.)
- Configuration files ([`docker-compose.yml`](../docker-compose.yml), [`Dockerfile`](../Dockerfile))
- Documentation updates
- Tests and development files
- **NO automatic image building occurs**

### What You Push to Container Registry (Image Repository):
- Pre-built Docker images (built locally on your Mac)
- Tagged with versions/dates for tracking
- Users pull these images directly
- **Completely separate from code pushes**

### GitHub Actions Removal:
- **REMOVE** the entire [`.github/workflows/docker-build.yml`](../.github/workflows/docker-build.yml) file
- **REMOVE** any automatic build triggers
- GitHub becomes purely a code repository, not a build system

## Gap Analysis

### Current State Analysis
- ✅ **Deterministic Build**: [`Dockerfile`](../Dockerfile), [`conda-lock.txt`](../conda-lock.txt), [`requirements-lock.txt`](../requirements-lock.txt) work perfectly
- ✅ **Testing Infrastructure**: [`pytest.ini`](../pytest.ini), [`tests/conftest.py`](../tests/conftest.py), [`run_tests.sh`](../run_tests.sh) established
- ✅ **Workflow Manager Core**: [`app.py`](../app.py), [`src/core.py`](../src/core.py), [`src/logic.py`](../src/logic.py) functional
- ❌ **GitHub Actions Build**: Fails due to ARM64/AMD64 platform mismatch
- ❌ **Local Build Script**: Missing standardized build and push process
- ❌ **Cross-Platform Testing**: No validation that ARM64 images work on AMD64

### Integration Points
- **Docker Compose**: [`docker-compose.yml`](../docker-compose.yml) must continue working for local development
- **Volume Mounts**: `/data` and `/workflow-scripts` volumes must remain functional
- **Entrypoint**: [`entrypoint.sh`](../entrypoint.sh) must continue working across platforms
- **Update Detection**: [`src/update_detector.py`](../src/update_detector.py) and [`src/scripts_updater.py`](../src/scripts_updater.py) must work with new deployment model

## TDD Implementation Plan

### Phase 1: Test Infrastructure for Build System

#### Task 1.1: Create Docker Build Tests
**File**: `tests/test_docker_build_system.py`

**TDD Approach**:
1. **Write failing tests first**
2. **Implement minimal code to pass**
3. **Refactor and improve**

**Test Cases to Implement**:
```python
class TestDockerBuildSystem:
    def test_dockerfile_exists_and_valid(self):
        """Test that Dockerfile exists and has required components"""
        # Test: Dockerfile exists
        # Test: Contains deterministic base image SHA
        # Test: Contains conda-lock.txt copy
        # Test: Contains requirements-lock.txt copy
        
    def test_lock_files_exist_and_valid(self):
        """Test that lock files exist and contain expected content"""
        # Test: conda-lock.txt exists and has ARM64 platform
        # Test: requirements-lock.txt exists and has pinned versions
        # Test: Lock files are not empty
        
    def test_local_build_succeeds(self):
        """Test that local Docker build completes successfully"""
        # Test: docker build command succeeds
        # Test: Image is created with correct tags
        # Test: Image contains expected labels
        
    def test_built_image_functionality(self):
        """Test that built image runs and responds correctly"""
        # Test: Container starts successfully
        # Test: Streamlit app is accessible
        # Test: Health check passes
        # Test: Volume mounts work correctly
```

#### Task 1.2: Create Build Script Tests
**File**: `tests/test_build_script.py`

**Test Cases**:
```python
class TestBuildScript:
    def test_build_script_exists_and_executable(self):
        """Test build script is present and executable"""
        
    def test_build_script_validates_prerequisites(self):
        """Test script checks for Docker, authentication, etc."""
        
    def test_build_script_handles_errors_gracefully(self):
        """Test script fails gracefully with helpful messages"""
        
    def test_build_script_creates_correct_tags(self):
        """Test script creates images with correct naming"""
```

#### Task 1.3: Create Cross-Platform Compatibility Tests
**File**: `tests/test_cross_platform_compatibility.py`

**Test Cases**:
```python
class TestCrossPlatformCompatibility:
    def test_arm64_image_metadata(self):
        """Test that built ARM64 image has correct platform metadata"""
        
    def test_docker_emulation_compatibility(self):
        """Test that ARM64 image can run on AMD64 via emulation"""
        # Note: This may need to be marked as @pytest.mark.slow
        
    def test_volume_mounts_cross_platform(self):
        """Test volume mounts work across platforms"""
        
    def test_entrypoint_cross_platform(self):
        """Test entrypoint.sh works across platforms"""
```

### Phase 2: Implement Build System Components

#### Task 2.1: Create Local Build Script
**File**: `build_and_push.sh`

**TDD Implementation**:
1. Write tests for script functionality first
2. Implement script to pass tests
3. Add error handling and validation

**Script Requirements** (based on failing tests):
```bash
#!/bin/bash
# Local Build and Push Script for SIP LIMS Workflow Manager

set -e  # Exit on any error

# Configuration
IMAGE_NAME="ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
TAG="latest"

# Functions to implement (test-driven):
validate_prerequisites() {
    # Check Docker is running
    # Check GitHub authentication
    # Check required files exist
}

build_image() {
    # Build deterministic Docker image
    # Apply correct tags and labels
    # Validate build success
}

test_image() {
    # Run basic functionality tests
    # Verify health check
    # Test volume mounts
}

push_image() {
    # Push to GitHub Container Registry
    # Verify push success
    # Display pull instructions
}

main() {
    validate_prerequisites
    build_image
    test_image
    push_image
}
```

#### Task 2.2: Create Build Validation Utilities
**File**: `utils/build_validation.py`

**Purpose**: Support the build script with Python utilities for validation

**TDD Implementation**:
```python
class BuildValidator:
    def validate_docker_environment(self):
        """Validate Docker is available and running"""
        
    def validate_github_auth(self):
        """Validate GitHub Container Registry authentication"""
        
    def validate_deterministic_files(self):
        """Validate lock files and Dockerfile are present and valid"""
        
    def test_built_image(self, image_name: str):
        """Test that built image functions correctly"""
        
    def validate_cross_platform_compatibility(self, image_name: str):
        """Validate image will work across platforms"""
```

#### Task 2.3: Remove GitHub Actions Workflow
**File**: `.github/workflows/docker-build.yml`

**TDD Approach**: Create tests that validate the workflow file is properly removed

**Changes Required**:
1. **COMPLETELY REMOVE** `.github/workflows/docker-build.yml`
2. Remove any other GitHub Actions build configurations
3. Update documentation to reflect manual-only builds

**Test**: `tests/test_github_actions_removal.py`
```python
class TestGitHubActionsRemoval:
    def test_docker_build_workflow_removed(self):
        """Test that docker-build.yml workflow file is completely removed"""
        assert not os.path.exists('.github/workflows/docker-build.yml')
        
    def test_no_automatic_build_triggers(self):
        """Test that no automatic build triggers remain in repository"""
        # Check for any remaining workflow files that might trigger builds
        
    def test_github_directory_cleanup(self):
        """Test .github directory is cleaned up appropriately"""
        # May keep .github for other purposes, but no build workflows
```

### Phase 3: Integration with Existing Workflow Manager

#### Task 3.1: Update Docker Compose for New Strategy
**File**: `docker-compose.yml`

**TDD Tests**: `tests/test_docker_compose_integration.py`
```python
class TestDockerComposeIntegration:
    def test_compose_uses_prebuilt_image_by_default(self):
        """Test compose pulls prebuilt image when available"""
        
    def test_compose_falls_back_to_local_build(self):
        """Test compose can still build locally for development"""
        
    def test_volume_mounts_preserved(self):
        """Test that data and scripts volumes still work"""
        
    def test_environment_variables_preserved(self):
        """Test that all environment variables still work"""
```

**Implementation**: Modify [`docker-compose.yml`](../docker-compose.yml) to prefer prebuilt images

#### Task 3.2: Update Update Detection System
**Files**: [`src/update_detector.py`](../src/update_detector.py), [`src/scripts_updater.py`](../src/scripts_updater.py)

**TDD Tests**: `tests/test_update_detection_with_prebuilt_images.py`
```python
class TestUpdateDetectionWithPrebuiltImages:
    def test_detects_new_image_versions(self):
        """Test system can detect when new prebuilt images are available"""
        
    def test_handles_local_vs_remote_image_differences(self):
        """Test system handles differences between local and remote images"""
        
    def test_update_workflow_with_prebuilt_images(self):
        """Test update process works with prebuilt image strategy"""
```

**Implementation Requirements**:
- Modify update detection to check for new image tags
- Update pull logic to use prebuilt images
- Maintain backward compatibility with local builds

#### Task 3.3: Update Documentation and User Guides
**Files**: [`README.md`](../README.md), [`docs/user_guide/QUICK_SETUP_GUIDE.md`](../docs/user_guide/QUICK_SETUP_GUIDE.md)

**TDD Tests**: `tests/test_documentation_accuracy.py`
```python
class TestDocumentationAccuracy:
    def test_readme_reflects_new_workflow(self):
        """Test README accurately describes new build process"""
        
    def test_setup_guide_updated(self):
        """Test setup guide reflects prebuilt image usage"""
        
    def test_troubleshooting_includes_cross_platform_issues(self):
        """Test troubleshooting covers cross-platform scenarios"""
```

### Phase 4: Cross-Platform Validation and Testing

#### Task 4.1: Create Cross-Platform Test Suite
**File**: `tests/test_cross_platform_end_to_end.py`

**Test Cases**:
```python
class TestCrossPlatformEndToEnd:
    @pytest.mark.slow
    def test_arm64_image_on_amd64_emulation(self):
        """Test ARM64 image runs correctly on AMD64 via Docker emulation"""
        
    def test_volume_mount_compatibility(self):
        """Test volume mounts work correctly across platforms"""
        
    def test_workflow_manager_functionality_cross_platform(self):
        """Test core workflow manager features work across platforms"""
        
    def test_performance_acceptable_with_emulation(self):
        """Test performance is acceptable when running emulated"""
```

#### Task 4.2: Create Integration Test for Complete Workflow
**File**: `tests/test_complete_build_push_workflow.py`

**Test Cases**:
```python
class TestCompleteBuildPushWorkflow:
    def test_full_developer_workflow(self):
        """Test complete developer workflow: build → test → push"""
        
    def test_full_user_workflow(self):
        """Test complete user workflow: pull → run → use"""
        
    def test_error_recovery_scenarios(self):
        """Test recovery from common error scenarios"""
```

## Implementation Order and Dependencies

### Sprint 1: Foundation (Tests + Basic Build Script)
1. **Day 1-2**: Implement `tests/test_docker_build_system.py` (all tests failing)
2. **Day 3-4**: Create basic `build_and_push.sh` to pass core tests
3. **Day 5**: Implement `utils/build_validation.py` to support build script

### Sprint 2: Integration (Docker Compose + Update System)
1. **Day 6-7**: Implement `tests/test_docker_compose_integration.py` and update compose file
2. **Day 8-9**: Implement `tests/test_update_detection_with_prebuilt_images.py` and update detection system
3. **Day 10**: Update GitHub Actions workflow and create tests

### Sprint 3: Cross-Platform Validation
1. **Day 11-12**: Implement cross-platform test suite
2. **Day 13-14**: Create end-to-end integration tests
3. **Day 15**: Documentation updates and final validation

## Success Criteria for Each Phase

### Phase 1 Success Criteria:
- [ ] All Docker build tests pass
- [ ] Build script tests pass (even with minimal implementation)
- [ ] Cross-platform compatibility tests are defined and initially failing

### Phase 2 Success Criteria:
- [ ] `build_and_push.sh` script works end-to-end
- [ ] Local Docker builds succeed consistently
- [ ] Images can be pushed to GitHub Container Registry
- [ ] Basic functionality tests pass

### Phase 3 Success Criteria:
- [ ] Docker Compose works with prebuilt images
- [ ] Update detection system works with new strategy
- [ ] All existing workflow manager functionality preserved
- [ ] Documentation accurately reflects new process

### Phase 4 Success Criteria:
- [ ] ARM64 images confirmed working on AMD64 systems
- [ ] Performance acceptable across platforms
- [ ] Complete end-to-end workflows tested and validated
- [ ] Error scenarios handled gracefully

## Risk Mitigation

### Technical Risks:
1. **Cross-platform compatibility issues**: Mitigated by comprehensive testing
2. **Performance degradation with emulation**: Mitigated by performance tests
3. **Breaking existing functionality**: Mitigated by preserving all existing tests

### Process Risks:
1. **Complex migration**: Mitigated by phased approach with rollback options
2. **User confusion**: Mitigated by clear documentation and gradual rollout

## Rollback Strategy

If any phase fails:
1. **Phase 1 failure**: Continue with existing GitHub Actions approach
2. **Phase 2 failure**: Revert to original docker-compose.yml and update system
3. **Phase 3 failure**: Use hybrid approach with both local and CI builds
4. **Phase 4 failure**: Implement platform-specific builds instead

## Testing Commands for Coding Agent

```bash
# Run all tests
pytest -v

# Run only build system tests
pytest tests/test_docker_build_system.py -v

# Run cross-platform tests (may be slow)
pytest -m "slow" -v

# Run specific test categories
pytest tests/test_docker_compose_integration.py -v
pytest tests/test_update_detection_with_prebuilt_images.py -v

# Test the build script
./build_and_push.sh --dry-run

# Validate cross-platform compatibility
python -m utils.build_validation --test-cross-platform
```

This plan ensures that every change is test-driven, maintains compatibility with the existing workflow manager, and provides a clear path to implement the approved local build + push strategy.