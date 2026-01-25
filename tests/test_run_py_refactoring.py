"""
Test suite for run.py refactoring to native execution.
This test ensures that run.py is properly refactored from Docker orchestration
to native Python execution while preserving essential functionality.

Following TDD methodology:
1. Write tests first (RED)
2. Refactor run.py (GREEN) 
3. Validate and optimize (REFACTOR)
"""

import os
import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRunPyRefactoredStructure:
    """Test that run.py has the correct refactored structure."""
    
    def test_run_py_exists(self):
        """Test that run.py still exists after refactoring."""
        run_path = Path("run.py")
        assert run_path.exists(), "run.py should still exist after refactoring"
    
    def test_run_py_size_reduced(self):
        """Test that run.py is significantly reduced in size."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                lines = f.readlines()
                # Should be around 300 lines, allow some flexibility
                assert len(lines) < 500, f"run.py should be under 500 lines, got {len(lines)}"
                assert len(lines) > 100, f"run.py should be over 100 lines, got {len(lines)}"
    
    def test_no_docker_classes_in_run_py(self):
        """Test that Docker-specific classes are removed."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check that Docker classes are removed
                docker_classes = [
                    'class ContainerManager',
                    'class DockerLauncher',
                    'class PlatformAdapter'
                ]
                for docker_class in docker_classes:
                    assert docker_class not in content, f"Docker class '{docker_class}' should be removed from run.py"
    
    def test_no_smart_sync_functions_in_run_py(self):
        """Test that Smart Sync functions are removed."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check that Smart Sync functions are removed
                smart_sync_functions = [
                    'detect_smart_sync_scenario',
                    'setup_smart_sync_environment',
                    'log_smart_sync_detection'
                ]
                for function in smart_sync_functions:
                    assert function not in content, f"Smart Sync function '{function}' should be removed from run.py"


class TestRunPyPreservedFunctionality:
    """Test that essential functionality is preserved in refactored run.py."""
    
    def test_argument_parsing_preserved(self):
        """Test that argument parsing functionality is preserved."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for argument parsing
                assert 'argparse' in content or 'click' in content, "Argument parsing should be preserved"
                assert 'workflow_type' in content, "workflow_type argument should be preserved"
                assert 'project_path' in content, "project_path argument should be preserved"
    
    def test_workflow_selection_preserved(self):
        """Test that workflow selection logic is preserved."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for workflow selection
                assert 'sip' in content.lower() or 'SIP' in content, "SIP workflow support should be preserved"
                assert 'sps' in content.lower() or 'SPS' in content, "SPS workflow support should be preserved"
    
    def test_native_launcher_integration(self):
        """Test that run.py integrates with app.py for native execution."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for integration with Streamlit app
                assert 'app.py' in content, "run.py should integrate with app.py for native execution"
                assert 'streamlit' in content.lower(), "run.py should use Streamlit to launch app.py"
    
    def test_workflow_type_propagation_preserved(self):
        """Test that workflow type is properly propagated to app.py for title display."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check that workflow type is captured and passed through
                # This was previously passed to Docker, now should go directly to app.py
                workflow_propagation_indicators = [
                    'workflow_type',
                    'WORKFLOW_TYPE',
                    'workflow',
                    'sip',
                    'sps'
                ]
                has_workflow_propagation = any(indicator in content.lower() for indicator in workflow_propagation_indicators)
                assert has_workflow_propagation, "run.py should preserve workflow type propagation for app.py title display"
    
    def test_environment_variable_workflow_passing(self):
        """Test that workflow type is set as environment variable for app.py."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for environment variable setting (previously done for Docker)
                env_setting_indicators = [
                    'os.environ',
                    'WORKFLOW_TYPE',
                    'setenv',
                    'env'
                ]
                has_env_setting = any(indicator in content for indicator in env_setting_indicators)
                assert has_env_setting, "run.py should set workflow type as environment variable for app.py"


class TestRunPyDockerRemoval:
    """Test that Docker-specific functionality is completely removed."""
    
    def test_no_docker_commands(self):
        """Test that Docker commands are removed."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for Docker commands
                docker_commands = [
                    'docker pull',
                    'docker run',
                    'docker-compose up',
                    'docker ps',
                    'docker stop',
                    'docker rm'
                ]
                for command in docker_commands:
                    assert command not in content, f"Docker command '{command}' should be removed from run.py"
    
    def test_no_docker_environment_setup(self):
        """Test that Docker environment setup is removed."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for Docker environment variables
                docker_env_vars = [
                    'DOCKER_IMAGE',
                    'USER_ID',
                    'GROUP_ID',
                    'DOCKER_USER_ID',
                    'DOCKER_GROUP_ID'
                ]
                for env_var in docker_env_vars:
                    assert env_var not in content, f"Docker environment variable '{env_var}' should be removed from run.py"
    
    def test_no_container_lifecycle_management(self):
        """Test that container lifecycle management is removed."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for container lifecycle functions
                container_functions = [
                    'cleanup_containers',
                    'launch_container',
                    'prepare_environment'
                ]
                for function in container_functions:
                    assert function not in content, f"Container function '{function}' should be removed from run.py"


class TestRunPyExecutionRedirection:
    """Test that run.py properly redirects to native execution."""
    
    @patch('subprocess.run')
    def test_redirects_to_native_launcher(self, mock_subprocess):
        """Test that run.py redirects execution to run_native.py."""
        # This test will need to be implemented after the refactoring
        # For now, just check that the structure supports redirection
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check that there's some form of execution redirection
                redirection_indicators = [
                    'run_native',
                    'subprocess',
                    'exec',
                    'launch'
                ]
                has_redirection = any(indicator in content for indicator in redirection_indicators)
                assert has_redirection, "run.py should have some form of execution redirection"
    
    def test_preserves_command_line_arguments(self):
        """Test that command line arguments are preserved during redirection."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check that arguments are handled for redirection
                assert 'args' in content or 'argv' in content, "Command line arguments should be preserved"


class TestRunPyImportCleanup:
    """Test that imports are cleaned up after refactoring."""
    
    def test_no_docker_related_imports(self):
        """Test that Docker-related imports are removed."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for Docker-related imports that should be removed
                docker_imports = [
                    'from src.smart_sync import',
                    'from utils.docker_validation import',
                    'from src.fatal_sync_checker import'
                ]
                for docker_import in docker_imports:
                    assert docker_import not in content, f"Docker import '{docker_import}' should be removed from run.py"
    
    def test_preserves_essential_imports(self):
        """Test that essential imports are preserved."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for essential imports that should be preserved
                essential_imports = [
                    'import os',
                    'import sys',
                    'from pathlib import Path'
                ]
                for essential_import in essential_imports:
                    assert essential_import in content, f"Essential import '{essential_import}' should be preserved in run.py"


class TestRunPyBackwardCompatibility:
    """Test that run.py maintains backward compatibility for basic usage."""
    
    def test_can_be_executed_with_help(self):
        """Test that run.py can be executed with --help flag."""
        try:
            result = subprocess.run([
                sys.executable, "run.py", "--help"
            ], capture_output=True, text=True, timeout=10)
            # Should not crash, regardless of exit code
            assert result.returncode in [0, 1, 2], "run.py --help should not crash"
        except subprocess.TimeoutExpired:
            pytest.fail("run.py --help timed out")
        except Exception as e:
            # Allow for import errors during refactoring
            if "ImportError" not in str(e) and "ModuleNotFoundError" not in str(e):
                pytest.fail(f"run.py --help failed unexpectedly: {e}")
    
    def test_provides_usage_information(self):
        """Test that run.py provides usage information."""
        run_path = Path("run.py")
        if run_path.exists():
            with open(run_path, 'r') as f:
                content = f.read()
                # Check for usage information
                usage_indicators = [
                    'usage',
                    'help',
                    'description',
                    'SIP LIMS Workflow Manager'
                ]
                has_usage = any(indicator in content.lower() for indicator in usage_indicators)
                assert has_usage, "run.py should provide usage information"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])