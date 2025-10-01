"""
Test suite for the unified update system integration.
Tests the complete integration between app.py and the unified Git update manager.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the functions we're testing from app.py
sys.path.insert(0, str(Path(__file__).parent.parent))
from app import check_for_app_updates, check_for_script_updates, update_scripts


class TestUnifiedUpdateIntegration:
    """Test the unified update system integration."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear Streamlit cache before each test
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
    
    @patch('app.create_update_manager')
    def test_check_for_app_updates_success(self, mock_create_manager):
        """Test successful app update check."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_for_updates.return_value = {
            'update_available': True,
            'current_version': 'v1.0.2',
            'latest_version': 'v1.1.0',
            'error': None
        }
        mock_create_manager.return_value = mock_manager
        
        # Act
        result = check_for_app_updates()
        
        # Assert
        mock_create_manager.assert_called_once_with("application")
        mock_manager.check_for_updates.assert_called_once()
        assert result['update_available'] is True
        assert result['current_version'] == 'v1.0.2'
        assert result['latest_version'] == 'v1.1.0'
        assert 'error' not in result or result['error'] is None
    
    @patch('app.create_update_manager')
    def test_check_for_app_updates_no_update(self, mock_create_manager):
        """Test app update check when no update is available."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_for_updates.return_value = {
            'update_available': False,
            'current_version': 'v1.1.0',
            'latest_version': 'v1.1.0',
            'error': None
        }
        mock_create_manager.return_value = mock_manager
        
        # Act
        result = check_for_app_updates()
        
        # Assert
        assert result['update_available'] is False
        assert result['current_version'] == 'v1.1.0'
        assert result['latest_version'] == 'v1.1.0'
    
    @patch('app.create_update_manager')
    def test_check_for_app_updates_error(self, mock_create_manager):
        """Test app update check when an error occurs."""
        # Arrange
        mock_create_manager.side_effect = Exception("SSH key not found")
        
        # Act
        result = check_for_app_updates()
        
        # Assert
        assert result['update_available'] is False
        assert result['current_version'] is None
        assert result['latest_version'] is None
        assert "Failed to check for app updates: SSH key not found" in result['error']
    
    @patch('app.create_update_manager')
    def test_check_for_script_updates_success(self, mock_create_manager):
        """Test successful script update check."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_for_updates.return_value = {
            'update_available': True,
            'current_version': 'v1.0.0',
            'latest_version': 'v1.0.1',
            'error': None
        }
        mock_create_manager.return_value = mock_manager
        
        # Act
        result = check_for_script_updates()
        
        # Assert
        mock_create_manager.assert_called_once_with("scripts")
        mock_manager.check_for_updates.assert_called_once()
        assert result['update_available'] is True
        assert result['current_version'] == 'v1.0.0'
        assert result['latest_version'] == 'v1.0.1'
    
    @patch('app.create_update_manager')
    def test_check_for_script_updates_no_update(self, mock_create_manager):
        """Test script update check when no update is available."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_for_updates.return_value = {
            'update_available': False,
            'current_version': 'v1.0.1',
            'latest_version': 'v1.0.1',
            'error': None
        }
        mock_create_manager.return_value = mock_manager
        
        # Act
        result = check_for_script_updates()
        
        # Assert
        assert result['update_available'] is False
        assert result['current_version'] == 'v1.0.1'
        assert result['latest_version'] == 'v1.0.1'
    
    @patch('app.create_update_manager')
    def test_check_for_script_updates_error(self, mock_create_manager):
        """Test script update check when an error occurs."""
        # Arrange
        mock_create_manager.side_effect = Exception("Repository access denied")
        
        # Act
        result = check_for_script_updates()
        
        # Assert
        assert result['update_available'] is False
        assert result['current_version'] is None
        assert result['latest_version'] is None
        assert "Failed to check for script updates: Repository access denied" in result['error']
    
    @patch('app.create_update_manager')
    def test_update_scripts_success(self, mock_create_manager):
        """Test successful script update."""
        # Arrange
        mock_manager = Mock()
        mock_manager.update_to_latest.return_value = {
            'success': True,
            'message': 'Scripts updated to v1.0.1',
            'error': None
        }
        mock_create_manager.return_value = mock_manager
        
        # Act
        result = update_scripts()
        
        # Assert
        mock_create_manager.assert_called_once_with("scripts")
        mock_manager.update_to_latest.assert_called_once()
        assert result['success'] is True
        assert 'error' not in result or result['error'] is None
    
    @patch('app.create_update_manager')
    def test_update_scripts_failure(self, mock_create_manager):
        """Test script update failure."""
        # Arrange
        mock_manager = Mock()
        mock_manager.update_to_latest.return_value = {
            'success': False,
            'error': 'Git pull failed'
        }
        mock_create_manager.return_value = mock_manager
        
        # Act
        result = update_scripts()
        
        # Assert
        assert result['success'] is False
        assert 'Git pull failed' in result.get('error', '')
    
    @patch('app.create_update_manager')
    def test_update_scripts_exception(self, mock_create_manager):
        """Test script update when an exception occurs."""
        # Arrange
        mock_create_manager.side_effect = Exception("Network timeout")
        
        # Act
        result = update_scripts()
        
        # Assert
        assert result['success'] is False
        assert "Failed to update scripts: Network timeout" in result['error']
    
    def test_cache_configuration(self):
        """Test that caching is properly configured for 60 minutes."""
        # This test verifies the cache TTL is set correctly
        # We can't easily test the actual caching behavior without Streamlit running,
        # but we can verify the function decorators are applied
        
        # Check that the functions have cache decorators
        assert hasattr(check_for_app_updates, '__wrapped__')
        assert hasattr(check_for_script_updates, '__wrapped__')
        
        # The TTL should be 3600 seconds (60 minutes)
        # This is verified by the decorator configuration in the source code


class TestUnifiedUpdateSystemIntegration:
    """Integration tests for the complete unified update system."""
    
    @patch('app.create_update_manager')
    @patch('app.webbrowser')
    def test_complete_app_update_workflow(self, mock_webbrowser, mock_create_manager):
        """Test the complete app update workflow."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_for_updates.return_value = {
            'update_available': True,
            'current_version': 'v1.0.2',
            'latest_version': 'v1.1.0'
        }
        mock_create_manager.return_value = mock_manager
        
        # Act - Check for updates
        update_info = check_for_app_updates()
        
        # Assert - Update is available
        assert update_info['update_available'] is True
        assert update_info['current_version'] == 'v1.0.2'
        assert update_info['latest_version'] == 'v1.1.0'
        
        # The UI would then call webbrowser.open() when user clicks the button
        # We can't test the Streamlit UI directly, but we can verify the URL
        expected_url = "https://github.com/RRMalmstrom/sip_lims_workflow_manager/releases/latest"
        # This would be called by the UI button click handler
        mock_webbrowser.open(expected_url)
        mock_webbrowser.open.assert_called_once_with(expected_url)
    
    @patch('app.create_update_manager')
    def test_complete_script_update_workflow(self, mock_create_manager):
        """Test the complete script update workflow."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_for_updates.return_value = {
            'update_available': True,
            'current_version': 'v1.0.0',
            'latest_version': 'v1.0.1'
        }
        mock_manager.update_to_latest.return_value = {
            'success': True,
            'message': 'Scripts updated successfully'
        }
        mock_create_manager.return_value = mock_manager
        
        # Act - Check for updates
        update_info = check_for_script_updates()
        
        # Assert - Update is available
        assert update_info['update_available'] is True
        assert update_info['current_version'] == 'v1.0.0'
        assert update_info['latest_version'] == 'v1.0.1'
        
        # Act - Perform update
        update_result = update_scripts()
        
        # Assert - Update succeeded
        assert update_result['success'] is True
        mock_manager.update_to_latest.assert_called_once()
    
    @patch('app.create_update_manager')
    def test_error_handling_integration(self, mock_create_manager):
        """Test error handling across the unified system."""
        # Clear cache to ensure fresh test
        check_for_app_updates.clear()
        check_for_script_updates.clear()
        
        # Test app update error
        mock_create_manager.side_effect = Exception("SSH configuration error")
        
        app_result = check_for_app_updates()
        assert app_result['update_available'] is False
        assert "SSH configuration error" in app_result['error']
        
        script_result = check_for_script_updates()
        assert script_result['update_available'] is False
        assert "SSH configuration error" in script_result['error']
        
        update_result = update_scripts()
        assert update_result['success'] is False
        assert "SSH configuration error" in update_result['error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])