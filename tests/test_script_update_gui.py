import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta

# Note: These tests are designed to test the GUI integration logic
# Actual Streamlit GUI testing is limited, so we focus on the underlying functions


class TestScriptUpdateGUI:
    """Test cases for script update GUI integration."""
    
    @pytest.fixture
    def temp_scripts_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_script_update_manager(self):
        """Create a mock ScriptUpdateManager for testing."""
        manager = Mock()
        manager.check_for_updates.return_value = {
            'update_available': False,
            'error': None,
            'status_message': 'Up to date',
            'last_check': datetime.now()
        }
        manager.update_scripts.return_value = {
            'success': True,
            'error': None,
            'message': 'Scripts updated successfully'
        }
        manager.get_last_check_time.return_value = datetime.now()
        return manager
    
    def test_check_for_script_updates_function_with_updates_available(self, temp_scripts_dir):
        """Test the check_for_script_updates function when updates are available."""
        from src.script_update_manager import ScriptUpdateManager
        
        with patch.object(ScriptUpdateManager, 'check_for_updates') as mock_check:
            mock_check.return_value = {
                'update_available': True,
                'error': None,
                'status_message': 'Your branch is behind by 2 commits',
                'last_check': datetime.now()
            }
            
            # Import the function we'll add to app.py
            # For now, we'll test the logic directly
            def check_for_script_updates():
                try:
                    scripts_dir = Path(__file__).parent / "scripts"
                    manager = ScriptUpdateManager(scripts_dir)
                    return manager.check_for_updates()
                except Exception as e:
                    return {
                        'update_available': False,
                        'error': str(e),
                        'status_message': 'Error checking for updates',
                        'last_check': None
                    }
            
            # Mock the scripts directory path
            with patch('pathlib.Path.__truediv__', return_value=temp_scripts_dir):
                result = check_for_script_updates()
            
            assert result['update_available'] is True
            assert result['error'] is None
            assert 'behind' in result['status_message']
    
    def test_check_for_script_updates_function_when_up_to_date(self, temp_scripts_dir):
        """Test the check_for_script_updates function when scripts are current."""
        from src.script_update_manager import ScriptUpdateManager
        
        with patch.object(ScriptUpdateManager, 'check_for_updates') as mock_check:
            mock_check.return_value = {
                'update_available': False,
                'error': None,
                'status_message': 'Your branch is up to date',
                'last_check': datetime.now()
            }
            
            def check_for_script_updates():
                try:
                    scripts_dir = Path(__file__).parent / "scripts"
                    manager = ScriptUpdateManager(scripts_dir)
                    return manager.check_for_updates()
                except Exception as e:
                    return {
                        'update_available': False,
                        'error': str(e),
                        'status_message': 'Error checking for updates',
                        'last_check': None
                    }
            
            with patch('pathlib.Path.__truediv__', return_value=temp_scripts_dir):
                result = check_for_script_updates()
            
            assert result['update_available'] is False
            assert result['error'] is None
            assert 'up to date' in result['status_message']
    
    def test_check_for_script_updates_function_with_error(self, temp_scripts_dir):
        """Test the check_for_script_updates function when an error occurs."""
        from src.script_update_manager import ScriptUpdateManager
        
        with patch.object(ScriptUpdateManager, '__init__', side_effect=Exception("Scripts directory not found")):
            def check_for_script_updates():
                try:
                    scripts_dir = Path(__file__).parent / "scripts"
                    manager = ScriptUpdateManager(scripts_dir)
                    return manager.check_for_updates()
                except Exception as e:
                    return {
                        'update_available': False,
                        'error': str(e),
                        'status_message': 'Error checking for updates',
                        'last_check': None
                    }
            
            result = check_for_script_updates()
            
            assert result['update_available'] is False
            assert result['error'] is not None
            assert 'Scripts directory not found' in result['error']
    
    def test_update_scripts_function_success(self, temp_scripts_dir):
        """Test the update_scripts function with successful update."""
        from src.script_update_manager import ScriptUpdateManager
        
        with patch.object(ScriptUpdateManager, 'update_scripts') as mock_update:
            mock_update.return_value = {
                'success': True,
                'error': None,
                'message': 'Scripts updated successfully'
            }
            
            def update_scripts():
                try:
                    scripts_dir = Path(__file__).parent / "scripts"
                    manager = ScriptUpdateManager(scripts_dir)
                    return manager.update_scripts()
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'message': 'Failed to update scripts'
                    }
            
            with patch('pathlib.Path.__truediv__', return_value=temp_scripts_dir):
                result = update_scripts()
            
            assert result['success'] is True
            assert result['error'] is None
            assert 'successfully' in result['message']
    
    def test_update_scripts_function_failure(self, temp_scripts_dir):
        """Test the update_scripts function with failed update."""
        from src.script_update_manager import ScriptUpdateManager
        
        with patch.object(ScriptUpdateManager, 'update_scripts') as mock_update:
            mock_update.return_value = {
                'success': False,
                'error': 'Merge conflict detected',
                'message': 'Failed to update scripts'
            }
            
            def update_scripts():
                try:
                    scripts_dir = Path(__file__).parent / "scripts"
                    manager = ScriptUpdateManager(scripts_dir)
                    return manager.update_scripts()
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'message': 'Failed to update scripts'
                    }
            
            with patch('pathlib.Path.__truediv__', return_value=temp_scripts_dir):
                result = update_scripts()
            
            assert result['success'] is False
            assert result['error'] is not None
            assert 'conflict' in result['error']
    
    def test_render_script_update_notification_with_updates_available(self, mock_script_update_manager):
        """Test rendering update notification when updates are available."""
        mock_script_update_manager.check_for_updates.return_value = {
            'update_available': True,
            'error': None,
            'status_message': 'Your branch is behind by 2 commits',
            'last_check': datetime.now()
        }
        
        def render_script_update_notification(manager):
            """Simulate the GUI rendering logic."""
            result = manager.check_for_updates()
            
            notification_data = {
                'show_notification': result['update_available'],
                'message': result['status_message'],
                'error': result['error'],
                'last_check': result.get('last_check')
            }
            
            return notification_data
        
        notification = render_script_update_notification(mock_script_update_manager)
        
        assert notification['show_notification'] is True
        assert 'behind' in notification['message']
        assert notification['error'] is None
        assert notification['last_check'] is not None
    
    def test_render_script_update_notification_when_up_to_date(self, mock_script_update_manager):
        """Test rendering when no updates are available."""
        mock_script_update_manager.check_for_updates.return_value = {
            'update_available': False,
            'error': None,
            'status_message': 'Your branch is up to date',
            'last_check': datetime.now()
        }
        
        def render_script_update_notification(manager):
            result = manager.check_for_updates()
            
            notification_data = {
                'show_notification': result['update_available'],
                'message': result['status_message'],
                'error': result['error'],
                'last_check': result.get('last_check')
            }
            
            return notification_data
        
        notification = render_script_update_notification(mock_script_update_manager)
        
        assert notification['show_notification'] is False
        assert 'up to date' in notification['message']
        assert notification['error'] is None
    
    def test_render_script_update_notification_with_error(self, mock_script_update_manager):
        """Test rendering when an error occurs."""
        mock_script_update_manager.check_for_updates.return_value = {
            'update_available': False,
            'error': 'Network connection failed',
            'status_message': 'Error checking for updates',
            'last_check': None
        }
        
        def render_script_update_notification(manager):
            result = manager.check_for_updates()
            
            notification_data = {
                'show_notification': False,  # Don't show notification on error
                'message': result['status_message'],
                'error': result['error'],
                'last_check': result.get('last_check'),
                'show_error': result['error'] is not None
            }
            
            return notification_data
        
        notification = render_script_update_notification(mock_script_update_manager)
        
        assert notification['show_notification'] is False
        assert notification['show_error'] is True
        assert 'Network connection failed' in notification['error']
    
    def test_cache_clearing_functionality(self, mock_script_update_manager):
        """Test manual cache clearing functionality."""
        def clear_script_update_cache(manager):
            """Simulate the cache clearing logic."""
            manager.clear_cache()
            return {'cache_cleared': True}
        
        result = clear_script_update_cache(mock_script_update_manager)
        
        assert result['cache_cleared'] is True
        mock_script_update_manager.clear_cache.assert_called_once()
    
    def test_last_checked_timestamp_formatting(self, mock_script_update_manager):
        """Test formatting of last checked timestamp for display."""
        now = datetime.now()
        mock_script_update_manager.get_last_check_time.return_value = now
        
        def format_last_check_time(manager):
            """Simulate timestamp formatting logic."""
            last_check = manager.get_last_check_time()
            if last_check is None:
                return "Never"
            
            time_diff = datetime.now() - last_check
            if time_diff.total_seconds() < 60:
                return "Just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = int(time_diff.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        # Test "Just now"
        formatted = format_last_check_time(mock_script_update_manager)
        assert formatted == "Just now"
        
        # Test minutes ago
        past_time = now - timedelta(minutes=5)
        mock_script_update_manager.get_last_check_time.return_value = past_time
        formatted = format_last_check_time(mock_script_update_manager)
        assert "5 minutes ago" in formatted
        
        # Test hours ago
        past_time = now - timedelta(hours=2)
        mock_script_update_manager.get_last_check_time.return_value = past_time
        formatted = format_last_check_time(mock_script_update_manager)
        assert "2 hours ago" in formatted
        
        # Test never checked
        mock_script_update_manager.get_last_check_time.return_value = None
        formatted = format_last_check_time(mock_script_update_manager)
        assert formatted == "Never"
    
    def test_update_button_logic(self, mock_script_update_manager):
        """Test the logic behind the update button functionality."""
        def handle_update_button_click(manager):
            """Simulate update button click logic."""
            result = manager.update_scripts()
            
            response = {
                'success': result['success'],
                'message': result['message'],
                'error': result['error'],
                'should_clear_cache': result['success']  # Clear cache on successful update
            }
            
            if response['should_clear_cache']:
                manager.clear_cache()
            
            return response
        
        # Test successful update
        response = handle_update_button_click(mock_script_update_manager)
        
        assert response['success'] is True
        assert 'successfully' in response['message']
        assert response['error'] is None
        assert response['should_clear_cache'] is True
        mock_script_update_manager.clear_cache.assert_called_once()
        
        # Test failed update
        mock_script_update_manager.reset_mock()
        mock_script_update_manager.update_scripts.return_value = {
            'success': False,
            'error': 'Update failed',
            'message': 'Failed to update scripts'
        }
        
        response = handle_update_button_click(mock_script_update_manager)
        
        assert response['success'] is False
        assert response['error'] == 'Update failed'
        assert response['should_clear_cache'] is False
        mock_script_update_manager.clear_cache.assert_not_called()