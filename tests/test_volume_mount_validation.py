"""
Test volume mount validation for Docker environment.

This test suite validates volume mount functionality with various
project directory structures and cross-platform compatibility.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.docker_validation import (
    validate_volume_mounts,
    is_mount_point,
    check_write_permissions,
    get_docker_environment_info
)


class TestVolumeMountValidation:
    """Test volume mount validation functionality."""
    
    @pytest.fixture
    def complex_project_structure(self):
        """Create a complex project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create complex nested structure
        project_structure = {
            'root': temp_dir,
            'directories': {
                'data': os.path.join(temp_dir, 'data'),
                'data_raw': os.path.join(temp_dir, 'data', 'raw'),
                'data_processed': os.path.join(temp_dir, 'data', 'processed'),
                'data_results': os.path.join(temp_dir, 'data', 'results'),
                'scripts': os.path.join(temp_dir, 'scripts'),
                'scripts_analysis': os.path.join(temp_dir, 'scripts', 'analysis'),
                'scripts_utils': os.path.join(temp_dir, 'scripts', 'utils'),
                'config': os.path.join(temp_dir, 'config'),
                'logs': os.path.join(temp_dir, 'logs'),
                'temp': os.path.join(temp_dir, 'temp'),
            },
            'files': {}
        }
        
        # Create all directories
        for dir_name, dir_path in project_structure['directories'].items():
            os.makedirs(dir_path, exist_ok=True)
        
        # Create test files in various locations
        test_files = {
            'workflow_main': os.path.join(project_structure['directories']['config'], 'workflow.yml'),
            'workflow_analysis': os.path.join(project_structure['directories']['config'], 'analysis_workflow.yml'),
            'raw_data_1': os.path.join(project_structure['directories']['data_raw'], 'sample1.csv'),
            'raw_data_2': os.path.join(project_structure['directories']['data_raw'], 'sample2.csv'),
            'processed_data': os.path.join(project_structure['directories']['data_processed'], 'cleaned_data.csv'),
            'results': os.path.join(project_structure['directories']['data_results'], 'analysis_results.json'),
            'main_script': os.path.join(project_structure['directories']['scripts'], 'main_analysis.py'),
            'analysis_script': os.path.join(project_structure['directories']['scripts_analysis'], 'statistical_analysis.py'),
            'utils_script': os.path.join(project_structure['directories']['scripts_utils'], 'data_utils.py'),
            'log_file': os.path.join(project_structure['directories']['logs'], 'workflow.log'),
        }
        
        # Create test files with realistic content
        file_contents = {
            'workflow_main': """
name: Main ESP Workflow
description: Primary analysis workflow for ESP data
steps:
  - name: data_preparation
    script: scripts/main_analysis.py
    input: data/raw/
    output: data/processed/
  - name: statistical_analysis
    script: scripts/analysis/statistical_analysis.py
    input: data/processed/
    output: data/results/
""",
            'workflow_analysis': """
name: Statistical Analysis Workflow
description: Detailed statistical analysis for ESP results
steps:
  - name: load_data
    script: scripts/utils/data_utils.py
  - name: analyze
    script: scripts/analysis/statistical_analysis.py
""",
            'raw_data_1': "id,value,timestamp\n1,10.5,2023-01-01\n2,11.2,2023-01-02\n",
            'raw_data_2': "id,value,timestamp\n3,9.8,2023-01-03\n4,12.1,2023-01-04\n",
            'processed_data': "id,normalized_value,category\n1,0.85,A\n2,0.92,A\n3,0.78,B\n4,1.0,A\n",
            'results': '{"mean": 10.65, "std": 0.95, "categories": {"A": 3, "B": 1}}',
            'main_script': "# Main analysis script\nimport pandas as pd\nprint('Running main analysis')\n",
            'analysis_script': "# Statistical analysis\nimport numpy as np\nprint('Running statistical analysis')\n",
            'utils_script': "# Data utilities\ndef load_data(path):\n    return pd.read_csv(path)\n",
            'log_file': "2023-01-01 10:00:00 - Workflow started\n2023-01-01 10:05:00 - Data loaded\n"
        }
        
        # Write all test files
        for file_key, file_path in test_files.items():
            content = file_contents.get(file_key, f"# Test content for {file_key}\n")
            with open(file_path, 'w') as f:
                f.write(content)
        
        project_structure['files'] = test_files
        
        yield project_structure
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_volume_mount_validation_native(self):
        """Test volume mount validation in native environment."""
        # In native environment, Docker volume paths shouldn't exist
        volume_status = validate_volume_mounts()
        
        # Should return a dictionary
        assert isinstance(volume_status, dict)
        
        # In native environment, Docker volumes shouldn't exist
        expected_volumes = ["/data", "/workflow-scripts"]
        for volume in expected_volumes:
            if volume in volume_status:
                # In native environment, these should typically be False
                # unless someone created these directories manually
                assert isinstance(volume_status[volume], bool)
        
        print(f"DEBUG: Volume status in native environment: {volume_status}")
    
    def test_mount_point_detection(self, complex_project_structure):
        """Test mount point detection functionality."""
        project_root = complex_project_structure['root']
        directories = complex_project_structure['directories']
        
        # Test mount point detection on regular directories
        # In native environment, these should not be mount points
        for dir_name, dir_path in directories.items():
            is_mount = is_mount_point(dir_path)
            # In native environment, regular directories are not mount points
            assert isinstance(is_mount, bool)
            print(f"DEBUG: {dir_name} ({dir_path}) is mount point: {is_mount}")
        
        # Test with non-existent path
        non_existent = os.path.join(project_root, "non_existent_directory")
        is_mount_nonexistent = is_mount_point(non_existent)
        assert is_mount_nonexistent == False
        print(f"DEBUG: Non-existent path is mount point: {is_mount_nonexistent}")
    
    def test_write_permissions_various_locations(self, complex_project_structure):
        """Test write permissions in various project locations."""
        directories = complex_project_structure['directories']
        
        # Test write permissions in different directories
        for dir_name, dir_path in directories.items():
            # Test write permissions (should pass in native environment)
            has_write_permission = check_write_permissions(dir_path, required=False)
            assert isinstance(has_write_permission, bool)
            
            # In native environment with proper permissions, this should be True
            if has_write_permission:
                print(f"DEBUG: Write permissions OK for {dir_name}: {dir_path}")
            else:
                print(f"DEBUG: Write permissions FAILED for {dir_name}: {dir_path}")
    
    def test_project_structure_compatibility(self, complex_project_structure):
        """Test compatibility with various project structures."""
        project_root = complex_project_structure['root']
        directories = complex_project_structure['directories']
        files = complex_project_structure['files']
        
        # Test that all expected directories exist
        for dir_name, dir_path in directories.items():
            assert os.path.exists(dir_path), f"Directory {dir_name} should exist: {dir_path}"
            assert os.path.isdir(dir_path), f"Path {dir_name} should be a directory: {dir_path}"
        
        # Test that all expected files exist
        for file_name, file_path in files.items():
            assert os.path.exists(file_path), f"File {file_name} should exist: {file_path}"
            assert os.path.isfile(file_path), f"Path {file_name} should be a file: {file_path}"
        
        # Test relative path calculations
        for file_name, file_path in files.items():
            rel_path = os.path.relpath(file_path, project_root)
            assert not rel_path.startswith('/'), f"Relative path should not start with /: {rel_path}"
            
            # Test path reconstruction
            reconstructed = os.path.join(project_root, rel_path)
            assert os.path.exists(reconstructed), f"Reconstructed path should exist: {reconstructed}"
            
            print(f"DEBUG: {file_name} - Relative: {rel_path}")
    
    def test_docker_volume_path_simulation(self, complex_project_structure):
        """Test Docker volume path simulation with complex structure."""
        project_root = complex_project_structure['root']
        files = complex_project_structure['files']
        
        def simulate_docker_volume_mapping(native_path, project_root):
            """Simulate how paths would be mapped in Docker volumes."""
            if native_path.startswith(project_root):
                rel_path = os.path.relpath(native_path, project_root)
                
                # Determine which Docker volume based on path
                if rel_path.startswith('scripts'):
                    # Scripts go to /workflow-scripts volume
                    script_rel_path = os.path.relpath(rel_path, 'scripts')
                    if script_rel_path == '.':
                        return '/workflow-scripts'
                    else:
                        return f'/workflow-scripts/{script_rel_path}'.replace('\\', '/')
                else:
                    # Everything else goes to /data volume
                    return f'/data/{rel_path}'.replace('\\', '/')
            
            return native_path
        
        # Test volume mapping for all files
        for file_name, file_path in files.items():
            docker_path = simulate_docker_volume_mapping(file_path, project_root)
            
            # Validate Docker path format
            assert docker_path.startswith('/'), f"Docker path should be absolute: {docker_path}"
            assert '\\' not in docker_path, f"Docker path should use forward slashes: {docker_path}"
            
            # Check volume assignment
            if 'script' in file_name:
                assert docker_path.startswith('/workflow-scripts'), f"Script should be in /workflow-scripts: {docker_path}"
            else:
                assert docker_path.startswith('/data'), f"Non-script should be in /data: {docker_path}"
            
            print(f"DEBUG: {file_name}")
            print(f"  Native: {file_path}")
            print(f"  Docker: {docker_path}")
    
    def test_cross_platform_path_handling(self, complex_project_structure):
        """Test cross-platform path handling."""
        project_root = complex_project_structure['root']
        files = complex_project_structure['files']
        
        def normalize_path_for_docker(path):
            """Normalize paths for Docker compatibility."""
            # Convert to forward slashes
            normalized = path.replace('\\', '/')
            
            # Ensure absolute paths start with /
            if not normalized.startswith('/'):
                normalized = '/' + normalized
            
            return normalized
        
        # Test path normalization
        for file_name, file_path in files.items():
            # Get relative path
            rel_path = os.path.relpath(file_path, project_root)
            
            # Simulate Windows-style path (with backslashes)
            windows_style = rel_path.replace('/', '\\')
            
            # Normalize for Docker
            docker_normalized = normalize_path_for_docker(windows_style)
            
            # Should be forward slashes and absolute
            assert '\\' not in docker_normalized, f"Normalized path should not have backslashes: {docker_normalized}"
            assert docker_normalized.startswith('/'), f"Normalized path should be absolute: {docker_normalized}"
            
            print(f"DEBUG: {file_name}")
            print(f"  Original relative: {rel_path}")
            print(f"  Windows style: {windows_style}")
            print(f"  Docker normalized: {docker_normalized}")


class TestScriptRepositoryMounting:
    """Test script repository mounting scenarios."""
    
    @pytest.fixture
    def script_repository_structure(self):
        """Create a script repository structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create script repository structure
        script_structure = {
            'root': temp_dir,
            'directories': {
                'analysis': os.path.join(temp_dir, 'analysis'),
                'data_processing': os.path.join(temp_dir, 'data_processing'),
                'utilities': os.path.join(temp_dir, 'utilities'),
                'workflows': os.path.join(temp_dir, 'workflows'),
                'templates': os.path.join(temp_dir, 'templates'),
            },
            'scripts': {}
        }
        
        # Create directories
        for dir_name, dir_path in script_structure['directories'].items():
            os.makedirs(dir_path, exist_ok=True)
        
        # Create script files
        scripts = {
            'main_analysis': os.path.join(script_structure['directories']['analysis'], 'main_analysis.py'),
            'statistical_test': os.path.join(script_structure['directories']['analysis'], 'statistical_test.py'),
            'data_cleaner': os.path.join(script_structure['directories']['data_processing'], 'data_cleaner.py'),
            'file_utils': os.path.join(script_structure['directories']['utilities'], 'file_utils.py'),
            'workflow_runner': os.path.join(script_structure['directories']['workflows'], 'workflow_runner.py'),
            'template_workflow': os.path.join(script_structure['directories']['templates'], 'template_workflow.yml'),
        }
        
        # Create script content
        script_contents = {
            'main_analysis': "#!/usr/bin/env python3\n# Main analysis script\nimport sys\nprint('Running main analysis')\n",
            'statistical_test': "#!/usr/bin/env python3\n# Statistical testing\nimport scipy.stats\nprint('Running statistical tests')\n",
            'data_cleaner': "#!/usr/bin/env python3\n# Data cleaning utilities\nimport pandas as pd\nprint('Cleaning data')\n",
            'file_utils': "#!/usr/bin/env python3\n# File utilities\nimport os\nprint('File utilities loaded')\n",
            'workflow_runner': "#!/usr/bin/env python3\n# Workflow runner\nimport yaml\nprint('Running workflow')\n",
            'template_workflow': "name: Template Workflow\nsteps:\n  - name: example\n    script: analysis/main_analysis.py\n"
        }
        
        # Write script files
        for script_name, script_path in scripts.items():
            content = script_contents.get(script_name, f"# {script_name}\nprint('Script: {script_name}')\n")
            with open(script_path, 'w') as f:
                f.write(content)
            
            # Make Python scripts executable
            if script_path.endswith('.py'):
                os.chmod(script_path, 0o755)
        
        script_structure['scripts'] = scripts
        
        yield script_structure
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_script_repository_structure(self, script_repository_structure):
        """Test script repository structure validation."""
        script_root = script_repository_structure['root']
        directories = script_repository_structure['directories']
        scripts = script_repository_structure['scripts']
        
        # Validate directory structure
        for dir_name, dir_path in directories.items():
            assert os.path.exists(dir_path), f"Script directory {dir_name} should exist"
            assert os.path.isdir(dir_path), f"Script path {dir_name} should be directory"
        
        # Validate script files
        for script_name, script_path in scripts.items():
            assert os.path.exists(script_path), f"Script {script_name} should exist"
            assert os.path.isfile(script_path), f"Script path {script_name} should be file"
            
            # Check if Python scripts are executable
            if script_path.endswith('.py'):
                file_stat = os.stat(script_path)
                is_executable = bool(file_stat.st_mode & 0o111)
                assert is_executable, f"Python script {script_name} should be executable"
        
        print(f"DEBUG: Script repository validated: {script_root}")
        print(f"DEBUG: Found {len(directories)} directories and {len(scripts)} scripts")
    
    def test_script_volume_mapping(self, script_repository_structure):
        """Test script volume mapping for Docker."""
        script_root = script_repository_structure['root']
        scripts = script_repository_structure['scripts']
        
        def map_script_to_docker_volume(script_path, script_root):
            """Map script path to Docker volume path."""
            if script_path.startswith(script_root):
                rel_path = os.path.relpath(script_path, script_root)
                return f'/workflow-scripts/{rel_path}'.replace('\\', '/')
            return script_path
        
        # Test script mapping
        for script_name, script_path in scripts.items():
            docker_path = map_script_to_docker_volume(script_path, script_root)
            
            # Validate Docker script path
            assert docker_path.startswith('/workflow-scripts/'), f"Script should be in /workflow-scripts: {docker_path}"
            assert '\\' not in docker_path, f"Docker path should use forward slashes: {docker_path}"
            
            print(f"DEBUG: {script_name}")
            print(f"  Native: {script_path}")
            print(f"  Docker: {docker_path}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])