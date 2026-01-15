# 🧪 Windows Smart Sync Testing Strategy

## 📋 Testing Challenge

**Current Situation**: Smart Sync implementation is complete with 52/52 unit tests passing, but we need **real Windows testing** to validate the actual network drive functionality.

**Challenge**: We're developing on macOS, but Smart Sync only activates on Windows with network drives (Z:\, Y:\, etc.).

---

## 🎯 Multi-Phase Testing Strategy

### **Phase 1: Simulated Windows Testing (Current Environment)**

#### **1.1 Mock Windows Environment Testing**
We can simulate Windows scenarios on macOS for initial validation:

```python
# Test file: tests/test_windows_simulation.py
import pytest
import platform
from unittest.mock import patch, MagicMock
from pathlib import Path

@patch('platform.system', return_value='Windows')
def test_smart_sync_detection_simulation():
    """Simulate Windows environment to test detection logic."""
    from run import PlatformAdapter
    
    # Test network drive detection
    assert PlatformAdapter.detect_smart_sync_scenario(Path("Z:\\test_project"))
    assert PlatformAdapter.detect_smart_sync_scenario(Path("Y:\\another_project"))
    assert not PlatformAdapter.detect_smart_sync_scenario(Path("C:\\local_project"))

@patch('platform.system', return_value='Windows')
@patch('pathlib.Path.mkdir')
@patch('src.smart_sync.SmartSyncManager.initial_sync', return_value=True)
def test_smart_sync_environment_setup_simulation(mock_sync, mock_mkdir):
    """Simulate Smart Sync environment setup."""
    from run import PlatformAdapter
    
    network_path = Path("Z:\\test_project")
    env = PlatformAdapter.setup_smart_sync_environment(network_path)
    
    assert env["SMART_SYNC_ENABLED"] == "true"
    assert "C:\\temp\\sip_workflow\\test_project" in env["LOCAL_PROJECT_PATH"]
    assert "Z:\\test_project" in env["NETWORK_PROJECT_PATH"]
```

#### **1.2 Docker Environment Variable Testing**
Test that Docker receives correct environment variables:

```python
# Test file: tests/test_docker_env_simulation.py
@patch('platform.system', return_value='Windows')
def test_docker_environment_variables():
    """Test Docker gets correct environment when Smart Sync is active."""
    # Simulate Windows + network drive scenario
    # Verify docker-compose.yml gets correct environment variables
```

### **Phase 2: Windows Virtual Machine Testing**

#### **2.1 Windows VM Setup**
**Recommended Approach**: Set up a Windows VM with network drive simulation

**VM Configuration**:
- Windows 11 with Docker Desktop
- Shared folder mounted as network drive (Z:\)
- Git clone of the repository
- Python environment setup

**Network Drive Simulation**:
```powershell
# In Windows VM, create simulated network drive
net use Z: \\localhost\shared_folder /persistent:yes
# Or use subst command for testing
subst Z: C:\NetworkDriveSimulation
```

#### **2.2 VM Testing Checklist**
- [ ] Clone repository in Windows VM
- [ ] Set up Python environment
- [ ] Create test project on Z:\ drive
- [ ] Run `python run.py` and verify Smart Sync activation
- [ ] Test complete workflow execution
- [ ] Verify sync operations work correctly
- [ ] Test network disconnection scenarios

### **Phase 3: Real Windows Environment Testing**

#### **3.1 Windows Lab Computer Testing**
**Ideal Scenario**: Test on actual Windows computer with real network drive

**Test Environment**:
- Windows computer with Docker Desktop
- Actual network drive mapped (Z:\)
- Real SIP workflow project data
- Multiple workflow steps to test sync

#### **3.2 User Acceptance Testing**
**Final Validation**: Have actual Windows users test the solution

**Test Scenarios**:
- Laboratory teammate with Windows computer
- Real network drive with actual project data
- Complete workflow execution from start to finish
- Performance measurement of sync operations

---

## 🔧 Testing Implementation Plan

### **Immediate Actions (Phase 1)**

#### **1. Create Windows Simulation Tests**

**File**: `tests/test_windows_simulation.py` (new)

```python
import pytest
import platform
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

class TestWindowsSimulation:
    """Test Smart Sync functionality by simulating Windows environment."""
    
    @patch('platform.system', return_value='Windows')
    def test_windows_detection(self):
        """Test Windows platform detection."""
        from run import PlatformAdapter
        
        # Should detect network drives
        assert PlatformAdapter.detect_smart_sync_scenario(Path("Z:\\project"))
        assert PlatformAdapter.detect_smart_sync_scenario(Path("Y:\\data"))
        assert PlatformAdapter.detect_smart_sync_scenario(Path("D:\\shared"))
        
        # Should NOT detect local drives
        assert not PlatformAdapter.detect_smart_sync_scenario(Path("C:\\local"))
    
    @patch('platform.system', return_value='Windows')
    @patch('src.smart_sync.SmartSyncManager')
    def test_smart_sync_environment_setup(self, mock_sync_manager):
        """Test Smart Sync environment setup simulation."""
        from run import PlatformAdapter
        
        # Mock successful sync
        mock_instance = MagicMock()
        mock_instance.initial_sync.return_value = True
        mock_sync_manager.return_value = mock_instance
        
        # Test environment setup
        network_path = Path("Z:\\test_project")
        
        with patch('pathlib.Path.mkdir'):
            env = PlatformAdapter.setup_smart_sync_environment(network_path)
        
        # Verify environment variables
        assert env["SMART_SYNC_ENABLED"] == "true"
        assert "test_project" in env["LOCAL_PROJECT_PATH"]
        assert "Z:\\test_project" in env["NETWORK_PROJECT_PATH"]
        
        # Verify sync manager was called
        mock_sync_manager.assert_called_once()
        mock_instance.initial_sync.assert_called_once()
    
    @patch('platform.system', return_value='Windows')
    def test_workflow_integration_simulation(self):
        """Test workflow integration with simulated Windows environment."""
        from src.core import Project
        from pathlib import Path
        import os
        
        # Set up simulated Smart Sync environment
        os.environ['SMART_SYNC_ENABLED'] = 'true'
        os.environ['NETWORK_PROJECT_PATH'] = 'Z:\\test_project'
        os.environ['LOCAL_PROJECT_PATH'] = 'C:\\temp\\test_project'
        
        try:
            # Test that sync triggers are called (mocked)
            with patch('src.core.Project._trigger_pre_step_sync') as mock_pre:
                with patch('src.core.Project._trigger_post_step_sync') as mock_post:
                    # Simulate workflow step execution
                    # Verify sync triggers are called appropriately
                    pass
        finally:
            # Clean up environment
            for key in ['SMART_SYNC_ENABLED', 'NETWORK_PROJECT_PATH', 'LOCAL_PROJECT_PATH']:
                os.environ.pop(key, None)
```

#### **2. Create Docker Configuration Tests**

**File**: `tests/test_docker_windows_config.py` (new)

```python
import pytest
import os
from unittest.mock import patch

class TestDockerWindowsConfig:
    """Test Docker configuration for Windows Smart Sync scenarios."""
    
    @patch('platform.system', return_value='Windows')
    def test_docker_compose_environment(self):
        """Test docker-compose gets correct environment variables."""
        # Test that when Smart Sync is enabled, Docker gets correct env vars
        pass
    
    def test_docker_compose_backward_compatibility(self):
        """Test docker-compose works normally when Smart Sync is disabled."""
        # Test that macOS/Linux workflows are unaffected
        pass
```

### **Medium-term Actions (Phase 2)**

#### **3. Windows VM Testing Setup**

**VM Configuration Script**: `scripts/setup_windows_vm.ps1` (new)

```powershell
# Windows VM setup script for Smart Sync testing
# Install Docker Desktop
# Set up Python environment
# Create simulated network drive
# Clone repository and run tests
```

**VM Test Script**: `scripts/test_windows_vm.py` (new)

```python
#!/usr/bin/env python3
"""
Windows VM testing script for Smart Sync functionality.
Run this script in Windows VM to validate Smart Sync operations.
"""

import subprocess
import sys
from pathlib import Path

def setup_test_environment():
    """Set up test environment in Windows VM."""
    # Create simulated network drive
    # Set up test project
    # Verify Docker Desktop is running
    pass

def run_smart_sync_tests():
    """Run comprehensive Smart Sync tests in Windows environment."""
    # Test detection
    # Test sync operations
    # Test workflow execution
    # Test error scenarios
    pass

if __name__ == "__main__":
    setup_test_environment()
    run_smart_sync_tests()
```

### **Long-term Actions (Phase 3)**

#### **4. Real Windows Environment Testing**

**Test Plan Document**: `plans/windows_real_environment_testing.md`

```markdown
# Real Windows Environment Testing Plan

## Test Scenarios
1. Laboratory computer with actual network drive
2. Real SIP workflow project data
3. Complete workflow execution
4. Performance benchmarking
5. User acceptance testing

## Success Criteria
- Smart Sync activates automatically
- Sync operations complete in <10 seconds
- All workflow steps execute successfully
- Hidden files (.snapshots) preserved
- Network disconnection handled gracefully
```

---

## 🎯 Testing Priorities

### **Priority 1: Immediate (This Week)**
- [ ] Create Windows simulation tests
- [ ] Add Docker configuration tests
- [ ] Verify unit test coverage is complete
- [ ] Test error handling scenarios

### **Priority 2: Short-term (Next Week)**
- [ ] Set up Windows VM for testing
- [ ] Create VM testing scripts
- [ ] Test complete workflow in simulated environment
- [ ] Document VM testing procedures

### **Priority 3: Medium-term (Following Week)**
- [ ] Arrange access to Windows lab computer
- [ ] Test with real network drive
- [ ] Performance benchmarking
- [ ] User acceptance testing with lab teammates

---

## 🔍 Testing Validation Checklist

### **Functional Testing**
- [ ] Smart Sync detection works on Windows
- [ ] Local staging directory created correctly
- [ ] Initial sync completes successfully
- [ ] Incremental sync operations work
- [ ] Workflow steps trigger sync correctly
- [ ] Final sync and cleanup work
- [ ] Hidden files preserved (.snapshots, .workflow_status)

### **Performance Testing**
- [ ] Initial sync time acceptable (<60 seconds)
- [ ] Incremental sync time fast (<10 seconds)
- [ ] Large project handling (>500MB)
- [ ] Many files handling (>1000 files)

### **Error Handling Testing**
- [ ] Network drive disconnection
- [ ] Permission errors
- [ ] Disk space issues
- [ ] Docker failures
- [ ] Graceful degradation

### **Integration Testing**
- [ ] Docker container launches correctly
- [ ] Environment variables passed correctly
- [ ] Workflow manager functions normally
- [ ] Snapshot system preserved
- [ ] Undo functionality works

### **Compatibility Testing**
- [ ] macOS workflows unaffected
- [ ] Linux workflows unaffected
- [ ] Existing Docker functionality preserved
- [ ] No performance impact on non-Windows

---

## 🚀 Next Steps

1. **Commit Current Implementation**: Save all Smart Sync code changes
2. **Create Simulation Tests**: Implement Phase 1 testing immediately
3. **Set Up VM Testing**: Prepare Windows VM environment
4. **Plan Real Testing**: Coordinate with Windows lab computer access
5. **Document Results**: Track testing progress and issues

This comprehensive testing strategy ensures we can validate Smart Sync functionality across simulated, virtual, and real Windows environments while maintaining development velocity on macOS.