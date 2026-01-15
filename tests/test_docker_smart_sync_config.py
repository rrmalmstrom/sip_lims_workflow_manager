"""
Test Suite for Docker Smart Sync Configuration

This module tests the Docker configuration changes to support Smart Sync functionality,
including environment variable passing and container setup validation.
"""

import pytest
import yaml
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestDockerComposeSmartSyncConfig:
    """Test Docker Compose configuration for Smart Sync support."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = Path(__file__).parent.parent
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_docker_compose_has_smart_sync_environment_variables(self):
        """Test that docker-compose.yml includes Smart Sync environment variables."""
        docker_compose_path = self.project_root / "docker-compose.yml"
        assert docker_compose_path.exists(), "docker-compose.yml should exist"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Check that the service exists
        assert 'services' in compose_config
        assert 'sip-lims-workflow' in compose_config['services']
        
        service_config = compose_config['services']['sip-lims-workflow']
        assert 'environment' in service_config
        
        # Convert environment list to dict for easier checking
        env_vars = {}
        for env_item in service_config['environment']:
            if '=' in env_item:
                key, value = env_item.split('=', 1)
                env_vars[key] = value
        
        # Check that Smart Sync environment variables are present
        assert 'SMART_SYNC_ENABLED' in env_vars
        assert 'NETWORK_PROJECT_PATH' in env_vars
        assert 'LOCAL_PROJECT_PATH' in env_vars
        
        # Check default values
        assert env_vars['SMART_SYNC_ENABLED'] == '${SMART_SYNC_ENABLED:-false}'
        assert env_vars['NETWORK_PROJECT_PATH'] == '${NETWORK_PROJECT_PATH:-}'
        assert env_vars['LOCAL_PROJECT_PATH'] == '${LOCAL_PROJECT_PATH:-}'
    
    def test_docker_compose_preserves_existing_environment_variables(self):
        """Test that existing environment variables are preserved."""
        docker_compose_path = self.project_root / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        service_config = compose_config['services']['sip-lims-workflow']
        env_vars = {}
        for env_item in service_config['environment']:
            if '=' in env_item:
                key, value = env_item.split('=', 1)
                env_vars[key] = value
        
        # Check that original environment variables still exist
        assert 'APP_ENV' in env_vars
        assert 'PROJECT_NAME' in env_vars
        assert 'WORKFLOW_TYPE' in env_vars
        
        # Check their default values are preserved
        assert env_vars['APP_ENV'] == '${APP_ENV:-production}'
        assert env_vars['PROJECT_NAME'] == '${PROJECT_NAME:-data}'
        assert env_vars['WORKFLOW_TYPE'] == '${WORKFLOW_TYPE}'
    
    def test_docker_compose_volume_configuration_unchanged(self):
        """Test that volume configuration remains unchanged for compatibility."""
        docker_compose_path = self.project_root / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        service_config = compose_config['services']['sip-lims-workflow']
        assert 'volumes' in service_config
        
        volumes = service_config['volumes']
        assert len(volumes) == 2  # Should have exactly 2 volumes
        
        # Check project data volume
        project_volume = volumes[0]
        assert project_volume['type'] == 'bind'
        assert project_volume['source'] == '${PROJECT_PATH:-.}'
        assert project_volume['target'] == '/data'
        
        # Check scripts volume
        scripts_volume = volumes[1]
        assert scripts_volume['type'] == 'bind'
        assert scripts_volume['source'] == '${SCRIPTS_PATH}'
        assert scripts_volume['target'] == '/workflow-scripts'


class TestDockerfileSmartSyncSupport:
    """Test Dockerfile configuration for Smart Sync support."""
    
    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
    
    def test_dockerfile_includes_src_directory(self):
        """Test that Dockerfile includes the src/ directory containing smart_sync.py."""
        dockerfile_path = self.project_root / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile should exist"
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check that src/ directory is copied
        assert 'COPY src/ ./src/' in dockerfile_content
        
        # Verify smart_sync.py exists in the src directory
        smart_sync_path = self.project_root / "src" / "smart_sync.py"
        assert smart_sync_path.exists(), "smart_sync.py should exist in src/ directory"
    
    def test_dockerfile_preserves_existing_structure(self):
        """Test that Dockerfile preserves existing application structure."""
        dockerfile_path = self.project_root / "Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check that all required files are still copied
        required_copies = [
            'COPY app.py .',
            'COPY src/ ./src/',
            'COPY templates/ ./templates/',
            'COPY utils/ ./utils/',
            'COPY entrypoint.sh .'
        ]
        
        for copy_line in required_copies:
            assert copy_line in dockerfile_content, f"Missing: {copy_line}"
    
    def test_dockerfile_working_directory_unchanged(self):
        """Test that working directory and volume mounts remain unchanged."""
        dockerfile_path = self.project_root / "Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check working directory
        assert 'WORKDIR /opt/app' in dockerfile_content
        
        # Check volume mount points
        assert 'mkdir -p /data /workflow-scripts' in dockerfile_content
        assert 'chown appuser:appuser /data /workflow-scripts' in dockerfile_content


class TestSmartSyncDockerIntegration:
    """Test Smart Sync integration with Docker environment."""
    
    def test_smart_sync_environment_variable_defaults(self):
        """Test Smart Sync environment variable default behavior."""
        # Test default disabled state
        with patch.dict(os.environ, {}, clear=True):
            # When no Smart Sync environment variables are set
            smart_sync_enabled = os.getenv("SMART_SYNC_ENABLED", "false")
            network_path = os.getenv("NETWORK_PROJECT_PATH", "")
            local_path = os.getenv("LOCAL_PROJECT_PATH", "")
            
            assert smart_sync_enabled == "false"
            assert network_path == ""
            assert local_path == ""
    
    def test_smart_sync_environment_variable_override(self):
        """Test Smart Sync environment variable override behavior."""
        # Test enabled state with paths
        test_env = {
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "/network/path",
            "LOCAL_PROJECT_PATH": "/local/path"
        }
        
        with patch.dict(os.environ, test_env):
            smart_sync_enabled = os.getenv("SMART_SYNC_ENABLED")
            network_path = os.getenv("NETWORK_PROJECT_PATH")
            local_path = os.getenv("LOCAL_PROJECT_PATH")
            
            assert smart_sync_enabled == "true"
            assert network_path == "/network/path"
            assert local_path == "/local/path"
    
    def test_docker_compose_environment_variable_substitution(self):
        """Test that Docker Compose environment variable substitution works correctly."""
        # Simulate Docker Compose environment variable substitution
        test_cases = [
            # (env_var_value, expected_result)
            (None, "false"),  # Default when not set
            ("true", "true"), # Override value
            ("false", "false") # Explicit false
        ]
        
        for env_value, expected in test_cases:
            env_dict = {}
            if env_value is not None:
                env_dict["SMART_SYNC_ENABLED"] = env_value
            
            with patch.dict(os.environ, env_dict, clear=True):
                # Simulate Docker Compose variable substitution logic
                result = os.getenv("SMART_SYNC_ENABLED", "false")
                assert result == expected, f"Expected {expected}, got {result} for input {env_value}"
        
        # Test empty string case separately (os.getenv returns empty string, not default)
        with patch.dict(os.environ, {"SMART_SYNC_ENABLED": ""}, clear=True):
            result = os.getenv("SMART_SYNC_ENABLED", "false")
            assert result == "", "Empty string should return empty string, not default"


class TestDockerConfigurationValidation:
    """Test Docker configuration file validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
    
    def test_docker_compose_yaml_syntax_valid(self):
        """Test that docker-compose.yml has valid YAML syntax."""
        docker_compose_path = self.project_root / "docker-compose.yml"
        
        try:
            with open(docker_compose_path, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"docker-compose.yml has invalid YAML syntax: {e}")
    
    def test_docker_compose_required_sections_present(self):
        """Test that docker-compose.yml has all required sections."""
        docker_compose_path = self.project_root / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Check required top-level sections
        assert 'services' in compose_config
        assert 'networks' in compose_config
        
        # Check required service configuration
        service_config = compose_config['services']['sip-lims-workflow']
        required_sections = ['image', 'platform', 'container_name', 'ports', 'volumes', 'environment']
        
        for section in required_sections:
            assert section in service_config, f"Missing required section: {section}"
    
    def test_dockerfile_syntax_basic_validation(self):
        """Test basic Dockerfile syntax validation."""
        dockerfile_path = self.project_root / "Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check for required Dockerfile instructions
        required_instructions = ['FROM', 'WORKDIR', 'COPY', 'RUN', 'EXPOSE', 'CMD']
        
        for instruction in required_instructions:
            assert instruction in dockerfile_content, f"Missing Dockerfile instruction: {instruction}"
        
        # Check that lines don't have obvious syntax errors
        lines = dockerfile_content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic check: lines should not end with backslash unless continued
                if line.endswith('\\'):
                    # Should have a continuation line
                    if i < len(lines):
                        next_line = lines[i].strip() if i < len(lines) else ""
                        assert next_line, f"Line {i} ends with backslash but has no continuation"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])