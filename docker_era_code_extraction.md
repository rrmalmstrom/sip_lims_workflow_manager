# Docker Era Code Extraction for Mac + VNC Integration
## Complete Code Capture Before Branch Switch

This document captures the exact code from the current Docker-era branch that needs to be integrated into the Mac + VNC baseline (commit 3d5ac82). This file will survive the branch switch and provide the code needed for integration.

---

## 1. Enhanced Debug Logger (src/debug_logger.py)

### PRESERVE: Core Debug Infrastructure (Docker-Independent)

```python
# Core debug logger class structure to preserve
import os
import sys
import json
import time
import platform
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import threading
from contextlib import contextmanager

try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False

class LogLevel(Enum):
    """Log levels for debugging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EnhancedDebugLogger:
    """
    Enhanced debug logger for Mac + VNC workflow manager.
    Adapted from Smart Sync debug logger, removing Docker-specific functionality.
    """
    
    def __init__(self, log_file: Optional[Path] = None, console_output: bool = True, 
                 log_level: LogLevel = LogLevel.INFO):
        """
        Initialize the enhanced debug logger.
        
        Args:
            log_file: Path to log file (default: project/.workflow_debug.log)
            console_output: Whether to output to console
            log_level: Minimum log level to record
        """
        self.log_level = log_level
        self.console_output = console_output
        self.session_id = self._generate_session_id()
        self.start_time = time.time()
        
        # Set up log file in centralized debug directory
        if log_file is None:
            # Create centralized debug directory in workflow manager root
            debug_dir = Path.cwd() / "debug_output"
            debug_dir.mkdir(exist_ok=True)
            self.log_file = debug_dir / "workflow_debug.log"
        else:
            self.log_file = Path(log_file)
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.operation_timers = {}
        self.performance_stats = {
            "workflow_operations": [],
            "script_executions": [],
            "vnc_sessions": [],
            "errors": []
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize log file with session header
        self._write_session_header()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for this debug session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"workflow_{timestamp}_{os.getpid()}"
    
    def _write_session_header(self):
        """Write session header to log file."""
        header_info = {
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "working_directory": str(Path.cwd()),
            "log_level": self.log_level.value
        }
        
        self._write_log_entry("SESSION_START", "Debug session started", header_info)
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on current log level."""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return level_order[level] >= level_order[self.log_level]
    
    def _write_log_entry(self, level: str, message: str, details: Optional[Dict] = None):
        """Write a structured log entry to file and optionally console."""
        # Handle special session levels that aren't in LogLevel enum
        if level in ["SESSION_START", "SESSION_END"]:
            log_level_check = LogLevel.INFO
        else:
            try:
                log_level_check = LogLevel(level)
            except ValueError:
                # Default to INFO for unknown levels
                log_level_check = LogLevel.INFO
        
        if not self._should_log(log_level_check):
            return
        
        with self._lock:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            log_entry = {
                "session_id": self.session_id,
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "details": details or {},
                "thread_id": threading.get_ident()
            }
            
            # Write to file
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                # Fallback to stderr if file write fails
                print(f"DEBUG LOGGER ERROR: Could not write to log file: {e}", file=sys.stderr)
            
            # Console output
            if self.console_output:
                self._print_console_message(level, message, details)
    
    def _print_console_message(self, level: str, message: str, details: Optional[Dict] = None):
        """Print formatted message to console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding for different levels
        if HAS_CLICK:
            if level == "DEBUG":
                click.secho(f"[{timestamp}] 🔍 DEBUG: {message}", fg='cyan', dim=True)
            elif level == "INFO":
                click.secho(f"[{timestamp}] ℹ️  INFO: {message}", fg='blue')
            elif level == "WARNING":
                click.secho(f"[{timestamp}] ⚠️  WARNING: {message}", fg='yellow')
            elif level == "ERROR":
                click.secho(f"[{timestamp}] ❌ ERROR: {message}", fg='red')
            elif level == "CRITICAL":
                click.secho(f"[{timestamp}] 💥 CRITICAL: {message}", fg='red', bold=True)
            else:
                click.echo(f"[{timestamp}] {level}: {message}")
        else:
            print(f"[{timestamp}] {level}: {message}")
        
        # Print details if provided and in debug mode
        if details and self.log_level == LogLevel.DEBUG:
            if HAS_CLICK:
                click.echo(f"    Details: {json.dumps(details, indent=2)}")
            else:
                print(f"    Details: {json.dumps(details, indent=2)}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._write_log_entry("DEBUG", message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._write_log_entry("INFO", message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._write_log_entry("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._write_log_entry("ERROR", message, kwargs)
        
        # Track error for analysis
        error_info = {
            "message": message,
            "details": kwargs,
            "timestamp": time.time(),
            "traceback": traceback.format_stack()
        }
        self.performance_stats["errors"].append(error_info)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._write_log_entry("CRITICAL", message, kwargs)
    
    @contextmanager
    def operation_timer(self, operation_name: str, **context):
        """Context manager for timing operations."""
        start_time = time.time()
        operation_id = f"{operation_name}_{int(start_time * 1000)}"
        
        self.debug(f"Starting operation: {operation_name}", 
                  operation_id=operation_id, context=context)
        
        try:
            yield operation_id
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"Operation failed: {operation_name}", 
                      operation_id=operation_id, duration=duration, 
                      error=str(e), context=context)
            raise
        else:
            duration = time.time() - start_time
            self.info(f"Operation completed: {operation_name}", 
                     operation_id=operation_id, duration=duration, context=context)
            
            # Track performance
            perf_data = {
                "operation": operation_name,
                "duration": duration,
                "timestamp": start_time,
                "context": context
            }
            self.performance_stats["workflow_operations"].append(perf_data)
```

### ADD: Mac + VNC Specific Logging Functions

```python
    def log_vnc_session_start(self, session_id: str, user: str, client_ip: str = None):
        """Log VNC session initiation."""
        details = {
            "vnc_session_id": session_id,
            "user": user,
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._write_log_entry("INFO", f"VNC session started for user {user}", details)
        self.performance_stats["vnc_sessions"].append(details)

    def log_native_script_execution(self, script_path: str, args: List[str], 
                                   working_dir: str = None):
        """Log native Python script execution."""
        details = {
            "script_path": str(script_path),
            "arguments": args,
            "working_directory": working_dir,
            "execution_method": "native_python"
        }
        self._write_log_entry("INFO", f"Executing native script: {script_path}", details)
        self.performance_stats["script_executions"].append(details)

    def log_workflow_step_native(self, step_id: str, success: bool, 
                                duration: float, output_summary: str = None):
        """Log workflow step execution in native environment."""
        details = {
            "step_id": step_id,
            "success": success,
            "duration_seconds": duration,
            "execution_environment": "native_python",
            "output_summary": output_summary
        }
        level = "INFO" if success else "ERROR"
        message = f"Workflow step {step_id} {'completed' if success else 'failed'}"
        self._write_log_entry(level, message, details)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for analysis."""
        current_time = time.time()
        session_duration = current_time - self.start_time
        
        summary = {
            "session_id": self.session_id,
            "session_duration": session_duration,
            "total_workflow_operations": len(self.performance_stats["workflow_operations"]),
            "total_script_executions": len(self.performance_stats["script_executions"]),
            "total_vnc_sessions": len(self.performance_stats["vnc_sessions"]),
            "total_errors": len(self.performance_stats["errors"]),
            "average_operation_duration": 0
        }
        
        # Calculate averages
        if self.performance_stats["workflow_operations"]:
            total_duration = sum(op["duration"] for op in self.performance_stats["workflow_operations"])
            summary["average_operation_duration"] = total_duration / len(self.performance_stats["workflow_operations"])
        
        return summary

    def export_debug_data(self, output_file: Optional[Path] = None) -> Path:
        """Export all debug data for analysis."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_dir = Path.cwd() / "debug_output"
            debug_dir.mkdir(exist_ok=True)
            output_file = debug_dir / f"workflow_debug_export_{timestamp}.json"
        
        export_data = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.start_time,
                "export_time": time.time(),
                "platform": platform.system(),
                "log_file": str(self.log_file)
            },
            "performance_stats": self.performance_stats,
            "performance_summary": self.get_performance_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.info(f"Debug data exported to: {output_file}")
        return output_file

    def close(self):
        """Close the debug logger and write session summary."""
        summary = self.get_performance_summary()
        self._write_log_entry("SESSION_END", "Debug session ended", summary)
        
        if self.console_output:
            if HAS_CLICK:
                click.echo("\n" + "="*50)
                click.secho("Workflow Debug Session Summary", fg='blue', bold=True)
                click.echo("="*50)
                click.echo(f"Session Duration: {summary['session_duration']:.2f}s")
                click.echo(f"Workflow Operations: {summary['total_workflow_operations']}")
                click.echo(f"Script Executions: {summary['total_script_executions']}")
                click.echo(f"VNC Sessions: {summary['total_vnc_sessions']}")
                click.echo(f"Errors: {summary['total_errors']}")
                if summary['average_operation_duration'] > 0:
                    click.echo(f"Average Operation Duration: {summary['average_operation_duration']:.3f}s")
                click.echo(f"Log File: {self.log_file}")
                click.echo("="*50)
            else:
                print(f"\nWorkflow Debug Summary:")
                print(f"Session Duration: {summary['session_duration']:.2f}s")
                print(f"Log File: {self.log_file}")

# Global logger instance
_global_logger: Optional[EnhancedDebugLogger] = None

def get_debug_logger(log_file: Optional[Path] = None, 
                    console_output: bool = True,
                    log_level: LogLevel = LogLevel.INFO) -> EnhancedDebugLogger:
    """Get or create the global enhanced debug logger."""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = EnhancedDebugLogger(log_file, console_output, log_level)
    
    return _global_logger

def close_debug_logger():
    """Close the global debug logger."""
    global _global_logger
    
    if _global_logger is not None:
        _global_logger.close()
        _global_logger = None

def debug_enabled() -> bool:
    """Check if debug logging is enabled via environment variable."""
    return os.getenv("WORKFLOW_DEBUG", "").lower() in ("true", "1", "yes", "on")

def get_debug_level() -> LogLevel:
    """Get debug level from environment variable."""
    level_str = os.getenv("WORKFLOW_DEBUG_LEVEL", "INFO").upper()
    try:
        return LogLevel(level_str)
    except ValueError:
        return LogLevel.INFO

@contextmanager
def debug_context(operation_name: str, **context):
    """Context manager for debugging operations with automatic logger setup."""
    if not debug_enabled():
        yield None
        return
    
    logger = get_debug_logger(log_level=get_debug_level())
    
    with logger.operation_timer(operation_name, **context) as operation_id:
        yield logger

# Convenience functions for common debugging scenarios
def log_error(message: str, **details):
    """Log error (convenience function)."""
    if debug_enabled():
        logger = get_debug_logger()
        logger.error(message, **details)

def log_info(message: str, **details):
    """Log info (convenience function)."""
    if debug_enabled():
        logger = get_debug_logger()
        logger.info(message, **details)

def log_warning(message: str, **details):
    """Log warning (convenience function)."""
    if debug_enabled():
        logger = get_debug_logger()
        logger.warning(message, **details)
```

---

## 2. Git Update Manager (src/git_update_manager.py) - PRESERVE ENTIRELY

```python
# PRESERVE: Complete git_update_manager.py (Docker-independent)
# This file is 100% Docker-independent and should be integrated as-is
# Key functions to preserve:
# - get_repository_config()
# - detect_script_repository_config()
# - GitUpdateManager class with all methods:
#   - get_current_version()
#   - get_latest_release()
#   - compare_versions()
#   - check_for_updates()
#   - update_to_latest()
#   - get_update_details()
# - create_update_managers() factory function

# NOTE: This entire file should be copied as-is to the Mac + VNC baseline
```

---

## 3. Scripts Updater (src/scripts_updater.py) - PRESERVE ENTIRELY

```python
# PRESERVE: Complete scripts_updater.py (Docker-independent)
# This file is 100% Docker-independent and should be integrated as-is
# Key functions to preserve:
# - ScriptsUpdater class with all methods:
#   - check_scripts_update()
#   - update_scripts()
#   - get_scripts_summary()
# - main() CLI interface

# NOTE: This entire file should be copied as-is to the Mac + VNC baseline
```

---

## 4. Workflow Utils (src/workflow_utils.py) - PRESERVE ENTIRELY

```python
# PRESERVE: Complete workflow_utils.py (Docker-independent)
# This file is 100% Docker-independent and should be integrated as-is
# Key functions to preserve:
# - get_workflow_template_path()
# - get_workflow_type_display()
# - validate_workflow_type()

# NOTE: This entire file should be copied as-is to the Mac + VNC baseline
```

---

## 5. Update Detector (src/update_detector.py) - EXTRACT GIT FUNCTIONS ONLY

### PRESERVE: Git-Only Functions

```python
# Extract these Git-only functions from update_detector.py:

def get_local_commit_sha(self) -> Optional[str]:
    """Get the current local git commit SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    return None

def get_remote_commit_sha(self, branch: str = "main") -> Optional[str]:
    """Get the latest commit SHA from GitHub for the specified branch."""
    api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/branches/{branch}"
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['commit']['sha']
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None

def get_commit_timestamp(self, commit_sha: str) -> Optional[datetime]:
    """Get the timestamp of a specific commit from GitHub API."""
    api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/commits/{commit_sha}"
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = json.loads(response.read().decode())
            timestamp_str = data['commit']['committer']['date']
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None

def is_commit_ancestor(self, ancestor_sha: str, descendant_sha: str) -> Optional[bool]:
    """Check if ancestor_sha is an ancestor of descendant_sha using git merge-base."""
    try:
        result = subprocess.run(
            ['git', 'merge-base', '--is-ancestor', ancestor_sha, descendant_sha],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None

# REMOVE: All Docker image detection methods
# DO NOT PRESERVE: Any methods with "docker", "image", "digest", "manifest" in the name
```

---

## 6. Native Python Launcher Code

### NEW: Native Python Launcher (run_native.py)

```python
#!/usr/bin/env python3
"""
Native Python launcher for SIP LIMS Workflow Manager
Replaces Docker-based execution with native Python
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional

def validate_python_version() -> bool:
    """Validate Python version meets requirements"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    return current_version >= required_version

def validate_dependencies() -> Dict[str, bool]:
    """Validate required dependencies are installed"""
    required_packages = [
        'streamlit', 'pyyaml', 'requests', 'click'
    ]
    
    validation_results = {}
    for package in required_packages:
        try:
            __import__(package)
            validation_results[package] = True
        except ImportError:
            validation_results[package] = False
    
    return validation_results

def setup_environment() -> Dict[str, str]:
    """Set up environment variables and paths"""
    env_vars = {}
    
    # Set workflow manager paths
    base_path = Path(__file__).parent
    env_vars['WORKFLOW_MANAGER_BASE'] = str(base_path)
    env_vars['WORKFLOW_TEMPLATES_PATH'] = str(base_path / 'templates')
    env_vars['WORKFLOW_SCRIPTS_PATH'] = str(Path.home() / '.sip_lims_workflow_manager')
    
    # Set Python path
    env_vars['PYTHONPATH'] = str(base_path)
    
    return env_vars

def start_streamlit_application(port: int = 8501) -> subprocess.Popen:
    """Start the Streamlit application"""
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ]
    
    return subprocess.Popen(cmd, cwd=Path(__file__).parent)

def main():
    """Main launcher function"""
    print("🧪 SIP LIMS Workflow Manager - Native Python Launcher")
    print("=" * 60)
    
    # Validate environment
    if not validate_python_version():
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    deps = validate_dependencies()
    missing_deps = [pkg for pkg, available in deps.items() if not available]
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements_native.txt")
        sys.exit(1)
    
    # Setup environment
    env_vars = setup_environment()
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment validated")
    print("🚀 Starting Streamlit application...")
    
    # Start application
    try:
        process = start_streamlit_application()
        print("📱 Application available at: http://localhost:8501")
        print("Press Ctrl+C to stop")
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
```

### NEW: Native Requirements File (requirements_native.txt)

```
streamlit>=1.28.0
pyyaml>=6.0
requests>=2.31.0
click>=8.1.0
pathlib>=1.0.1
```

---

## 7. Integration Strategy

### Files to Copy Entirely (No Changes)
1. `src/git_update_manager.py` → Copy as-is
2. `src/scripts_updater.py` → Copy as-is  
3. `src/workflow_utils.py` → Copy as-is

### Files to Create (New)
1. `src/enhanced_debug_logger.py` → Create from extracted code above
2. `run_native.py` → Create from code above
3. `requirements_native.txt` → Create from content above

### Files to Modify (Selective Integration)
1. `src/core.py` → Replace debug logging imports with enhanced_debug_logger
2. `src/logic.py` → Replace debug logging imports with enhanced_debug_logger
3. `app.py` → Remove Docker dependencies, add native execution

### Files to Remove (Docker-Specific)
1. `src/smart_sync.py` → Remove entirely
2. `src/fatal_sync_checker.py` → Remove entirely
3. `docker-compose.yml` → Remove entirely
4. `Dockerfile` → Remove entirely
5. `entrypoint.sh` → Remove entirely

---

## 8. Implementation Order

1. **Switch to baseline branch**: `git checkout 3d5ac82`
2. **Create implementation branch**: `git checkout -b feature/mac-vnc-enhanced-implementation`
3. **Copy Docker-independent files**: git_update_manager.py, scripts_updater.py, workflow_utils.py
4. **Create enhanced debug logger**: From extracted code above
5. **Create native launcher**: From code above
6. **Modify core files**: Update imports and remove Docker dependencies
7. **Test integration**: Ensure all enhanced features work in native environment

This document preserves all the code needed for the Mac + VNC integration and will survive the branch switch.