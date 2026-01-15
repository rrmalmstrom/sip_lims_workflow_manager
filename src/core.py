import yaml
import os
from pathlib import Path
from typing import List, Dict, Any
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult
from src.smart_sync import get_smart_sync_manager
from src.debug_logger import (
    debug_context, log_info, log_error, log_warning,
    log_smart_sync_detection, debug_enabled
)

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
    def __init__(self, project_path: Path, script_path: Path = None, load_workflow: bool = True):
        self.path = project_path
        # If no script_path provided, default to project_path/scripts
        if script_path is None:
            self.script_path = self.path / "scripts"
        else:
            self.script_path = script_path
        self.workflow_file_path = self.path / "workflow.yml"
        
        self.state_manager = StateManager(self.path / "workflow_state.json")
        self.snapshot_manager = SnapshotManager(self.path, self.path / ".snapshots")
        # Roo-Fix: Pass the script_path to the ScriptRunner.
        self.script_runner = ScriptRunner(self.path, script_path=self.script_path)
        
        # Initialize Smart Sync if enabled
        self.smart_sync_manager = None
        smart_sync_enabled = os.getenv("SMART_SYNC_ENABLED") == "true"
        
        if debug_enabled():
            log_info("Project initialization: Smart Sync check",
                    smart_sync_enabled=smart_sync_enabled,
                    project_path=str(project_path))
        
        if smart_sync_enabled:
            network_path = os.getenv("NETWORK_PROJECT_PATH")
            local_path = os.getenv("LOCAL_PROJECT_PATH")
            
            if debug_enabled():
                log_info("Project initialization: Smart Sync environment variables",
                        network_path=network_path,
                        local_path=local_path)
            
            if network_path and local_path:
                try:
                    self.smart_sync_manager = get_smart_sync_manager(network_path, local_path)
                    print(f"Smart Sync enabled: {network_path} <-> {local_path}")
                    
                    log_info("Project initialization: Smart Sync manager created successfully",
                            network_path=network_path,
                            local_path=local_path,
                            manager_type=type(self.smart_sync_manager).__name__)
                    
                except Exception as e:
                    log_error("Project initialization: Smart Sync manager creation failed",
                             error=str(e),
                             network_path=network_path,
                             local_path=local_path)
                    print(f"Smart Sync initialization failed: {e}")
            else:
                log_warning("Project initialization: Smart Sync enabled but missing environment variables",
                           network_path=network_path,
                           local_path=local_path)
        
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

    def has_workflow_state(self) -> bool:
        """Check if a workflow state file exists."""
        state_file = self.path / "workflow_state.json"
        return state_file.exists() and state_file.stat().st_size > 0

    def skip_to_step(self, target_step_id: str) -> str:
        """
        Skip all steps before target step, marking them as 'skipped'.
        Creates a safety snapshot for undo capability.
        Returns a message describing the action taken.
        """
        # Validate target step exists
        target_step = self.workflow.get_step_by_id(target_step_id)
        if not target_step:
            raise ValueError(f"Step {target_step_id} not found")
        
        # Create safety snapshot of current project state
        self.snapshot_manager.take_complete_snapshot("skip_to_initial")
        
        # Initialize ALL steps in the workflow state for consistency
        target_step_found = False
        steps_skipped = 0
        
        for step in self.workflow.steps:
            step_id = step['id']
            
            if step_id == target_step_id:
                target_step_found = True
                # Mark target step as pending
                self.update_state(step_id, 'pending')
            elif not target_step_found:
                # Mark all steps before target as skipped
                self.update_state(step_id, 'skipped')
                steps_skipped += 1
            else:
                # Mark all steps after target as pending
                self.update_state(step_id, 'pending')
        
        return f"Skipped to {target_step['name']}"

    def get_next_available_step(self):
        """Get the next step that can be run (first pending step)."""
        for step in self.workflow.steps:
            if self.get_state(step['id']) == 'pending':
                return step
        return None


    def run_step(self, step_id: str, user_inputs: Dict[str, Any] = None):
        """
        Starts a workflow step asynchronously for interactive execution.
        This method is used by the UI for scripts that require user interaction.
        The UI must handle the result and call handle_step_result() when complete.
        """
        with debug_context("workflow_step_execution",
                          step_id=step_id,
                          user_inputs=user_inputs) as debug_logger:
            
            if user_inputs is None:
                user_inputs = {}
                
            step = self.workflow.get_step_by_id(step_id)
            if not step:
                raise ValueError(f"Step '{step_id}' not found in workflow.")

            if debug_logger:
                debug_logger.info("Starting workflow step execution",
                                step_id=step_id,
                                step_name=step.get('name', 'Unknown'),
                                step_script=step.get('script', 'No script'),
                                user_inputs=user_inputs,
                                smart_sync_enabled=self.smart_sync_manager is not None)

            # Smart Sync: Pre-step sync (network -> local)
            if self.smart_sync_manager:
                print(f"Smart Sync: Syncing latest changes before step '{step_id}'...")
                
                if debug_logger:
                    debug_logger.info("Starting pre-step Smart Sync (network -> local)",
                                    step_id=step_id)
                
                try:
                    sync_success = self.smart_sync_manager.incremental_sync_down()
                    if sync_success:
                        print("Smart Sync: Pre-step sync completed successfully")
                        
                        log_info("Workflow pre-step sync completed successfully",
                                step_id=step_id,
                                sync_direction="network_to_local")
                        
                    else:
                        print("Smart Sync: Pre-step sync failed, continuing with step execution")
                        
                        log_warning("Workflow pre-step sync failed, continuing execution",
                                   step_id=step_id,
                                   sync_direction="network_to_local")
                        
                except Exception as e:
                    print(f"Smart Sync: Pre-step sync error: {e}, continuing with step execution")
                    
                    log_error("Workflow pre-step sync error, continuing execution",
                             step_id=step_id,
                             sync_direction="network_to_local",
                             error=str(e))
            else:
                if debug_logger:
                    debug_logger.info("No Smart Sync manager - skipping pre-step sync",
                                    step_id=step_id)

        is_first_run = self.get_state(step_id) == "pending"
        snapshot_items = step.get("snapshot_items", [])

        # Get the next run number for this step
        allow_rerun = step.get('allow_rerun', False)
        run_number = self.snapshot_manager.get_next_run_number(step_id, allow_rerun)
        
        # Always take a snapshot before running (for both first runs and re-runs)
        if is_first_run:
            # Take both the old-style snapshot (for compatibility) and complete snapshot
            self.snapshot_manager.take(step_id, snapshot_items)
        
        # Take a run-specific complete snapshot for granular undo
        self.snapshot_manager.take_complete_snapshot(f"{step_id}_run_{run_number}")

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
        with debug_context("workflow_step_result_handling",
                          step_id=step_id,
                          result_success=result.success) as debug_logger:
            
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
            
            if debug_logger:
                debug_logger.info("Processing step result",
                                step_id=step_id,
                                step_name=step.get('name', 'Unknown'),
                                script_name=script_name,
                                exit_code_success=exit_code_success,
                                marker_file_success=marker_file_success,
                                actual_success=actual_success,
                                is_first_run=is_first_run)
            
            # Log what happened for debugging
            if exit_code_success and not marker_file_success:
                debug_msg = f"Script {script_name} exited with code 0 but no success marker found - treating as failure"
                print(debug_msg)
                
                log_warning("Step result: Exit code success but no marker file",
                           step_id=step_id,
                           script_name=script_name,
                           exit_code_success=exit_code_success,
                           marker_file_success=marker_file_success)
                
                try:
                    # Create hidden log directory if it doesn't exist
                    log_dir = self.path / ".workflow_logs"
                    log_dir.mkdir(exist_ok=True)
                    debug_file = log_dir / "workflow_debug.log"
                    with open(debug_file, "a") as f:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {debug_msg}\n")
                except:
                    pass

            # Handle the result based on our enhanced success detection
            if actual_success:
                self.update_state(step_id, "completed")
                
                log_info("Workflow step completed successfully",
                        step_id=step_id,
                        step_name=step.get('name', 'Unknown'),
                        exit_code_success=exit_code_success,
                        marker_file_success=marker_file_success)
                
                # Smart Sync: Post-step sync (local -> network) on successful completion
                if self.smart_sync_manager:
                    print(f"Smart Sync: Syncing results after successful step '{step_id}'...")
                    
                    if debug_logger:
                        debug_logger.info("Starting post-step Smart Sync (local -> network)",
                                        step_id=step_id,
                                        step_name=step.get('name', 'Unknown'))
                    
                    try:
                        sync_success = self.smart_sync_manager.incremental_sync_up()
                        if sync_success:
                            print("Smart Sync: Post-step sync completed successfully")
                            
                            log_info("Workflow post-step sync completed successfully",
                                    step_id=step_id,
                                    sync_direction="local_to_network")
                            
                        else:
                            print("Smart Sync: Post-step sync failed, but step marked as completed")
                            
                            log_warning("Workflow post-step sync failed, but step marked as completed",
                                       step_id=step_id,
                                       sync_direction="local_to_network")
                            
                    except Exception as e:
                        print(f"Smart Sync: Post-step sync error: {e}, but step marked as completed")
                        
                        log_error("Workflow post-step sync error, but step marked as completed",
                                 step_id=step_id,
                                 sync_direction="local_to_network",
                                 error=str(e))
                else:
                    if debug_logger:
                        debug_logger.info("No Smart Sync manager - skipping post-step sync",
                                        step_id=step_id)
                
                # Note: "after" snapshots removed for simplified undo system
                # Only "before" snapshots are now used for undo functionality
            else:
                # Step failed - log the failure
                log_error("Workflow step failed",
                         step_id=step_id,
                         step_name=step.get('name', 'Unknown'),
                         exit_code_success=exit_code_success,
                         marker_file_success=marker_file_success,
                         is_first_run=is_first_run)
                
                # If this was the first run and it failed, restore the snapshot
                if is_first_run:
                    rollback_msg = f"ROLLBACK: Restoring snapshot for failed step '{step_id}'"
                    print(rollback_msg)
                    
                    log_info("Starting automatic rollback for failed step",
                            step_id=step_id,
                            step_name=step.get('name', 'Unknown'),
                            is_first_run=is_first_run)
                try:
                    # Create hidden log directory if it doesn't exist
                    log_dir = self.path / ".workflow_logs"
                    log_dir.mkdir(exist_ok=True)
                    debug_file = log_dir / "workflow_debug.log"
                    with open(debug_file, "a") as f:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {rollback_msg}\n")
                        f.write(f"[{timestamp}] Using complete snapshot restoration to 'before' state\n")
                except:
                    pass
                
                # Use complete snapshot restoration for consistency with undo button
                # Restore to the "before" snapshot taken immediately before this step started
                run_number = self.snapshot_manager.get_current_run_number(step_id)
                if run_number > 0:
                    # Use the granular system - restore to "before" snapshot (as if step never ran)
                    before_snapshot = f"{step_id}_run_{run_number}"
                    if self.snapshot_manager.snapshot_exists(before_snapshot):
                        self.snapshot_manager.restore_complete_snapshot(before_snapshot)
                        # CRITICAL FIX: Remove the "before" snapshot after automatic rollback
                        # This prevents corrupting the run counter for future runs
                        self.snapshot_manager.remove_run_snapshots_from(step_id, run_number)
                        rollback_complete_msg = f"ROLLBACK COMPLETE: Restored to before state (run {run_number}) for step '{step_id}' and cleaned up snapshot"
                    else:
                        # Fallback to legacy complete snapshot if granular doesn't exist
                        if self.snapshot_manager.snapshot_exists(step_id):
                            self.snapshot_manager.restore_complete_snapshot(step_id)
                            rollback_complete_msg = f"ROLLBACK COMPLETE: Restored using legacy complete snapshot for step '{step_id}'"
                        else:
                            # Last resort: use legacy selective restore
                            self.snapshot_manager.restore(step_id, snapshot_items)
                            rollback_complete_msg = f"ROLLBACK COMPLETE: Restored using legacy selective restore for step '{step_id}'"
                else:
                    # No granular snapshots exist, try legacy complete snapshot
                    if self.snapshot_manager.snapshot_exists(step_id):
                        self.snapshot_manager.restore_complete_snapshot(step_id)
                        rollback_complete_msg = f"ROLLBACK COMPLETE: Restored using legacy complete snapshot for step '{step_id}'"
                    else:
                        # Last resort: use legacy selective restore
                        self.snapshot_manager.restore(step_id, snapshot_items)
                        rollback_complete_msg = f"ROLLBACK COMPLETE: Restored using legacy selective restore for step '{step_id}'"
                
                print(rollback_complete_msg)
                try:
                    with open(debug_file, "a") as f:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {rollback_complete_msg}\n")
                except:
                    pass
            # Keep the state as "pending" for failed steps

    def terminate_script(self, step_id: str) -> bool:
        """
        Terminates a running script and rolls back to the snapshot taken before the step started.
        
        Args:
            step_id: The ID of the step whose script should be terminated
            
        Returns:
            bool: True if script was terminated and rollback successful, False if no script was running
        """
        # Check if script is actually running
        if not self.script_runner.is_running():
            return False
        
        step = self.workflow.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"Step '{step_id}' not found in workflow.")
        
        # Terminate the running script
        self.script_runner.terminate()
        
        # Get the current run number to find the correct "before" snapshot
        run_number = self.snapshot_manager.get_current_run_number(step_id)
        if run_number == 0:
            run_number = 1  # If no runs recorded yet, assume this is run 1
        
        # Restore to the "before" snapshot (state before script started)
        before_snapshot = f"{step_id}_run_{run_number}"
        try:
            if self.snapshot_manager.snapshot_exists(before_snapshot):
                self.snapshot_manager.restore_complete_snapshot(before_snapshot)
                # CRITICAL FIX: Remove the "before" snapshot after termination rollback
                # This prevents corrupting the run counter for future runs
                self.snapshot_manager.remove_run_snapshots_from(step_id, run_number)
                print(f"TERMINATE: Restored project to state before step {step_id} (run {run_number}) and cleaned up snapshot")
            else:
                # Fallback to legacy snapshot if granular doesn't exist
                if self.snapshot_manager.snapshot_exists(step_id):
                    self.snapshot_manager.restore_complete_snapshot(step_id)
                    print(f"TERMINATE: Restored project using legacy snapshot for step {step_id}")
                else:
                    print(f"TERMINATE: No snapshot found for step {step_id} - script terminated but no rollback performed")
        except Exception as e:
            print(f"TERMINATE: Error during rollback: {e}")
        
        # Remove any success marker that might have been created
        script_name = step.get("script", "")
        if script_name:
            script_filename = Path(script_name).stem
            status_dir = self.path / ".workflow_status"
            success_file = status_dir / f"{script_filename}.success"
            if success_file.exists():
                success_file.unlink()
                print(f"TERMINATE: Removed success marker for {script_filename}")
        
        # Ensure step state remains "pending" (not completed)
        self.update_state(step_id, "pending")
        
        return True

    def _check_success_marker(self, script_name: str) -> bool:
        """
        Check if a script completed successfully by looking for its success marker file.
        """
        if not script_name:
            return True  # No script name, can't check marker
            
        # Extract just the filename without path and extension
        script_filename = Path(script_name).stem
        
        status_dir = self.path / ".workflow_status"
        success_file = status_dir / f"{script_filename}.success"
        return success_file.exists()

    def finalize_smart_sync(self):
        """
        Perform final sync and cleanup when workflow is complete.
        Should be called when the project is done or being destroyed.
        """
        with debug_context("smart_sync_finalization") as debug_logger:
            
            if self.smart_sync_manager:
                print("Smart Sync: Performing final sync and cleanup...")
                
                if debug_logger:
                    debug_logger.info("Starting Smart Sync finalization",
                                    project_path=str(self.path))
                
                try:
                    # Final sync to ensure all changes are saved to network
                    sync_success = self.smart_sync_manager.final_sync()
                    if sync_success:
                        print("Smart Sync: Final sync completed successfully")
                        
                        log_info("Smart Sync final sync completed successfully",
                                project_path=str(self.path))
                        
                    else:
                        print("Smart Sync: Final sync failed")
                        
                        log_error("Smart Sync final sync failed",
                                 project_path=str(self.path))
                    
                    # Cleanup local staging directory
                    self.smart_sync_manager.cleanup()
                    print("Smart Sync: Cleanup completed")
                    
                    log_info("Smart Sync cleanup completed",
                            project_path=str(self.path))
                    
                except Exception as e:
                    print(f"Smart Sync: Error during finalization: {e}")
                    
                    log_error("Smart Sync finalization error",
                             project_path=str(self.path),
                             error=str(e))
            else:
                if debug_logger:
                    debug_logger.info("No Smart Sync manager - skipping finalization",
                                    project_path=str(self.path))

    def __del__(self):
        """
        Destructor to ensure Smart Sync cleanup happens even if finalize_smart_sync() isn't called.
        """
        try:
            self.finalize_smart_sync()
        except:
            pass  # Ignore errors during destruction
