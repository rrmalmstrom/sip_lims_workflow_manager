# Phase 2: Update Detector Enhancement Detail

## Overview
Fix the hardcoded branch reference in `src/update_detector.py` line 114 and make it branch-aware while preserving all existing SHA comparison logic.

## Critical Requirements
- **PRESERVE** all existing SHA comparison and chronological logic
- **DO NOT BREAK** the ancestry checking and timestamp comparison
- **MAINTAIN** backward compatibility with existing API
- **KEEP** all existing error handling

## Current State Analysis

### Problem Location
**File**: `src/update_detector.py`
**Line 114**: `return self.get_remote_commit_sha("analysis/esp-docker-adaptation")`

This hardcoded branch reference means update detection always checks against the development branch, regardless of what branch the user is actually on.

### Current Method Signatures
```python
def get_remote_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
    """Get the commit SHA from REMOTE Docker image without pulling."""
```

## Required Changes

### 1. Modify `get_remote_docker_image_commit_sha` Method

**Current Implementation** (line 109-116):
```python
def get_remote_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
    """Get the commit SHA from REMOTE Docker image without pulling."""
    try:
        # Use GitHub API to get the latest commit SHA from the branch that builds the image
        # This assumes the remote image is built from the latest commit on analysis/esp-docker-adaptation
        return self.get_remote_commit_sha("analysis/esp-docker-adaptation")
    except Exception:
        return None
```

**New Implementation**:
```python
def get_remote_docker_image_commit_sha(self, tag: str = "latest", branch: Optional[str] = None) -> Optional[str]:
    """Get the commit SHA from REMOTE Docker image without pulling."""
    try:
        # If branch not specified, detect current branch
        if branch is None:
            from utils.branch_utils import get_current_branch
            branch = get_current_branch()
        
        # Use GitHub API to get the latest commit SHA from the specified branch
        return self.get_remote_commit_sha(branch)
    except Exception:
        return None
```

### 2. Modify `get_local_docker_image_commit_sha` Method

**Current Implementation** (line 86-107):
```python
def get_local_docker_image_commit_sha(self, tag: str = "latest") -> Optional[str]:
    """Get the commit SHA from a LOCAL Docker image's labels (no pulling)."""
    try:
        # Inspect the LOCAL image only - do NOT pull
        result = subprocess.run(
            ["docker", "inspect", f"{self.ghcr_image}:{tag}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        inspect_data = json.loads(result.stdout)
        labels = inspect_data[0]["Config"]["Labels"]
        
        # Try multiple label keys for commit SHA
        for key in ["com.sip-lims.commit-sha", "org.opencontainers.image.revision"]:
            if key in labels:
                return labels[key]
        
        return None
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
        return None
```

**New Implementation**:
```python
def get_local_docker_image_commit_sha(self, tag: str = "latest", branch_tag: Optional[str] = None) -> Optional[str]:
    """Get the commit SHA from a LOCAL Docker image's labels (no pulling)."""
    try:
        # If branch_tag not specified, detect current branch tag
        if branch_tag is None:
            from utils.branch_utils import get_docker_tag_for_current_branch
            branch_tag = get_docker_tag_for_current_branch()
        
        # Inspect the LOCAL image with branch-specific tag
        result = subprocess.run(
            ["docker", "inspect", f"{self.ghcr_image}:{branch_tag}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        inspect_data = json.loads(result.stdout)
        labels = inspect_data[0]["Config"]["Labels"]
        
        # Try multiple label keys for commit SHA
        for key in ["com.sip-lims.commit-sha", "org.opencontainers.image.revision"]:
            if key in labels:
                return labels[key]
        
        return None
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
        return None
```

### 3. Update `check_docker_update` Method

**Current Implementation** (line 124-191):
```python
def check_docker_update(self, tag: str = "latest") -> Dict[str, any]:
    """Enhanced Docker update check with chronological validation."""
    local_sha = self.get_local_docker_image_commit_sha(tag)
    remote_sha = self.get_remote_docker_image_commit_sha(tag)
    # ... rest of method unchanged
```

**New Implementation**:
```python
def check_docker_update(self, tag: str = "latest", branch: Optional[str] = None) -> Dict[str, any]:
    """Enhanced Docker update check with chronological validation."""
    # Detect branch if not provided
    if branch is None:
        from utils.branch_utils import get_current_branch, get_docker_tag_for_current_branch
        branch = get_current_branch()
        branch_tag = get_docker_tag_for_current_branch()
    else:
        from utils.branch_utils import sanitize_branch_for_docker_tag
        branch_tag = sanitize_branch_for_docker_tag(branch)
    
    local_sha = self.get_local_docker_image_commit_sha(branch_tag, branch_tag)
    remote_sha = self.get_remote_docker_image_commit_sha(branch_tag, branch)
    
    # ... rest of method unchanged - preserve all existing logic
```

## Backward Compatibility

### Maintain Existing API
- Keep all existing method signatures working
- Add optional parameters with sensible defaults
- Preserve all existing behavior when no branch specified

### Fallback Strategy
```python
def get_local_docker_image_commit_sha(self, tag: str = "latest", branch_tag: Optional[str] = None) -> Optional[str]:
    """Get the commit SHA from a LOCAL Docker image's labels (no pulling)."""
    try:
        # If branch_tag not specified, try current branch first, then fallback to tag
        if branch_tag is None:
            try:
                from utils.branch_utils import get_docker_tag_for_current_branch
                branch_tag = get_docker_tag_for_current_branch()
            except:
                # Fallback to provided tag if branch detection fails
                branch_tag = tag
        
        # Try branch-specific tag first
        result = subprocess.run(
            ["docker", "inspect", f"{self.ghcr_image}:{branch_tag}"],
            capture_output=True,
            text=True,
            check=True
        )
        # ... process result
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
        # Fallback to original tag if branch-specific fails
        if branch_tag != tag:
            try:
                result = subprocess.run(
                    ["docker", "inspect", f"{self.ghcr_image}:{tag}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # ... process result
            except:
                return None
        return None
```

## Test Requirements

### Unit Tests: `tests/test_update_detector_branch_aware.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from src.update_detector import UpdateDetector

class TestBranchAwareUpdateDetector:
    def setup_method(self):
        self.detector = UpdateDetector()

    @patch('utils.branch_utils.get_current_branch')
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    def test_remote_sha_uses_current_branch(self, mock_remote_commit, mock_current_branch):
        """Test that remote SHA detection uses current branch"""
        mock_current_branch.return_value = "main"
        mock_remote_commit.return_value = "abc123"
        
        result = self.detector.get_remote_docker_image_commit_sha()
        
        mock_remote_commit.assert_called_with("main")
        assert result == "abc123"

    @patch('utils.branch_utils.get_current_branch')
    @patch('src.update_detector.UpdateDetector.get_remote_commit_sha')
    def test_remote_sha_uses_specified_branch(self, mock_remote_commit, mock_current_branch):
        """Test that remote SHA detection uses specified branch"""
        mock_remote_commit.return_value = "def456"
        
        result = self.detector.get_remote_docker_image_commit_sha(branch="analysis/esp-docker-adaptation")
        
        mock_remote_commit.assert_called_with("analysis/esp-docker-adaptation")
        mock_current_branch.assert_not_called()
        assert result == "def456"

    @patch('utils.branch_utils.get_docker_tag_for_current_branch')
    @patch('subprocess.run')
    def test_local_sha_uses_branch_tag(self, mock_subprocess, mock_branch_tag):
        """Test that local SHA detection uses branch-specific tag"""
        mock_branch_tag.return_value = "main"
        mock_subprocess.return_value.stdout = '{"Config": {"Labels": {"com.sip-lims.commit-sha": "abc123"}}}'
        mock_subprocess.return_value.returncode = 0
        
        result = self.detector.get_local_docker_image_commit_sha()
        
        mock_subprocess.assert_called_with(
            ["docker", "inspect", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main"],
            capture_output=True,
            text=True,
            check=True
        )
        assert result == "abc123"

    @patch('utils.branch_utils.get_current_branch')
    def test_backward_compatibility(self, mock_current_branch):
        """Test that existing API still works"""
        mock_current_branch.return_value = "main"
        
        # Should not raise exception when called with old signature
        result = self.detector.check_docker_update("latest")
        assert isinstance(result, dict)
        assert "update_available" in result
```

### Integration Tests

```python
class TestUpdateDetectorIntegration:
    def test_preserves_sha_comparison_logic(self):
        """Test that SHA comparison logic is preserved"""
        detector = UpdateDetector()
        
        # Mock different scenarios and verify logic is unchanged
        with patch.object(detector, 'get_local_docker_image_commit_sha') as mock_local, \
             patch.object(detector, 'get_remote_docker_image_commit_sha') as mock_remote, \
             patch.object(detector, 'is_commit_ancestor') as mock_ancestor:
            
            mock_local.return_value = "abc123"
            mock_remote.return_value = "def456"
            mock_ancestor.return_value = True
            
            result = detector.check_docker_update()
            
            # Verify ancestry check was called with correct parameters
            mock_ancestor.assert_called_with("abc123", "def456")
            assert result["update_available"] == True
```

## Error Handling

### Import Error Handling
```python
def get_remote_docker_image_commit_sha(self, tag: str = "latest", branch: Optional[str] = None) -> Optional[str]:
    """Get the commit SHA from REMOTE Docker image without pulling."""
    try:
        if branch is None:
            try:
                from utils.branch_utils import get_current_branch
                branch = get_current_branch()
            except ImportError:
                # Fallback to hardcoded branch if utils not available
                branch = "main"
            except Exception:
                # Fallback to main if branch detection fails
                branch = "main"
        
        return self.get_remote_commit_sha(branch)
    except Exception:
        return None
```

## Success Criteria

- [ ] Line 114 hardcoded branch reference removed
- [ ] All existing SHA comparison logic preserved
- [ ] Backward compatibility maintained
- [ ] New branch-aware functionality works
- [ ] All existing tests still pass
- [ ] New tests pass
- [ ] Error handling works correctly
- [ ] Performance impact is minimal

## Migration Notes

- Existing code calling `check_docker_update()` will automatically use current branch
- Existing code can optionally specify branch: `check_docker_update(branch="main")`
- Fallback logic ensures system works even if branch detection fails
- No breaking changes to existing API