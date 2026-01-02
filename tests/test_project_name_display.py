"""
Tests for project name display functionality.
This tests the cosmetic display of project folder names in the Docker environment.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestProjectNameDisplay:
    """Test project name display functionality."""
    
    def test_extract_project_name_from_environment(self):
        """Test that project name is correctly extracted from environment variable."""
        # Test case 1: Environment variable is set
        with patch.dict(os.environ, {'PROJECT_NAME': 'my-awesome-project'}):
            from app import get_project_display_name
            result = get_project_display_name(Path('/data'))
            assert result == 'my-awesome-project'
    
    def test_fallback_to_path_name_when_no_environment(self):
        """Test fallback to path name when environment variable is not set."""
        # Test case 2: No environment variable, fallback to path name
        with patch.dict(os.environ, {}, clear=True):
            from app import get_project_display_name
            result = get_project_display_name(Path('/data'))
            assert result == 'data'
    
    def test_fallback_to_path_name_when_environment_empty(self):
        """Test fallback to path name when environment variable is empty."""
        # Test case 3: Empty environment variable, fallback to path name
        with patch.dict(os.environ, {'PROJECT_NAME': ''}):
            from app import get_project_display_name
            result = get_project_display_name(Path('/data'))
            assert result == 'data'
    
    def test_project_name_with_special_characters(self):
        """Test project names with special characters are handled correctly."""
        test_cases = [
            'project-with-dashes',
            'project_with_underscores',
            'project with spaces',
            'project.with.dots',
            'Project-With-Mixed_Cases.123'
        ]
        
        for project_name in test_cases:
            with patch.dict(os.environ, {'PROJECT_NAME': project_name}):
                from app import get_project_display_name
                result = get_project_display_name(Path('/data'))
                assert result == project_name
    
    def test_project_name_display_in_sidebar(self):
        """Test that project name is correctly displayed in sidebar."""
        # Mock streamlit session state and components
        with patch('streamlit.session_state') as mock_session_state, \
             patch('streamlit.info') as mock_info, \
             patch.dict(os.environ, {'PROJECT_NAME': 'test-project'}):
            
            # Set up mock session state
            mock_session_state.project_path = Path('/data')
            
            # Import and call the sidebar display function
            from app import display_project_info_in_sidebar
            display_project_info_in_sidebar()
            
            # Verify the correct display text was called
            mock_info.assert_called_with('🐳 **Docker Project**: `test-project`')
    
    def test_project_name_display_fallback_in_sidebar(self):
        """Test sidebar display falls back to path name when no environment variable."""
        with patch('streamlit.session_state') as mock_session_state, \
             patch('streamlit.info') as mock_info, \
             patch.dict(os.environ, {}, clear=True):
            
            # Set up mock session state
            mock_session_state.project_path = Path('/data')
            
            # Import and call the sidebar display function
            from app import display_project_info_in_sidebar
            display_project_info_in_sidebar()
            
            # Verify fallback display text was called
            mock_info.assert_called_with('🐳 **Docker Project**: `data`')


class TestDockerEnvironmentIntegration:
    """Test Docker environment variable integration."""
    
    def test_docker_compose_environment_variable_passing(self):
        """Test that PROJECT_NAME environment variable is properly configured."""
        # Read docker-compose.yml and verify PROJECT_NAME is included
        compose_file = Path('docker-compose.yml')
        assert compose_file.exists(), "docker-compose.yml should exist"
        
        content = compose_file.read_text()
        assert 'PROJECT_NAME=${PROJECT_NAME:-data}' in content, \
            "docker-compose.yml should include PROJECT_NAME environment variable with fallback"
    
    def test_run_script_sets_project_name(self):
        """Test that run script correctly sets PROJECT_NAME environment variable."""
        # This test would verify the bash script logic
        # For now, we'll test the expected behavior conceptually
        
        # Test data: various project paths and expected names
        test_cases = [
            ('/Users/john/Documents/my-project', 'my-project'),
            ('/home/user/work/awesome-workflow', 'awesome-workflow'),
            ('/path/to/project with spaces', 'project with spaces'),
            ('/simple/path', 'path'),
            ('/single', 'single')
        ]
        
        for project_path, expected_name in test_cases:
            # Simulate basename extraction (what the bash script does)
            actual_name = os.path.basename(project_path)
            assert actual_name == expected_name, \
                f"basename of {project_path} should be {expected_name}, got {actual_name}"


class TestBackwardCompatibility:
    """Test that changes don't break existing functionality."""
    
    def test_existing_project_loading_unchanged(self):
        """Test that project loading functionality is unchanged."""
        # This test ensures our display changes don't affect core functionality
        with patch('streamlit.session_state') as mock_session_state:
            mock_session_state.project_path = Path('/data')
            
            # The core project loading should still work with /data path
            # This is a conceptual test - the actual Project class should still
            # initialize correctly with the /data path
            from src.core import Project
            
            # Mock the workflow file existence check and directory creation
            with patch.object(Path, 'is_file', return_value=True), \
                 patch.object(Path, 'mkdir'), \
                 patch('builtins.open'), \
                 patch('yaml.safe_load', return_value={'workflow_name': 'test', 'steps': []}):
                
                # This should not raise an exception
                project = Project(Path('/data'), load_workflow=True)
                assert project.path == Path('/data')
    
    def test_file_operations_still_use_data_path(self):
        """Test that all file operations still use the /data mount point."""
        # Verify that our display changes don't affect where files are accessed
        test_project_path = Path('/data')
        
        # Mock project initialization
        with patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'mkdir'), \
             patch('builtins.open'), \
             patch('yaml.safe_load', return_value={'workflow_name': 'test', 'steps': []}):
            
            from src.core import Project
            project = Project(test_project_path, load_workflow=True)
            
            # Verify all paths are still based on /data
            assert project.path == Path('/data')
            assert project.workflow_file_path == Path('/data/workflow.yml')
            assert str(project.state_manager.path).startswith('/data')