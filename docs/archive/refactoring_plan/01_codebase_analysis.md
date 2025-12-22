# 01 - Current Codebase Analysis

## Overview
Analysis of the existing `sip_lims_workflow_manager` codebase to understand current structure and identify refactoring requirements.

## Current Directory Structure
```
sip_lims_workflow_manager/
├── scripts/                    # Currently nested - NEEDS TO BE EXTERNAL
├── app.py                     # Main Streamlit application
├── src/
│   ├── core.py               # Project and Workflow classes
│   ├── git_update_manager.py # Update management system
│   └── logic.py              # Supporting logic
├── setup.command/setup.bat   # Setup scripts
├── run.command/run.bat       # Run scripts
└── .gitignore               # Git ignore file
```

## Target Structure
```
Desktop/
├── sip_lims_workflow_manager/      # Main application
├── sip_scripts_workflow_gui/       # Development scripts (sibling)
└── sip_scripts_production/         # Production scripts (sibling)
```

## Key Code Dependencies Requiring Changes

### 1. Script Path Dependencies
- **File**: `src/git_update_manager.py`
  - **Line 473**: `repo_path = base_path / "scripts"` (hardcoded nested path)
  - **Line 33**: Hardcoded repository URL for scripts
  - **Impact**: Update manager assumes nested scripts directory

- **File**: `src/core.py`
  - **Line 41**: `self.script_runner = ScriptRunner(self.path)` (assumes scripts in project)
  - **Impact**: ScriptRunner needs to support external script paths

### 2. Setup Script Dependencies
- **File**: `setup.command`
  - **Lines 16-24**: Clones scripts into nested `scripts/` directory
  - **Impact**: Must be modified to setup external sibling directories

### 3. Project Initialization Points
- **File**: `app.py`
  - **Line 804**: `st.session_state.project = Project(project_path)`
  - **Line 825**: `st.session_state.project = Project(project_path)`
  - **Line 866**: `st.session_state.project = Project(project_path)`
  - **Line 902**: `project_for_restore = Project(project_path, load_workflow=False)`
  - **Line 1055**: `st.session_state.project = Project(project_path)`
  - **Impact**: All Project instantiations need script_path parameter

### 4. Update System Dependencies
- **File**: `app.py`
  - **Lines 32-34**: `create_update_manager("application")`
  - **Lines 50-52**: `create_update_manager("scripts")` - uses nested scripts
  - **Lines 1072-1117**: Update UI that needs to handle external script paths
  - **Impact**: Update managers need external script path support

### 5. Run Script Dependencies
- **File**: `run.command`
  - **Line 20**: `streamlit run app.py --server.headless=true --server.address=127.0.0.1`
  - **Impact**: No script path selection, needs mode detection and path passing

## Analysis Summary

### Components Requiring Modification:
1. ✅ **Setup Scripts** - Add mode detection and external repository setup
2. ✅ **Run Scripts** - Add script path selection and argument passing
3. ✅ **app.py** - Add argument parsing and script path handling
4. ✅ **src/core.py** - Add script_path parameter to Project class
5. ✅ **src/git_update_manager.py** - Support external script repositories
6. ✅ **.gitignore** - Add developer marker file exclusion

### New Components Required:
1. ✅ **Developer Marker System** - File-based dev/prod detection
2. ✅ **Mode Detection Logic** - Shared between setup and run scripts
3. ✅ **Script Path Passing** - Command line argument mechanism
4. ✅ **External Repository Management** - Setup and update external scripts

### Backward Compatibility Requirements:
- ✅ All existing functionality must continue to work
- ✅ Production mode should work exactly as current system
- ✅ Nested scripts should work as fallback during transition