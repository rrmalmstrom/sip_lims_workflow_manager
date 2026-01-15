"""
Smart Sync Debug Logger

This module provides comprehensive debugging and logging capabilities for the Smart Sync
implementation. It helps diagnose issues, track performance, and validate functionality
across different platforms and scenarios.

Key Features:
- Structured logging with multiple levels (DEBUG, INFO, WARNING, ERROR)
- Performance monitoring and timing
- File operation tracking
- Error scenario analysis
- Windows-specific debugging support
- Test validation helpers
"""

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
    """Log levels for Smart Sync debugging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SmartSyncDebugLogger:
    """
    Comprehensive debug logger for Smart Sync operations.
    
    Provides structured logging, performance monitoring, and debugging
    capabilities specifically designed for Smart Sync functionality.
    """
    
    def __init__(self, log_file: Optional[Path] = None, console_output: bool = True, 
                 log_level: LogLevel = LogLevel.INFO):
        """
        Initialize the Smart Sync debug logger.
        
        Args:
            log_file: Path to log file (default: project/.smart_sync_debug.log)
            console_output: Whether to output to console
            log_level: Minimum log level to record
        """
        self.log_level = log_level
        self.console_output = console_output
        self.session_id = self._generate_session_id()
        self.start_time = time.time()
        
        # Set up log file
        if log_file is None:
            # Default to debug output directory
            debug_dir = Path.cwd() / ".debug_output"
            debug_dir.mkdir(exist_ok=True)
            self.log_file = debug_dir / "smart_sync_debug.log"
        else:
            self.log_file = Path(log_file)
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.operation_timers = {}
        self.performance_stats = {
            "sync_operations": [],
            "file_operations": [],
            "detection_calls": [],
            "errors": []
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize log file with session header
        self._write_session_header()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for this debug session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"smart_sync_{timestamp}_{os.getpid()}"
    
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
            self.performance_stats["sync_operations"].append(perf_data)
    
    def log_smart_sync_detection(self, project_path: Path, detected: bool, 
                                platform_name: str, **details):
        """Log Smart Sync detection attempt."""
        detection_data = {
            "project_path": str(project_path),
            "detected": detected,
            "platform": platform_name,
            "timestamp": time.time(),
            **details
        }
        
        self.performance_stats["detection_calls"].append(detection_data)
        
        if detected:
            self.info(f"Smart Sync detected for path: {project_path}", **detection_data)
        else:
            self.debug(f"Smart Sync not needed for path: {project_path}", **detection_data)
    
    def log_file_operation(self, operation: str, source: Path, dest: Path, 
                          success: bool, **details):
        """Log file operation (copy, delete, etc.)."""
        file_op_data = {
            "operation": operation,
            "source": str(source),
            "destination": str(dest),
            "success": success,
            "timestamp": time.time(),
            **details
        }
        
        self.performance_stats["file_operations"].append(file_op_data)
        
        if success:
            self.debug(f"File operation successful: {operation}", **file_op_data)
        else:
            self.warning(f"File operation failed: {operation}", **file_op_data)
    
    def log_sync_operation(self, sync_type: str, direction: str, files_affected: int,
                          duration: float, success: bool, **details):
        """Log sync operation summary."""
        sync_data = {
            "sync_type": sync_type,
            "direction": direction,
            "files_affected": files_affected,
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
            **details
        }
        
        if success:
            self.info(f"Sync completed: {sync_type} ({direction})", **sync_data)
        else:
            self.error(f"Sync failed: {sync_type} ({direction})", **sync_data)
    
    def log_environment_setup(self, network_path: Path, local_path: Path, 
                             env_vars: Dict[str, str], success: bool):
        """Log Smart Sync environment setup."""
        setup_data = {
            "network_path": str(network_path),
            "local_path": str(local_path),
            "environment_variables": env_vars,
            "success": success,
            "timestamp": time.time()
        }
        
        if success:
            self.info("Smart Sync environment setup completed", **setup_data)
        else:
            self.error("Smart Sync environment setup failed", **setup_data)
    
    def log_workflow_integration(self, step_id: str, sync_type: str, 
                                success: bool, **details):
        """Log workflow step integration with Smart Sync."""
        integration_data = {
            "step_id": step_id,
            "sync_type": sync_type,
            "success": success,
            "timestamp": time.time(),
            **details
        }
        
        if success:
            self.debug(f"Workflow sync successful: {step_id} ({sync_type})", **integration_data)
        else:
            self.warning(f"Workflow sync failed: {step_id} ({sync_type})", **integration_data)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for analysis."""
        current_time = time.time()
        session_duration = current_time - self.start_time
        
        summary = {
            "session_id": self.session_id,
            "session_duration": session_duration,
            "total_sync_operations": len(self.performance_stats["sync_operations"]),
            "total_file_operations": len(self.performance_stats["file_operations"]),
            "total_detection_calls": len(self.performance_stats["detection_calls"]),
            "total_errors": len(self.performance_stats["errors"]),
            "average_sync_duration": 0,
            "sync_success_rate": 0,
            "file_operation_success_rate": 0
        }
        
        # Calculate averages
        if self.performance_stats["sync_operations"]:
            total_duration = sum(op["duration"] for op in self.performance_stats["sync_operations"])
            summary["average_sync_duration"] = total_duration / len(self.performance_stats["sync_operations"])
        
        # Calculate success rates
        if self.performance_stats["file_operations"]:
            successful_files = sum(1 for op in self.performance_stats["file_operations"] if op.get("success", False))
            summary["file_operation_success_rate"] = successful_files / len(self.performance_stats["file_operations"])
        
        return summary
    
    def export_debug_data(self, output_file: Optional[Path] = None) -> Path:
        """Export all debug data for analysis."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_dir = Path.cwd() / ".debug_output"
            debug_dir.mkdir(exist_ok=True)
            output_file = debug_dir / f"smart_sync_debug_export_{timestamp}.json"
        
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
                click.secho("Smart Sync Debug Session Summary", fg='blue', bold=True)
                click.echo("="*50)
                click.echo(f"Session Duration: {summary['session_duration']:.2f}s")
                click.echo(f"Sync Operations: {summary['total_sync_operations']}")
                click.echo(f"File Operations: {summary['total_file_operations']}")
                click.echo(f"Detection Calls: {summary['total_detection_calls']}")
                click.echo(f"Errors: {summary['total_errors']}")
                if summary['average_sync_duration'] > 0:
                    click.echo(f"Average Sync Duration: {summary['average_sync_duration']:.3f}s")
                click.echo(f"Log File: {self.log_file}")
                click.echo("="*50)
            else:
                print(f"\nSmart Sync Debug Summary:")
                print(f"Session Duration: {summary['session_duration']:.2f}s")
                print(f"Log File: {self.log_file}")


# Global logger instance
_global_logger: Optional[SmartSyncDebugLogger] = None


def get_debug_logger(log_file: Optional[Path] = None, 
                    console_output: bool = True,
                    log_level: LogLevel = LogLevel.INFO) -> SmartSyncDebugLogger:
    """
    Get or create the global Smart Sync debug logger.
    
    Args:
        log_file: Path to log file (only used on first call)
        console_output: Whether to output to console (only used on first call)
        log_level: Minimum log level (only used on first call)
    
    Returns:
        SmartSyncDebugLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = SmartSyncDebugLogger(log_file, console_output, log_level)
    
    return _global_logger


def close_debug_logger():
    """Close the global debug logger."""
    global _global_logger
    
    if _global_logger is not None:
        _global_logger.close()
        _global_logger = None


def debug_enabled() -> bool:
    """Check if debug logging is enabled via environment variable."""
    return os.getenv("SMART_SYNC_DEBUG", "").lower() in ("true", "1", "yes", "on")


def get_debug_level() -> LogLevel:
    """Get debug level from environment variable."""
    level_str = os.getenv("SMART_SYNC_DEBUG_LEVEL", "INFO").upper()
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
def log_smart_sync_detection(project_path: Path, detected: bool, **details):
    """Log Smart Sync detection (convenience function)."""
    if debug_enabled():
        logger = get_debug_logger()
        logger.log_smart_sync_detection(project_path, detected, platform.system(), **details)


def log_sync_operation(sync_type: str, direction: str, files_affected: int,
                      duration: float, success: bool, **details):
    """Log sync operation (convenience function)."""
    if debug_enabled():
        logger = get_debug_logger()
        logger.log_sync_operation(sync_type, direction, files_affected, duration, success, **details)


def log_file_operation(operation: str, source: Path, dest: Path, success: bool, **details):
    """Log file operation (convenience function)."""
    if debug_enabled():
        logger = get_debug_logger()
        logger.log_file_operation(operation, source, dest, success, **details)


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


# Test validation helpers
class DebugTestValidator:
    """Helper class for validating debug output in tests."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.entries = []
        self._load_entries()
    
    def _load_entries(self):
        """Load log entries from file."""
        if not self.log_file.exists():
            return
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    self.entries.append(entry)
                except json.JSONDecodeError:
                    continue
    
    def get_entries_by_level(self, level: str) -> List[Dict]:
        """Get all log entries of a specific level."""
        return [entry for entry in self.entries if entry.get("level") == level]
    
    def get_entries_by_message_pattern(self, pattern: str) -> List[Dict]:
        """Get entries containing a message pattern."""
        return [entry for entry in self.entries if pattern in entry.get("message", "")]
    
    def get_operation_entries(self, operation_name: str) -> List[Dict]:
        """Get entries related to a specific operation."""
        return [entry for entry in self.entries 
                if entry.get("details", {}).get("operation") == operation_name]
    
    def assert_no_errors(self):
        """Assert that no error-level entries exist."""
        errors = self.get_entries_by_level("ERROR")
        if errors:
            raise AssertionError(f"Found {len(errors)} error entries: {errors}")
    
    def assert_operation_completed(self, operation_name: str):
        """Assert that an operation completed successfully."""
        entries = self.get_operation_entries(operation_name)
        completed = [e for e in entries if "completed" in e.get("message", "")]
        if not completed:
            raise AssertionError(f"Operation {operation_name} did not complete successfully")
    
    def get_performance_data(self) -> Dict[str, List]:
        """Extract performance data from log entries."""
        perf_data = {
            "sync_operations": [],
            "file_operations": [],
            "detection_calls": []
        }
        
        for entry in self.entries:
            details = entry.get("details", {})
            if "duration" in details:
                if "sync" in entry.get("message", "").lower():
                    perf_data["sync_operations"].append(details)
                elif "file" in entry.get("message", "").lower():
                    perf_data["file_operations"].append(details)
                elif "detection" in entry.get("message", "").lower():
                    perf_data["detection_calls"].append(details)
        
        return perf_data