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
from pathlib import Path
from typing import Optional

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
        return "sip"  # Default to SIP
    
    workflow_type = workflow_type.lower().strip()
    
    # Handle various input formats
    if workflow_type in ['sip', 'sip-lims']:
        return "sip"
    elif workflow_type in ['sps', 'sps-ce', 'spsceq']:
        return "sps"
    else:
        click.secho(f"⚠️  Warning: Unknown workflow type '{workflow_type}', defaulting to 'sip'", fg='yellow')
        return "sip"


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
    # Set workflow type for app.py title display (preserves Docker-era functionality)
    os.environ["WORKFLOW_TYPE"] = workflow_type.upper()
    
    # Set project information
    os.environ["PROJECT_PATH"] = str(project_path)
    os.environ["PROJECT_NAME"] = project_path.name
    
    # Set scripts path if provided
    if scripts_path:
        scripts_path_resolved = Path(scripts_path).resolve()
        if scripts_path_resolved.exists():
            os.environ["SCRIPTS_PATH"] = str(scripts_path_resolved)
        else:
            click.secho(f"⚠️  Warning: Scripts path does not exist: {scripts_path}", fg='yellow')
    
    # Set native execution mode
    os.environ["EXECUTION_MODE"] = "native"
    os.environ["APP_ENV"] = "production"


def perform_updates(workflow_type: str):
    """Perform core updates (repository and scripts)."""
    try:
        click.secho("🔄 Performing core updates...", fg='blue', bold=True)
        click.echo("   • Repository updates")
        click.echo("   • Scripts updates")
        click.echo()
        
        # Import update components
        try:
            from src.git_update_manager import GitUpdateManager
            from src.scripts_updater import ScriptsUpdater
        except ImportError as e:
            click.secho(f"❌ ERROR: Failed to import update modules: {e}", fg='red', bold=True)
            return False
        
        # Repository updates
        click.echo("🔍 Checking for repository updates...")
        try:
            git_manager = GitUpdateManager(".", "main")  # Adjust branch as needed
            repo_updated = git_manager.check_and_update()
            if repo_updated:
                click.secho("✅ Repository updated", fg='green')
            else:
                click.secho("✅ Repository is up to date", fg='green')
        except Exception as e:
            click.secho(f"⚠️  Warning: Repository update failed: {e}", fg='yellow')
        
        # Scripts updates
        click.echo("🔍 Checking for scripts updates...")
        try:
            scripts_updater = ScriptsUpdater(workflow_type=workflow_type)
            scripts_updated = scripts_updater.check_and_update()
            if scripts_updated:
                click.secho("✅ Scripts updated", fg='green')
            else:
                click.secho("✅ Scripts are up to date", fg='green')
        except Exception as e:
            click.secho(f"⚠️  Warning: Scripts update failed: {e}", fg='yellow')
        
        click.secho("✅ Updates completed", fg='green')
        return True
        
    except Exception as e:
        click.secho(f"❌ ERROR during updates: {e}", fg='red', bold=True)
        return False


def launch_streamlit_app(workflow_type: str, project_path: Path, 
                        scripts_path: Optional[str] = None, 
                        mode: Optional[str] = None,
                        perform_core_updates: bool = False):
    """Launch the Streamlit workflow manager."""
    try:
        click.echo()
        click.secho("--- Starting SIP LIMS Workflow Manager (Native) ---", fg='blue', bold=True)
        click.echo(f"   Workflow Type: {workflow_type.upper()}")
        click.echo(f"   Project Path: {project_path}")
        click.echo(f"   Execution Mode: Native Python")
        click.echo()
        
        # Set up environment variables (preserves workflow type propagation)
        setup_environment_variables(workflow_type, project_path, scripts_path)
        
        # Handle updates mode
        if perform_core_updates:
            success = perform_updates(workflow_type)
            click.echo()
            if success:
                click.secho("🔄 RESTART REQUIRED", fg='yellow', bold=True)
                click.echo("Please restart the script to launch with the latest version:")
                click.echo(f"   python run.py {workflow_type} \"{project_path}\"")
            else:
                click.secho("⚠️  Updates completed with warnings", fg='yellow')
            return
        
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
        
        # Prepare arguments for app.py (Streamlit)
        app_args = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ]
        
        # Execute app.py with Streamlit
        result = subprocess.run(app_args, env=os.environ.copy())
        
        # Exit with the same code as the Streamlit app
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        click.echo()
        click.secho("❌ Launch cancelled by user", fg='red')
        sys.exit(1)
    except FileNotFoundError:
        click.secho("❌ ERROR: app.py not found", fg='red', bold=True)
        click.echo("Please ensure app.py is in the same directory as run.py")
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create argument parser for the native launcher."""
    parser = argparse.ArgumentParser(
        description="SIP LIMS Workflow Manager Native Launcher\n\n"
                   "Cross-platform launcher for the native Python workflow manager.\n"
                   "Replaces Docker-based execution with direct Python execution.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('workflow_type', nargs='?', default='sip',
                       help='Workflow type: sip (default) or sps')
    parser.add_argument('project_path', nargs='?', default=None,
                       help='Path to project directory (default: current directory)')
    parser.add_argument('scripts_path', nargs='?', default=None,
                       help='Path to scripts directory (optional)')
    parser.add_argument('--mode', choices=['production', 'development'], default='production',
                       help='Execution mode (default: production)')
    parser.add_argument('--updates', action='store_true',
                       help='Perform core updates (repository, scripts) and terminate with restart instructions')
    parser.add_argument('--version', action='version', version='2.0.0-native')
    
    return parser


# Click interface (if available)
if HAS_CLICK:
    @click.command()
    @click.argument('workflow_type', default='sip', 
                   type=click.Choice(['sip', 'sps', 'sip-lims', 'sps-ce', 'spsceq'], case_sensitive=False))
    @click.argument('project_path', default=None, required=False,
                   type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
    @click.argument('scripts_path', default=None, required=False,
                   type=click.Path(exists=True, file_okay=False, dir_okay=True))
    @click.option('--mode', type=click.Choice(['production', 'development']), default='production',
                  help='Execution mode (auto-detected if not provided)')
    @click.option('--updates', is_flag=True, 
                  help='Perform core updates (repository, scripts) and terminate with restart instructions')
    @click.version_option(version="2.0.0-native", prog_name="SIP LIMS Workflow Manager Native Launcher")
    def main(workflow_type, project_path, scripts_path, mode, updates):
        """
        SIP LIMS Workflow Manager Native Launcher
        
        Cross-platform launcher for the native Python workflow manager.
        Replaces Docker-based execution with direct Python execution.
        """
        try:
            # Validate and normalize inputs
            workflow_type = validate_workflow_type(workflow_type)
            project_path = validate_project_path(str(project_path) if project_path else None)
            
            # Launch the Streamlit workflow manager
            launch_streamlit_app(
                workflow_type=workflow_type,
                project_path=project_path,
                scripts_path=str(scripts_path) if scripts_path else None,
                mode=mode,
                perform_core_updates=updates
            )
            
        except KeyboardInterrupt:
            click.echo()
            click.secho("❌ Launch cancelled by user", fg='red')
            sys.exit(1)
        except Exception as e:
            click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
            sys.exit(1)

else:
    # Fallback main function for systems without Click
    def main():
        """
        SIP LIMS Workflow Manager Native Launcher (Fallback Mode)
        
        Cross-platform launcher for the native Python workflow manager.
        Replaces Docker-based execution with direct Python execution.
        """
        parser = create_argument_parser()
        args = parser.parse_args()
        
        try:
            # Validate and normalize inputs
            workflow_type = validate_workflow_type(args.workflow_type)
            project_path = validate_project_path(args.project_path)
            
            # Launch the Streamlit workflow manager
            launch_streamlit_app(
                workflow_type=workflow_type,
                project_path=project_path,
                scripts_path=args.scripts_path,
                mode=args.mode,
                perform_core_updates=args.updates
            )
            
        except KeyboardInterrupt:
            print("\n❌ Launch cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()