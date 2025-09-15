# Project Summary: LIMS Workflow Manager (v3)

## 1. Project Goal
To create a simple, lightweight, cross-platform GUI application to manage and execute a series of Python-based laboratory workflow scripts, with robust error handling and version control for the scripts.

## 2. Current Status
- **Phase 1 (Core Engine):** Complete. All logic for parsing, state management, snapshots, and script execution is implemented and tested. Success marker system implemented for reliable rollback functionality.
- **Phase 2 (GUI):** Complete. The Streamlit UI is fully featured with interactive script execution, enhanced failure detection, smart re-run behavior, and comprehensive undo functionality.
- **Phase 3 (Distribution):** Complete. The script-based distribution model using Git is implemented and tested on macOS. Awaiting final Windows test.
- **Phase 4 (Workflow Implementation):** Complete. The production `workflow.yml` and user `README.md` are authored. All 19 workflow scripts updated with success markers.
- **Phase 5 (Rollback & Reliability):** Complete. Critical rollback functionality fixed with success marker implementation.
- **Phase 6 (Enhanced GUI Features):** Complete. Smart re-run file input behavior and comprehensive undo functionality with complete project state restoration.
- **Phase 7 (Pseudo-Terminal Bug Fixes):** Complete. Resolved critical pseudo-terminal display issues and enhanced terminal visibility for all interactive scripts.
- **Phase 8 (Granular Undo System):** Complete. Implemented comprehensive granular undo for individual step re-runs with unlimited re-run support and intelligent step status management.
- **Phase 9 (Enhanced Undo with Previous Step Restoration):** Complete. Fixed critical gap in granular undo system to handle previous step restoration when no current step "after" snapshots exist.
- **Phase 10 (Workflow Template Protection System):** Complete. Implemented comprehensive protection for workflow.yml templates with Git-based version control, YAML validation, and multiple recovery mechanisms.
- **Phase 11 (Skip to Step Functionality):** Complete. Implemented comprehensive "Skip to Step" feature allowing users to start workflows from any midway point with proper state management and safety snapshots.

## 3. Key Design Decisions
- **Core Engine:** A generic engine that reads workflow definitions from a `workflow.yml` file.
- **State Management:** Workflow progress is tracked in a `workflow_state.json` file, supporting "pending", "completed", and "skipped" states.
- **Undo/Redo:** Implemented via a snapshot mechanism.
- **Error Handling:** The engine automatically restores the pre-run snapshot if any script fails. Enhanced with success marker files for reliable failure detection.
- **Script Management (Centralized Git Repository):**
    - The application's workflow scripts are managed in a central, private Git repository and cloned into a local `scripts` folder during setup.
- **Distribution Model:** The application is distributed as a folder. A one-time `setup` script prepares the environment. A `run` script launches the app.

## 4. Recent Major Accomplishments
1. **Critical Rollback Bug Fix**: Resolved issue where failed scripts were incorrectly marked as "completed" instead of triggering rollback.
2. **Success Marker System**: Implemented reliable failure detection using `.workflow_status/{script_name}.success` files.
3. **Script Updates**: All 19 workflow scripts updated with success marker functionality.
4. **Configuration Fixes**: Corrected script name mismatches in workflow.yml files.
5. **Interactive Functionality**: Restored proper interactive script execution while maintaining enhanced failure detection.
6. **Enhanced Re-run Behavior**: Implemented smart re-run functionality that always prompts for new file inputs, preventing accidental reuse of old data.
7. **Complete Undo System**: Implemented comprehensive undo functionality with complete project state restoration using enhanced snapshot system.
8. **Success Marker Bug Fixes**: Fixed naming convention issues across all 19 workflow scripts for reliable completion detection.
9. **Pseudo-Terminal Bug Resolution**: Systematically debugged and fixed critical pseudo-terminal display issues for ultracentrifuge script.
10. **Enhanced Terminal Visibility**: Implemented prominent visual indicators to make interactive terminals impossible to miss.
11. **Granular Undo System**: Implemented comprehensive granular undo for individual step re-runs with unlimited re-run support.
12. **Intelligent Step Status Management**: Enhanced step status to accurately reflect completion state across multiple re-runs.
13. **Progressive Undo Logic**: Each undo operation targets exactly one run, not entire steps, with proper snapshot tracking.
14. **Enhanced Undo with Previous Step Restoration**: Fixed critical gap where undo would fail silently when no current step "after" snapshots existed, now properly restores to previous step's state.
15. **Backwards Search Algorithm**: Implemented robust backwards search to handle gaps in "after" snapshots created by previous undo operations.
16. **Workflow Template Protection System**: Implemented comprehensive protection for critical workflow.yml templates with dedicated templates directory, Git version control, and YAML validation.
17. **Critical YAML Bug Fix**: Resolved duplicate inputs sections causing parsing failures and corrected ultracentrifuge step input requirements.
18. **Enhanced Error Handling**: Added proactive workflow validation with multiple recovery options including snapshot restoration and template replacement.
19. **Skip to Step Functionality**: Implemented comprehensive workflow entry point selection allowing users to start from any step when previous work was completed outside the tool.
20. **7-Scenario File Handling**: Robust detection and handling of all possible project file combinations with guided setup interface.
21. **Enhanced Project Setup**: Radio button interface for choosing between "New Project" and "Existing Work" with dynamic step selection dropdown.

## 5. Next Steps (Optional Enhancements)
1. **Enhanced Logging**: Improve GUI feedback and real-time information display.
2. **Script Update Mechanism**: Enhance reliability and user experience of script updates.
3. **Workflow Validation**: Implement validation for `workflow.yml` file syntax and structure.
4. **Comprehensive Testing**: Perform full end-to-end testing on both macOS and Windows platforms.

## 6. Latest Features (Session 4)
### Enhanced Re-run File Input Behavior
- **Problem Solved**: Re-runs now always prompt for new file inputs instead of reusing previous selections
- **User Experience**: Clear messaging and automatic input clearing for fresh data selection
- **Implementation**: Modified GUI logic in `app.py` with smart input widget management

### Complete Undo Functionality
- **Problem Solved**: Comprehensive project state restoration that removes all files/directories created by undone steps
- **Technical Implementation**: Enhanced snapshot system with `take_complete_snapshot()` and `restore_complete_snapshot()` methods
- **User Experience**: Two-click confirmation system with detailed restoration feedback
- **Reliability**: Smart file exclusions and complete directory structure restoration

## 7. Latest Features (Session 5)
### Pseudo-Terminal Bug Resolution
- **Problem Solved**: Ultracentrifuge script pseudo-terminal was not appearing, preventing interactive user input
- **Root Causes Fixed**: Invalid YAML syntax, path construction bugs, and script structure inconsistencies
- **Technical Implementation**: Fixed workflow.yml parsing, corrected file path logic, and standardized script structure
- **Result**: Ultracentrifuge script now works identically to setup isotope script

### Enhanced Terminal Visibility
- **Problem Solved**: Users couldn't easily locate the terminal when it appeared at the top of the page
- **Solution**: Replaced complex JavaScript auto-scroll with prominent native Streamlit visual indicators
- **User Experience**: Large "🖥️ LIVE TERMINAL" header, colored alert banners, and clear messaging
- **Reliability**: Works consistently across all browsers and doesn't depend on JavaScript execution

## 8. Latest Features (Session 6)
### Granular Undo for Individual Step Re-runs
- **Problem Solved**: Users needed to undo individual re-runs of steps, not entire steps when multiple runs existed
- **Root Causes Fixed**: Original undo system designed for linear workflows, couldn't handle multiple runs per step
- **Technical Implementation**: Enhanced snapshot system with run-specific tracking and progressive undo logic
- **Key Features**:
  - **Unlimited Re-runs**: Any step can be re-run unlimited times with proper tracking
  - **Granular Undo**: Each undo goes back exactly one run, not entire steps
  - **Intelligent Status**: Step remains "completed" as long as successful runs exist
  - **Progressive Restoration**: Files from only the most recent run are removed per undo
- **Snapshot Strategy**: Dual snapshot system (before/after each run) for precise state restoration
- **Universal Compatibility**: Works for all steps in any workflow configuration with backward compatibility

## 9. Latest Features (Session 7)
### Enhanced Undo with Previous Step Restoration
- **Problem Solved**: Undo button would appear but do nothing when trying to undo the last remaining run of a step after previous undos created gaps in "after" snapshots
- **Root Cause Fixed**: Original logic assumed consecutive "after" snapshots existed, but previous undo operations removed them
- **Technical Implementation**: Enhanced backwards search algorithm and previous step restoration logic
- **Key Features**:
  - **Backwards Search Algorithm**: Searches through all possible previous "after" snapshots, handling gaps gracefully
  - **Previous Step Restoration**: When no current step "after" snapshots exist, restores to previous step's latest "after" snapshot
  - **Proper State Management**: Correctly marks steps as "pending" and removes success markers when undoing entire steps
  - **Comprehensive Testing**: 9 TDD tests covering all scenarios including gaps, normal operation, and edge cases
- **Universal Compatibility**: Works for all step combinations and maintains full backward compatibility

## 10. Latest Features (Session 8)
### Selective Re-run Capability
- **Problem Solved**: Users needed to restrict re-run capability to only specific workflow steps, preventing unnecessary re-execution of steps that should only run once
- **Root Cause Addressed**: Previous implementation allowed all completed steps to be re-run, which could lead to unintended workflow execution
- **Technical Implementation**: Enhanced workflow definition with optional `allow_rerun` property and updated GUI logic
- **Key Features**:
  - **Selective Control**: Only steps with `allow_rerun: true` show re-run buttons when completed
  - **Script-Based Logic**: Re-run capability tied to specific scripts rather than step numbers for maintainability
  - **Input Widget Management**: Smart display of input widgets only for pending steps and re-run-enabled completed steps
  - **Backward Compatibility**: Existing workflows continue to work without modification
- **Workflow Configuration**: Added `allow_rerun: true` to four specific scripts requiring iterative execution
- **Test Coverage**: Comprehensive TDD approach with 5 test cases validating all functionality aspects
- **Documentation**: Updated README.md and technical documentation with complete implementation details
- **Universal Compatibility**: Works for all workflow configurations with graceful property handling

## 11. Latest Features (Session 9)
### Workflow Template Protection System
- **Problem Solved**: Critical workflow.yml template was vulnerable to corruption, accidental modification, and lacked proper version control
- **Root Cause Addressed**: Template was stored in application root directory without protection, causing confusion and potential data loss
- **Technical Implementation**: Created dedicated templates/ directory with Git-based version control and comprehensive validation
- **Key Features**:
  - **Protected Template Directory**: Master workflow.yml stored in templates/ with clear documentation
  - **YAML Validation**: Comprehensive syntax and structure validation before project loading
  - **Multiple Recovery Options**: Snapshot restoration and template replacement for corrupted files
  - **Enhanced Error Handling**: Clear error messages with step-by-step recovery guidance
- **Critical Bug Fixes**: Resolved duplicate inputs sections causing YAML parsing failures
- **Input Correction**: Fixed ultracentrifuge step to require only "Sample List" input as per script requirements
- **Git Integration**: Template changes tracked with commit history for full version control
- **User Experience**: Proactive validation prevents crashes with user-friendly recovery options
- **Universal Compatibility**: Works with all existing projects while providing enhanced protection for new ones

## 12. Latest Features (Session 10)
### Skip to Step Functionality
- **Problem Solved**: Users needed ability to start workflows from midway points when some steps were completed outside the workflow tool
- **Root Cause Addressed**: System only supported linear execution from beginning, forcing users to re-run completed steps or manually manipulate state files
- **Technical Implementation**: Enhanced state management with "skipped" state support and comprehensive GUI integration
- **Key Features**:
  - **Flexible Workflow Entry**: Start from any step with proper state management and safety snapshots
  - **Three-State System**: Enhanced state management supporting "pending", "completed", and "skipped" states
  - **7-Scenario File Handling**: Comprehensive detection and handling of all possible project file combinations
  - **Guided Project Setup**: Radio button interface for "New Project" vs "Existing Work" with dynamic step selection
  - **Safety Snapshots**: Complete project snapshots taken before skip operations for rollback capability
- **Enhanced File Scenario Detection**: Robust logic handling all combinations of .yml/.db/.json file presence
- **Consistency Validation**: Stricter validation ensuring workflow state matches actual project files
- **Test Coverage**: Comprehensive TDD approach with 10 test cases covering all skip functionality scenarios
- **Visual Treatment**: Clear indicators for skipped steps with distinct styling and informational messages
- **Universal Compatibility**: Works with existing granular undo system and maintains full backward compatibility