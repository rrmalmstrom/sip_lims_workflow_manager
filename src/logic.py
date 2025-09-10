import json
import zipfile
import shutil
import subprocess
import sys
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

import os
import pty
import threading
import queue
import time
class ScriptRunner:
    """Executes workflow scripts in a pseudo-terminal."""
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.master_fd = None
        self.pid = None
        self.output_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.reader_thread = None
        self.is_running_flag = threading.Event()

    def is_running(self):
        return self.is_running_flag.is_set()

    def _read_and_wait_loop(self):
        """
        Reads output from the pty until the child process closes it,
        then waits for the process to get the exit code.
        """
        try:
            while self.is_running_flag.is_set():
                try:
                    output = os.read(self.master_fd, 1024)
                    if not output:  # This indicates the child has closed the pty fd, usually on exit
                        break
                    self.output_queue.put(output.decode(errors='ignore'))
                except (OSError, IOError):
                    break
            
            # Once the output stream is closed, wait for the process to terminate
            _, status = os.waitpid(self.pid, 0)
            return_code = os.WEXITSTATUS(status)
            
            # Add debugging output to the terminal
            debug_msg = f"\n[DEBUG] Script finished with exit code: {return_code}, success: {return_code == 0}\n"
            self.output_queue.put(debug_msg)
            
            self.result_queue.put(RunResult(success=return_code == 0, stdout="", stderr="", return_code=return_code))

        except Exception as e:
            self.result_queue.put(RunResult(success=False, stdout="", stderr=str(e), return_code=-1))
        finally:
            self.is_running_flag.clear()
            self.output_queue.put(None)  # Sentinel for end of output
            if self.master_fd:
                os.close(self.master_fd)

    def run(self, script_path_str: str, args: List[str] = None):
        """
        Executes a script in a pseudo-terminal, managed by a background thread.
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
        # Use a simpler approach: run the script directly but with proper error handling
        command = [python_executable, "-u", str(script_path)] + args

        self.pid, self.master_fd = pty.fork()

        if self.pid == 0:  # Child process
            os.chdir(self.project_path)
            os.execvp(command[0], command)
        else:  # Parent process
            self.is_running_flag.set()
            self.reader_thread = threading.Thread(target=self._read_and_wait_loop)
            self.reader_thread.start()


    def send_input(self, user_input: str):
        """Sends user input to the running script's stdin."""
        if self.master_fd is not None and self.is_running():
            os.write(self.master_fd, (user_input + "\n").encode())

    def stop(self):
        """Forcefully stops the running script and reader thread."""
        if not self.is_running_flag.is_set():
            return

        self.is_running_flag.clear()
        
        if self.pid:
            try:
                os.kill(self.pid, 9)
            except OSError:
                pass  # Process may already be dead
        
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        self.master_fd = None
        self.pid = None
        self.reader_thread = None