# 06 - App.py Modifications for External Script Path Support

## Overview
Plan for modifying `app.py` to receive script path arguments from run scripts and pass them to all components that need script access, while maintaining full backward compatibility.

**IMPORTANT**: These changes do NOT affect the application's working directory. The GUI continues to operate from the project folder, and scripts execute in the project context. The script path only determines WHERE scripts are sourced from.

## Current App.py Analysis

### Key Areas Requiring Modification
- **Line 12**: `from src.core import Project` - Project initialization needs script path
- **Lines 32-34**: `create_update_manager("application")` - App update manager (no change needed)
- **Lines 50-52**: `create_update_manager("scripts")` - Script update manager needs external path
- **Lines 804-1055**: Multiple Project initialization points - Need script path parameter
- **Lines 1072-1117**: Update UI - Script update manager needs external path support

### Project Initialization Points Requiring Changes
1. **Line 804**: `st.session_state.project = Project(project_path)`
2. **Line 825**: `st.session_state.project = Project(project_path)`
3. **Line 866**: `st.session_state.project = Project(project_path)`
4. **Line 902**: `project_for_restore = Project(project_path, load_workflow=False)`
5. **Line 967**: `st.session_state.project = Project(project_path)`
6. **Line 1006**: `st.session_state.project = Project(project_path)`
7. **Line 1029**: `project_for_restore = Project(project_path, load_workflow=False)`
8. **Line 1055**: `st.session_state.project = Project(project_path)`

## Working Directory Preservation

### Current Working Directory Behavior ✅ PRESERVED
- **App Working Directory**: Streamlit runs from `sip_lims_workflow_manager/` (unchanged)
- **Project Working Directory**: All project operations use `project_path` (unchanged)
- **Script Execution Directory**: Scripts execute in project context (unchanged)
- **File Operations**: All GUI file operations relative to project folder (unchanged)

### What Changes vs What Stays the Same
**Changes (Script Sourcing Only)**:
- Script discovery: `project/scripts/` → `../sip_scripts_production/`
- Script updates: External repository instead of nested directory

**Unchanged (All Working Directory Operations)**:
- GUI working directory: Still `sip_lims_workflow_manager/`
- Project operations: Still use `project_path`
- Script execution: Still runs in project context
- File browsing: Still relative to project folder

## Required Modifications

### 1. Add Argument Parsing (Insert after imports, before page config)
```python
# NEW: Add after line 14 (after imports)
import argparse
from pathlib import Path

def parse_script_path_argument():
    """
    Parse command line arguments to get script path.
    Uses argparse to handle Streamlit's argument passing format.
    
    NOTE: This only affects WHERE scripts are sourced from,
    NOT the working directory of the application or script execution.
    """
    parser = argparse.ArgumentParser(add_help=False)  # Disable help to avoid conflicts
    parser.add_argument('--script-path', 
                       default='scripts', 
                       help='Path to scripts directory')
    
    # Parse only known args to avoid conflicts with Streamlit args
    try:
        args, unknown = parser.parse_known_args()
        script_path = Path(args.script_path)
        
        # Validate that script path exists
        if not script_path.exists():
            print(f"Warning: Script path does not exist: {script_path}")
            print("Falling back to default 'scripts' directory")
            script_path = Path("scripts")
            
        return script_path
    except Exception as e:
        print(f"Error parsing script path argument: {e}")
        print("Using default 'scripts' directory")
        return Path("scripts")

# Initialize script path globally
SCRIPT_PATH = parse_script_path_argument()
```

### 2. Modify Update Manager Functions (Lines 25-70)
```python
# MODIFIED: Update check_for_script_updates function (line 43)
@st.cache_data(ttl=3600)
def check_for_script_updates():
    """
    Check for script updates using the unified Git system.
    Uses the configured script path instead of hardcoded 'scripts' directory.
    """
    try:
        # Pass script path to update manager
        script_manager = create_update_manager("scripts", script_path=SCRIPT_PATH)
        return script_manager.check_for_updates()
    except Exception as e:
        return {
            'update_available': False,
            'current_version': None,
            'latest_version': None,
            'error': f"Failed to check for script updates: {str(e)}"
        }

# MODIFIED: Update update_scripts function (line 61)
def update_scripts():
    """Update scripts to latest version using configured script path."""
    try:
        script_manager = create_update_manager("scripts", script_path=SCRIPT_PATH)
        return script_manager.update_to_latest()
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to update scripts: {str(e)}"
        }
```

### 3. Store Script Path in Session State (In main() function)
```python
# MODIFIED: Add to main() function after state initialization (around line 543)
def main():
    st.title("🧪 SIP LIMS Workflow Manager")

    # --- State Initialization ---
    if 'project' not in st.session_state:
        st.session_state.project = None
    # ... existing state initialization ...
    
    # NEW: Initialize script path in session state
    if 'script_path' not in st.session_state:
        st.session_state.script_path = SCRIPT_PATH
        
    # Display script path info for debugging/transparency
    if st.session_state.script_path != Path("scripts"):
        st.sidebar.info(f"📁 Using external scripts: {st.session_state.script_path}")
```

### 4. Modify All Project Initialization Points
```python
# MODIFIED: Project creation with script path (Line 804)
try:
    st.session_state.project = Project(project_path, script_path=st.session_state.script_path)
    st.success("🎉 New project loaded! Ready to start from Step 1.")
    st.rerun()
except Exception as e:
    st.error(f"Error loading project: {e}")
    return

# MODIFIED: Project loading with script path (Line 825)
try:
    # Validate workflow file before loading
    is_valid, error_message = validate_workflow_yaml(workflow_file)
    if not is_valid:
        st.error(f"❌ **Workflow Validation Failed**: {error_message}")
        return
    
    # Load the project with script path
    st.session_state.project = Project(project_path, script_path=st.session_state.script_path)
    st.success(f"✅ Loaded: {st.session_state.project.path.name}")
    st.rerun()
except Exception as e:
    st.error(f"Error loading project: {e}")
    return

# MODIFIED: All other Project instantiations (Lines 866, 902, 967, 1006, 1029, 1055)
# Pattern for all:
st.session_state.project = Project(project_path, script_path=st.session_state.script_path)
# Or for restoration projects:
project_for_restore = Project(project_path, script_path=st.session_state.script_path, load_workflow=False)
```

### 5. Add Script Path Validation and Error Handling
```python
# NEW: Add script path validation function
def validate_script_path(script_path: Path) -> tuple[bool, str]:
    """
    Validate that the script path exists and contains expected scripts.
    Returns (is_valid, error_message)
    """
    if not script_path.exists():
        return False, f"Script directory does not exist: {script_path}"
    
    if not script_path.is_dir():
        return False, f"Script path is not a directory: {script_path}"
    
    # Check for at least one Python script
    python_scripts = list(script_path.glob("*.py"))
    if not python_scripts:
        return False, f"No Python scripts found in: {script_path}"
    
    return True, "Script path is valid"

# NEW: Add to main() function for validation
def main():
    # ... existing code ...
    
    # Validate script path on startup
    is_valid, error_msg = validate_script_path(st.session_state.script_path)
    if not is_valid:
        st.error(f"❌ **Script Path Error**: {error_msg}")
        st.info("💡 Please run the setup script to initialize script repositories.")
        st.stop()
```

### 6. Update Debug Information Display
```python
# MODIFIED: Enhanced debug information in sidebar
with st.sidebar:
    st.header("Controls")
    
    # NEW: Script path information
    with st.expander("📁 Script Configuration", expanded=False):
        st.write(f"**Script Path**: `{st.session_state.script_path}`")
        st.write(f"**Absolute Path**: `{st.session_state.script_path.resolve()}`")
        
        # Show available scripts
        if st.session_state.script_path.exists():
            scripts = list(st.session_state.script_path.glob("*.py"))
            st.write(f"**Available Scripts**: {len(scripts)}")
            if scripts:
                for script in sorted(scripts)[:5]:  # Show first 5
                    st.write(f"  • {script.name}")
                if len(scripts) > 5:
                    st.write(f"  • ... and {len(scripts) - 5} more")
        else:
            st.error("Script directory not found!")
```

## Test Specifications (TDD)

### Test Cases
```python
# Test 1: Working directory preservation
def test_working_directory_unchanged():
    # Given: app.py runs with external script path
    # When: any GUI operation occurs
    # Then: working directory should still be app directory
    # And: project operations should use project_path

def test_script_execution_directory():
    # Given: external script path is configured
    # When: script executes
    # Then: script should run in project context, not script source context

# Test 2: Command line argument parsing
def test_script_path_argument_parsing():
    # Given: app.py launched with --script-path="../sip_scripts_production"
    # When: arguments are parsed
    # Then: script_path should be Path("../sip_scripts_production")

def test_default_script_path_fallback():
    # Given: app.py launched without --script-path argument
    # When: arguments are parsed
    # Then: script_path should default to Path("scripts")

# Test 3: Project initialization
def test_project_initialization_with_script_path():
    # Given: script_path is set in session state
    # When: Project is initialized
    # Then: Project should receive the script_path parameter
    # And: Project should still use project_path for working directory

# Test 4: Update manager integration
def test_script_update_manager_uses_external_path():
    # Given: external script path is configured
    # When: script update manager is created
    # Then: should use external path instead of nested scripts/
```

## Implementation Strategy

### Phase 1: Add Argument Parsing
- Add argument parsing function
- Initialize global SCRIPT_PATH variable
- Test that app still works with default path
- Verify working directory unchanged

### Phase 2: Update Session State Management
- Add script path to session state
- Add validation function
- Add debug information display
- Test script path storage and display

### Phase 3: Modify Update Managers
- Update script update manager to use external path
- Test script update functionality
- Ensure app update manager unchanged

### Phase 4: Update Project Instantiations
- Modify all Project initialization points
- Test that all project loading scenarios work
- Verify script execution uses external path but runs in project context

## Working Directory Guarantee

### Explicit Preservation
```python
# NEW: Add working directory verification function
def verify_working_directory_preservation():
    """
    Verify that working directory operations remain unchanged.
    This is a safety check to ensure script path changes don't affect GUI operations.
    """
    import os
    
    # App should always run from its own directory
    current_wd = Path.cwd()
    expected_wd = Path(__file__).parent
    
    if current_wd != expected_wd:
        st.error(f"❌ Working directory changed unexpectedly!")
        st.error(f"Current: {current_wd}")
        st.error(f"Expected: {expected_wd}")
        st.stop()
```

### Key Assurances
1. **GUI Operations**: All file browsing, project selection remains relative to project
2. **Script Execution**: Scripts run in project context (via ScriptRunner)
3. **Project Management**: All project file operations use project_path
4. **App Functionality**: All existing app behavior preserved

## Benefits

### For Developers
- ✅ Can use different script repositories per session
- ✅ Clear visibility into which scripts are being used
- ✅ Working directory behavior unchanged (no confusion)
- ✅ All existing project operations work identically

### For Production Users
- ✅ No changes to user experience
- ✅ Working directory behavior unchanged
- ✅ All file operations work exactly as before
- ✅ No impact on project management workflow

### For Maintenance
- ✅ All existing app.py logic preserved
- ✅ Working directory operations unchanged
- ✅ Clean separation between script sourcing and execution
- ✅ Easy to test and verify no behavioral changes