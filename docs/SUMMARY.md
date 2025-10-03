# Project Summary: SIP LIMS Workflow Manager (v3)

## 1. Project Goal
To create a simple, lightweight, cross-platform GUI application to manage and execute a series of Python-based SIP (Stable Isotope Probing) laboratory workflow scripts, with robust error handling and version control for the scripts.

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
- **Phase 12 (Rollback System Unification):** Complete. Unified rollback behavior between manual undo and automatic failed step rollback for consistent project restoration.
- **Phase 13 (Timestamp Preservation):** Complete. Implemented timestamp preservation during rollback operations to maintain accurate file modification times.
- **Phase 14 (Conditional Workflow System):** Complete. Implemented comprehensive conditional workflow functionality allowing users to make Yes/No decisions at specific workflow points with automatic triggering, enhanced undo behavior, and complete state management.
- **Phase 15 (Terminal Output Cleanup):** Complete. Cleaned up verbose debug output from user-visible terminal interface while preserving comprehensive debug logging in background files for troubleshooting.
- **Phase 16 (Persistent Script Update Notifications):** Complete. Implemented comprehensive script update notification system that checks for updates every 30 minutes during app runtime, displays notifications in sidebar, and allows one-click updates without restarting the application.
- **Phase 17 (Unified Update System):** Complete. Implemented unified Git-based update system that manages both application and script updates through a single, clean interface with SSH authentication, eliminating Google Drive dependency and providing consistent user experience.
- **Phase 18 (SSH Key Architecture Fix):** Complete. Resolved critical SSH key authentication issues by implementing separate Ed25519 deploy keys for each repository, fixing permissions handling, and updating all update managers to use repository-specific SSH keys for reliable GitHub access.

## 3. Key Design Decisions
- **Core Engine:** A generic engine that reads workflow definitions from a `workflow.yml` file.
- **State Management:** Workflow progress is tracked in a `workflow_state.json` file, supporting "pending", "completed", and "skipped" states.
- **Undo/Redo:** Implemented via a snapshot mechanism.
- **Error Handling:** The engine automatically restores the pre-run snapshot if any script fails. Enhanced with success marker files for reliable failure detection.
- **Script Management (Centralized Git Repository):**
    - The application's workflow scripts are managed in a central, private Git repository and cloned into a local `scripts` folder during setup.
- **Distribution Model:** The application is distributed as a folder. A one-time `setup` script prepares the environment and clones the separate scripts repository. A `run` script launches the app.
- **Two-Repository Architecture:** Main application (`sip_lims_workflow_manager`) and scripts (`sip_scripts_workflow_gui`) are managed in separate repositories for independent versioning.

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
22. **Rollback System Unification**: Unified rollback behavior between manual undo and automatic failed step rollback using complete snapshot restoration for consistency.
23. **Timestamp Preservation**: Implemented file modification time preservation during all rollback operations to maintain accurate file creation timestamps.
24. **Conditional Workflow System**: Implemented comprehensive conditional workflow functionality with automatic triggering, Yes/No decision prompts, enhanced undo behavior for decision points, and complete integration with existing workflow management.
25. **Script Termination Functionality**: Added terminate button in terminal interface allowing users to stop running scripts and automatically rollback to pre-execution state.
26. **SIP Branding Update**: Updated application title and branding from "LIMS Workflow Manager" to "SIP LIMS Workflow Manager" to reflect Stable Isotope Probing laboratory focus.
27. **Terminal Output Cleanup**: Removed verbose debug messages from user-visible terminal output while preserving comprehensive debug logging in background files for professional user experience.
28. **Repository Separation**: Separated workflow scripts into independent `sip_scripts_workflow_gui` repository for better version control, independent updates, and cleaner architecture.
29. **Persistent Script Update Notifications**: Implemented comprehensive script update system with 30-minute automatic checking, sidebar notifications, one-click updates, and manual refresh capability, eliminating the need to restart the app to see script updates.
30. **Auto-Scroll Functionality Removal**: Removed automatic page scrolling functionality after determining it caused usability issues and interfered with user control. Users now manually scroll to view terminal output, maintaining full control over page navigation while relying on prominent visual indicators to locate the terminal.
31. **SSH Key Architecture Fix**: Resolved critical SSH key authentication issues by implementing separate Ed25519 deploy keys for each repository (scripts_deploy_key and app_deploy_key), fixing SSH permissions handling in setup scripts, and updating all update managers to use repository-specific SSH keys for reliable GitHub access.

## 5. Next Steps (Optional Enhancements)
1. **Enhanced Logging**: Improve GUI feedback and real-time information display.
2. **Workflow Validation**: Implement validation for `workflow.yml` file syntax and structure.
3. **Comprehensive Testing**: Perform full end-to-end testing on both macOS and Windows platforms.

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

## 13. Latest Features (Session 11)
### Rollback System Unification
- **Problem Solved**: Inconsistent rollback behavior between manual undo (complete snapshots) and failed step rollback (selective restoration)
- **Root Cause Addressed**: Failed steps weren't properly cleaning up all script artifacts, causing rollback loops and incomplete restoration
- **Technical Implementation**: Unified both rollback scenarios to use complete snapshot restoration for consistency
- **Key Features**:
  - **Consistent Behavior**: Both manual undo and automatic rollback now use identical restoration logic
  - **Complete Cleanup**: All script artifacts properly removed during failed step rollback
  - **Fallback Compatibility**: Multiple fallback options for missing snapshots with legacy support
  - **Enhanced Logging**: Detailed debug messages for troubleshooting rollback operations
- **Test Coverage**: Comprehensive TDD approach with 6 test cases validating unified rollback system
- **Performance**: Minimal overhead with efficient complete snapshot restoration
- **Universal Compatibility**: Works with all existing snapshots and maintains full backward compatibility

## 14. Latest Features (Session 12)
### Timestamp Preservation During Rollback Operations
- **Problem Solved**: File modification dates were updated to current time during rollback instead of preserving original timestamps
- **Root Cause Addressed**: Standard ZIP extraction automatically updates file timestamps regardless of original metadata
- **Technical Implementation**: Enhanced snapshot restoration with individual file extraction and timestamp preservation
- **Key Features**:
  - **Automatic Preservation**: File modification times preserved during all rollback operations (manual undo, automatic rollback, granular undo)
  - **ZIP Metadata Utilization**: Leverages original timestamps stored in ZIP file metadata for accurate restoration
  - **Universal Application**: Works with all file types and rollback scenarios without user intervention
  - **Workflow Integrity**: Time-dependent workflows continue to function correctly with accurate file timestamps
- **Technical Details**: Uses `os.utime()` with ZIP `member.date_time` metadata for precise timestamp restoration
- **Test Coverage**: Comprehensive TDD approach with multiple test files validating timestamp preservation functionality
- **Performance**: Minimal overhead with individual file extraction and microsecond timestamp operations
- **Limitations**: File timestamps preserved (primary use case), directory timestamps require future enhancement
- **Universal Compatibility**: Works with all existing snapshots and maintains full backward compatibility

## 15. Latest Features (Session 13)
### Conditional Workflow System
- **Problem Solved**: Users needed ability to make conditional decisions during workflow execution, specifically whether to run optional steps like emergency third attempts
- **Root Cause Addressed**: Linear workflow system couldn't handle decision points where users choose between different execution paths
- **Technical Implementation**: Comprehensive conditional workflow system with automatic triggering, state management, and enhanced undo behavior
- **Key Features**:
  - **Automatic Triggering**: Conditional prompts appear automatically when trigger scripts complete
  - **Yes/No Decision Interface**: Clear prompts with intuitive Yes/No buttons for user decisions
  - **Enhanced State Management**: New states (`awaiting_decision`, `skipped_conditional`) for conditional workflow tracking
  - **Smart Undo Behavior**: Enhanced undo logic that respects conditional decision points and allows undoing decisions separately from step execution
  - **Dependency Handling**: Automatic management of dependent conditional steps based on user decisions
  - **Configuration Preservation**: Workflow.yml files preserved during undo operations to maintain conditional configurations
- **Workflow Configuration**: Enhanced workflow.yml with conditional step definitions including trigger scripts, prompts, target steps, and dependencies
- **Test Coverage**: Comprehensive TDD approach with 17 test cases validating all conditional workflow functionality
- **User Experience**: Seamless integration with existing workflow interface, clear visual indicators for conditional states, and intuitive decision-making process
- **Universal Compatibility**: Works with all existing workflows while providing new conditional capabilities for enhanced workflow flexibility

## 16. Latest Features (Session 15)
### Terminal Output Cleanup
- **Problem Solved**: Users were seeing verbose debug information (process IDs, file descriptors, exit codes) that cluttered the terminal interface and made it less professional
- **Root Cause Addressed**: Debug messages intended for development were being displayed to end users in the terminal output
- **Technical Implementation**: Separated debug logging from user output using dual logging functions in ScriptRunner class
- **Key Features**:
  - **Clean Terminal Interface**: Users now see only relevant script output and interactive prompts
  - **Professional Appearance**: Removed technical jargon and debug clutter from user interface
  - **Preserved Debug Capability**: All technical information still captured in background log files
  - **Enhanced User Focus**: Users can concentrate on actual script interactions without distraction
- **Debug Information Preservation**: Complete execution traces, timing, and error information maintained in `.workflow_logs/debug_script_execution.log`
- **User Experience**: Significantly improved professional appearance while maintaining full debugging capabilities for troubleshooting
- **Universal Compatibility**: Works with all existing workflows and maintains backward compatibility

## 17. Latest Features (Session 16)
### Repository Separation and Architecture Improvement
- **Problem Solved**: Scripts were bundled with main application repository, preventing independent versioning and updates
- **Root Cause Addressed**: During development, scripts evolved within main repository and became more current than separate scripts repository
- **Technical Implementation**: Created new `sip_scripts_workflow_gui` repository with updated scripts and modified setup process
- **Key Features**:
  - **Independent Repositories**: Main app (`sip_lims_workflow_manager`) and scripts (`sip_scripts_workflow_gui`) now completely separate
  - **Automatic Script Cloning**: Setup process automatically clones scripts from separate repository
  - **Independent Updates**: Scripts and app can be updated separately with different release cycles
  - **Cleaner Architecture**: App repository no longer contains bundled scripts, reducing download size
- **Setup Process Enhancement**: Modified `setup.command` and `setup.bat` to clone from new scripts repository
- **User Experience**: No change to user workflow - scripts still appear in same `scripts/` folder location
- **Version Control**: Each component (app vs scripts) has independent Git history and release management
- **Documentation Updates**: Updated README.md and technical documentation to reflect new architecture
- **Universal Compatibility**: Existing user workflows unchanged while providing better development architecture

## 18. Latest Features (Session 17)
### Unified Update System Implementation
- **Problem Solved**: Inconsistent update architecture with Google Drive for app updates and separate SSH system for scripts, causing cluttered interface and user confusion
- **Root Cause Addressed**: Dual update systems used different authentication methods, interfaces, and checking frequencies, creating maintenance complexity and poor user experience
- **Technical Implementation**: Complete unified Git-based update system with SSH authentication for both repositories and clean, expandable user interface
- **Key Features**:
  - **Unified GitUpdateManager**: Single class handles both application and script updates with consistent SSH authentication
  - **Clean Interface**: Updates only appear when available, eliminating persistent sidebar clutter
  - **Smart Notifications**: Expandable "🔔 Updates Available" section with side-by-side app and script details
  - **User Control**: All updates require explicit user approval - no automatic installations
  - **Consistent Frequency**: 60-minute checking for both update types with page refresh triggers
  - **SSH Security**: Enhanced SSH key validation with Ed25519 support and comprehensive security checks
- **Architecture Benefits**: Eliminated Google Drive dependency, unified authentication, consistent versioning with Git tags, and single codebase for maintenance
- **User Experience**: Non-intrusive notifications, expandable details on demand, one-click script updates, manual app downloads from GitHub releases
- **Test Coverage**: Comprehensive TDD approach with 13 integration tests plus full regression testing (153/154 tests passing)
- **Security Enhancements**: SSH key type validation, permission verification, repository access testing, and graceful error handling
- **Documentation**: Complete technical documentation, user guide updates, and migration notes for seamless transition
- **Universal Compatibility**: Maintains all existing functionality while providing cleaner, more consistent update experience

## 18. Latest Features (Session 18)
### Auto-Scroll Functionality Removal
- **Problem Identified**: Users running scripts from later workflow steps (12, 13, 14) couldn't see the terminal that opened at the top of the page
- **Initial Solution Attempted**: Implemented comprehensive JavaScript auto-scroll function with aggressive multi-method approach for Streamlit compatibility
- **Issues Discovered**: Auto-scroll functionality caused "crazy scrolling" behavior that interfered with users' ability to manually scroll and control page navigation
- **Final Decision**: Complete removal of auto-scroll functionality after determining it caused more usability problems than it solved
- **Key Changes**:
  - **Function Removal**: Completely removed `scroll_to_top()` function from [`app.py`](../app.py)
  - **Call Site Cleanup**: Removed all auto-scroll function calls from Run and Re-run button handlers
  - **Test Updates**: Modified tests to verify removal and serve as safeguards against re-introduction
  - **User Control**: Users now maintain full control over page scrolling behavior
- **User Experience**: Users manually scroll to view terminal output when needed, relying on prominent "🖥️ LIVE TERMINAL" visual indicators
- **Technical Benefits**: Eliminated JavaScript execution overhead, timing conflicts, and cross-browser compatibility issues
- **Test Coverage**: Updated TDD approach with 5 test cases validating complete removal of auto-scroll functionality
- **Manual Verification**: Confirmed clean removal with no interference in user scrolling behavior
- **Universal Compatibility**: Maintains all existing functionality while eliminating scrolling interference

## 19. Latest Features (Session 19)
### Conditional Undo Bug Fix
- **Problem Solved**: Critical bug where undo functionality was broken for conditional steps in "awaiting_decision" state, causing infinite loops or no response when clicking "Undo Last Step"
- **Root Cause Addressed**: Conditional undo logic was missing "awaiting_decision" from state checks, and conditional decision snapshots contained the problematic state causing forward jumping instead of backward undo
- **Technical Implementation**: Enhanced conditional undo logic with proper state detection, snapshot management, and trigger step undo functionality
- **Key Features**:
  - **State Detection Fix**: Added "awaiting_decision" to conditional undo state check in [`perform_undo()`](../app.py:318)
  - **Snapshot Management**: Enhanced logic to remove conditional decision snapshots when undoing to prevent forward jumping
  - **Trigger Step Undo**: Modified logic to undo the trigger step (e.g., step 9) when undoing from conditional "awaiting_decision" state
  - **Complete Restoration**: Implemented full trigger step undo including snapshot restoration, success marker removal, and state updates
- **Test Coverage**: Comprehensive TDD approach with 6 test cases reproducing the bug and validating the complete fix
- **User Experience**: Conditional undo now works seamlessly - first undo resets conditional step and undoes trigger step, subsequent undos work normally going backwards through workflow
- **Manual Verification**: Confirmed fix works correctly in real-world scenarios with both test projects (rex_test2 and rex_test2_production_test)
- **Universal Compatibility**: Maintains all existing undo functionality while properly handling conditional workflow decision points

## 20. Latest Features (Session 21)
### SSH Key Architecture Fix
- **Problem Solved**: Critical SSH key authentication issues preventing installation and updates, including permissions errors, repository access conflicts, and "key already in use" GitHub deploy key limitations
- **Root Cause Addressed**: Single SSH key trying to access multiple repositories violated GitHub's one-deploy-key-per-repository security model, combined with incorrect file permissions and hardcoded key paths in update managers
- **Technical Implementation**: Complete SSH key architecture redesign with separate Ed25519 deploy keys for each repository and enhanced SSH key manager supporting multiple keys
- **Key Features**:
  - **Separate Deploy Keys**: Dedicated `scripts_deploy_key` for scripts repository and `app_deploy_key` for application repository
  - **Enhanced SSH Key Manager**: Multi-key support with configurable key names while maintaining backward compatibility
  - **Repository-Specific Key Selection**: GitUpdateManager automatically selects correct SSH key based on repository type
  - **Automatic Permission Management**: Setup scripts automatically set correct SSH key permissions (0600 for private keys)
  - **Ed25519 Security**: Modern elliptic curve algorithm for enhanced security and performance
- **Test Coverage**: Comprehensive TDD approach with 10 test cases covering multi-key support, repository mapping, and real-world integration
- **User Experience**: Transparent operation with reliable installation, seamless updates, and elimination of SSH error messages
- **Security Enhancements**: Key separation reduces security risk, dedicated permissions per repository, and automatic permission enforcement
- **Universal Compatibility**: Maintains backward compatibility while providing robust SSH authentication for all repository operations