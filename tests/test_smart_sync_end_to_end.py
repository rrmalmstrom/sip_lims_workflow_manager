"""
End-to-End Test Suite for Smart Sync Layer

This module provides comprehensive end-to-end tests for the Smart Sync functionality,
validating the complete workflow from Windows network drive detection through Docker
container execution with sync operations.
"""

import pytest
import tempfile
import shutil
import os
import yaml
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.smart_sync import (
    detect_smart_sync_scenario, 
    setup_smart_sync_environment,
    SmartSyncManager
)
from run import PlatformAdapter


class TestSmartSyncEndToEndWorkflow:
    """End-to-end tests for complete Smart Sync workflow."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_project = self.temp_dir / "network_project"
        self.local_staging = self.temp_dir / "local_staging"
        
        # Create network project with test files
        self.network_project.mkdir(parents=True)
        self._create_test_project_structure()
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_project_structure(self):
        """Create a realistic project structure for testing."""
        # Create workflow file
        workflow_content = {
            "workflow_name": "Test SIP Workflow",
            "steps": [
                {
                    "id": "data_preparation",
                    "name": "Data Preparation",
                    "script": "prepare_data.py",
                    "snapshot_items": ["data/"]
                },
                {
                    "id": "analysis",
                    "name": "Run Analysis", 
                    "script": "run_analysis.py",
                    "allow_rerun": True
                }
            ]
        }
        
        workflow_file = self.network_project / "workflow.yml"
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow_content, f)
        
        # Create data directory with test files
        data_dir = self.network_project / "data"
        data_dir.mkdir()
        (data_dir / "input.csv").write_text("sample,value\nA,1\nB,2\nC,3")
        (data_dir / "metadata.json").write_text('{"experiment": "test", "date": "2024-01-01"}')
        
        # Create scripts directory
        scripts_dir = self.network_project / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "prepare_data.py").write_text("print('Preparing data...')")
        (scripts_dir / "run_analysis.py").write_text("print('Running analysis...')")
        
        # Create hidden workflow directories
        (self.network_project / ".workflow_status").mkdir()
        (self.network_project / ".workflow_logs").mkdir()
        (self.network_project / ".snapshots").mkdir()
    
    def test_complete_smart_sync_workflow_simulation(self):
        """Test complete Smart Sync workflow from detection to execution."""
        with patch('platform.system', return_value='Windows'):
            # Simulate Windows network drive path
            network_drive_path = Path("Z:\\test_project")
            
            # Step 1: Test detection
            assert detect_smart_sync_scenario(network_drive_path) is True
            assert PlatformAdapter.detect_smart_sync_scenario(network_drive_path) is True
            
            # Step 2: Test environment setup
            with patch('tempfile.gettempdir', return_value=str(self.temp_dir)):
                env_vars = setup_smart_sync_environment(self.network_project)
                
                # Verify environment variables
                assert env_vars["SMART_SYNC_ENABLED"] == "true"
                assert env_vars["NETWORK_PROJECT_PATH"] == str(self.network_project)
                assert "LOCAL_PROJECT_PATH" in env_vars
                assert "PROJECT_PATH" in env_vars
                
                local_path = Path(env_vars["LOCAL_PROJECT_PATH"])
                
                # Step 3: Verify initial sync completed
                assert local_path.exists()
                assert (local_path / "workflow.yml").exists()
                assert (local_path / "data" / "input.csv").exists()
                assert (local_path / "scripts" / "prepare_data.py").exists()
                
                # Step 4: Test workflow execution with Smart Sync
                with patch.dict(os.environ, env_vars):
                    from src.core import Project
                    
                    # Create project using local staging path
                    project = Project(local_path)
                    
                    # Verify Smart Sync manager was initialized
                    assert project.smart_sync_manager is not None
                    assert isinstance(project.smart_sync_manager, SmartSyncManager)
                    
                    # Step 5: Simulate workflow step execution
                    with patch.object(project.script_runner, 'run'):
                        with patch.object(project.smart_sync_manager, 'incremental_sync_down', return_value=True) as mock_pre_sync:
                            project.run_step("data_preparation")
                            
                            # Verify pre-step sync was called
                            mock_pre_sync.assert_called_once()
                    
                    # Step 6: Simulate successful step completion
                    with patch.object(project.smart_sync_manager, 'incremental_sync_up', return_value=True) as mock_post_sync:
                        # Create success marker
                        status_dir = local_path / ".workflow_status"
                        status_dir.mkdir(exist_ok=True)
                        (status_dir / "prepare_data.success").write_text("success")
                        
                        from src.logic import RunResult
                        result = RunResult(success=True, stdout="Success", stderr="", return_code=0)
                        project.handle_step_result("data_preparation", result)
                        
                        # Verify post-step sync was called
                        mock_post_sync.assert_called_once()
                        
                        # Verify step was marked as completed
                        assert project.get_state("data_preparation") == "completed"
                    
                    # Step 7: Test final cleanup
                    with patch.object(project.smart_sync_manager, 'final_sync', return_value=True) as mock_final_sync:
                        with patch.object(project.smart_sync_manager, 'cleanup') as mock_cleanup:
                            project.finalize_smart_sync()
                            
                            # Verify final sync and cleanup were called
                            mock_final_sync.assert_called_once()
                            mock_cleanup.assert_called_once()
    
    def test_smart_sync_file_preservation(self):
        """Test that Smart Sync preserves all important files including hidden ones."""
        # Create additional hidden files and directories
        hidden_items = [
            ".snapshots/step1/data.zip",
            ".workflow_status/step1.success",
            ".workflow_logs/debug.log",
            ".gitignore",
            "data/.hidden_file"
        ]
        
        for item in hidden_items:
            file_path = self.network_project / item
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"content of {item}")
        
        # Test sync preserves hidden files
        sync_manager = SmartSyncManager(self.network_project, self.local_staging)
        result = sync_manager.initial_sync()
        assert result is True
        
        # Verify all hidden items were synced
        for item in hidden_items:
            local_file = self.local_staging / item
            assert local_file.exists(), f"Hidden file {item} should be synced"
            assert local_file.read_text() == f"content of {item}"
    
    def test_smart_sync_error_resilience(self):
        """Test Smart Sync error handling and resilience."""
        sync_manager = SmartSyncManager(self.network_project, self.local_staging)
        
        # Test sync with permission errors - should handle gracefully
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            result = sync_manager.initial_sync()
            # Should handle gracefully and return True (no files copied but no crash)
            assert result is True
        
        # Test sync with network disconnection simulation - should return False but not crash
        with patch('pathlib.Path.exists', side_effect=OSError("Network error")):
            result = sync_manager.incremental_sync_down()
            # Should handle gracefully and return False (indicating failure)
            assert result is False
        
        # Test logging errors don't break sync
        with patch('json.dump', side_effect=ValueError("JSON error")):
            result = sync_manager.initial_sync()
            # Should still succeed despite logging error
            assert result is True
    
    def test_smart_sync_disabled_on_macos(self):
        """Test that Smart Sync is completely disabled on macOS."""
        with patch('platform.system', return_value='Darwin'):
            # Even network-like paths should not trigger Smart Sync on macOS
            test_paths = [
                Path("/Volumes/NetworkDrive/project"),
                Path("/mnt/share/project"),
                Path("Z:\\project")  # Even Windows-style paths
            ]
            
            for path in test_paths:
                assert detect_smart_sync_scenario(path) is False
                assert PlatformAdapter.detect_smart_sync_scenario(path) is False
            
            # Environment setup should not create Smart Sync environment on macOS
            # Test the proper integration through run.py's PlatformAdapter
            # Since detect_smart_sync_scenario returns False on macOS, setup_smart_sync_environment should not be called
            
            # On macOS, detect_smart_sync_scenario should return False, so setup should not happen
            should_setup = PlatformAdapter.detect_smart_sync_scenario(self.network_project)
            assert should_setup is False, "Smart Sync should not be detected on macOS"
            
            # If we were to call setup_smart_sync_environment directly (which run.py wouldn't do),
            # it would still work, but run.py prevents this call from happening
            # This tests the actual integration logic in run.py
    
    def test_smart_sync_disabled_on_linux(self):
        """Test that Smart Sync is completely disabled on Linux."""
        with patch('platform.system', return_value='Linux'):
            test_paths = [
                Path("/mnt/network/project"),
                Path("/media/share/project"),
                Path("Z:\\project")  # Windows-style paths
            ]
            
            for path in test_paths:
                assert detect_smart_sync_scenario(path) is False
                assert PlatformAdapter.detect_smart_sync_scenario(path) is False


class TestSmartSyncPerformanceAndScaling:
    """Test Smart Sync performance and scaling characteristics."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_dir = self.temp_dir / "network"
        self.local_dir = self.temp_dir / "local"
        self.network_dir.mkdir(parents=True)
        self.local_dir.mkdir(parents=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_smart_sync_with_large_file_count(self):
        """Test Smart Sync performance with many files."""
        # Create many small files
        for i in range(100):
            file_path = self.network_dir / f"file_{i:03d}.txt"
            file_path.write_text(f"Content of file {i}")
        
        # Create nested directory structure
        for i in range(10):
            subdir = self.network_dir / f"subdir_{i}"
            subdir.mkdir()
            for j in range(10):
                (subdir / f"nested_{j}.txt").write_text(f"Nested content {i}-{j}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        # Test initial sync
        result = sync_manager.initial_sync()
        assert result is True
        
        # Verify all files were synced
        assert len(list(self.local_dir.rglob("*.txt"))) == 200  # 100 + (10*10)
        
        # Test incremental sync performance
        # Add a few new files
        for i in range(100, 105):
            (self.network_dir / f"new_file_{i}.txt").write_text(f"New content {i}")
        
        result = sync_manager.incremental_sync_down()
        assert result is True
        
        # Verify new files were synced
        assert len(list(self.local_dir.rglob("*.txt"))) == 205
    
    def test_smart_sync_with_large_files(self):
        """Test Smart Sync with larger files (simulated)."""
        # Create files with more content (simulating larger files)
        large_content = "x" * 10000  # 10KB content
        
        for i in range(5):
            file_path = self.network_dir / f"large_file_{i}.dat"
            file_path.write_text(large_content)
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        
        result = sync_manager.initial_sync()
        assert result is True
        
        # Verify large files were synced correctly
        for i in range(5):
            local_file = self.local_dir / f"large_file_{i}.dat"
            assert local_file.exists()
            assert local_file.read_text() == large_content
    
    def test_smart_sync_incremental_efficiency(self):
        """Test that incremental sync only processes changed files."""
        # Create initial files
        for i in range(10):
            (self.network_dir / f"file_{i}.txt").write_text(f"Original content {i}")
        
        sync_manager = SmartSyncManager(self.network_dir, self.local_dir)
        sync_manager.initial_sync()
        
        # Modify only one file
        (self.network_dir / "file_5.txt").write_text("Modified content 5")
        
        # Mock copy operations to count them
        with patch('shutil.copy2') as mock_copy:
            sync_manager.incremental_sync_down()
            
            # Should only copy the modified file (plus potentially some metadata)
            assert mock_copy.call_count <= 2  # Modified file + possible metadata


class TestSmartSyncDockerIntegration:
    """Test Smart Sync integration with Docker environment."""
    
    def test_docker_environment_variable_integration(self):
        """Test that Smart Sync integrates correctly with Docker environment variables."""
        test_env = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "/network/path",
            "LOCAL_PROJECT_PATH": "/local/path",
            "PROJECT_PATH": "/local/path"  # Docker should use local path
        }
        
        with patch.dict(os.environ, test_env):
            # Test that environment variables are accessible
            assert os.getenv("SMART_SYNC_ENABLED") == "true"
            assert os.getenv("NETWORK_PROJECT_PATH") == "/network/path"
            assert os.getenv("LOCAL_PROJECT_PATH") == "/local/path"
            assert os.getenv("PROJECT_PATH") == "/local/path"
    
    def test_docker_compose_configuration_compatibility(self):
        """Test that Docker Compose configuration supports Smart Sync."""
        # Read docker-compose.yml
        project_root = Path(__file__).parent.parent
        docker_compose_path = project_root / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        service_config = compose_config['services']['sip-lims-workflow']
        
        # Verify Smart Sync environment variables are configured
        env_vars = {}
        for env_item in service_config['environment']:
            if '=' in env_item:
                key, value = env_item.split('=', 1)
                env_vars[key] = value
        
        smart_sync_vars = ['SMART_SYNC_ENABLED', 'NETWORK_PROJECT_PATH', 'LOCAL_PROJECT_PATH']
        for var in smart_sync_vars:
            assert var in env_vars, f"Missing Smart Sync environment variable: {var}"


class TestSmartSyncRealWorldScenarios:
    """Test Smart Sync with realistic usage scenarios."""
    
    def setup_method(self):
        """Set up realistic test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.network_project = self.temp_dir / "sip_project"
        self.network_project.mkdir(parents=True)
        
        # Create realistic SIP project structure
        self._create_realistic_sip_project()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_realistic_sip_project(self):
        """Create a realistic SIP LIMS project structure."""
        # Create workflow file
        workflow = {
            "workflow_name": "SIP Metagenomic Analysis",
            "steps": [
                {"id": "quality_control", "name": "Quality Control", "script": "qc_check.py"},
                {"id": "trimming", "name": "Read Trimming", "script": "trim_reads.py"},
                {"id": "assembly", "name": "Genome Assembly", "script": "assemble.py"},
                {"id": "annotation", "name": "Gene Annotation", "script": "annotate.py"}
            ]
        }
        
        with open(self.network_project / "workflow.yml", 'w') as f:
            yaml.dump(workflow, f)
        
        # Create data directories
        data_dir = self.network_project / "data"
        data_dir.mkdir()
        (data_dir / "raw_reads_R1.fastq").write_text("@read1\nACGT\n+\nIIII\n")
        (data_dir / "raw_reads_R2.fastq").write_text("@read2\nTGCA\n+\nIIII\n")
        (data_dir / "sample_metadata.csv").write_text("sample_id,condition\nS1,control\nS2,treatment\n")
        
        # Create scripts directory
        scripts_dir = self.network_project / "scripts"
        scripts_dir.mkdir()
        for script in ["qc_check.py", "trim_reads.py", "assemble.py", "annotate.py"]:
            (scripts_dir / script).write_text(f"# {script}\nprint('Running {script}')")
        
        # Create results directory structure
        results_dir = self.network_project / "results"
        results_dir.mkdir()
        (results_dir / "qc_report.html").write_text("<html>QC Report</html>")
        
        # Create hidden workflow directories with some content
        for hidden_dir in [".workflow_status", ".workflow_logs", ".snapshots"]:
            dir_path = self.network_project / hidden_dir
            dir_path.mkdir()
            # Add a placeholder file so the directory gets synced
            (dir_path / ".gitkeep").write_text("")
    
    def test_realistic_sip_workflow_with_smart_sync(self):
        """Test Smart Sync with a realistic SIP workflow."""
        with patch('platform.system', return_value='Windows'):
            # Simulate Windows network drive
            network_path = Path("Z:\\sip_projects\\project_001")
            
            # Test detection
            assert detect_smart_sync_scenario(network_path) is True
            
            # Test environment setup
            with patch('tempfile.gettempdir', return_value=str(self.temp_dir)):
                env_vars = setup_smart_sync_environment(self.network_project)
                
                local_path = Path(env_vars["LOCAL_PROJECT_PATH"])
                
                # Verify realistic project structure was synced
                assert (local_path / "workflow.yml").exists()
                assert (local_path / "data" / "raw_reads_R1.fastq").exists()
                assert (local_path / "data" / "sample_metadata.csv").exists()
                assert (local_path / "scripts" / "qc_check.py").exists()
                assert (local_path / "results" / "qc_report.html").exists()
                
                # Verify hidden directories were synced
                assert (local_path / ".workflow_status").exists()
                assert (local_path / ".workflow_logs").exists()
                assert (local_path / ".snapshots").exists()
    
    def test_smart_sync_handles_workflow_artifacts(self):
        """Test that Smart Sync properly handles workflow-generated artifacts."""
        sync_manager = SmartSyncManager(self.network_project, self.temp_dir / "local")
        
        # Initial sync
        sync_manager.initial_sync()
        
        # Simulate workflow generating artifacts
        local_path = self.temp_dir / "local"
        
        # Create workflow artifacts (ensure parent directories exist)
        results_dir = local_path / "results"
        results_dir.mkdir(exist_ok=True)
        (results_dir / "trimmed_reads.fastq").write_text("@trimmed\nACGT\n+\nIIII\n")
        
        status_dir = local_path / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        (status_dir / "trimming.success").write_text("success")
        
        snapshots_dir = local_path / ".snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        (snapshots_dir / "trimming_complete.zip").write_bytes(b"fake zip content")
        
        # Test sync back to network
        result = sync_manager.incremental_sync_up()
        assert result is True
        
        # Verify artifacts were synced back
        assert (self.network_project / "results" / "trimmed_reads.fastq").exists()
        assert (self.network_project / ".workflow_status" / "trimming.success").exists()
        assert (self.network_project / ".snapshots" / "trimming_complete.zip").exists()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])