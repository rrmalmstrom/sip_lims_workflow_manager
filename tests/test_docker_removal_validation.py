"""
Test suite for Docker removal validation.
This test ensures that Docker components are properly removed and 
the system functions without Docker dependencies.

Following TDD methodology:
1. Write tests first (RED)
2. Remove Docker components (GREEN) 
3. Refactor and validate (REFACTOR)
"""

import os
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDockerInfrastructureRemoval:
    """Test that Docker infrastructure files are properly removed."""
    
    def test_dockerfile_removed(self):
        """Test that Dockerfile is removed."""
        dockerfile_path = Path("Dockerfile")
        assert not dockerfile_path.exists(), "Dockerfile should be removed"
    
    def test_docker_compose_removed(self):
        """Test that docker-compose.yml is removed."""
        compose_path = Path("docker-compose.yml")
        assert not compose_path.exists(), "docker-compose.yml should be removed"
    
    def test_entrypoint_script_removed(self):
        """Test that entrypoint.sh is removed."""
        entrypoint_path = Path("entrypoint.sh")
        assert not entrypoint_path.exists(), "entrypoint.sh should be removed"


class TestSmartSyncSystemRemoval:
    """Test that Smart Sync system components are properly removed."""
    
    def test_smart_sync_module_removed(self):
        """Test that smart_sync.py is removed."""
        smart_sync_path = Path("src/smart_sync.py")
        assert not smart_sync_path.exists(), "src/smart_sync.py should be removed"
    
    def test_fatal_sync_checker_removed(self):
        """Test that fatal_sync_checker.py is removed."""
        fatal_sync_path = Path("src/fatal_sync_checker.py")
        assert not fatal_sync_path.exists(), "src/fatal_sync_checker.py should be removed"
    
    def test_smart_sync_imports_removed(self):
        """Test that imports of smart_sync are removed from other modules."""
        # Check core.py doesn't import smart_sync
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                assert "from smart_sync" not in content, "smart_sync import should be removed from core.py"
                assert "import smart_sync" not in content, "smart_sync import should be removed from core.py"
        
        # Check run.py doesn't import smart_sync
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                assert "from smart_sync" not in content, "smart_sync import should be removed from run.py"
                assert "import smart_sync" not in content, "smart_sync import should be removed from run.py"


class TestDockerUtilitiesRemoval:
    """Test that Docker utility components are properly removed."""
    
    def test_docker_validation_removed(self):
        """Test that docker_validation.py is removed."""
        docker_validation_path = Path("utils/docker_validation.py")
        assert not docker_validation_path.exists(), "utils/docker_validation.py should be removed"
    
    def test_docker_validation_imports_removed(self):
        """Test that imports of docker_validation are removed."""
        # Check that no files import docker_validation
        for py_file in Path(".").rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue  # Skip test files
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    assert "from utils.docker_validation" not in content, f"docker_validation import found in {py_file}"
                    assert "import utils.docker_validation" not in content, f"docker_validation import found in {py_file}"
            except (UnicodeDecodeError, PermissionError):
                continue  # Skip binary or protected files


class TestPlatformLaunchersRemoval:
    """Test that platform-specific launchers are properly removed."""
    
    def test_mac_launcher_removed(self):
        """Test that run.mac.command is removed."""
        mac_launcher_path = Path("run.mac.command")
        assert not mac_launcher_path.exists(), "run.mac.command should be removed"
    
    def test_windows_launcher_removed(self):
        """Test that run.windows.bat is removed."""
        windows_launcher_path = Path("run.windows.bat")
        assert not windows_launcher_path.exists(), "run.windows.bat should be removed"


class TestSystemFunctionalityWithoutDocker:
    """Test that core system functionality works without Docker components."""
    
    def test_core_module_imports_successfully(self):
        """Test that core module can be imported without Docker dependencies."""
        try:
            import core
            assert True, "core module should import successfully"
        except ImportError as e:
            pytest.fail(f"core module failed to import: {e}")
    
    def test_git_update_manager_works(self):
        """Test that git update manager works without Docker dependencies."""
        try:
            from git_update_manager import GitUpdateManager
            # Basic instantiation test
            manager = GitUpdateManager("test_repo", "test_branch")
            assert manager is not None, "GitUpdateManager should instantiate successfully"
        except ImportError as e:
            pytest.fail(f"GitUpdateManager failed to import: {e}")
    
    def test_scripts_updater_works(self):
        """Test that scripts updater works without Docker dependencies."""
        try:
            from scripts_updater import ScriptsUpdater
            assert True, "ScriptsUpdater should import successfully"
        except ImportError as e:
            pytest.fail(f"ScriptsUpdater failed to import: {e}")
    
    def test_workflow_utils_works(self):
        """Test that workflow utilities work without Docker dependencies."""
        try:
            from workflow_utils import get_workflow_template_path, get_workflow_type_display, validate_workflow_type
            assert True, "workflow_utils functions should import successfully"
        except ImportError as e:
            pytest.fail(f"workflow_utils functions failed to import: {e}")


class TestImportReferencesRemoved:
    """Test that broken import references are properly removed (Phase A2 scope)."""
    
    def test_no_broken_imports_in_run_py(self):
        """Test that run.py has no broken imports to deleted components."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for imports of deleted components
                broken_imports = [
                    'from utils.branch_utils import',
                    'import utils.branch_utils',
                    'from src.fatal_sync_checker import',
                    'import src.fatal_sync_checker'
                ]
                for broken_import in broken_imports:
                    assert broken_import not in content, f"Broken import '{broken_import}' found in run.py"
    
    def test_no_broken_imports_in_core_py(self):
        """Test that core.py has no broken imports to deleted components."""
        core_path = Path("src/core.py")
        if core_path.exists():
            with open(core_path, 'r') as f:
                content = f.read()
                # Check for imports of deleted components
                broken_imports = [
                    'from src.smart_sync import',
                    'import src.smart_sync'
                ]
                for broken_import in broken_imports:
                    assert broken_import not in content, f"Broken import '{broken_import}' found in core.py"
    
    def test_no_broken_imports_in_app_py(self):
        """Test that app.py has no broken imports to deleted components."""
        app_path = Path("app.py")
        if app_path.exists():
            with open(app_path, 'r') as f:
                content = f.read()
                # Check for imports of deleted components
                broken_imports = [
                    'from utils.docker_validation import',
                    'import utils.docker_validation'
                ]
                for broken_import in broken_imports:
                    assert broken_import not in content, f"Broken import '{broken_import}' found in app.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])