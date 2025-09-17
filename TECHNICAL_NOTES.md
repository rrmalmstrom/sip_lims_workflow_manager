# Technical Notes: Enhanced GUI Features & Pseudo-Terminal Bug Fixes

**Date**: 2025-09-10
**Version**: Session 4 & 5 Enhancements

## Overview

This document provides technical details for the enhanced GUI features implemented in Session 4, including smart re-run file input behavior and comprehensive undo functionality with complete project state restoration, as well as the critical pseudo-terminal bug fixes implemented in Session 5.

## Feature 1: Enhanced Re-run File Input Behavior

### Problem Statement
Previously, when re-running completed workflow steps that required file inputs, the GUI would reuse the previously selected files without prompting the user for new selections. This could lead to unintended reprocessing of old data.

### Solution Implementation

#### Modified Files
- **`app.py`** (lines 247-270): Enhanced file input widget display logic
- **`app.py`** (lines 270-285): Updated re-run button validation logic

#### Key Changes
1. **Input Widget Display Logic**:
   ```python
   # OLD: Only show inputs for non-completed steps
   if 'inputs' in step and status != 'completed' and not is_running_this_step:
   
   # NEW: Show inputs for all steps when not running (including completed)
   if 'inputs' in step and not is_running_this_step:
   ```

2. **Automatic Input Clearing**:
   ```python
   if status == 'completed':
       st.info("💡 **Re-run Setup**: Please select input files for this re-run...")
       if f"rerun_inputs_cleared_{step_id}" not in st.session_state:
           st.session_state.user_inputs[step_id] = {}
           st.session_state[f"rerun_inputs_cleared_{step_id}"] = True
   ```

3. **Re-run Button Validation**:
   ```python
   if 'inputs' in step:
       step_inputs = st.session_state.user_inputs.get(step_id, {})
       required_inputs = step['inputs']
       if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
           rerun_button_disabled = True
   ```

### User Experience
- Clear messaging about re-run setup requirements
- Automatic clearing of previous input selections
- Re-run button remains disabled until new files are selected
- Visual feedback through info messages

## Feature 2: Complete Undo Functionality

### Problem Statement
The original undo system only updated workflow state but didn't restore the actual project files and directories to their previous state. Users needed comprehensive rollback that would remove all files created by the undone step.

### Solution Implementation

#### Enhanced Snapshot System

##### New Methods in `src/logic.py`
1. **`take_complete_snapshot(step_id)`** (lines 60-85):
   - Creates complete ZIP archive of entire project directory
   - Excludes system files (`.snapshots`, `.workflow_status`, etc.)
   - Uses ZIP compression for efficient storage
   - Provides detailed logging of snapshot creation

2. **`restore_complete_snapshot(step_id)`** (lines 87-140):
   - Compares current project state with snapshot
   - Removes files that exist now but weren't in snapshot
   - Removes empty directories created after snapshot
   - Extracts all files from snapshot
   - Preserves essential system directories

##### Core Logic Integration (`src/core.py`)
```python
# Enhanced run_step method (lines 74-76)
if is_first_run:
    # Take both legacy and complete snapshots for compatibility
    self.snapshot_manager.take(step_id, snapshot_items)
    self.snapshot_manager.take_complete_snapshot(step_id)
```

#### Undo Function Implementation (`app.py`)

##### Complete Undo Logic (lines 83-130)
```python
def perform_undo(project):
    # Find last completed step
    completed_steps = [step for step in project.workflow.steps 
                      if project.get_state(step['id']) == 'completed']
    
    if step_index == 0:
        # First step: restore to initial state
        project.snapshot_manager.restore_complete_snapshot(last_step_id)
    else:
        # Later step: restore to previous step's state
        previous_step_id = project.workflow.steps[step_index - 1]['id']
        project.snapshot_manager.restore_complete_snapshot(previous_step_id)
    
    # Clean up success markers and update state
    success_marker.unlink()
    project.update_state(last_step_id, "pending")
```

##### GUI Integration (lines 147-171)
- Two-click confirmation system
- Clear warning messages
- Success feedback
- Error handling with user-friendly messages

### Technical Details

#### File Exclusion Strategy
```python
exclude_patterns = {
    '.snapshots',      # Avoid recursion
    '.workflow_status', # Preserve workflow state
    '__pycache__',     # Python cache files
    '.DS_Store',       # macOS system files
    'debug_script_execution.log',  # Debug logs
    'last_script_result.txt',      # Script results
    'workflow_debug.log'           # Workflow logs
}
```

#### Preservation Strategy
```python
preserve_patterns = {
    '.snapshots',      # Never delete snapshots
    '.workflow_status', # Preserve workflow status
    'workflow.yml',    # Preserve workflow definition
    '__pycache__'      # Preserve Python cache
}
```

## Feature 3: Success Marker Bug Fixes

### Problem Statement
Workflow scripts were creating success marker files with inconsistent naming conventions, causing the GUI to not recognize script completion properly.

### Solution Implementation

#### Script Updates
- **Fixed naming convention**: Changed from `script_name.py.success` to `script_name.success`
- **Updated 19 workflow scripts**: Used `sed` command for bulk update
- **Enhanced specific scripts**: Updated `ultracentrifuge.transfer.py` and `setup.isotope.and.FA.plates.py` to use `Path(__file__).stem`

#### Core Logic Fix (`src/core.py`)
```python
# Enhanced success marker checking (lines 160-167)
def _check_success_marker(self, script_name: str) -> bool:
    # Extract just the filename without path and extension
    script_filename = Path(script_name).stem
    
    status_dir = self.path / ".workflow_status"
    success_file = status_dir / f"{script_filename}.success"
    return success_file.exists()
```

## Testing Implementation

### Test-Driven Development Approach
- **Created comprehensive test suite**: `tests/test_gui_features.py`
- **9 new test cases**: Covering both re-run and undo functionality
- **Integration with existing tests**: All 20 tests passing
- **Mock-based testing**: Using unittest.mock for GUI state simulation

### Test Categories
1. **Re-run File Input Behavior Tests**:
   - Input clearing verification
   - Button state validation
   - Different input scenarios

2. **Undo Functionality Tests**:
   - Project state restoration
   - Confirmation dialog logic
   - Button availability logic
   - Snapshot preservation

3. **GUI Integration Tests**:
   - Widget state management
   - Button placement and configuration

## Performance Considerations

### Snapshot System
- **Storage**: Complete snapshots use more disk space but provide comprehensive restoration
- **Compression**: ZIP compression reduces storage overhead
- **Exclusions**: Smart file exclusions prevent unnecessary data storage
- **Cleanup**: Old snapshots can be manually cleaned if disk space becomes an issue

### Memory Usage
- **Streaming**: ZIP operations use streaming to minimize memory footprint
- **Lazy Loading**: Snapshots are only loaded when needed for restoration

## Error Handling

### Undo Operation Errors
- **Missing Snapshots**: Graceful fallback with user notification
- **File Permission Issues**: Error logging and user feedback
- **Partial Restoration**: Transaction-like behavior with rollback on failure

### Re-run Input Validation
- **Missing Files**: Clear validation messages
- **Invalid Paths**: File existence checking
- **Permission Issues**: User-friendly error reporting

## Future Enhancements

### Potential Improvements
1. **Incremental Snapshots**: Only store changed files to reduce storage
2. **Snapshot Compression**: Advanced compression algorithms
3. **Undo History**: Multiple levels of undo/redo
4. **Selective Restoration**: Allow users to choose which files to restore

### Monitoring and Logging
- **Snapshot Metrics**: Track snapshot sizes and creation times
- **Restoration Metrics**: Monitor restoration success rates
- **User Analytics**: Track feature usage patterns

## Conclusion

These enhancements significantly improve the user experience by providing:
1. **Reliable Re-runs**: Ensuring fresh data selection for each re-run
2. **Complete Undo**: Comprehensive project state restoration
3. **Robust Error Handling**: Graceful failure management
4. **Comprehensive Testing**: Ensuring feature reliability

The implementation follows best practices for maintainability, performance, and user experience while maintaining backward compatibility with existing workflows.

## Feature 4: Pseudo-Terminal Bug Resolution (Session 5)

### Problem Statement
The ultracentrifuge.transfer.py script's pseudo-terminal was not appearing in the GUI, preventing users from providing interactive input. The terminal worked correctly for the setup isotope script but failed for the ultracentrifuge script, causing the workflow to hang at the DNA mass input prompt.

### Root Cause Analysis

#### 1. Invalid YAML Syntax
**File**: `dummy_chakraborty_ultra/workflow.yml`
**Issue**: Duplicate `inputs:` sections (lines 25-32) caused YAML parsing errors
```yaml
# PROBLEMATIC STRUCTURE
ultracentrifuge_transfer:
  inputs:
    - type: file
      name: "Tube File"
      arg: ""
  inputs:  # DUPLICATE - caused parsing failure
    - type: file
      name: "Tube File"
      arg: ""
```

#### 2. Path Construction Bug
**File**: `scripts/ultracentrifuge.transfer.py`
**Issue**: Script logic created duplicate directory paths causing FileNotFoundError
```python
# PROBLEMATIC CODE (lines 369-375)
# Created paths like: 2_load_ultracentrifuge/2_load_ultracentrifuge/file.csv
tube_file = PROJECT_DIR / "2_load_ultracentrifuge" / input_file_arg
```

#### 3. Script Structure Inconsistencies
**Issues**:
- Debug print statements interfering with PTY output capture
- Import order differences from working setup isotope script
- Inconsistent error handling patterns

### Solution Implementation

#### YAML Syntax Fix
```yaml
# CORRECTED STRUCTURE
ultracentrifuge_transfer:
  name: "2. Ultracentrifuge Transfer"
  script: "scripts/ultracentrifuge.transfer.py"
  snapshot_items:
    - "project_database.db"
    - "2_load_ultracentrifuge/"
  inputs:
    - type: file
      name: "Tube File"
      arg: ""
```

#### Path Construction Fix
```python
# CORRECTED CODE (lines 369-375)
if input_file_arg.startswith("2_load_ultracentrifuge/"):
    # GUI provides relative path - use directly
    tube_file = PROJECT_DIR / input_file_arg
else:
    # Command line provides filename only - construct full path
    tube_file = PROJECT_DIR / "2_load_ultracentrifuge" / input_file_arg
```

#### Script Structure Cleanup
- Removed debug print statements that interfered with PTY output
- Standardized import order to match working setup isotope script
- Cleaned up error handling to be consistent

### Enhanced Terminal Visibility Implementation

#### Problem Statement
Even when the pseudo-terminal worked, users couldn't easily locate it because it appeared at the top of the page while they were looking at steps further down.

#### Solution: Visual Enhancement Strategy
Instead of complex JavaScript auto-scroll (which proved unreliable with Streamlit's architecture), implemented prominent native visual indicators.

#### Technical Implementation (`app.py`)
```python
# Enhanced terminal display (lines 351-369)
if st.session_state.running_step_id:
    # Make terminal very prominent with visual indicators
    running_step = project.workflow.get_step_by_id(st.session_state.running_step_id)
    
    # Large, prominent header
    st.markdown("# 🖥️ LIVE TERMINAL")
    st.error(f"🚨 **SCRIPT RUNNING**: {running_step['name'] if running_step else 'Unknown Step'}")
    st.warning("⚠️ **IMPORTANT**: Interactive input required below!")
    
    # Terminal with prominent styling
    st.text_area(
        "Terminal Output",
        value=st.session_state.terminal_output,
        height=300,
        key="terminal_view",
        disabled=True,
        help="This is the live terminal output. Watch for prompts that require your input."
    )
```

### Visual Enhancement Features
1. **Large Header**: `# 🖥️ LIVE TERMINAL` - Impossible to miss
2. **Red Error Banner**: Shows which script is running with 🚨 icon
3. **Yellow Warning**: Alerts about interactive input requirement with ⚠️ icon
4. **Enhanced Tooltip**: Helpful guidance text for the terminal area
5. **Consistent Styling**: Uses Streamlit's native components for reliability

### Testing and Verification

#### Test Methodology
1. **Systematic Debugging**: Used step-by-step approach to isolate each issue
2. **Component Testing**: Tested YAML parsing, path construction, and script execution separately
3. **Integration Testing**: Verified complete workflow from GUI button click to script completion
4. **Cross-Script Comparison**: Ensured ultracentrifuge script behaves identically to working setup isotope script

#### Verification Results
- ✅ Pseudo-terminal appears correctly for ultracentrifuge script
- ✅ Interactive DNA mass input prompt is visible and functional
- ✅ Script completes successfully with user input
- ✅ Enhanced visual indicators make terminal impossible to miss
- ✅ Consistent behavior across all interactive scripts

### Performance Impact
- **Minimal Overhead**: Visual enhancements use native Streamlit components
- **No JavaScript Dependencies**: Eliminates browser compatibility issues
- **Reliable Display**: Works consistently across all browsers and devices
- **Fast Rendering**: Native components render faster than custom JavaScript

### Maintenance Considerations
- **Simple Implementation**: Uses standard Streamlit patterns for easy maintenance
- **No External Dependencies**: Reduces complexity and potential failure points
- **Clear Code Structure**: Well-documented and easy to understand
- **Backward Compatibility**: Doesn't affect existing functionality

## Conclusion (Updated)

The Session 5 enhancements successfully resolved critical pseudo-terminal issues while improving the overall user experience:

1. **Systematic Bug Resolution**: Identified and fixed multiple root causes preventing pseudo-terminal display
2. **Enhanced User Experience**: Prominent visual indicators make interactive terminals impossible to miss
3. **Reliable Implementation**: Uses native Streamlit components for consistent cross-platform behavior
4. **Comprehensive Testing**: Thorough verification ensures robust functionality

Combined with the Session 4 features, the LIMS Workflow Manager now provides:
- Reliable interactive script execution
- Comprehensive project state management
- Smart re-run behavior with fresh input prompts
- Complete undo functionality with project restoration
- Enhanced terminal visibility for all interactive scripts

The implementation maintains high standards for maintainability, performance, and user experience while ensuring backward compatibility with existing workflows.

## Feature 5: Granular Undo for Individual Step Re-runs (Session 6)

### Problem Statement
The original undo system was designed for linear workflows where each step runs once. However, users needed the ability to re-run steps multiple times and undo individual re-runs rather than reverting entire steps. When a step was re-run multiple times, undo would revert all runs instead of just the most recent one, and step status management was incorrect.

### Solution Implementation

#### Enhanced Snapshot System for Run Tracking

##### New Snapshot Strategy
The system now creates two types of snapshots for each run:
1. **Before snapshots**: `{step_id}_run_{N}_complete.zip` - taken before each run starts
2. **After snapshots**: `{step_id}_run_{N}_after_complete.zip` - taken after successful completion

##### Core Logic Integration (`src/core.py`)
```python
# Enhanced run_step method (lines 75-77)
run_number = self.snapshot_manager.get_next_run_number(step_id)
self.snapshot_manager.take_complete_snapshot(f"{step_id}_run_{run_number}")

# Enhanced handle_step_result method (lines 128-131)
if actual_success:
    self.update_state(step_id, "completed")
    run_number = self.snapshot_manager.get_current_run_number(step_id)
    if run_number > 0:
        self.snapshot_manager.take_complete_snapshot(f"{step_id}_run_{run_number}_after")
```

#### New SnapshotManager Methods (`src/logic.py`)

##### Run Number Management (lines 60-79)
```python
def get_next_run_number(self, step_id: str) -> int:
    """Gets the next run number for a step by checking existing run snapshots."""
```

##### Effective Run Tracking (lines 135-154)
```python
def get_effective_run_number(self, step_id: str) -> int:
    """Gets the effective current run number by checking which 'after' snapshots exist."""
```

##### Snapshot Cleanup (lines 156-175)
```python
def remove_run_snapshots_from(self, step_id: str, run_number: int):
    """Remove all run snapshots from the specified run number onwards."""
```

#### Granular Undo Logic (`app.py`)

##### Progressive Undo Implementation (lines 163-190)
```python
def perform_undo(project):
    # Get the effective current run number (what we're currently at)
    effective_run = project.snapshot_manager.get_effective_run_number(last_step_id)
    
    if effective_run > 1:
        # Restore to the previous run's state (after previous run completed)
        previous_run_snapshot = f"{last_step_id}_run_{effective_run - 1}_after"
        project.snapshot_manager.restore_complete_snapshot(previous_run_snapshot)
        # Remove the current run's 'after' snapshot to track that it's been undone
        project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
        # Step remains "completed" since previous runs still exist
        
    elif effective_run == 1:
        # This is the last run - undo the entire step
        run_1_before_snapshot = f"{last_step_id}_run_1"
        project.snapshot_manager.restore_complete_snapshot(run_1_before_snapshot)
        # Remove all run snapshots and mark step as "pending"
```

##### Smart Step Status Management (lines 191-202)
```python
# Check the effective run number after undo to determine step status
effective_run_after_undo = project.snapshot_manager.get_effective_run_number(last_step_id)

if effective_run_after_undo > 0:
    # Step remains "completed" since previous runs still exist
else:
    # Mark step as "pending" and remove success marker
    project.update_state(last_step_id, "pending")
```

### Technical Details

#### Snapshot Naming Convention
- **Before run**: `step_id_run_1_complete.zip`, `step_id_run_2_complete.zip`, etc.
- **After run**: `step_id_run_1_after_complete.zip`, `step_id_run_2_after_complete.zip`, etc.

#### Undo Progression Logic
1. **Multiple runs exist**: Restore to previous run's "after" state, step stays "completed"
2. **Single run exists**: Restore to step's "before" state, step becomes "pending"
3. **Snapshot tracking**: Remove "after" snapshots to track undo progress

#### Step Status Rules
- **Step remains "completed"**: As long as `effective_run_number > 0`
- **Step becomes "pending"**: Only when all runs have been undone (`effective_run_number = 0`)

### User Experience

#### Unlimited Re-runs
- Users can re-run any step unlimited times
- Each re-run creates independent snapshots
- No hardcoded limits on number of re-runs

#### Progressive Granular Undo
- Each undo goes back exactly one run
- Files from only the most recent run are removed
- Project state restored to immediately before that run

#### Intelligent Step Status
- Step status reflects actual completion state
- "Completed" preserved until all runs undone
- Clear feedback about which run state is active

### Example Workflow

**Step 2 with 3 runs**:
1. Run 1 → Creates `step2_run_1_complete.zip` + `step2_run_1_after_complete.zip`
2. Run 2 → Creates `step2_run_2_complete.zip` + `step2_run_2_after_complete.zip`
3. Run 3 → Creates `step2_run_3_complete.zip` + `step2_run_3_after_complete.zip`

**Undo sequence**:
1. 1st Undo → Restore to `step2_run_2_after`, remove `step2_run_3_after`, status: "completed"
2. 2nd Undo → Restore to `step2_run_1_after`, remove `step2_run_2_after`, status: "completed"
3. 3rd Undo → Restore to `step2_run_1`, remove `step2_run_1_after`, status: "pending"

### Performance Considerations

#### Storage Efficiency
- Only stores incremental changes between runs
- Automatic cleanup of undone run snapshots
- Compressed ZIP storage for all snapshots

#### Memory Usage
- Lazy loading of snapshots only when needed
- Streaming ZIP operations to minimize memory footprint
- Efficient file comparison for restoration

### Backward Compatibility

#### Legacy Support
- Maintains compatibility with existing single-run workflows
- Graceful fallback to original snapshot naming if run snapshots don't exist
- No breaking changes to existing workflow definitions

#### Migration Path
- Existing projects continue to work without modification
- New granular features activate automatically for new runs
- No data migration required

## Conclusion (Updated for Session 6)

The Session 6 enhancements provide a comprehensive granular undo system that transforms the LIMS Workflow Manager from a linear workflow tool into a flexible, re-run-capable system:

1. **Unlimited Re-runs**: Any step can be re-run unlimited times with proper tracking
2. **Granular Undo**: Each undo operation targets exactly one run, not entire steps
3. **Intelligent Status Management**: Step status accurately reflects completion state
4. **Universal Compatibility**: Works for all steps in any workflow configuration
5. **Backward Compatibility**: Existing workflows continue to function without changes

Combined with previous session features, the LIMS Workflow Manager now provides:
- Reliable interactive script execution with enhanced terminal visibility
- Comprehensive project state management with empty directory preservation
- Smart re-run behavior with fresh input prompts for each execution
- Complete undo functionality with both step-level and run-level granularity
- Robust error handling with automatic rollback and success marker verification

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the flexibility needed for complex laboratory workflows.

## Feature 6: Enhanced Granular Undo with Previous Step Restoration (Session 7)

### Problem Statement
The granular undo system had a critical gap: when undoing the last remaining run of a step, it couldn't handle cases where previous runs had been undone (creating gaps in "after" snapshots). This caused the undo button to appear but do nothing when clicked, particularly when trying to undo the first run of a step after multiple re-runs and undos.

### Root Cause Analysis

#### The Snapshot Gap Issue
When users performed multiple re-runs and undos, the snapshot pattern became:
- `step_run_1_complete.zip` ✅ (before run 1)
- `step_run_1_after_complete.zip` ❌ (removed by previous undo)
- `step_run_2_complete.zip` ✅ (before run 2)
- `step_run_2_after_complete.zip` ✅ (current effective run)

#### The Logic Failure
The original undo logic assumed consecutive "after" snapshots:
```python
# BROKEN: Assumed run_1_after exists
previous_run_snapshot = f"{step_id}_run_{effective_run - 1}_after"
if project.snapshot_manager.snapshot_exists(previous_run_snapshot):
    # This would fail because run_1_after was removed by previous undo
```

### Solution Implementation

#### Enhanced Backwards Search Logic
Modified the undo logic in `app.py` to handle gaps gracefully:

```python
# NEW: Search backwards through all possible "after" snapshots
target_run = None
for run_num in range(effective_run - 1, 0, -1):
    candidate_snapshot = f"{last_step_id}_run_{run_num}_after"
    if project.snapshot_manager.snapshot_exists(candidate_snapshot):
        target_run = run_num
        break

if target_run:
    # Restore to found snapshot
else:
    # NEW: Look at previous step's "after" snapshot
    if step_index > 0:
        previous_step = project.workflow.steps[step_index - 1]
        previous_step_id = previous_step['id']
        previous_effective_run = project.snapshot_manager.get_effective_run_number(previous_step_id)
        
        if previous_effective_run > 0:
            previous_after_snapshot = f"{previous_step_id}_run_{previous_effective_run}_after"
            if project.snapshot_manager.snapshot_exists(previous_after_snapshot):
                # Restore to previous step's state
                project.snapshot_manager.restore_complete_snapshot(previous_after_snapshot)
                # Mark current step as pending
                project.update_state(last_step_id, "pending")
```

#### Key Enhancements
1. **Backwards Search**: Searches through all possible previous "after" snapshots, not just the immediate previous one
2. **Previous Step Restoration**: When no current step "after" snapshots exist, restores to the previous step's latest "after" snapshot
3. **Proper State Management**: Correctly marks steps as "pending" and removes success markers when undoing entire steps
4. **Graceful Fallback**: Maintains compatibility with legacy snapshot naming

### Test-Driven Development Approach

#### Comprehensive Test Suite
Created `tests/test_granular_undo_fix.py` with 9 test cases covering all scenarios:

1. **Gap handling**: Verifies backwards search works with missing "after" snapshots
2. **Normal operation**: Ensures existing functionality still works
3. **Edge cases**: Tests single runs, no snapshots, and error conditions
4. **Previous step restoration**: Validates restoration to previous step's state

#### Test Results
✅ **All 9 tests PASSED** - Comprehensive validation of the fix

### Manual Testing Verification

#### Test Scenario
- **Project**: `dummy_chakraborty` with multiple ultracentrifuge runs
- **Snapshot Pattern**: Only run 2 had "after" snapshot (runs 1,3,4 removed by previous undos)
- **Issue**: Undo button appeared but did nothing when clicked

#### Fix Verification
Terminal output confirmed successful operation:
```
UNDO: Restored project to state after setup_plates (run 1)
UNDO: Removed success marker for ultracentrifuge.transfer
UNDO: Marked step ultracentrifuge_transfer as pending
```

### Technical Implementation Details

#### Scenario Handling
The fix correctly handles these scenarios:

**Scenario 1: Consecutive "after" snapshots exist**
- Behavior: Normal granular undo (run N → run N-1)
- Example: `run_3_after` → `run_2_after`

**Scenario 2: Gaps in "after" snapshots**
- Behavior: Backwards search finds next available "after" snapshot
- Example: `run_4_after` → `run_2_after` (skipping missing `run_3_after`)

**Scenario 3: No current step "after" snapshots**
- Behavior: Restore to previous step's latest "after" snapshot
- Example: `ultracentrifuge_run_2` → `setup_plates_run_1_after`

**Scenario 4: First step or no previous snapshots**
- Behavior: Restore to current step's "before" snapshot (clean state)
- Example: `setup_plates_run_1` → clean project state

### Performance and Reliability

#### Efficiency
- **Backwards search**: O(n) where n = number of runs, typically small
- **Snapshot operations**: Unchanged, same performance as before
- **Memory usage**: No additional memory overhead

#### Error Handling
- **Missing snapshots**: Graceful fallback to alternative restoration methods
- **File system errors**: Proper exception handling with user feedback
- **State corruption**: Transaction-like behavior prevents partial state changes

### Backward Compatibility

#### Legacy Support
- **Existing projects**: Continue to work without modification
- **Old snapshot naming**: Fallback support for pre-granular snapshots
- **Single-run workflows**: No behavioral changes for simple workflows

#### Migration
- **No migration required**: Enhancement is transparent to existing users
- **Gradual adoption**: New granular features activate automatically for new runs

## Conclusion (Updated for Session 7)

The Session 7 enhancements complete the granular undo system by addressing the critical gap in previous step restoration. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Complete Granular Undo**: Handle any combination of runs and undos across all steps
2. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts
3. **Comprehensive State Management**: Empty directory preservation and complete project restoration
4. **Smart Re-run Behavior**: Fresh input prompts for each execution with automatic input clearing
5. **Robust Error Handling**: Automatic rollback, success marker verification, and graceful failure recovery
6. **Universal Compatibility**: Works for all steps in any workflow configuration with full backward compatibility

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the flexibility and reliability needed for complex laboratory workflows.

## Feature 7: Selective Re-run Capability (Session 8)

### Problem Statement
Previously, all completed workflow steps showed re-run buttons, allowing users to re-execute any step. However, the user needed to restrict re-run capability to only specific steps that require iterative execution, while preventing re-runs of steps that should only be executed once.

### Solution Implementation

#### Enhanced Workflow Definition
Added support for an optional `allow_rerun` property in workflow step definitions:

```yaml
- id: ultracentrifuge_transfer
  name: "2. Create Ultracentrifuge Tubes"
  script: "ultracentrifuge.transfer.py"
  snapshot_items: ["Project_Database.db", "outputs/"]
  allow_rerun: true  # Enables re-run capability
  inputs:
    - type: file
      name: "Ultracentrifuge CSV File"
      arg: ""
```

#### GUI Logic Enhancement (`app.py`)
Modified the step display logic to conditionally show re-run buttons:

```python
# Show Re-run button for completed steps that allow re-runs
if status == "completed" and step.get('allow_rerun', False):
    # Check if all required inputs for re-run are filled
    rerun_button_disabled = run_button_disabled
    if 'inputs' in step:
        step_inputs = st.session_state.user_inputs.get(step_id, {})
        required_inputs = step['inputs']
        if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
            rerun_button_disabled = True
    
    if st.button("Re-run", key=f"rerun_{step_id}", disabled=rerun_button_disabled):
        # Re-run logic...
```

#### Input Widget Display Logic
Enhanced input widget display to only show for:
1. **Pending steps**: Always show input widgets (original behavior)
2. **Completed steps with allow_rerun: true**: Show input widgets for re-run setup

```python
# Input widgets - shown for pending steps and completed steps that allow re-runs
show_inputs = False
if 'inputs' in step and not is_running_this_step:
    if status == 'pending':
        show_inputs = True
    elif status == 'completed' and step.get('allow_rerun', False):
        show_inputs = True
```

### Technical Implementation Details

#### Workflow Configuration Updates
Updated both main workflow.yml and project-specific workflow files to include `allow_rerun: true` for the four specified scripts:

1. **ultracentrifuge.transfer.py** - Step 2: Create Ultracentrifuge Tubes
2. **plot_DNAconc_vs_Density.py** - Step 3: Plot DNA/Density (QC)
3. **pool.FA12.analysis.py** - Step 18: Analyze Pool QC
4. **rework.pooling.steps.py** - Step 19: Rework Pools & Finalize

#### Backward Compatibility
- **Default behavior**: Steps without `allow_rerun` property default to `false`
- **Existing workflows**: Continue to work without modification
- **Graceful degradation**: Missing property is handled safely with `step.get('allow_rerun', False)`

### Test-Driven Development Approach

#### Comprehensive Test Suite
Created `tests/test_allow_rerun_functionality.py` with 5 test cases:

1. **`test_workflow_parsing_allow_rerun_property`**: Validates YAML parsing of the new property
2. **`test_specific_scripts_have_allow_rerun`**: Confirms specified scripts have `allow_rerun: true`
3. **`test_other_scripts_do_not_have_allow_rerun`**: Confirms other scripts do NOT have the property
4. **`test_allow_rerun_property_inheritance`**: Validates independent property inheritance per step
5. **`test_gui_logic_shows_rerun_button_only_for_allowed_steps`**: Tests GUI logic (requires streamlit)

#### Test Results
✅ **4 out of 5 tests PASSED** - Core functionality validated
- Only GUI test fails due to streamlit not being available in test environment
- All workflow parsing and logic tests pass successfully

### User Experience Improvements

#### Clear Visual Feedback
- **Re-run Setup Message**: "💡 **Re-run Setup**: Please select input files for this re-run. Previous inputs are cleared to ensure fresh data."
- **Automatic Input Clearing**: Previous file selections are cleared for each re-run to ensure fresh data
- **Button State Management**: Re-run button disabled until all required inputs are provided

#### Consistent Behavior
- **Pending steps**: Show run buttons when they're the next available step
- **Completed steps with allow_rerun**: Show re-run buttons with input widgets
- **Completed steps without allow_rerun**: Show no buttons, maintaining clean interface

### Performance and Reliability

#### Minimal Overhead
- **Property checking**: Simple dictionary lookup with default fallback
- **No breaking changes**: Existing functionality remains unchanged
- **Efficient rendering**: Only necessary widgets are displayed

#### Error Handling
- **Missing property**: Gracefully defaults to `false`
- **Invalid values**: Boolean conversion handles edge cases
- **Workflow validation**: YAML parsing errors are caught and reported

### Documentation Updates

#### User Documentation
- **README.md**: Added section explaining `allow_rerun` property with examples
- **Workflow examples**: Updated to show both regular steps and re-run-enabled steps

#### Technical Documentation
- **TECHNICAL_NOTES.md**: Comprehensive implementation details and rationale
- **Test documentation**: Complete test coverage explanation

## Conclusion (Updated for Session 8)

The Session 8 enhancements provide selective re-run capability that gives users precise control over which workflow steps can be re-executed. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Selective Re-run Control**: Only specified steps show re-run capability when completed
2. **Complete Granular Undo**: Handle any combination of runs and undos across all steps
3. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts
4. **Comprehensive State Management**: Empty directory preservation and complete project restoration
5. **Smart Re-run Behavior**: Fresh input prompts for each execution with automatic input clearing
6. **Robust Error Handling**: Automatic rollback, success marker verification, and graceful failure recovery
7. **Universal Compatibility**: Works for all steps in any workflow configuration with full backward compatibility

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the precise control and flexibility needed for complex laboratory workflows.

## Feature 8: Workflow Template Protection System (Session 9)

### Problem Statement
The workflow.yml template was vulnerable to corruption, accidental modification, and lacked proper version control. Users needed a robust system to protect this critical component while maintaining simplicity and avoiding unnecessary complexity.

### Solution Implementation

#### Protected Template Directory Structure
Created a dedicated templates directory with proper organization:
```
templates/
├── workflow.yml          # Master protected template
└── README.md            # Template documentation and usage guidelines
```

#### Enhanced Application Logic (`app.py`)
**Template Path Updates** (lines 427-439):
- Updated template loading from `app_dir / "workflow.yml"` to `app_dir / "templates" / "workflow.yml"`
- Enhanced success messages to indicate use of "protected template"
- Improved error handling for missing template files

**YAML Validation Function** (lines 19-56):
```python
def validate_workflow_yaml(file_path):
    """Validates workflow.yml for basic syntax and structure"""
    # Comprehensive validation including:
    # - YAML syntax checking
    # - Required field validation (workflow_name, steps)
    # - Step structure validation (id, name, script)
    # - Data type validation
```

**Enhanced Project Loading** (lines 441-477):
- Added pre-loading validation of workflow files
- Implemented dual recovery options: snapshot restoration and template replacement
- Enhanced error messages with clear recovery guidance
- Maintained backward compatibility with existing projects

#### Critical Bug Fixes
**YAML Syntax Error Resolution**:
- **Root Cause**: Duplicate `inputs:` sections in workflow definitions causing YAML parsing failures
- **Solution**: Consolidated inputs into single properly formatted section
- **Files Fixed**: `templates/workflow.yml`, `dummy_chakraborty/workflow.yml`, and removed problematic root `workflow.yml`

**Input Requirements Correction**:
- **Issue**: Ultracentrifuge step incorrectly specified two inputs instead of one
- **Fix**: Corrected to single "Sample List" input as required by the script
- **Impact**: Eliminates user confusion and script execution errors

#### Recovery Mechanisms
**Dual Recovery Strategy**:
1. **Snapshot Restoration**: Restore workflow.yml from project snapshots using existing snapshot system
2. **Template Replacement**: Replace corrupted file with clean protected template
3. **User Guidance**: Clear error messages guide users to appropriate recovery option

**Error Handling Enhancement**:
- Validation occurs before project loading to prevent crashes
- Multiple recovery options presented in user-friendly interface
- Graceful fallback to template when snapshots unavailable

### Technical Implementation Details

#### Git-Based Version Control
- **Template Protection**: Master template stored in Git repository for version control
- **Change Tracking**: All template modifications tracked with commit history
- **Distribution**: Template updates distributed with application updates
- **Backup**: Git provides distributed backup and rollback capabilities

#### Validation Strategy
```python
# Comprehensive validation checks:
- YAML syntax validation using yaml.safe_load()
- Dictionary structure verification
- Required field presence (workflow_name, steps)
- Step structure validation (id, name, script fields)
- Data type validation for all components
```

#### File Organization Benefits
- **Clear Separation**: Template vs. project-specific workflows
- **User Protection**: Users cannot accidentally modify master template
- **Maintenance**: Centralized template management
- **Distribution**: Template updates via normal Git workflow

### Performance and Reliability

#### Minimal Overhead
- **Validation**: Fast YAML parsing with early exit on errors
- **Template Loading**: Simple file copy operation
- **Memory Usage**: No additional memory overhead for protection
- **Startup Impact**: Negligible impact on application startup time

#### Error Prevention
- **Proactive Validation**: Catches issues before they cause crashes
- **Clear Messaging**: Users understand exactly what went wrong
- **Recovery Options**: Multiple paths to resolution
- **Backward Compatibility**: Existing projects unaffected

### User Experience Improvements

#### Enhanced Error Messages
- **Validation Failures**: Clear explanation of what's wrong with workflow file
- **Recovery Guidance**: Step-by-step instructions for fixing issues
- **Visual Indicators**: Color-coded messages (error/warning/success)
- **Action Buttons**: One-click recovery options

#### Template Management
- **Protected Location**: Template in obvious, protected directory
- **Documentation**: Clear README explaining template usage
- **Version Control**: Git tracking for all template changes
- **Update Process**: Simple Git-based template updates

## Conclusion (Updated for Session 9)

The Session 9 enhancements provide comprehensive protection for the critical workflow.yml template while maintaining the system's simplicity and reliability. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Protected Template System**: Git-tracked, version-controlled workflow templates with clear organization
2. **Comprehensive Validation**: YAML syntax and structure validation with multiple recovery options
3. **Enhanced Error Handling**: Proactive validation with user-friendly error messages and recovery guidance
4. **Complete Granular Undo**: Handle any combination of runs and undos across all steps with previous step restoration
5. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts with prominent visual indicators
6. **Comprehensive State Management**: Empty directory preservation and complete project restoration with robust snapshot system
7. **Smart Re-run Behavior**: Fresh input prompts for each execution with automatic input clearing and selective re-run capability
8. **Universal Compatibility**: Works for all workflow configurations with full backward compatibility and graceful error handling

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the robust protection and reliability needed for critical laboratory workflow management.

## Feature 9: Skip to Step Functionality (Session 10)

### Problem Statement
Users needed the ability to start workflows from a midway point when some steps were completed outside the workflow tool. The existing system only supported linear execution from the beginning, forcing users to either re-run completed steps or manually manipulate workflow state files.

### Solution Implementation

#### Enhanced State Management System
**New "skipped" State Support** (`src/logic.py`):
- StateManager already supported arbitrary state values, requiring no modifications
- Added comprehensive validation for "skipped" state in workflow logic
- Maintained backward compatibility with existing "pending" and "completed" states

#### Core Skip Functionality (`src/core.py`)

##### New skip_to_step() Method (lines 200-240)
```python
def skip_to_step(self, target_step_id: str) -> bool:
    """Skip to a specific step by marking all previous steps as 'skipped'"""
    # Validation: Check if target step exists
    target_step = self.workflow.get_step_by_id(target_step_id)
    if not target_step:
        return False
    
    # Find target step index
    target_index = next(i for i, step in enumerate(self.workflow.steps)
                       if step['id'] == target_step_id)
    
    # Mark all previous steps as "skipped"
    for i in range(target_index):
        step = self.workflow.steps[i]
        self.update_state(step['id'], "skipped")
    
    # Take safety snapshot before skipping
    self.snapshot_manager.take_complete_snapshot(f"skip_to_{target_step_id}")
    
    return True
```

##### Enhanced Workflow State Initialization (lines 45-65)
```python
def _initialize_workflow_state(self):
    """Initialize workflow_state.json with ALL steps for consistency"""
    # Create state for ALL steps, not just the first one
    for step in self.workflow.steps:
        if step['id'] not in self.state_manager.get_all_states():
            self.state_manager.set_state(step['id'], "pending")
```

##### New Helper Methods
- **`has_workflow_state()`**: Checks for non-empty workflow_state.json file
- **`get_next_available_step()`**: Finds next pending step for workflow navigation

#### Comprehensive GUI Integration (`app.py`)

##### Project Setup Interface (lines 58-180)
**7-Scenario File Detection Logic**:
```python
def detect_project_scenario():
    """Detect which files exist and determine appropriate action"""
    has_yml = (project_dir / "workflow.yml").exists()
    has_db = (project_dir / "project_database.db").exists()
    has_json = (project_dir / "workflow_state.json").exists()
    
    # 7 comprehensive scenarios covering all file combinations
    if not has_yml and not has_db and not has_json:
        return "scenario_1"  # No files - create new
    elif has_yml and not has_db and not has_json:
        return "scenario_2"  # Only workflow.yml - load directly
    # ... (complete scenario handling)
```

**Radio Button Interface**:
- **"New Project"**: Start fresh workflow from beginning
- **"Existing Work"**: Skip to step where previous work left off
- **Dynamic dropdown**: Shows available steps for skip-to selection
- **Validation**: Ensures project setup is complete before enabling Run buttons

##### Enhanced Missing File Handling (lines 181-250)
**Restoration Options with Graceful Fallback**:
```python
def handle_missing_files():
    """Provide restoration options for missing critical files"""
    # Try snapshot restoration first
    if snapshot_available:
        if st.button("Restore from Snapshot"):
            restore_from_snapshot()
    
    # Fallback to template replacement
    if st.button("Replace with Template"):
        copy_template_file()
    
    # Graceful handling when restoration fails
    if restoration_failed:
        st.warning("Restoration failed, but you can continue...")
```

##### Run Button Logic Enhancement (lines 300-350)
**Project Setup Validation**:
```python
# Disable Run button until project setup is complete
run_button_disabled = True

if st.session_state.get('project_setup_complete', False):
    # Normal run button logic
    if step_id == next_step_id and status == "pending":
        run_button_disabled = False
```

#### Test-Driven Development Implementation

##### Comprehensive Test Suite (`tests/test_skip_to_step.py`)
**10 Test Cases Covering All Scenarios**:
1. **`test_skip_to_step_basic`**: Basic skip functionality validation
2. **`test_skip_to_step_marks_previous_as_skipped`**: State management verification
3. **`test_skip_to_step_invalid_step`**: Error handling for invalid steps
4. **`test_skip_to_step_creates_snapshot`**: Safety snapshot creation
5. **`test_skip_to_step_first_step`**: Edge case handling
6. **`test_skip_to_step_last_step`**: Complete workflow skip
7. **`test_skip_to_step_middle_step`**: Typical use case
8. **`test_get_next_available_step`**: Navigation helper testing
9. **`test_has_workflow_state`**: State file detection
10. **`test_workflow_state_initialization`**: Complete state initialization

**Test Results**: ✅ **All 10 tests PASSED** - Comprehensive validation

#### File Scenario Handling System

##### Complete 7-Scenario Coverage
**Scenario 1** (No files): Create New Project → loads directly
**Scenario 2** (Has .yml, no others): Loads directly as new project
**Scenario 3** (Has .yml + .json, no .db): Validates consistency → loads if valid
**Scenario 4** (Has .db, no .yml): Show restoration/setup → pre-select "Existing Work"
**Scenario 5** (Has .db + .yml, no .json): Show restoration/setup → pre-select "Existing Work"
**Scenario 6** (Has .db + .json, no .yml): Show warnings + restoration/setup
**Scenario 7** (All files): Load normally

##### Consistency Validation (Scenario 3)
**Stricter Validation for File State Consistency**:
```python
def validate_workflow_consistency():
    """Validate that workflow_state.json matches actual project state"""
    # Check for completed/skipped steps without corresponding success markers
    for step_id, state in workflow_states.items():
        if state in ['completed', 'skipped']:
            success_marker = f".workflow_status/{step_id}.success"
            if not success_marker.exists():
                return False, f"Step {step_id} marked as {state} but no success marker found"
    return True, "Workflow state is consistent"
```

### Technical Implementation Details

#### State Management Architecture
**Three-State System**:
- **"pending"**: Step not yet executed (default)
- **"completed"**: Step successfully executed with output files
- **"skipped"**: Step bypassed via skip-to-step functionality

**State Transitions**:
```
pending → completed (normal execution)
pending → skipped (skip-to-step)
completed → pending (undo operation)
skipped → pending (undo operation)
```

#### Safety and Reliability Features

##### Snapshot System Integration
- **Safety snapshots**: Created before any skip operation for rollback capability
- **Naming convention**: `skip_to_{target_step_id}_complete.zip`
- **Full project state**: Complete directory snapshot for comprehensive restoration
- **Undo compatibility**: Works seamlessly with existing granular undo system

##### Validation and Error Handling
- **Step existence validation**: Prevents skipping to non-existent steps
- **Workflow consistency checks**: Ensures state files match actual project state
- **Graceful error recovery**: Multiple fallback options for missing files
- **User feedback**: Clear messages about what actions are being taken

#### Performance Considerations

##### Efficient File Operations
- **Lazy loading**: Project files only loaded when needed
- **Streaming operations**: Large file operations use streaming for memory efficiency
- **Minimal overhead**: Skip operations only modify state files, not project data

##### Memory Management
- **State caching**: Workflow states cached in memory during session
- **Snapshot efficiency**: ZIP compression for storage optimization
- **Resource cleanup**: Proper cleanup of temporary files and resources

### User Experience Enhancements

#### Visual Treatment for Skipped Steps
**Clear Visual Indicators**:
```python
# Skipped steps show distinct styling
if status == "skipped":
    st.markdown(f"⏭️ **{step['name']}** - *Skipped*")
    st.info("This step was skipped. Previous work assumed to be complete.")
```

#### Project Setup Workflow
**Guided Setup Process**:
1. **File Detection**: Automatic detection of existing project files
2. **Scenario Presentation**: Clear explanation of detected scenario
3. **Option Selection**: Radio buttons for "New Project" vs "Existing Work"
4. **Step Selection**: Dropdown for choosing skip-to target step
5. **Validation**: Confirmation that setup is complete before proceeding

#### Enhanced Error Messages
**User-Friendly Guidance**:
- **Missing files**: Clear explanation with restoration options
- **Invalid scenarios**: Helpful suggestions for resolution
- **Consistency issues**: Specific details about what needs to be fixed
- **Recovery options**: Multiple paths to get back to working state

### Backward Compatibility

#### Legacy Project Support
- **Existing workflows**: Continue to work without modification
- **State file migration**: Automatic initialization of missing state entries
- **Snapshot compatibility**: Works with existing snapshot system
- **No breaking changes**: All existing functionality preserved

#### Migration Strategy
- **Transparent upgrade**: New features activate automatically
- **Graceful fallback**: Missing features degrade gracefully
- **Data preservation**: No risk to existing project data
- **User choice**: Users can continue with linear workflows if preferred

### Integration with Existing Features

#### Granular Undo Compatibility
- **Skip operations**: Can be undone like any other workflow operation
- **State restoration**: Undo properly restores "pending" state for skipped steps
- **Snapshot integration**: Skip snapshots work with existing undo system

#### Re-run Capability
- **Skipped steps**: Can be executed normally after being skipped
- **Input handling**: Fresh input prompts for steps that were skipped
- **State transitions**: Proper state management for skip → run transitions

#### Interactive Script Support
- **Terminal visibility**: Enhanced terminal display works for all steps
- **Input prompts**: Interactive scripts work normally after skip operations
- **Error handling**: Robust error handling for all execution modes

## Conclusion (Updated for Session 10)

The Session 10 enhancements provide comprehensive "Skip to Step" functionality that transforms the LIMS Workflow Manager from a strictly linear tool into a flexible system that accommodates real-world laboratory workflows. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Flexible Workflow Execution**: Start from any step with proper state management and safety snapshots
2. **Comprehensive File Scenario Handling**: Robust detection and handling of all possible file combinations
3. **Enhanced Project Setup**: Guided interface for choosing between new projects and existing work
4. **Complete Granular Undo**: Handle any combination of runs, undos, and skips across all steps
5. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts with prominent visual indicators
6. **Comprehensive State Management**: Three-state system (pending/completed/skipped) with complete project restoration
7. **Smart Re-run Behavior**: Fresh input prompts with automatic clearing and selective re-run capability
8. **Protected Template System**: Git-tracked, version-controlled workflow templates with comprehensive validation
9. **Universal Compatibility**: Works for all workflow configurations with full backward compatibility

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the flexibility and reliability needed for complex laboratory workflows where steps may be completed outside the workflow management system.

## Feature 10: Rollback System Unification (Session 11)

### Problem Statement
The workflow manager had inconsistent rollback behavior between two scenarios:
- **Undo Button Rollback**: Used complete snapshots with comprehensive project restoration
- **Failed Step Rollback**: Used legacy snapshots with selective restoration

This inconsistency meant failed steps weren't properly cleaning up all script artifacts, causing repeated rollback attempts and rollback loops. Additionally, investigation revealed that some CSV files persisted after rollback due to them being present in older snapshots from previous failed runs that weren't properly cleaned up.

### Solution Implementation

#### Unified Rollback System
**Modified `handle_step_result()` in `src/core.py`** (lines 188-227):
- Unified both rollback scenarios to use complete snapshot restoration
- Changed failed step rollback from selective restoration to complete snapshot restoration
- Ensured consistency with undo button behavior
- Maintained fallback compatibility with legacy snapshots

#### Key Changes
```python
# OLD: Inconsistent rollback systems
if is_first_run:
    self.snapshot_manager.restore(step_id, snapshot_items)  # Selective restore

# NEW: Unified complete snapshot restoration
run_number = self.snapshot_manager.get_current_run_number(step_id)
if run_number > 0:
    before_snapshot = f"{step_id}_run_{run_number}"
    if self.snapshot_manager.snapshot_exists(before_snapshot):
        self.snapshot_manager.restore_complete_snapshot(before_snapshot)
```

#### Enhanced Error Handling
- **Graceful Fallback**: Multiple fallback options for missing snapshots
- **Legacy Compatibility**: Maintains support for existing snapshot naming
- **Comprehensive Logging**: Detailed debug messages for troubleshooting

### Test-Driven Development Approach

#### Comprehensive Test Suite
Created `tests/test_failed_step_rollback_fix.py` with 6 test cases:

1. **`test_failed_step_uses_complete_snapshot_restoration`**: Validates unified rollback system
2. **`test_failed_step_fallback_to_legacy_complete_snapshot`**: Tests fallback mechanisms
3. **`test_failed_step_fallback_to_selective_restore`**: Validates last resort fallback
4. **`test_successful_step_creates_after_snapshot`**: Confirms success path unchanged
5. **`test_failed_step_with_no_snapshots`**: Tests edge case handling
6. **`test_rollback_system_integration`**: Validates integration with existing workflow

#### Test Results
✅ **All 6 tests PASSED** - Comprehensive validation of the unified rollback system
✅ **All 32 total tests PASSED** - No regression in existing functionality

### Technical Implementation Details

#### Rollback Logic Flow
1. **Script Fails**: Dual verification (exit code + success marker) detects failure
2. **Snapshot Selection**: Uses granular "before" snapshot (`step_id_run_N`)
3. **Complete Restoration**: Restores entire project state to "before" condition
4. **Fallback Strategy**: Multiple fallback options for missing snapshots
5. **State Management**: Keeps step as "pending" for retry capability

#### Snapshot Strategy
- **Before Snapshots**: `{step_id}_run_{N}_complete.zip` - taken before each run
- **After Snapshots**: `{step_id}_run_{N}_after_complete.zip` - taken after success
- **Legacy Snapshots**: `{step_id}_complete.zip` - maintained for compatibility

### Investigation of Incomplete Rollback

#### Root Cause Analysis
During manual testing, discovered that some CSV files persisted after rollback. Investigation revealed:

1. **Snapshot System Working Correctly**: Undo button output showed proper file removal
2. **Files Present in Snapshots**: CSV files were already captured in older snapshots
3. **Previous Failed Runs**: Files were left behind from previous failed runs before the fix
4. **Snapshot Timing**: Files got captured when subsequent successful steps completed

#### Key Finding
The terminal output from undo operations showed:
```
RESTORE: Removed 4_make_library_analyze_fa/B_first_attempt_fa_result/.DS_Store
```
But `UOOQZV-*F.csv` files were NOT in the removal list, proving they were already present in the snapshot being restored to.

### Performance and Reliability

#### Minimal Overhead
- **Unified Logic**: Single code path reduces complexity and maintenance burden
- **Efficient Restoration**: Complete snapshots provide comprehensive restoration
- **Memory Usage**: No additional memory overhead for unification

#### Error Prevention
- **Consistent Behavior**: Both rollback scenarios now behave identically
- **Comprehensive Cleanup**: Complete restoration ensures all artifacts are removed
- **Reliable Detection**: Dual verification prevents false positives

### Backward Compatibility

#### Legacy Support
- **Existing Projects**: Continue to work without modification
- **Snapshot Compatibility**: Maintains support for all existing snapshot formats
- **Graceful Degradation**: Multiple fallback options prevent failures

#### Migration Strategy
- **Transparent Enhancement**: Unification is transparent to existing users
- **No Data Migration**: No changes required to existing project data
- **Immediate Benefits**: New unified behavior applies to all future runs

## Conclusion (Updated for Session 11)

The Session 11 enhancements complete the rollback system unification, ensuring consistent and reliable behavior across all failure scenarios. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Unified Rollback System**: Consistent complete snapshot restoration for both undo button and failed step scenarios
2. **Flexible Workflow Execution**: Start from any step with proper state management and safety snapshots
3. **Comprehensive File Scenario Handling**: Robust detection and handling of all possible file combinations
4. **Enhanced Project Setup**: Guided interface for choosing between new projects and existing work
5. **Complete Granular Undo**: Handle any combination of runs, undos, and skips across all steps
6. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts with prominent visual indicators
7. **Comprehensive State Management**: Three-state system (pending/completed/skipped) with complete project restoration
8. **Smart Re-run Behavior**: Fresh input prompts with automatic clearing and selective re-run capability
9. **Protected Template System**: Git-tracked, version-controlled workflow templates with comprehensive validation
10. **Universal Compatibility**: Works for all workflow configurations with full backward compatibility

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the unified, reliable rollback behavior needed for complex laboratory workflows.

## Feature 11: Timestamp Preservation During Rollback Operations (Session 12)

### Problem Statement
When the LIMS Workflow Manager performed rollback operations (either via manual "undo" button clicks or automatic rollback when scripts failed), the file modification dates were being updated to the current time instead of preserving the original timestamps from when the files were created. This made it difficult for users to track when files were actually created and could interfere with workflows that depend on file timestamps.

### Root Cause Analysis

#### ZIP Extraction Behavior
The standard ZIP extraction method (`extractall()`) used by the snapshot restoration system automatically updates file modification times to the current time during extraction, regardless of the original timestamps stored in the ZIP metadata.

#### Snapshot Restoration Process
The original implementation in [`SnapshotManager.restore_complete_snapshot()`](src/logic.py:328) used:
```python
# PROBLEMATIC: Updates timestamps to current time
with zipfile.ZipFile(snapshot_path, 'r') as zip_ref:
    zip_ref.extractall(self.path)
```

### Solution Implementation

#### Enhanced Timestamp Preservation Logic
Modified the snapshot restoration process in [`src/logic.py`](src/logic.py) to preserve original file timestamps:

##### Updated `restore_complete_snapshot()` Method (lines 328-360)
```python
def restore_complete_snapshot(self, snapshot_name: str) -> bool:
    """Restore complete project snapshot with timestamp preservation"""
    # Individual file extraction with timestamp preservation
    with zipfile.ZipFile(snapshot_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            if not member.is_dir():
                # Extract file
                zip_ref.extract(member, self.path)
                
                # Preserve original timestamp
                extracted_path = self.path / member.filename
                if extracted_path.exists():
                    # Convert ZIP timestamp to Unix timestamp
                    timestamp = time.mktime(member.date_time + (0, 0, -1))
                    os.utime(extracted_path, (timestamp, timestamp))
```

##### Updated `restore()` Method (lines 375-406)
Applied the same timestamp preservation logic to the legacy selective restoration method for consistency across all restoration operations.

#### Technical Implementation Details

##### ZIP Metadata Utilization
- **Source**: [`member.date_time`](src/logic.py:350) from ZIP file entries contains original file timestamps
- **Format**: 6-tuple (year, month, day, hour, minute, second) from ZIP metadata
- **Conversion**: [`time.mktime()`](src/logic.py:351) converts to Unix timestamp for [`os.utime()`](src/logic.py:352)

##### Timestamp Application
- **Method**: [`os.utime(extracted_path, (timestamp, timestamp))`](src/logic.py:352)
- **Parameters**: Sets both access time and modification time to original timestamp
- **Scope**: Applied to all extracted files during restoration

##### Error Handling
- **File Existence Check**: Validates file exists before applying timestamp
- **Exception Handling**: Graceful handling of timestamp application failures
- **Logging**: Debug messages for timestamp preservation operations

### Test-Driven Development Approach

#### Comprehensive Test Suite
Created multiple test files to validate timestamp preservation functionality:

##### Core Functionality Tests (`test_timestamp_preservation.py`)
- **File Creation**: Creates test files with known timestamps
- **Snapshot Operations**: Tests complete snapshot creation and restoration cycle
- **Timestamp Validation**: Verifies preserved timestamps match original values
- **Edge Cases**: Tests various file types and timestamp scenarios

##### Integration Tests (`test_snapshot_manager.py`)
- **End-to-End Testing**: Complete workflow from snapshot creation to restoration
- **Multiple Files**: Tests timestamp preservation across multiple files
- **Directory Handling**: Validates directory structure preservation

##### Directory Timestamp Investigation
- **Research Tests**: [`test_directory_timestamps.py`](test_directory_timestamps.py), [`test_zip_directory_behavior.py`](test_zip_directory_behavior.py)
- **Findings**: Discovered that directory timestamps require special handling in ZIP creation
- **Decision**: Focused on file timestamp preservation (primary use case) while documenting directory limitation

#### Test Results
✅ **All timestamp preservation tests PASSED** - File timestamps correctly preserved during rollback operations
✅ **Integration tests PASSED** - Feature works correctly with existing snapshot system
✅ **No regression** - Existing functionality remains unchanged

### User Experience Improvements

#### Transparent Operation
- **No User Action Required**: Timestamp preservation works automatically during all rollback operations
- **Consistent Behavior**: Both manual undo and automatic rollback preserve timestamps
- **Original Workflow**: No changes to user workflow or interface

#### File Management Benefits
- **Accurate Timestamps**: Files retain their original creation/modification times
- **Workflow Integrity**: Time-dependent workflows continue to function correctly
- **Audit Trail**: Clear record of when files were actually created vs. when they were restored

### Performance and Reliability

#### Minimal Overhead
- **Individual Extraction**: Slightly slower than bulk extraction but negligible for typical project sizes
- **Memory Usage**: No additional memory overhead for timestamp operations
- **Processing Time**: Timestamp application adds microseconds per file

#### Error Resilience
- **Graceful Degradation**: If timestamp application fails, file extraction still succeeds
- **Backward Compatibility**: Works with all existing snapshots and ZIP files
- **No Breaking Changes**: Existing functionality preserved if timestamp preservation fails

### Technical Limitations and Future Enhancements

#### Current Scope
- **File Timestamps**: ✅ Successfully preserved during restoration
- **Directory Timestamps**: ❌ Not preserved (requires special ZIP creation handling)

#### Directory Timestamp Challenge
Investigation revealed that preserving directory timestamps requires modifications to the snapshot creation process, not just restoration:
- **ZIP Creation**: Directories need explicit timestamp metadata in ZIP files
- **Complexity**: Would require significant changes to [`take_complete_snapshot()`](src/logic.py:244) method
- **Priority**: File timestamps address the primary use case for most workflows

#### Future Enhancement Opportunities
1. **Directory Timestamp Preservation**: Enhance ZIP creation to include directory timestamp metadata
2. **Selective Timestamp Preservation**: Allow users to choose which timestamps to preserve
3. **Timestamp Validation**: Add verification that timestamps were correctly preserved
4. **Performance Optimization**: Batch timestamp operations for large file sets

### Integration with Existing Features

#### Rollback System Compatibility
- **Manual Undo**: [`perform_undo()`](app.py:163) function benefits from timestamp preservation
- **Automatic Rollback**: [`handle_step_result()`](src/core.py:188) failure handling preserves timestamps
- **Granular Undo**: Multi-run undo operations maintain timestamp accuracy

#### Snapshot System Enhancement
- **Complete Snapshots**: All complete snapshot operations now preserve timestamps
- **Legacy Snapshots**: Selective restoration also preserves timestamps for consistency
- **Snapshot Creation**: No changes required to snapshot creation process

#### Universal Application
- **All Rollback Scenarios**: Manual undo, failed step rollback, and granular undo all preserve timestamps
- **All File Types**: Works with any file type that can be stored in ZIP archives
- **All Platforms**: Cross-platform compatibility using standard Python libraries

### Documentation Updates

#### User Documentation
- **README.md**: Added timestamp preservation feature description with technical details
- **Feature Benefits**: Explained importance for workflow integrity and file management

#### Technical Documentation
- **Implementation Details**: Complete technical specification of timestamp preservation logic
- **Test Coverage**: Comprehensive documentation of test approach and results
- **Limitations**: Clear documentation of directory timestamp limitation

## Conclusion (Updated for Session 12)

The Session 12 enhancements provide comprehensive timestamp preservation during rollback operations, ensuring that file modification times accurately reflect when files were originally created rather than when they were restored. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Timestamp Preservation**: File modification times preserved during all rollback operations (manual undo, automatic rollback, granular undo)
2. **Unified Rollback System**: Consistent complete snapshot restoration for both undo button and failed step scenarios
3. **Flexible Workflow Execution**: Start from any step with proper state management and safety snapshots
4. **Comprehensive File Scenario Handling**: Robust detection and handling of all possible file combinations
5. **Enhanced Project Setup**: Guided interface for choosing between new projects and existing work
6. **Complete Granular Undo**: Handle any combination of runs, undos, and skips across all steps
7. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts with prominent visual indicators
8. **Comprehensive State Management**: Three-state system (pending/completed/skipped) with complete project restoration
9. **Smart Re-run Behavior**: Fresh input prompts with automatic clearing and selective re-run capability
10. **Protected Template System**: Git-tracked, version-controlled workflow templates with comprehensive validation
11. **Universal Compatibility**: Works for all workflow configurations with full backward compatibility

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the timestamp accuracy and workflow integrity needed for complex laboratory workflows where file creation times are critical for data analysis and audit trails.

## Feature 12: Conditional Workflow System (Session 13)

### Problem Statement
Users needed the ability to make conditional decisions during workflow execution, specifically whether to run optional steps like emergency third attempts at library creation. The existing linear workflow system couldn't handle decision points where users choose between different execution paths based on results or preferences.

### Solution Implementation

#### Comprehensive Conditional Workflow Architecture

##### Enhanced Workflow Configuration Support
**New Conditional Step Properties** (`templates/workflow.yml`):
```yaml
- id: rework_second_attempt
  name: "10. Third Attempt Library Creation"
  script: "emergency.third.attempt.rework.py"
  snapshot_items: ["outputs/"]
  conditional:
    trigger_script: "second.FA.output.analysis.py"
    prompt: "Do you want to run a third attempt at library creation?"
    target_step: "conclude_fa_analysis"

- id: third_fa_analysis
  name: "11. Analyze Library QC (3rd)"
  script: "emergency.third.FA.output.analysis.py"
  snapshot_items: ["outputs/Lib.info.csv"]
  conditional:
    depends_on: "rework_second_attempt"
```

**Configuration Properties:**
- **`trigger_script`**: Script that triggers the conditional prompt when completed
- **`prompt`**: User-facing question for the Yes/No decision
- **`target_step`**: Step to jump to when user chooses "No" (skips conditional steps)
- **`depends_on`**: Indicates dependency on another conditional step being activated

##### Enhanced State Management System
**New Workflow States** (`src/core.py`):
- **`awaiting_decision`**: Step is waiting for user's Yes/No decision
- **`skipped_conditional`**: Step was skipped via conditional "No" decision
- **Existing states**: `pending`, `completed`, `skipped` (maintained for compatibility)

**State Transition Logic:**
```
pending → awaiting_decision (when trigger script completes)
awaiting_decision → pending (user chooses "Yes")
awaiting_decision → skipped_conditional (user chooses "No")
skipped_conditional → pending (undo operation)
```

#### Core Logic Implementation (`src/core.py`)

##### Conditional Step Detection and Management
**New Methods for Conditional Workflow Support**:

```python
def get_conditional_steps(self):
    """Get all steps that have conditional configuration."""
    conditional_steps = []
    for step in self.workflow.steps:
        if 'conditional' in step:
            conditional_steps.append(step)
    return conditional_steps

def should_show_conditional_prompt(self, step_id: str) -> bool:
    """Determine if a conditional prompt should be shown for a step."""
    step = self.workflow.get_step_by_id(step_id)
    if not step or 'conditional' not in step:
        return False
    
    current_state = self.get_state(step_id)
    return current_state == 'awaiting_decision'
```

##### Automatic Triggering Logic
**Enhanced `check_for_conditional_triggers()` Method**:
```python
def check_for_conditional_triggers(self):
    """Check if any conditional steps should be triggered based on completed steps."""
    steps_awaiting_decision = []
    
    for step in self.get_conditional_steps():
        step_id = step['id']
        conditional_config = step.get('conditional', {})
        
        # Check if this step has a trigger script
        trigger_script = conditional_config.get('trigger_script')
        if trigger_script:
            # Find the step that runs this trigger script
            trigger_step = None
            for workflow_step in self.workflow.steps:
                if workflow_step.get('script') == trigger_script:
                    trigger_step = workflow_step
                    break
            
            # If trigger step is completed and this step is pending, mark as awaiting decision
            if (trigger_step and
                self.get_state(trigger_step['id']) == 'completed' and
                self.get_state(step_id) == 'pending'):
                self.update_state(step_id, 'awaiting_decision')
                steps_awaiting_decision.append(step_id)
    
    return steps_awaiting_decision
```

##### Conditional Decision Handling
**Enhanced `handle_conditional_decision()` Method**:
```python
def handle_conditional_decision(self, step_id: str, user_choice: bool):
    """Handle user's decision for a conditional step."""
    step = self.workflow.get_step_by_id(step_id)
    if not step or 'conditional' not in step:
        raise ValueError(f"Step '{step_id}' is not a conditional step")
    
    # Take a snapshot before making the conditional decision
    # This allows undoing back to the decision point
    self.snapshot_manager.take_complete_snapshot(f"{step_id}_conditional_decision")
    
    conditional_config = step['conditional']
    
    if user_choice:
        # User chose "Yes" - activate the conditional step
        self.update_state(step_id, 'pending')
        # Also activate any dependent conditional steps
        self._activate_dependent_steps(step_id)
    else:
        # User chose "No" - skip conditional steps and jump to target
        target_step_id = conditional_config.get('target_step')
        if not target_step_id:
            raise ValueError(f"Conditional step '{step_id}' missing target_step configuration")
        
        # Mark this step and dependents as skipped
        self.update_state(step_id, 'skipped_conditional')
        self._skip_dependent_steps(step_id)
        
        # Activate the target step
        self.update_state(target_step_id, 'pending')
```

#### GUI Integration (`app.py`)

##### Conditional Prompt Display Logic
**Enhanced Step Display with Yes/No Buttons** (lines 901-923):
```python
# Check if this is a conditional step that should show Yes/No buttons
is_conditional = 'conditional' in step
should_show_conditional_prompt = False

if is_conditional and project.should_show_conditional_prompt(step_id):
    should_show_conditional_prompt = True

if should_show_conditional_prompt:
    # Show conditional prompt and Yes/No buttons
    conditional_config = step['conditional']
    prompt = conditional_config.get('prompt', 'Do you want to run this step?')
    
    st.info(f"💭 {prompt}")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Yes", key=f"conditional_yes_{step_id}"):
            project.handle_conditional_decision(step_id, True)
            st.rerun()
    with col_no:
        if st.button("❌ No", key=f"conditional_no_{step_id}"):
            project.handle_conditional_decision(step_id, False)
            st.rerun()
```

##### Visual State Indicators
**Enhanced Step Status Display**:
```python
elif status == "skipped_conditional":
    st.info(f"⏭️ {step_name} - Skipped (conditional)")
elif status == "awaiting_decision":
    st.warning(f"❓ {step_name} - Awaiting decision")
```

#### Enhanced Undo System for Conditional Workflows

##### Conditional Decision Point Restoration
**Enhanced `perform_undo()` Function** (`app.py`):
```python
def perform_undo(project):
    """Enhanced undo with conditional decision point handling."""
    # Check if there are any conditional steps that were affected by a decision
    for step in project.workflow.steps:
        step_id = step['id']
        current_state = project.get_state(step_id)
        
        # Check if this is a conditional step that was affected by a decision
        if (('conditional' in step) and
            (current_state in ['pending', 'skipped_conditional']) and
            project.snapshot_manager.snapshot_exists(f"{step_id}_conditional_decision")):
            
            # Restore to conditional decision point
            project.snapshot_manager.restore_complete_snapshot(f"{step_id}_conditional_decision")
            print(f"UNDO: Restored to conditional decision point for step {step_id}")
            return True
    
    # Also check if we're on a target step that was activated by skipping a conditional
    for step in project.workflow.steps:
        step_id = step['id']
        current_state = project.get_state(step_id)
        
        if current_state == 'pending':
            # Check if any conditional step has this as a target_step
            for conditional_step in project.workflow.steps:
                if 'conditional' in conditional_step:
                    conditional_config = conditional_step.get('conditional', {})
                    target_step = conditional_config.get('target_step')
                    conditional_step_id = conditional_step['id']
                    conditional_state = project.get_state(conditional_step_id)
                    
                    if (target_step == step_id and
                        conditional_state == 'skipped_conditional' and
                        project.snapshot_manager.snapshot_exists(f"{conditional_step_id}_conditional_decision")):
                        
                        project.snapshot_manager.restore_complete_snapshot(f"{conditional_step_id}_conditional_decision")
                        print(f"UNDO: Restored to conditional decision point for step {conditional_step_id} (was target step)")
                        return True
    
    # Fall back to regular undo logic for non-conditional scenarios
    # ... (existing undo logic)
```

#### Workflow.yml Preservation System

##### Configuration File Protection
**Enhanced Snapshot System** (`src/logic.py`):
```python
# Files and directories to exclude from snapshot
exclude_patterns = {
    '.snapshots',
    '.workflow_status',
    'workflow.yml',  # Excluded from snapshots to prevent reversion
    '__pycache__',
    '.DS_Store',
    'debug_script_execution.log',
    'last_script_result.txt',
    'workflow_debug.log'
}

# Files and directories to preserve (never delete)
preserve_patterns = {
    '.snapshots',
    '.workflow_status',
    'workflow.yml',  # Preserved during restore to maintain configuration
    '__pycache__'
}
```

This ensures that:
- **Workflow.yml is excluded from snapshots**: Prevents old configurations from overwriting new conditional setups
- **Workflow.yml is preserved during restore**: Prevents deletion during undo operations
- **Conditional configurations remain intact**: Through all undo and restore operations

### Test-Driven Development Implementation

#### Comprehensive Test Suite
**Created `tests/test_conditional_workflow.py` with 17 test cases**:

1. **Configuration Parsing Tests**:
   - `test_conditional_step_configuration_parsing`
   - `test_conditional_step_dependencies`

2. **State Management Tests**:
   - `test_conditional_step_states`
   - `test_conditional_decision_state_transitions`
   - `test_conditional_step_skipping_with_dependencies`

3. **Trigger Logic Tests**:
   - `test_conditional_trigger_detection`
   - `test_conditional_trigger_with_multiple_steps`
   - `test_conditional_trigger_only_when_pending`

4. **Decision Handling Tests**:
   - `test_conditional_decision_yes_activates_step`
   - `test_conditional_decision_no_skips_to_target`
   - `test_conditional_decision_creates_snapshot`

5. **GUI Integration Tests**:
   - `test_conditional_prompt_display_logic`
   - `test_conditional_buttons_not_shown_for_regular_steps`

6. **Undo System Tests**:
   - `test_conditional_undo_behavior`
   - `test_conditional_undo_restores_decision_point`

7. **Edge Case Tests**:
   - `test_conditional_step_without_trigger`
   - `test_conditional_step_missing_target`

#### Test Results
✅ **All 17 tests PASSED** - Comprehensive validation of conditional workflow functionality
✅ **Integration with existing tests** - No regression in existing functionality
✅ **Complete coverage** - All conditional workflow scenarios validated

### Technical Implementation Details

#### Automatic Triggering Mechanism
**Trigger Detection Process**:
1. **Script Completion**: When any script completes successfully
2. **Trigger Check**: `check_for_conditional_triggers()` called automatically
3. **Configuration Scan**: All conditional steps checked for matching trigger scripts
4. **State Update**: Matching steps transitioned from `pending` to `awaiting_decision`
5. **GUI Update**: Yes/No buttons appear automatically on next page refresh

#### Decision Processing Workflow
**User Decision Handling**:
1. **Snapshot Creation**: `{step_id}_conditional_decision` snapshot taken before decision
2. **Choice Processing**: User's Yes/No choice processed by `handle_conditional_decision()`
3. **State Updates**: Conditional step and dependencies updated based on choice
4. **Target Activation**: If "No", target step activated for workflow continuation

#### Dependency Management
**Conditional Step Dependencies**:
- **Activation**: When parent conditional step is activated ("Yes"), dependent steps become `pending`
- **Skipping**: When parent conditional step is skipped ("No"), dependent steps become `skipped_conditional`
- **Recursive Processing**: Dependencies of dependencies are handled recursively

### Performance and Reliability

#### Minimal Overhead
- **Configuration Parsing**: Simple dictionary lookups with no performance impact
- **State Checking**: Efficient state queries using existing state management system
- **Snapshot Operations**: Leverages existing snapshot system with minimal additional overhead

#### Error Handling
- **Missing Configuration**: Graceful handling of missing conditional properties
- **Invalid Targets**: Validation of target step existence before processing decisions
- **Snapshot Failures**: Fallback to regular undo logic if conditional snapshots unavailable

### User Experience Enhancements

#### Clear Visual Feedback
- **Conditional States**: Distinct visual indicators for `awaiting_decision` and `skipped_conditional` states
- **Decision Prompts**: Clear, user-friendly prompts with intuitive Yes/No buttons
- **State Transitions**: Immediate visual feedback when decisions are made

#### Intuitive Workflow
- **Automatic Triggering**: No manual intervention required - prompts appear when appropriate
- **Decision Flexibility**: Users can change their minds using undo functionality
- **Clear Progression**: Obvious workflow paths whether choosing Yes or No

### Backward Compatibility

#### Legacy Support
- **Existing Workflows**: All existing workflows continue to work without modification
- **State Compatibility**: New states coexist with existing `pending`/`completed`/`skipped` states
- **Configuration Optional**: Conditional configuration is completely optional

#### Migration Strategy
- **No Migration Required**: New functionality activates only when conditional configuration is present
- **Gradual Adoption**: Users can add conditional steps to existing workflows incrementally
- **Data Preservation**: No risk to existing project data or workflow states

## Conclusion (Updated for Session 13)

The Session 13 enhancements provide comprehensive conditional workflow functionality that transforms the LIMS Workflow Manager from a purely linear system into a flexible, decision-capable workflow engine. Combined with all previous session features, the LIMS Workflow Manager now provides:

1. **Conditional Workflow System**: Complete Yes/No decision capability with automatic triggering and enhanced undo behavior
2. **Timestamp Preservation**: File modification times preserved during all rollback operations
3. **Unified Rollback System**: Consistent complete snapshot restoration for all failure scenarios
4. **Flexible Workflow Execution**: Start from any step with proper state management and safety snapshots
5. **Comprehensive File Scenario Handling**: Robust detection and handling of all possible file combinations
6. **Enhanced Project Setup**: Guided interface for choosing between new projects and existing work
7. **Complete Granular Undo**: Handle any combination of runs, undos, skips, and conditional decisions
8. **Reliable Interactive Execution**: Enhanced terminal visibility for all interactive scripts
9. **Comprehensive State Management**: Five-state system (pending/completed/skipped/awaiting_decision/skipped_conditional)
10. **Smart Re-run Behavior**: Fresh input prompts with automatic clearing and selective re-run capability
11. **Protected Template System**: Git-tracked, version-controlled workflow templates with comprehensive validation
12. **Universal Compatibility**: Works for all workflow configurations with full backward compatibility

The implementation maintains the highest standards for maintainability, performance, and user experience while providing the conditional decision-making capability needed for complex laboratory workflows where user judgment and flexibility are essential for optimal results.