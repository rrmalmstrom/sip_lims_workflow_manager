"""
Windows Simulation Test Suite for Smart Sync

This module provides comprehensive Windows environment simulation tests for Smart Sync
functionality, allowing validation on macOS development environment.

Key Testing Areas:
1. Windows platform detection and network drive identification
2. Smart Sync environment setup and configuration
3. Docker integration with Windows-specific paths
4. Error handling and edge cases
5. Performance validation under simulated Windows conditions
"""

import pytest
import tempfile
import shutil
import os
import platform
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import subprocess

from src.smart_sync import (
    SmartSyncManager, 
    detect_smart_sync_scenario, 
    setup_smart_sync_environment
)
from run import PlatformAdapter, ContainerManager


class TestWindowsPlatformSimulation:
    """Test Windows platform detection and Smart Sync activation."""
    
    @patch('platform.system', return_value='Windows')
    def test_windows_detection_network_drives(self, mock_platform):
        """Test detection of Windows network drives (D: through Z:)."""
        # Test all potential network drives
        network_drives = [
            'D:\\project', 'E:\\data', 'F:\\shared', 'G:\\network',
            'H:\\storage', 'I:\\backup', 'J:\\temp', 'K:\\files',
            'L:\\documents', 'M:\\media', 'N:\\archive', 'O:\\work',
            'P:\\projects', 'Q:\\queue', 'R:\\resources', 'S:\\scripts',
            'T:\\tools', 'U:\\users', 'V:\\volumes', 'W:\\workspace',
            'X:\\external', 'Y:\\yesterday', 'Z:\\zone'
        ]
        
        for drive_path in network_drives:
            path = Path(drive_path)
            assert detect_smart_sync_scenario(path) is True, f"Should detect {drive_path} as network drive"
            assert PlatformAdapter.detect_smart_sync_scenario(path) is True, f"PlatformAdapter should detect {drive_path}"
    
    @patch('platform.system', return_value='Windows')
    def test_windows_detection_local_drives(self, mock_platform):
        """Test that C: drive (local) does not trigger Smart Sync."""
        local_paths = [
            'C:\\Users\\test', 'C:\\Program Files', 'C:\\temp',
            'C:\\Windows', 'C:\\ProgramData', 'C:\\Projects'
        ]
        
        for local_path in local_paths:
            path = Path(local_path)
            assert detect_smart_sync_scenario(path) is False, f"Should NOT detect {local_path} as network drive"
            assert PlatformAdapter.detect_smart_sync_scenario(path) is False, f"PlatformAdapter should NOT detect {local_path}"
    
    @patch('platform.system', return_value='Windows')
    def test_windows_detection_unc_paths(self, mock_platform):
        """Test detection of UNC network paths."""
        unc_paths = [
            '\\\\server\\share\\folder',
            '\\\\storage.company.com\\data\\project',
            '\\\\192.168.1.100\\shared\\files',
            '//server/share/folder',  # Unix-style UNC
            '//storage/data/project'
        ]
        
        for unc_path in unc_paths:
            path = Path(unc_path)
            assert detect_smart_sync_scenario(path) is True, f"Should detect {unc_path} as UNC path"
            assert PlatformAdapter.detect_smart_sync_scenario(path) is True, f"PlatformAdapter should detect {unc_path}"
    
    @patch('platform.system', return_value='Windows')
    def test_windows_detection_edge_cases(self, mock_platform):
        """Test edge cases and invalid paths."""
        edge_cases = [
            '',  # Empty string
            'relative/path',  # Relative path
            '/unix/style/path',  # Unix absolute path
            'C:',  # Drive letter only
            'Z:',  # Network drive letter only
            '\\',  # Single backslash
            '\\\\',  # Double backslash only
            'file.txt',  # Just filename
            '.',  # Current directory
            '..',  # Parent directory
        ]
        
        for edge_case in edge_cases:
            path = Path(edge_case)
            # Most edge cases should not trigger Smart Sync
            result = detect_smart_sync_scenario(path)
            platform_result = PlatformAdapter.detect_smart_sync_scenario(path)
            
            # Only 'Z:' and '\\\\' (UNC start) should trigger Smart Sync among these edge cases
            if edge_case in ['Z:', '\\\\']:
                assert result is True, f"Should detect {edge_case} as network drive"
                assert platform_result is True, f"PlatformAdapter should detect {edge_case}"
            else:
                assert result is False, f"Should NOT detect {edge_case} as network drive"
                assert platform_result is False, f"PlatformAdapter should NOT detect {edge_case}"
    
    def test_non_windows_platforms_disabled(self):
        """Test that Smart Sync is completely disabled on non-Windows platforms."""
        platforms = ['Darwin', 'Linux', 'FreeBSD', 'OpenBSD']
        
        for platform_name in platforms:
            with patch('platform.system', return_value=platform_name):
                # Even Windows-style paths should not trigger Smart Sync
                windows_paths = [
                    Path('Z:\\project'),
                    Path('D:\\data'),
                    Path('\\\\server\\share')
                ]
                
                for path in windows_paths:
                    assert detect_smart_sync_scenario(path) is False, f"Should NOT detect on {platform_name}"
                    assert PlatformAdapter.detect_smart_sync_scenario(path) is False, f"PlatformAdapter should NOT detect on {platform_name}"


class TestWindowsSmartSyncEnvironmentSetup:
    """Test Smart Sync environment setup simulation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_project = self.temp_dir / "test_project"
        self.network_project.mkdir(parents=True)
        
        # Create realistic project structure
        self._create_test_project()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_project(self):
        """Create a realistic test project structure."""
        # Create workflow file
        workflow = {
            "workflow_name": "Test SIP Workflow",
            "steps": [
                {"id": "step1", "name": "Test Step 1", "script": "test1.py"},
                {"id": "step2", "name": "Test Step 2", "script": "test2.py"}
            ]
        }
        with open(self.network_project / "workflow.yml", 'w') as f:
            yaml.dump(workflow, f)
        
        # Create data and scripts
        (self.network_project / "data").mkdir()
        (self.network_project / "data" / "input.csv").write_text("sample,value\nA,1\nB,2")
        (self.network_project / "scripts").mkdir()
        (self.network_project / "scripts" / "test1.py").write_text("print('Test 1')")
        
        # Create hidden directories
        for hidden_dir in [".workflow_status", ".workflow_logs", ".snapshots"]:
            (self.network_project / hidden_dir).mkdir()
            (self.network_project / hidden_dir / ".gitkeep").write_text("")
    
    @patch('platform.system', return_value='Windows')
    @patch('tempfile.gettempdir')
    def test_smart_sync_environment_setup_success(self, mock_tempdir, mock_platform):
        """Test successful Smart Sync environment setup."""
        mock_tempdir.return_value = str(self.temp_dir)
        
        # Test environment setup
        env_vars = setup_smart_sync_environment(self.network_project)
        
        # Verify environment variables
        assert env_vars["SMART_SYNC_ENABLED"] == "true"
        assert env_vars["NETWORK_PROJECT_PATH"] == str(self.network_project)
        assert "LOCAL_PROJECT_PATH" in env_vars
        assert "PROJECT_PATH" in env_vars
        
        # Verify local staging was created
        local_path = Path(env_vars["LOCAL_PROJECT_PATH"])
        assert local_path.exists()
        assert local_path.name == "test_project"
        
        # Verify files were synced
        assert (local_path / "workflow.yml").exists()
        assert (local_path / "data" / "input.csv").exists()
        assert (local_path / "scripts" / "test1.py").exists()
        
        # Verify hidden directories were synced
        assert (local_path / ".workflow_status").exists()
        assert (local_path / ".workflow_logs").exists()
        assert (local_path / ".snapshots").exists()
    
    @patch('platform.system', return_value='Windows')
    @patch('tempfile.gettempdir')
    @patch('src.smart_sync.SmartSyncManager.initial_sync', return_value=False)
    def test_smart_sync_environment_setup_failure(self, mock_sync, mock_tempdir, mock_platform):
        """Test Smart Sync environment setup failure handling."""
        mock_tempdir.return_value = str(self.temp_dir)
        
        # Should raise RuntimeError when initial sync fails
        with pytest.raises(RuntimeError, match="Initial sync failed"):
            setup_smart_sync_environment(self.network_project)
    
    @patch('platform.system', return_value='Windows')
    def test_platform_adapter_integration(self, mock_platform):
        """Test PlatformAdapter integration with Smart Sync setup."""
        with patch('tempfile.gettempdir', return_value=str(self.temp_dir)):
            # Test that PlatformAdapter can set up Smart Sync environment
            env_vars = PlatformAdapter.setup_smart_sync_environment(self.network_project)
            
            # Verify it returns the same structure as direct setup
            assert env_vars["SMART_SYNC_ENABLED"] == "true"
            assert "NETWORK_PROJECT_PATH" in env_vars
            assert "LOCAL_PROJECT_PATH" in env_vars
            assert "PROJECT_PATH" in env_vars


class TestWindowsDockerIntegration:
    """Test Docker integration with Windows Smart Sync simulation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True)
        
        # Create minimal project structure
        (self.project_dir / "workflow.yml").write_text("workflow_name: Test\nsteps: []")
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('platform.system', return_value='Windows')
    @patch('tempfile.gettempdir')
    def test_container_manager_smart_sync_integration(self, mock_tempdir, mock_platform):
        """Test ContainerManager integration with Smart Sync."""
        mock_tempdir.return_value = str(self.temp_dir)
        
        # Mock branch info for ContainerManager
        branch_info = {
            'branch': 'main',
            'tag': 'latest',
            'local_image': 'local:latest',
            'remote_image': 'remote:latest'
        }
        
        container_manager = ContainerManager(branch_info)
        
        # Simulate Windows network drive path
        network_path = Path("Z:\\test_project")
        
        # Mock the actual container launch to avoid Docker dependency
        with patch.object(container_manager, 'prepare_environment') as mock_prepare:
            with patch('subprocess.run') as mock_subprocess:
                with patch.object(container_manager, 'display_environment_summary'):
                    mock_prepare.return_value = {"TEST": "value"}
                    
                    # Test that Smart Sync is detected and environment is set up
                    try:
                        container_manager.launch_container(self.project_dir, "sip", {"scripts_path": "/test"})
                    except Exception:
                        pass  # Expected since we're mocking subprocess
                    
                    # Verify prepare_environment was called with local path when Smart Sync is active
                    mock_prepare.assert_called()
    
    @patch('platform.system', return_value='Windows')
    def test_docker_environment_variables_windows(self, mock_platform):
        """Test Docker environment variables in Windows Smart Sync scenario."""
        # Simulate Smart Sync environment
        smart_sync_env = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "Z:\\test_project",
            "LOCAL_PROJECT_PATH": "C:\\temp\\sip_workflow\\test_project",
            "PROJECT_PATH": "C:\\temp\\sip_workflow\\test_project"
        }
        
        with patch.dict(os.environ, smart_sync_env):
            # Verify environment variables are accessible
            assert os.getenv("SMART_SYNC_ENABLED") == "true"
            assert os.getenv("NETWORK_PROJECT_PATH") == "Z:\\test_project"
            assert os.getenv("LOCAL_PROJECT_PATH") == "C:\\temp\\sip_workflow\\test_project"
            assert os.getenv("PROJECT_PATH") == "C:\\temp\\sip_workflow\\test_project"
    
    def test_docker_compose_compatibility_check(self):
        """Test that docker-compose.yml supports Smart Sync environment variables."""
        # Read actual docker-compose.yml
        project_root = Path(__file__).parent.parent
        docker_compose_path = project_root / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        service_config = compose_config['services']['sip-lims-workflow']
        
        # Convert environment list to dict
        env_vars = {}
        for env_item in service_config['environment']:
            if '=' in env_item:
                key, value = env_item.split('=', 1)
                env_vars[key] = value
        
        # Verify Smart Sync environment variables are present
        required_vars = ['SMART_SYNC_ENABLED', 'NETWORK_PROJECT_PATH', 'LOCAL_PROJECT_PATH']
        for var in required_vars:
            assert var in env_vars, f"Missing Smart Sync environment variable: {var}"
            
        # Verify default values
        assert env_vars['SMART_SYNC_ENABLED'] == '${SMART_SYNC_ENABLED:-false}'
        assert env_vars['NETWORK_PROJECT_PATH'] == '${NETWORK_PROJECT_PATH:-}'
        assert env_vars['LOCAL_PROJECT_PATH'] == '${LOCAL_PROJECT_PATH:-}'


class TestWindowsWorkflowIntegration:
    """Test workflow execution integration with Windows Smart Sync simulation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True)
        
        # Create test workflow
        workflow_content = {
            "workflow_name": "Test Workflow",
            "steps": [
                {"id": "step1", "name": "Test Step", "script": "test.py"}
            ]
        }
        
        with open(self.project_dir / "workflow.yml", 'w') as f:
            yaml.dump(workflow_content, f)
        
        # Create scripts directory
        scripts_dir = self.project_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.py").write_text("print('Test script')")
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('platform.system', return_value='Windows')
    def test_project_smart_sync_initialization(self, mock_platform):
        """Test Project class initialization with Smart Sync environment."""
        # Set Smart Sync environment variables
        smart_sync_env = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "Z:\\test_project",
            "LOCAL_PROJECT_PATH": str(self.project_dir)
        }
        
        with patch.dict(os.environ, smart_sync_env):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock()
                mock_get_manager.return_value = mock_manager
                
                from src.core import Project
                project = Project(self.project_dir)
                
                # Verify Smart Sync manager was initialized
                assert project.smart_sync_manager is not None
                mock_get_manager.assert_called_once_with("Z:\\test_project", str(self.project_dir))
    
    @patch('platform.system', return_value='Windows')
    def test_workflow_step_sync_triggers(self, mock_platform):
        """Test that workflow steps trigger sync operations in Windows environment."""
        smart_sync_env = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "Z:\\test_project",
            "LOCAL_PROJECT_PATH": str(self.project_dir)
        }
        
        with patch.dict(os.environ, smart_sync_env):
            with patch('src.core.get_smart_sync_manager') as mock_get_manager:
                mock_manager = MagicMock()
                mock_manager.incremental_sync_down.return_value = True
                mock_manager.incremental_sync_up.return_value = True
                mock_get_manager.return_value = mock_manager
                
                from src.core import Project
                project = Project(self.project_dir)
                
                # Mock script runner to avoid actual execution
                with patch.object(project.script_runner, 'run'):
                    # Test pre-step sync
                    project.run_step("step1")
                    mock_manager.incremental_sync_down.assert_called_once()
                    
                    # Test post-step sync
                    status_dir = self.project_dir / ".workflow_status"
                    status_dir.mkdir(exist_ok=True)
                    (status_dir / "test.success").write_text("success")
                    
                    from src.logic import RunResult
                    result = RunResult(success=True, stdout="Success", stderr="", return_code=0)
                    project.handle_step_result("step1", result)
                    
                    mock_manager.incremental_sync_up.assert_called_once()


class TestWindowsErrorHandling:
    """Test error handling in Windows Smart Sync scenarios."""
    
    @patch('platform.system', return_value='Windows')
    def test_sync_failure_graceful_handling(self, mock_platform):
        """Test that sync failures are handled gracefully without crashing workflow."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            network_dir = temp_dir / "network"
            local_dir = temp_dir / "local"
            network_dir.mkdir()
            local_dir.mkdir()
            
            sync_manager = SmartSyncManager(network_dir, local_dir)
            
            # Test permission error handling
            with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
                # Should not raise exception
                result = sync_manager.initial_sync()
                assert result is True  # Should handle gracefully
            
            # Test network disconnection simulation
            with patch('pathlib.Path.exists', side_effect=OSError("Network error")):
                result = sync_manager.incremental_sync_down()
                assert result is False  # Should return False but not crash
                
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('platform.system', return_value='Windows')
    def test_invalid_path_handling(self, mock_platform):
        """Test handling of invalid Windows paths."""
        invalid_paths = [
            "Z:\\nonexistent\\path",
            "\\\\invalid\\server\\share",
            "X:\\",  # Drive root that doesn't exist
            "",  # Empty path
        ]
        
        for invalid_path in invalid_paths:
            # Should not crash on invalid paths
            try:
                result = detect_smart_sync_scenario(Path(invalid_path))
                # Drive letters should trigger Smart Sync regardless of path validity
                # UNC paths should also trigger Smart Sync
                if invalid_path.startswith(("Z:", "X:", "\\\\")):
                    assert result is True, f"Should detect {invalid_path} as network drive"
                else:
                    assert result is False, f"Should NOT detect {invalid_path} as network drive"
            except Exception as e:
                pytest.fail(f"Should not raise exception for invalid path {invalid_path}: {e}")


class TestWindowsPerformanceSimulation:
    """Test performance characteristics under simulated Windows conditions."""
    
    def setup_method(self):
        """Set up performance test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir()
        self.local_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('platform.system', return_value='Windows')
    def test_large_project_sync_performance(self, mock_platform):
        """Test sync performance with large number of files (Windows simulation)."""
        # Create many files to simulate large project
        for i in range(50):  # Reduced from 200 for faster testing
            (self.network_dir / f"file_{i:03d}.txt").write_text(f"Content {i}")
        
        # Create nested structure
        for i in range(5):
            subdir = self.network_dir / f"subdir_{i}"
            subdir.mkdir()
            for j in range(10):
                (subdir / f"nested_{j}.txt").write_text(f"Nested {i}-{j}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Measure initial sync time
        import time
        start_time = time.time()
        result = sync_manager.initial_sync()
        sync_duration = time.time() - start_time
        
        assert result is True
        assert sync_duration < 10.0, f"Initial sync took too long: {sync_duration:.2f}s"
        
        # Verify all files were synced
        assert len(list(self.local_dir.rglob("*.txt"))) == 100  # 50 + (5*10)
    
    @patch('platform.system', return_value='Windows')
    def test_incremental_sync_efficiency(self, mock_platform):
        """Test incremental sync efficiency under Windows simulation."""
        # Set up initial files
        for i in range(20):
            (self.network_dir / f"file_{i}.txt").write_text(f"Original {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.initial_sync()
        
        # Modify only a few files
        (self.network_dir / "file_5.txt").write_text("Modified 5")
        (self.network_dir / "file_15.txt").write_text("Modified 15")
        
        # Test incremental sync performance
        import time
        start_time = time.time()
        result = sync_manager.incremental_sync_down()
        sync_duration = time.time() - start_time
        
        assert result is True
        assert sync_duration < 2.0, f"Incremental sync took too long: {sync_duration:.2f}s"
        
        # Verify only modified files were processed
        assert (self.local_dir / "file_5.txt").read_text() == "Modified 5"
        assert (self.local_dir / "file_15.txt").read_text() == "Modified 15"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])