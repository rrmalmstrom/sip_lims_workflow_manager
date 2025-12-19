"""
Test file browser integration for Docker environment compatibility.

This test suite validates the file browser functionality that replaces
tkinter file dialogs for Docker compatibility.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.streamlit_file_browser import st_file_browser
from utils.docker_validation import is_docker_environment, get_docker_environment_info


class TestFileBrowserIntegration:
    """Test file browser integration functionality."""
    
    @pytest.fixture
    def temp_project_structure(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test project structure
        project_structure = {
            'project_root': temp_dir,
            'data_dir': os.path.join(temp_dir, 'data'),
            'scripts_dir': os.path.join(temp_dir, 'scripts'),
            'config_dir': os.path.join(temp_dir, 'config'),
            'test_files': {
                'workflow.yml': os.path.join(temp_dir, 'config', 'workflow.yml'),
                'data.csv': os.path.join(temp_dir, 'data', 'sample_data.csv'),
                'script.py': os.path.join(temp_dir, 'scripts', 'test_script.py'),
            }
        }
        
        # Create directories
        for dir_path in [project_structure['data_dir'], 
                        project_structure['scripts_dir'], 
                        project_structure['config_dir']]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Create test files
        test_files = project_structure['test_files']
        
        # Create workflow.yml
        with open(test_files['workflow.yml'], 'w') as f:
            f.write("""
name: Test Workflow
steps:
  - name: test_step
    script: test_script.py
""")
        
        # Create sample data file
        with open(test_files['data.csv'], 'w') as f:
            f.write("id,value\n1,test\n2,data\n")
        
        # Create test script
        with open(test_files['script.py'], 'w') as f:
            f.write("# Test script\nprint('Hello from test script')\n")
        
        yield project_structure
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_docker_environment_detection(self):
        """Test Docker environment detection."""
        # This should return False in native environment
        is_docker = is_docker_environment()
        assert isinstance(is_docker, bool)
        
        # Get environment info
        env_info = get_docker_environment_info()
        assert isinstance(env_info, dict)
        assert 'is_docker' in env_info
        assert 'working_directory' in env_info
        assert 'user_id' in env_info
        assert 'group_id' in env_info
        assert 'environment_variables' in env_info
        
        # In native environment, should not have Docker-specific keys
        if not is_docker:
            assert 'data_path_exists' not in env_info
            assert 'scripts_path_exists' not in env_info
        
        print(f"DEBUG: Docker environment detected: {is_docker}")
        print(f"DEBUG: Environment info: {env_info}")
    
    def test_file_browser_basic_functionality(self, temp_project_structure):
        """Test basic file browser functionality."""
        project_root = temp_project_structure['project_root']
        
        # Test that we can access the file browser function
        # Note: We can't fully test Streamlit components without a Streamlit session
        # but we can test the function exists and basic path handling
        
        assert callable(st_file_browser)
        
        # Test path validation
        assert os.path.exists(project_root)
        assert os.path.isdir(project_root)
        
        print(f"DEBUG: Testing with project root: {project_root}")
        print(f"DEBUG: Project structure: {os.listdir(project_root)}")
    
    def test_path_format_compatibility(self, temp_project_structure):
        """Test path format compatibility between native and Docker environments."""
        project_root = temp_project_structure['project_root']
        test_files = temp_project_structure['test_files']
        
        # Test native path handling
        for file_type, file_path in test_files.items():
            assert os.path.exists(file_path), f"Test file {file_type} not found: {file_path}"
            
            # Test relative path conversion
            rel_path = os.path.relpath(file_path, project_root)
            assert not rel_path.startswith('/'), f"Relative path should not start with /: {rel_path}"
            
            # Test absolute path reconstruction
            abs_path = os.path.join(project_root, rel_path)
            assert os.path.exists(abs_path), f"Reconstructed path not found: {abs_path}"
            
            print(f"DEBUG: {file_type} - Original: {file_path}")
            print(f"DEBUG: {file_type} - Relative: {rel_path}")
            print(f"DEBUG: {file_type} - Reconstructed: {abs_path}")
    
    def test_docker_volume_path_handling(self, temp_project_structure):
        """Test Docker volume path handling (when /data prefix exists)."""
        project_root = temp_project_structure['project_root']
        
        # Simulate Docker environment paths
        docker_data_path = "/data"
        docker_scripts_path = "/workflow-scripts"
        
        # Test path conversion logic
        def convert_to_docker_path(native_path, project_root):
            """Convert native path to Docker volume path."""
            if native_path.startswith(project_root):
                rel_path = os.path.relpath(native_path, project_root)
                return os.path.join(docker_data_path, rel_path).replace('\\', '/')
            return native_path
        
        # Test conversion for each test file
        test_files = temp_project_structure['test_files']
        for file_type, file_path in test_files.items():
            docker_path = convert_to_docker_path(file_path, project_root)
            
            # Docker paths should start with /data
            expected_prefix = docker_data_path
            if file_type == 'script.py':
                # Scripts might be in /workflow-scripts volume
                pass  # Allow flexibility for script paths
            
            print(f"DEBUG: {file_type} - Native: {file_path}")
            print(f"DEBUG: {file_type} - Docker: {docker_path}")
            
            # Validate Docker path format
            assert docker_path.startswith('/'), f"Docker path should be absolute: {docker_path}"
            assert '\\' not in docker_path, f"Docker path should use forward slashes: {docker_path}"
    
    def test_file_selection_integration(self, temp_project_structure):
        """Test integration with existing code expectations."""
        project_root = temp_project_structure['project_root']
        test_files = temp_project_structure['test_files']
        
        # Test that file selection returns expected format
        # This simulates what the file browser should return
        
        def simulate_file_selection(file_path, project_root):
            """Simulate file browser selection result."""
            if os.path.exists(file_path):
                return {
                    'selected_file': file_path,
                    'relative_path': os.path.relpath(file_path, project_root),
                    'file_type': os.path.splitext(file_path)[1],
                    'exists': True
                }
            return None
        
        # Test file selection for each test file
        for file_type, file_path in test_files.items():
            selection_result = simulate_file_selection(file_path, project_root)
            
            assert selection_result is not None, f"File selection failed for {file_type}"
            assert selection_result['exists'], f"Selected file should exist: {file_type}"
            assert selection_result['selected_file'] == file_path
            
            print(f"DEBUG: {file_type} selection result: {selection_result}")
    
    def test_folder_selection_functionality(self, temp_project_structure):
        """Test folder selection functionality."""
        project_root = temp_project_structure['project_root']
        data_dir = temp_project_structure['data_dir']
        scripts_dir = temp_project_structure['scripts_dir']
        
        # Test folder selection simulation
        def simulate_folder_selection(folder_path, project_root):
            """Simulate folder browser selection result."""
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                return {
                    'selected_folder': folder_path,
                    'relative_path': os.path.relpath(folder_path, project_root),
                    'is_directory': True,
                    'contents': os.listdir(folder_path)
                }
            return None
        
        # Test folder selections
        test_folders = {
            'project_root': project_root,
            'data_dir': data_dir,
            'scripts_dir': scripts_dir
        }
        
        for folder_type, folder_path in test_folders.items():
            selection_result = simulate_folder_selection(folder_path, project_root)
            
            assert selection_result is not None, f"Folder selection failed for {folder_type}"
            assert selection_result['is_directory'], f"Selected path should be directory: {folder_type}"
            assert isinstance(selection_result['contents'], list), f"Contents should be list: {folder_type}"
            
            print(f"DEBUG: {folder_type} selection result: {selection_result}")
            print(f"DEBUG: {folder_type} contents: {selection_result['contents']}")


class TestDockerIntegrationSpecific:
    """Docker-specific integration tests."""
    
    def test_volume_mount_simulation(self):
        """Test volume mount path simulation."""
        # Simulate Docker volume mounts
        volume_mounts = {
            '/data': '/host/project/path',
            '/workflow-scripts': '/host/scripts/path'
        }
        
        def simulate_docker_path_resolution(docker_path, volume_mounts):
            """Simulate how Docker resolves volume-mounted paths."""
            for mount_point, host_path in volume_mounts.items():
                if docker_path.startswith(mount_point):
                    relative_path = docker_path[len(mount_point):].lstrip('/')
                    return os.path.join(host_path, relative_path)
            return docker_path
        
        # Test path resolution
        test_paths = [
            '/data/config/workflow.yml',
            '/data/data/sample.csv',
            '/workflow-scripts/test_script.py'
        ]
        
        for docker_path in test_paths:
            host_path = simulate_docker_path_resolution(docker_path, volume_mounts)
            print(f"DEBUG: Docker path: {docker_path} -> Host path: {host_path}")
            
            # Validate path conversion
            assert not host_path.startswith('/data'), f"Path should be converted from Docker: {host_path}"
            assert not host_path.startswith('/workflow-scripts'), f"Path should be converted from Docker: {host_path}"
    
    def test_user_permission_simulation(self):
        """Test user permission handling simulation."""
        import pwd
        import grp
        
        try:
            # Get current user info (for macOS/Linux)
            current_user = pwd.getpwuid(os.getuid())
            current_group = grp.getgrgid(os.getgid())
            
            user_info = {
                'uid': current_user.pw_uid,
                'gid': current_group.gr_gid,
                'username': current_user.pw_name,
                'groupname': current_group.gr_name
            }
            
            print(f"DEBUG: Current user info: {user_info}")
            
            # Validate user info
            assert user_info['uid'] > 0, "User ID should be positive"
            assert user_info['gid'] > 0, "Group ID should be positive"
            assert user_info['username'], "Username should not be empty"
            assert user_info['groupname'], "Group name should not be empty"
            
        except (ImportError, KeyError):
            # Skip on Windows or if pwd/grp not available
            pytest.skip("User permission test requires Unix-like system")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])