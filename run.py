#!/usr/bin/env python3
"""
Unified Docker Launcher for SIP LIMS Workflow Manager
Cross-platform replacement for run.mac.command and run.windows.bat

This launcher provides a consistent, robust interface for launching the
containerized workflow manager across Windows, macOS, and Linux platforms.
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

# Try to import Click, fall back to standard library if not available
try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False
    # Create a minimal click-like interface using standard library
    class click:
        @staticmethod
        def echo(message="", **kwargs):
            print(message)
        
        @staticmethod
        def secho(message, fg=None, bold=False, **kwargs):
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
            while True:
                try:
                    response = input(f"{text}: ").strip()
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
            suffix = " [Y/n]" if default else " [y/N]"
            while True:
                response = input(f"{text}{suffix}: ").strip().lower()
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
    from utils.branch_utils import (
        get_current_branch, get_docker_tag_for_current_branch,
        get_local_image_name_for_current_branch, get_remote_image_name_for_current_branch,
        get_branch_info, GitRepositoryError, BranchDetectionError
    )
    from src.update_detector import UpdateDetector
    from src.scripts_updater import ScriptsUpdater
    from src.fatal_sync_checker import check_fatal_sync_errors
except ImportError as e:
    click.secho(f"❌ ERROR: Failed to import required modules: {e}", fg='red', bold=True)
    click.echo("Make sure you're running from the project root directory.")
    sys.exit(1)


class PlatformAdapter:
    """Platform-specific adaptations for cross-platform compatibility."""
    
    @staticmethod
    def get_platform() -> str:
        """Get normalized platform name."""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        return system
    
    @staticmethod
    def get_user_ids() -> Dict[str, str]:
        """Get user/group IDs for Docker volume mapping."""
        if platform.system() == "Windows":
            # Windows Docker Desktop standard mapping
            return {
                "USER_ID": os.environ.get("DOCKER_USER_ID", "1000"),
                "GROUP_ID": os.environ.get("DOCKER_GROUP_ID", "1000")
            }
        else:
            # Unix-like systems
            return {
                "USER_ID": str(os.getuid()),
                "GROUP_ID": str(os.getgid())
            }
    
    @staticmethod
    def validate_docker() -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def normalize_path(path_str: str) -> Path:
        """Normalize path input across platforms."""
        # Remove quotes and whitespace
        cleaned = path_str.strip().strip('"').strip("'")
        
        # Handle drag-and-drop artifacts
        if platform.system() == "Darwin":  # macOS
            # Remove escape characters from drag-and-drop
            cleaned = cleaned.replace('\\ ', ' ')
        
        # Try to resolve the path, but handle Windows network path issues gracefully
        try:
            return Path(cleaned).resolve()
        except (OSError, ValueError) as e:
            # On Windows, if resolve() fails (common with UNC paths), fall back to unresolved path
            # This preserves Docker compatibility for network drives while allowing resolve() to work
            # for mapped drives and local paths where it's beneficial
            if platform.system() == "Windows":
                # Convert forward slashes to backslashes for Windows consistency
                if cleaned.startswith(('\\\\', '//')):
                    cleaned = cleaned.replace('/', '\\')
                return Path(cleaned)
            # Re-raise the exception on Mac/Linux as this indicates a real problem
            raise
    
    @staticmethod
    def get_docker_compose_command() -> List[str]:
        """Get the appropriate docker-compose command for the platform."""
        # Try docker compose (newer) first, then docker-compose (legacy)
        for cmd in [["docker", "compose"], ["docker-compose"]]:
            try:
                subprocess.run(cmd + ["--version"], capture_output=True, check=True, timeout=5)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise RuntimeError("Neither 'docker compose' nor 'docker-compose' found")


class UserInterface:
    """Rich CLI interface using Click for cross-platform user interaction."""
    
    @staticmethod
    def select_workflow_type() -> str:
        """Interactive workflow type selection."""
        click.echo()
        click.secho("🧪 Select workflow type:", fg='blue', bold=True)
        click.echo("1) SIP (Stable Isotope Probing)")
        click.echo("2) SPS-CE (Single Particle Sorting - Cell Enrichment)")
        click.echo()
        
        while True:
            choice = click.prompt("Enter choice (1 or 2)", type=str).strip()
            if choice == "1":
                click.secho("✅ Selected: SIP workflow", fg='green')
                return "sip"
            elif choice == "2":
                click.secho("✅ Selected: SPS-CE workflow", fg='green')
                return "sps-ce"
            else:
                click.secho(f"❌ Invalid choice '{choice}'. Please enter 1 or 2.", fg='red')
    
    @staticmethod
    def select_project_path() -> Path:
        """Interactive project folder selection with validation."""
        click.echo()
        click.secho("📁 Project Folder Selection", fg='blue', bold=True)
        click.echo("Please drag and drop your project folder here, then press Enter:")
        
        while True:
            try:
                path_input = click.prompt("Project path", type=str)
                project_path = PlatformAdapter.normalize_path(path_input)
                
                if not project_path.exists():
                    click.secho(f"❌ Path does not exist: {project_path}", fg='red')
                    continue
                
                if not project_path.is_dir():
                    click.secho(f"❌ Path is not a directory: {project_path}", fg='red')
                    continue
                
                click.secho(f"✅ Selected project folder: {project_path.name}", fg='green')
                click.echo(f"📍 Full path: {project_path}")
                return project_path
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                click.secho(f"❌ Error processing path: {e}", fg='red')
    
    @staticmethod
    def select_scripts_path(workflow_type: str) -> Path:
        """Interactive scripts folder selection for development mode."""
        click.echo()
        click.secho(f"📁 {workflow_type.upper()} Development Scripts Selection", fg='blue', bold=True)
        click.echo(f"Please drag and drop your {workflow_type} workflow development scripts folder here, then press Enter:")
        
        while True:
            try:
                path_input = click.prompt("Scripts path", type=str)
                scripts_path = PlatformAdapter.normalize_path(path_input)
                
                if not scripts_path.exists():
                    click.secho(f"❌ Path does not exist: {scripts_path}", fg='red')
                    continue
                
                if not scripts_path.is_dir():
                    click.secho(f"❌ Path is not a directory: {scripts_path}", fg='red')
                    continue
                
                click.secho(f"✅ Selected development scripts folder: {scripts_path.name}", fg='green')
                click.echo(f"📍 Full path: {scripts_path}")
                return scripts_path
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                click.secho(f"❌ Error processing path: {e}", fg='red')
    
    @staticmethod
    def choose_developer_mode() -> bool:
        """Developer mode choice selection."""
        click.echo()
        click.secho("🔧 Developer mode detected", fg='blue', bold=True)
        click.echo()
        click.echo("Choose your workflow mode:")
        click.echo("1) Production mode (auto-updates, centralized scripts)")
        click.echo("2) Development mode (local scripts, no auto-updates)")
        click.echo()
        
        while True:
            choice = click.prompt("Enter choice (1 or 2)", type=str).strip()
            if choice == "1":
                click.secho("✅ Using production mode workflow", fg='green')
                return True  # Use production workflow
            elif choice == "2":
                click.secho("✅ Using development mode workflow", fg='green')
                return False  # Use development workflow
            else:
                click.secho(f"❌ Invalid choice '{choice}'. Please enter 1 or 2.", fg='red')
    
    @staticmethod
    def confirm_action(message: str, default: bool = False) -> bool:
        """Confirmation prompt with styling."""
        return click.confirm(
            click.style(message, fg='yellow', bold=True),
            default=default
        )


class ContainerManager:
    """Docker container lifecycle management."""
    
    def __init__(self, branch_info: dict):
        self.branch_info = branch_info
        self.local_image_name = branch_info['local_image']
        self.remote_image_name = branch_info['remote_image']
        self.compose_cmd = PlatformAdapter.get_docker_compose_command()
    
    def cleanup_existing_containers(self):
        """Stop and remove existing workflow manager containers."""
        click.echo("🛑 Checking for running workflow manager containers...")
        
        try:
            # Find containers using workflow manager images
            result = subprocess.run([
                "docker", "ps", "-a",
                "--filter", f"ancestor={self.remote_image_name}",
                "--filter", f"ancestor={self.local_image_name}",
                "--format", "{{.ID}} {{.Names}} {{.Status}}"
            ], capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                click.echo("📋 Found workflow manager containers:")
                container_ids = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        container_id, name = parts[0], parts[1]
                        status = ' '.join(parts[2:])
                        click.echo(f"    - {name} ({container_id}): {status}")
                        container_ids.append(container_id)
                
                if container_ids:
                    click.echo("🛑 Stopping workflow manager containers...")
                    subprocess.run(["docker", "stop"] + container_ids, 
                                 capture_output=True, check=False)
                    
                    click.echo("🗑️  Removing workflow manager containers...")
                    subprocess.run(["docker", "rm"] + container_ids, 
                                 capture_output=True, check=False)
                    
                    click.secho("✅ Workflow manager containers cleaned up", fg='green')
            else:
                click.secho("✅ No running workflow manager containers found", fg='green')
                
        except subprocess.CalledProcessError as e:
            click.secho(f"⚠️  Warning: Could not check containers: {e}", fg='yellow')
    
    def launch_container(self, project_path: Path, workflow_type: str, mode_config: dict):
        """Launch the Docker container using docker-compose."""
        click.echo()
        click.secho("🐳 Launching Docker container...", fg='blue', bold=True)
        
        # Prepare environment variables
        env = self.prepare_environment(project_path, workflow_type, mode_config)
        
        # Display environment summary
        self.display_environment_summary(env)
        
        # Launch container
        try:
            click.echo("--- Starting Container ---")
            subprocess.run(
                self.compose_cmd + ["up"],
                cwd=Path.cwd(),
                env={**os.environ, **env},
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker container launch failed: {e}")
        except KeyboardInterrupt:
            click.echo("\n🛑 Container stopped by user")
        finally:
            click.echo("Application has been shut down.")
    
    def prepare_environment(self, project_path: Path, workflow_type: str, mode_config: dict) -> Dict[str, str]:
        """Prepare environment variables for Docker container."""
        user_ids = PlatformAdapter.get_user_ids()
        
        env = {
            "PROJECT_PATH": str(project_path),
            "PROJECT_NAME": project_path.name,
            "SCRIPTS_PATH": mode_config["scripts_path"],
            "WORKFLOW_TYPE": workflow_type,
            "APP_ENV": mode_config["app_env"],
            "DOCKER_IMAGE": mode_config["docker_image"],
            **user_ids
        }
        
        return env
    
    def display_environment_summary(self, env: Dict[str, str]):
        """Display environment configuration summary."""
        click.echo("--- Environment Variables ---")
        for key, value in env.items():
            if key in ["USER_ID", "GROUP_ID", "PROJECT_PATH", "PROJECT_NAME", 
                      "SCRIPTS_PATH", "APP_ENV", "DOCKER_IMAGE", "WORKFLOW_TYPE"]:
                click.echo(f"{key}: {value}")


class UpdateManager:
    """Integrate existing update detection and management."""
    
    def __init__(self, branch_info: dict):
        self.branch_info = branch_info
        self.update_detector = UpdateDetector()
    
    def perform_updates(self, workflow_type: str, mode_config: dict, perform_all_updates: bool = False):
        """Perform updates before container launch based on mode and flags."""
        if mode_config["app_env"] == "production":
            self.production_auto_update(workflow_type, mode_config, perform_all_updates)
        else:
            click.secho("🔧 Development mode - skipping auto-updates", fg='blue')
    
    def production_auto_update(self, workflow_type: str, mode_config: dict, perform_all_updates: bool = False):
        """Production mode automatic updates with configurable behavior."""
        if perform_all_updates:
            click.secho("🏭 Production mode - performing all updates...", fg='blue', bold=True)
            
            # Perform all updates (same as current default behavior)
            self.check_fatal_sync_errors()
            self.check_repository_updates()
            self.check_docker_updates()
            self.check_scripts_updates(workflow_type, mode_config["scripts_path"])
        else:
            click.secho("🏭 Production mode - performing scripts updates only...", fg='blue', bold=True)
            self.display_skipped_updates_message()
            
            # Only perform scripts updates
            self.check_scripts_updates(workflow_type, mode_config["scripts_path"])
    
    def display_skipped_updates_message(self):
        """Display informational message about skipped updates."""
        click.echo()
        click.secho("ℹ️  Update Information:", fg='blue', bold=True)
        click.echo("   • Core system updates are skipped by default in production mode")
        click.echo("   • Skipping: Fatal sync check, repository updates, Docker image updates")
        click.echo("   • Performing: Scripts updates (always enabled)")
        click.echo("   • To enable all updates, use the --updates flag")
        click.echo()
    
    def check_fatal_sync_errors(self):
        """Check for fatal repository/Docker sync errors."""
        click.echo("🔍 Checking for fatal repository/Docker sync errors...")
        try:
            result = check_fatal_sync_errors()
            if result == 0:
                click.secho("✅ No fatal sync errors detected", fg='green')
            else:
                raise RuntimeError("💥 FATAL SYNC ERROR DETECTED - STOPPING EXECUTION")
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError("💥 FATAL SYNC ERROR DETECTED - STOPPING EXECUTION")
    
    def check_repository_updates(self):
        """Check and handle workflow manager repository updates."""
        click.echo("🔍 Checking for workflow manager repository updates...")
        
        try:
            # Get current branch
            current_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            if not current_branch:
                click.secho("⚠️  Warning: Could not determine current branch", fg='yellow')
                return
            
            # Fetch latest remote information
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
            
            # Check if local branch is behind remote
            commits_behind = subprocess.run(
                ["git", "rev-list", "--count", f"HEAD..origin/{current_branch}"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            commits_behind = int(commits_behind)
            
            if commits_behind > 0:
                click.echo(f"📦 Workflow manager updates available ({commits_behind} commit(s) behind) - updating repository...")
                
                # Check for local changes that might conflict
                result = subprocess.run(
                    ["git", "diff-index", "--quiet", "HEAD", "--"],
                    capture_output=True
                )
                
                if result.returncode != 0:
                    click.secho("⚠️  Warning: Local changes detected - skipping automatic update", fg='yellow')
                    click.echo("   Please commit or stash your changes and update manually")
                    return
                
                # Pull the updates
                subprocess.run(["git", "pull", "origin", current_branch], check=True)
                click.secho("✅ Workflow manager repository updated successfully", fg='green')
                click.secho("🔄 Note: Restart the script to use the updated version", fg='blue')
            else:
                click.secho("✅ Workflow manager repository is up to date", fg='green')
                
        except subprocess.CalledProcessError as e:
            click.secho(f"⚠️  Warning: Could not check for repository updates: {e}", fg='yellow')
    
    def check_docker_updates(self):
        """Check and handle Docker image updates."""
        click.echo("🔍 Checking for Docker image updates...")
        
        try:
            result = self.update_detector.check_docker_update(
                tag=self.branch_info['tag'],
                branch=self.branch_info['branch']
            )
            
            if result.get("update_available", False):
                if result.get("chronology_uncertain", False) and result.get("requires_user_confirmation", False):
                    # Handle chronology uncertainty
                    self.handle_chronology_warning(result)
                else:
                    click.echo("📦 Docker image update available - updating to latest version...")
                
                self.perform_docker_update()
            else:
                click.secho("✅ Docker image is up to date", fg='green')
                
        except Exception as e:
            click.secho(f"⚠️  Warning: Could not check for Docker updates: {e}", fg='yellow')
    
    def handle_chronology_warning(self, result: dict):
        """Handle chronology uncertainty in Docker updates."""
        click.echo()
        click.secho("⚠️  **CHRONOLOGY WARNING**", fg='yellow', bold=True)
        click.echo(f"   {result.get('reason', 'Unknown reason')}")
        click.echo(f"   {result.get('warning', 'Chronology uncertain')}")
        click.echo()
        click.echo("The system cannot determine if your local Docker image is newer or older than the remote version.")
        click.echo("Proceeding with the update might overwrite a newer local version with an older remote version.")
        click.echo()
        
        if not UserInterface.confirm_action("Do you want to proceed with the Docker image update?", default=False):
            click.secho("❌ Docker image update cancelled by user", fg='red')
            click.secho("✅ Continuing with current local Docker image", fg='green')
            return
        
        click.secho("✅ User confirmed - proceeding with Docker image update...", fg='green')
    
    def perform_docker_update(self):
        """Perform Docker image update with cleanup."""
        try:
            remote_image_name = self.branch_info['remote_image']
            
            # Get current image ID for cleanup
            result = subprocess.run([
                "docker", "images", remote_image_name,
                "--format", "{{.ID}}"
            ], capture_output=True, text=True)
            
            old_image_id = result.stdout.strip() if result.returncode == 0 else None
            
            # Clean up old image before pulling new one
            if old_image_id:
                click.echo("🧹 Removing old Docker image before update...")
                subprocess.run(["docker", "rmi", remote_image_name], 
                             capture_output=True, check=False)
                subprocess.run(["docker", "image", "prune", "-f"], 
                             capture_output=True, check=False)
                click.secho("✅ Old Docker image cleaned up", fg='green')
            
            # Pull new image
            click.echo(f"📥 Pulling Docker image for branch: {self.branch_info['branch']}...")
            subprocess.run(["docker", "pull", remote_image_name], check=True)
            click.secho("✅ Docker image updated successfully", fg='green')
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker image update failed: {e}")
    
    def check_scripts_updates(self, workflow_type: str, scripts_path: str):
        """Check and handle scripts updates."""
        click.echo("🔍 Checking for workflow-specific script updates...")
        
        try:
            scripts_updater = ScriptsUpdater(workflow_type=workflow_type)
            result = scripts_updater.check_scripts_update(scripts_path)
            
            if result.get("update_available", False):
                click.echo("📦 Script updates available - updating scripts...")
                update_result = scripts_updater.update_scripts(scripts_path)
                
                if update_result.get("success", False):
                    click.secho("✅ Scripts updated successfully", fg='green')
                else:
                    click.secho(f"❌ ERROR: Failed to update scripts: {update_result.get('error', 'Unknown error')}", fg='red')
            else:
                click.secho("✅ Scripts are up to date", fg='green')
                
        except Exception as e:
            click.secho(f"⚠️  Warning: Could not check for script updates: {e}", fg='yellow')


class DockerLauncher:
    """Unified Docker container launcher for all platforms."""
    
    def __init__(self):
        self.platform = PlatformAdapter.get_platform()
        self.project_root = Path.cwd()
        
        # Initialize branch information
        try:
            self.branch_info = get_branch_info()
        except (GitRepositoryError, BranchDetectionError) as e:
            click.secho(f"❌ ERROR: {e}", fg='red', bold=True)
            sys.exit(1)
        
        # Initialize managers
        self.container_manager = ContainerManager(self.branch_info)
        self.update_manager = UpdateManager(self.branch_info)
    
    def validate_environment(self):
        """Validate the execution environment."""
        # Check Docker availability
        if not PlatformAdapter.validate_docker():
            click.secho("❌ ERROR: Docker is not running.", fg='red', bold=True)
            click.echo("Please start Docker Desktop and try again.")
            sys.exit(1)
        
        click.secho("✅ Docker is running", fg='green')
    
    def display_branch_info(self):
        """Display current branch information."""
        click.echo()
        click.secho("🌿 Branch Information:", fg='blue', bold=True)
        click.echo(f"   ✅ Current branch: {self.branch_info['branch']}")
        click.echo(f"   ✅ Docker tag: {self.branch_info['tag']}")
        click.echo(f"   ✅ Local image: {self.branch_info['local_image']}")
        click.echo(f"   ✅ Remote image: {self.branch_info['remote_image']}")
    
    def detect_mode(self) -> str:
        """Detect if running in developer or production mode."""
        developer_marker = self.project_root / "config" / "developer.marker"
        return "developer" if developer_marker.exists() else "production"
    
    def handle_mode_selection(self, workflow_type: str) -> dict:
        """Handle mode detection and configuration."""
        mode = self.detect_mode()
        
        if mode == "developer":
            # Developer detected - ask for production vs development workflow
            use_production_workflow = UserInterface.choose_developer_mode()
            
            if use_production_workflow:
                # Developer chose production workflow - use auto-updates
                return self.setup_production_mode(workflow_type)
            else:
                # Developer chose development workflow - use local scripts
                return self.setup_development_mode(workflow_type)
        else:
            # Regular production user - always use auto-updates
            return self.setup_production_mode(workflow_type)
    
    def setup_production_mode(self, workflow_type: str) -> dict:
        """Set up production mode configuration."""
        # Set up workflow-specific scripts directory
        if self.platform == "windows":
            scripts_dir = Path.home() / ".sip_lims_workflow_manager" / f"{workflow_type}_scripts"
        else:
            scripts_dir = Path.home() / ".sip_lims_workflow_manager" / f"{workflow_type}_scripts"
        
        return {
            "scripts_path": str(scripts_dir),
            "app_env": "production",
            "docker_image": self.branch_info['remote_image']
        }
    
    def setup_development_mode(self, workflow_type: str) -> dict:
        """Set up development mode configuration."""
        scripts_path = UserInterface.select_scripts_path(workflow_type)
        
        return {
            "scripts_path": str(scripts_path),
            "app_env": "development",
            "docker_image": self.branch_info['local_image']
        }
    
    def launch(self, workflow_type: Optional[str] = None, project_path: Optional[Path] = None,
               scripts_path: Optional[Path] = None, mode: Optional[str] = None, perform_all_updates: bool = False):
        """Main launcher workflow."""
        try:
            click.secho("--- Starting SIP LIMS Workflow Manager (Docker) ---", fg='blue', bold=True)
            
            # 1. Environment validation
            self.validate_environment()
            
            # 2. Display branch information
            self.display_branch_info()
            
            # 3. Container cleanup
            self.container_manager.cleanup_existing_containers()
            
            # 4. Workflow type selection
            if not workflow_type:
                workflow_type = UserInterface.select_workflow_type()
            
            # 5. Mode selection and configuration
            if scripts_path and mode:
                # CLI arguments provided
                mode_config = {
                    "scripts_path": str(scripts_path),
                    "app_env": mode,
                    "docker_image": self.branch_info['local_image'] if mode == "development" else self.branch_info['remote_image']
                }
            else:
                # Interactive mode selection
                mode_config = self.handle_mode_selection(workflow_type)
            
            # 6. Project path selection
            if not project_path:
                project_path = UserInterface.select_project_path()
            
            # 7. Update management
            self.update_manager.perform_updates(workflow_type, mode_config, perform_all_updates)
            
            # 8. Launch Docker container
            self.container_manager.launch_container(project_path, workflow_type, mode_config)
            
        except KeyboardInterrupt:
            click.echo("\n❌ Launch cancelled by user")
            sys.exit(1)
        except Exception as e:
            click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
            sys.exit(1)


def create_argument_parser():
    """Create argument parser for command line interface."""
    parser = argparse.ArgumentParser(
        description="SIP LIMS Workflow Manager Docker Launcher\n\n"
                   "Cross-platform launcher for the containerized workflow manager.\n"
                   "Replaces run.mac.command and run.windows.bat with unified Python implementation.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--workflow-type', choices=['sip', 'sps-ce'],
                       help='Workflow type (will prompt if not provided)')
    parser.add_argument('--project-path', type=Path,
                       help='Project folder path (will prompt if not provided)')
    parser.add_argument('--scripts-path', type=Path,
                       help='Scripts folder path (for development mode)')
    parser.add_argument('--mode', choices=['production', 'development'],
                       help='Execution mode (auto-detected if not provided)')
    parser.add_argument('--updates', action='store_true',
                       help='Perform all updates (fatal sync, repository, Docker, and scripts)')
    parser.add_argument('--version', action='version', version='1.1.0')
    
    return parser


if HAS_CLICK:
    @click.command()
    @click.option('--workflow-type', type=click.Choice(['sip', 'sps-ce']),
                  help='Workflow type (will prompt if not provided)')
    @click.option('--project-path', type=click.Path(exists=True, file_okay=False, path_type=Path),
                  help='Project folder path (will prompt if not provided)')
    @click.option('--scripts-path', type=click.Path(exists=True, file_okay=False, path_type=Path),
                  help='Scripts folder path (for development mode)')
    @click.option('--mode', type=click.Choice(['production', 'development']),
                  help='Execution mode (auto-detected if not provided)')
    @click.option('--updates', is_flag=True, help='Perform all updates (fatal sync, repository, Docker, and scripts)')
    @click.version_option(version="1.1.0", prog_name="SIP LIMS Workflow Manager Docker Launcher")
    def main(workflow_type, project_path, scripts_path, mode, updates):
        """
        SIP LIMS Workflow Manager Docker Launcher
        
        Cross-platform launcher for the containerized workflow manager.
        Replaces run.mac.command and run.windows.bat with unified Python implementation.
        """
        try:
            launcher = DockerLauncher()
            launcher.launch(
                workflow_type=workflow_type,
                project_path=project_path,
                scripts_path=scripts_path,
                mode=mode,
                perform_all_updates=updates
            )
            
        except KeyboardInterrupt:
            click.echo("\n❌ Launch cancelled by user")
            sys.exit(1)
        except Exception as e:
            click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
            sys.exit(1)

else:
    def main():
        """
        SIP LIMS Workflow Manager Docker Launcher (Fallback Mode)
        
        Cross-platform launcher for the containerized workflow manager.
        Replaces run.mac.command and run.windows.bat with unified Python implementation.
        """
        parser = create_argument_parser()
        args = parser.parse_args()
        
        try:
            launcher = DockerLauncher()
            launcher.launch(
                workflow_type=args.workflow_type,
                project_path=args.project_path,
                scripts_path=args.scripts_path,
                mode=args.mode,
                perform_all_updates=args.updates
            )
            
        except KeyboardInterrupt:
            print("\n❌ Launch cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()