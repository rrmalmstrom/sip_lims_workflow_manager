# 🚀 Smart Sync Implementation Plan

## 📋 Overview

This document provides detailed implementation instructions for the Smart Sync Layer solution to resolve Windows Docker network drive permission issues. The plan is structured for handoff to a coding agent.

---

## 🎯 Implementation Phases

### **Phase 1: Core Smart Sync Infrastructure**

#### **1.1 Create SmartSyncManager Class**

**File**: `src/smart_sync.py` (new file)

```python
import os
import json
import time
import shutil
import datetime
from pathlib import Path
from typing import List, Dict, Optional
import click

class SmartSyncManager:
    """Manages bidirectional sync between network and local drives for Windows Docker compatibility."""
    
    def __init__(self, network_path: str, local_path: str):
        self.network_path = Path(network_path)
        self.local_path = Path(local_path)
        self.sync_log = self.local_path / ".sync_log.json"
        
    def initial_sync(self) -> bool:
        """Perform initial full sync from network to local."""
        try:
            click.echo("📥 Initial sync: Network → Local...")
            start_time = time.time()
            
            # Ensure local directory exists
            self.local_path.mkdir(parents=True, exist_ok=True)
            
            # Full copy with hidden files
            self._copy_directory_contents(self.network_path, self.local_path)
            
            # Record sync metadata
            self._update_sync_log("initial_sync", "network_to_local")
            
            elapsed = time.time() - start_time
            click.echo(f"✅ Initial sync completed in {elapsed:.1f}s")
            return True
            
        except Exception as e:
            click.secho(f"❌ Initial sync failed: {e}", fg='red')
            return False
    
    def incremental_sync_down(self) -> bool:
        """Fast incremental sync from network to local."""
        try:
            changes = self._detect_changes(direction="down")
            if not changes:
                return False
                
            click.echo(f"📥 Syncing {len(changes)} changed files from network...")
            
            for file_path in changes:
                self._sync_file(file_path, "down")
            
            self._update_sync_log("incremental_sync", "network_to_local")
            return True
            
        except Exception as e:
            click.secho(f"⚠️ Incremental sync down failed: {e}", fg='yellow')
            return False
    
    def incremental_sync_up(self) -> bool:
        """Fast incremental sync from local to network."""
        try:
            changes = self._detect_changes(direction="up")
            if not changes:
                return False
                
            click.echo(f"📤 Syncing {len(changes)} changed files to network...")
            
            for file_path in changes:
                self._sync_file(file_path, "up")
            
            self._update_sync_log("incremental_sync", "local_to_network")
            return True
            
        except Exception as e:
            click.secho(f"⚠️ Incremental sync up failed: {e}", fg='yellow')
            return False
    
    def _copy_directory_contents(self, source: Path, target: Path):
        """Copy directory contents including hidden files."""
        for item in source.rglob('*'):
            if self._should_ignore(item):
                continue
                
            rel_path = item.relative_to(source)
            target_item = target / rel_path
            
            if item.is_dir():
                target_item.mkdir(parents=True, exist_ok=True)
            else:
                target_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_item)
    
    def _detect_changes(self, direction: str) -> List[Path]:
        """Detect changed files between network and local."""
        changes = []
        
        if direction == "down":
            source, target = self.network_path, self.local_path
        else:
            source, target = self.local_path, self.network_path
        
        # Compare all files including hidden ones
        for file_path in source.rglob('*'):
            if file_path.is_file() and not self._should_ignore(file_path):
                rel_path = file_path.relative_to(source)
                target_file = target / rel_path
                
                if not target_file.exists():
                    changes.append(rel_path)
                elif file_path.stat().st_mtime > target_file.stat().st_mtime:
                    changes.append(rel_path)
        
        return changes
    
    def _sync_file(self, rel_path: Path, direction: str):
        """Sync a single file in the specified direction."""
        if direction == "down":
            source_file = self.network_path / rel_path
            target_file = self.local_path / rel_path
        else:
            source_file = self.local_path / rel_path
            target_file = self.network_path / rel_path
        
        if source_file.exists():
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
        elif target_file.exists():
            target_file.unlink()
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored during sync."""
        ignore_patterns = {
            '__pycache__',
            '.DS_Store',
            'Thumbs.db',
            '.sync_log.json'
        }
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def _update_sync_log(self, operation: str, direction: str):
        """Update sync log with operation metadata."""
        log_data = {
            "last_sync": datetime.datetime.now().isoformat(),
            "operation": operation,
            "direction": direction,
            "network_path": str(self.network_path),
            "local_path": str(self.local_path)
        }
        
        try:
            with open(self.sync_log, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception:
            pass  # Don't fail sync if logging fails
```

#### **1.2 Modify run.py for Smart Sync Detection**

**File**: `run.py`

**Location**: After line 267 (end of PlatformAdapter class)

**Add new methods**:

```python
@staticmethod
def detect_smart_sync_scenario(project_path: Path) -> bool:
    """Detect if Smart Sync is needed for Windows network drives."""
    if platform.system() != "Windows":
        return False
    
    # Check if path is a mapped network drive (exclude C: local drive)
    path_str = str(project_path)
    if re.match(r'^[D-Z]:', path_str):
        return True
    
    return False

@staticmethod
def setup_smart_sync_environment(network_path: Path) -> Dict[str, str]:
    """Set up Smart Sync staging environment."""
    from src.smart_sync import SmartSyncManager
    
    project_name = network_path.name
    local_staging = Path(f"C:/temp/sip_workflow/{project_name}")
    
    # Create staging directory
    local_staging.mkdir(parents=True, exist_ok=True)
    
    # Perform initial full sync
    click.echo("🔄 Setting up Smart Sync for Windows network drive...")
    click.echo(f"   Network: {network_path}")
    click.echo(f"   Local:   {local_staging}")
    
    sync_manager = SmartSyncManager(str(network_path), str(local_staging))
    if not sync_manager.initial_sync():
        raise RuntimeError("Initial sync failed")
    
    return {
        "PROJECT_PATH": str(local_staging),  # Docker gets local path
        "NETWORK_PROJECT_PATH": str(network_path),  # For sync reference
        "LOCAL_PROJECT_PATH": str(local_staging),   # For sync reference
        "SMART_SYNC_ENABLED": "true"
    }
```

**Location**: Modify `launch_container` method around line 431

**Replace the existing method with**:

```python
def launch_container(self, project_path: Path, workflow_type: str, mode_config: dict):
    """Launch the Docker container using docker-compose with Smart Sync support."""
    click.echo()
    click.secho("🐳 Launching Docker container...", fg='blue', bold=True)
    
    # Check if Smart Sync is needed
    docker_project_path = project_path
    sync_env = {}
    
    if PlatformAdapter.detect_smart_sync_scenario(project_path):
        try:
            sync_env = PlatformAdapter.setup_smart_sync_environment(project_path)
            docker_project_path = Path(sync_env["PROJECT_PATH"])
        except Exception as e:
            click.secho(f"❌ Smart Sync setup failed: {e}", fg='red')
            click.echo("Falling back to direct network drive access (may fail on Windows)")
            sync_env = {"SMART_SYNC_ENABLED": "false"}
    else:
        sync_env = {"SMART_SYNC_ENABLED": "false"}
    
    # Prepare environment variables
    env = self.prepare_environment(docker_project_path, workflow_type, mode_config)
    env.update(sync_env)
    
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
        
        # Perform final sync if Smart Sync was enabled
        if sync_env.get("SMART_SYNC_ENABLED") == "true":
            click.echo("🔄 Performing final sync to network drive...")
            try:
                from src.smart_sync import SmartSyncManager
                sync_manager = SmartSyncManager(
                    sync_env["NETWORK_PROJECT_PATH"],
                    sync_env["LOCAL_PROJECT_PATH"]
                )
                sync_manager.incremental_sync_up()
                click.echo("✅ Final sync completed")
            except Exception as e:
                click.secho(f"⚠️ Final sync failed: {e}", fg='yellow')
    finally:
        click.echo("Application has been shut down.")
```

#### **1.3 Create Sync Scripts Directory**

**Directory**: `sync_scripts/` (new directory in project root)

**File**: `sync_scripts/pre_step_sync.py` (new file)

```python
#!/usr/bin/env python3
"""Pre-step sync script for Smart Sync."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, '/opt/app/src')

def main():
    if os.environ.get('SMART_SYNC_ENABLED') != 'true':
        sys.exit(0)
    
    try:
        from smart_sync import SmartSyncManager
        
        network_path = os.environ.get('NETWORK_PROJECT_PATH')
        local_path = os.environ.get('LOCAL_PROJECT_PATH')
        
        if not network_path or not local_path:
            print("Missing sync paths", file=sys.stderr)
            sys.exit(1)
        
        sync_manager = SmartSyncManager(network_path, local_path)
        if sync_manager.incremental_sync_down():
            print("Pre-step sync completed")
        else:
            print("No changes to sync")
            
    except Exception as e:
        print(f"Pre-step sync failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**File**: `sync_scripts/post_step_sync.py` (new file)

```python
#!/usr/bin/env python3
"""Post-step sync script for Smart Sync."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, '/opt/app/src')

def main():
    if os.environ.get('SMART_SYNC_ENABLED') != 'true':
        sys.exit(0)
    
    step_id = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    
    try:
        from smart_sync import SmartSyncManager
        
        network_path = os.environ.get('NETWORK_PROJECT_PATH')
        local_path = os.environ.get('LOCAL_PROJECT_PATH')
        
        if not network_path or not local_path:
            print("Missing sync paths", file=sys.stderr)
            sys.exit(1)
        
        sync_manager = SmartSyncManager(network_path, local_path)
        if sync_manager.incremental_sync_up():
            print(f"Step {step_id} synced to network")
        else:
            print(f"No changes to sync for step {step_id}")
            
    except Exception as e:
        print(f"Post-step sync failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### **Phase 2: Container Integration**

#### **2.1 Modify docker-compose.yml**

**File**: `docker-compose.yml`

**Location**: Add to volumes section around line 29

```yaml
      # Smart Sync scripts volume (conditionally mounted)
      - type: bind
        source: ${SYNC_SCRIPTS_PATH:-./sync_scripts}
        target: /opt/sync
        bind:
          create_host_path: true
```

**Location**: Add to environment section around line 36

```yaml
      - SMART_SYNC_ENABLED=${SMART_SYNC_ENABLED:-false}
      - NETWORK_PROJECT_PATH=${NETWORK_PROJECT_PATH:-}
      - LOCAL_PROJECT_PATH=${LOCAL_PROJECT_PATH:-}
```

#### **2.2 Modify core.py for Sync Integration**

**File**: `src/core.py`

**Location**: Add import at top of file (around line 4)

```python
import subprocess
import os
```

**Location**: Add method to Project class (around line 152, before `run_step`)

```python
def _trigger_pre_step_sync(self):
    """Trigger pre-step sync to get latest network changes."""
    if os.environ.get('SMART_SYNC_ENABLED') != 'true':
        return
        
    try:
        result = subprocess.run([
            'python3', '/opt/sync/pre_step_sync.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"📥 {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("⚠️ Pre-step sync timeout - continuing with local data")
    except Exception as e:
        print(f"⚠️ Pre-step sync failed: {e}")

def _trigger_post_step_sync(self, step_id: str):
    """Trigger post-step sync to push changes to network."""
    if os.environ.get('SMART_SYNC_ENABLED') != 'true':
        return
        
    try:
        result = subprocess.run([
            'python3', '/opt/sync/post_step_sync.py', step_id
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"📤 {result.stdout.strip()}")
        else:
            print(f"⚠️ Sync to network failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️ Post-step sync timeout - changes remain local only")
    except Exception as e:
        print(f"⚠️ Post-step sync failed: {e}")
```

**Location**: Modify `run_step` method around line 112

**Add this line after line 118 (after user_inputs validation)**:

```python
# Smart Sync: Check for network changes before step
self._trigger_pre_step_sync()
```

**Location**: Modify `handle_step_result` method around line 192

**Add this after `self.update_state(step_id, "completed")`**:

```python
# Smart Sync: Push changes to network after successful step
self._trigger_post_step_sync(step_id)
```

#### **2.3 Update Dockerfile for Sync Scripts**

**File**: `Dockerfile`

**Location**: Add after line 64 (after volume mount points creation)

```dockerfile
# Smart Sync scripts mount point
RUN mkdir -p /opt/sync && \
    chown appuser:appuser /opt/sync
```

### **Phase 3: Environment Variable Management**

#### **3.1 Modify run.py prepare_environment method**

**File**: `run.py`

**Location**: Modify `prepare_environment` method around line 458

**Add to the env dictionary**:

```python
env = {
    "PROJECT_PATH": str(project_path),
    "PROJECT_NAME": project_path.name,
    "SCRIPTS_PATH": mode_config["scripts_path"],
    "WORKFLOW_TYPE": workflow_type,
    "APP_ENV": mode_config["app_env"],
    "DOCKER_IMAGE": mode_config["docker_image"],
    "SYNC_SCRIPTS_PATH": str(Path.cwd() / "sync_scripts"),  # Add this line
    **user_ids
}
```

### **Phase 4: Error Handling & Recovery**

#### **4.1 Add Network Error Handling**

**File**: `src/smart_sync.py`

**Add method to SmartSyncManager class**:

```python
def handle_network_error(self) -> bool:
    """Handle network drive disconnection gracefully."""
    try:
        # Test network connectivity
        if not self.network_path.exists():
            click.secho("⚠️ Network drive disconnected", fg='yellow')
            click.echo("Workflow will continue with local data.")
            click.echo("Reconnect network drive and restart to sync changes.")
            return False
        return True
    except Exception:
        return False

def validate_sync_environment(self) -> bool:
    """Validate that sync environment is ready."""
    try:
        # Check network path exists and is accessible
        if not self.network_path.exists():
            return False
            
        # Check local path exists and is writable
        if not self.local_path.exists():
            self.local_path.mkdir(parents=True, exist_ok=True)
            
        # Test write permissions
        test_file = self.local_path / ".sync_test"
        test_file.write_text("test")
        test_file.unlink()
        
        return True
    except Exception:
        return False
```

#### **4.2 Add Sync Status Validation**

**File**: `src/core.py`

**Add method to Project class**:

```python
def _validate_sync_status(self) -> bool:
    """Validate that local and network are in sync before critical operations."""
    if os.environ.get('SMART_SYNC_ENABLED') != 'true':
        return True
        
    try:
        # Import here to avoid circular imports
        import sys
        sys.path.append('/opt/app/src')
        from smart_sync import SmartSyncManager
        
        network_path = os.environ.get('NETWORK_PROJECT_PATH')
        local_path = os.environ.get('LOCAL_PROJECT_PATH')
        
        if not network_path or not local_path:
            return True  # Can't validate, assume OK
            
        sync_manager = SmartSyncManager(network_path, local_path)
        return sync_manager.validate_sync_environment()
        
    except Exception as e:
        print(f"⚠️ Sync validation failed: {e}")
        return True  # Don't block workflow on validation errors
```

---

## 🧪 Testing Implementation

### **Test File**: `tests/test_smart_sync.py` (new file)

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from src.smart_sync import SmartSyncManager

class TestSmartSyncManager:
    
    def setup_method(self):
        """Set up test directories."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        
        self.network_dir.mkdir()
        self.local_dir.mkdir()
        
        self.sync_manager = SmartSyncManager(
            str(self.network_dir), 
            str(self.local_dir)
        )
    
    def teardown_method(self):
        """Clean up test directories."""
        shutil.rmtree(self.temp_dir)
    
    def test_initial_sync(self):
        """Test initial full sync from network to local."""
        # Create test files in network directory
        (self.network_dir / "test.txt").write_text("test content")
        (self.network_dir / ".hidden").write_text("hidden content")
        
        # Perform initial sync
        result = self.sync_manager.initial_sync()
        
        assert result is True
        assert (self.local_dir / "test.txt").exists()
        assert (self.local_dir / ".hidden").exists()
        assert (self.local_dir / "test.txt").read_text() == "test content"
    
    def test_incremental_sync_down(self):
        """Test incremental sync from network to local."""
        # Set up initial state
        (self.network_dir / "existing.txt").write_text("existing")
        (self.local_dir / "existing.txt").write_text("existing")
        
        # Add new file to network
        (self.network_dir / "new.txt").write_text("new content")
        
        # Perform incremental sync
        result = self.sync_manager.incremental_sync_down()
        
        assert result is True
        assert (self.local_dir / "new.txt").exists()
        assert (self.local_dir / "new.txt").read_text() == "new content"
    
    def test_incremental_sync_up(self):
        """Test incremental sync from local to network."""
        # Set up initial state
        (self.network_dir / "existing.txt").write_text("existing")
        (self.local_dir / "existing.txt").write_text("existing")
        
        # Add new file to local
        (self.local_dir / "new.txt").write_text("new content")
        
        # Perform incremental sync
        result = self.sync_manager.incremental_sync_up()
        
        assert result is True
        assert (self.network_dir / "new.txt").exists()
        assert (self.network_dir / "new.txt").read_text() == "new content"
    
    def test_hidden_files_sync(self):
        """Test that hidden files are properly synced."""
        # Create hidden files and directories
        hidden_dir = self.network_dir / ".hidden_dir"
        hidden_dir.mkdir()
        (hidden_dir / "hidden_file.txt").write_text("hidden content")
        
        # Perform sync
        self.sync_manager.initial_sync()
        
        assert (self.local_dir / ".hidden_dir").exists()
        assert (self.local_dir / ".hidden_dir" / "hidden_file.txt").exists()
```

---

## 📝 Implementation Checklist

### **Phase 1: Core Infrastructure**
- [ ] Create `src/smart_sync.py` with `SmartSyncManager` class
- [ ] Add Smart Sync detection methods to `run.py`
- [ ] Modify `launch_container` method in `run.py`
- [ ] Create `sync_scripts/` directory with Python sync scripts
- [ ] Test basic sync functionality

### **Phase 2: Container Integration**
- [ ] Update `docker-compose.yml` with sync volumes and environment
- [ ] Add sync trigger methods to `src/core.py`
- [ ] Integrate pre-step sync in `run_step` method
- [ ] Integrate post-step sync in `handle_step_result` method
- [ ] Update `Dockerfile` for sync script mount points

### **Phase 3: Environment & Error Handling**
- [ ] Add sync scripts path to environment preparation
- [ ] Implement network error handling in `SmartSyncManager`
- [ ] Add sync status validation methods
- [ ] Test error scenarios and recovery

### **Phase 4: Testing & Validation**
- [ ] Create comprehensive test suite for `SmartSyncManager`
- [ ] Test Windows network drive scenarios
- [ ] Test sync performance with various project sizes
- [ ] Validate hidden file synchronization
- [ ] Test network disconnection scenarios

---

## 🚀 Deployment Instructions

### **For Coding Agent**

1. **Start with Phase 1**: Implement core sync infrastructure first
2. **Test incrementally**: Validate each phase before proceeding
3. **Focus on error handling**: Ensure graceful degradation when sync fails
4. **Preserve existing functionality**: All changes should be backward compatible
5. **Windows testing**: Test specifically on Windows with mapped network drives

### **Key Integration Points**

- **run.py line 267**: Add Smart Sync detection methods
- **run.py line 431**: Modify container launch for sync support
- **core.py line 112**: Add pre-step sync trigger
- **core.py line 192**: Add post-step sync trigger
- **docker-compose.yml line 29**: Add sync script volumes
- **Dockerfile line 64**: Add sync mount points

### **Success Criteria**

- ✅ Windows users can run workflows on Z: drives
- ✅ Sync time <10 seconds for typical incremental operations
- ✅ All hidden files (.snapshots, .workflow_status) preserved
- ✅ Graceful handling of network disconnections
- ✅ Zero configuration required from users
- ✅ Backward compatibility with existing macOS/Linux workflows

This implementation plan provides a complete roadmap for implementing the Smart Sync solution while maintaining the existing workflow manager functionality.