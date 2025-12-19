"""
Test user permission validation for Docker environment.

This test suite validates user permission handling, file ownership,
and shared network drive compatibility scenarios.
"""

import pytest
import os
import tempfile
import shutil
import stat
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.docker_validation import (
    check_write_permissions,
    get_docker_environment_info,
    is_docker_environment
)


class TestUserPermissionValidation:
    """Test user permission validation functionality."""
    
    @pytest.fixture
    def permission_test_structure(self):
        """Create a test structure for permission testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test structure
        test_structure = {
            'root': temp_dir,
            'directories': {
                'shared_data': os.path.join(temp_dir, 'shared_data'),
                'user_data': os.path.join(temp_dir, 'user_data'),
                'readonly_data': os.path.join(temp_dir, 'readonly_data'),
                'scripts': os.path.join(temp_dir, 'scripts'),
                'output': os.path.join(temp_dir, 'output'),
            },
            'files': {}
        }
        
        # Create directories
        for dir_name, dir_path in test_structure['directories'].items():
            os.makedirs(dir_path, exist_ok=True)
        
        # Create test files
        test_files = {
            'shared_config': os.path.join(test_structure['directories']['shared_data'], 'config.yml'),
            'user_data_file': os.path.join(test_structure['directories']['user_data'], 'user_data.csv'),
            'readonly_file': os.path.join(test_structure['directories']['readonly_data'], 'readonly.txt'),
            'script_file': os.path.join(test_structure['directories']['scripts'], 'analysis.py'),
            'output_file': os.path.join(test_structure['directories']['output'], 'results.json'),
        }
        
        # Create test files with content
        file_contents = {
            'shared_config': "# Shared configuration\nproject: ESP_Analysis\nversion: 1.0\n",
            'user_data_file': "id,value\n1,10.5\n2,11.2\n",
            'readonly_file': "This is readonly data\nDo not modify\n",
            'script_file': "#!/usr/bin/env python3\n# Analysis script\nprint('Running analysis')\n",
            'output_file': '{"status": "completed", "results": [1, 2, 3]}'
        }
        
        # Write test files
        for file_key, file_path in test_files.items():
            content = file_contents.get(file_key, f"# Test content for {file_key}\n")
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Set special permissions
        # Make script executable
        os.chmod(test_files['script_file'], 0o755)
        
        # Make readonly file readonly (but still owned by current user)
        os.chmod(test_files['readonly_file'], 0o444)
        
        test_structure['files'] = test_files
        
        yield test_structure
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_current_user_info(self):
        """Test current user information detection."""
        env_info = get_docker_environment_info()
        
        # Validate user information
        assert 'user_id' in env_info
        assert 'group_id' in env_info
        
        user_id = env_info['user_id']
        group_id = env_info['group_id']
        
        # In native environment, should have valid user/group IDs
        if not is_docker_environment():
            assert isinstance(user_id, int), f"User ID should be integer: {user_id}"
            assert isinstance(group_id, int), f"Group ID should be integer: {group_id}"
            assert user_id > 0, f"User ID should be positive: {user_id}"
            assert group_id > 0, f"Group ID should be positive: {group_id}"
        
        print(f"DEBUG: Current user ID: {user_id}")
        print(f"DEBUG: Current group ID: {group_id}")
        print(f"DEBUG: Environment variables: {env_info['environment_variables']}")
    
    def test_file_ownership_detection(self, permission_test_structure):
        """Test file ownership detection."""
        files = permission_test_structure['files']
        
        # Test file ownership for each test file
        for file_name, file_path in files.items():
            file_stat = os.stat(file_path)
            
            # Get file ownership info
            file_uid = file_stat.st_uid
            file_gid = file_stat.st_gid
            file_mode = file_stat.st_mode
            
            # Validate ownership info
            assert isinstance(file_uid, int), f"File UID should be integer: {file_uid}"
            assert isinstance(file_gid, int), f"File GID should be integer: {file_gid}"
            assert file_uid >= 0, f"File UID should be non-negative: {file_uid}"
            assert file_gid >= 0, f"File GID should be non-negative: {file_gid}"
            
            # Check if current user owns the file
            current_uid = os.getuid() if hasattr(os, 'getuid') else None
            if current_uid is not None:
                owns_file = (file_uid == current_uid)
                print(f"DEBUG: {file_name} - UID: {file_uid}, Current: {current_uid}, Owns: {owns_file}")
            
            # Check file permissions
            is_readable = bool(file_mode & stat.S_IRUSR)
            is_writable = bool(file_mode & stat.S_IWUSR)
            is_executable = bool(file_mode & stat.S_IXUSR)
            
            print(f"DEBUG: {file_name} permissions - R: {is_readable}, W: {is_writable}, X: {is_executable}")
    
    def test_write_permission_scenarios(self, permission_test_structure):
        """Test various write permission scenarios."""
        directories = permission_test_structure['directories']
        
        # Test write permissions in different scenarios
        permission_results = {}
        
        for dir_name, dir_path in directories.items():
            # Test write permissions
            has_write = check_write_permissions(dir_path, required=False)
            permission_results[dir_name] = has_write
            
            print(f"DEBUG: {dir_name} write permissions: {has_write}")
            
            # In native environment with proper setup, most should be writable
            if dir_name != 'readonly_data':  # readonly_data might have restricted permissions
                assert isinstance(has_write, bool)
        
        # Validate that we got results for all directories
        assert len(permission_results) == len(directories)
    
    def test_shared_network_drive_simulation(self, permission_test_structure):
        """Test shared network drive compatibility simulation."""
        project_root = permission_test_structure['root']
        
        # Simulate shared network drive scenarios
        def simulate_network_drive_permissions(path):
            """Simulate network drive permission checking."""
            try:
                # Test file creation
                test_file = os.path.join(path, '.network_test')
                with open(test_file, 'w') as f:
                    f.write("Network drive test")
                
                # Test file reading
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Test file modification
                with open(test_file, 'a') as f:
                    f.write("\nModified")
                
                # Test file deletion
                os.remove(test_file)
                
                return {
                    'create': True,
                    'read': True,
                    'modify': True,
                    'delete': True,
                    'error': None
                }
                
            except PermissionError as e:
                return {
                    'create': False,
                    'read': False,
                    'modify': False,
                    'delete': False,
                    'error': f"Permission error: {e}"
                }
            except Exception as e:
                return {
                    'create': False,
                    'read': False,
                    'modify': False,
                    'delete': False,
                    'error': f"Other error: {e}"
                }
        
        # Test network drive simulation
        network_result = simulate_network_drive_permissions(project_root)
        
        print(f"DEBUG: Network drive simulation result: {network_result}")
        
        # In native environment, should typically succeed
        assert isinstance(network_result, dict)
        assert 'create' in network_result
        assert 'read' in network_result
        assert 'modify' in network_result
        assert 'delete' in network_result
        assert 'error' in network_result
    
    def test_collaborative_access_simulation(self, permission_test_structure):
        """Test collaborative access scenarios."""
        files = permission_test_structure['files']
        
        def simulate_collaborative_access(file_path):
            """Simulate collaborative file access."""
            try:
                # Simulate user A creates/modifies file
                with open(file_path, 'a') as f:
                    f.write(f"\n# Modified by user A at {os.getpid()}")
                
                # Check if file is accessible for reading (user B)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Simulate user B modifies file
                with open(file_path, 'a') as f:
                    f.write(f"\n# Modified by user B at {os.getpid()}")
                
                return {
                    'user_a_write': True,
                    'user_b_read': True,
                    'user_b_write': True,
                    'collaborative': True,
                    'error': None
                }
                
            except PermissionError as e:
                return {
                    'user_a_write': False,
                    'user_b_read': False,
                    'user_b_write': False,
                    'collaborative': False,
                    'error': f"Permission error: {e}"
                }
            except Exception as e:
                return {
                    'user_a_write': False,
                    'user_b_read': False,
                    'user_b_write': False,
                    'collaborative': False,
                    'error': f"Other error: {e}"
                }
        
        # Test collaborative access for writable files
        collaborative_results = {}
        
        for file_name, file_path in files.items():
            if file_name != 'readonly_file':  # Skip readonly file
                result = simulate_collaborative_access(file_path)
                collaborative_results[file_name] = result
                
                print(f"DEBUG: {file_name} collaborative access: {result}")
        
        # Validate results
        assert len(collaborative_results) > 0
        for file_name, result in collaborative_results.items():
            assert isinstance(result, dict)
            assert 'collaborative' in result
    
    def test_docker_user_mapping_simulation(self):
        """Test Docker user mapping simulation."""
        # Get current user info
        env_info = get_docker_environment_info()
        current_uid = env_info.get('user_id')
        current_gid = env_info.get('group_id')
        
        # Simulate Docker user mapping scenarios
        def simulate_docker_user_mapping(host_uid, host_gid, container_uid, container_gid):
            """Simulate Docker user ID mapping."""
            mapping_info = {
                'host_user': {'uid': host_uid, 'gid': host_gid},
                'container_user': {'uid': container_uid, 'gid': container_gid},
                'mapping_correct': (host_uid == container_uid and host_gid == container_gid),
                'potential_issues': []
            }
            
            # Check for potential issues
            if host_uid != container_uid:
                mapping_info['potential_issues'].append(
                    f"UID mismatch: host {host_uid} != container {container_uid}"
                )
            
            if host_gid != container_gid:
                mapping_info['potential_issues'].append(
                    f"GID mismatch: host {host_gid} != container {container_gid}"
                )
            
            if container_uid == 0:
                mapping_info['potential_issues'].append(
                    "Container running as root - potential permission issues"
                )
            
            return mapping_info
        
        # Test various mapping scenarios
        test_scenarios = [
            # Correct mapping
            (current_uid, current_gid, current_uid, current_gid),
            # Root container (problematic)
            (current_uid, current_gid, 0, 0),
            # Different user mapping (problematic)
            (current_uid, current_gid, 1000, 1000),
        ]
        
        for i, (host_uid, host_gid, container_uid, container_gid) in enumerate(test_scenarios):
            mapping_result = simulate_docker_user_mapping(host_uid, host_gid, container_uid, container_gid)
            
            print(f"DEBUG: Scenario {i+1} mapping result: {mapping_result}")
            
            # Validate mapping result structure
            assert isinstance(mapping_result, dict)
            assert 'host_user' in mapping_result
            assert 'container_user' in mapping_result
            assert 'mapping_correct' in mapping_result
            assert 'potential_issues' in mapping_result
            
            # First scenario should be correct mapping
            if i == 0:
                assert mapping_result['mapping_correct'], "First scenario should have correct mapping"
                assert len(mapping_result['potential_issues']) == 0, "First scenario should have no issues"


class TestFileOwnershipScenarios:
    """Test file ownership scenarios for Docker compatibility."""
    
    @pytest.fixture
    def ownership_test_files(self):
        """Create files for ownership testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files with different purposes
        test_files = {
            'config_file': os.path.join(temp_dir, 'config.yml'),
            'data_file': os.path.join(temp_dir, 'data.csv'),
            'script_file': os.path.join(temp_dir, 'script.py'),
            'output_file': os.path.join(temp_dir, 'output.json'),
            'log_file': os.path.join(temp_dir, 'workflow.log'),
        }
        
        # Create files with content
        for file_name, file_path in test_files.items():
            with open(file_path, 'w') as f:
                f.write(f"# Test content for {file_name}\n")
        
        # Make script executable
        os.chmod(test_files['script_file'], 0o755)
        
        yield {'root': temp_dir, 'files': test_files}
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_file_creation_ownership(self, ownership_test_files):
        """Test file creation and ownership."""
        temp_dir = ownership_test_files['root']
        
        # Create new files and check ownership
        new_files = {
            'new_config': os.path.join(temp_dir, 'new_config.yml'),
            'new_data': os.path.join(temp_dir, 'new_data.csv'),
            'new_output': os.path.join(temp_dir, 'new_output.json'),
        }
        
        current_uid = os.getuid() if hasattr(os, 'getuid') else None
        current_gid = os.getgid() if hasattr(os, 'getgid') else None
        
        for file_name, file_path in new_files.items():
            # Create file
            with open(file_path, 'w') as f:
                f.write(f"# Newly created {file_name}\n")
            
            # Check ownership
            file_stat = os.stat(file_path)
            file_uid = file_stat.st_uid
            file_gid = file_stat.st_gid
            
            print(f"DEBUG: {file_name} - UID: {file_uid}, GID: {file_gid}")
            
            # In native environment, new files should be owned by current user
            if current_uid is not None:
                assert file_uid == current_uid, f"New file should be owned by current user: {file_name}"
            if current_gid is not None:
                assert file_gid == current_gid, f"New file should have current group: {file_name}"
    
    def test_permission_inheritance(self, ownership_test_files):
        """Test permission inheritance in directories."""
        temp_dir = ownership_test_files['root']
        
        # Create subdirectory
        subdir = os.path.join(temp_dir, 'subdir')
        os.makedirs(subdir, exist_ok=True)
        
        # Create file in subdirectory
        subfile = os.path.join(subdir, 'subfile.txt')
        with open(subfile, 'w') as f:
            f.write("File in subdirectory\n")
        
        # Check permissions
        dir_stat = os.stat(subdir)
        file_stat = os.stat(subfile)
        
        # Validate that subdirectory and file have appropriate permissions
        dir_mode = dir_stat.st_mode
        file_mode = file_stat.st_mode
        
        # Directory should be readable and executable by owner
        assert bool(dir_mode & stat.S_IRUSR), "Directory should be readable by owner"
        assert bool(dir_mode & stat.S_IXUSR), "Directory should be executable by owner"
        
        # File should be readable by owner
        assert bool(file_mode & stat.S_IRUSR), "File should be readable by owner"
        
        print(f"DEBUG: Subdirectory permissions: {oct(dir_mode)}")
        print(f"DEBUG: Subfile permissions: {oct(file_mode)}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])