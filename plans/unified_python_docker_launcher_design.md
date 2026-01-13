# Unified Python Docker Launcher Design

## Executive Summary

**RECOMMENDATION: Replace platform-specific scripts with a unified Python Docker launcher**

Based on comprehensive analysis of [`run.mac.command`](../run.mac.command) and [`run.windows.bat`](../run.windows.bat), the core functionality is **Docker container orchestration** - setting up environment variables, mounting volumes, and launching a prebuilt Docker image. This is perfectly suited for a unified Python implementation that eliminates Windows batch limitations while leveraging existing Python infrastructure.

## Architecture Overview

### Core Design Principles

1. **Single Responsibility**: Focus only on Docker container setup and launch
2. **Platform Agnostic**: Use Python's cross-platform capabilities
3. **Leverage Existing Code**: Reuse [`utils/branch_utils.py`](../utils/branch_utils.py), [`src/update_detector.py`](../src/update_detector.py), [`src/scripts_updater.py`](../src/scripts_updater.py)
4. **User-Friendly**: Rich CLI interface with clear error messages
5. **Maintainable**: Single codebase instead of dual bash/batch implementations

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Unified Python Launcher                     │
├─────────────────────────────────────────────────────────────┤
│  launcher.py (Single entry point for all platforms)        │
│  ├── CLI Interface (Click-based)                           │
│  ├── Platform Detection & Adaptation                       │
│  ├── Docker Container Orchestration                        │
│  └── User Interaction Management                           │
├─────────────────────────────────────────────────────────────┤
│                 Existing Infrastructure                     │
│  ├── utils/branch_utils.py (Branch detection)              │
│  ├── src/update_detector.py (Docker image updates)         │
│  ├── src/scripts_updater.py (Script repository updates)    │
│  └── docker-compose.yml (Container configuration)          │
├─────────────────────────────────────────────────────────────┤
│                 Platform Adapters                          │
│  ├── Windows: User ID mapping, path handling               │
│  ├── macOS: User ID detection, Docker for Mac             │
│  └── Linux: Permissions, Docker engine compatibility       │
├─────────────────────────────────────────────────────────────┤
│                 Entry Point Wrappers                       │
│  ├── launcher.py (Main Python script)                      │
│  ├── run.bat (Windows: python launcher.py %*)             │
│  ├── run.command (macOS: python3 launcher.py "$@")        │
│  └── run.sh (Linux: python3 launcher.py "$@")             │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Main Launcher Class

```python
#!/usr/bin/env python3
"""
Unified Docker Launcher for SIP LIMS Workflow Manager
Cross-platform replacement for run.mac.command and run.windows.bat
"""

import click
import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

# Import existing infrastructure
from utils.branch_utils import (
    get_current_branch, get_docker_tag_for_current_branch,
    get_local_image_name_for_current_branch, get_remote_image_name_for_current_branch
)
from src.update_detector import UpdateDetector
from src.scripts_updater import ScriptsUpdater
from src.fatal_sync_checker import main as check_fatal_sync

class DockerLauncher:
    """Unified Docker container launcher for all platforms."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.project_root = Path(__file__).parent
        self.update_detector = UpdateDetector()
        
    def launch(self):
        """Main launcher workflow."""
        try:
            # 1. Environment validation
            self.validate_environment()
            
            # 2. Branch detection and Docker image setup
            self.setup_branch_info()
            
            # 3. Container cleanup
            self.cleanup_existing_containers()
            
            # 4. User interactions
            workflow_type = self.select_workflow_type()
            mode_config = self.handle_mode_selection()
            project_path = self.select_project_path()
            
            # 5. Update management
            self.perform_updates(workflow_type, mode_config)
            
            # 6. Launch Docker container
            self.launch_container(project_path, workflow_type, mode_config)
            
        except KeyboardInterrupt:
            click.echo("\n❌ Launch cancelled by user")
            sys.exit(1)
        except Exception as e:
            click.secho(f"❌ ERROR: {e}", fg='red', bold=True)
            sys.exit(1)
```

### 2. Platform Adaptation Layer

```python
class PlatformAdapter:
    """Platform-specific adaptations for cross-platform compatibility."""
    
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
        
        return Path(cleaned).resolve()
    
    @staticmethod
    def get_docker_compose_command() -> list:
        """Get the appropriate docker-compose command for the platform."""
        # Try docker compose (newer) first, then docker-compose (legacy)
        for cmd in [["docker", "compose"], ["docker-compose"]]:
            try:
                subprocess.run(cmd + ["--version"], capture_output=True, check=True)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        raise RuntimeError("Neither 'docker compose' nor 'docker-compose' found")
```

### 3. User Interface Layer

```python
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
    def confirm_action(message: str, default: bool = False) -> bool:
        """Confirmation prompt with styling."""
        return click.confirm(
            click.style(message, fg='yellow', bold=True),
            default=default
        )
    
    @staticmethod
    def show_progress(items, label: str):
        """Show progress bar for long operations."""
        with click.progressbar(items, label=label) as bar:
            for item in bar:
                yield item
```

### 4. Docker Container Management

```python
class ContainerManager:
    """Docker container lifecycle management."""
    
    def __init__(self, launcher: 'DockerLauncher'):
        self.launcher = launcher
        self.compose_cmd = PlatformAdapter.get_docker_compose_command()
    
    def cleanup_existing_containers(self):
        """Stop and remove existing workflow manager containers."""
        click.echo("🛑 Checking for running workflow manager containers...")
        
        try:
            # Find containers using workflow manager images
            result = subprocess.run([
                "docker", "ps", "-a",
                "--filter", f"ancestor={self.launcher.remote_image_name}",
                "--filter", f"ancestor={self.launcher.local_image_name}",
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
                cwd=self.launcher.project_root,
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
```

### 5. Update Management Integration

```python
class UpdateManager:
    """Integrate existing update detection and management."""
    
    def __init__(self, launcher: 'DockerLauncher'):
        self.launcher = launcher
        self.update_detector = launcher.update_detector
    
    def perform_updates(self, workflow_type: str, mode_config: dict):
        """Perform all necessary updates before container launch."""
        if mode_config["app_env"] == "production":
            self.production_auto_update(workflow_type, mode_config)
        else:
            click.secho("🔧 Development mode - skipping auto-updates", fg='blue')
    
    def production_auto_update(self, workflow_type: str, mode_config: dict):
        """Production mode automatic updates."""
        click.secho("🏭 Production mode - performing automatic updates...", fg='blue', bold=True)
        
        # 1. Fatal sync error check
        self.check_fatal_sync_errors()
        
        # 2. Workflow manager repository updates
        self.check_repository_updates()
        
        # 3. Docker image updates
        self.check_docker_updates()
        
        # 4. Scripts updates
        self.check_scripts_updates(workflow_type, mode_config["scripts_path"])
    
    def check_fatal_sync_errors(self):
        """Check for fatal repository/Docker sync errors."""
        click.echo("🔍 Checking for fatal repository/Docker sync errors...")
        try:
            check_fatal_sync()
            click.secho("✅ No fatal sync errors detected", fg='green')
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError("💥 FATAL SYNC ERROR DETECTED - STOPPING EXECUTION")
    
    def check_docker_updates(self):
        """Check and handle Docker image updates."""
        click.echo("🔍 Checking for Docker image updates...")
        
        try:
            result = self.update_detector.check_docker_update(
                tag=self.launcher.current_branch,
                branch=self.launcher.current_branch
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
            # Get current image ID for cleanup
            result = subprocess.run([
                "docker", "images", self.launcher.remote_image_name,
                "--format", "{{.ID}}"
            ], capture_output=True, text=True)
            
            old_image_id = result.stdout.strip() if result.returncode == 0 else None
            
            # Clean up old image before pulling new one
            if old_image_id:
                click.echo("🧹 Removing old Docker image before update...")
                subprocess.run(["docker", "rmi", self.launcher.remote_image_name], 
                             capture_output=True, check=False)
                subprocess.run(["docker", "image", "prune", "-f"], 
                             capture_output=True, check=False)
                click.secho("✅ Old Docker image cleaned up", fg='green')
            
            # Pull new image
            click.echo(f"📥 Pulling Docker image for branch: {self.launcher.current_branch}...")
            subprocess.run(["docker", "pull", self.launcher.remote_image_name], check=True)
            click.secho("✅ Docker image updated successfully", fg='green')
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker image update failed: {e}")
```

## Entry Point Strategy

### 1. Main Python Script

```python
#!/usr/bin/env python3
"""
launcher.py - Unified Docker Launcher Entry Point
"""

@click.command()
@click.option('--workflow-type', type=click.Choice(['sip', 'sps-ce']), 
              help='Workflow type (will prompt if not provided)')
@click.option('--project-path', type=click.Path(exists=True, file_okay=False),
              help='Project folder path (will prompt if not provided)')
@click.option('--scripts-path', type=click.Path(exists=True, file_okay=False),
              help='Scripts folder path (for development mode)')
@click.option('--mode', type=click.Choice(['production', 'development']),
              help='Execution mode (auto-detected if not provided)')
@click.option('--no-updates', is_flag=True, help='Skip update checks')
@click.version_option()
def main(workflow_type, project_path, scripts_path, mode, no_updates):
    """
    SIP LIMS Workflow Manager Docker Launcher
    
    Cross-platform launcher for the containerized workflow manager.
    Replaces run.mac.command and run.windows.bat with unified Python implementation.
    """
    try:
        launcher = DockerLauncher()
        
        # Override defaults with CLI arguments if provided
        if workflow_type:
            launcher.workflow_type = workflow_type
        if project_path:
            launcher.project_path = Path(project_path)
        if scripts_path:
            launcher.scripts_path = Path(scripts_path)
        if mode:
            launcher.mode = mode
        if no_updates:
            launcher.skip_updates = True
        
        launcher.launch()
        
    except KeyboardInterrupt:
        click.echo("\n❌ Launch cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ FATAL ERROR: {e}", fg='red', bold=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Platform-Specific Wrappers

**Windows (`run.bat`)**:
```batch
@echo off
python launcher.py %*
```

**macOS (`run.command`)**:
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 launcher.py "$@"
```

**Linux (`run.sh`)**:
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 launcher.py "$@"
```

## Implementation Benefits

### 1. Eliminates Windows Batch Problems

- ✅ **No Variable Scoping Issues**: Python variables work consistently
- ✅ **Robust Error Handling**: Python exceptions vs batch error codes
- ✅ **Native JSON Processing**: No fragile parsing with external calls
- ✅ **Consistent String Operations**: Python string methods work reliably
- ✅ **Cross-Platform Path Handling**: `pathlib` handles all platforms

### 2. Leverages Existing Infrastructure

- ✅ **Reuses [`utils/branch_utils.py`](../utils/branch_utils.py)**: No duplication
- ✅ **Integrates [`src/update_detector.py`](../src/update_detector.py)**: Existing update logic
- ✅ **Uses [`src/scripts_updater.py`](../src/scripts_updater.py)**: Script management
- ✅ **Maintains [`docker-compose.yml`](../docker-compose.yml)**: No container changes

### 3. Improves User Experience

- ✅ **Rich CLI Interface**: Click provides excellent user interaction
- ✅ **Better Error Messages**: Clear, actionable error reporting
- ✅ **Progress Indicators**: Visual feedback for long operations
- ✅ **Consistent Behavior**: Same experience across all platforms
- ✅ **Command Line Options**: Advanced users can skip prompts

### 4. Simplifies Maintenance

- ✅ **Single Codebase**: One script instead of bash + batch
- ✅ **Easier Testing**: Python unit tests vs platform-specific testing
- ✅ **Better Documentation**: Python docstrings and type hints
- ✅ **Version Control**: Single file to track changes

## Migration Strategy

### Phase 1: Development and Testing
1. Implement core `launcher.py` with all functionality
2. Create platform-specific wrapper scripts
3. Test on all platforms (Windows, macOS, Linux)
4. Validate feature parity with existing scripts

### Phase 2: Parallel Deployment
1. Deploy alongside existing scripts as `launcher.py`
2. Update documentation with new usage instructions
3. Gather user feedback and iterate
4. Fix any platform-specific issues

### Phase 3: Migration and Cleanup
1. Update default instructions to use `launcher.py`
2. Keep old scripts as backup during transition period
3. Remove old scripts after successful migration
4. Update all documentation and guides

## Risk Assessment and Mitigation

### Low Risk Items
- ✅ **Python Availability**: Already required by the project
- ✅ **Docker Integration**: Uses same docker-compose approach
- ✅ **Existing Infrastructure**: Leverages proven Python modules
- ✅ **User Interface**: Click is mature and well-tested

### Medium Risk Items
- ⚠️ **Platform-Specific Paths**: Mitigated by `pathlib` and testing
- ⚠️ **User Adoption**: Mitigated by parallel deployment and documentation
- ⚠️ **Edge Cases**: Mitigated by comprehensive testing

### Mitigation Strategies
1. **Comprehensive Testing**: Test on all target platforms
2. **Gradual Migration**: Keep existing scripts during transition
3. **Clear Documentation**: Provide migration guide and troubleshooting
4. **Fallback Plan**: Existing scripts remain available as backup

## Conclusion

**The unified Python Docker launcher is a superior solution that eliminates all Windows batch limitations while providing a better user experience across all platforms.** 

Key advantages:
- **Eliminates Windows batch architectural problems**
- **Leverages existing Python infrastructure**
- **Provides consistent cross-platform experience**
- **Simplifies maintenance and testing**
- **Improves error handling and user feedback**

**Recommendation**: Proceed with implementation of the unified Python launcher to replace both [`run.mac.command`](../run.mac.command) and [`run.windows.bat`](../run.windows.bat) with a single, robust, cross-platform solution.