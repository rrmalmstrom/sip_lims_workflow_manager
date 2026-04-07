import yaml
import os
from pathlib import Path
from typing import List, Dict, Any
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult
# Native execution only - Smart Sync removed
from src.enhanced_debug_logger import (
    debug_context, log_info, log_error, log_warning,
    debug_enabled
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

    def get_all_steps(self) -> List[Dict[str, Any]]:
        """Returns the list of all step dicts in the workflow."""
        return self.steps

class Project:
    """
    Represents a single project folder, containing a workflow, its state,
    and all associated data. It coordinates the StateManager, SnapshotManager,
    and ScriptRunner.
    """
    def __init__(self, project_path: Path, script_path: Path, load_workflow: bool = True):
        self.path = project_path
        # NO FALLBACKS! script_path is REQUIRED for native execution
        if script_path is None:
            raise ValueError(
                "script_path is required for native execution. "
                "The system must know exactly where workflow scripts are located. "
                "Check that SCRIPTS_PATH environment variable is properly set by run.py"
            )
        self.script_path = script_path
        self.workflow_file_path = self.path / "workflow.yml"
        
        # CRITICAL DEBUG: Log Project initialization details
        if debug_enabled():
            log_info("Project initialization: Native execution mode",
                    project_path=str(project_path),
                    script_path=str(self.script_path),
                    script_path_exists=self.script_path.exists(),
                    script_path_type=type(self.script_path).__name__)
        
        self.state_manager = StateManager(self.path / "workflow_state.json")
        self.snapshot_manager = SnapshotManager(self.path, self.path / ".snapshots")
        # Pass the script_path to the ScriptRunner for native execution
        self.script_runner = ScriptRunner(self.path, script_path=self.script_path)
        
        # CRITICAL DEBUG: Log ScriptRunner initialization
        if debug_enabled():
            log_info("ScriptRunner initialized",
                    project_path=str(project_path),
                    script_runner_script_path=str(self.script_runner.script_path),
                    script_runner_path_exists=self.script_runner.script_path.exists())
        
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
                                execution_mode="native")

            # Native execution - proceeding directly to step
            if debug_logger:
                debug_logger.info("Native execution mode - proceeding directly to step",
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
        # COMPREHENSIVE LOGGING: Create detailed log for race condition debugging
        log_dir = self.path / ".workflow_logs"
        log_dir.mkdir(exist_ok=True)
        step_result_log = log_dir / "step_result_handling.log"
        
        def log_step_detail(message, **kwargs):
            """Log detailed step processing information"""
            try:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                with open(step_result_log, "a") as f:
                    f.write(f"[{timestamp}] {message}\n")
                    for key, value in kwargs.items():
                        f.write(f"  {key}: {value}\n")
                    f.flush()
            except Exception:
                pass  # Don't let logging errors break workflow
        
        log_step_detail("=== STEP RESULT HANDLING STARTED ===",
                       step_id=step_id,
                       result_success=result.success,
                       result_return_code=result.return_code)
        
        with debug_context("workflow_step_result_handling",
                          step_id=step_id,
                          result_success=result.success) as debug_logger:
            
            step = self.workflow.get_step_by_id(step_id)
            if not step:
                log_step_detail("ERROR: Step not found in workflow", step_id=step_id)
                raise ValueError(f"Step '{step_id}' not found in workflow.")

            log_step_detail("Step found in workflow",
                           step_name=step.get('name', 'Unknown'),
                           step_script=step.get('script', 'No script'))

            is_first_run = self.get_state(step_id) == "pending"
            snapshot_items = step.get("snapshot_items", [])

            log_step_detail("Current step state analysis",
                           current_state=self.get_state(step_id),
                           is_first_run=is_first_run,
                           snapshot_items=snapshot_items)

            # Two-factor success detection: exit code and success marker (native execution)
            exit_code_success = result.success
            script_name = step.get("script", "")
            
            log_step_detail("Starting success marker check",
                           script_name=script_name,
                           exit_code_success=exit_code_success)
            
            marker_file_success = self._check_success_marker(script_name)
            
            log_step_detail("Success marker check completed",
                           marker_file_success=marker_file_success,
                           marker_file_path=f".workflow_status/{Path(script_name).stem}.success" if script_name else "N/A")
            
            # Both conditions must be true for actual success
            actual_success = exit_code_success and marker_file_success
            
            log_step_detail("Final success determination",
                           exit_code_success=exit_code_success,
                           marker_file_success=marker_file_success,
                           actual_success=actual_success)
            
            if debug_logger:
                debug_logger.info("Processing step result",
                                step_id=step_id,
                                step_name=step.get('name', 'Unknown'),
                                script_name=script_name,
                                exit_code_success=exit_code_success,
                                marker_file_success=marker_file_success,
                                actual_success=actual_success,
                                is_first_run=is_first_run,
                                execution_mode="native")
            
            # Provide detailed user feedback about what failed
            if exit_code_success and not marker_file_success:
                failure_msg = f"❌ STEP FAILED: '{step.get('name', step_id)}' - Script did not complete successfully"
                print(failure_msg)
                print("   Script exited with code 0 but no success marker found.")
                
                log_warning("Step failed: Exit code success but no marker file",
                           step_id=step_id,
                           script_name=script_name,
                           exit_code_success=exit_code_success,
                           marker_file_success=marker_file_success)
                
            elif not exit_code_success:
                failure_msg = f"❌ STEP FAILED: '{step.get('name', step_id)}' - Script execution failed"
                print(failure_msg)
                print("   Script exited with non-zero error code.")
                
                log_error("Step failed: Script execution error",
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

            # Handle the result based on our two-factor success detection
            if actual_success:
                log_step_detail("=== ATTEMPTING ATOMIC STATE UPDATE ===",
                               target_state="completed",
                               current_state=self.get_state(step_id))
                
                # ATOMIC STATE UPDATE: Use try-catch to ensure state update completes
                try:
                    # Read current state before update
                    pre_update_state = self.state_manager.load()
                    log_step_detail("Pre-update state loaded",
                                   pre_update_state=pre_update_state,
                                   step_current_status=pre_update_state.get(step_id, "unknown"))
                    
                    # Perform the atomic state update
                    self.update_state(step_id, "completed")
                    
                    # Verify the update succeeded
                    post_update_state = self.state_manager.load()
                    updated_status = post_update_state.get(step_id, "unknown")
                    
                    log_step_detail("Post-update state verification",
                                   post_update_state=post_update_state,
                                   step_updated_status=updated_status,
                                   update_successful=(updated_status == "completed"))
                    
                    if updated_status == "completed":
                        log_step_detail("✅ ATOMIC STATE UPDATE SUCCESSFUL")
                        
                        success_msg = f"✅ STEP COMPLETED: '{step.get('name', step_id)}' - All operations successful"
                        print(success_msg)
                        print("   • Script executed successfully")
                        print("   • Success marker created")
                        print("   • Workflow state updated atomically")
                        
                        log_info("Workflow step completed successfully",
                                step_id=step_id,
                                step_name=step.get('name', 'Unknown'),
                                exit_code_success=exit_code_success,
                                marker_file_success=marker_file_success,
                                execution_mode="native")
                    else:
                        log_step_detail("❌ ATOMIC STATE UPDATE FAILED - State not updated",
                                       expected_status="completed",
                                       actual_status=updated_status)
                        print(f"❌ WARNING: Step {step_id} completed successfully but state update failed!")
                        print(f"   Expected: completed, Actual: {updated_status}")
                        
                except Exception as state_update_error:
                    log_step_detail("❌ ATOMIC STATE UPDATE EXCEPTION",
                                   error_type=type(state_update_error).__name__,
                                   error_message=str(state_update_error))
                    print(f"❌ CRITICAL: State update failed with exception: {state_update_error}")
                    # Re-raise to ensure the error is visible
                    raise
                
                # Note: "after" snapshots removed for simplified undo system
                # Only "before" snapshots are now used for undo functionality
            else:
                # Step failed - log the failure
                log_error("Workflow step failed",
                         step_id=step_id,
                         step_name=step.get('name', 'Unknown'),
                         exit_code_success=exit_code_success,
                         marker_file_success=marker_file_success,
                         is_first_run=is_first_run,
                         execution_mode="native")
                
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
            
            log_step_detail("=== STEP RESULT HANDLING COMPLETED ===",
                           final_step_state=self.get_state(step_id),
                           processing_successful=True)

    def terminate_script(self, step_id: str) -> bool:
        """
        Terminates a running script and rolls back to the snapshot taken before the step started.
        
        Args:
            step_id: The ID of the step whose script should be terminated
            
        Returns:
            bool: True if script was terminated and rollback successful, False if no script was running
        """
        # Check if script is actually running
        log_info("Script termination requested", step_id=step_id)
        
        is_running = self.script_runner.is_running()
        log_info("Script runner status check", is_running=is_running, step_id=step_id)
        
        if not is_running:
            log_warning("Script termination failed - no running script", step_id=step_id)
            return False
        
        step = self.workflow.get_step_by_id(step_id)
        if not step:
            log_error("Script termination failed - step not found", step_id=step_id)
            raise ValueError(f"Step '{step_id}' not found in workflow.")
        
        log_info("Script termination proceeding", step_id=step_id, step_name=step.get('name', 'Unknown'))
        
        # Terminate the running script
        log_info("Calling script runner terminate method", step_id=step_id)
        self.script_runner.terminate()
        log_info("Script runner terminate method completed", step_id=step_id)
        
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

    # Native execution only - Smart Sync methods removed
    # All synchronization overhead eliminated for performance
