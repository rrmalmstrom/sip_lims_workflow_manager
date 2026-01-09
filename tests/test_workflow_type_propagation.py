"""
Test workflow type propagation through the system.
Tests that WORKFLOW_TYPE environment variable flows correctly through all components.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestWorkflowTypePropagation:
    """Test WORKFLOW_TYPE environment variable propagation."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing WORKFLOW_TYPE environment variable
        if 'WORKFLOW_TYPE' in os.environ:
            del os.environ['WORKFLOW_TYPE']
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Clear any WORKFLOW_TYPE environment variable
        if 'WORKFLOW_TYPE' in os.environ:
            del os.environ['WORKFLOW_TYPE']
    
    def test_app_template_selection_sip(self):
        """Test app.py template selection for SIP workflow."""
        from workflow_utils import get_workflow_template_path
        
        os.environ['WORKFLOW_TYPE'] = 'sip'
        template_path = get_workflow_template_path()
        assert 'sip_workflow.yml' in str(template_path)
    
    def test_app_template_selection_sps_ce(self):
        """Test app.py template selection for SPS-CE workflow."""
        from workflow_utils import get_workflow_template_path
        
        os.environ['WORKFLOW_TYPE'] = 'sps-ce'
        template_path = get_workflow_template_path()
        assert 'sps_workflow.yml' in str(template_path)
    
    def test_app_template_selection_invalid_workflow(self):
        """Test app.py template selection with invalid workflow type."""
        from workflow_utils import get_workflow_template_path
        
        os.environ['WORKFLOW_TYPE'] = 'invalid'
        with pytest.raises(ValueError, match="Invalid WORKFLOW_TYPE"):
            get_workflow_template_path()
    
    def test_app_template_selection_missing_workflow(self):
        """Test app.py template selection with missing WORKFLOW_TYPE."""
        from workflow_utils import get_workflow_template_path
        
        # Ensure WORKFLOW_TYPE is not set
        if 'WORKFLOW_TYPE' in os.environ:
            del os.environ['WORKFLOW_TYPE']
        
        with pytest.raises(ValueError, match="WORKFLOW_TYPE environment variable is required"):
            get_workflow_template_path()
    
    def test_scripts_updater_sip_workflow(self):
        """Test ScriptsUpdater for SIP workflow."""
        from scripts_updater import ScriptsUpdater
        
        os.environ['WORKFLOW_TYPE'] = 'sip'
        updater = ScriptsUpdater()
        
        assert updater.workflow_type == 'sip'
        assert updater.scripts_repo_name == 'sip_scripts_workflow_gui'
        assert 'sip_scripts_workflow_gui' in updater.scripts_repo_url
    
    def test_scripts_updater_sps_ce_workflow(self):
        """Test ScriptsUpdater for SPS-CE workflow."""
        from scripts_updater import ScriptsUpdater
        
        os.environ['WORKFLOW_TYPE'] = 'sps-ce'
        updater = ScriptsUpdater()
        
        assert updater.workflow_type == 'sps-ce'
        assert updater.scripts_repo_name == 'SPS_library_creation_scripts'
        assert 'SPS_library_creation_scripts' in updater.scripts_repo_url
    
    def test_scripts_updater_invalid_workflow(self):
        """Test ScriptsUpdater with invalid workflow type."""
        from scripts_updater import ScriptsUpdater
        
        os.environ['WORKFLOW_TYPE'] = 'invalid'
        with pytest.raises(ValueError, match="Invalid workflow_type"):
            ScriptsUpdater()
    
    def test_git_update_manager_sip_config(self):
        """Test git_update_manager repository config for SIP."""
        from git_update_manager import get_repository_config
        
        os.environ['WORKFLOW_TYPE'] = 'sip'
        config = get_repository_config()
        
        assert 'sip_scripts_workflow_gui' in config['repo_url']
        assert 'sip_scripts_workflow_gui' in config['api_url']
    
    def test_git_update_manager_sps_ce_config(self):
        """Test git_update_manager repository config for SPS-CE."""
        from git_update_manager import get_repository_config
        
        os.environ['WORKFLOW_TYPE'] = 'sps-ce'
        config = get_repository_config()
        
        assert 'SPS_library_creation_scripts' in config['repo_url']
        assert 'SPS_library_creation_scripts' in config['api_url']
    
    def test_git_update_manager_fallback_behavior(self):
        """Test git_update_manager fallback for invalid workflow type."""
        from git_update_manager import get_repository_config
        
        os.environ['WORKFLOW_TYPE'] = 'invalid'
        config = get_repository_config()
        
        # Should fallback to SIP
        assert 'sip_scripts_workflow_gui' in config['repo_url']
    
    def test_environment_variable_defaults(self):
        """Test default behavior when WORKFLOW_TYPE is not set."""
        # Ensure WORKFLOW_TYPE is not set
        if 'WORKFLOW_TYPE' in os.environ:
            del os.environ['WORKFLOW_TYPE']
        
        from scripts_updater import ScriptsUpdater
        from git_update_manager import get_repository_config
        
        # Should default to SIP
        updater = ScriptsUpdater()
        assert updater.workflow_type == 'sip'
        
        config = get_repository_config()
        assert 'sip_scripts_workflow_gui' in config['repo_url']


class TestWorkflowTypeValidation:
    """Test workflow type validation across components."""
    
    def test_valid_workflow_types(self):
        """Test that all components accept valid workflow types."""
        from scripts_updater import ScriptsUpdater
        from git_update_manager import get_repository_config
        
        valid_types = ['sip', 'sps-ce']
        
        for workflow_type in valid_types:
            os.environ['WORKFLOW_TYPE'] = workflow_type
            
            # Test ScriptsUpdater
            updater = ScriptsUpdater()
            assert updater.workflow_type == workflow_type
            
            # Test git_update_manager
            config = get_repository_config()
            assert config is not None
            assert 'repo_url' in config
            
            # Clean up
            if 'WORKFLOW_TYPE' in os.environ:
                del os.environ['WORKFLOW_TYPE']
    
    def test_case_insensitive_workflow_types(self):
        """Test that workflow types are handled case-insensitively."""
        from scripts_updater import ScriptsUpdater
        
        test_cases = ['SIP', 'sip', 'Sip', 'SPS-CE', 'sps-ce', 'Sps-Ce']
        
        for workflow_type in test_cases:
            os.environ['WORKFLOW_TYPE'] = workflow_type
            
            updater = ScriptsUpdater()
            # Should be normalized to lowercase
            assert updater.workflow_type.lower() in ['sip', 'sps-ce']
            
            # Clean up
            if 'WORKFLOW_TYPE' in os.environ:
                del os.environ['WORKFLOW_TYPE']


class TestBackwardCompatibility:
    """Test that SIP workflow behavior remains unchanged."""
    
    def test_sip_workflow_unchanged(self):
        """Test that SIP workflow behavior is identical to before."""
        from scripts_updater import ScriptsUpdater
        from git_update_manager import get_repository_config
        
        # Test with explicit SIP setting
        os.environ['WORKFLOW_TYPE'] = 'sip'
        
        updater = ScriptsUpdater()
        config = get_repository_config()
        
        # Should use the same repository as before
        assert updater.scripts_repo_name == 'sip_scripts_workflow_gui'
        assert 'sip_scripts_workflow_gui' in config['repo_url']
        
        # Clean up
        if 'WORKFLOW_TYPE' in os.environ:
            del os.environ['WORKFLOW_TYPE']
        
        # Test with no WORKFLOW_TYPE set (default behavior)
        updater_default = ScriptsUpdater()
        config_default = get_repository_config()
        
        # Should default to SIP behavior
        assert updater_default.workflow_type == 'sip'
        assert updater_default.scripts_repo_name == 'sip_scripts_workflow_gui'
        assert 'sip_scripts_workflow_gui' in config_default['repo_url']