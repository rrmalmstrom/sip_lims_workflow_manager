# Branch-Aware Docker Implementation Instructions

## OBJECTIVE
Transform SIP LIMS Workflow Manager from hardcoded `:latest` Docker tags to branch-aware tags where `main` → `:main`, `analysis/esp-docker-adaptation` → `:analysis-esp-docker-adaptation`, etc.

## CRITICAL REQUIREMENTS
- **Preserve existing SHA comparison logic** - DO NOT BREAK the chronological update detection
- **Use Test-Driven Development** - Write tests first, then implement
- **Manual validation required** - User will test manually before final commit
- **Zero breaking changes** - Existing workflows must continue working

## IMPLEMENTATION APPROACH

### Phase 1: Create Branch Utilities
**File**: `utils/branch_utils.py`
```python
def get_current_branch() -> str:
    """Get current Git branch using: git rev-parse --abbrev-ref HEAD"""

def sanitize_branch_for_docker_tag(branch_name: str) -> str:
    """Convert branch to valid Docker tag: replace / with -, lowercase"""

def get_docker_tag_for_current_branch() -> str:
    """Return sanitized tag for current branch"""
```

**File**: `utils/branch_utils.sh` (bash wrapper)
```bash
get_current_branch_tag() {
    python3 -c "from utils.branch_utils import get_docker_tag_for_current_branch; print(get_docker_tag_for_current_branch())"
}
```

### Phase 2: Fix Update Detector
**File**: `src/update_detector.py`
- **Line 114**: Remove hardcoded `"analysis/esp-docker-adaptation"`
- **Replace with**: Dynamic branch detection using new utilities
- **Preserve**: All existing SHA comparison and chronological logic

### Phase 3: Enhance Build Script
**File**: `build_image_from_lock_files.sh`
- **Line 60**: Change `-t sip-lims-workflow-manager:latest` to `-t sip-lims-workflow-manager:{branch-tag}`
- **Add**: Branch detection at top of script
- **Preserve**: All existing SHA embedding and build args

### Phase 4: Enhance Push Script
**File**: `push_image_to_github.sh`
- **Lines 19, 39, 53**: Replace `:latest` with `:{branch-tag}`
- **Add**: Safety confirmation showing branch being pushed
- **Preserve**: All existing validation and error handling

### Phase 5: Enhance Run Script
**File**: `run.command`
- **Lines 151, 230**: Replace hardcoded image URLs with branch-aware versions
- **Modify**: `production_auto_update()` to use branch-specific images
- **Preserve**: All existing update detection workflow

## KEY TECHNICAL DETAILS

### Docker Tag Rules
- Lowercase only: `Analysis/ESP` → `analysis-esp`
- Replace `/` with `-`: `feature/auth` → `feature-auth`
- Max 128 characters
- No invalid characters

### Error Handling
- Handle detached HEAD gracefully
- Validate Git repository exists
- Provide clear error messages
- Fallback to existing behavior on errors

### Bash-Python Integration
```bash
# Source utilities at top of bash scripts
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$DIR/utils/branch_utils.sh"

# Use in scripts
BRANCH_TAG=$(get_current_branch_tag)
```

## TESTING REQUIREMENTS

### Unit Tests
- `tests/test_branch_utils.py` - Test all utility functions
- Mock Git commands for consistent testing
- Test edge cases: detached HEAD, invalid characters, long names

### Integration Tests
- `tests/test_branch_aware_docker_integration.py`
- Test each script uses correct branch detection
- Mock Docker operations to avoid actual pulls/pushes

### Manual Test Scenarios
1. **Main Branch**: Build → Push → Pull on `main` branch
2. **Dev Branch**: Build → Push → Pull on `analysis/esp-docker-adaptation`
3. **Branch Switching**: Switch branches, verify different images used
4. **Update Detection**: Verify SHA comparison still works correctly

## FILES TO MODIFY
- `utils/branch_utils.py` (new)
- `utils/branch_utils.sh` (new)
- `src/update_detector.py` (fix line 114)
- `build_image_from_lock_files.sh` (line 60 + branch detection)
- `push_image_to_github.sh` (lines 19, 39, 53)
- `run.command` (lines 151, 230 + update functions)

## SUCCESS CRITERIA
- [ ] All automated tests pass
- [ ] Manual validation scenarios work
- [ ] No hardcoded branch references remain
- [ ] SHA comparison logic preserved
- [ ] Cross-branch isolation verified

## WORKFLOW
1. **TDD**: Write tests first for each component
2. **Implement**: Create utilities, then modify scripts
3. **Manual Test**: User validates functionality
4. **Document**: Update docs after validation
5. **Commit**: Final commit with comprehensive message

## CRITICAL NOTES
- **DO NOT** break existing SHA comparison in `update_detector.py`
- **DO NOT** change the core update detection workflow in `run.command`
- **DO** preserve all existing error handling and validation
- **DO** maintain backward compatibility during transition