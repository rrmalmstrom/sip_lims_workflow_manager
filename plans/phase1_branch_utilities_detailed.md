# Phase 1: Branch Utilities Implementation Detail

## Overview
Create the foundational utilities that all other scripts will use for branch detection and Docker tag generation.

## Files to Create

### 1. `utils/branch_utils.py`

**Purpose**: Core Python functions for branch detection and tag sanitization

**Required Functions**:

```python
import subprocess
import re
from typing import Optional

class GitRepositoryError(Exception):
    """Raised when Git operations fail"""
    pass

class BranchDetectionError(Exception):
    """Raised when branch detection fails"""
    pass

def get_current_branch() -> str:
    """
    Get current Git branch name.
    
    Returns:
        str: Branch name (e.g., "main", "analysis/esp-docker-adaptation")
        
    Raises:
        GitRepositoryError: If not in a Git repository
        BranchDetectionError: If branch detection fails
    """
    # Implementation details:
    # 1. Run: git rev-parse --abbrev-ref HEAD
    # 2. Handle detached HEAD: return "detached-{short-sha}"
    # 3. Validate output is not empty
    # 4. Strip whitespace

def sanitize_branch_for_docker_tag(branch_name: str) -> str:
    """
    Convert branch name to valid Docker tag.
    
    Docker tag rules:
    - Lowercase alphanumeric, periods, dashes, underscores only
    - Cannot start with period or dash
    - Max 128 characters
    
    Args:
        branch_name: Raw branch name
        
    Returns:
        str: Sanitized Docker tag
    """
    # Implementation steps:
    # 1. Convert to lowercase
    # 2. Replace '/' with '-'
    # 3. Replace '_' with '-'
    # 4. Remove invalid characters (keep only: a-z, 0-9, -, .)
    # 5. Ensure doesn't start with . or -
    # 6. Truncate to 128 chars if needed

def get_docker_tag_for_current_branch() -> str:
    """Get Docker tag for current branch."""
    # Combines get_current_branch() + sanitize_branch_for_docker_tag()

def get_local_image_name_for_current_branch() -> str:
    """Get local Docker image name with branch tag."""
    # Returns: sip-lims-workflow-manager:{branch-tag}

def get_remote_image_name_for_current_branch() -> str:
    """Get remote Docker image name with branch tag."""
    # Returns: ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{branch-tag}
```

**Constants**:
```python
REGISTRY_BASE = "ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
LOCAL_IMAGE_BASE = "sip-lims-workflow-manager"
MAX_DOCKER_TAG_LENGTH = 128
```

### 2. `utils/branch_utils.sh`

**Purpose**: Bash wrapper functions that call Python utilities

```bash
#!/bin/bash
# Branch utilities for bash scripts

# Get the directory where this script is located
UTILS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$(dirname "$UTILS_DIR")"

get_current_branch_tag() {
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from utils.branch_utils import get_docker_tag_for_current_branch
try:
    print(get_docker_tag_for_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    exit(1)
"
}

get_local_image_name() {
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from utils.branch_utils import get_local_image_name_for_current_branch
try:
    print(get_local_image_name_for_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    exit(1)
"
}

get_remote_image_name() {
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from utils.branch_utils import get_remote_image_name_for_current_branch
try:
    print(get_remote_image_name_for_current_branch())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    exit(1)
"
}
```

## Test Requirements

### Unit Tests: `tests/test_branch_utils.py`

**Test Cases**:

```python
import pytest
from unittest.mock import patch, MagicMock
from utils.branch_utils import (
    get_current_branch,
    sanitize_branch_for_docker_tag,
    get_docker_tag_for_current_branch,
    GitRepositoryError,
    BranchDetectionError
)

class TestGetCurrentBranch:
    @patch('subprocess.run')
    def test_main_branch(self, mock_run):
        """Test detection of main branch"""
        mock_run.return_value.stdout = "main\n"
        mock_run.return_value.returncode = 0
        assert get_current_branch() == "main"

    @patch('subprocess.run')
    def test_development_branch(self, mock_run):
        """Test detection of development branch"""
        mock_run.return_value.stdout = "analysis/esp-docker-adaptation\n"
        mock_run.return_value.returncode = 0
        assert get_current_branch() == "analysis/esp-docker-adaptation"

    @patch('subprocess.run')
    def test_detached_head(self, mock_run):
        """Test detached HEAD state"""
        mock_run.return_value.stdout = "HEAD\n"
        mock_run.return_value.returncode = 0
        # Should handle detached HEAD gracefully
        result = get_current_branch()
        assert result.startswith("detached-")

    @patch('subprocess.run')
    def test_git_error(self, mock_run):
        """Test Git command failure"""
        mock_run.side_effect = subprocess.CalledProcessError(128, 'git')
        with pytest.raises(GitRepositoryError):
            get_current_branch()

class TestSanitizeBranch:
    def test_main_branch(self):
        """Test main branch sanitization"""
        assert sanitize_branch_for_docker_tag("main") == "main"

    def test_slash_replacement(self):
        """Test slash replacement"""
        assert sanitize_branch_for_docker_tag("analysis/esp-docker-adaptation") == "analysis-esp-docker-adaptation"

    def test_underscore_replacement(self):
        """Test underscore replacement"""
        assert sanitize_branch_for_docker_tag("feature_auth") == "feature-auth"

    def test_case_conversion(self):
        """Test uppercase conversion"""
        assert sanitize_branch_for_docker_tag("Feature/User_Auth") == "feature-user-auth"

    def test_invalid_characters(self):
        """Test invalid character removal"""
        assert sanitize_branch_for_docker_tag("feature@#$%auth") == "feature-auth"

    def test_length_limit(self):
        """Test length truncation"""
        long_name = "a" * 150
        result = sanitize_branch_for_docker_tag(long_name)
        assert len(result) <= 128

    def test_leading_invalid_chars(self):
        """Test removal of leading periods/dashes"""
        assert sanitize_branch_for_docker_tag(".feature") == "feature"
        assert sanitize_branch_for_docker_tag("-feature") == "feature"
```

### Integration Tests: `tests/test_branch_utils_integration.py`

```python
import subprocess
import tempfile
import os
from pathlib import Path
from utils.branch_utils import get_current_branch, get_docker_tag_for_current_branch

class TestBranchUtilsIntegration:
    def test_real_git_repository(self):
        """Test with actual Git repository"""
        # This test runs in the actual project repository
        branch = get_current_branch()
        assert isinstance(branch, str)
        assert len(branch) > 0

    def test_docker_tag_generation(self):
        """Test complete tag generation"""
        tag = get_docker_tag_for_current_branch()
        assert isinstance(tag, str)
        assert len(tag) > 0
        # Verify it's a valid Docker tag format
        assert tag.islower()
        assert not tag.startswith('.')
        assert not tag.startswith('-')
```

## Error Handling Requirements

1. **Git Repository Validation**: Check if we're in a Git repository before running commands
2. **Command Failure Handling**: Graceful handling of Git command failures
3. **Empty Output Handling**: Handle cases where Git commands return empty output
4. **Path Resolution**: Ensure Python path is correctly set for imports
5. **Subprocess Error Propagation**: Properly propagate errors from Python to bash

## Success Criteria

- [ ] All unit tests pass
- [ ] Integration tests work in real Git repository
- [ ] Bash functions can call Python utilities successfully
- [ ] Error handling works correctly
- [ ] Docker tag validation passes for all test cases
- [ ] Performance is acceptable (< 100ms for branch detection)

## Usage Examples

```bash
# In bash scripts
source utils/branch_utils.sh
BRANCH_TAG=$(get_current_branch_tag)
LOCAL_IMAGE=$(get_local_image_name)
REMOTE_IMAGE=$(get_remote_image_name)
```

```python
# In Python scripts
from utils.branch_utils import get_docker_tag_for_current_branch
tag = get_docker_tag_for_current_branch()