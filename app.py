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
            with st.expander("Live Terminal Output", expanded=True):
                st.text_area("Output", value=st.session_state.terminal_output, height=300, key="terminal_view", disabled=True)
                
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

                # Input widgets...
                if 'inputs' in step and status != 'completed' and not is_running_this_step:
                    st.session_state.user_inputs.setdefault(step_id, {})
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
                    if st.button("Re-run", key=f"rerun_{step_id}", disabled=run_button_disabled):
                        st.session_state.running_step_id = step_id
                        st.session_state.terminal_output = ""
                        step_user_inputs = st.session_state.user_inputs.get(step_id, {})
                        start_script_thread(project, step_id, step_user_inputs)
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