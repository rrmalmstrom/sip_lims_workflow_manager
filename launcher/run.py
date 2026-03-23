#!/usr/bin/env python3
"""
Native Launcher for SIP LIMS Workflow Manager
Cross-platform replacement for Docker-based execution

This launcher provides a consistent interface for launching the
native Python workflow manager across Windows, macOS, and Linux platforms.
Replaces the previous Docker-based orchestration with direct Python execution.
"""

import os
import sys
import subprocess
import argparse
import signal
from pathlib import Path
from typing import Optional

# Add parent directory to Python path to find src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

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
            elif fg == 'cyan':
                print(f"\033[96m{message}\033[0m" if bold else f"\033[36m{message}\033[0m")
            else:
                print(message)
        
        @staticmethod
        def confirm(text, default=False):
            """Simple confirmation prompt."""
            suffix = " [Y/n]" if default else " [y/N]"
            response = input(text + suffix + ": ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes']


def validate_workflow_type(workflow_type: str) -> str:
    """Validate and normalize workflow type."""
    if not workflow_type:
        click.secho("❌ ERROR: No workflow type provided.", fg='red', bold=True)
        sys.exit(1)
    
    workflow_type = workflow_type.lower().strip()
    
    # Handle various input formats - keep sps-ce format for ScriptsUpdater compatibility
    if workflow_type in ['sip', 'sip-lims']:
        return "sip"
    elif workflow_type in ['sps', 'sps-ce', 'spsceq']:
        return "sps-ce"  # Always return sps-ce for consistency with ScriptsUpdater
    elif workflow_type in ['capsule-sorting', 'capsule_sorting']:
        return "capsule-sorting"  # Always return capsule-sorting for consistency with ScriptsUpdater
    else:
        click.secho(f"❌ ERROR: Unknown workflow type '{workflow_type}'", fg='red', bold=True)
        click.secho("Valid options: sip, sps-ce, capsule-sorting", fg='red')
        sys.exit(1)


def validate_project_path(project_path: Optional[str]) -> Path:
    """Validate and resolve project path."""
    if not project_path:
        # Default to current directory
        return Path.cwd()
    
    path = Path(project_path).resolve()
    
    if not path.exists():
        click.secho(f"❌ ERROR: Project path does not exist: {path}", fg='red', bold=True)
        sys.exit(1)
    
    if not path.is_dir():
        click.secho(f"❌ ERROR: Project path is not a directory: {path}", fg='red', bold=True)
        sys.exit(1)
    
    return path


def setup_environment_variables(workflow_type: str, project_path: Path, scripts_path: Optional[str] = None):
    """Set up environment variables for the native launcher."""
    # DEBUG: Show what we're setting up
    click.echo(f"🔧 DEBUG: Setting up environment variables")
    click.echo(f"   Workflow Type: {workflow_type}")
    click.echo(f"   Project Path: {project_path}")
    click.echo(f"   Scripts Path: {scripts_path}")
    
    # Set workflow type for app.py title display (preserves Docker-era functionality)
    os.environ["WORKFLOW_TYPE"] = workflow_type.upper()
    
    # Set project information
    os.environ["PROJECT_PATH"] = str(project_path)
    os.environ["PROJECT_NAME"] = project_path.name
    
    # Set scripts path if provided
    if scripts_path:
        scripts_path_resolved = Path(scripts_path).resolve()
        click.echo(f"   Resolved Scripts Path: {scripts_path_resolved}")
        click.echo(f"   Scripts Path Exists: {scripts_path_resolved.exists()}")
        
        if scripts_path_resolved.exists():
            os.environ["SCRIPTS_PATH"] = str(scripts_path_resolved)
            click.secho(f"✅ SCRIPTS_PATH set to: {scripts_path_resolved}", fg='green')
        else:
            click.secho(f"⚠️  Warning: Scripts path does not exist: {scripts_path}", fg='yellow')
    else:
        click.secho(f"❌ WARNING: No scripts_path provided to setup_environment_variables!", fg='red')
    
    # Set native execution mode
    os.environ["EXECUTION_MODE"] = "native"
    os.environ["APP_ENV"] = "production"
    
    # DEBUG: Show final environment variables
    click.echo(f"🔍 Final environment variables:")
    click.echo(f"   WORKFLOW_TYPE = {os.environ.get('WORKFLOW_TYPE', 'NOT SET')}")
    click.echo(f"   PROJECT_PATH = {os.environ.get('PROJECT_PATH', 'NOT SET')}")
    click.echo(f"   SCRIPTS_PATH = {os.environ.get('SCRIPTS_PATH', 'NOT SET')}")


def perform_updates():
    """Perform core repository updates only (not workflow-specific scripts)."""
    try:
        click.secho("🔄 Performing core repository updates...", fg='blue', bold=True)
        click.echo("   • Repository updates only")
        click.echo("   • Workflow-specific scripts are updated during normal execution")
        click.echo()
        
        # Import update components
        try:
            from src.git_update_manager import GitUpdateManager
        except ImportError as e:
            click.secho(f"❌ ERROR: Failed to import update modules: {e}", fg='red', bold=True)
            return False
        
        # Repository updates only
        click.echo("🔍 Checking for repository updates...")
        try:
            git_manager = GitUpdateManager("application", ".")
            update_check = git_manager.check_for_updates()
            if update_check.get('update_available', False):
                update_result = git_manager.update_to_latest()
                if update_result.get('success', False):
                    click.secho("✅ Repository updated", fg='green')
                else:
                    click.secho(f"⚠️  Repository update failed: {update_result.get('error', 'Unknown error')}", fg='yellow')
            else:
                click.secho("✅ Repository is up to date", fg='green')
        except Exception as e:
            click.secho(f"⚠️  Warning: Repository update failed: {e}", fg='yellow')
        
        click.secho("✅ Core updates completed", fg='green')
        return True
        
    except Exception as e:
        click.secho(f"❌ ERROR during updates: {e}", fg='red', bold=True)
        return False


def check_and_update_scripts_automatically(workflow_type: str):
    """Automatically check and update workflow-specific scripts during normal execution."""
    try:
        from src.scripts_updater import ScriptsUpdater
        
        scripts_updater = ScriptsUpdater(workflow_type=workflow_type)
        scripts_dir = Path.home() / ".sip_lims_workflow_manager" / f"{workflow_type}_scripts"
        
        # Always show what we're checking
        click.secho(f"🔍 Checking {workflow_type.upper()} scripts for updates...", fg='blue')
        click.echo(f"   Scripts location: {scripts_dir}")
        
        # Check for updates with visible feedback
        update_check = scripts_updater.check_scripts_update(str(scripts_dir))
        if update_check.get('update_available', False):
            click.secho(f"🔄 Auto-updating {workflow_type.upper()} scripts...", fg='blue')
            update_result = scripts_updater.update_scripts(str(scripts_dir))
            if update_result.get('success', False):
                click.secho(f"✅ {workflow_type.upper()} scripts auto-updated", fg='green')
            else:
                click.secho(f"⚠️  Auto-update failed: {update_result.get('error', 'Unknown error')}", fg='yellow')
        else:
            click.secho(f"✅ {workflow_type.upper()} scripts are up to date", fg='green')
        
    except Exception as e:
        # Show error instead of silent failure
        click.secho(f"⚠️  Script update check failed: {e}", fg='yellow')


def detect_mode() -> str:
    """Detect if running in developer or production mode."""
    project_root = Path.cwd()
    developer_marker = project_root / "config" / "developer.marker"
    return "developer" if developer_marker.exists() else "production"


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


def interactive_workflow_selection():
    """Interactive workflow type selection."""
    click.echo()
    click.secho("🧪 SIP LIMS Workflow Manager - Native Launcher", fg='blue', bold=True)
    click.echo()
    click.echo("Available workflow types:")
    click.echo("  1. SIP - Standard workflow")
    click.echo("  2. SPS-CE - SPS workflow")
    click.echo("  3. Capsule Sorting - Capsule Sorting workflow")
    click.echo()
    
    while True:
        choice = click.prompt("Select workflow type (1, 2, or 3)", type=str).strip()
        
        if choice == '1':
            return 'sip'
        elif choice == '2':
            return 'sps-ce'
        elif choice == '3':
            return 'capsule-sorting'
        else:
            click.secho(f"❌ Invalid choice '{choice}'. Please enter 1, 2, or 3.", fg='red')
            click.secho("❌ Terminating - invalid workflow selection", fg='red', bold=True)
            sys.exit(1)


def normalize_path(path_input: str) -> Path:
    """Normalize path input from drag-and-drop or manual entry."""
    # Strip quotes and whitespace
    path_str = path_input.strip().strip('"').strip("'")
    
    # Convert to Path object without resolving (to avoid concatenation issues)
    path = Path(path_str).expanduser()
    
    # Return absolute path without resolve() to avoid current directory concatenation
    if path.is_absolute():
        return path
    else:
        # If relative path provided, make it absolute from current directory
        return Path.cwd() / path


def interactive_project_selection():
    """Interactive project folder selection with drag-and-drop support."""
    click.echo()
    click.secho("📁 Project Folder Selection", fg='blue', bold=True)
    click.echo("Please drag and drop your project folder here, then press Enter:")
    
    while True:
        try:
            path_input = click.prompt("Project path", type=str)
            project_path = normalize_path(path_input)
            
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


def handle_mode_selection(workflow_type: str) -> dict:
    """Handle mode detection and configuration."""
    mode = detect_mode()
    
    if mode == "developer":
        # Developer detected - ask for production vs development workflow
        use_production_workflow = choose_developer_mode()
        
        if use_production_workflow:
            # Developer chose production workflow - use auto-updates
            return setup_production_mode(workflow_type)
        else:
            # Developer chose development workflow - use local scripts
            return setup_development_mode(workflow_type)
    else:
        # Regular production user - always use auto-updates
        return setup_production_mode(workflow_type)


def setup_production_mode(workflow_type: str) -> dict:
    """Set up production mode configuration."""
    scripts_dir = Path.home() / ".sip_lims_workflow_manager" / f"{workflow_type}_scripts"
    
    return {
        "scripts_path": str(scripts_dir),
        "app_env": "production",
        "mode": "production"
    }


def setup_development_mode(workflow_type: str) -> dict:
    """Set up development mode configuration."""
    click.echo()
    click.secho(f"📁 {workflow_type.upper()} Development Scripts Selection", fg='blue', bold=True)
    click.echo(f"Please drag and drop your {workflow_type} workflow development scripts folder here, then press Enter:")
    
    while True:
        try:
            path_input = click.prompt("Scripts path", type=str)
            scripts_path = normalize_path(path_input)
            
            if not scripts_path.exists():
                click.secho(f"❌ Path does not exist: {scripts_path}", fg='red')
                continue
            
            if not scripts_path.is_dir():
                click.secho(f"❌ Path is not a directory: {scripts_path}", fg='red')
                continue
            
            click.secho(f"✅ Selected development scripts folder: {scripts_path.name}", fg='green')
            click.echo(f"📍 Full path: {scripts_path}")
            
            return {
                "scripts_path": str(scripts_path),
                "app_env": "development",
                "mode": "development"
            }
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            click.secho(f"❌ Error processing path: {e}", fg='red')


def launch_streamlit_app(workflow_type: str, project_path: Path,
                        scripts_path: Optional[str] = None,
                        mode: Optional[str] = None,
                        perform_core_updates: bool = False):
    """Launch the Streamlit workflow manager."""
    streamlit_process = None
    
    def signal_handler(signum, frame):
        """Handle Ctrl+C and other signals by terminating Streamlit gracefully."""
        click.echo()
        click.secho("🛑 Received interrupt signal - shutting down gracefully...", fg='yellow')
        if streamlit_process:
            try:
                streamlit_process.terminate()
                streamlit_process.wait(timeout=5)
                click.secho("✅ Streamlit process terminated successfully", fg='green')
            except subprocess.TimeoutExpired:
                click.secho("⚠️  Force killing Streamlit process...", fg='yellow')
                streamlit_process.kill()
                streamlit_process.wait()
            except Exception as e:
                click.secho(f"⚠️  Error during shutdown: {e}", fg='yellow')
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        click.echo()
        click.secho("--- Starting SIP LIMS Workflow Manager (Native) ---", fg='blue', bold=True)
        click.echo(f"   Workflow Type: {workflow_type.upper()}")
        click.echo(f"   Project Path: {project_path}")
        click.echo(f"   Execution Mode: Native Python")
        click.echo()
        click.secho("💡 Press Ctrl+C to stop the workflow manager", fg='cyan')
        click.echo()
        
        # Set up environment variables (preserves workflow type propagation)
        setup_environment_variables(workflow_type, project_path, scripts_path)
        
        # Handle updates mode
        if perform_core_updates:
            success = perform_updates()
            click.echo()
            if success:
                click.secho("🔄 RESTART REQUIRED", fg='yellow', bold=True)
                click.echo("Please restart the script to launch with the latest version:")
                click.echo("   python run.py")
            else:
                click.secho("⚠️  Updates completed with warnings", fg='yellow')
            return
        
        # Automatically check and update workflow-specific scripts during normal execution
        check_and_update_scripts_automatically(workflow_type)
        
        # Launch the Streamlit app directly
        click.secho("🚀 Launching Streamlit workflow manager...", fg='green', bold=True)
        
        # Check if streamlit is available
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "--version"],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.secho("❌ ERROR: Streamlit is not installed", fg='red', bold=True)
            click.echo("Please install streamlit: pip install streamlit")
            sys.exit(1)
        
        # Prepare arguments for app.py (Streamlit) - app.py is in parent directory
        app_py_path = str(Path(__file__).parent.parent / "app.py")
        app_args = [
            sys.executable, "-m", "streamlit", "run", app_py_path,
            "--server.headless", "true",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ]
        
        # Execute app.py with Streamlit using Popen for better signal handling
        streamlit_process = subprocess.Popen(app_args, env=os.environ.copy())
        
        # Wait for the process to complete
        result = streamlit_process.wait()
        
        # Exit with the same code as the Streamlit app
        sys.exit(result)
        
    except KeyboardInterrupt:
        click.echo()
        click.secho("❌ Launch cancelled by user", fg='red')
        sys.exit(1)
    except FileNotFoundError:
        click.secho("❌ ERROR: app.py not found", fg='red', bold=True)
        click.echo("Please ensure app.py is in the parent directory of the launcher")
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create argument parser for the native launcher - interactive mode only."""
    parser = argparse.ArgumentParser(
        description="SIP LIMS Workflow Manager Native Launcher\n\n"
                   "Interactive launcher for the native Python workflow manager.\n"
                   "All workflow and project configuration is done through interactive prompts.\n"
                   "Replaces Docker-based execution with direct Python execution.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Only allow utility flags - no workflow/project arguments
    parser.add_argument('--updates', action='store_true',
                       help='Perform core updates (repository, scripts) and terminate with restart instructions')
    parser.add_argument('--version', action='version', version='2.0.0-native')
    
    return parser


# Interactive-only interface with limited command-line support
def main():
    """
    SIP LIMS Workflow Manager Native Launcher - Interactive Mode Only
    
    Cross-platform launcher for the native Python workflow manager.
    Replaces Docker-based execution with direct Python execution.
    
    All workflow and project configuration is done through interactive prompts.
    Command-line arguments are only supported for utility functions like --updates.
    """
    try:
        # Check for utility command-line arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Handle updates flag
        if args.updates:
            # Perform core repository updates only (no workflow selection needed)
            success = perform_updates()
            if HAS_CLICK:
                click.echo()
                if success:
                    click.secho("🔄 RESTART REQUIRED", fg='yellow', bold=True)
                    click.echo("Please restart the script to launch with the latest version:")
                    click.echo("   python run.py")
                else:
                    click.secho("⚠️  Updates completed with warnings", fg='yellow')
            else:
                print()
                if success:
                    print("🔄 RESTART REQUIRED")
                    print("Please restart the script to launch with the latest version:")
                    print("   python run.py")
                else:
                    print("⚠️  Updates completed with warnings")
            return
        
        # Normal interactive workflow
        workflow_type = interactive_workflow_selection()
        project_path = interactive_project_selection()
        
        # Always use interactive mode selection and configuration
        mode_config = handle_mode_selection(workflow_type)
        scripts_path = mode_config["scripts_path"]
        mode = mode_config["mode"]
        
        # Validate and normalize inputs
        workflow_type = validate_workflow_type(workflow_type)
        project_path = validate_project_path(str(project_path))
        
        # Launch the Streamlit workflow manager
        launch_streamlit_app(
            workflow_type=workflow_type,
            project_path=project_path,
            scripts_path=scripts_path,
            mode=mode,
            perform_core_updates=False
        )
        
    except KeyboardInterrupt:
        if HAS_CLICK:
            click.echo()
            click.secho("❌ Launch cancelled by user", fg='red')
        else:
            print("\n❌ Launch cancelled by user")
        sys.exit(1)
    except Exception as e:
        if HAS_CLICK:
            click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
        else:
            print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()