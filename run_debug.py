#!/usr/bin/env python3
"""
DEBUG VERSION - SIP LIMS Workflow Manager Docker Launcher
This version includes comprehensive logging to debug Windows UNC path issues.
All debug output goes to 'debug_log.txt' file.
"""

import os
import sys
import platform
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import tempfile
import argparse
import datetime
import traceback

# Set up debug logging
DEBUG_LOG_FILE = "debug_log.txt"

def debug_log(message: str):
    """Write debug message to log file with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

# Initialize debug log
debug_log("=" * 80)
debug_log("DEBUG SESSION STARTED")
debug_log(f"Platform: {platform.system()} {platform.release()}")
debug_log(f"Python: {sys.version}")
debug_log(f"Working Directory: {os.getcwd()}")
debug_log("=" * 80)

# Try to import Click, fall back to standard library if not available
try:
    import click
    HAS_CLICK = True
    debug_log("Click library imported successfully")
except ImportError:
    HAS_CLICK = False
    debug_log("Click library not available, using fallback")
    # Create a minimal click-like interface using standard library
    class click:
        @staticmethod
        def echo(message="", **kwargs):
            debug_log(f"ECHO: {message}")
            print(message)
        
        @staticmethod
        def secho(message, fg=None, bold=False, **kwargs):
            debug_log(f"SECHO: {message} (fg={fg}, bold={bold})")
            if fg == 'red':
                print(f"\033[91m{message}\033[0m" if bold else f"\033[31m{message}\033[0m")
            elif fg == 'green':
                print(f"\033[92m{message}\033[0m" if bold else f"\033[32m{message}\033[0m")
            elif fg == 'blue':
                print(f"\033[94m{message}\033[0m" if bold else f"\033[34m{message}\033[0m")
            elif fg == 'yellow':
                print(f"\033[93m{message}\033[0m" if bold else f"\033[33m{message}\033[0m")
            else:
                print(f"\033[1m{message}\033[0m" if bold else message)
        
        @staticmethod
        def prompt(text, type=str, **kwargs):
            debug_log(f"PROMPT: {text} (type={type})")
            while True:
                try:
                    response = input(f"{text}: ").strip()
                    debug_log(f"PROMPT_RESPONSE: {repr(response)}")
                    if type == str:
                        return response
                    else:
                        return type(response)
                except (ValueError, KeyboardInterrupt):
                    if type != str:
                        print("Invalid input, please try again.")
                        continue
                    raise
        
        @staticmethod
        def confirm(text, default=False, **kwargs):
            debug_log(f"CONFIRM: {text} (default={default})")
            suffix = " [Y/n]" if default else " [y/N]"
            while True:
                response = input(f"{text}{suffix}: ").strip().lower()
                debug_log(f"CONFIRM_RESPONSE: {repr(response)}")
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                elif response == '':
                    return default
                else:
                    print("Please enter 'y' or 'n'.")
        
        @staticmethod
        def command():
            def decorator(func):
                return func
            return decorator
        
        @staticmethod
        def option(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        @staticmethod
        def version_option(**kwargs):
            def decorator(func):
                return func
            return decorator
        
        class Choice:
            def __init__(self, choices):
                self.choices = choices
        
        class Path:
            def __init__(self, exists=False, file_okay=True, path_type=None):
                self.exists = exists
                self.file_okay = file_okay
                self.path_type = path_type or str

# Import existing infrastructure
try:
    debug_log("Attempting to import required modules...")
    from utils.branch_utils import (
        get_current_branch, get_docker_tag_for_current_branch,
        get_local_image_name_for_current_branch, get_remote_image_name_for_current_branch,
        get_branch_info, GitRepositoryError, BranchDetectionError
    )
    from src.update_detector import UpdateDetector
    from src.scripts_updater import ScriptsUpdater
    from src.fatal_sync_checker import check_fatal_sync_errors
    from src.debug_logger import (
        debug_context, log_smart_sync_detection, log_info, log_error,
        log_warning, debug_enabled, get_debug_logger
    )
    debug_log("All required modules imported successfully")
except ImportError as e:
    debug_log(f"IMPORT ERROR: {e}")
    debug_log(f"Traceback: {traceback.format_exc()}")
    click.secho(f"❌ ERROR: Failed to import required modules: {e}", fg='red', bold=True)
    click.echo("Make sure you're running from the project root directory.")
    sys.exit(1)


class PlatformAdapter:
    """Platform-specific adaptations for cross-platform compatibility."""
    
    @staticmethod
    def get_platform() -> str:
        """Get normalized platform name."""
        system = platform.system().lower()
        debug_log(f"Raw platform system: {platform.system()}")
        if system == "darwin":
            result = "macos"
        else:
            result = system
        debug_log(f"Normalized platform: {result}")
        return result
    
    @staticmethod
    def get_user_ids() -> Dict[str, str]:
        """Get user/group IDs for Docker volume mapping."""
        debug_log("Getting user IDs for Docker volume mapping...")
        if platform.system() == "Windows":
            # Windows Docker Desktop standard mapping
            result = {
                "USER_ID": os.environ.get("DOCKER_USER_ID", "1000"),
                "GROUP_ID": os.environ.get("DOCKER_GROUP_ID", "1000")
            }
            debug_log(f"Windows user IDs: {result}")
            return result
        else:
            # Unix-like systems
            result = {
                "USER_ID": str(os.getuid()),
                "GROUP_ID": str(os.getgid())
            }
            debug_log(f"Unix user IDs: {result}")
            return result
    
    @staticmethod
    def validate_docker() -> bool:
        """Check if Docker is available and running."""
        debug_log("Validating Docker availability...")
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            is_running = result.returncode == 0
            debug_log(f"Docker validation result: returncode={result.returncode}, running={is_running}")
            if not is_running:
                debug_log(f"Docker stderr: {result.stderr}")
            return is_running
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            debug_log(f"Docker validation exception: {e}")
            return False
    
    @staticmethod
    def normalize_path(path_str: str) -> Path:
        """Normalize path input across platforms with intelligent Windows UNC handling."""
        debug_log(f"NORMALIZE_PATH called with: {repr(path_str)}")
        
        # Remove quotes and whitespace
        cleaned = path_str.strip().strip('"').strip("'")
        debug_log(f"After cleaning: {repr(cleaned)}")
        
        # Platform-specific path handling
        current_platform = platform.system()
        debug_log(f"Current platform: {current_platform}")
        
        if current_platform == "Windows":
            debug_log("Using Windows path normalization")
            result = PlatformAdapter._normalize_windows_path(cleaned)
            debug_log(f"Windows normalization result: {result}")
            return result
        elif current_platform == "Darwin":  # macOS
            debug_log("Using macOS path normalization")
            # Remove escape characters from drag-and-drop
            cleaned = cleaned.replace('\\ ', ' ')
            debug_log(f"After escape character removal: {repr(cleaned)}")
            result = Path(cleaned).resolve()
            debug_log(f"macOS normalization result: {result}")
            return result
        else:  # Linux and other Unix-like systems
            debug_log("Using Unix path normalization")
            result = Path(cleaned).resolve()
            debug_log(f"Unix normalization result: {result}")
            return result
    
    @staticmethod
    def _normalize_windows_path(cleaned: str) -> Path:
        """Windows-specific path normalization with bidirectional UNC/drive letter detection."""
        debug_log(f"WINDOWS_NORMALIZE called with: {repr(cleaned)}")
        
        # Handle UNC paths by attempting to find existing mapped drives
        if cleaned.startswith(('\\\\', '//')):
            debug_log("UNC path detected")
            # UNC path detected - try to convert to mapped drive path
            unc_path = cleaned.replace('/', '\\')
            debug_log(f"Normalized UNC path: {repr(unc_path)}")
            
            mapped_drive_path = PlatformAdapter._convert_unc_to_mapped_drive(unc_path)
            debug_log(f"Mapped drive conversion result: {mapped_drive_path}")
            
            if mapped_drive_path:
                click.echo(f"🔄 Converted UNC path to mapped drive: {mapped_drive_path}")
                debug_log(f"Successfully converted UNC to mapped drive: {mapped_drive_path}")
                
                # CRITICAL FIX: Create Path object from the converted string, not the original UNC
                # This ensures the Path object contains the drive letter path, not the UNC path
                try:
                    converted_path = Path(mapped_drive_path)
                    debug_log(f"Path object created from converted string: {converted_path}")
                    debug_log(f"Path object str() representation: {str(converted_path)}")
                    
                    # Validate the converted path exists and is accessible
                    if converted_path.exists():
                        # CRITICAL FIX: Do NOT call .resolve() on converted mapped drive paths!
                        # .resolve() will convert the drive letter back to UNC path
                        debug_log(f"Path exists, returning unresolved converted path: {converted_path}")
                        debug_log(f"Converted path str() representation: {str(converted_path)}")
                        return converted_path
                    else:
                        # Mapped drive exists but path doesn't - return as-is for Docker to handle
                        debug_log(f"Path doesn't exist, returning unconverted: {converted_path}")
                        debug_log(f"Unconverted path str() representation: {str(converted_path)}")
                        return converted_path
                except (OSError, ValueError) as e:
                    # If Path creation fails, return the string as a Path anyway
                    debug_log(f"Path creation failed with error: {e}")
                    fallback_path = Path(mapped_drive_path)
                    debug_log(f"Fallback path: {fallback_path}")
                    debug_log(f"Fallback path str() representation: {str(fallback_path)}")
                    return fallback_path
            else:
                debug_log("No existing mapping found for UNC path")
                # No existing mapping found - provide helpful error
                click.echo()
                click.secho("❌ ERROR: UNC Network Path Not Supported by Docker Desktop", fg='red', bold=True)
                click.echo(f"   Path: {unc_path}")
                click.echo()
                click.echo("Docker Desktop on Windows requires network drives to be mapped to drive letters.")
                click.echo("Please map this network location to a drive letter first:")
                click.echo()
                click.secho("📋 Steps to fix:", fg='blue', bold=True)
                click.echo("1. Open Command Prompt as Administrator")
                click.echo("2. Run this command:")
                
                # Extract server and share for cleaner command
                try:
                    parts = unc_path.split('\\')
                    debug_log(f"UNC path parts: {parts}")
                    if len(parts) >= 4:
                        server = parts[2]
                        share = parts[3]
                        base_unc = f"\\\\{server}\\{share}"
                        click.echo(f"   net use Z: \"{base_unc}\" /persistent:yes")
                        debug_log(f"Suggested mapping command for {base_unc}")
                    else:
                        click.echo(f"   net use Z: \"{unc_path}\" /persistent:yes")
                        debug_log(f"Suggested mapping command for full path {unc_path}")
                except Exception as e:
                    debug_log(f"Error parsing UNC path: {e}")
                    click.echo(f"   net use Z: \"{unc_path}\" /persistent:yes")
                
                click.echo("3. Use Z:\\ instead of the UNC path in this application")
                click.echo()
                click.echo("The mapping will persist across reboots. You can use any available drive letter.")
                click.echo()
                error_msg = f"UNC network path requires drive mapping: {unc_path}"
                debug_log(f"Raising ValueError: {error_msg}")
                raise ValueError(error_msg)
        
        debug_log("Regular Windows path (not UNC)")
        # Handle regular Windows paths (including already mapped drives)
        try:
            path_obj = Path(cleaned)
            debug_log(f"Created Path object from: {cleaned}")
            debug_log(f"Path object before resolve: {path_obj}")
            
            # CRITICAL FIX: Do NOT call .resolve() on mapped drive paths on Windows!
            # .resolve() converts drive letters back to UNC paths on Windows
            # Check if this is a Windows mapped drive (starts with drive letter like C:, Z:, etc.)
            import re
            is_drive_letter_path = re.match(r'^[A-Za-z]:', cleaned)
            debug_log(f"Drive letter path check: {is_drive_letter_path is not None}")
            
            if is_drive_letter_path:
                debug_log("Detected Windows mapped drive path - skipping .resolve() to prevent UNC conversion")
                debug_log(f"Returning unresolved mapped drive path: {path_obj}")
                return path_obj
            else:
                result = path_obj.resolve()
                debug_log(f"Successfully resolved regular Windows path: {result}")
                return result
        except (OSError, ValueError) as e:
            debug_log(f"Error processing regular Windows path: {e}")
            # Fallback for edge cases
            cleaned = cleaned.replace('/', '\\')
            debug_log(f"Fallback path after slash conversion: {repr(cleaned)}")
            result = Path(cleaned)
            debug_log(f"Fallback path result: {result}")
            return result
    
    @staticmethod
    def _convert_unc_to_mapped_drive(unc_path: str) -> Optional[str]:
        """Convert UNC path to mapped drive path if mapping exists."""
        debug_log(f"CONVERT_UNC_TO_MAPPED called with: {repr(unc_path)}")
        
        try:
            # Run 'net use' to get current drive mappings
            debug_log("Running 'net use' command...")
            result = subprocess.run(['net', 'use'], capture_output=True, text=True, check=True)
            debug_log(f"'net use' command successful, returncode: {result.returncode}")
            debug_log(f"'net use' stdout length: {len(result.stdout)} characters")
            debug_log(f"'net use' stdout:\n{result.stdout}")
            
            # Parse the output to find mappings
            debug_log("Parsing 'net use' output...")
            for i, line in enumerate(result.stdout.split('\n')):
                debug_log(f"Line {i}: {repr(line)}")
                if 'OK' in line and ':' in line:
                    debug_log(f"Found potential mapping line: {repr(line)}")
                    parts = line.split()
                    debug_log(f"Line parts: {parts}")
                    if len(parts) >= 3:
                        drive_letter = parts[1]  # e.g., "Z:"
                        mapped_unc = parts[2]    # e.g., "\\server\share"
                        debug_log(f"Found mapping: {drive_letter} -> {mapped_unc}")
                        
                        # Check if the UNC path starts with this mapped path
                        unc_lower = unc_path.lower()
                        mapped_lower = mapped_unc.lower()
                        debug_log(f"Comparing: {repr(unc_lower)} starts with {repr(mapped_lower)}")
                        
                        if unc_lower.startswith(mapped_lower):
                            debug_log("UNC path matches this mapping!")
                            # Convert the UNC path to use the mapped drive
                            relative_path = unc_path[len(mapped_unc):].lstrip('\\')
                            debug_log(f"Relative path after mapping: {repr(relative_path)}")
                            
                            if relative_path:
                                converted = f"{drive_letter}\\{relative_path}"
                                debug_log(f"Converted path: {converted}")
                                return converted
                            else:
                                debug_log(f"No relative path, returning drive letter: {drive_letter}")
                                return drive_letter
            
            debug_log("No matching mapping found")
            return None
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            debug_log(f"'net use' command failed: {e}")
            # 'net use' command failed or not available
            return None
    
    @staticmethod
    def get_docker_compose_command() -> List[str]:
        """Get the appropriate docker-compose command for the platform."""
        debug_log("Getting docker-compose command...")
        # Try docker compose (newer) first, then docker-compose (legacy)
        for cmd in [["docker", "compose"], ["docker-compose"]]:
            debug_log(f"Trying command: {cmd}")
            try:
                result = subprocess.run(cmd + ["--version"], capture_output=True, check=True, timeout=5)
                debug_log(f"Command {cmd} successful, returncode: {result.returncode}")
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                debug_log(f"Command {cmd} failed: {e}")
                continue
        
        error_msg = "Neither 'docker compose' nor 'docker-compose' found"
        debug_log(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)
    
    @staticmethod
    def detect_smart_sync_scenario(project_path: Path) -> bool:
        """Detect if Smart Sync is needed for Windows network drives."""
        debug_log(f"DETECT_SMART_SYNC called with: {project_path}")
        platform_name = platform.system()
        debug_log(f"Platform: {platform_name}")
        
        if platform_name != "Windows":
            debug_log("Non-Windows platform - Smart Sync not needed")
            log_smart_sync_detection(project_path, False,
                                   platform=platform_name,
                                   reason="Non-Windows platform (run_debug.py)")
            return False
        
        try:
            # CRITICAL FIX: Use original path string, NOT .resolve()
            # .resolve() converts drive letters back to UNC paths on Windows
            path_str = str(project_path)
            detected = False
            detection_reason = ""
            
            # Check if path is on a network drive (D: through Z:, excluding C:)
            if len(path_str) >= 2 and path_str[1] == ':':
                drive_letter = path_str[0].upper()
                # Network drives are typically D: through Z: (excluding C: which is usually local)
                if drive_letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
                    detected = True
                    detection_reason = f"Network drive detected in run_debug.py: {drive_letter}:"
                else:
                    detection_reason = f"Local drive detected in run_debug.py: {drive_letter}:"
            
            # Check for UNC paths (should have been converted to mapped drives by PlatformAdapter)
            elif path_str.startswith(('\\\\', '//')):
                detected = True
                detection_reason = "UNC path detected in run_debug.py"
            else:
                detection_reason = "No network drive pattern detected in run_debug.py"
            
            debug_log(f"Smart Sync detection result: {detected} - {detection_reason}")
            log_smart_sync_detection(project_path, detected,
                                   platform=platform_name,
                                   reason=detection_reason, path_str=path_str,
                                   source="run_debug.py PlatformAdapter")
            
            return detected
            
        except Exception as e:
            debug_log(f"Exception during Smart Sync detection: {e}")
            # If we can't determine the path type, assume no Smart Sync needed
            log_smart_sync_detection(project_path, False,
                                   platform=platform_name,
                                   reason="Exception during detection in run_debug.py",
                                   error=str(e), source="run_debug.py PlatformAdapter")
            return False
    
    @staticmethod
    def cleanup_orphaned_staging_directories(project_path: Path):
        """Clean up any orphaned staging directories for this project."""
        debug_log(f"CLEANUP_ORPHANED called with: {project_path}")
        try:
            staging_base = Path("C:/temp/sip_workflow")
            if not staging_base.exists():
                debug_log("Staging base directory doesn't exist - nothing to clean")
                return
            
            project_name = project_path.name
            project_staging = staging_base / project_name
            debug_log(f"Checking for orphaned staging: {project_staging}")
            
            if project_staging.exists():
                click.echo(f"🧹 Cleaning up orphaned staging directory: {project_staging}")
                debug_log(f"Found orphaned staging directory: {project_staging}")
                
                import shutil
                shutil.rmtree(project_staging, ignore_errors=True)
                
                if not project_staging.exists():
                    click.secho("✅ Orphaned staging directory cleaned up", fg='green')
                    debug_log("Orphaned staging directory cleanup completed")
                else:
                    click.secho("⚠️ Could not fully clean staging directory", fg='yellow')
                    debug_log("Orphaned staging directory cleanup incomplete")
            else:
                debug_log("No orphaned staging directory found")
                    
        except Exception as e:
            debug_log(f"Error during orphaned staging cleanup: {e}")
    
    @staticmethod
    def setup_smart_sync_environment(network_path: Path) -> Dict[str, str]:
        """Set up Smart Sync environment and perform initial sync."""
        debug_log(f"SETUP_SMART_SYNC called with: {network_path}")
        
        with debug_context("run_debug_py_setup_smart_sync_environment",
                          network_path=str(network_path)) as debug_logger:
            
            try:
                if debug_logger:
                    debug_logger.info("Setting up Smart Sync environment from run_debug.py",
                                    network_path=str(network_path))
                
                debug_log("Setting up Smart Sync environment from run_debug.py")
                log_info("run_debug.py: Setting up Smart Sync environment",
                        network_path=str(network_path))
                
                from src.smart_sync import setup_smart_sync_environment
                env_vars = setup_smart_sync_environment(network_path)
                
                if debug_logger:
                    debug_logger.info("Smart Sync environment setup completed from run_debug.py",
                                    environment_variables=env_vars)
                
                debug_log(f"Smart Sync environment setup completed: {env_vars}")
                log_info("run_debug.py: Smart Sync environment setup completed",
                        environment_variables=env_vars)
                
                return env_vars
                
            except Exception as e:
                debug_log(f"Smart Sync environment setup failed: {e}")
                click.secho(f"❌ Failed to setup Smart Sync environment: {e}", fg='red')
                
                log_error("run_debug.py: Smart Sync environment setup failed",
                         error=str(e), network_path=str(network_path))
                
                click.echo()
                click.secho("CRITICAL ERROR: Smart Sync is required for Windows network drives", fg='red', bold=True)
                click.echo("Docker Desktop cannot access network drives directly on Windows.")
                click.echo("Please resolve the Smart Sync setup issue and try again.")
                click.echo()
                
                # FAIL-FAST: No fallback behavior, terminate completely
                raise RuntimeError(f"Smart Sync setup failed: {e}")


class UserInterface:
    """Rich CLI interface using Click for cross-platform user interaction."""
    
    @staticmethod
    def select_workflow_type() -> str:
        """Interactive workflow type selection."""
        debug_log("Selecting workflow type...")
        click.echo()
        click.secho("🧪 Select workflow type:", fg='blue', bold=True)
        click.echo("1) SIP (Stable Isotope Probing)")
        click.echo("2) SPS-CE (Single Particle Sorting - Cell Enrichment)")
        click.echo()
        
        while True:
            choice = click.prompt("Enter choice (1 or 2)", type=str).strip()
            debug_log(f"Workflow choice: {repr(choice)}")
            if choice == "1":
                click.secho("✅ Selected: SIP workflow", fg='green')
                debug_log("Selected SIP workflow")
                return "sip"
            elif choice == "2":
                click.secho("✅ Selected: SPS-CE workflow", fg='green')
                debug_log("Selected SPS-CE workflow")
                return "sps-ce"
            else:
                click.secho(f"❌ Invalid choice '{choice}'. Please enter 1 or 2.", fg='red')
                debug_log(f"Invalid workflow choice: {repr(choice)}")
    
    @staticmethod
    def select_project_path() -> Path:
        """Interactive project folder selection with validation."""
        debug_log("Selecting project path...")
        click.echo()
        click.secho("📁 Project Folder Selection", fg='blue', bold=True)
        click.echo("Please drag and drop your project folder here, then press Enter:")
        
        while True:
            try:
                path_input = click.prompt("Project path", type=str)
                debug_log(f"Raw project path input: {repr(path_input)}")
                
                project_path = PlatformAdapter.normalize_path(path_input)
                debug_log(f"Normalized project path: {project_path}")
                
                if not project_path.exists():
                    debug_log(f"Path does not exist: {project_path}")
                    click.secho(f"❌ Path does not exist: {project_path}", fg='red')
                    continue
                
                if not project_path.is_dir():
                    debug_log(f"Path is not a directory: {project_path}")
                    click.secho(f"❌ Path is not a directory: {project_path}", fg='red')
                    continue
                
                click.secho(f"✅ Selected project folder: {project_path.name}", fg='green')
                click.echo(f"📍 Full path: {project_path}")
                debug_log(f"Successfully selected project path: {project_path}")
                return project_path
                
            except KeyboardInterrupt:
                debug_log("Project path selection cancelled by user")
                raise
            except Exception as e:
                debug_log(f"Error processing project path: {e}")
                debug_log(f"Traceback: {traceback.format_exc()}")
                click.secho(f"❌ Error processing path: {e}", fg='red')
    
    @staticmethod
    def confirm_action(message: str, default: bool = False) -> bool:
        """Confirmation prompt with styling."""
        debug_log(f"Confirmation prompt: {message} (default={default})")
        return click.confirm(
            click.style(message, fg='yellow', bold=True),
            default=default
        )


class ContainerManager:
    """Docker container lifecycle management."""
    
    def __init__(self, branch_info: dict):
        debug_log(f"Initializing ContainerManager with branch_info: {branch_info}")
        self.branch_info = branch_info
        self.local_image_name = branch_info['local_image']
        self.remote_image_name = branch_info['remote_image']
        self.compose_cmd = PlatformAdapter.get_docker_compose_command()
        debug_log(f"Docker compose command: {self.compose_cmd}")
    
    def prepare_environment(self, project_path: Path, workflow_type: str, mode_config: dict) -> Dict[str, str]:
        """Prepare environment variables for Docker container."""
        debug_log("Preparing environment variables...")
        debug_log(f"Project path: {project_path}")
        debug_log(f"Workflow type: {workflow_type}")
        debug_log(f"Mode config: {mode_config}")
        
        user_ids = PlatformAdapter.get_user_ids()
        debug_log(f"User IDs: {user_ids}")
        
        env = {
            "PROJECT_PATH": str(project_path),
            "PROJECT_NAME": project_path.name,
            "SCRIPTS_PATH": mode_config["scripts_path"],
            "WORKFLOW_TYPE": workflow_type,
            "APP_ENV": mode_config["app_env"],
            "DOCKER_IMAGE": mode_config["docker_image"],
            "SYNC_SCRIPTS_PATH": str(Path.cwd() / "sync_scripts"),
            **user_ids
        }
        
        debug_log("Final environment variables:")
        for key, value in env.items():
            debug_log(f"  {key}: {repr(value)}")
        
        return env
    
    def display_environment_summary(self, env: Dict[str, str]):
        """Display environment configuration summary."""
        debug_log("Displaying environment summary...")
        click.echo("--- Environment Variables ---")
        for key, value in env.items():
            if key in ["USER_ID", "GROUP_ID", "PROJECT_PATH", "PROJECT_NAME", 
                      "SCRIPTS_PATH", "APP_ENV", "DOCKER_IMAGE", "WORKFLOW_TYPE"]:
                click.echo(f"{key}: {value}")
                debug_log(f"Displayed: {key}: {value}")
    
    def cleanup_existing_containers(self):
        """Stop and remove existing workflow manager containers."""
        debug_log("Checking for running workflow manager containers...")
        click.echo("🛑 Checking for running workflow manager containers...")
        
        try:
            # Find containers using workflow manager images
            result = subprocess.run([
                "docker", "ps", "-a",
                "--filter", f"ancestor={self.remote_image_name}",
                "--filter", f"ancestor={self.local_image_name}",
                "--format", "{{.ID}} {{.Names}} {{.Status}}"
            ], capture_output=True, text=True, check=True)
            
            debug_log(f"Container search result: {result.stdout}")
            
            if result.stdout.strip():
                click.echo("📋 Found workflow manager containers:")
                container_ids = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        container_id, name = parts[0], parts[1]
                        status = ' '.join(parts[2:])
                        click.echo(f"    - {name} ({container_id}): {status}")
                        debug_log(f"Found container: {name} ({container_id}): {status}")
                        container_ids.append(container_id)
                
                if container_ids:
                    click.echo("🛑 Stopping workflow manager containers...")
                    debug_log(f"Stopping containers: {container_ids}")
                    subprocess.run(["docker", "stop"] + container_ids,
                                 capture_output=True, check=False)
                    
                    click.echo("🗑️  Removing workflow manager containers...")
                    debug_log(f"Removing containers: {container_ids}")
                    subprocess.run(["docker", "rm"] + container_ids,
                                 capture_output=True, check=False)
                    
                    click.secho("✅ Workflow manager containers cleaned up", fg='green')
                    debug_log("Container cleanup completed")
            else:
                click.secho("✅ No running workflow manager containers found", fg='green')
                debug_log("No running containers found")
                
        except subprocess.CalledProcessError as e:
            debug_log(f"Container cleanup error: {e}")
            click.secho(f"⚠️  Warning: Could not check containers: {e}", fg='yellow')

    def launch_container(self, project_path: Path, workflow_type: str, mode_config: dict):
        """Launch the Docker container using docker-compose with Smart Sync support."""
        with debug_context("container_launch_debug",
                          project_path=str(project_path),
                          workflow_type=workflow_type) as debug_logger:
            
            debug_log("Launching Docker container...")
            click.echo()
            click.secho("🐳 Launching Docker container...", fg='blue', bold=True)
            
            if debug_logger:
                debug_logger.info("Starting container launch from run_debug.py",
                                project_path=str(project_path),
                                workflow_type=workflow_type,
                                mode_config=mode_config)
            
            # Check if Smart Sync is needed
            docker_project_path = project_path
            sync_env = {}
            smart_sync_detected = PlatformAdapter.detect_smart_sync_scenario(project_path)
            debug_log(f"Smart Sync detection result: {smart_sync_detected}")
            
            if debug_logger:
                debug_logger.info(f"Smart Sync detection result: {smart_sync_detected}")
            
            if smart_sync_detected:
                try:
                    debug_log("Setting up Smart Sync environment")
                    
                    if debug_logger:
                        debug_logger.info("Setting up Smart Sync environment")
                    
                    # Cleanup any orphaned staging directories before setup
                    PlatformAdapter.cleanup_orphaned_staging_directories(project_path)
                    
                    sync_env = PlatformAdapter.setup_smart_sync_environment(project_path)
                    docker_project_path = Path(sync_env["PROJECT_PATH"])
                    click.secho("✅ Smart Sync enabled for Windows network drive", fg='green')
                    debug_log(f"Smart Sync enabled - docker path: {docker_project_path}")
                    
                    log_info("Container launch: Smart Sync enabled",
                            original_path=str(project_path),
                            docker_path=str(docker_project_path),
                            sync_environment=sync_env)
                    
                except Exception as e:
                    debug_log(f"Smart Sync setup failed: {e}")
                    click.secho(f"❌ Smart Sync setup failed: {e}", fg='red')
                    click.echo()
                    click.secho("CRITICAL ERROR: Smart Sync is required for Windows network drives", fg='red', bold=True)
                    click.echo("Docker Desktop cannot access network drives directly on Windows.")
                    click.echo("Please resolve the Smart Sync setup issue and try again.")
                    click.echo()
                    
                    log_error("Container launch: Smart Sync setup failed - terminating",
                             error=str(e), project_path=str(project_path))
                    
                    # FAIL-FAST: No fallback behavior, terminate completely
                    raise RuntimeError(f"Smart Sync setup failed: {e}")
            else:
                sync_env = {"SMART_SYNC_ENABLED": "false"}
                debug_log("Smart Sync not needed")
                
                log_info("Container launch: Smart Sync not needed",
                        project_path=str(project_path))
            
            # Prepare environment variables
            env = self.prepare_environment(docker_project_path, workflow_type, mode_config)
            env.update(sync_env)
            
            if debug_logger:
                debug_logger.info("Environment prepared for container",
                                environment_variables=env)
            
            # Display environment summary
            self.display_environment_summary(env)
            
            # Launch container
            try:
                click.echo("--- Starting Container ---")
                debug_log("About to run docker-compose command...")
                debug_log(f"Command: {self.compose_cmd + ['up']}")
                debug_log(f"Working directory: {Path.cwd()}")
                debug_log("Environment variables being passed to docker-compose:")
                combined_env = {**os.environ, **env}
                for key, value in combined_env.items():
                    if key in env:  # Only log our custom env vars
                        debug_log(f"  {key}: {repr(value)}")
                
                if debug_logger:
                    debug_logger.info("Executing docker-compose up",
                                    compose_command=self.compose_cmd + ["up"])
                
                result = subprocess.run(
                    self.compose_cmd + ["up"],
                    cwd=Path.cwd(),
                    env=combined_env,
                    check=True
                )
                debug_log(f"Docker-compose completed with returncode: {result.returncode}")
                
                log_info("Container launch completed successfully")
                
            except subprocess.CalledProcessError as e:
                debug_log(f"Docker-compose failed with CalledProcessError: {e}")
                debug_log(f"Return code: {e.returncode}")
                debug_log(f"Command: {e.cmd}")
                if hasattr(e, 'stdout') and e.stdout:
                    debug_log(f"Stdout: {e.stdout}")
                if hasattr(e, 'stderr') and e.stderr:
                    debug_log(f"Stderr: {e.stderr}")
                error_msg = f"Docker container launch failed: {e}"
                debug_log(f"Raising RuntimeError: {error_msg}")
                
                log_error("Docker container launch failed",
                         error=str(e), compose_command=self.compose_cmd)
                raise RuntimeError(error_msg)
                
            except KeyboardInterrupt:
                debug_log("Container launch interrupted by user")
                click.echo("\n🛑 Container stopped by user")
                
                log_info("Container stopped by user interrupt")
                
                # Immediate cleanup of local staging directory
                if sync_env.get("SMART_SYNC_ENABLED") == "true":
                    click.echo("🧹 Cleaning up local staging directory...")
                    debug_log("Performing Smart Sync cleanup on container shutdown")
                    
                    if debug_logger:
                        debug_logger.info("Performing Smart Sync cleanup on container shutdown")
                    
                    try:
                        from src.smart_sync import SmartSyncManager
                        sync_manager = SmartSyncManager(
                            Path(sync_env["NETWORK_PROJECT_PATH"]),
                            Path(sync_env["LOCAL_PROJECT_PATH"])
                        )
                        sync_manager.cleanup()
                        click.secho("✅ Local staging cleanup completed", fg='green')
                        debug_log("Smart Sync cleanup completed on container shutdown")
                        
                        log_info("Smart Sync cleanup completed on container shutdown")
                        
                    except Exception as e:
                        click.secho(f"⚠️ Cleanup failed: {e}", fg='yellow')
                        debug_log(f"Smart Sync cleanup failed on container shutdown: {e}")
                        
                        log_error("Smart Sync cleanup failed on container shutdown",
                                 error=str(e))
            except Exception as e:
                debug_log(f"Unexpected error during container launch: {e}")
                debug_log(f"Traceback: {traceback.format_exc()}")
                raise
            finally:
                debug_log("Container launch finished")
                click.echo("Application has been shut down.")
                
                if debug_logger:
                    debug_logger.info("Container launch process completed")


class UpdateManager:
    """Integrate existing update detection and management for debug mode."""
    
    def __init__(self, branch_info: dict):
        debug_log("Initializing UpdateManager...")
        self.branch_info = branch_info
        self.update_detector = UpdateDetector()
        debug_log(f"UpdateManager initialized with branch: {branch_info['branch']}")
    
    def check_scripts_updates(self, workflow_type: str, scripts_path: str):
        """Check and handle scripts updates."""
        debug_log("Checking for workflow-specific script updates...")
        click.echo("🔍 Checking for workflow-specific script updates...")
        
        try:
            scripts_updater = ScriptsUpdater(workflow_type=workflow_type)
            result = scripts_updater.check_scripts_update(scripts_path)
            debug_log(f"Scripts update check result: {result}")
            
            if result.get("update_available", False):
                click.echo("📦 Script updates available - updating scripts...")
                debug_log("Script updates available - performing update...")
                update_result = scripts_updater.update_scripts(scripts_path)
                debug_log(f"Scripts update result: {update_result}")
                
                if update_result.get("success", False):
                    click.secho("✅ Scripts updated successfully", fg='green')
                    debug_log("Scripts updated successfully")
                else:
                    error_msg = update_result.get('error', 'Unknown error')
                    click.secho(f"❌ ERROR: Failed to update scripts: {error_msg}", fg='red')
                    debug_log(f"Scripts update failed: {error_msg}")
            else:
                click.secho("✅ Scripts are up to date", fg='green')
                debug_log("Scripts are up to date")
                
        except Exception as e:
            debug_log(f"Exception during scripts update check: {e}")
            debug_log(f"Traceback: {traceback.format_exc()}")
            click.secho(f"⚠️  Warning: Could not check for script updates: {e}", fg='yellow')


class DockerLauncher:
    """Unified Docker container launcher for all platforms."""
    
    def __init__(self):
        debug_log("Initializing DockerLauncher...")
        self.platform = PlatformAdapter.get_platform()
        self.project_root = Path.cwd()
        debug_log(f"Platform: {self.platform}")
        debug_log(f"Project root: {self.project_root}")
        
        # Initialize branch information
        try:
            debug_log("Getting branch info...")
            self.branch_info = get_branch_info()
            debug_log(f"Branch info: {self.branch_info}")
        except (GitRepositoryError, BranchDetectionError) as e:
            debug_log(f"Branch info error: {e}")
            click.secho(f"❌ ERROR: {e}", fg='red', bold=True)
            sys.exit(1)
        
        # Initialize managers
        debug_log("Initializing container manager...")
        self.container_manager = ContainerManager(self.branch_info)
        debug_log("Initializing update manager...")
        self.update_manager = UpdateManager(self.branch_info)
    
    def validate_environment(self):
        """Validate the execution environment."""
        debug_log("Validating environment...")
        # Check Docker availability
        if not PlatformAdapter.validate_docker():
            debug_log("Docker validation failed")
            click.secho("❌ ERROR: Docker is not running.", fg='red', bold=True)
            click.echo("Please start Docker Desktop and try again.")
            sys.exit(1)
        
        debug_log("Docker validation successful")
        click.secho("✅ Docker is running", fg='green')
    
    def setup_production_mode(self, workflow_type: str) -> dict:
        """Set up production mode configuration."""
        debug_log(f"Setting up production mode for workflow: {workflow_type}")
        # Set up workflow-specific scripts directory
        if self.platform == "windows":
            scripts_dir = Path.home() / ".sip_lims_workflow_manager" / f"{workflow_type}_scripts"
        else:
            scripts_dir = Path.home() / ".sip_lims_workflow_manager" / f"{workflow_type}_scripts"
        
        config = {
            "scripts_path": str(scripts_dir),
            "app_env": "production",
            "docker_image": self.branch_info['remote_image']
        }
        debug_log(f"Production mode config: {config}")
        return config
    
    def launch(self, workflow_type: Optional[str] = None, project_path: Optional[Path] = None,
               scripts_path: Optional[Path] = None, mode: Optional[str] = None, perform_all_updates: bool = False):
        """Main launcher workflow."""
        debug_log("Starting main launch workflow...")
        debug_log(f"Parameters: workflow_type={workflow_type}, project_path={project_path}, scripts_path={scripts_path}, mode={mode}, perform_all_updates={perform_all_updates}")
        
        try:
            click.secho("--- Starting SIP LIMS Workflow Manager (Docker) ---", fg='blue', bold=True)
            
            # 1. Environment validation
            debug_log("Step 1: Environment validation")
            self.validate_environment()
            
            # 2. Display branch information
            debug_log("Step 2: Display branch information")
            self.display_branch_info()
            
            # 3. Container cleanup
            debug_log("Step 3: Container cleanup")
            self.container_manager.cleanup_existing_containers()
            
            # 4. Workflow type selection
            debug_log("Step 4: Workflow type selection")
            if not workflow_type:
                workflow_type = UserInterface.select_workflow_type()
            debug_log(f"Final workflow type: {workflow_type}")
            
            # 5. Mode selection and configuration (simplified for debug)
            debug_log("Step 5: Mode configuration (using production mode)")
            mode_config = self.setup_production_mode(workflow_type)
            
            # 6. Project path selection
            debug_log("Step 6: Project path selection")
            if not project_path:
                project_path = UserInterface.select_project_path()
            debug_log(f"Final project path: {project_path}")
            
            # 7. Scripts updates (debug mode only performs scripts updates)
            debug_log("Step 7: Scripts updates")
            self.update_manager.check_scripts_updates(workflow_type, mode_config["scripts_path"])
            
            # 8. Launch Docker container
            debug_log("Step 8: Launching Docker container")
            self.container_manager.launch_container(project_path, workflow_type, mode_config)
            
        except KeyboardInterrupt:
            debug_log("Launch cancelled by user (KeyboardInterrupt)")
            click.echo("\n❌ Launch cancelled by user")
            sys.exit(1)
        except Exception as e:
            debug_log(f"FATAL ERROR in launch: {e}")
            debug_log(f"Traceback: {traceback.format_exc()}")
            click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
            sys.exit(1)
    
    def display_branch_info(self):
        """Display current branch information."""
        debug_log("Displaying branch information...")
        click.echo()
        click.secho("🌿 Branch Information:", fg='blue', bold=True)
        click.echo(f"   ✅ Current branch: {self.branch_info['branch']}")
        click.echo(f"   ✅ Docker tag: {self.branch_info['tag']}")
        click.echo(f"   ✅ Local image: {self.branch_info['local_image']}")
        click.echo(f"   ✅ Remote image: {self.branch_info['remote_image']}")
        debug_log(f"Branch info displayed: {self.branch_info}")


def main():
    """Debug version main function with --debug flag support."""
    debug_log("Main function started")
    
    # Parse command line arguments for --debug flag
    parser = argparse.ArgumentParser(description="SIP LIMS Workflow Manager Docker Launcher (Debug Version)")
    parser.add_argument('--debug', action='store_true',
                       help='Enable Smart Sync debug logging (sets SMART_SYNC_DEBUG=true)')
    args = parser.parse_args()
    
    # Set debug environment variable if flag is provided
    if args.debug:
        os.environ["SMART_SYNC_DEBUG"] = "true"
        os.environ["SMART_SYNC_DEBUG_LEVEL"] = "DEBUG"
        click.secho("🔍 Smart Sync debug logging enabled", fg='cyan')
        debug_log("Smart Sync debug logging enabled via --debug flag")
    
    try:
        launcher = DockerLauncher()
        launcher.launch()
    except KeyboardInterrupt:
        debug_log("Main function interrupted by user")
        print("\n❌ Launch cancelled by user")
        sys.exit(1)
    except Exception as e:
        debug_log(f"Main function fatal error: {e}")
        debug_log(f"Traceback: {traceback.format_exc()}")
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)
    finally:
        debug_log("Main function finished")
        debug_log("=" * 80)


if __name__ == "__main__":
    main()