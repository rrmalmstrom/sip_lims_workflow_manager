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
from src.core import Project
from src.logic import RunResult
from src.git_update_manager import create_update_managers
import argparse

def parse_script_path_argument():
    """
    Parse command line arguments to get script path.
    Uses argparse to handle Streamlit's argument passing format.
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

# Initialize script path globally and resolve to an absolute path
SCRIPT_PATH = parse_script_path_argument().resolve()

# --- Page Configuration ---
st.set_page_config(page_title="SIP LIMS Workflow Manager", page_icon="🧪", layout="wide")

import streamlit.components.v1 as components

# --- Terminal Configuration ---
TERMINAL_HEIGHT = 450  # Reduced height for better screen utilization

# --- Helper Functions ---
@st.cache_data(ttl=3600)  # Cache for 60 minutes
def check_for_updates(script_path: Path):
    """
    Check for updates for both the application and the scripts.
    Uses a single factory to get both managers and returns a consolidated result.
    """
    results = {
        'app': {'error': 'Check not performed'},
        'scripts': {'error': 'Check not performed'}
    }
    try:
        managers = create_update_managers(script_path=script_path)
        results['app'] = managers['app'].check_for_updates()
        results['scripts'] = managers['scripts'].check_for_updates()
    except Exception as e:
        results['app']['error'] = f"Failed to create update managers: {str(e)}"
        results['scripts']['error'] = f"Failed to create update managers: {str(e)}"
    return results

def update_scripts(script_path: Path):
    """Update scripts to the latest version."""
    try:
        # We only need the script manager for this operation
        managers = create_update_managers(script_path=script_path)
        return managers['scripts'].update_to_latest()
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to update scripts: {str(e)}"
        }

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
            
            required_fields = ['id', 'name', 'script']
            for field in required_fields:
                if field not in step:
                    return False, f"Step {i+1} missing required field '{field}'"
        
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

def handle_terminal_input_change():
    """Handle when terminal input changes - triggered by Enter key or other changes."""
    if 'terminal_input_box' in st.session_state and 'project' in st.session_state:
        user_input = st.session_state.terminal_input_box
        # Strip whitespace and newlines to prevent PTY input buffer contamination
        # This fixes the issue where pressing Enter leaves stray newlines that
        # get consumed by subsequent input() calls in the same script
        user_input = user_input.strip() if user_input else ""
        
        # Send input regardless of whether it's empty (for default answers)
        project = st.session_state.project
        if project and project.script_runner.is_running():
            # Prevent double input by checking if we just sent input
            current_time = time.time()
            last_input_time = st.session_state.get('last_input_time', 0)
            
            # Only send if it's been more than 100ms since last input
            if current_time - last_input_time > 0.1:
                project.script_runner.send_input(user_input)
                st.session_state.last_input_time = current_time
                st.session_state.terminal_input_box = ""
                st.session_state.scroll_to_bottom = True

def select_file_via_subprocess():
    python_executable = sys.executable
    script_path = Path(__file__).parent / "utils" / "file_dialog.py"
    process = subprocess.run([python_executable, str(script_path), 'file'], capture_output=True, text=True)
    return process.stdout.strip()

def select_folder_via_subprocess():
    python_executable = sys.executable
    script_path = Path(__file__).parent / "utils" / "file_dialog.py"
    process = subprocess.run([python_executable, str(script_path)], capture_output=True, text=True)
    return process.stdout.strip()

def perform_undo(project):
    """
    Performs undo operation by reverting to the previous completed step state.
    Uses the complete snapshot system for comprehensive rollback.
    Enhanced to handle conditional workflow states properly.
    """
    # Check if there are any conditional steps in "awaiting_decision" state
    # For these, we should undo the trigger step instead of the conditional step
    for step in project.workflow.steps:
        step_id = step['id']
        current_state = project.get_state(step_id)
        
        # Check if this is a conditional step in awaiting_decision state
        if (('conditional' in step) and (current_state == 'awaiting_decision')):
            conditional_config = step.get('conditional', {})
            trigger_script = conditional_config.get('trigger_script')
            
            if trigger_script:
                # Find the step that runs this trigger script
                trigger_step = None
                for workflow_step in project.workflow.steps:
                    if workflow_step.get('script') == trigger_script:
                        trigger_step = workflow_step
                        break
                
                if trigger_step and project.get_state(trigger_step['id']) == 'completed':
                    # Reset the conditional step to pending first
                    project.update_state(step_id, "pending")
                    print(f"UNDO: Reset conditional step {step_id} from awaiting_decision to pending")
                    
                    # Remove the conditional decision snapshot to prevent it from interfering with future undos
                    conditional_decision_snapshot = f"{step_id}_conditional_decision"
                    conditional_snapshot_path = project.snapshot_manager.snapshots_dir / f"{conditional_decision_snapshot}_complete.zip"
                    if conditional_snapshot_path.exists():
                        conditional_snapshot_path.unlink()
                        print(f"UNDO: Removed conditional decision snapshot {conditional_decision_snapshot}")
                    
                    # Now undo the trigger step using regular undo logic
                    trigger_step_id = trigger_step['id']
                    
                    # Find the step index of the trigger step
                    trigger_step_index = next(i for i, s in enumerate(project.workflow.steps) if s['id'] == trigger_step_id)
                    
                    try:
                        # Get the effective current run number for the trigger step
                        effective_run = project.snapshot_manager.get_effective_run_number(trigger_step_id)
                        
                        if effective_run > 1:
                            # Search backwards to find the highest available "after" snapshot
                            target_run = None
                            for run_num in range(effective_run - 1, 0, -1):
                                candidate_snapshot = f"{trigger_step_id}_run_{run_num}_after"
                                if project.snapshot_manager.snapshot_exists(candidate_snapshot):
                                    target_run = run_num
                                    break
                            
                            if target_run:
                                # Restore to the found "after" snapshot
                                target_snapshot = f"{trigger_step_id}_run_{target_run}_after"
                                project.snapshot_manager.restore_complete_snapshot(target_snapshot)
                                # Remove the current run's 'after' snapshot to track that it's been undone
                                project.snapshot_manager.remove_run_snapshots_from(trigger_step_id, effective_run)
                                print(f"UNDO: Restored trigger step {trigger_step_id} to state after run {target_run}")
                                # Step should remain "completed" since we still have a previous run
                                return True
                            else:
                                # No "after" snapshots available for this step, check previous step
                                if trigger_step_index > 0:
                                    # Look for the previous step's latest "after" snapshot
                                    previous_step = project.workflow.steps[trigger_step_index - 1]
                                    previous_step_id = previous_step['id']
                                    previous_effective_run = project.snapshot_manager.get_effective_run_number(previous_step_id)
                                    
                                    if previous_effective_run > 0:
                                        # Restore to previous step's most recent "after" snapshot
                                        previous_after_snapshot = f"{previous_step_id}_run_{previous_effective_run}_after"
                                        if project.snapshot_manager.snapshot_exists(previous_after_snapshot):
                                            project.snapshot_manager.restore_complete_snapshot(previous_after_snapshot)
                                            # Remove current step's "after" snapshot and mark as pending
                                            project.snapshot_manager.remove_run_snapshots_from(trigger_step_id, effective_run)
                                            print(f"UNDO: Restored project to state after {previous_step_id} (run {previous_effective_run})")
                                            # Mark trigger step as pending since we're undoing it completely
                                            script_name = trigger_step.get('script', '').replace('.py', '')
                                            success_marker = project.path / ".workflow_status" / f"{script_name}.success"
                                            if success_marker.exists():
                                                success_marker.unlink()
                                                print(f"UNDO: Removed success marker for {script_name}")
                                            project.update_state(trigger_step_id, "pending")
                                            print(f"UNDO: Marked trigger step {trigger_step_id} as pending")
                                            return True
                                
                                # No previous step or no previous step snapshots, treat as undoing the entire step
                                effective_run = 1  # Fall through to the next condition
                            
                        elif effective_run == 1:
                            # This is the last run - undo the entire trigger step
                            # Use the run 1 "before" snapshot (taken before first run)
                            run_1_before_snapshot = f"{trigger_step_id}_run_1"
                            if project.snapshot_manager.snapshot_exists(run_1_before_snapshot):
                                project.snapshot_manager.restore_complete_snapshot(run_1_before_snapshot)
                                print(f"UNDO: Restored project to state before trigger step {trigger_step_id} ran")
                            else:
                                # Fallback to legacy snapshot naming if run snapshot doesn't exist
                                project.snapshot_manager.restore_complete_snapshot(trigger_step_id)
                                print(f"UNDO: Restored project to state before trigger step {trigger_step_id} ran (legacy)")
                            # Remove all run snapshots since we're undoing the entire step
                            project.snapshot_manager.remove_run_snapshots_from(trigger_step_id, 1)
                            
                            # Handle success marker and step status
                            script_name = trigger_step.get('script', '').replace('.py', '')
                            success_marker = project.path / ".workflow_status" / f"{script_name}.success"
                            if success_marker.exists():
                                success_marker.unlink()
                                print(f"UNDO: Removed success marker for {script_name}")
                            project.update_state(trigger_step_id, "pending")
                            print(f"UNDO: Marked trigger step {trigger_step_id} as pending")
                        else:
                            # No run snapshots exist - fallback to original behavior
                            project.snapshot_manager.restore_complete_snapshot(trigger_step_id)
                            print(f"UNDO: Restored project to state before trigger step {trigger_step_id} ran")
                            # Mark trigger step as pending
                            script_name = trigger_step.get('script', '').replace('.py', '')
                            success_marker = project.path / ".workflow_status" / f"{script_name}.success"
                            if success_marker.exists():
                                success_marker.unlink()
                                print(f"UNDO: Removed success marker for {script_name}")
                            project.update_state(trigger_step_id, "pending")
                            print(f"UNDO: Marked trigger step {trigger_step_id} as pending")
                        
                        return True
                        
                    except FileNotFoundError as e:
                        print(f"UNDO ERROR: {e}")
                        print("Complete snapshot not found for trigger step.")
                        return False
                    except Exception as e:
                        print(f"UNDO ERROR: Unexpected error during trigger step undo: {e}")
                        return False
    
    # Check if there are any conditional steps that were affected by a decision (but not awaiting_decision)
    # These should be undone to their conditional decision point
    for step in project.workflow.steps:
        step_id = step['id']
        current_state = project.get_state(step_id)
        
        # Check if this is a conditional step that was affected by a decision and has a conditional decision snapshot
        if (('conditional' in step) and
            (current_state in ['pending', 'skipped_conditional']) and
            project.snapshot_manager.snapshot_exists(f"{step_id}_conditional_decision")):
            
            # This step was affected by a conditional decision - undo to decision point
            try:
                project.snapshot_manager.restore_complete_snapshot(f"{step_id}_conditional_decision")
                print(f"UNDO: Restored to conditional decision point for step {step_id}")
                return True
            except FileNotFoundError:
                pass  # Fall through to regular undo logic
    
    # Also check if we're on a target step that was activated by skipping a conditional
    # In this case, we should also undo to the conditional decision point
    for step in project.workflow.steps:
        step_id = step['id']
        current_state = project.get_state(step_id)
        
        # If this step is pending and could be a target of a conditional skip
        if current_state == 'pending':
            # Check if any conditional step has this as a target_step and was recently skipped
            for conditional_step in project.workflow.steps:
                if 'conditional' in conditional_step:
                    conditional_config = conditional_step.get('conditional', {})
                    target_step = conditional_config.get('target_step')
                    conditional_step_id = conditional_step['id']
                    conditional_state = project.get_state(conditional_step_id)
                    
                    # If this step is the target of a skipped conditional and decision snapshot exists
                    if (target_step == step_id and
                        conditional_state == 'skipped_conditional' and
                        project.snapshot_manager.snapshot_exists(f"{conditional_step_id}_conditional_decision")):
                        
                        try:
                            project.snapshot_manager.restore_complete_snapshot(f"{conditional_step_id}_conditional_decision")
                            print(f"UNDO: Restored to conditional decision point for step {conditional_step_id} (was target step)")
                            return True
                        except FileNotFoundError:
                            pass  # Fall through to regular undo logic
    
    # Find all completed steps
    completed_steps = []
    for step in project.workflow.steps:
        if project.get_state(step['id']) == 'completed':
            completed_steps.append(step)
    
    if not completed_steps:
        return False  # Nothing to undo
    
    # Get the last completed step
    last_step = completed_steps[-1]
    last_step_id = last_step['id']
    
    # Find the step index
    step_index = next(i for i, s in enumerate(project.workflow.steps) if s['id'] == last_step_id)
    
    try:
        # Get the effective current run number (what we're currently at)
        effective_run = project.snapshot_manager.get_effective_run_number(last_step_id)
        
        if effective_run > 1:
            # Search backwards to find the highest available "after" snapshot
            target_run = None
            for run_num in range(effective_run - 1, 0, -1):
                candidate_snapshot = f"{last_step_id}_run_{run_num}_after"
                if project.snapshot_manager.snapshot_exists(candidate_snapshot):
                    target_run = run_num
                    break
            
            if target_run:
                # Restore to the found "after" snapshot
                target_snapshot = f"{last_step_id}_run_{target_run}_after"
                project.snapshot_manager.restore_complete_snapshot(target_snapshot)
                # Remove the current run's 'after' snapshot to track that it's been undone
                project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
                print(f"UNDO: Restored project to state after run {target_run} of step {last_step_id}")
                # Step should remain "completed" since we still have a previous run
                return True
            else:
                # No "after" snapshots available for this step, check previous step
                if step_index > 0:
                    # Look for the previous step's latest "after" snapshot
                    previous_step = project.workflow.steps[step_index - 1]
                    previous_step_id = previous_step['id']
                    previous_effective_run = project.snapshot_manager.get_effective_run_number(previous_step_id)
                    
                    if previous_effective_run > 0:
                        # Restore to previous step's most recent "after" snapshot
                        previous_after_snapshot = f"{previous_step_id}_run_{previous_effective_run}_after"
                        if project.snapshot_manager.snapshot_exists(previous_after_snapshot):
                            project.snapshot_manager.restore_complete_snapshot(previous_after_snapshot)
                            # Remove current step's "after" snapshot and mark as pending
                            project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
                            print(f"UNDO: Restored project to state after {previous_step_id} (run {previous_effective_run})")
                            # Mark current step as pending since we're undoing it completely
                            script_name = last_step.get('script', '').replace('.py', '')
                            success_marker = project.path / ".workflow_status" / f"{script_name}.success"
                            if success_marker.exists():
                                success_marker.unlink()
                                print(f"UNDO: Removed success marker for {script_name}")
                            project.update_state(last_step_id, "pending")
                            print(f"UNDO: Marked step {last_step_id} as pending")
                            return True
                
                # No previous step or no previous step snapshots, treat as undoing the entire step
                effective_run = 1  # Fall through to the next condition
            
        elif effective_run == 1:
            # This is the last run - undo the entire step
            # Use the run 1 "before" snapshot (taken before first run)
            run_1_before_snapshot = f"{last_step_id}_run_1"
            if project.snapshot_manager.snapshot_exists(run_1_before_snapshot):
                project.snapshot_manager.restore_complete_snapshot(run_1_before_snapshot)
                print(f"UNDO: Restored project to state before step {last_step_id} ran")
            else:
                # Fallback to legacy snapshot naming if run snapshot doesn't exist
                project.snapshot_manager.restore_complete_snapshot(last_step_id)
                print(f"UNDO: Restored project to state before step {last_step_id} ran (legacy)")
            # Remove all run snapshots since we're undoing the entire step
            project.snapshot_manager.remove_run_snapshots_from(last_step_id, 1)
        else:
            # No run snapshots exist - fallback to original behavior
            project.snapshot_manager.restore_complete_snapshot(last_step_id)
            print(f"UNDO: Restored project to state before step {last_step_id} ran")
        
        # Handle success marker and step status based on undo type
        script_name = last_step.get('script', '').replace('.py', '')
        success_marker = project.path / ".workflow_status" / f"{script_name}.success"
        
        # Check the effective run number after undo to determine step status
        effective_run_after_undo = project.snapshot_manager.get_effective_run_number(last_step_id)
        
        if effective_run_after_undo > 0:
            # Granular undo - step should remain "completed" since we still have previous runs
            print(f"UNDO: Step {last_step_id} remains completed (run {effective_run_after_undo} still exists)")
        else:
            # Full step undo - mark as pending and remove success marker
            if success_marker.exists():
                success_marker.unlink()
                print(f"UNDO: Removed success marker for {script_name}")
            project.update_state(last_step_id, "pending")
            print(f"UNDO: Marked step {last_step_id} as pending")
        
        return True
        
    except FileNotFoundError as e:
        print(f"UNDO ERROR: {e}")
        print("Complete snapshot not found. This may be because the step was run before the enhanced snapshot system was implemented.")
        return False
    except Exception as e:
        print(f"UNDO ERROR: Unexpected error during undo: {e}")
        return False

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


# --- Main Application ---
def main():
    st.title("🧪 SIP LIMS Workflow Manager")

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
    if 'conditional_steps_awaiting' not in st.session_state:
        st.session_state.conditional_steps_awaiting = []


    # --- Sidebar ---
    with st.sidebar:
        st.header("Controls")
        
        st.subheader("Project")
        if st.button("Browse for Project Folder", key="browse_button"):
            folder = select_folder_via_subprocess()
            if folder:
                st.session_state.project_path = Path(folder)
                st.session_state.project = None
                st.rerun()
        
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
            
            # Check if undo is possible
            can_undo = False
            for step in st.session_state.project.workflow.steps:
                if st.session_state.project.get_state(step['id']) == 'completed':
                    can_undo = True
                    break
            
            # Undo button with confirmation
            if st.session_state.get('undo_confirmation', False):
                st.warning("⚠️ This will revert to the previous step state and cannot be undone!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Undo", key="confirm_undo"):
                        perform_undo(st.session_state.project)
                        st.session_state.undo_confirmation = False
                        st.success("✅ Undo completed!")
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
        
        # Add permanent update cache clearing option in sidebar
        st.subheader("Updates")
        if st.button("🔄 Manual Check for Updates", key="sidebar_check_updates"):
            check_for_updates.clear()
            st.success("✅ Update cache cleared!")
            st.rerun()
        st.caption("Clears update cache and checks for new versions")
        
        # Shutdown functionality
        st.subheader("Application")
        if st.button("🛑 Shutdown App", key="shutdown_app", type="secondary"):
            st.warning("⚠️ Shutting down the application...")
            st.info("💡 Terminating Streamlit server...")
            
            # Try multiple methods to terminate the process
            try:
                import os
                import signal
                import threading
                import platform
                
                def delayed_shutdown():
                    """Shutdown the process after a short delay to allow the response to be sent."""
                    time.sleep(1)  # Give time for the response to be sent to browser
                    
                    # Try psutil first if available (most reliable cross-platform method)
                    try:
                        import psutil
                        current_process = psutil.Process(os.getpid())
                        
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
                        
                        return  # Success with psutil
                        
                    except ImportError:
                        # psutil not available, fall back to platform-specific methods
                        pass
                    except Exception as e:
                        # psutil failed, fall back to platform-specific methods
                        pass
                    
                    # Fallback methods using standard library
                    try:
                        system = platform.system().lower()
                        
                        if system in ['linux', 'darwin']:  # macOS/Linux
                            # Method 1: Try pkill first (Unix-like systems)
                            subprocess.run(["pkill", "-f", "streamlit"], check=False)
                            time.sleep(0.5)
                            
                            # Method 2: Kill current process with SIGTERM
                            os.kill(os.getpid(), signal.SIGTERM)
                            time.sleep(0.5)
                            
                            # Method 3: Force kill with SIGKILL
                            os.kill(os.getpid(), signal.SIGKILL)
                            
                        elif system == 'windows':  # Windows
                            # Method 1: Try taskkill for streamlit processes
                            subprocess.run(["taskkill", "/f", "/im", "python.exe", "/fi", "COMMANDLINE eq *streamlit*"], check=False)
                            time.sleep(0.5)
                            
                            # Method 2: Kill current process (Windows doesn't have SIGKILL)
                            os.kill(os.getpid(), signal.SIGTERM)
                        
                    except:
                        pass  # Ignore errors, try next method
                    
                    # Last resort: force exit (works on all platforms)
                    try:
                        os._exit(0)
                    except:
                        pass
                
                # Start shutdown in background thread
                shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
                shutdown_thread.start()
                
                st.success("✅ Server shutdown initiated! Browser connection will be lost shortly.")
                st.info("You can close this browser tab.")
                
            except Exception as e:
                st.error(f"❌ Could not terminate server automatically: {e}")
                st.info("💡 **Manual shutdown required:**")
                if platform.system().lower() == 'windows':
                    st.info("Press **Ctrl+C** in the command prompt where you started the app")
                else:
                    st.info("Press **Ctrl+C** in the terminal where you started the app")
            
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
                    # Read the content from the template workflow.yml in the templates directory
                    app_dir = Path(__file__).parent
                    template_workflow_path = app_dir / "templates" / "workflow.yml"
                    if template_workflow_path.is_file():
                        default_workflow_content = template_workflow_path.read_text()
                        with open(workflow_file, "w") as f:
                            f.write(default_workflow_content)
                        st.success("✅ Created a new workflow.yml from the protected template.")
                        
                        # Load the project immediately
                        try:
                            st.session_state.project = Project(project_path)
                            st.success("🎉 New project loaded! Ready to start from Step 1.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading project: {e}")
                            return
                    else:
                        st.error("Could not find the workflow.yml template file in the templates directory.")
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
                st.session_state.project = Project(project_path)
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
                completed_steps = [step_id for step_id, status in state_data.items() if status == 'completed']
                skipped_steps = [step_id for step_id, status in state_data.items() if status == 'skipped']
                
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
                        st.session_state.project = Project(project_path)
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
                        project_for_restore = Project(project_path, load_workflow=False)
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
                            app_dir = Path(__file__).parent
                            template_workflow_path = app_dir / "templates" / "workflow.yml"
                            if template_workflow_path.is_file():
                                default_workflow_content = template_workflow_path.read_text()
                                with open(workflow_file, "w") as f:
                                    f.write(default_workflow_content)
                                st.success("✅ Created workflow.yml from template")
                            else:
                                st.error("Could not find the workflow.yml template file.")
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
                            st.session_state.project = Project(project_path)
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
                            app_dir = Path(__file__).parent
                            template_workflow_path = app_dir / "templates" / "workflow.yml"
                            if template_workflow_path.is_file():
                                default_workflow_content = template_workflow_path.read_text()
                                with open(workflow_file, "w") as f:
                                    f.write(default_workflow_content)
                                st.success("✅ Created workflow.yml from template")
                                
                                # Now load the project directly
                                try:
                                    # Validate workflow file before loading
                                    is_valid, error_message = validate_workflow_yaml(workflow_file)
                                    if not is_valid:
                                        st.error(f"❌ **Workflow Validation Failed**: {error_message}")
                                        return
                                    
                                    # Load the project and set flag for existing work pre-selection
                                    st.session_state.project = Project(project_path)
                                    st.session_state.setup_with_existing_preselected = True
                                    st.success("🎉 Project loaded! Please choose your setup option in the sidebar.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error loading project: {e}")
                                    return
                            else:
                                st.error("Could not find the workflow.yml template file.")
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
                            project_for_restore = Project(project_path, load_workflow=False)
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
                            app_dir = Path(__file__).parent
                            template_path = app_dir / "templates" / "workflow.yml"
                            if template_path.exists():
                                shutil.copy2(template_path, workflow_file)
                                st.success("✅ Replaced with clean template!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Template file not found.")
                        except Exception as e:
                            st.error(f"Template replacement failed: {e}")
            else:
                try:
                    st.session_state.project = Project(project_path)
                    
                    # Check for conditional steps that need user decision after loading project
                    conditional_steps = st.session_state.project.check_for_conditional_triggers()
                    if conditional_steps:
                        st.session_state.conditional_steps_awaiting = conditional_steps
                    
                    st.success(f"✅ Loaded: {st.session_state.project.path.name}")
                    # Trigger rerun so sidebar re-renders with undo button if there are completed steps
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading project: {e}")
                    st.session_state.project = None

    # --- Main Content Area ---
    
    # Check for updates and show notifications at top of main area
    update_info = check_for_updates(SCRIPT_PATH)
    app_update_info = update_info.get('app', {})
    script_update_info = update_info.get('scripts', {})

    updates_available = (
        app_update_info.get('update_available', False) or
        script_update_info.get('update_available', False)
    )

    # Always show the update status expander for persistent visibility.
    # The title and expanded state will change based on whether updates are available.
    expander_title = "📦 Updates Available" if updates_available else "✅ System is Up-to-Date"
    expander_expanded = True if updates_available else False

    with st.expander(expander_title, expanded=expander_expanded):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🏠 Application**")
            if app_update_info.get('error'):
                st.error(f"Error: {app_update_info['error']}")
            elif app_update_info.get('update_available'):
                st.warning(f"Update: `{app_update_info.get('current_version', 'N/A')}` → `{app_update_info.get('latest_version', 'N/A')}`")
                if st.button("📥 Download App Update", key="app_update_btn"):
                    webbrowser.open("https://github.com/RRMalmstrom/sip_lims_workflow_manager/releases/latest")
                    st.success("🌐 Opening GitHub releases...")
            else:
                st.success(f"✅ Up to date (v{app_update_info.get('current_version', 'N/A')})")

        with col2:
            st.markdown("**🔧 Scripts**")
            if script_update_info.get('error'):
                st.error(f"Error: {script_update_info['error']}")
            elif script_update_info.get('update_available'):
                st.warning(f"Update: `{script_update_info.get('current_version', 'N/A')}` → `{script_update_info.get('latest_version', 'N/A')}`")
                if st.button("📥 Update Scripts", key="script_update_btn"):
                    with st.spinner("Updating scripts..."):
                        result = update_scripts(SCRIPT_PATH)
                        if result.get('success'):
                            st.success("✅ Scripts updated!")
                            check_for_updates.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Update failed: {result.get('error', 'Unknown error')}")
            else:
                st.success(f"✅ Up to date (v{script_update_info.get('current_version', 'N/A')})")

        # Manual refresh option in expander
        st.markdown("---")
        if st.button("🔄 Force Check Updates", key="manual_check"):
            check_for_updates.clear()
            st.rerun()
    
    if not st.session_state.project:
        st.info("Select a project folder using the 'Browse' button in the sidebar.")
    else:
        project = st.session_state.project
        
        # Display project folder name prominently beneath the main header
        st.markdown(f"## 📁 {project.path.name}")

        # --- Terminal Output and Interaction ---
        # Show terminal for running scripts
        if st.session_state.running_step_id:
            # Make terminal very prominent with visual indicators
            running_step = project.workflow.get_step_by_id(st.session_state.running_step_id)
            
            # Large, prominent header
            st.markdown("# 🖥️ LIVE TERMINAL")
            st.error(f"🚨 **SCRIPT RUNNING**: {running_step['name'] if running_step else 'Unknown Step'}")
            st.warning("⚠️ **IMPORTANT**: Interactive input required below!")
            
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
                    help="Type your input and press Enter or click 'Send Input'",
                    placeholder="Type your input here...",
                    on_change=handle_terminal_input_change
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
                    if project.terminate_script(st.session_state.running_step_id):
                        st.session_state.running_step_id = None
                        st.session_state.terminal_output = ""
                        st.success("✅ Script terminated and project rolled back!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to terminate script")
            
        
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
                    st.info(f"⏳ {step_name} (Running...)")
                elif status == "completed":
                    st.success(f"✅ {step_name}")
                elif status == "skipped":
                    st.info(f"⏩ {step_name} - Completed outside workflow")
                elif status == "skipped_conditional":
                    st.info(f"⏭️ {step_name} - Skipped (conditional)")
                elif status == "awaiting_decision":
                    st.warning(f"❓ {step_name} - Awaiting decision")
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
                        st.info("💡 **Re-run Setup**: Please select input files for this re-run. Previous inputs are cleared to ensure fresh data.")
                        # Clear previous inputs for re-run to force user to select new files
                        if f"rerun_inputs_cleared_{step_id}" not in st.session_state:
                            st.session_state.user_inputs[step_id] = {}
                            st.session_state[f"rerun_inputs_cleared_{step_id}"] = True
                    
                    for i, input_def in enumerate(step['inputs']):
                        input_key = f"{step_id}_input_{i}"
                        if input_def['type'] == 'file':
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                current_value = st.session_state.user_inputs[step_id].get(input_key, "")
                                
                                file_path = st.text_input(
                                    label=input_def['name'],
                                    value=current_value,
                                    key=f"text_{input_key}_{current_value}"  # Force widget recreation when value changes
                                )
                            with col_b:
                                if st.button("Browse", key=f"browse_{input_key}"):
                                    selected_file = select_file_via_subprocess()
                                    if selected_file:
                                        st.session_state.user_inputs[step_id][input_key] = selected_file
                                        st.rerun()

            with col2:
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
                else:
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
                        
                        if st.button("Re-run", key=f"rerun_{step_id}", disabled=rerun_button_disabled):
                            # Clear the rerun flag so inputs get cleared again next time
                            if f"rerun_inputs_cleared_{step_id}" in st.session_state:
                                del st.session_state[f"rerun_inputs_cleared_{step_id}"]
                            
                            st.session_state.running_step_id = step_id
                            st.session_state.terminal_output = ""
                            step_user_inputs = st.session_state.user_inputs.get(step_id, {})
                            start_script_thread(project, step_id, step_user_inputs)
                            st.rerun()  # Force immediate rerun to show terminal
                    
                    # Show Run button for pending steps (or all steps if they're the next step)
                    if status not in ["completed", "skipped_conditional", "awaiting_decision"]:
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

    # --- Background Loop for UI Updates & Final Result Processing ---
    if st.session_state.project:
        # This block handles both polling for terminal output and the final result
        if st.session_state.running_step_id:
            runner = st.session_state.project.script_runner
            
            # DEBUG: Add diagnostic logging to understand polling behavior
            import datetime
            current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Enhanced polling logic to retrieve all available output
            # This fixes the pseudo-terminal buffering issue where prompts
            # would remain invisible until user interaction
            output_received = False
            items_retrieved = 0
            queue_size_before = runner.output_queue.qsize()
            
            for attempt in range(10):  # Increased from single attempt to 10
                try:
                    output = runner.output_queue.get_nowait()
                    if output is not None:
                        st.session_state.terminal_output += output
                        output_received = True
                        items_retrieved += 1
                        # DEBUG: Log each item retrieved
                        print(f"[{current_time}] POLLING DEBUG: Retrieved item {items_retrieved}: '{output[:50]}{'...' if len(output) > 50 else ''}'")
                except queue.Empty:
                    if output_received:
                        # If we got some output, wait briefly and try again
                        # This handles cases where output arrives in quick succession
                        time.sleep(0.01)
                        continue
                    else:
                        break  # No output available, stop polling
            
            queue_size_after = runner.output_queue.qsize()
            
            # DEBUG: Log polling results
            if queue_size_before > 0 or items_retrieved > 0:
                print(f"[{current_time}] POLLING DEBUG: Queue before={queue_size_before}, retrieved={items_retrieved}, queue after={queue_size_after}, will_rerun={output_received}")
            
            # Only trigger rerun if we actually received output
            if output_received:
                print(f"[{current_time}] POLLING DEBUG: Triggering st.rerun() due to output received")
                st.rerun()
            else:
                # DEBUG: Check if there's actually content in the queue that we missed
                if queue_size_before > 0:
                    print(f"[{current_time}] POLLING DEBUG: WARNING - Queue had {queue_size_before} items but we retrieved {items_retrieved}")

            # Poll for the final result
            try:
                result = runner.result_queue.get_nowait()
                
                # We got the result, the script is done.
                # Now we can update the state and UI using the new handle_step_result method.
                step_id = st.session_state.running_step_id
                
                # Use the new handle_step_result method which includes rollback logic
                st.session_state.project.handle_step_result(step_id, result)

                # Check for conditional triggers after step completion
                if result.success:
                    conditional_steps = st.session_state.project.check_for_conditional_triggers()
                    if conditional_steps:
                        # Store conditional steps that need user decision
                        st.session_state.conditional_steps_awaiting = conditional_steps

                # Preserve the terminal output for completed script display
                st.session_state.completed_script_output = st.session_state.terminal_output
                st.session_state.completed_script_step = step_id
                st.session_state.completed_script_success = result.success

                st.session_state.last_run_result = {"step_name": st.session_state.project.workflow.get_step_by_id(step_id)['name'], **result.__dict__}
                st.session_state.running_step_id = None
                st.session_state.redo_stack = []
                st.rerun()

            except queue.Empty:
                pass # Not finished yet

            # If still running, schedule another rerun with shorter delay
            # This ensures prompts appear immediately without waiting for user interaction
            if st.session_state.running_step_id:
                # Reduced delay to make polling more responsive
                # This fixes the issue where users need to click "Send Input" twice
                time.sleep(0.05)  # Reduced from 0.1s to 0.05s
                st.rerun()
        

if __name__ == "__main__":
    main()