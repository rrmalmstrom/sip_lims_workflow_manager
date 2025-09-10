import streamlit as st
from pathlib import Path
import subprocess
import sys
import json
import shutil
import threading
import time
import queue
from src.core import Project
from src.logic import RunResult

# --- Page Configuration ---
st.set_page_config(page_title="LIMS Workflow Manager", page_icon="🧪", layout="wide")

import streamlit.components.v1 as components

# --- Helper Functions ---
def auto_scroll_terminal():
    """
    Injects a JavaScript snippet to persistently poll the terminal textarea
    and scroll it to the bottom whenever its content grows.
    """
    js_code = """
    <script>
    (function() {
        // Find the textarea element for the terminal output
        const terminal = window.parent.document.querySelector('textarea[data-testid="stTextarea"]');
        if (!terminal) {
            return; // Exit if terminal not found
        }

        // Use a MutationObserver to detect when the content of the terminal changes
        const observer = new MutationObserver((mutations) => {
            // We only need to know that it changed, not what the change was
            terminal.scrollTop = terminal.scrollHeight;
        });

        // Start observing the terminal for changes in its child nodes (the text)
        observer.observe(terminal, { childList: true, subtree: true });

        // Also, scroll to bottom one time on initial load
        terminal.scrollTop = terminal.scrollHeight;

        // Clean up the observer when the component is unmounted
        const streamlitDoc = window.parent.document;
        const observerCleanup = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.removedNodes.forEach((removedNode) => {
                    if (removedNode.contains && removedNode.contains(terminal)) {
                        observer.disconnect();
                    }
                });
            });
        });
        observerCleanup.observe(streamlitDoc.body, { childList: true, subtree: true });
    })();
    </script>
    """
    components.html(js_code, height=0)

def scroll_to_top():
    """
    Injects JavaScript to scroll the page to the top when the terminal opens.
    Uses multiple methods to ensure compatibility with Streamlit's iframe structure.
    """
    js_code = """
    <script>
    (function() {
        // Multiple aggressive attempts to scroll to top
        function scrollToTop() {
            try {
                // Method 1: Immediate scroll attempts
                if (window.parent) {
                    window.parent.scrollTo(0, 0);
                    window.parent.scrollTo({top: 0, behavior: 'instant'});
                }
                window.scrollTo(0, 0);
                window.scrollTo({top: 0, behavior: 'instant'});
                
                // Method 2: Target Streamlit containers
                const streamlitDoc = window.parent.document;
                if (streamlitDoc) {
                    // Try multiple container selectors
                    const containers = [
                        streamlitDoc.querySelector('[data-testid="stAppViewContainer"]'),
                        streamlitDoc.querySelector('.main'),
                        streamlitDoc.querySelector('[data-testid="stApp"]'),
                        streamlitDoc.querySelector('.stApp'),
                        streamlitDoc.body,
                        streamlitDoc.documentElement
                    ];
                    
                    containers.forEach(container => {
                        if (container) {
                            container.scrollTop = 0;
                            if (container.scrollTo) {
                                container.scrollTo(0, 0);
                                container.scrollTo({top: 0, behavior: 'instant'});
                            }
                        }
                    });
                }
            } catch (e) {
                console.log('Scroll attempt failed:', e);
            }
        }
        
        // Try immediately
        scrollToTop();
        
        // Try again after short delays
        setTimeout(scrollToTop, 50);
        setTimeout(scrollToTop, 100);
        setTimeout(scrollToTop, 200);
        setTimeout(scrollToTop, 500);
    })();
    </script>
    """
    components.html(js_code, height=0)

def send_and_clear_input(project, user_input):
    """Callback to send input to the script and clear the input box."""
    if project.script_runner.is_running():
        project.script_runner.send_input(user_input)
        st.session_state.terminal_input_box = ""
        st.session_state.scroll_to_bottom = True
        st.session_state.scroll_to_bottom = True

def select_file_via_subprocess():
    python_executable = sys.executable
    script_path = Path(__file__).parent / "file_dialog.py"
    process = subprocess.run([python_executable, str(script_path), 'file'], capture_output=True, text=True)
    return process.stdout.strip()

def select_folder_via_subprocess():
    python_executable = sys.executable
    script_path = Path(__file__).parent / "file_dialog.py"
    process = subprocess.run([python_executable, str(script_path)], capture_output=True, text=True)
    return process.stdout.strip()

def perform_undo(project):
    """
    Performs undo operation by reverting to the previous completed step state.
    Uses the complete snapshot system for comprehensive rollback.
    """
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
            # Restore to the previous run's state (after previous run completed)
            previous_run_snapshot = f"{last_step_id}_run_{effective_run - 1}_after"
            if project.snapshot_manager.snapshot_exists(previous_run_snapshot):
                project.snapshot_manager.restore_complete_snapshot(previous_run_snapshot)
                # Remove the current run's 'after' snapshot to track that it's been undone
                project.snapshot_manager.remove_run_snapshots_from(last_step_id, effective_run)
                print(f"UNDO: Restored project to state after run {effective_run - 1} of step {last_step_id}")
                # Step should remain "completed" since we still have a previous run
                return True
            
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
    st.title("🧪 LIMS Workflow Manager")

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

    if st.session_state.project_path and not st.session_state.project:
        project_path = st.session_state.project_path
        workflow_file = project_path / "workflow.yml"

        if not workflow_file.is_file():
            # Check for a .db file to determine the scenario
            db_files = list(project_path.glob("*.db"))
            if db_files:
                # Scenario: DB exists, workflow.yml is missing
                st.warning("⚠️ Workflow file is missing, but a project database was found.")
                st.info("This may indicate that the workflow.yml file was accidentally deleted.")
                if st.button("Attempt to Restore workflow.yml from Last Snapshot"):
                    try:
                        # We need a project object to access the snapshot manager
                        # Temporarily create one without the workflow to access its methods
                        project_for_restore = Project(project_path, load_workflow=False)
                        restored = project_for_restore.snapshot_manager.restore_file_from_latest_snapshot("workflow.yml")
                        if restored:
                            st.success("Successfully restored workflow.yml! The page will now reload.")
                            time.sleep(2) # Give user time to read the message
                            st.rerun()
                        else:
                            st.error("Could not find a snapshot to restore the workflow.yml from.")
                    except Exception as e:
                        st.error(f"An error occurred during restoration: {e}")

            else:
                # Scenario: New project, no DB, no workflow.yml
                st.info("This looks like a new project.")
                st.warning("A `workflow.yml` file was not found in the selected directory.")
                if st.button("Create a New workflow.yml"):
                    try:
                        # Read the content from the template workflow.yml in the app's root directory
                        app_dir = Path(__file__).parent
                        template_workflow_path = app_dir / "workflow.yml"
                        if template_workflow_path.is_file():
                            default_workflow_content = template_workflow_path.read_text()
                            with open(workflow_file, "w") as f:
                                f.write(default_workflow_content)
                            st.success("Created a new workflow.yml from the template. The page will now reload.")
                        else:
                            st.error("Could not find the workflow.yml template file in the application directory.")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not create workflow.yml: {e}")
        else:
            try:
                st.session_state.project = Project(project_path)
                st.success(f"Loaded: {st.session_state.project.path.name}")
                # Trigger rerun so sidebar re-renders with undo button if there are completed steps
                st.rerun()
            except Exception as e:
                st.error(f"Error loading project: {e}")
                st.session_state.project = None

    # --- Main Content Area ---
    st.header("Workflow Status")

    if not st.session_state.project:
        st.info("Select a project folder using the 'Browse' button in the sidebar.")
    else:
        project = st.session_state.project
        
        st.subheader(f"Workflow: {project.workflow.name}")

        # --- Terminal Output and Interaction ---
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
            
            # Input section for terminal
            col1, col2 = st.columns([4, 1])
            with col1:
                user_input = st.text_input("Input:", key="terminal_input_box")
            with col2:
                st.button(
                    "Send Input",
                    key="send_terminal_input",
                    on_click=send_and_clear_input,
                    args=(project, user_input)
                )
        
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
                    st.warning(f"⏩ {step_name} (Skipped)")
                else:
                    st.info(f"⚪ {step_name}")

                # Input widgets - now shown for completed steps too (for re-runs)
                if 'inputs' in step and not is_running_this_step:
                    st.session_state.user_inputs.setdefault(step_id, {})
                    
                    # For completed steps, show a note about re-run inputs
                    if status == 'completed':
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
                                file_path = st.text_input(
                                    label=input_def['name'],
                                    value=st.session_state.user_inputs[step_id].get(input_key, ""),
                                    key=f"text_{input_key}"
                                )
                                st.session_state.user_inputs[step_id][input_key] = file_path
                            with col_b:
                                if st.button("Browse", key=f"browse_{input_key}"):
                                    selected_file = select_file_via_subprocess()
                                    if selected_file:
                                        st.session_state.user_inputs[step_id][input_key] = selected_file
                                        st.rerun()

            with col2:
                # Run/Re-run buttons...
                run_button_disabled = st.session_state.running_step_id is not None
                if status == "completed":
                    # Check if all required inputs for re-run are filled
                    rerun_button_disabled = run_button_disabled
                    if 'inputs' in step:
                        step_inputs = st.session_state.user_inputs.get(step_id, {})
                        required_inputs = step['inputs']
                        if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
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
                else:
                    is_next_step = (step_id == first_pending_step['id']) if first_pending_step else False
                    if not is_next_step:
                        run_button_disabled = True
                    
                    # Check if all required inputs for this step are filled
                    if 'inputs' in step:
                        step_inputs = st.session_state.user_inputs.get(step_id, {})
                        required_inputs = step['inputs']
                        if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
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
            # Poll for terminal output
            try:
                output = runner.output_queue.get_nowait()
                if output is not None:
                    st.session_state.terminal_output += output
                    st.rerun()
            except queue.Empty:
                pass # No new output

            # Poll for the final result
            try:
                result = runner.result_queue.get_nowait()
                
                # We got the result, the script is done.
                # Now we can update the state and UI using the new handle_step_result method.
                step_id = st.session_state.running_step_id
                
                # Use the new handle_step_result method which includes rollback logic
                st.session_state.project.handle_step_result(step_id, result)

                st.session_state.last_run_result = {"step_name": st.session_state.project.workflow.get_step_by_id(step_id)['name'], **result.__dict__}
                st.session_state.running_step_id = None
                st.session_state.redo_stack = []
                st.rerun()

            except queue.Empty:
                pass # Not finished yet

            # If still running, schedule another rerun
            if st.session_state.running_step_id:
                auto_scroll_terminal()
                time.sleep(0.1)
                st.rerun()
        
        if st.session_state.scroll_to_bottom:
            auto_scroll_terminal()
            st.session_state.scroll_to_bottom = False
        
        if st.session_state.scroll_to_bottom:
            auto_scroll_terminal()
            st.session_state.scroll_to_bottom = False

if __name__ == "__main__":
    main()