import unittest
import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import requests
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from update_manager import UpdateManager


class TestUpdateManager(unittest.TestCase):
    """Test cases for UpdateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, 'test_version.json')
        self.update_manager = UpdateManager(config_path=self.test_config_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        os.rmdir(self.temp_dir)
    
    def create_test_config(self, version: str):
        """Helper method to create a test config file."""
        config = {"version": version}
        with open(self.test_config_path, 'w') as f:
            json.dump(config, f)
    
    # Tests for local version reading
    def test_get_local_version_success(self):
        """Test successful reading of local version."""
        self.create_test_config("1.2.3")
        version = self.update_manager.get_local_version()
        self.assertEqual(version, "1.2.3")
    
    def test_get_local_version_file_not_found(self):
        """Test handling of missing config file."""
        # Don't create the config file
        version = self.update_manager.get_local_version()
        self.assertIsNone(version)
    
    def test_get_local_version_invalid_json(self):
        """Test handling of invalid JSON in config file."""
        with open(self.test_config_path, 'w') as f:
            f.write("invalid json content")
        version = self.update_manager.get_local_version()
        self.assertIsNone(version)
    
    def test_get_local_version_missing_version_key(self):
        """Test handling of config file without version key."""
        config = {"other_key": "value"}
        with open(self.test_config_path, 'w') as f:
            json.dump(config, f)
        version = self.update_manager.get_local_version()
        self.assertIsNone(version)
    
    # Tests for remote version fetching
    @patch('requests.get')
    def test_get_remote_version_success(self, mock_get):
        """Test successful fetching of remote version."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"version": "2.0.0"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        version = self.update_manager.get_remote_version()
        self.assertEqual(version, "2.0.0")
        mock_get.assert_called_once_with(self.update_manager.remote_version_url, timeout=10)
    
    @patch('requests.get')
    def test_get_remote_version_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        version = self.update_manager.get_remote_version()
        self.assertIsNone(version)
    
    @patch('requests.get')
    def test_get_remote_version_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        version = self.update_manager.get_remote_version()
        self.assertIsNone(version)
    
    @patch('requests.get')
    def test_get_remote_version_invalid_json(self, mock_get):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        version = self.update_manager.get_remote_version()
        self.assertIsNone(version)
    
    @patch('requests.get')
    def test_get_remote_version_missing_version_key(self, mock_get):
        """Test handling of response without version key."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"other_key": "value"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        version = self.update_manager.get_remote_version()
        self.assertIsNone(version)
    
    @patch('requests.get')
    def test_get_remote_version_latest_version_key(self, mock_get):
        """Test successful fetching with 'latest_version' key (Google Drive format)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "latest_version": "2.1.0",
            "release_date": "2024-09-24",
            "release_notes": "Test release"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        version = self.update_manager.get_remote_version()
        self.assertEqual(version, "2.1.0")
    
    # Tests for version comparison
    def test_compare_versions_special_case_999(self):
        """Test that version 9.9.9 always shows updates available."""
        result = self.update_manager.compare_versions("9.9.9", "1.0.0")
        self.assertTrue(result)
        
        result = self.update_manager.compare_versions("9.9.9", "10.0.0")
        self.assertTrue(result)
    
    def test_compare_versions_remote_higher(self):
        """Test comparison when remote version is higher."""
        result = self.update_manager.compare_versions("1.0.0", "1.0.1")
        self.assertTrue(result)
        
        result = self.update_manager.compare_versions("1.0.0", "1.1.0")
        self.assertTrue(result)
        
        result = self.update_manager.compare_versions("1.0.0", "2.0.0")
        self.assertTrue(result)
    
    def test_compare_versions_local_higher(self):
        """Test comparison when local version is higher."""
        result = self.update_manager.compare_versions("1.0.1", "1.0.0")
        self.assertFalse(result)
        
        result = self.update_manager.compare_versions("1.1.0", "1.0.0")
        self.assertFalse(result)
        
        result = self.update_manager.compare_versions("2.0.0", "1.0.0")
        self.assertFalse(result)
    
    def test_compare_versions_equal(self):
        """Test comparison when versions are equal."""
        result = self.update_manager.compare_versions("1.0.0", "1.0.0")
        self.assertFalse(result)
        
        result = self.update_manager.compare_versions("2.1.3", "2.1.3")
        self.assertFalse(result)
    
    def test_compare_versions_different_lengths(self):
        """Test comparison with different version string lengths."""
        result = self.update_manager.compare_versions("1.0", "1.0.1")
        self.assertTrue(result)
        
        result = self.update_manager.compare_versions("1.0.1", "1.0")
        self.assertFalse(result)
        
        result = self.update_manager.compare_versions("1.0", "1.0.0")
        self.assertFalse(result)
    
    def test_compare_versions_invalid_format(self):
        """Test comparison with invalid version formats."""
        result = self.update_manager.compare_versions("invalid", "1.0.0")
        self.assertFalse(result)
        
        result = self.update_manager.compare_versions("1.0.0", "invalid")
        self.assertFalse(result)
    
    # Tests for check_for_updates method
    def test_check_for_updates_success(self):
        """Test successful update check."""
        self.create_test_config("1.0.0")
        
        with patch.object(self.update_manager, 'get_remote_version', return_value="1.0.1"):
            result = self.update_manager.check_for_updates()
            
            self.assertIsNone(result['error'])
            self.assertEqual(result['local_version'], "1.0.0")
            self.assertEqual(result['remote_version'], "1.0.1")
            self.assertTrue(result['update_available'])
    
    def test_check_for_updates_no_update_needed(self):
        """Test update check when no update is needed."""
        self.create_test_config("1.0.0")
        
        with patch.object(self.update_manager, 'get_remote_version', return_value="1.0.0"):
            result = self.update_manager.check_for_updates()
            
            self.assertIsNone(result['error'])
            self.assertEqual(result['local_version'], "1.0.0")
            self.assertEqual(result['remote_version'], "1.0.0")
            self.assertFalse(result['update_available'])
    
    def test_check_for_updates_local_version_error(self):
        """Test update check when local version cannot be read."""
        # Don't create config file
        with patch.object(self.update_manager, 'get_remote_version', return_value="1.0.0"):
            result = self.update_manager.check_for_updates()
            
            self.assertEqual(result['error'], "Could not read local version")
            self.assertIsNone(result['local_version'])
            self.assertIsNone(result['remote_version'])
            self.assertFalse(result['update_available'])
    
    def test_check_for_updates_remote_version_error(self):
        """Test update check when remote version cannot be fetched."""
        self.create_test_config("1.0.0")
        
        with patch.object(self.update_manager, 'get_remote_version', return_value=None):
            result = self.update_manager.check_for_updates()
            
            self.assertEqual(result['error'], "Could not fetch remote version")
            self.assertEqual(result['local_version'], "1.0.0")
            self.assertIsNone(result['remote_version'])
            self.assertFalse(result['update_available'])
    
    def test_check_for_updates_special_case_999(self):
        """Test update check with version 9.9.9 (should always show update available)."""
        self.create_test_config("9.9.9")
        
        with patch.object(self.update_manager, 'get_remote_version', return_value="1.0.0"):
            result = self.update_manager.check_for_updates()
            
            self.assertIsNone(result['error'])
            self.assertEqual(result['local_version'], "9.9.9")
            self.assertEqual(result['remote_version'], "1.0.0")
            self.assertTrue(result['update_available'])


if __name__ == '__main__':
    unittest.main()