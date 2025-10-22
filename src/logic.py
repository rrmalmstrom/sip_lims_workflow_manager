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

    def get_next_run_number(self, step_id: str) -> int:
        """
        Gets the next run number for a step by checking existing run snapshots.
        Returns 1 for first run, 2 for second run, etc.
        """
        existing_runs = list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip"))
        if not existing_runs:
            return 1
        
        # Extract run numbers from existing snapshots
        run_numbers = []
        for snapshot in existing_runs:
            try:
                # Parse filename like "step_id_run_2_complete.zip"
                parts = snapshot.stem.split('_')
                # Find 'run' and get the number after it
                for i, part in enumerate(parts):
                    if part == 'run' and i + 1 < len(parts):
                        run_numbers.append(int(parts[i + 1]))
                        break
            except (ValueError, IndexError):
                continue
        
        return max(run_numbers, default=0) + 1

    def get_latest_run_snapshot(self, step_id: str) -> str:
        """
        Gets the snapshot name for the most recent run of a step.
        Returns None if no run snapshots exist.
        """
        existing_runs = list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip"))
        if not existing_runs:
            return None
        
        # Find the highest run number
        latest_run = 0
        for snapshot in existing_runs:
            try:
                parts = snapshot.stem.split('_')
                # Find 'run' and get the number after it
                for i, part in enumerate(parts):
                    if part == 'run' and i + 1 < len(parts):
                        run_num = int(parts[i + 1])
                        if run_num > latest_run:
                            latest_run = run_num
                        break
            except (ValueError, IndexError):
                continue
        
        return f"{step_id}_run_{latest_run}" if latest_run > 0 else None

    def get_current_run_number(self, step_id: str) -> int:
        """
        Gets the current run number for a step (highest existing run).
        Returns 0 if no runs exist.
        """
        existing_runs = list(self.snapshots_dir.glob(f"{step_id}_run_*_complete.zip"))
        if not existing_runs:
            return 0
        
        # Find the highest run number
        latest_run = 0
        for snapshot in existing_runs:
            try:
                parts = snapshot.stem.split('_')
                for i, part in enumerate(parts):
                    if part == 'run' and i + 1 < len(parts):
                        run_num = int(parts[i + 1])
                        if run_num > latest_run:
                            latest_run = run_num
                        break
            except (ValueError, IndexError):
                continue
        
        return latest_run

    def snapshot_exists(self, snapshot_name: str) -> bool:
        """Check if a snapshot exists."""
        zip_path = self.snapshots_dir / f"{snapshot_name}_complete.zip"
        return zip_path.exists()

    def get_effective_run_number(self, step_id: str) -> int:
        """
        Gets the effective current run number by checking which 'after' snapshots exist
        and finding the highest one that represents the current state.
        """
        # Check which 'after' snapshots exist
        after_snapshots = list(self.snapshots_dir.glob(f"{step_id}_run_*_after_complete.zip"))
        if not after_snapshots:
            return 0
        
        # Find the highest run number with an 'after' snapshot
        highest_run = 0
        for snapshot in after_snapshots:
            try:
                parts = snapshot.stem.split('_')
                for i, part in enumerate(parts):
                    if part == 'run' and i + 1 < len(parts):
                        run_num = int(parts[i + 1])
                        if run_num > highest_run:
                            highest_run = run_num
                        break
            except (ValueError, IndexError):
                continue
        
        return highest_run

    def remove_run_snapshots_from(self, step_id: str, run_number: int):
        """
        Remove all run snapshots from the specified run number onwards.
        This is used to track which runs have been undone.
        """
        # Remove 'after' snapshots from this run onwards
        snapshots_to_remove = list(self.snapshots_dir.glob(f"{step_id}_run_*_after_complete.zip"))
        
        for snapshot in snapshots_to_remove:
            try:
                parts = snapshot.stem.split('_')
                for i, part in enumerate(parts):
                    if part == 'run' and i + 1 < len(parts):
                        run_num = int(parts[i + 1])
                        if run_num >= run_number:
                            snapshot.unlink()
                            print(f"UNDO: Removed snapshot {snapshot.name}")
                        break
            except (ValueError, IndexError):
                continue

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

    def take_complete_snapshot(self, step_id: str):
        """
        Creates a complete snapshot of the entire project directory.
        Excludes the .snapshots directory itself to avoid recursion.
        """
        zip_path = self.snapshots_dir / f"{step_id}_complete.zip"
        
        # Files and directories to exclude from snapshot
        exclude_patterns = {
            '.snapshots',
            '.workflow_status',
            '.workflow_logs',
            'workflow.yml',
            '__pycache__',
            '.DS_Store'
        }
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Collect all directories first to preserve their timestamps
            directories_to_add = []
            
            # First, add all files and collect directories
            for file_path in self.project_path.rglob('*'):
                # Skip if any part of the path matches exclude patterns
                if any(part in exclude_patterns for part in file_path.parts):
                    continue
                
                # Skip if it's a file/directory we want to exclude
                if file_path.name in exclude_patterns:
                    continue
                
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_path)
                    zf.write(file_path, relative_path)
                elif file_path.is_dir() and file_path != self.project_path:
                    # Collect directory info for later processing
                    relative_dir = file_path.relative_to(self.project_path)
                    directories_to_add.append((file_path, relative_dir))
            
            # Add directories with preserved timestamps
            for dir_path, relative_dir in directories_to_add:
                try:
                    # Get the directory's modification time
                    dir_stat = dir_path.stat()
                    dir_mtime = time.localtime(dir_stat.st_mtime)
                    
                    # Create a ZipInfo for the directory with original timestamp
                    dir_info = zipfile.ZipInfo(str(relative_dir) + '/')
                    dir_info.date_time = dir_mtime[:6]  # (year, month, day, hour, minute, second)
                    dir_info.external_attr = 0o755 << 16  # Directory permissions
                    
                    # Always add the directory entry with preserved timestamp
                    zf.writestr(dir_info, "")
                    
                    # Check if directory is empty and add placeholder if needed
                    is_empty = not any(dir_path.iterdir())
                    if is_empty:
                        # Add placeholder file to preserve empty directory
                        placeholder_path = str(relative_dir / ".keep_empty_dir")
                        placeholder_info = zipfile.ZipInfo(placeholder_path)
                        placeholder_info.date_time = dir_mtime[:6]
                        zf.writestr(placeholder_info, "")
                        
                except OSError:
                    pass  # Skip if we can't read directory
        
        print(f"SNAPSHOT: Complete project snapshot saved for step {step_id}")

    def restore_complete_snapshot(self, step_id: str):
        """
        Restores the complete project directory from a snapshot.
        This will remove all files not in the snapshot and restore the exact state.
        """
        zip_path = self.snapshots_dir / f"{step_id}_complete.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Complete snapshot for step '{step_id}' not found.")
        
        # Files and directories to preserve (never delete)
        preserve_patterns = {
            '.snapshots',
            '.workflow_status',
            '.workflow_logs',
            'workflow.yml',
            '__pycache__'
        }
        
        # Get list of files currently in project
        current_files = set()
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                # Skip preserved files
                if any(part in preserve_patterns for part in file_path.parts):
                    continue
                if file_path.name in preserve_patterns:
                    continue
                current_files.add(file_path.relative_to(self.project_path))
        
        # Get list of files in snapshot and identify empty directory placeholders
        snapshot_files = set()
        empty_dirs_to_preserve = set()
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if not name.endswith('/'):
                    path = Path(name)
                    if path.name == ".keep_empty_dir":
                        # This is a placeholder for an empty directory
                        empty_dirs_to_preserve.add(path.parent)
                    else:
                        snapshot_files.add(path)
        
        # Remove files that exist now but weren't in the snapshot
        files_to_remove = current_files - snapshot_files
        for rel_path in files_to_remove:
            file_path = self.project_path / rel_path
            if file_path.exists():
                file_path.unlink()
                print(f"RESTORE: Removed {rel_path}")
        
        # Remove empty directories that shouldn't exist (not in snapshot and not preserved)
        for dir_path in sorted(self.project_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and dir_path != self.project_path:
                # Skip preserved directories
                if any(part in preserve_patterns for part in dir_path.parts):
                    continue
                if dir_path.name in preserve_patterns:
                    continue
                
                # Skip directories that should be preserved from snapshot
                rel_dir = dir_path.relative_to(self.project_path)
                if rel_dir in empty_dirs_to_preserve:
                    continue
                
                try:
                    if not any(dir_path.iterdir()):  # Directory is empty
                        dir_path.rmdir()
                        print(f"RESTORE: Removed empty directory {rel_dir}")
                except OSError:
                    pass  # Directory not empty or other error
        
        # Extract snapshot files while preserving timestamps
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                # Extract the file or directory
                zf.extract(member, self.project_path)
                
                # Restore the original timestamp for both files and directories
                extracted_path = self.project_path / member.filename
                if extracted_path.exists():
                    try:
                        # Convert ZIP timestamp to Unix timestamp
                        timestamp = time.mktime(member.date_time + (0, 0, -1))
                        # Set both access time and modification time to the original
                        os.utime(extracted_path, (timestamp, timestamp))
                    except (OSError, ValueError):
                        # If timestamp restoration fails, continue without error
                        # This ensures rollback still works even if timestamp preservation fails
                        pass
        
        # Clean up placeholder files and ensure empty directories exist
        for empty_dir in empty_dirs_to_preserve:
            dir_path = self.project_path / empty_dir
            placeholder_file = dir_path / ".keep_empty_dir"
            
            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Remove placeholder file if it exists
            if placeholder_file.exists():
                placeholder_file.unlink()
        
        print(f"RESTORE: Complete project state restored from step {step_id}")

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

        # Extract files while preserving timestamps
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                # Extract the file or directory
                zf.extract(member, self.project_path)
                
                # Restore the original timestamp for both files and directories
                extracted_path = self.project_path / member.filename
                if extracted_path.exists():
                    try:
                        # Convert ZIP timestamp to Unix timestamp
                        timestamp = time.mktime(member.date_time + (0, 0, -1))
                        # Set both access time and modification time to the original
                        os.utime(extracted_path, (timestamp, timestamp))
                    except (OSError, ValueError):
                        # If timestamp restoration fails, continue without error
                        pass

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
    def __init__(self, project_path: Path, script_path: Path = None):
        self.project_path = project_path
        self.script_path = script_path or (project_path / "scripts")
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
        # Create hidden log directory if it doesn't exist
        log_dir = self.project_path / ".workflow_logs"
        log_dir.mkdir(exist_ok=True)
        debug_log_path = log_dir / "debug_script_execution.log"
        
        def log_debug(message):
            """Log debug info to file only (not to terminal output)"""
            try:
                with open(debug_log_path, "a") as f:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {message}")
                    f.flush()
            except:
                pass  # Don't let logging errors break execution
        
        def log_to_terminal(message):
            """Log message to terminal output only"""
            self.output_queue.put(message)
        
        try:
            # Log debug info to file only (not visible to user)
            log_debug("=== SCRIPT STARTING (PTY) ===\n")
            log_debug(f"Process PID: {self.process.pid if self.process else 'None'}\n")
            log_debug(f"Master FD: {self.master_fd}\n")
            log_debug(f"Project path: {self.project_path}\n")
            
            # Read output from pseudo-terminal in real-time
            # Give the process a moment to start and produce initial output
            time.sleep(0.05)  # Small delay to let process start
            
            while self.is_running_flag.is_set() and self.master_fd is not None:
                try:
                    # Check if process is still running
                    if self.process:
                        poll_result = self.process.poll()
                        if poll_result is not None:
                            # Process finished - do one final read to get any remaining output
                            log_debug(f"=== PROCESS FINISHED WITH POLL RESULT: {poll_result} ===\n")
                            # Try to read any remaining output before breaking
                            try:
                                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                                if ready:
                                    output = os.read(self.master_fd, 4096).decode('utf-8', errors='replace')
                                    if output:
                                        self.output_queue.put(output)
                            except OSError:
                                pass
                            break
                    
                    # Use select to check if there's data to read with shorter timeout for responsiveness
                    ready, _, _ = select.select([self.master_fd], [], [], 0.02)  # Reduced from 0.1 to 0.02
                    if ready:
                        try:
                            # Read available data - try to read more at once for better performance
                            output = os.read(self.master_fd, 4096).decode('utf-8', errors='replace')
                            if output:
                                self.output_queue.put(output)
                                # Immediately check for more data without waiting
                                continue
                        except OSError:
                            # PTY closed
                            break
                    else:
                        # No data ready, small sleep to prevent busy waiting
                        time.sleep(0.01)
                    
                except Exception as e:
                    log_debug(f"Error reading PTY output: {str(e)}\n")
                    break
            
            # Get the final exit code
            if self.process:
                return_code = self.process.wait()  # Ensure process is fully finished
                success = return_code == 0
                
                # Log debug info to file only (not visible to user)
                debug_msg = f"""=== SCRIPT EXECUTION COMPLETE (PTY) ===
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
                log_dir = self.project_path / ".workflow_logs"
                log_dir.mkdir(exist_ok=True)
                summary_path = log_dir / "last_script_result.txt"
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
            # Show error to user since this indicates a real problem
            log_to_terminal(f"Error: {str(e)}\n")
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
        script_path = self.script_path / script_filename
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script '{script_filename}' not found in '{self.script_path}'")

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

        # Clear the output and result queues to prevent old output from appearing
        # when the next script runs
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break

        self.process = None
        self.reader_thread = None

    def terminate(self):
        """Alias for stop() method for consistency with terminate_script functionality."""
        self.stop()