# Final Implementation Handoff to Coding Agent

## Overview
Complete implementation plan for transforming SIP LIMS Workflow Manager from hardcoded `:latest` Docker tags to branch-aware tagging system.

## Implementation Documents Created

### 1. Main Instructions
- **[`CODING_AGENT_INSTRUCTIONS.md`](CODING_AGENT_INSTRUCTIONS.md)** - Concise overview and requirements

### 2. Detailed Phase Plans
- **[`phase1_branch_utilities_detailed.md`](phase1_branch_utilities_detailed.md)** - Branch detection and Docker tag utilities
- **[`phase2_update_detector_detailed.md`](phase2_update_detector_detailed.md)** - Fix hardcoded branch in update detector
- **[`phase3_build_push_scripts_detailed.md`](phase3_build_push_scripts_detailed.md)** - Branch-aware build and push scripts
- **[`phase4_run_script_detailed.md`](phase4_run_script_detailed.md)** - Branch-aware run script integration

### 3. Analysis Documents
- **[`branch_aware_docker_implementation_plan.md`](branch_aware_docker_implementation_plan.md)** - Original comprehensive plan
- **[`branch_aware_docker_implementation_plan_gaps_analysis.md`](branch_aware_docker_implementation_plan_gaps_analysis.md)** - Gap analysis and missing details

## Implementation Order (CRITICAL)

### Phase 1: Foundation (MUST BE FIRST)
1. Create `utils/branch_utils.py` with all Python functions
2. Create `utils/branch_utils.sh` with bash wrapper functions
3. Write comprehensive unit tests in `tests/test_branch_utils.py`
4. **Verify all tests pass before proceeding**

### Phase 2: Core Fix (MOST CRITICAL)
1. Modify `src/update_detector.py` to remove hardcoded branch (line 114)
2. Add branch parameter support while preserving existing API
3. Write integration tests for update detection
4. **Verify SHA comparison logic still works correctly**

### Phase 3: Build/Push Scripts
1. Enhance `build_image_from_lock_files.sh` for branch-aware building
2. Enhance `push_image_to_github.sh` for branch-aware pushing
3. Add safety confirmations and error handling
4. Test build → push → verify workflow

### Phase 4: Run Script Integration
1. Enhance `run.command` for branch-aware image selection
2. Integrate with existing update detection workflow
3. Preserve all mode selection and container management
4. Test complete end-to-end workflow

### Phase 5: Manual Validation (USER REQUIRED)
1. User will manually test all scenarios
2. Verify cross-branch isolation works
3. Confirm SHA comparison accuracy
4. Test error handling and edge cases

### Phase 6: Documentation and Finalization
1. Update relevant documentation
2. Create migration guide
3. Commit all changes with comprehensive message

## Key Technical Requirements

### Branch-to-Tag Mapping
- `main` → `:main`
- `analysis/esp-docker-adaptation` → `:analysis-esp-docker-adaptation`
- `feature/auth` → `:feature-auth`
- Any branch → sanitized branch name as tag

### Critical Preservation Requirements
- **SHA comparison logic** in update detector MUST be preserved
- **Chronological update detection** MUST continue working
- **Existing API compatibility** MUST be maintained
- **Docker Compose integration** MUST work unchanged

### Error Handling Requirements
- Graceful fallback when branch detection fails
- Clear error messages for users
- Fallback to 'latest' tag when needed
- Robust bash-Python integration

## Test-Driven Development Approach

### Unit Tests First
- Write tests for each utility function before implementation
- Mock Git commands for consistent testing
- Test edge cases: detached HEAD, invalid characters, long names

### Integration Tests
- Test each script uses correct branch detection
- Mock Docker operations to avoid actual pulls/pushes
- Verify cross-component integration

### Manual Validation
- User will test real-world scenarios
- Verify branch switching works correctly
- Confirm update detection accuracy

## Files to Create/Modify

### New Files
- `utils/branch_utils.py`
- `utils/branch_utils.sh`
- `tests/test_branch_utils.py`
- `tests/test_branch_aware_docker_integration.py`

### Modified Files
- `src/update_detector.py` (line 114 + method enhancements)
- `build_image_from_lock_files.sh` (line 60 + branch detection)
- `push_image_to_github.sh` (lines 19, 39, 53 + safety features)
- `run.command` (lines 151, 230 + update functions)

## Success Criteria Checklist

- [ ] All automated tests pass
- [ ] Manual validation scenarios work correctly
- [ ] No hardcoded branch references remain
- [ ] SHA comparison logic preserved and functional
- [ ] Cross-branch isolation verified
- [ ] Zero breaking changes to existing workflows
- [ ] Error handling works correctly
- [ ] Performance impact is minimal

## Critical Notes for Coding Agent

### DO NOT BREAK
- Existing SHA comparison in `src/update_detector.py`
- Chronological update detection logic
- Docker Compose environment variable handling
- Mode selection workflow in `run.command`

### MUST PRESERVE
- All existing error handling
- Backward compatibility with existing API
- Fallback behavior when utilities fail
- User experience and workflow patterns

### TESTING APPROACH
- Use Test-Driven Development (TDD)
- Write tests first, then implement
- Mock external dependencies (Git, Docker)
- Verify integration between components

### USER VALIDATION REQUIRED
- After automated tests pass, user will manually validate
- User will test branch switching scenarios
- User will verify update detection accuracy
- Only after user approval should documentation be updated and changes committed

## Implementation Tips

### Bash-Python Integration
```bash
# Source utilities at top of bash scripts
source "$DIR/utils/branch_utils.sh"

# Use functions with error checking
BRANCH_TAG=$(get_current_branch_tag)
if [ $? -ne 0 ] || [ -z "$BRANCH_TAG" ]; then
    echo "Error: Branch detection failed"
    exit 1
fi
```

### Error Handling Pattern
```python
def get_current_branch() -> str:
    try:
        # Primary method
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], ...)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # Handle Git errors
        raise GitRepositoryError("Not in a Git repository")
    except Exception as e:
        # Handle unexpected errors
        raise BranchDetectionError(f"Branch detection failed: {e}")
```

### Docker Tag Sanitization
```python
def sanitize_branch_for_docker_tag(branch_name: str) -> str:
    # Convert to lowercase
    tag = branch_name.lower()
    # Replace invalid characters
    tag = re.sub(r'[^a-z0-9.-]', '-', tag)
    # Remove leading/trailing invalid chars
    tag = tag.strip('.-')
    # Truncate if too long
    return tag[:128]
```

## Final Checklist Before Handoff

- [x] All phase plans created with detailed specifications
- [x] Test requirements defined for each phase
- [x] Error handling strategies documented
- [x] Backward compatibility requirements specified
- [x] Critical preservation requirements highlighted
- [x] Implementation order clearly defined
- [x] Success criteria established
- [x] Manual validation plan created

## Ready for Implementation

The coding agent now has comprehensive documentation covering:
- Exact implementation details for each phase
- Complete test specifications
- Error handling requirements
- Backward compatibility preservation
- Integration strategies
- Manual validation procedures

**Proceed with Phase 1 implementation using Test-Driven Development approach.**