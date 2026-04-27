import streamlit as st
from pathlib import Path
import subprocess
import sys
import json
import shutil
import threading
import time
import queue
import yaml
import webbrowser
import os
from src.core import Project
from src.logic import RunResult, RollbackError
from src.workflow_utils import get_workflow_template_path, get_workflow_type_display
# Docker validation imports removed - native execution only
import argparse

# CRITICAL: Enable debug logging for app.py and import debug functions
os.environ['WORKFLOW_DEBUG'] = 'true'
from src.enhanced_debug_logger import (
    debug_context, log_info, log_error, log_warning,
    debug_enabled
)

def get_dynamic_title() -> str:
    """
    Generate dynamic title based on WORKFLOW_TYPE environment variable.
    
    Returns:
        str: Dynamic title showing the specific workflow type
    """
    workflow_type = os.environ.get('WORKFLOW_TYPE', '').strip().upper()
    
    if workflow_type == 'SIP':
        return "🧪 SIP LIMS Workflow Manager"
    elif workflow_type == 'SPS-CE':
        return "🧪 SPS-CE LIMS Workflow Manager"
    elif workflow_type == 'CAPSULE-SORTING':
        return "🧪 Capsule Sorting LIMS Workflow Manager"
    else:
        # Fallback to generic title if workflow type is not set or unknown
        return "🧪 SIP LIMS Workflow Manager"

def get_project_display_name(project_path: Path) -> str:
    """
    Get the display name for the project.
    Uses PROJECT_NAME environment variable if available, otherwise falls back to path name.
    
    Args:
        project_path: The project path for native execution
        
    Returns:
        str: The project name to display in the UI
    """
    project_name = os.environ.get('PROJECT_NAME', '').strip()
    
    if project_name:
        return project_name
    return project_path.name

def display_project_info_in_sidebar():
    """
    Display project information in the sidebar.
    Shows the project folder name for native execution.
    """
    if st.session_state.project_path:
        project_display_name = get_project_display_name(st.session_state.project_path)
        st.info(f"📁 **Current Project**: `{project_display_name}`")
    else:
        st.warning("📁 **No Project**: Please select a project directory")

def parse_script_path_argument():
    """
    Parse command line arguments to get script path.
    Uses argparse to handle Streamlit's argument passing format.
    Native execution: uses SCRIPTS_PATH environment variable or default.
    """
    parser = argparse.ArgumentParser(add_help=False)  # Disable help to avoid conflicts
    parser.add_argument('--script-path',
                       default='scripts',
                       help='Path to scripts directory')
    
    # Parse only known args to avoid conflicts with Streamlit args
    try:
        args, unknown = parser.parse_known_args()
        
        # Check for SCRIPTS_PATH environment variable (set by run.py)
        env_script_path = os.environ.get('SCRIPTS_PATH', '').strip()
        if env_script_path:
            script_path = Path(env_script_path)
            # REMOVED: print statement was causing infinite Streamlit refresh loops
        else:
            script_path = Path(args.script_path)
        
        # Validate that script path exists - FAIL FAST instead of fallback
        if not script_path.exists():
            print(f"CRITICAL ERROR: Script path does not exist: {script_path}")
            print(f"Environment SCRIPTS_PATH: {os.environ.get('SCRIPTS_PATH', 'NOT SET')}")
            print("This indicates a configuration or setup issue.")
            print("Please check your workflow setup and script path configuration.")
            # DO NOT fallback to local scripts - this causes wrong script path issues
            raise FileNotFoundError(f"Script path does not exist: {script_path}")
            
        return script_path
    except Exception as e:
        print(f"Error parsing script path argument: {e}")
        print("Using default 'scripts' directory")
        return Path("scripts")

# Script path will be determined dynamically when needed
def get_script_path():
    """Get the current script path, checking environment variables each time."""
    script_path = parse_script_path_argument().resolve()
    
    # REMOVED DEBUG LOGGING HERE - it was causing infinite loop
    # Debug logging will be done in Project initialization instead
    
    return script_path

def clear_cached_project_if_script_path_changed():
    """Clear cached project if the script path has changed to force recreation with correct path."""
    if 'project' in st.session_state:
        current_script_path = get_script_path()
        cached_script_path = st.session_state.project.script_path
        
        # Debug information
        st.info(f"🔍 **Debug**: Current script path: `{current_script_path}`")
        st.info(f"🔍 **Debug**: Cached script path: `{cached_script_path}`")
        
        if current_script_path != cached_script_path:
            st.error(f"🚨 **SCRIPT PATH MISMATCH DETECTED!**")
            st.error(f"   Cached: `{cached_script_path}`")
            st.error(f"   Current: `{current_script_path}`")
            st.warning("🗑️ **Clearing cached project to use correct script path...**")
            
            # Clear the cached project using Streamlit's recommended method
            del st.session_state.project
            
            # Also clear any other related cached state
            keys_to_clear = [key for key in st.session_state.keys() if 'project' in key.lower()]
            for key in keys_to_clear:
                del st.session_state[key]
                st.info(f"🗑️ Cleared cached state: `{key}`")
            
            st.success("✅ **Session state cleared! Reloading with correct script path...**")
            st.rerun()
        else:
            st.success(f"✅ **Script paths match**: `{current_script_path}`")

# --- Page Configuration ---
st.set_page_config(page_title="SIP LIMS Workflow Manager", page_icon="🧪", layout="wide")

import streamlit.components.v1 as components

# --- Terminal Configuration ---
TERMINAL_HEIGHT = 450  # Reduced height for better screen utilization

# --- Helper Functions ---
# Update functionality removed - all updates are handled by run scripts before container creation
# Scripts are mounted read-only into the container, so in-app updates are not possible or needed

def format_last_check_time(last_check):
    """Format the last check time for display."""
    if not last_check:
        return "Never"
    
    now = time.time()
    if hasattr(last_check, 'timestamp'):
        check_time = last_check.timestamp()
    else:
        check_time = time.mktime(last_check.timetuple())
    
    diff = now - check_time
    
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(diff / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

def get_script_run_count(project, step_id):
    """
    Count how many times a script has been completed.
    This count automatically adjusts when steps are undone since it reads
    from the current _completion_order array in workflow_state.json.
    """
    completion_order = project.state_manager.get_completion_order()
    return completion_order.count(step_id)

def validate_workflow_yaml(file_path):
    """
    Validates a workflow.yml file for basic syntax and structure.
    Returns (is_valid, error_message)
    """
    try:
        with open(file_path, 'r') as f:
            workflow_data = yaml.safe_load(f)
        
        # Basic structure validation
        if not isinstance(workflow_data, dict):
            return False, "Workflow file must contain a YAML dictionary"
        
        if 'workflow_name' not in workflow_data:
            return False, "Missing required 'workflow_name' field"
        
        if 'steps' not in workflow_data:
            return False, "Missing required 'steps' field"
        
        if not isinstance(workflow_data['steps'], list):
            return False, "'steps' must be a list"
        
        # Validate each step has required fields
        for i, step in enumerate(workflow_data['steps']):
            if not isinstance(step, dict):
                return False, f"Step {i+1} must be a dictionary"
            
            required_fields = ['id', 'name']
            for field in required_fields:
                if field not in step:
                    return False, f"Step {i+1} missing required field '{field}'"
            
            # Script field is optional for decision steps
            step_type = step.get('type', 'script')
            if step_type != 'decision' and 'script' not in step:
                return False, f"Step {i+1} missing required field 'script' (required for non-decision steps)"
        
        return True, "Workflow file is valid"
        
    except yaml.YAMLError as e:
        return False, f"YAML syntax error: {e}"
    except Exception as e:
        return False, f"Error reading workflow file: {e}"


def send_and_clear_input(project, user_input):
    """Callback to send input to the script and clear the input box."""
    if project.script_runner.is_running():
        # Strip whitespace and newlines to prevent PTY input buffer contamination
        # This fixes the issue where pressing Enter leaves stray newlines that
        # get consumed by subsequent input() calls in the same script
        user_input = user_input.strip() if user_input else ""
        
        # Prevent double input by checking if we just sent input
        current_time = time.time()
        last_input_time = st.session_state.get('last_input_time', 0)
        
        # Only send if it's been more than 100ms since last input
        if current_time - last_input_time > 0.1:
            project.script_runner.send_input(user_input)
            st.session_state.last_input_time = current_time
            st.session_state.terminal_input_box = ""
            st.session_state.scroll_to_bottom = True

# handle_terminal_input_change() function removed - Enter key functionality disabled
# to prevent race conditions with workflow_state.json file access on external drives

def create_inline_file_browser(input_key: str, start_path: str = None):
    """
    Create an inline file browser widget for native file selection.
    
    Args:
        input_key: Unique key for this file browser instance
        start_path: Starting directory path (defaults to current project or home directory)
    
    Returns:
        str: Selected file path or None if no selection made
    """
    if start_path is None:
        # Use PROJECT_PATH environment variable if available, otherwise current directory
        project_path = os.environ.get('PROJECT_PATH', '').strip()
        start_path = project_path if project_path else "."
    
    # Initialize session state for this browser instance
    browser_key = f"browser_{input_key}"
    current_path_key = f"current_path_{input_key}"
    selected_file_key = f"selected_file_{input_key}"
    
    if current_path_key not in st.session_state:
        st.session_state[current_path_key] = Path(start_path)
    if selected_file_key not in st.session_state:
        st.session_state[selected_file_key] = None
    
    current_path = st.session_state[current_path_key]
    
    # File browser container
    with st.container():
        st.markdown("**📁 File Browser**")
        
        # Current path display
        st.text(f"📍 Current: {current_path}")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("⬆️ Up", key=f"up_{input_key}"):
                parent = current_path.parent
                if parent != current_path:  # Prevent going above root
                    st.session_state[current_path_key] = parent
                    st.rerun()
        
        with col2:
            if st.button("🏠 Home", key=f"home_{input_key}"):
                # Use PROJECT_PATH environment variable if available, otherwise user home
                project_path = os.environ.get('PROJECT_PATH', '').strip()
                home_path = project_path if project_path else str(Path.home())
                st.session_state[current_path_key] = Path(home_path)
                st.rerun()
        
        # Directory contents
        try:
            items = []
            if current_path.exists() and current_path.is_dir():
                # Get directories first, then files
                dirs = [item for item in current_path.iterdir() if item.is_dir() and not item.name.startswith('.')]
                files = [item for item in current_path.iterdir() if item.is_file() and not item.name.startswith('.')]
                
                # Sort both lists
                dirs.sort(key=lambda x: x.name.lower())
                files.sort(key=lambda x: x.name.lower())
                
                items = dirs + files
            
            if items:
                # Create a scrollable area for file listing
                with st.container():
                    st.markdown("**Contents:**")
                    
                    # Display items in a more compact format
                    for item in items[:50]:  # Limit to first 50 items for performance
                        col_icon, col_name, col_action = st.columns([1, 4, 1])
                        
                        with col_icon:
                            if item.is_dir():
                                st.text("�")
                            else:
                                st.text("📄")
                        
                        with col_name:
                            st.text(item.name)
                        
                        with col_action:
                            if item.is_dir():
                                if st.button("Open", key=f"open_{input_key}_{item.name}"):
                                    st.session_state[current_path_key] = item
                                    st.rerun()
                            else:
                                if st.button("Select", key=f"select_{input_key}_{item.name}"):
                                    st.session_state[selected_file_key] = str(item)
                                    st.success(f"✅ Selected: {item.name}")
                                    st.rerun()
                    
                    if len(items) > 50:
                        st.info(f"Showing first 50 of {len(items)} items")
            else:
                st.info("📂 Empty directory")
                
        except PermissionError:
            st.error("❌ Permission denied accessing this directory")
        except Exception as e:
            st.error(f"❌ Error reading directory: {e}")
    
    # Return selected file if any
    return st.session_state[selected_file_key]

# Dead file browser functions removed - project selection handled by run.command
# Only inline file browser for workflow steps is needed

def perform_undo(project):
    """
    Undo the last completed step using the new selective snapshot system.
    Falls back to legacy complete ZIPs for steps completed before the upgrade.
    Uses chronological completion order for proper cyclical workflow support.

    Returns:
        (True, None)           — undo succeeded
        (False, error_msg)     — undo failed; error_msg is a human-readable string
        (False, RollbackError) — undo failed with a structured rollback error
    """
    # Get the most recently completed step using chronological order
    last_step_id = project.state_manager.get_last_completed_step_chronological()

    if not last_step_id:
        return False, "No completed steps to undo."

    # Get the step object
    last_step = project.workflow.get_step_by_id(last_step_id)
    if not last_step:
        msg = f"Step '{last_step_id}' not found in workflow definition."
        log_error("Undo failed: step not found in workflow", step_id=last_step_id)
        return False, msg

    try:
        # Get the effective current run number (highest snapshot that exists)
        effective_run = project.snapshot_manager.get_effective_run_number(last_step_id)
        log_info("Undo requested", step_id=last_step_id, effective_run=effective_run)

        if effective_run > 1:
            # Granular undo — restore to before the most recent run.
            # restore_snapshot() raises RollbackError on failure.
            log_info("Undo: granular restore to before most recent run",
                     step_id=last_step_id, run=effective_run)
            project.snapshot_manager.restore_snapshot(last_step_id, effective_run)
            # Remove the most recent run snapshot (consumed by restore)
            project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
            log_info("Undo: granular restore completed",
                     step_id=last_step_id, run=effective_run)
            # Step remains "completed" since earlier runs still exist.
            # Remove the most recent occurrence of this step from _completion_order
            # so the GUI run counter decrements correctly.
            state = project.state_manager.load()
            completion_order = state.get("_completion_order", [])
            for i in range(len(completion_order) - 1, -1, -1):
                if completion_order[i] == last_step_id:
                    completion_order.pop(i)
                    break
            state["_completion_order"] = completion_order
            project.state_manager.save(state)
            log_info("Undo: decremented completion count",
                     step_id=last_step_id,
                     remaining_runs=completion_order.count(last_step_id))

            # Remove the run-number-specific success marker for the undone run.
            script_name = Path(last_step.get('script', '')).stem
            if script_name:
                status_dir = project.path / ".workflow_status"
                run_marker = status_dir / f"{script_name}.run_{effective_run}.success"
                if run_marker.exists():
                    run_marker.unlink()
                    log_info("Undo: removed run-specific success marker",
                             marker=run_marker.name)

            return True, None

        if effective_run == 1:
            # Full step undo — restore to before the step ever ran.
            log_info("Undo: full step undo (run 1)", step_id=last_step_id)
            project.snapshot_manager.restore_snapshot(last_step_id, 1)
            # Remove all run snapshots for this step
            project.snapshot_manager.remove_all_run_snapshots(last_step_id)

            # Remove the success marker for this step.
            script_name = Path(last_step.get('script', '')).stem
            if script_name:
                status_dir = project.path / ".workflow_status"
                # Run-number-specific marker (current format)
                run_marker = status_dir / f"{script_name}.run_1.success"
                if run_marker.exists():
                    run_marker.unlink()
                    log_info("Undo: removed run-specific success marker",
                             marker=run_marker.name)
                # Flat marker (legacy format — safety net for old projects)
                flat_marker = status_dir / f"{script_name}.success"
                if flat_marker.exists():
                    flat_marker.unlink()
                    log_info("Undo: removed flat success marker (legacy)",
                             script=script_name)

            project.update_state(last_step_id, "pending")
            log_info("Undo: step marked as pending", step_id=last_step_id)
            return True, None

        # No snapshots found at all
        msg = (f"No snapshot found for step '{last_step.get('name', last_step_id)}'. "
               "Cannot undo — the snapshot may have already been consumed.")
        log_error("Undo failed: no snapshot found", step_id=last_step_id)
        return False, msg

    except RollbackError as e:
        log_error("Undo failed with RollbackError",
                  step_id=last_step_id, reason=e.reason)
        return False, e
    except Exception as e:
        msg = f"Unexpected error during undo: {e}"
        log_error("Undo failed with unexpected exception",
                  step_id=last_step_id, error=str(e))
        return False, msg

def run_step_background(project, step_id, user_inputs):
    """
    This function runs in a background thread. It calls the non-blocking
    run_step method from the core, which simply starts the script. The
    main UI thread is responsible for polling for the result.
    """
    project.run_step(step_id, user_inputs)

def start_script_thread(project, step_id, user_inputs):
    """Starts the script execution in a background thread."""
    if 'script_thread' in st.session_state and st.session_state['script_thread'] and st.session_state['script_thread'].is_alive():
        return  # A thread is already running

    thread = threading.Thread(target=run_step_background, args=(project, step_id, user_inputs))
    st.session_state['script_thread'] = thread
    thread.start()


def detect_and_load_native_project():
    """Auto-detect and load project from environment variables."""
    project_path_env = os.environ.get('PROJECT_PATH', '').strip()
    
    if project_path_env:
        project_path = Path(project_path_env)
        
        # Auto-load the project from environment variable
        if 'project_path' not in st.session_state or st.session_state.project_path != project_path:
            st.session_state.project_path = project_path
            st.session_state.project = None  # Force reload
            st.info(f"📁 **Native Mode**: Auto-loaded project from environment: `{project_path}`")
        return True
    return False

# --- Main Application ---
def main():
    # REMOVED: clear_cached_project_if_script_path_changed() was causing infinite refresh loops
    # Script path validation is now handled during project creation
    
    st.title(get_dynamic_title())

    # --- Native Environment Validation ---
    # Native execution only - no Docker validation needed

    # --- Native Project Loading ---
    # Load project from PROJECT_PATH environment variable if available

    # --- State Initialization ---
    if 'project' not in st.session_state:
        st.session_state.project = None
    if 'last_run_result' not in st.session_state:
        st.session_state.last_run_result = None
    if 'undo_confirmation' not in st.session_state:
        st.session_state.undo_confirmation = False
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = []
    if 'skip_confirmation_step_id' not in st.session_state:
        st.session_state.skip_confirmation_step_id = None
    if 'project_path' not in st.session_state:
        st.session_state.project_path = None
    if 'user_inputs' not in st.session_state:
        st.session_state.user_inputs = {}
    if 'terminal_output' not in st.session_state:
        st.session_state.terminal_output = ""
    if 'running_step_id' not in st.session_state:
        st.session_state.running_step_id = None
    if 'script_thread' not in st.session_state:
        st.session_state.script_thread = None
    if 'scroll_to_bottom' not in st.session_state:
        st.session_state.scroll_to_bottom = False
    if 'completed_script_output' not in st.session_state:
        st.session_state.completed_script_output = ""
    if 'completed_script_step' not in st.session_state:
        st.session_state.completed_script_step = None
    if 'completed_script_success' not in st.session_state:
        st.session_state.completed_script_success = None
    # Persistent critical alert shown when an automatic or manual rollback fails.
    # Stored as a dict so it survives reruns until the user explicitly dismisses it.
    if 'critical_rollback_alert' not in st.session_state:
        st.session_state.critical_rollback_alert = None
    # Tracks which auxiliary script is currently running (None when idle).
    if 'running_auxiliary_id' not in st.session_state:
        st.session_state.running_auxiliary_id = None

    # --- Native Auto-Detection ---
    # Try to auto-detect and load native project
    is_native_mode = detect_and_load_native_project()

    # --- Sidebar ---
    with st.sidebar:
        st.header("Controls")
        
        st.subheader("Project")
        
        # Native mode - project path set by run.py environment variables
        display_project_info_in_sidebar()
        
        # Quick Start functionality - only show for projects without workflow state
        if st.session_state.project and not st.session_state.project.has_workflow_state():
            st.subheader("🚀 Project Setup Required")
            st.warning("⚠️ **Action Required**: You must choose how to set up this project before running any steps.")
            
            # Determine default selection based on presence of .db files
            project_path = st.session_state.project.path
            db_files = list(project_path.glob("*.db"))
            has_db_files = len(db_files) > 0
            
            # Pre-select "existing_work" if we have .db files or if explicitly set
            default_index = 1 if (has_db_files or st.session_state.get('setup_with_existing_preselected', False)) else 0
            
            # User choice between new project or existing work
            project_type = st.radio(
                "Choose your situation:",
                options=[
                    "new_project",
                    "existing_work"
                ],
                format_func=lambda x: {
                    "new_project": "🆕 New Project - Start from Step 1",
                    "existing_work": "📋 Existing Work - Some steps completed outside workflow"
                }[x],
                index=default_index,
                key="project_type_selector"
            )
            
            # Clear the pre-selection flag after use
            if 'setup_with_existing_preselected' in st.session_state:
                del st.session_state.setup_with_existing_preselected
            
            if project_type == "new_project":
                if st.button("Start New Workflow", key="start_new_workflow"):
                    # Initialize workflow state with all steps pending
                    for step in st.session_state.project.workflow.steps:
                        st.session_state.project.update_state(step['id'], 'pending')
                    st.success("✅ New workflow initialized! Ready to start from Step 1.")
                    st.rerun()
            
            elif project_type == "existing_work":
                st.info("Select which step you want to start from. Previous steps will be marked as completed outside the workflow.")
                
                # Create dropdown options from workflow steps
                step_options = []
                for step in st.session_state.project.workflow.steps:
                    step_options.append((step['id'], step['name']))
                
                # Dropdown for step selection
                selected_step = st.selectbox(
                    "Start from step:",
                    options=step_options,
                    format_func=lambda x: x[1],  # Display the step name
                    key="quick_start_step_selector"
                )
                
                # Skip to Step button
                if st.button("Skip to This Step", key="skip_to_step_button"):
                    try:
                        result_message = st.session_state.project.skip_to_step(selected_step[0])
                        st.success(f"✅ {result_message}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            st.markdown("---")
        
        # Undo functionality
        if st.session_state.project:
            st.subheader("Workflow Controls")
            
            # Check if undo is possible using chronological completion order
            can_undo = st.session_state.project.state_manager.get_last_completed_step_chronological() is not None
            
            # Undo button with confirmation
            if st.session_state.get('undo_confirmation', False):
                st.warning("⚠️ This will revert to the previous step state and cannot be undone!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Undo", key="confirm_undo"):
                        success, err = perform_undo(st.session_state.project)
                        st.session_state.undo_confirmation = False
                        if success:
                            st.success("✅ Undo completed!")
                            st.rerun()
                        else:
                            # Surface the failure as a persistent critical alert so it
                            # survives the st.rerun() and stays visible until dismissed.
                            # Both RollbackError (structured) and plain string errors
                            # are stored in critical_rollback_alert — never shown via
                            # st.error() which would be wiped by the rerun.
                            if isinstance(err, RollbackError):
                                st.session_state.critical_rollback_alert = {
                                    "context": "manual_undo",
                                    "step_id": err.step_id,
                                    "run_number": err.run_number,
                                    "reason": err.reason,
                                }
                            else:
                                # Plain string error (e.g. "No snapshot found" or
                                # "Step not found in workflow") — store as alert too
                                last_step_id = (
                                    st.session_state.project.state_manager
                                    .get_last_completed_step_chronological()
                                    or "unknown"
                                )
                                st.session_state.critical_rollback_alert = {
                                    "context": "manual_undo",
                                    "step_id": last_step_id,
                                    "run_number": 0,
                                    "reason": str(err),
                                }
                            st.rerun()
                with col2:
                    if st.button("❌ Cancel", key="cancel_undo"):
                        st.session_state.undo_confirmation = False
                        st.rerun()
            else:
                if st.button("↶ Undo Last Step", key="undo_button", disabled=not can_undo):
                    st.session_state.undo_confirmation = True
                    st.rerun()
            
            if not can_undo:
                st.caption("No completed steps to undo")
        
        
        # Shutdown functionality
        st.subheader("Application")
        if st.button("Shut Down Workflow Manager", key="shutdown_app", type="primary", help="Stop the native application"):
            st.warning("⚠️ Shutting down the application...")
            st.info("💡 Terminating Streamlit...")
            
            # Native shutdown logic
            try:
                import os
                import signal
                import platform
                
                def delayed_shutdown():
                    """Shutdown the application after a short delay to allow the response to be sent."""
                    time.sleep(1)  # Give time for the response to be sent to browser
                    
                    try:
                        import psutil
                        # Find all streamlit processes
                        streamlit_processes = []
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                            try:
                                if proc.info['cmdline'] and any('streamlit' in str(arg).lower() for arg in proc.info['cmdline']):
                                    streamlit_processes.append(proc)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        
                        # Terminate all streamlit processes gracefully
                        for proc in streamlit_processes:
                            try:
                                proc.terminate()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        
                        # Wait for processes to terminate
                        gone, alive = psutil.wait_procs(streamlit_processes, timeout=3)
                        
                        # Force kill any remaining processes
                        for proc in alive:
                            try:
                                proc.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        
                    except ImportError:
                        # psutil not available, fall back to platform-specific methods
                        system = platform.system().lower()
                        
                        if system in ['linux', 'darwin']:  # macOS/Linux
                            subprocess.run(["pkill", "-f", "streamlit"], check=False)
                            time.sleep(0.5)
                            os.kill(os.getpid(), signal.SIGTERM)
                        elif system == 'windows':  # Windows
                            subprocess.run(["taskkill", "/f", "/im", "python.exe", "/fi", "COMMANDLINE eq *streamlit*"], check=False)
                            time.sleep(0.5)
                            os.kill(os.getpid(), signal.SIGTERM)
                    except Exception:
                        # Last resort: force exit
                        os._exit(0)
                
                # Start shutdown in background thread
                shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
                shutdown_thread.start()
                
                st.success("✅ Application shutdown initiated! Browser connection will be lost shortly.")
                st.info("You can close this browser tab.")
                
            except Exception as e:
                st.error(f"❌ Could not shutdown application automatically: {e}")
                st.info("💡 **Manual shutdown required:**")
                st.info("Use Ctrl+C in the terminal where you started the application")
            
            # Stop the Streamlit script execution
            st.stop()

    if st.session_state.project_path and not st.session_state.project:
        project_path = st.session_state.project_path
        workflow_file = project_path / "workflow.yml"

        # Check for missing workflow files
        workflow_state_file = project_path / "workflow_state.json"
        missing_workflow_yml = not workflow_file.is_file()
        missing_workflow_state = not workflow_state_file.is_file()
        db_files = list(project_path.glob("*.db"))
        
        has_db_files = len(db_files) > 0
        
        # Determine which scenario we're in and handle accordingly
        if missing_workflow_yml and missing_workflow_state and not has_db_files:
            # Scenario 1: No .db, No .yml, No .json - New Project
            st.info("This looks like a new project.")
            st.warning("A `workflow.yml` file was not found in the selected directory.")
            if st.button("🆕 Create New Project", key="create_new_project"):
                try:
                    # Read the content from the appropriate workflow template based on WORKFLOW_TYPE
                    template_workflow_path = get_workflow_template_path()
                    default_workflow_content = template_workflow_path.read_text()
                    with open(workflow_file, "w") as f:
                        f.write(default_workflow_content)
                    
                    workflow_type = get_workflow_type_display()
                    st.success(f"✅ Created a new {workflow_type} workflow.yml from template.")
                    
                    # Load the project immediately
                    try:
                        st.session_state.project = Project(project_path, script_path=get_script_path())
                        st.success("🎉 New project loaded! Ready to start from Step 1.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading project: {e}")
                        return
                except Exception as e:
                    st.error(f"Could not create workflow.yml: {e}")
        
        elif not missing_workflow_yml and missing_workflow_state and not has_db_files:
            # Scenario 2: No .db, Has .yml, No .json - Load as new project
            try:
                # Validate workflow file before loading
                is_valid, error_message = validate_workflow_yaml(workflow_file)
                if not is_valid:
                    st.error(f"❌ **Workflow Validation Failed**: {error_message}")
                    return
                
                # Load the project directly
                st.session_state.project = Project(project_path, script_path=get_script_path())
                st.success(f"✅ Loaded: {st.session_state.project.path.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading project: {e}")
                return
        
        elif not missing_workflow_yml and not missing_workflow_state and not has_db_files:
            # Scenario 3: No .db, Has .yml, Has .json - Check consistency
            try:
                # Load the workflow state to check for completed steps
                with open(workflow_state_file, 'r') as f:
                    state_data = json.load(f)
                
                # Check if any steps are marked as completed or skipped
                # Filter out the _completion_order array which is not a step status
                completed_steps = [step_id for step_id, status in state_data.items()
                                 if step_id != '_completion_order' and status == 'completed']
                skipped_steps = [step_id for step_id, status in state_data.items()
                               if step_id != '_completion_order' and status == 'skipped']
                
                if completed_steps or skipped_steps:
                    # Inconsistent state - steps marked as completed/skipped but no .db files
                    st.error("❌ **INCONSISTENT STATE DETECTED**")
                    if completed_steps:
                        st.error("🚨 **ERROR**: Steps are marked as completed in workflow_state.json but no database files (.db) were found.")
                    if skipped_steps:
                        st.error("🚨 **ERROR**: Steps are marked as skipped in workflow_state.json but no database files (.db) were found.")
                    st.warning("This indicates that database files may have been deleted or moved.")
                    st.info("💡 **SOLUTION**: Please restore the missing .db files offline before proceeding.")
                    
                    problem_steps = completed_steps + skipped_steps
                    st.info(f"**Problem steps found**: {', '.join(problem_steps)}")
                    return  # Don't proceed with loading
                else:
                    # All steps are pending - consistent state, load normally
                    try:
                        # Validate workflow file before loading
                        is_valid, error_message = validate_workflow_yaml(workflow_file)
                        if not is_valid:
                            st.error(f"❌ **Workflow Validation Failed**: {error_message}")
                            return
                        
                        # Load the project directly
                        st.session_state.project = Project(project_path, script_path=get_script_path())
                        st.success(f"✅ Loaded: {st.session_state.project.path.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading project: {e}")
                        return
                    
            except (json.JSONDecodeError, FileNotFoundError) as e:
                st.error(f"❌ Error reading workflow_state.json: {e}")
                return
        
        elif (missing_workflow_yml or missing_workflow_state) and has_db_files:
            # Scenarios 4, 5, 6: Has .db files but missing workflow files
            if missing_workflow_yml and not missing_workflow_state:
                # Scenario 6: Has .db, No .yml, Has .json - Unusual situation
                st.error("⚠️ **UNUSUAL SITUATION DETECTED**")
                st.warning("🚨 **WARNING**: Your project has database files and workflow state, but the workflow.yml file is missing!")
                st.warning("This is an unusual situation that suggests the workflow.yml file may have been accidentally deleted.")
                st.info("💡 **STRONGLY RECOMMENDED**: Try to restore the workflow.yml file from snapshots first.")
            else:
                # Scenarios 4, 5: Normal missing files with .db present
                st.warning("⚠️ **Project appears to be underway but is missing workflow state files**")
            
            missing_files = []
            if missing_workflow_yml:
                missing_files.append("workflow.yml")
            if missing_workflow_state:
                missing_files.append("workflow_state.json")
            
            st.info(f"Missing files: {', '.join(missing_files)}")
            st.info("💡 **Choose how to proceed:**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔧 Try Restore from Snapshots", key="try_restore"):
                    try:
                        project_for_restore = Project(project_path, script_path=get_script_path(), load_workflow=False)
                        restored_any = False
                        
                        if missing_workflow_yml:
                            restored = project_for_restore.snapshot_manager.restore_file_from_latest_snapshot("workflow.yml")
                            if restored:
                                st.success("✅ Restored workflow.yml from snapshot")
                                restored_any = True
                            else:
                                st.error("❌ Could not restore workflow.yml from snapshots")
                        
                        if missing_workflow_state:
                            restored = project_for_restore.snapshot_manager.restore_file_from_latest_snapshot("workflow_state.json")
                            if restored:
                                st.success("✅ Restored workflow_state.json from snapshot")
                                restored_any = True
                            else:
                                st.error("❌ Could not restore workflow_state.json from snapshots")
                        
                        if restored_any:
                            st.success("🎉 Restoration completed! The page will now reload.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            # Set flag to show project setup after failed restoration
                            st.session_state.restoration_failed = True
                            st.session_state.has_db_files_for_setup = True  # Remember we have .db files
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ An error occurred during restoration: {e}")
                        st.info("Proceeding to project setup...")
                        st.session_state.show_project_setup_after_failed_restore = True
                        st.session_state.has_db_files_for_setup = True  # Remember we have .db files
                        time.sleep(2)
                        st.rerun()
                st.caption("Attempt to restore missing files from project snapshots")
            
            with col2:
                if st.button("📋 Set Up Project", key="setup_project"):
                    try:
                        # Only create workflow.yml if it's missing
                        if missing_workflow_yml:
                            try:
                                template_workflow_path = get_workflow_template_path()
                                default_workflow_content = template_workflow_path.read_text()
                                with open(workflow_file, "w") as f:
                                    f.write(default_workflow_content)
                                
                                workflow_type = get_workflow_type_display()
                                st.success(f"✅ Created {workflow_type} workflow.yml from template")
                            except (ValueError, FileNotFoundError) as e:
                                st.error(f"❌ **Template Error**: {e}")
                                return
                        else:
                            st.info("✅ workflow.yml already exists")
                        
                        # Now that workflow.yml exists, load the project directly
                        try:
                            # Validate workflow file before loading
                            is_valid, error_message = validate_workflow_yaml(workflow_file)
                            if not is_valid:
                                st.error(f"❌ **Workflow Validation Failed**: {error_message}")
                                return
                            
                            # Load the project and set flag for existing work pre-selection
                            st.session_state.project = Project(project_path, script_path=get_script_path())
                            st.session_state.setup_with_existing_preselected = True
                            st.success("🎉 Project loaded! Please choose your setup option in the sidebar.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading project: {e}")
                            return
                        
                    except Exception as e:
                        st.error(f"Could not set up project: {e}")
                st.caption("Create missing files and set up project workflow")
            
            # Handle failed restoration - show setup option after restoration fails
            if st.session_state.get('restoration_failed', False):
                st.session_state.restoration_failed = False
                st.error("❌ **Restoration failed** - No snapshots available.")
                st.info("💡 **Proceeding to project setup...**")
                
                if st.button("📋 Continue with Project Setup", key="continue_setup_after_failed_restore"):
                    try:
                        # Create workflow.yml from template if missing
                        if missing_workflow_yml:
                            try:
                                template_workflow_path = get_workflow_template_path()
                                default_workflow_content = template_workflow_path.read_text()
                                with open(workflow_file, "w") as f:
                                    f.write(default_workflow_content)
                                
                                workflow_type = get_workflow_type_display()
                                st.success(f"✅ Created {workflow_type} workflow.yml from template")
                                
                                # Now load the project directly
                                try:
                                    # Validate workflow file before loading
                                    is_valid, error_message = validate_workflow_yaml(workflow_file)
                                    if not is_valid:
                                        st.error(f"❌ **Workflow Validation Failed**: {error_message}")
                                        return
                                    
                                    # Load the project and set flag for existing work pre-selection
                                    st.session_state.project = Project(project_path, script_path=get_script_path())
                                    st.session_state.setup_with_existing_preselected = True
                                    st.success("🎉 Project loaded! Please choose your setup option in the sidebar.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error loading project: {e}")
                                    return
                            except (ValueError, FileNotFoundError) as e:
                                st.error(f"❌ **Template Error**: {e}")
                    except Exception as e:
                        st.error(f"Could not create workflow.yml: {e}")

        else:
            # Scenario 7: Has .db, Has .yml, Has .json - Normal project, load directly
            # Validate workflow file before loading
            is_valid, error_message = validate_workflow_yaml(workflow_file)
            if not is_valid:
                st.error(f"❌ **Workflow Validation Failed**: {error_message}")
                st.info("💡 **Recovery Options:**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔧 Try to Restore from Snapshot"):
                        try:
                            project_for_restore = Project(project_path, script_path=get_script_path(), load_workflow=False)
                            restored = project_for_restore.snapshot_manager.restore_file_from_latest_snapshot("workflow.yml")
                            if restored:
                                st.success("✅ Restored workflow.yml from snapshot!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("No snapshot available to restore from.")
                        except Exception as e:
                            st.error(f"Restore failed: {e}")
                with col2:
                    if st.button("📋 Replace with Template"):
                        try:
                            template_path = get_workflow_template_path()
                            shutil.copy2(template_path, workflow_file)
                            
                            workflow_type = get_workflow_type_display()
                            st.success(f"✅ Replaced with clean {workflow_type} template!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Template replacement failed: {e}")
            else:
                try:
                    st.session_state.project = Project(project_path, script_path=get_script_path())
                    st.success(f"✅ Loaded: {st.session_state.project.path.name}")
                    # Trigger rerun so sidebar re-renders with undo button if there are completed steps
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading project: {e}")
                    st.session_state.project = None

    # --- Main Content Area ---
    # Update functionality removed - all updates handled by run.py before application launch
    
    if not st.session_state.project:
        st.info("Select a project folder using the 'Browse' button in the sidebar.")
    else:
        project = st.session_state.project

        # ---------------------------------------------------------------
        # CRITICAL ROLLBACK FAILURE ALERT
        # Shown persistently at the top of the page until dismissed.
        # This fires when an automatic rollback (script failure) or a
        # manual undo fails to restore the project folder.
        # ---------------------------------------------------------------
        if st.session_state.critical_rollback_alert:
            alert = st.session_state.critical_rollback_alert
            context = alert.get("context", "rollback")
            step_id = alert.get("step_id", "unknown")
            run_number = alert.get("run_number", 0)
            reason = alert.get("reason", "Unknown error")

            context_label = {
                "auto_rollback": "AUTOMATIC ROLLBACK AFTER SCRIPT FAILURE",
                "manual_undo": "MANUAL UNDO",
                "terminate": "SCRIPT TERMINATION ROLLBACK",
            }.get(context, "ROLLBACK")

            st.error(
                f"🚨 **CRITICAL: {context_label} FAILED**\n\n"
                f"**Step**: `{step_id}`  |  **Run**: {run_number}\n\n"
                f"**Reason**: {reason}\n\n"
                "---\n"
                "⚠️ **The project folder may be in an inconsistent state.** "
                "Some files may have been added or modified by the failed script "
                "but could not be removed by the rollback.\n\n"
                "**What to do:**\n"
                "1. Do NOT run any further workflow steps until this is resolved.\n"
                "2. Check the rollback log at `.workflow_logs/rollback.log` inside "
                "your project folder for details on what was attempted.\n"
                "3. Manually inspect the project folder and compare it against the "
                "last known good state (check `.snapshots/` for any remaining ZIP files).\n"
                "4. If you cannot restore manually, contact your system administrator "
                "or restore the project folder from an external backup."
            )
            if st.button("✅ I understand — dismiss this alert", key="dismiss_rollback_alert"):
                st.session_state.critical_rollback_alert = None
                st.rerun()
            st.markdown("---")

        # Display project folder name prominently beneath the main header
        st.markdown(f"## 📁 {project.path.name}")

        # --- Terminal Output and Interaction ---
        # Show terminal for running scripts
        if st.session_state.running_step_id:
            # Make terminal very prominent with visual indicators
            running_step = project.workflow.get_step_by_id(st.session_state.running_step_id)
            
            # Large, prominent header
            st.markdown("# 🖥️ LIVE TERMINAL")
            st.warning(f"⏳ **SCRIPT RUNNING**: {running_step['name'] if running_step else 'Unknown Step'}")
            st.markdown("""
            <div style="background-color: #e6d7ff; padding: 10px; border-radius: 5px; border-left: 5px solid #9966cc; color: #4a4a4a;">
                👇 <strong>INTERACTIVE INPUT</strong>: Please respond to prompts below
            </div>
            """, unsafe_allow_html=True)
            
            # Terminal with prominent styling - use st.code for better real-time updates
            st.subheader("Terminal Output")
            terminal_container = st.container()
            with terminal_container:
                if st.session_state.terminal_output:
                    st.code(st.session_state.terminal_output, language=None)
                else:
                    st.text("Waiting for script output...")
            
            # Input section for terminal
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                user_input = st.text_input(
                    "Input:",
                    key="terminal_input_box",
                    help="Type your input and click 'Send Input' button",
                    placeholder="Type your input here..."
                )
            with col2:
                send_button = st.button(
                    "Send Input",
                    key="send_terminal_input",
                    on_click=send_and_clear_input,
                    args=(project, user_input)
                )
            with col3:
                if st.button(
                    "🛑 Terminate",
                    key="terminate_script",
                    type="secondary",
                    help="Stop the running script and rollback to before it started"
                ):
                    try:
                        terminated = project.terminate_script(st.session_state.running_step_id)
                        if terminated:
                            st.session_state.running_step_id = None
                            st.session_state.terminal_output = ""
                            st.success("✅ Script terminated and project rolled back!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to terminate script — no script was running.")
                    except RollbackError as rollback_err:
                        log_error(
                            "Rollback failed after script termination — storing critical alert",
                            step_id=rollback_err.step_id,
                            run_number=rollback_err.run_number,
                            reason=rollback_err.reason,
                        )
                        st.session_state.critical_rollback_alert = {
                            "context": "terminate",
                            "step_id": rollback_err.step_id,
                            "run_number": rollback_err.run_number,
                            "reason": rollback_err.reason,
                        }
                        st.session_state.running_step_id = None
                        st.session_state.terminal_output = ""
                        st.rerun()
            
        
        # Show terminal for running auxiliary scripts
        elif st.session_state.running_auxiliary_id:
            aux_id = st.session_state.running_auxiliary_id
            aux_script = project.workflow.get_auxiliary_script_by_id(aux_id)

            st.markdown("# 🖥️ LIVE TERMINAL")
            st.warning(f"⏳ **AUXILIARY SCRIPT RUNNING**: {aux_script['name'] if aux_script else aux_id}")
            st.markdown("""
            <div style="background-color: #e6d7ff; padding: 10px; border-radius: 5px; border-left: 5px solid #9966cc; color: #4a4a4a;">
                👇 <strong>AUXILIARY TOOL</strong>: Running — does not affect workflow state
            </div>
            """, unsafe_allow_html=True)

            st.subheader("Terminal Output")
            if st.session_state.terminal_output:
                st.code(st.session_state.terminal_output, language=None)
            else:
                st.text("Waiting for script output...")

            # Input section for auxiliary terminal (same as workflow step terminal)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                user_input = st.text_input(
                    "Input:",
                    key="aux_terminal_input_box",
                    help="Type your input and click 'Send Input' button",
                    placeholder="Type your input here..."
                )
            with col2:
                st.button(
                    "Send Input",
                    key="send_aux_terminal_input",
                    on_click=send_and_clear_input,
                    args=(project, user_input)
                )
            with col3:
                if st.button(
                    "🛑 Terminate",
                    key="terminate_auxiliary_script",
                    type="secondary",
                    help="Stop the auxiliary script and rollback any partial changes"
                ):
                    try:
                        project.script_runner.terminate()
                        # Rollback from the pre-run snapshot if one exists
                        if project.snapshot_manager.snapshot_exists(aux_id, 1):
                            project.snapshot_manager.restore_snapshot(aux_id, 1)
                            project.snapshot_manager.remove_run_snapshots_from(aux_id, 1)
                        # Clean up manifest
                        manifest_path = (
                            project.snapshot_manager.snapshots_dir
                            / f"{aux_id}_run_1_manifest.json"
                        )
                        if manifest_path.exists():
                            manifest_path.unlink()
                        st.session_state.running_auxiliary_id = None
                        st.session_state.terminal_output = ""
                        st.success("✅ Auxiliary script terminated and changes rolled back.")
                        st.rerun()
                    except RollbackError as rollback_err:
                        st.session_state.critical_rollback_alert = {
                            "context": "terminate",
                            "step_id": aux_id,
                            "run_number": 1,
                            "reason": rollback_err.reason,
                        }
                        st.session_state.running_auxiliary_id = None
                        st.session_state.terminal_output = ""
                        st.rerun()

        # Show terminal for completed scripts
        elif st.session_state.completed_script_output and st.session_state.completed_script_step:
            completed_step = project.workflow.get_step_by_id(st.session_state.completed_script_step)
            
            # Header for completed script
            st.markdown("# 📋 COMPLETED SCRIPT OUTPUT")
            if st.session_state.completed_script_success:
                st.success(f"✅ **SCRIPT COMPLETED**: {completed_step['name'] if completed_step else 'Unknown Step'}")
            else:
                st.error(f"❌ **SCRIPT FAILED**: {completed_step['name'] if completed_step else 'Unknown Step'}")
            
            # Show completed output - use st.code for consistency with running terminal
            st.subheader("Script Output")
            completed_container = st.container()
            with completed_container:
                if st.session_state.completed_script_output:
                    st.code(st.session_state.completed_script_output, language=None)
                else:
                    st.text("No output captured.")
            
            # Clear button
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("Clear Output", key="clear_completed_output"):
                    st.session_state.completed_script_output = ""
                    st.session_state.completed_script_step = None
                    st.session_state.completed_script_success = None
                    st.rerun()
        
        st.markdown("---")

        # --- Workflow Steps Display ---
        first_pending_step = next((step for step in project.workflow.steps if project.get_state(step['id']) == 'pending'), None)

        for i, step in enumerate(project.workflow.steps):
            step_id = step['id']
            step_name = step['name']
            status = project.get_state(step_id)
            
            is_running_this_step = st.session_state.running_step_id == step_id
            
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                if is_running_this_step:
                    st.warning(f"⏳ {step_name} (Running...)")  # Changed to warning for visibility
                elif status == "completed":
                    if step.get('allow_rerun', False):
                        run_count = get_script_run_count(project, step_id)
                        # Light green styling for re-runnable completed steps
                        st.markdown(f"""
                        <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #28a745;">
                            🔄 {step_name} (Run #{run_count})
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.success(f"✅ {step_name}")  # Standard green for non-rerunnable
                elif status == "skipped":
                    # Gray styling for skipped steps
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; color: #6c757d;">
                        ⏩ {step_name} - Completed outside workflow
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"⚪ {step_name}")

                # Input widgets - shown for pending steps and completed steps that allow re-runs
                show_inputs = False
                if 'inputs' in step and not is_running_this_step:
                    if status == 'pending':
                        show_inputs = True
                    elif status == 'completed' and step.get('allow_rerun', False):
                        show_inputs = True
                
                if show_inputs:
                    st.session_state.user_inputs.setdefault(step_id, {})
                    
                    # For completed steps that allow re-runs, show a note about re-run inputs
                    if status == 'completed' and step.get('allow_rerun', False):
                        st.info("💡 **Re-run Setup**: Please select input files for this re-run.")
                    
                    for i, input_def in enumerate(step['inputs']):
                        input_key = f"{step_id}_input_{i}"
                        if input_def['type'] == 'file':
                            # Initialize browser state key
                            browser_state_key = f"show_browser_{input_key}"
                            if browser_state_key not in st.session_state:
                                st.session_state[browser_state_key] = False
                            
                            # Show current selection if any
                            current_value = st.session_state.user_inputs[step_id].get(input_key, "")
                            if current_value:
                                st.success(f"✅ **{input_def['name']}**: `{Path(current_value).name}`")
                                st.text(f"📍 Full path: {current_value}")
                                col_clear, col_change = st.columns([1, 1])
                                with col_clear:
                                    if st.button("Clear Selection", key=f"clear_{input_key}"):
                                        # Clear all related state
                                        browser_selected_key = f"selected_file_{input_key}"
                                        st.session_state.user_inputs[step_id][input_key] = ""
                                        if browser_selected_key in st.session_state:
                                            st.session_state[browser_selected_key] = None
                                        st.session_state[browser_state_key] = False
                                        st.rerun()
                                with col_change:
                                    if st.button("Change File", key=f"change_{input_key}"):
                                        # Clear current selection and show browser
                                        browser_selected_key = f"selected_file_{input_key}"
                                        st.session_state.user_inputs[step_id][input_key] = ""
                                        if browser_selected_key in st.session_state:
                                            st.session_state[browser_selected_key] = None
                                        st.session_state[browser_state_key] = True
                                        st.rerun()
                            else:
                                st.info(f"📄 **{input_def['name']}**: No file selected")
                                if st.button("Select File", key=f"select_{input_key}"):
                                    st.session_state[browser_state_key] = True
                                    st.rerun()
                            
                            # Show inline file browser when browser state is True
                            if st.session_state[browser_state_key]:
                                with st.expander("📁 File Browser", expanded=True):
                                    selected_file = create_inline_file_browser(input_key)
                                    
                                    if selected_file:
                                        st.session_state.user_inputs[step_id][input_key] = selected_file
                                        st.session_state[browser_state_key] = False
                                        st.success(f"✅ File selected: {Path(selected_file).name}")
                                        st.rerun()
                                    
                                    if st.button("Cancel", key=f"cancel_{input_key}"):
                                        st.session_state[browser_state_key] = False
                                        st.rerun()

            with col2:
                # Regular Run/Re-run buttons logic
                    run_button_disabled = st.session_state.running_step_id is not None
                    
                    # Show Re-run button for completed steps that allow re-runs
                    if status == "completed" and step.get('allow_rerun', False):
                        # Check if all required inputs for re-run are filled
                        rerun_button_disabled = run_button_disabled
                        if 'inputs' in step:
                            step_inputs = st.session_state.user_inputs.get(step_id, {})
                            required_inputs = step['inputs']
                            if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
                                rerun_button_disabled = True
                        
                        # Additional check: disable if project setup is not complete
                        if not project.has_workflow_state():
                            rerun_button_disabled = True
                        
                        # Enhanced button text with run count
                        run_count = get_script_run_count(project, step_id)
                        button_text = f"Re-run (#{run_count + 1})"
                        
                        if st.button(button_text, key=f"rerun_{step_id}", disabled=rerun_button_disabled):
                            st.session_state.running_step_id = step_id
                            st.session_state.terminal_output = ""
                            step_user_inputs = st.session_state.user_inputs.get(step_id, {})
                            start_script_thread(project, step_id, step_user_inputs)
                            st.rerun()  # Force immediate rerun to show terminal
                    
                    # Show Run button for pending steps (or all steps if they're the next step)
                    if status not in ["completed"]:
                        is_next_step = (step_id == first_pending_step['id']) if first_pending_step else False
                        if not is_next_step:
                            run_button_disabled = True
                        
                        # Check if all required inputs for this step are filled
                        # Check if all required inputs for this step are filled
                        # The button is disabled if the step has inputs and they are not all filled
                        if 'inputs' in step and step['inputs']:
                            step_inputs = st.session_state.user_inputs.get(step_id, {})
                            required_inputs = step['inputs']
                            if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
                                run_button_disabled = True
                        # If 'inputs' is not in step or is empty, the button should be enabled by default
                        
                        # Additional check: disable if project setup is not complete
                        if not project.has_workflow_state():
                            run_button_disabled = True

                        if st.button("Run", key=f"run_{step_id}", disabled=run_button_disabled):
                            st.session_state.running_step_id = step_id
                            st.session_state.terminal_output = ""
                            step_user_inputs = st.session_state.user_inputs.get(step_id, {})
                            start_script_thread(project, step_id, step_user_inputs)
                            st.rerun()  # Force immediate rerun to show terminal
            
            # ... (rest of the step display logic) ...
            st.markdown("---")

        # --- Auxiliary Tools Section ---
        aux_scripts = project.workflow.auxiliary_scripts
        if aux_scripts:
            st.markdown("## 🔧 Auxiliary Tools")
            st.caption(
                "These scripts can be run at any time and do not affect the workflow state. "
                "On failure, changes are automatically rolled back."
            )
            st.markdown("---")

            for aux in aux_scripts:
                aux_id = aux['id']
                aux_name = aux['name']
                is_running_this_aux = st.session_state.running_auxiliary_id == aux_id

                col1, col2 = st.columns([4, 1])
                with col1:
                    if is_running_this_aux:
                        st.warning(f"⏳ {aux_name} (Running...)")
                    else:
                        st.info(f"🔧 {aux_name}")

                with col2:
                    # Disable if any script (workflow or auxiliary) is currently running
                    launch_disabled = (
                        st.session_state.running_step_id is not None or
                        st.session_state.running_auxiliary_id is not None or
                        not project.has_workflow_state()
                    )
                    if st.button("Launch", key=f"aux_{aux_id}", disabled=launch_disabled):
                        st.session_state.running_auxiliary_id = aux_id
                        st.session_state.terminal_output = ""
                        thread = threading.Thread(
                            target=lambda aid=aux_id: project.run_auxiliary_script(aid)
                        )
                        st.session_state['script_thread'] = thread
                        thread.start()
                        st.rerun()

                st.markdown("---")

    # --- Background Loop for UI Updates & Final Result Processing ---
    if st.session_state.project:
        # Simple polling for both output and completion
        if st.session_state.running_step_id:
            runner = st.session_state.project.script_runner
            
            # Simple output polling without excessive reruns
            output_received = False
            while True:
                try:
                    output = runner.output_queue.get_nowait()
                    if output is not None:
                        st.session_state.terminal_output += output
                        output_received = True
                    else:
                        break  # Sentinel value received
                except queue.Empty:
                    break  # No more output available
            
            # Only rerun if we received output (minimal reruns)
            if output_received:
                st.rerun()

            # Poll for the final result
            try:
                result = runner.result_queue.get_nowait()
                
                # Script is done - handle the result
                step_id = st.session_state.running_step_id
                
                # Use the handle_step_result method which includes rollback logic.
                # If an automatic rollback fails, handle_step_result() raises
                # RollbackError — catch it and store a persistent critical alert.
                try:
                    st.session_state.project.handle_step_result(step_id, result)
                except RollbackError as rollback_err:
                    log_error(
                        "Automatic rollback failed after script failure — storing critical alert",
                        step_id=step_id,
                        run_number=rollback_err.run_number,
                        reason=rollback_err.reason,
                    )
                    st.session_state.critical_rollback_alert = {
                        "context": "auto_rollback",
                        "step_id": rollback_err.step_id,
                        "run_number": rollback_err.run_number,
                        "reason": rollback_err.reason,
                    }
                    # Mark the step as failed/inconsistent so the UI reflects reality
                    st.session_state.project.update_state(step_id, "pending")

                # Preserve the terminal output for completed script display.
                # Use the post-handle_step_result state to determine success — NOT
                # result.success (raw exit code).  A script can exit with code 0
                # (sys.exit() with no argument) but still fail the two-factor check
                # (exit code OK but no success marker written), in which case
                # handle_step_result() performs rollback and leaves the step as
                # "pending".  Showing "✅ SCRIPT COMPLETED" in that case is wrong.
                actual_step_success = (
                    st.session_state.project.get_state(step_id) == "completed"
                )
                st.session_state.completed_script_output = st.session_state.terminal_output
                st.session_state.completed_script_step = step_id
                st.session_state.completed_script_success = actual_step_success

                st.session_state.last_run_result = {"step_name": st.session_state.project.workflow.get_step_by_id(step_id)['name'], **result.__dict__}
                st.session_state.running_step_id = None
                st.session_state.redo_stack = []
                st.rerun()

            except queue.Empty:
                # Script still running - schedule a simple rerun to continue polling
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                st.rerun()

        # Poll for auxiliary script output and completion
        elif st.session_state.running_auxiliary_id:
            runner = st.session_state.project.script_runner
            aux_id = st.session_state.running_auxiliary_id

            # Poll for output (same pattern as workflow steps)
            output_received = False
            while True:
                try:
                    output = runner.output_queue.get_nowait()
                    if output is not None:
                        st.session_state.terminal_output += output
                        output_received = True
                    else:
                        break  # Sentinel value received
                except queue.Empty:
                    break

            if output_received:
                st.rerun()

            # Poll for the final result
            try:
                result = runner.result_queue.get_nowait()

                # Handle the result — no workflow state changes
                try:
                    st.session_state.project.handle_auxiliary_result(aux_id, result)
                except RollbackError as rollback_err:
                    log_error(
                        "Auxiliary script rollback failed — storing critical alert",
                        aux_id=aux_id,
                        reason=rollback_err.reason,
                    )
                    st.session_state.critical_rollback_alert = {
                        "context": "auto_rollback",
                        "step_id": aux_id,
                        "run_number": 1,
                        "reason": rollback_err.reason,
                    }

                # Preserve terminal output for completed display.
                # Use result.success directly — there is no workflow state to check.
                actual_success = result.success
                st.session_state.completed_script_output = st.session_state.terminal_output
                st.session_state.completed_script_step = aux_id
                st.session_state.completed_script_success = actual_success

                st.session_state.running_auxiliary_id = None
                st.rerun()

            except queue.Empty:
                # Auxiliary script still running — keep polling
                time.sleep(0.1)
                st.rerun()


if __name__ == "__main__":
    main()