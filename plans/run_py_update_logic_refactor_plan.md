# run.py Update Logic Refactor Implementation Plan

**Document Purpose**: Comprehensive implementation plan for refactoring [`run.py`](../run.py) update logic to invert production mode default behavior.

**Plan Date**: 2026-01-13  
**Target Version**: 1.1.0  
**Complexity**: Medium - Involves CLI changes, logic inversion, and user messaging

## Executive Summary

This plan details the refactoring of [`run.py`](../run.py) update logic to change the default behavior in production mode. Currently, production mode performs all updates by default with `--no-updates` to skip them. The new behavior will skip core system updates by default but always perform scripts updates, with a new `--updates` flag to enable all updates.

### Key Changes Overview
- **Production Mode Default**: Skip core updates (fatal sync, repository, Docker), always perform scripts updates
- **CLI Interface**: Remove `--no-updates`, add `--updates` flag (long form only)
- **Developer Mode**: No changes whatsoever - maintain existing behavior exactly
- **User Feedback**: Add informational messaging about what updates are being skipped

## 1. Current Architecture Analysis

### Current Update Flow in Production Mode

**Location**: [`UpdateManager.production_auto_update()`](../run.py:414-428)

**Current Sequence** (when updates enabled):
1. **Fatal sync error check** ([`check_fatal_sync_errors()`](../run.py:430-441))
2. **Repository updates** ([`check_repository_updates()`](../run.py:443-491))
3. **Docker image updates** ([`check_docker_updates()`](../run.py:493-515))
4. **Scripts updates** ([`check_scripts_updates()`](../run.py:565-585))

**Current CLI Control**:
- Default: All updates run
- `--no-updates`: All updates skipped

### Current Mode Detection Logic

**Location**: [`DockerLauncher.detect_mode()`](../run.py:625-628)
```python
developer_marker = self.project_root / "config" / "developer.marker"
return "developer" if developer_marker.exists() else "production"
```

**Current Behavior**:
- **Developer Mode**: Always skips all updates ([line 412](../run.py:412))
- **Production Mode**: Performs all updates unless `--no-updates` flag used

## 2. Required Changes Summary

### New Production Mode Behavior
- **Default**: Skip core updates (fatal sync, repository, Docker), always perform scripts updates
- **With `--updates`**: Perform all updates (same as current default behavior)
- **Informational Message**: Show what updates are being skipped and how to enable them

### CLI Changes
- **Remove**: `--no-updates` flag entirely
- **Add**: `--updates` flag (long form only, no short form)
- **Help Text**: Update to reflect new behavior

### Developer Mode
- **No Changes**: Continue to skip all auto-updates exactly as before
- **No New Flags**: `--updates` flag has no effect in developer mode

## 3. Detailed Code Changes

### 3.1 CLI Argument Parser Changes

#### File: [`run.py`](../run.py)

**Lines 739-740: Remove `--no-updates` flag**
```python
# CURRENT CODE (REMOVE):
parser.add_argument('--no-updates', action='store_true',
                   help='Skip update checks')

# REPLACE WITH:
parser.add_argument('--updates', action='store_true',
                   help='Perform all updates (fatal sync, repository, Docker, and scripts)')
```

**Lines 756: Update Click interface**
```python
# CURRENT CODE (REMOVE):
@click.option('--no-updates', is_flag=True, help='Skip update checks')

# REPLACE WITH:
@click.option('--updates', is_flag=True, help='Perform all updates (fatal sync, repository, Docker, and scripts)')
```

**Function Signature Updates**:
- Line 758: `def main(workflow_type, project_path, scripts_path, mode, no_updates):` 
  → `def main(workflow_type, project_path, scripts_path, mode, updates):`
- Line 672: `skip_updates: bool = False` → `perform_all_updates: bool = False`

### 3.2 UpdateManager Logic Changes

#### File: [`run.py`](../run.py)

**Lines 407-412: Update perform_updates method signature**
```python
# CURRENT CODE:
def perform_updates(self, workflow_type: str, mode_config: dict):
    """Perform all necessary updates before container launch."""
    if mode_config["app_env"] == "production":
        self.production_auto_update(workflow_type, mode_config)
    else:
        click.secho("🔧 Development mode - skipping auto-updates", fg='blue')

# NEW CODE:
def perform_updates(self, workflow_type: str, mode_config: dict, perform_all_updates: bool = False):
    """Perform updates before container launch based on mode and flags."""
    if mode_config["app_env"] == "production":
        self.production_auto_update(workflow_type, mode_config, perform_all_updates)
    else:
        click.secho("🔧 Development mode - skipping auto-updates", fg='blue')
```

**Lines 414-428: Refactor production_auto_update method**
```python
# CURRENT CODE:
def production_auto_update(self, workflow_type: str, mode_config: dict):
    """Production mode automatic updates."""
    click.secho("🏭 Production mode - performing automatic updates...", fg='blue', bold=True)
    
    # 1. Fatal sync error check
    self.check_fatal_sync_errors()
    
    # 2. Workflow manager repository updates
    self.check_repository_updates()
    
    # 3. Docker image updates
    self.check_docker_updates()
    
    # 4. Scripts updates
    self.check_scripts_updates(workflow_type, mode_config["scripts_path"])

# NEW CODE:
def production_auto_update(self, workflow_type: str, mode_config: dict, perform_all_updates: bool = False):
    """Production mode automatic updates with configurable behavior."""
    if perform_all_updates:
        click.secho("🏭 Production mode - performing all updates...", fg='blue', bold=True)
        
        # Perform all updates (same as current default behavior)
        self.check_fatal_sync_errors()
        self.check_repository_updates()
        self.check_docker_updates()
        self.check_scripts_updates(workflow_type, mode_config["scripts_path"])
    else:
        click.secho("🏭 Production mode - performing scripts updates only...", fg='blue', bold=True)
        self.display_skipped_updates_message()
        
        # Only perform scripts updates
        self.check_scripts_updates(workflow_type, mode_config["scripts_path"])
```

**Add new method after line 428**
```python
def display_skipped_updates_message(self):
    """Display informational message about skipped updates."""
    click.echo()
    click.secho("ℹ️  Update Information:", fg='blue', bold=True)
    click.echo("   • Core system updates are skipped by default in production mode")
    click.echo("   • Skipping: Fatal sync check, repository updates, Docker image updates")
    click.echo("   • Performing: Scripts updates (always enabled)")
    click.echo("   • To enable all updates, use the --updates flag")
    click.echo()
```

### 3.3 Main Launch Method Updates

**Lines 707-709: Update launch method call**
```python
# CURRENT CODE:
# 7. Update management
if not skip_updates:
    self.update_manager.perform_updates(workflow_type, mode_config)

# NEW CODE:
# 7. Update management
self.update_manager.perform_updates(workflow_type, mode_config, perform_all_updates)
```

**Lines 772, 800: Update main function calls**
```python
# CURRENT CODE (Click version):
launcher.launch(
    workflow_type=workflow_type,
    project_path=project_path,
    scripts_path=scripts_path,
    mode=mode,
    skip_updates=no_updates
)

# NEW CODE (Click version):
launcher.launch(
    workflow_type=workflow_type,
    project_path=project_path,
    scripts_path=scripts_path,
    mode=mode,
    perform_all_updates=updates
)

# CURRENT CODE (Fallback version):
launcher.launch(
    workflow_type=args.workflow_type,
    project_path=args.project_path,
    scripts_path=args.scripts_path,
    mode=args.mode,
    skip_updates=args.no_updates
)

# NEW CODE (Fallback version):
launcher.launch(
    workflow_type=args.workflow_type,
    project_path=args.project_path,
    scripts_path=args.scripts_path,
    mode=args.mode,
    perform_all_updates=args.updates
)
```

## 4. User Experience Changes

### 4.1 New Default Production Mode Behavior
**Command**: `python run.py`

**Output**:
```
🏭 Production mode - performing scripts updates only...

ℹ️  Update Information:
   • Core system updates are skipped by default in production mode
   • Skipping: Fatal sync check, repository updates, Docker image updates
   • Performing: Scripts updates (always enabled)
   • To enable all updates, use the --updates flag

🔍 Checking for workflow-specific script updates...
✅ Scripts are up to date
```

### 4.2 With --updates Flag
**Command**: `python run.py --updates`

**Output** (same as current default):
```
🏭 Production mode - performing all updates...
🔍 Checking for fatal repository/Docker sync errors...
✅ No fatal sync errors detected
🔍 Checking for workflow manager repository updates...
✅ Workflow manager repository is up to date
🔍 Checking for Docker image updates...
✅ Docker image is up to date
🔍 Checking for workflow-specific script updates...
✅ Scripts are up to date
```

### 4.3 Developer Mode (Unchanged)
**Command**: `python run.py` (with developer.marker present)

**Output** (no changes):
```
🔧 Development mode - skipping auto-updates
```

### 4.4 Error Handling for Removed Flag
If someone tries to use the old `--no-updates` flag, they'll get a clear error:
```
error: unrecognized arguments: --no-updates
```

## 5. Testing Strategy

### 5.1 Unit Tests Required

**New Test File**: `tests/test_run_py_update_logic_refactor.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from run import UpdateManager, DockerLauncher

class TestUpdateLogicRefactor:
    """Test suite for update logic refactor."""
    
    @patch('run.click')
    def test_production_mode_default_behavior(self, mock_click):
        """Test production mode skips core updates by default."""
        # Setup
        branch_info = {'branch': 'main', 'tag': 'latest'}
        update_manager = UpdateManager(branch_info)
        mode_config = {"app_env": "production", "scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.check_fatal_sync_errors = Mock()
        update_manager.check_repository_updates = Mock()
        update_manager.check_docker_updates = Mock()
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute
        update_manager.perform_updates("sip", mode_config, perform_all_updates=False)
        
        # Verify only scripts updates called
        update_manager.check_fatal_sync_errors.assert_not_called()
        update_manager.check_repository_updates.assert_not_called()
        update_manager.check_docker_updates.assert_not_called()
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
        update_manager.display_skipped_updates_message.assert_called_once()
    
    @patch('run.click')
    def test_production_mode_with_updates_flag(self, mock_click):
        """Test production mode performs all updates with --updates flag."""
        # Setup
        branch_info = {'branch': 'main', 'tag': 'latest'}
        update_manager = UpdateManager(branch_info)
        mode_config = {"app_env": "production", "scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.check_fatal_sync_errors = Mock()
        update_manager.check_repository_updates = Mock()
        update_manager.check_docker_updates = Mock()
        update_manager.check_scripts_updates = Mock()
        update_manager.display_skipped_updates_message = Mock()
        
        # Execute
        update_manager.perform_updates("sip", mode_config, perform_all_updates=True)
        
        # Verify all updates called
        update_manager.check_fatal_sync_errors.assert_called_once()
        update_manager.check_repository_updates.assert_called_once()
        update_manager.check_docker_updates.assert_called_once()
        update_manager.check_scripts_updates.assert_called_once_with("sip", "/test/scripts")
        update_manager.display_skipped_updates_message.assert_not_called()
    
    @patch('run.click')
    def test_developer_mode_unchanged(self, mock_click):
        """Test developer mode behavior remains unchanged."""
        # Setup
        branch_info = {'branch': 'main', 'tag': 'latest'}
        update_manager = UpdateManager(branch_info)
        mode_config = {"app_env": "development", "scripts_path": "/test/scripts"}
        
        # Mock the individual update methods
        update_manager.production_auto_update = Mock()
        
        # Execute with both flag values
        update_manager.perform_updates("sip", mode_config, perform_all_updates=False)
        update_manager.perform_updates("sip", mode_config, perform_all_updates=True)
        
        # Verify production_auto_update never called
        update_manager.production_auto_update.assert_not_called()
        
        # Verify development message displayed
        mock_click.secho.assert_called_with("🔧 Development mode - skipping auto-updates", fg='blue')
    
    def test_cli_argument_parsing_updates_flag(self):
        """Test CLI argument parsing for new --updates flag."""
        from run import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test with --updates flag
        args = parser.parse_args(['--updates'])
        assert args.updates is True
        
        # Test without --updates flag
        args = parser.parse_args([])
        assert args.updates is False
        
        # Test that --no-updates is no longer recognized
        with pytest.raises(SystemExit):
            parser.parse_args(['--no-updates'])
    
    @patch('run.click')
    def test_informational_messaging(self, mock_click):
        """Test informational message display."""
        # Setup
        branch_info = {'branch': 'main', 'tag': 'latest'}
        update_manager = UpdateManager(branch_info)
        
        # Execute
        update_manager.display_skipped_updates_message()
        
        # Verify message components displayed
        calls = mock_click.echo.call_args_list + mock_click.secho.call_args_list
        call_texts = [str(call) for call in calls]
        
        assert any("Update Information" in text for text in call_texts)
        assert any("Core system updates are skipped" in text for text in call_texts)
        assert any("--updates flag" in text for text in call_texts)
```

### 5.2 Integration Tests

**Test Scenarios**:
1. **Default Production Mode**: Verify only scripts updates run, informational message displayed
2. **Production Mode with --updates**: Verify all updates run, no informational message
3. **Developer Mode**: Verify no changes to existing behavior regardless of flags
4. **CLI Compatibility**: Verify `--no-updates` flag removal doesn't break argument parsing
5. **Error Handling**: Verify error handling remains intact for all update types

### 5.3 Manual Testing Checklist

- [ ] Run `python run.py` in production mode (verify default behavior: scripts only + message)
- [ ] Run `python run.py --updates` in production mode (verify all updates run)
- [ ] Run `python run.py` in developer mode (verify unchanged behavior)
- [ ] Run `python run.py --no-updates` (verify clear error message)
- [ ] Test with both Click and fallback CLI interfaces
- [ ] Verify informational messages display correctly and are helpful
- [ ] Test error scenarios (network issues, git problems, etc.)

## 6. Documentation Updates Required

### 6.1 User-Facing Documentation

**File**: [`docs/user_guide/QUICK_SETUP_GUIDE.md`](../docs/user_guide/QUICK_SETUP_GUIDE.md)
- Update CLI flag documentation (remove `--no-updates`, add `--updates`)
- Add explanation of new default behavior in production mode
- Update examples to show `--updates` flag usage
- Add migration notes for users upgrading from previous versions

**File**: [`docs/user_guide/FEATURES.md`](../docs/user_guide/FEATURES.md)
- Update "Update Management" section to reflect new behavior
- Explain scripts-only vs all-updates modes
- Document informational messaging feature

**File**: [`docs/UNIFIED_PYTHON_LAUNCHER.md`](../docs/UNIFIED_PYTHON_LAUNCHER.md)
- Update CLI reference section
- Add migration guide for `--no-updates` → `--updates` transition
- Update feature comparison table

### 6.2 Developer Documentation

**File**: [`docs/developer_guide/run_py_architecture_analysis.md`](../docs/developer_guide/run_py_architecture_analysis.md)
- Update section 4 "Update Application Timing and Methods"
- Modify production mode auto-update description (lines 131-152)
- Update CLI argument documentation (lines 327-328)
- Add new decision point for update behavior in section 5

**File**: [`docs/developer_guide/ARCHITECTURE.md`](../docs/developer_guide/ARCHITECTURE.md)
- Update update management workflow diagrams
- Document new default behavior patterns
- Update decision flow charts

### 6.3 Help Text Updates

**In [`run.py`](../run.py):**
- Update argument parser help text for `--updates` flag
- Update Click option help text
- Update main function docstrings to reflect new behavior

## 7. Migration and Compatibility

### 7.1 Breaking Changes
- **Removed Flag**: `--no-updates` flag no longer exists
- **Behavior Change**: Production mode default behavior inverted
- **Scripts Impact**: Any automation using `--no-updates` will need updates

### 7.2 Migration Strategy
- **Clear Error Messages**: Provide helpful error when `--no-updates` is used
- **Documentation**: Comprehensive migration guide in all relevant docs
- **Version Bump**: Increment to 1.1.0 to indicate behavior change
- **Release Notes**: Clear explanation of changes and migration path

### 7.3 Backward Compatibility Considerations
- **Developer Mode**: Completely unchanged - no migration needed
- **Interactive Usage**: No changes to interactive prompts or workflows
- **Core Functionality**: All existing functionality preserved, only defaults changed

## 8. Implementation Sequence

### Phase 1: Core Logic Changes (1-2 hours)
1. **Update CLI argument parser** (remove `--no-updates`, add `--updates`)
2. **Modify UpdateManager.perform_updates()** method signature
3. **Refactor UpdateManager.production_auto_update()** method
4. **Add display_skipped_updates_message()** method
5. **Update DockerLauncher.launch()** method signature and calls
6. **Update main() function** signatures and calls

### Phase 2: Testing (2-3 hours)
1. **Create comprehensive unit tests** for new logic
2. **Run existing test suite** to ensure no regressions
3. **Manual testing** of all scenarios
4. **Performance testing** to ensure no slowdowns

### Phase 3: Documentation (1-2 hours)
1. **Update user documentation** (Quick Setup, Features, Unified Launcher)
2. **Update developer documentation** (Architecture Analysis, Architecture)
3. **Update help text** in code
4. **Create migration guide**

### Phase 4: Validation (1 hour)
1. **Final code review** of all changes
2. **Documentation review** for accuracy and completeness
3. **Version bump** to 1.1.0
4. **Prepare release notes**

**Total Estimated Time**: 5-8 hours

## 9. Risk Assessment and Mitigation

### 9.1 High Risk Areas
- **CLI Compatibility**: Existing scripts using `--no-updates` will break
- **User Confusion**: Default behavior change may confuse existing users
- **Testing Coverage**: Complex logic changes require thorough testing

### 9.2 Mitigation Strategies
- **Clear Error Messages**: Provide helpful error for removed `--no-updates` flag
- **Comprehensive Documentation**: Update all user-facing documentation before release
- **Thorough Testing**: Create comprehensive test suite covering all scenarios
- **Gradual Rollout**: Consider feature flag or gradual deployment if possible

### 9.3 Rollback Plan
- **Single Commit**: Implement all changes in single commit for easy rollback
- **Documentation Rollback**: Revert documentation changes if needed
- **User Communication**: Clear communication if rollback required

## 10. Success Criteria

### 10.1 Functional Requirements
- [ ] Production mode skips core updates by default
- [ ] Scripts updates always run in production mode
- [ ] `--updates` flag enables all updates
- [ ] Developer mode behavior completely unchanged
- [ ] Clear informational messaging displayed
- [ ] `--no-updates` flag properly removed

### 10.2 Quality Requirements
- [ ] All existing tests pass
- [ ] New tests achieve >95% coverage of changed code
- [ ] No performance regression
- [ ] Documentation is complete and accurate
- [ ] User experience is intuitive and well-explained

### 10.3 Acceptance Criteria
- [ ] Manual testing confirms all scenarios work correctly
- [ ] Code review completed and approved
- [ ] Documentation review completed
- [ ] Migration guide tested with real scenarios
- [ ] Version properly incremented

## 11. Specific Line-by-Line Changes Summary

### CLI Argument Changes
- **Line 739-740**: Replace `--no-updates` with `--updates` in argument parser
- **Line 756**: Replace `--no-updates` with `--updates` in Click interface
- **Line 758**: Change `no_updates` parameter to `updates` in main function
- **Line 672**: Change `skip_updates: bool = False` to `perform_all_updates: bool = False`

### UpdateManager Changes
- **Line 407**: Add `perform_all_updates: bool = False` parameter
- **Line 409**: Pass `perform_all_updates` to `production_auto_update`
- **Line 414**: Add `perform_all_updates: bool = False` parameter
- **Line 416**: Replace with conditional logic based on `perform_all_updates`
- **After Line 428**: Add `display_skipped_updates_message()` method

### Launch Method Changes
- **Line 708**: Replace `if not skip_updates:` with direct call passing `perform_all_updates`
- **Line 772**: Change `skip_updates=no_updates` to `perform_all_updates=updates`
- **Line 800**: Change `skip_updates=args.no_updates` to `perform_all_updates=args.updates`

---

**Implementation Ready**: This plan provides comprehensive, line-by-line implementation details that a coding agent can follow to implement the requested changes while maintaining all existing functionality and ensuring proper testing and documentation.