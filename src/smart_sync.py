"""
Smart Sync Manager for Windows Network Drive Support

This module provides transparent sync functionality to solve Windows Docker
network drive permission issues. It automatically detects Windows + network
drive scenarios and creates a local staging environment for Docker operations.

Key Features:
- Automatic Windows network drive detection
- Bidirectional sync (network ↔ local)
- Hidden file preservation (.snapshots/, .workflow_status/, etc.)
- Error resilience with graceful fallback
- Performance optimization with incremental sync
- Comprehensive debug logging and performance monitoring
"""

import os
import platform
import shutil
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import tempfile
import subprocess
from datetime import datetime

try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False
    # Fallback for environments without click
    class click:
        @staticmethod
        def echo(message="", **kwargs):
            print(message)
        
        @staticmethod
        def secho(message, fg=None, bold=False, **kwargs):
            print(message)

# Import debug logging
from .debug_logger import (
    debug_context, log_smart_sync_detection, log_sync_operation,
    log_file_operation, log_error, log_info, log_warning,
    debug_enabled, get_debug_logger
)


class SmartSyncManager:
    """
    Manages transparent sync between network drives and local staging for Docker compatibility.
    
    This class handles the complete sync lifecycle:
    1. Initial full sync from network to local
    2. Incremental bidirectional sync during workflow execution
    3. Final sync back to network on completion
    4. Error handling and recovery
    """
    
    def __init__(self, network_path: Path, local_path: Path):
        """
        Initialize Smart Sync Manager.
        
        Args:
            network_path: Original project path on network drive (e.g., Z:\project)
            local_path: Local staging path (e.g., C:\temp\sip_workflow\project)
        """
        self.network_path = Path(network_path)
        self.local_path = Path(local_path)
        self.sync_log_file = self.local_path / ".sync_log.json"
        self.ignore_patterns = self._get_ignore_patterns()
        
        # Performance tracking
        self.last_sync_time = None
        self.sync_stats = {
            "files_synced": 0,
            "total_sync_time": 0,
            "last_sync_duration": 0
        }
        
        # Debug logging
        if debug_enabled():
            log_info("SmartSyncManager initialized",
                    network_path=str(self.network_path),
                    local_path=str(self.local_path),
                    ignore_patterns=list(self.ignore_patterns))
        
        # Ensure local staging directory exists
        self.local_path.mkdir(parents=True, exist_ok=True)
    
    def _get_ignore_patterns(self) -> Set[str]:
        """
        Get patterns for files/directories to ignore during sync.
        
        Returns:
            Set of patterns to ignore
        """
        return {
            "__pycache__",
            ".DS_Store", 
            "Thumbs.db",
            ".sync_log.json",
            "*.tmp",
            "*.temp",
            ".git",  # Git repositories should not be synced
            "node_modules",  # Large dependency directories
            ".vscode",  # Editor-specific files
            ".idea"  # IDE-specific files
        }
    
    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a file or directory should be ignored during sync.
        
        Args:
            path: Path to check
            
        Returns:
            True if path should be ignored
        """
        name = path.name
        
        # Check exact matches
        if name in self.ignore_patterns:
            return True
        
        # Check pattern matches
        for pattern in self.ignore_patterns:
            if pattern.startswith("*") and name.endswith(pattern[1:]):
                return True
        
        return False
    
    def _log_sync_operation(self, operation: str, details: Dict):
        """
        Log sync operation for debugging and recovery.
        
        Args:
            operation: Type of sync operation
            details: Operation details
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "details": details
            }
            
            # Read existing log
            log_data = []
            if self.sync_log_file.exists():
                try:
                    with open(self.sync_log_file, 'r') as f:
                        log_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    log_data = []
            
            # Append new entry
            log_data.append(log_entry)
            
            # Keep only last 100 entries to prevent log bloat
            if len(log_data) > 100:
                log_data = log_data[-100:]
            
            # Write back to file
            with open(self.sync_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            # Don't let logging errors break sync operations
            if HAS_CLICK:
                click.secho(f"⚠️  Warning: Could not log sync operation: {e}", fg='yellow')
    
    def _detect_changes(self, source_path: Path, dest_path: Path) -> List[Tuple[Path, Path, str]]:
        """
        Detect files that need to be synced between source and destination.
        
        Args:
            source_path: Source directory
            dest_path: Destination directory
            
        Returns:
            List of (source_file, dest_file, action) tuples
            Actions: 'copy' (new/modified), 'delete' (removed from source)
        """
        changes = []
        
        if not source_path.exists():
            return changes
        
        # Build file maps for comparison
        source_files = {}
        dest_files = {}
        
        # Scan source directory
        try:
            for item in source_path.rglob("*"):
                if self._should_ignore(item):
                    continue
                
                if item.is_file():
                    rel_path = item.relative_to(source_path)
                    source_files[rel_path] = {
                        'path': item,
                        'mtime': item.stat().st_mtime,
                        'size': item.stat().st_size
                    }
        except (OSError, PermissionError) as e:
            if HAS_CLICK:
                click.secho(f"⚠️  Warning: Could not scan source directory: {e}", fg='yellow')
            return changes
        
        # Scan destination directory
        if dest_path.exists():
            try:
                for item in dest_path.rglob("*"):
                    if self._should_ignore(item):
                        continue
                    
                    if item.is_file():
                        rel_path = item.relative_to(dest_path)
                        dest_files[rel_path] = {
                            'path': item,
                            'mtime': item.stat().st_mtime,
                            'size': item.stat().st_size
                        }
            except (OSError, PermissionError) as e:
                if HAS_CLICK:
                    click.secho(f"⚠️  Warning: Could not scan destination directory: {e}", fg='yellow')
        
        # Find files to copy (new or modified)
        for rel_path, source_info in source_files.items():
            dest_file = dest_path / rel_path
            
            if rel_path not in dest_files:
                # New file
                changes.append((source_info['path'], dest_file, 'copy'))
            else:
                # Check if modified
                dest_info = dest_files[rel_path]
                if (source_info['mtime'] > dest_info['mtime'] or 
                    source_info['size'] != dest_info['size']):
                    changes.append((source_info['path'], dest_file, 'copy'))
        
        # Find files to delete (removed from source)
        for rel_path, dest_info in dest_files.items():
            if rel_path not in source_files:
                changes.append((None, dest_info['path'], 'delete'))
        
        return changes
    
    def _copy_file_with_metadata(self, source: Path, dest: Path) -> bool:
        """
        Copy file preserving metadata (timestamps, permissions).
        
        Args:
            source: Source file path
            dest: Destination file path
            
        Returns:
            True if copy successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file with metadata preservation
            shutil.copy2(source, dest)
            return True
            
        except (OSError, PermissionError, shutil.Error) as e:
            if HAS_CLICK:
                click.secho(f"⚠️  Warning: Could not copy {source} to {dest}: {e}", fg='yellow')
            return False
    
    def _delete_file_safe(self, file_path: Path) -> bool:
        """
        Safely delete a file.
        
        Args:
            file_path: File to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
            return True
            
        except (OSError, PermissionError) as e:
            if HAS_CLICK:
                click.secho(f"⚠️  Warning: Could not delete {file_path}: {e}", fg='yellow')
            return False
    
    def initial_sync(self) -> bool:
        """
        Perform initial full sync from network to local staging.
        
        Returns:
            True if sync successful, False otherwise
        """
        with debug_context("initial_sync",
                          network_path=str(self.network_path),
                          local_path=str(self.local_path)) as debug_logger:
            
            start_time = time.time()
            
            if HAS_CLICK:
                click.echo("📥 Starting initial sync from network to local staging...")
            
            if debug_logger:
                debug_logger.info("Starting initial sync",
                                network_path=str(self.network_path),
                                local_path=str(self.local_path))
            
            try:
                # Detect all changes (full copy)
                if debug_logger:
                    debug_logger.debug("Detecting changes for initial sync")
                
                changes = self._detect_changes(self.network_path, self.local_path)
                
                if debug_logger:
                    debug_logger.info(f"Detected {len(changes)} changes for initial sync",
                                    total_changes=len(changes))
                
                if not changes:
                    if HAS_CLICK:
                        click.secho("✅ No files to sync - local staging is up to date", fg='green')
                    
                    log_sync_operation("initial_sync", "network_to_local", 0,
                                     time.time() - start_time, True)
                    return True
                
                # Perform sync operations
                files_copied = 0
                files_deleted = 0
                failed_operations = 0
                
                for source, dest, action in changes:
                    if action == 'copy':
                        success = self._copy_file_with_metadata(source, dest)
                        if success:
                            files_copied += 1
                        else:
                            failed_operations += 1
                        
                        if debug_logger:
                            log_file_operation("copy", source, dest, success)
                            
                    elif action == 'delete':
                        success = self._delete_file_safe(dest)
                        if success:
                            files_deleted += 1
                        else:
                            failed_operations += 1
                        
                        if debug_logger:
                            log_file_operation("delete", dest, dest, success)
                
                # Update stats
                duration = time.time() - start_time
                self.sync_stats.update({
                    "files_synced": files_copied + files_deleted,
                    "total_sync_time": self.sync_stats["total_sync_time"] + duration,
                    "last_sync_duration": duration
                })
                self.last_sync_time = time.time()
                
                # Log operation
                self._log_sync_operation("initial_sync", {
                    "files_copied": files_copied,
                    "files_deleted": files_deleted,
                    "failed_operations": failed_operations,
                    "duration_seconds": duration,
                    "network_path": str(self.network_path),
                    "local_path": str(self.local_path)
                })
                
                # Debug logging
                log_sync_operation("initial_sync", "network_to_local",
                                 files_copied + files_deleted, duration, True,
                                 files_copied=files_copied, files_deleted=files_deleted,
                                 failed_operations=failed_operations)
                
                if HAS_CLICK:
                    click.secho(f"✅ Initial sync completed: {files_copied} files copied, {files_deleted} files removed ({duration:.1f}s)", fg='green')
                
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                
                if HAS_CLICK:
                    click.secho(f"❌ Initial sync failed: {e}", fg='red')
                
                self._log_sync_operation("initial_sync_error", {
                    "error": str(e),
                    "duration_seconds": duration,
                    "network_path": str(self.network_path),
                    "local_path": str(self.local_path)
                })
                
                # Debug logging
                log_error("Initial sync failed", error=str(e), duration=duration,
                         network_path=str(self.network_path), local_path=str(self.local_path))
                
                log_sync_operation("initial_sync", "network_to_local", 0, duration, False,
                                 error=str(e))
                
                return False
    
    def incremental_sync_down(self) -> bool:
        """
        Perform incremental sync from network to local (before workflow steps).
        
        Returns:
            True if sync successful, False otherwise
        """
        with debug_context("incremental_sync_down",
                          network_path=str(self.network_path),
                          local_path=str(self.local_path)) as debug_logger:
            
            start_time = time.time()
            
            if HAS_CLICK:
                click.echo("📥 Syncing latest changes from network drive...")
            
            if debug_logger:
                debug_logger.info("Starting incremental sync down (network -> local)")
            
            try:
                changes = self._detect_changes(self.network_path, self.local_path)
                
                if debug_logger:
                    debug_logger.debug(f"Detected {len(changes)} changes for incremental sync down",
                                     total_changes=len(changes))
                
                if not changes:
                    if HAS_CLICK:
                        click.secho("✅ Local staging is up to date", fg='green')
                    
                    log_sync_operation("incremental_sync_down", "network_to_local", 0,
                                     time.time() - start_time, True)
                    return True
                
                # Perform sync operations
                files_copied = 0
                files_deleted = 0
                failed_operations = 0
                
                for source, dest, action in changes:
                    if action == 'copy':
                        success = self._copy_file_with_metadata(source, dest)
                        if success:
                            files_copied += 1
                        else:
                            failed_operations += 1
                        log_file_operation("copy", source, dest, success)
                        
                    elif action == 'delete':
                        success = self._delete_file_safe(dest)
                        if success:
                            files_deleted += 1
                        else:
                            failed_operations += 1
                        log_file_operation("delete", dest, dest, success)
                
                # Update stats
                duration = time.time() - start_time
                self.sync_stats.update({
                    "files_synced": self.sync_stats["files_synced"] + files_copied + files_deleted,
                    "total_sync_time": self.sync_stats["total_sync_time"] + duration,
                    "last_sync_duration": duration
                })
                self.last_sync_time = time.time()
                
                # Log operation
                self._log_sync_operation("incremental_sync_down", {
                    "files_copied": files_copied,
                    "files_deleted": files_deleted,
                    "failed_operations": failed_operations,
                    "duration_seconds": duration
                })
                
                # Debug logging
                log_sync_operation("incremental_sync_down", "network_to_local",
                                 files_copied + files_deleted, duration, True,
                                 files_copied=files_copied, files_deleted=files_deleted,
                                 failed_operations=failed_operations)
                
                if HAS_CLICK:
                    click.secho(f"✅ Incremental sync completed: {files_copied} files updated, {files_deleted} files removed ({duration:.1f}s)", fg='green')
                
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                
                if HAS_CLICK:
                    click.secho(f"⚠️  Warning: Incremental sync from network failed: {e}", fg='yellow')
                
                self._log_sync_operation("incremental_sync_down_error", {
                    "error": str(e),
                    "duration_seconds": duration
                })
                
                # Debug logging
                log_error("Incremental sync down failed", error=str(e), duration=duration)
                log_sync_operation("incremental_sync_down", "network_to_local", 0, duration, False,
                                 error=str(e))
                
                return False
    
    def incremental_sync_up(self) -> bool:
        """
        Perform incremental sync from local to network (after workflow steps).
        
        Returns:
            True if sync successful, False otherwise
        """
        with debug_context("incremental_sync_up",
                          network_path=str(self.network_path),
                          local_path=str(self.local_path)) as debug_logger:
            
            start_time = time.time()
            
            if HAS_CLICK:
                click.echo("📤 Syncing changes back to network drive...")
            
            if debug_logger:
                debug_logger.info("Starting incremental sync up (local -> network)")
            
            try:
                changes = self._detect_changes(self.local_path, self.network_path)
                
                if debug_logger:
                    debug_logger.debug(f"Detected {len(changes)} changes for incremental sync up",
                                     total_changes=len(changes))
                
                if not changes:
                    if HAS_CLICK:
                        click.secho("✅ Network drive is up to date", fg='green')
                    
                    log_sync_operation("incremental_sync_up", "local_to_network", 0,
                                     time.time() - start_time, True)
                    return True
                
                # Perform sync operations
                files_copied = 0
                files_deleted = 0
                failed_operations = 0
                
                for source, dest, action in changes:
                    if action == 'copy':
                        success = self._copy_file_with_metadata(source, dest)
                        if success:
                            files_copied += 1
                        else:
                            failed_operations += 1
                        log_file_operation("copy", source, dest, success)
                        
                    elif action == 'delete':
                        success = self._delete_file_safe(dest)
                        if success:
                            files_deleted += 1
                        else:
                            failed_operations += 1
                        log_file_operation("delete", dest, dest, success)
                
                # Update stats
                duration = time.time() - start_time
                self.sync_stats.update({
                    "files_synced": self.sync_stats["files_synced"] + files_copied + files_deleted,
                    "total_sync_time": self.sync_stats["total_sync_time"] + duration,
                    "last_sync_duration": duration
                })
                self.last_sync_time = time.time()
                
                # Log operation
                self._log_sync_operation("incremental_sync_up", {
                    "files_copied": files_copied,
                    "files_deleted": files_deleted,
                    "failed_operations": failed_operations,
                    "duration_seconds": duration
                })
                
                # Debug logging
                log_sync_operation("incremental_sync_up", "local_to_network",
                                 files_copied + files_deleted, duration, True,
                                 files_copied=files_copied, files_deleted=files_deleted,
                                 failed_operations=failed_operations)
                
                if HAS_CLICK:
                    click.secho(f"✅ Changes synced to network: {files_copied} files updated, {files_deleted} files removed ({duration:.1f}s)", fg='green')
                
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                
                if HAS_CLICK:
                    click.secho(f"⚠️  Warning: Sync to network drive failed: {e}", fg='red')
                
                self._log_sync_operation("incremental_sync_up_error", {
                    "error": str(e),
                    "duration_seconds": duration
                })
                
                # Debug logging
                log_error("Incremental sync up failed", error=str(e), duration=duration)
                log_sync_operation("incremental_sync_up", "local_to_network", 0, duration, False,
                                 error=str(e))
                
                return False
    
    def final_sync(self) -> bool:
        """
        Perform final sync from local to network on workflow completion.
        
        Returns:
            True if sync successful, False otherwise
        """
        if HAS_CLICK:
            click.echo("📤 Performing final sync to network drive...")
        
        # Final sync is same as incremental sync up, but with different messaging
        success = self.incremental_sync_up()
        
        if success:
            if HAS_CLICK:
                click.secho("✅ Final sync completed - all changes saved to network drive", fg='green')
        else:
            if HAS_CLICK:
                click.secho("❌ Final sync failed - some changes may not be saved to network drive", fg='red')
        
        return success
    
    def cleanup(self):
        """
        Clean up local staging directory and sync logs.
        """
        try:
            if self.local_path.exists():
                if HAS_CLICK:
                    click.echo("🧹 Cleaning up local staging directory...")
                shutil.rmtree(self.local_path)
                if HAS_CLICK:
                    click.secho("✅ Local staging cleaned up", fg='green')
        except Exception as e:
            if HAS_CLICK:
                click.secho(f"⚠️  Warning: Could not clean up staging directory: {e}", fg='yellow')
    
    def get_sync_stats(self) -> Dict:
        """
        Get sync performance statistics.
        
        Returns:
            Dictionary with sync statistics
        """
        return {
            **self.sync_stats,
            "network_path": str(self.network_path),
            "local_path": str(self.local_path),
            "last_sync_time": self.last_sync_time
        }


def detect_smart_sync_scenario(project_path: Path) -> bool:
    """
    Detect if Smart Sync is needed (Windows + network drive scenario).
    
    Args:
        project_path: Project path to check
        
    Returns:
        True if Smart Sync should be enabled
    """
    platform_name = platform.system()
    
    # Only enable on Windows
    if platform_name != "Windows":
        log_smart_sync_detection(project_path, False,
                                platform=platform_name,
                                reason="Non-Windows platform")
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
                detection_reason = f"Network drive detected: {drive_letter}:"
            else:
                detection_reason = f"Local drive detected: {drive_letter}:"
        
        # Check for UNC paths (should have been converted to mapped drives by PlatformAdapter)
        elif path_str.startswith(('\\\\', '//')):
            detected = True
            detection_reason = "UNC path detected"
        else:
            detection_reason = "No network drive pattern detected"
        
        log_smart_sync_detection(project_path, detected,
                                platform=platform_name,
                                reason=detection_reason, path_str=path_str)
        
        return detected
        
    except Exception as e:
        # If we can't determine the path type, assume no Smart Sync needed
        log_smart_sync_detection(project_path, False,
                                platform=platform_name,
                                reason="Exception during detection", error=str(e))
        return False


def setup_smart_sync_environment(network_path: Path) -> Dict[str, str]:
    """
    Set up Smart Sync environment and perform initial sync.
    
    Args:
        network_path: Original project path on network drive
        
    Returns:
        Dictionary with environment variables for Docker
    """
    with debug_context("setup_smart_sync_environment",
                      network_path=str(network_path)) as debug_logger:
        
        try:
            # Create local staging directory
            project_name = network_path.name
            staging_base = Path(tempfile.gettempdir()) / "sip_workflow"
            local_path = staging_base / project_name
            
            if HAS_CLICK:
                click.echo(f"🔄 Setting up Smart Sync environment...")
                click.echo(f"   Network path: {network_path}")
                click.echo(f"   Local staging: {local_path}")
            
            if debug_logger:
                debug_logger.info("Setting up Smart Sync environment",
                                network_path=str(network_path),
                                local_path=str(local_path),
                                project_name=project_name)
            
            # Initialize Smart Sync Manager
            sync_manager = SmartSyncManager(network_path, local_path)
            
            # Perform initial sync
            if not sync_manager.initial_sync():
                raise RuntimeError("Initial sync failed")
            
            # Return environment variables for Docker
            env_vars = {
                "SMART_SYNC_ENABLED": "true",
                "NETWORK_PROJECT_PATH": str(network_path),
                "LOCAL_PROJECT_PATH": str(local_path),
                "PROJECT_PATH": str(local_path)  # Docker will use local staging
            }
            
            # Debug logging for environment setup
            if debug_logger:
                debug_logger.info("Smart Sync environment setup completed successfully",
                                environment_variables=env_vars)
            
            log_info("Smart Sync environment setup completed",
                    network_path=str(network_path),
                    local_path=str(local_path),
                    environment_variables=env_vars)
            
            return env_vars
            
        except Exception as e:
            if HAS_CLICK:
                click.secho(f"❌ Failed to setup Smart Sync environment: {e}", fg='red')
            
            # Debug logging for setup failure
            log_error("Smart Sync environment setup failed",
                     error=str(e),
                     network_path=str(network_path))
            
            raise


def get_smart_sync_manager(network_path: str, local_path: str) -> SmartSyncManager:
    """
    Get a SmartSyncManager instance for use in sync scripts.
    
    Args:
        network_path: Network project path
        local_path: Local staging path
        
    Returns:
        SmartSyncManager instance
    """
    return SmartSyncManager(Path(network_path), Path(local_path))