import yaml
from pathlib import Path
from typing import List, Dict, Any
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult

class Workflow:
    """
    Represents a workflow defined in a YAML file.
    """
    def __init__(self, path: Path):
        self._path = path
        self._data = self._load_workflow()
        
        self.name: str = self._data.get("workflow_name", "Untitled Workflow")
        self.steps: List[Dict[str, Any]] = self._data.get("steps", [])

    def _load_workflow(self) -> Dict[str, Any]:
        """Loads and parses the workflow YAML file."""
        with open(self._path, 'r') as f:
            return yaml.safe_load(f)

    def get_step_by_id(self, step_id: str) -> Dict[str, Any]:
        """Finds a step in the workflow by its ID."""
        for step in self.steps:
            if step.get("id") == step_id:
                return step
        return None

class Project:
    """
    Represents a single project folder, containing a workflow, its state,
    and all associated data. It coordinates the StateManager, SnapshotManager,
    and ScriptRunner.
    """
    def __init__(self, project_path: Path, load_workflow: bool = True):
        self.path = project_path
        self.workflow_file_path = self.path / "workflow.yml"
        
        self.state_manager = StateManager(self.path / "workflow_state.json")
        self.snapshot_manager = SnapshotManager(self.path, self.path / ".snapshots")
        self.script_runner = ScriptRunner(self.path)
        
        if load_workflow:
            if not self.workflow_file_path.is_file():
                raise FileNotFoundError(f"Workflow file not found at {self.workflow_file_path}")
            self.workflow = Workflow(self.workflow_file_path)
        else:
            self.workflow = None

    def get_state(self, step_id: str) -> str:
        """Gets the status of a specific step."""
        return self.state_manager.get_step_state(step_id)

    def update_state(self, step_id: str, status: str):
        """Updates the status of a specific step."""
        self.state_manager.update_step_state(step_id, status)

    def run_step(self, step_id: str, user_inputs: Dict[str, Any] = None):
        """
        Starts a workflow step asynchronously for interactive execution.
        This method is used by the UI for scripts that require user interaction.
        The UI must handle the result and call handle_step_result() when complete.
        """
        if user_inputs is None:
            user_inputs = {}
            
        step = self.workflow.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"Step '{step_id}' not found in workflow.")

        is_first_run = self.get_state(step_id) == "pending"
        snapshot_items = step.get("snapshot_items", [])

        if is_first_run:
            self.snapshot_manager.take(step_id, snapshot_items)

        # Prepare arguments for the script
        args = []
        if "inputs" in step:
            for i, input_def in enumerate(step["inputs"]):
                input_key = f"{step_id}_input_{i}"
                value = user_inputs.get(input_key)
                if value:
                    if input_def.get("arg"):
                        args.append(input_def["arg"])
                    args.append(value)

        # Start the script asynchronously
        self.script_runner.run(step["script"], args=args)

    def handle_step_result(self, step_id: str, result: RunResult):
        """
        Handles the result of an asynchronously executed step.
        This should be called by the UI when the script completes.
        """
        step = self.workflow.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"Step '{step_id}' not found in workflow.")

        is_first_run = self.get_state(step_id) == "pending"
        snapshot_items = step.get("snapshot_items", [])

        # Enhanced success detection: check both exit code AND success marker
        exit_code_success = result.success
        script_name = step.get("script", "")
        marker_file_success = self._check_success_marker(script_name)
        
        # Both conditions must be true for actual success
        actual_success = exit_code_success and marker_file_success
        
        # Log what happened for debugging
        if exit_code_success and not marker_file_success:
            debug_msg = f"Script {script_name} exited with code 0 but no success marker found - treating as failure"
            print(debug_msg)
            try:
                debug_file = self.path / "workflow_debug.log"
                with open(debug_file, "a") as f:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {debug_msg}\n")
            except:
                pass

        # Handle the result based on our enhanced success detection
        if actual_success:
            self.update_state(step_id, "completed")
        else:
            # If this was the first run and it failed, restore the snapshot
            if is_first_run:
                rollback_msg = f"ROLLBACK: Restoring snapshot for failed step '{step_id}'"
                print(rollback_msg)
                try:
                    debug_file = self.path / "workflow_debug.log"
                    with open(debug_file, "a") as f:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {rollback_msg}\n")
                        f.write(f"[{timestamp}] Snapshot items to restore: {snapshot_items}\n")
                except:
                    pass
                
                self.snapshot_manager.restore(step_id, snapshot_items)
                
                # Log completion of rollback
                rollback_complete_msg = f"ROLLBACK COMPLETE: Snapshot restored for step '{step_id}'"
                print(rollback_complete_msg)
                try:
                    with open(debug_file, "a") as f:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {rollback_complete_msg}\n")
                except:
                    pass
            # Keep the state as "pending" for failed steps

    def _check_success_marker(self, script_name: str) -> bool:
        """
        Check if a script completed successfully by looking for its success marker file.
        """
        if not script_name:
            return True  # No script name, can't check marker
            
        status_dir = self.path / ".workflow_status"
        success_file = status_dir / f"{script_name}.success"
        return success_file.exists()
