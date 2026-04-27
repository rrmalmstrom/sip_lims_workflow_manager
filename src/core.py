import ast
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.logic import StateManager, SnapshotManager, ScriptRunner, RunResult, RollbackError
# Native execution only - Smart Sync removed
from src.enhanced_debug_logger import (
    debug_context, log_info, log_error, log_warning,
    debug_enabled
)


def parse_snapshot_items_from_script(script_path: Path) -> List[str]:
    """
    Reads SNAPSHOT_ITEMS from a workflow script without executing it.
    Uses Python's ast module for safe static analysis — no import side effects.

    Returns the list of strings declared in SNAPSHOT_ITEMS.
    Raises ValueError if SNAPSHOT_ITEMS is not found — caller must abort the
    step and display a clear error to the user.
    """
    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SNAPSHOT_ITEMS":
                    return ast.literal_eval(node.value)
    raise ValueError(
        f"SNAPSHOT_ITEMS not found in {script_path.name}. "
        f"Cannot proceed — add SNAPSHOT_ITEMS to the script before running."
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
        self.auxiliary_scripts: List[Dict[str, Any]] = self._data.get("auxiliary_scripts", [])

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

    def get_auxiliary_script_by_id(self, aux_id: str) -> Optional[Dict[str, Any]]:
        """Finds an auxiliary script entry by its ID. Returns None if not found."""
        for aux in self.auxiliary_scripts:
            if aux.get("id") == aux_id:
                return aux
        return None

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
        Creates a manifest + selective snapshot for each skipped step so that
        undo can work past the skip point.
        Returns a message describing the action taken.
        """
        # Validate target step exists
        target_step = self.workflow.get_step_by_id(target_step_id)
        if not target_step:
            raise ValueError(f"Step {target_step_id} not found")

        # Initialize ALL steps in the workflow state for consistency
        target_step_found = False
        steps_skipped = 0
        prev_manifest_path = None

        for step in self.workflow.steps:
            step_id = step['id']

            if step_id == target_step_id:
                target_step_found = True
                # Mark target step as pending
                self.update_state(step_id, 'pending')
            elif not target_step_found:
                # For each skipped step: write a manifest + empty selective snapshot
                # snapshot_items=[] because no script ran — nothing to back up.
                # The manifest captures the current folder state as the baseline
                # for this skipped step, enabling undo past the skip point.
                run_number = 1
                manifest_path, current_scan = self.snapshot_manager.scan_manifest(step_id, run_number)
                self.snapshot_manager.take_selective_snapshot(
                    step_id, run_number,
                    snapshot_items=[],
                    prev_manifest_path=prev_manifest_path,
                    current_scan=current_scan,
                )
                prev_manifest_path = manifest_path
                # Mark step as skipped and record in completion order
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

        Pre-run sequence (new selective snapshot system):
          1. Resolve the script path and parse SNAPSHOT_ITEMS from it (abort if missing)
          2. Determine run_number
          3. Write manifest (fast path-only scan)
          4. Write selective snapshot ZIP (SNAPSHOT_ITEMS + newly-added user files)
          5. Launch the script asynchronously
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

        # --- Resolve script path and parse SNAPSHOT_ITEMS ---
        script_filename = Path(step["script"]).name
        script_full_path = self.script_path / script_filename

        try:
            snapshot_items = parse_snapshot_items_from_script(script_full_path)
        except ValueError as e:
            # SNAPSHOT_ITEMS missing — abort with a clear error, do not run the script
            print(f"❌ CANNOT RUN STEP: {e}")
            log_error("run_step aborted: SNAPSHOT_ITEMS missing from script",
                     step_id=step_id, script=str(script_full_path), error=str(e))
            return
        except FileNotFoundError as e:
            print(f"❌ CANNOT RUN STEP: Script not found — {e}")
            log_error("run_step aborted: script file not found",
                     step_id=step_id, script=str(script_full_path), error=str(e))
            return

        # --- Determine run number ---
        allow_rerun = step.get('allow_rerun', False)
        run_number = self.snapshot_manager.get_next_run_number(step_id, allow_rerun)

        # --- Find previous manifest for diff (newly-added user file detection) ---
        completion_order = self.state_manager.get_completion_order()
        prev_manifest_path: Optional[Path] = None
        if completion_order:
            prev_step_id = completion_order[-1]
            prev_run = self.snapshot_manager.get_effective_run_number(prev_step_id)
            if prev_run > 0:
                candidate = (self.snapshot_manager.snapshots_dir /
                             f"{prev_step_id}_run_{prev_run}_manifest.json")
                if candidate.exists():
                    prev_manifest_path = candidate

        # --- Write manifest and capture scan result for reuse ---
        manifest_path, current_scan = self.snapshot_manager.scan_manifest(step_id, run_number)

        # --- Write selective snapshot ZIP (reuses scan — no second walk) ---
        self.snapshot_manager.take_selective_snapshot(
            step_id, run_number, snapshot_items, prev_manifest_path,
            current_scan=current_scan,
        )

        if debug_logger:
            log_info("Selective snapshot created",
                    step_id=step_id, run_number=run_number,
                    snapshot_items=snapshot_items,
                    prev_manifest=str(prev_manifest_path))

        # --- Prepare arguments for the script ---
        args = []
        if "inputs" in step:
            for i, input_def in enumerate(step["inputs"]):
                input_key = f"{step_id}_input_{i}"
                value = user_inputs.get(input_key)
                if value:
                    if input_def.get("arg"):
                        args.append(input_def["arg"])
                    args.append(value)

        # --- Start the script asynchronously ---
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

            log_step_detail("Current step state analysis",
                           current_state=self.get_state(step_id),
                           is_first_run=is_first_run)

            # Two-factor success detection: exit code and success marker (native execution)
            exit_code_success = result.success
            script_name = step.get("script", "")

            # Determine the run number for this result so we can look for the
            # run-number-specific marker (e.g. script.run_3.success).
            result_run_number = self.snapshot_manager.get_current_run_number(step_id)

            log_step_detail("Starting success marker rename + check",
                           script_name=script_name,
                           exit_code_success=exit_code_success,
                           result_run_number=result_run_number)

            # --- Rename flat marker → run-number-specific marker ---
            # Individual scripts write a flat ``<script_stem>.success`` file.
            # We rename it to ``<script_stem>.run_<N>.success`` immediately
            # after the script exits so that _check_success_marker() can
            # distinguish a fresh marker (this run) from a stale one (prior run).
            if script_name:
                script_stem = Path(script_name).stem
                status_dir = self.path / ".workflow_status"
                flat_marker = status_dir / f"{script_stem}.success"
                run_marker = status_dir / f"{script_stem}.run_{result_run_number}.success"
                if flat_marker.exists():
                    try:
                        flat_marker.rename(run_marker)
                        log_step_detail("Renamed flat marker to run-specific marker",
                                       flat_marker=str(flat_marker),
                                       run_marker=str(run_marker))
                    except OSError as e:
                        log_step_detail("WARNING: Could not rename success marker",
                                       error=str(e))

            marker_file_success = self._check_success_marker(script_name, result_run_number)

            log_step_detail("Success marker check completed",
                           marker_file_success=marker_file_success,
                           marker_file_path=f".workflow_status/{Path(script_name).stem}.run_{result_run_number}.success" if script_name else "N/A")
            
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
                
                # Snapshot ZIP and manifest remain in .snapshots/ as the undo record
            else:
                # Step failed — automatic rollback using the new restore_snapshot()
                log_error("Workflow step failed",
                         step_id=step_id,
                         step_name=step.get('name', 'Unknown'),
                         exit_code_success=exit_code_success,
                         marker_file_success=marker_file_success,
                         is_first_run=is_first_run,
                         execution_mode="native")

                run_number = self.snapshot_manager.get_current_run_number(step_id)
                if run_number > 0:
                    log_info("Starting automatic rollback for failed step",
                            step_id=step_id, run_number=run_number)
                    # restore_snapshot() raises RollbackError on failure — let it
                    # propagate so the UI can display a critical recovery alert.
                    self.snapshot_manager.restore_snapshot(step_id, run_number)
                    # Remove the snapshot pair — it was consumed by rollback
                    self.snapshot_manager.remove_run_snapshots_from(step_id, run_number)
                    log_info("Automatic rollback completed successfully",
                             step_id=step_id, run_number=run_number)
                else:
                    log_warning("No snapshot available for automatic rollback",
                                step_id=step_id)
                    # No snapshot means we cannot restore — raise so the UI knows
                    raise RollbackError(
                        step_id=step_id,
                        run_number=0,
                        reason=(
                            "No pre-run snapshot was found. The project folder may "
                            "contain partial changes from the failed script. "
                            "Manual inspection is required."
                        ),
                    )

                # After rollback, workflow_state.json is restored to its pre-run
                # state (because it is included in snapshots).
                #
                # For a FIRST-RUN failure (is_first_run is True): the step was
                # "pending" before this run; the restored state reflects that.
                # Explicitly set to "pending" to be safe.
                #
                # For a RERUN failure (is_first_run is False): the step was
                # "completed" before this run; the restored state already shows
                # "completed" (reflecting the last successful run).  Do NOT
                # overwrite it with "pending" — the prior successful run is still
                # valid and the UI should show the step as completed.
                if is_first_run:
                    self.update_state(step_id, "pending")
                    log_info("Automatic rollback: step marked as pending after first-run failure",
                             step_id=step_id)
                else:
                    # Rerun failure: rollback already restored "completed" state.
                    # No state change needed.
                    log_info("Automatic rollback: step remains completed — "
                             "prior successful run is still valid",
                             step_id=step_id, run_number=run_number)
            
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

        # Capture is_first_run BEFORE the rollback restores workflow_state.json.
        # This mirrors the same pattern used in handle_step_result():
        #   - "pending"   → this was the first attempt (step had never succeeded)
        #   - "completed" → this is a rerun (step had at least one prior success)
        is_first_run = self.get_state(step_id) == "pending"
        log_info("Terminate: captured is_first_run before rollback",
                 step_id=step_id, is_first_run=is_first_run)
        
        # Terminate the running script
        log_info("Calling script runner terminate method", step_id=step_id)
        self.script_runner.terminate()
        log_info("Script runner terminate method completed", step_id=step_id)
        
        # Get the current run number to find the correct pre-run snapshot
        run_number = self.snapshot_manager.get_current_run_number(step_id)
        if run_number == 0:
            run_number = 1  # If no runs recorded yet, assume this is run 1

        # Restore to the pre-run snapshot (state before script started).
        # For a rerun, this restore will put workflow_state.json back to
        # "completed" (the state from the last successful run).
        # restore_snapshot() raises RollbackError on failure — let it propagate
        # so the UI can display a critical recovery alert.
        if self.snapshot_manager.snapshot_exists(step_id, run_number):
            self.snapshot_manager.restore_snapshot(step_id, run_number)
            # Remove the snapshot pair — it was consumed by the termination rollback
            self.snapshot_manager.remove_run_snapshots_from(step_id, run_number)
            log_info("Terminate: restored project to pre-run state",
                     step_id=step_id, run_number=run_number)
        else:
            log_warning(
                "Terminate: no snapshot found — script terminated but no rollback performed",
                step_id=step_id, run_number=run_number,
            )
        
        # Remove any success marker that might have been created.
        # The script may have written the flat marker before being killed;
        # handle_step_result() may also have already renamed it to the
        # run-number-specific form.  Clean up both to be safe.
        script_name = step.get("script", "")
        if script_name:
            script_stem = Path(script_name).stem
            status_dir = self.path / ".workflow_status"

            # Flat marker (written by the script, not yet renamed)
            flat_marker = status_dir / f"{script_stem}.success"
            if flat_marker.exists():
                flat_marker.unlink()
                log_info("Terminate: removed flat success marker",
                         script=script_stem)

            # Run-number-specific marker (already renamed by handle_step_result)
            run_marker = status_dir / f"{script_stem}.run_{run_number}.success"
            if run_marker.exists():
                run_marker.unlink()
                log_info("Terminate: removed run-specific success marker",
                         script=script_stem, run_number=run_number)

        # After rollback, workflow_state.json is restored to its pre-run state.
        #
        # For a FIRST-RUN termination (is_first_run is True): the step was
        # "pending" before this run; the restored state reflects that.
        # Explicitly set to "pending" to be safe (handles the no-snapshot case).
        #
        # For a RERUN termination (is_first_run is False): the step was
        # "completed" before this run; the restored state already shows
        # "completed" (reflecting the last successful run).  Do NOT overwrite
        # it with "pending" — the prior successful run is still valid and the
        # UI should show the step as completed.
        if is_first_run:
            self.update_state(step_id, "pending")
            log_info("Terminate: step marked as pending after first-run termination",
                     step_id=step_id)
        else:
            # Rerun termination: rollback already restored "completed" state.
            # No state change needed.
            log_info("Terminate: step remains completed — prior successful run is still valid",
                     step_id=step_id, run_number=run_number)
        
        return True

    def run_auxiliary_script(self, aux_id: str):
        """
        Starts an auxiliary script asynchronously.

        Auxiliary scripts:
        - Can be launched at any time regardless of workflow state.
        - NEVER modify workflow_state.json (not even temporarily).
        - Take a manifest + empty selective snapshot before running so that
          automatic rollback is possible on failure.
        - Must write a <script_stem>.success marker file (same contract as
          workflow scripts) for the two-factor success check to work.

        On success: handle_auxiliary_result() deletes the snapshot, manifest,
        and success marker — leaving no trace in the workflow tracking system.
        On failure: handle_auxiliary_result() rolls back from the snapshot.
        """
        aux = self.workflow.get_auxiliary_script_by_id(aux_id)
        if not aux:
            raise ValueError(f"Auxiliary script '{aux_id}' not found in workflow.")

        script_filename = Path(aux["script"]).name
        script_full_path = self.script_path / script_filename

        if not script_full_path.exists():
            raise FileNotFoundError(
                f"Auxiliary script not found: {script_full_path}"
            )

        log_info("run_auxiliary_script: starting", aux_id=aux_id,
                 script=str(script_full_path))

        # Always run_number=1 for auxiliary scripts (no rerun tracking).
        run_number = 1

        # Write manifest and take an empty selective snapshot.
        # snapshot_items=[] means no specific files are backed up by name —
        # the manifest diff will still catch any newly-created files on failure.
        # This is the same pattern used by skip_to_step() for skipped steps.
        manifest_path, current_scan = self.snapshot_manager.scan_manifest(
            aux_id, run_number
        )
        self.snapshot_manager.take_selective_snapshot(
            aux_id, run_number,
            snapshot_items=[],
            prev_manifest_path=None,   # no previous manifest needed for aux scripts
            current_scan=current_scan,
        )

        log_info("run_auxiliary_script: snapshot taken", aux_id=aux_id,
                 run_number=run_number)

        # Launch the script — auxiliary scripts take no arguments.
        self.script_runner.run(aux["script"], args=[])

    def handle_auxiliary_result(self, aux_id: str, result: RunResult):
        """
        Handles the result of an auxiliary script.

        INVARIANT: workflow_state.json is NEVER read, written, or modified
        by this method. The JSON is captured passively in the manifest scan
        but is never changed.

        On success (exit code 0 + marker present):
          1. Rename flat marker → run-specific marker (same as handle_step_result).
          2. Verify two-factor success.
          3. Delete run-specific success marker.
          4. Delete snapshot ZIP and manifest.
          workflow_state.json is NOT touched.

        On failure:
          1. Rollback from snapshot (restore_snapshot).
          2. Delete snapshot ZIP and manifest.
          3. Clean up any stale marker files.
          workflow_state.json is NOT touched.
        """
        aux = self.workflow.get_auxiliary_script_by_id(aux_id)
        if not aux:
            raise ValueError(f"Auxiliary script '{aux_id}' not found in workflow.")

        script_name = aux.get("script", "")
        run_number = 1  # auxiliary scripts always use run_number=1

        log_info("handle_auxiliary_result: processing result",
                 aux_id=aux_id, result_success=result.success)

        # --- Rename flat marker → run-specific marker (same as handle_step_result) ---
        if script_name:
            script_stem = Path(script_name).stem
            status_dir = self.path / ".workflow_status"
            flat_marker = status_dir / f"{script_stem}.success"
            run_marker = status_dir / f"{script_stem}.run_{run_number}.success"
            if flat_marker.exists():
                try:
                    flat_marker.rename(run_marker)
                    log_info("handle_auxiliary_result: renamed flat marker to run-specific",
                             flat_marker=str(flat_marker), run_marker=str(run_marker))
                except OSError as e:
                    log_warning("handle_auxiliary_result: could not rename marker",
                                error=str(e))

        # --- Two-factor success check (same as handle_step_result) ---
        exit_code_success = result.success
        marker_file_success = self._check_success_marker(script_name, run_number)
        actual_success = exit_code_success and marker_file_success

        log_info("handle_auxiliary_result: success determination",
                 exit_code_success=exit_code_success,
                 marker_file_success=marker_file_success,
                 actual_success=actual_success)

        # Helper: delete snapshot ZIP and manifest for this aux run
        def _cleanup_snapshot_and_manifest():
            self.snapshot_manager.remove_all_run_snapshots(aux_id)
            manifest_path = (
                self.snapshot_manager.snapshots_dir
                / f"{aux_id}_run_{run_number}_manifest.json"
            )
            if manifest_path.exists():
                manifest_path.unlink()
                log_info("handle_auxiliary_result: deleted manifest",
                         manifest=str(manifest_path))

        if actual_success:
            # SUCCESS: clean up all temporary artifacts, leave no trace.
            # 1. Delete the run-specific success marker.
            if script_name:
                script_stem = Path(script_name).stem
                status_dir = self.path / ".workflow_status"
                run_marker = status_dir / f"{script_stem}.run_{run_number}.success"
                if run_marker.exists():
                    run_marker.unlink()
                    log_info("handle_auxiliary_result: deleted success marker",
                             marker=str(run_marker))

            # 2. Delete snapshot ZIP and manifest.
            _cleanup_snapshot_and_manifest()

            log_info("handle_auxiliary_result: SUCCESS — all artifacts cleaned up",
                     aux_id=aux_id)
            # workflow_state.json is NOT touched — this is intentional.

        else:
            # FAILURE: rollback from snapshot, then clean up.
            log_error("handle_auxiliary_result: FAILURE — rolling back",
                      aux_id=aux_id, exit_code_success=exit_code_success,
                      marker_file_success=marker_file_success)

            if self.snapshot_manager.snapshot_exists(aux_id, run_number):
                # restore_snapshot raises RollbackError on failure — let it propagate
                # so the UI can display a critical recovery alert.
                self.snapshot_manager.restore_snapshot(aux_id, run_number)
                self.snapshot_manager.remove_run_snapshots_from(aux_id, run_number)
                log_info("handle_auxiliary_result: rollback completed", aux_id=aux_id)
            else:
                log_warning("handle_auxiliary_result: no snapshot found for rollback",
                            aux_id=aux_id)

            # Clean up manifest.
            _cleanup_snapshot_and_manifest()

            # Clean up any stale marker files left by the failed script.
            if script_name:
                script_stem = Path(script_name).stem
                status_dir = self.path / ".workflow_status"
                for marker in [
                    status_dir / f"{script_stem}.success",
                    status_dir / f"{script_stem}.run_{run_number}.success",
                ]:
                    if marker.exists():
                        marker.unlink()
                        log_info("handle_auxiliary_result: cleaned up stale marker",
                                 marker=str(marker))

            # workflow_state.json is NOT touched — this is intentional.

    def _check_success_marker(self, script_name: str, run_number: int) -> bool:
        """
        Check if a script completed successfully by looking for its
        run-number-specific success marker file.

        The marker is named ``<script_stem>.run_<N>.success`` (e.g.
        ``SPS_initiate_project_folder_and_make_sort_plate_labels.run_3.success``).
        handle_step_result() renames the flat ``<script_stem>.success`` written
        by the individual script to this run-number-specific name immediately
        after the script exits, before this check is performed.

        A stale marker from a previous successful run (e.g. ``.run_2.success``)
        will never match the current run number, so it is correctly rejected.
        """
        if not script_name:
            return True  # No script name, can't check marker

        script_stem = Path(script_name).stem
        status_dir = self.path / ".workflow_status"
        success_file = status_dir / f"{script_stem}.run_{run_number}.success"
        return success_file.exists()

    # Native execution only - Smart Sync methods removed
    # All synchronization overhead eliminated for performance
