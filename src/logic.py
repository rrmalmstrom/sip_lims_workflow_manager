import json
import zipfile
import shutil
import subprocess
import sys
import datetime
import pty
import os
import select
import threading
import queue
import time
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class RunResult:
    """Holds the results of a script execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int

class StateManager:
    """Manages the state of a workflow."""
    def __init__(self, state_file_path: Path):
        self.path = state_file_path

    def load(self) -> Dict[str, str]:
        """Loads the current state from the state file."""
        if not self.path.exists():
            return {}
        with self.path.open('r') as f:
            return json.load(f)

    def save(self, state: Dict[str, str]):
        """Saves the given state to the state file."""
        with self.path.open('w') as f:
            json.dump(state, f, indent=2)

    def get_step_state(self, step_id: str) -> str:
        """Gets the status of a specific step."""
        state = self.load()
        return state.get(step_id, "pending")

    def update_step_state(self, step_id: str, status: str):
        """Updates the status of a specific step and saves it."""
        state = self.load()
        state[step_id] = status
        self.save(state)

class SnapshotManager:
    """Manages project snapshots."""
    def __init__(self, project_path: Path, snapshots_dir: Path):
        self.project_path = project_path
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(exist_ok=True)

    def take(self, step_id: str, items: List[str]):
        """Creates a zip archive of the specified items."""
        if not items:
            return
        
        zip_path = self.snapshots_dir / f"{step_id}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for item_name in items:
                item_path = self.project_path / item_name
                if item_path.exists():
                    if item_path.is_dir():
                        for file_path in item_path.rglob('*'):
                            zf.write(file_path, file_path.relative_to(self.project_path))
                    else:
                        zf.write(item_path, item_name)

    def restore(self, step_id: str, items: List[str]):
        """Restores the project state from a snapshot."""
        zip_path = self.snapshots_dir / f"{step_id}.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Snapshot for step '{step_id}' not found.")

        for item_name in items:
            item_path = self.project_path / item_name
            if item_path.exists():
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(self.project_path)

    def restore_file_from_latest_snapshot(self, filename: str) -> bool:
        """Finds the most recent snapshot and restores a single file from it."""
        snapshots = list(self.snapshots_dir.glob("*.zip"))
        if not snapshots:
            return False

        latest_snapshot = max(snapshots, key=lambda f: f.stat().st_mtime)
        
        with zipfile.ZipFile(latest_snapshot, 'r') as zf:
            if filename in zf.namelist():
                zf.extract(filename, self.project_path)
                return True
        return False

class ScriptRunner:
    """Executes workflow scripts using pseudo-terminal for interactive execution."""
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.output_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.reader_thread = None
        self.is_running_flag = threading.Event()

    def is_running(self):
        return self.is_running_flag.is_set()

    def _read_output_loop(self):
        """
        Reads output from the pseudo-terminal until the process finishes,
        then puts the final result in the result queue.
        """
        debug_log_path = self.project_path / "debug_script_execution.log"
        
        def log_debug(message):
            """Log to both output queue and file for backup"""
            self.output_queue.put(message)
            try:
                with open(debug_log_path, "a") as f:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {message}")
                    f.flush()
            except:
                pass  # Don't let logging errors break execution
        
        try:
            log_debug("=== SCRIPT STARTING (PTY) ===\n")
            log_debug(f"Process PID: {self.process.pid if self.process else 'None'}\n")
            log_debug(f"Master FD: {self.master_fd}\n")
            log_debug(f"Project path: {self.project_path}\n")
            
            # Read output from pseudo-terminal in real-time
            while self.is_running_flag.is_set() and self.master_fd is not None:
                try:
                    # Check if process is still running
                    if self.process:
                        poll_result = self.process.poll()
                        if poll_result is not None:
                            # Process finished
                            log_debug(f"=== PROCESS FINISHED WITH POLL RESULT: {poll_result} ===\n")
                            break
                    
                    # Use select to check if there's data to read
                    ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                    if ready:
                        try:
                            output = os.read(self.master_fd, 1024).decode('utf-8', errors='replace')
                            if output:
                                self.output_queue.put(output)
                        except OSError:
                            # PTY closed
                            break
                    
                except Exception as e:
                    log_debug(f"Error reading PTY output: {str(e)}\n")
                    break
            
            # Get the final exit code
            if self.process:
                return_code = self.process.wait()  # Ensure process is fully finished
                success = return_code == 0
                
                # Add comprehensive debug info to output AND file
                debug_msg = f"""
=== SCRIPT EXECUTION COMPLETE (PTY) ===
Exit Code: {return_code}
Success: {success}
Process Poll Result: {self.process.poll()}
Return Code Type: {type(return_code)}
=== END DEBUG INFO ===
"""
                log_debug(debug_msg)
                
                # Put the result in the queue
                result = RunResult(
                    success=success,
                    stdout="",  # We stream output in real-time, so this is empty
                    stderr="",  # PTY merges stderr into stdout
                    return_code=return_code
                )
                log_debug(f"=== PUTTING RESULT IN QUEUE: success={success}, return_code={return_code} ===\n")
                self.result_queue.put(result)
                
                # ALSO write a summary file that we can easily check
                summary_path = self.project_path / "last_script_result.txt"
                try:
                    with open(summary_path, "w") as f:
                        f.write(f"Last Script Execution Summary\n")
                        f.write(f"Exit Code: {return_code}\n")
                        f.write(f"Success: {success}\n")
                        f.write(f"Timestamp: {datetime.datetime.now()}\n")
                except:
                    pass

        except Exception as e:
            error_msg = f"[ERROR] Exception in script runner: {str(e)}\n"
            log_debug(error_msg)
            self.result_queue.put(RunResult(success=False, stdout="", stderr=str(e), return_code=-1))
        finally:
            self.is_running_flag.clear()
            log_debug("=== SCRIPT RUNNER THREAD ENDING ===\n")
            self.output_queue.put(None)  # Sentinel for end of output
            
            # Clean up PTY
            if self.master_fd is not None:
                try:
                    os.close(self.master_fd)
                except:
                    pass
                self.master_fd = None
            if self.slave_fd is not None:
                try:
                    os.close(self.slave_fd)
                except:
                    pass
                self.slave_fd = None

    def run(self, script_path_str: str, args: List[str] = None):
        """
        Executes a script using pseudo-terminal for interactive execution.
        This method is non-blocking.
        """
        if self.is_running():
            raise RuntimeError("A script is already running.")

        if args is None:
            args = []

        if getattr(sys, 'frozen', False):
            app_dir = Path(sys._MEIPASS).parent
        else:
            app_dir = Path(__file__).parent.parent

        script_filename = Path(script_path_str).name
        script_path = app_dir / "scripts" / script_filename
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script '{script_filename}' not found in '{app_dir / 'scripts'}'")

        python_executable = sys.executable
        command = [python_executable, "-u", str(script_path)] + args

        # Create pseudo-terminal
        self.master_fd, self.slave_fd = pty.openpty()

        # Start the subprocess with PTY
        self.process = subprocess.Popen(
            command,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            cwd=self.project_path,
            preexec_fn=os.setsid  # Create new session
        )

        # Start the output reading thread
        self.is_running_flag.set()
        self.reader_thread = threading.Thread(target=self._read_output_loop)
        self.reader_thread.start()

    def send_input(self, user_input: str):
        """Sends user input to the running script's stdin via PTY."""
        if self.master_fd is not None and self.is_running():
            try:
                os.write(self.master_fd, (user_input + "\n").encode('utf-8'))
            except Exception as e:
                self.output_queue.put(f"Error sending input: {str(e)}\n")

    def stop(self):
        """Forcefully stops the running script and reader thread."""
        if not self.is_running_flag.is_set():
            return

        self.is_running_flag.clear()
        
        if self.process:
            try:
                # Kill the process group to ensure all child processes are terminated
                os.killpg(os.getpgid(self.process.pid), 9)
            except Exception:
                try:
                    self.process.terminate()
                    # Give it a moment to terminate gracefully
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        self.process.kill()
                        self.process.wait()
                except Exception:
                    pass  # Process may already be dead
        
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        # Clean up PTY file descriptors
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except:
                pass
            self.master_fd = None
        if self.slave_fd is not None:
            try:
                os.close(self.slave_fd)
            except:
                pass
            self.slave_fd = None

        self.process = None
        self.reader_thread = None