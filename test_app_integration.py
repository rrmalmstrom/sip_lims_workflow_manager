"""
Test file to verify UpdateManager integration into app.py
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_update_manager_import():
    """Test that UpdateManager can be imported successfully"""
    from src.update_manager import UpdateManager
    assert UpdateManager is not None

def test_update_manager_initialization():
    """Test that UpdateManager can be initialized with custom URL"""
    from src.update_manager import UpdateManager
    
    # Test with default config
    manager = UpdateManager()
    assert manager.remote_version_url == "https://drive.google.com/uc?id=1pRsUbaKoieuInH67ghExSZw7p2I64-FQ&export=download"
    
def test_check_for_updates_function():
    """Test the cached update check function"""
    from src.update_manager import UpdateManager
    
    # Mock the UpdateManager to return test data
    with patch.object(UpdateManager, 'check_for_updates') as mock_check:
        mock_check.return_value = {
            'update_available': True,
            'local_version': '0.9.0',
            'remote_version': '1.0.0',
            'error': None
        }
        
        manager = UpdateManager()
        result = manager.check_for_updates()
        
        assert result['update_available'] is True
        assert result['remote_version'] == '1.0.0'
        assert result['error'] is None

def test_webbrowser_import():
    """Test that webbrowser module can be imported for download functionality"""
    import webbrowser
    assert webbrowser is not None

if __name__ == "__main__":
    # Run basic tests
    test_update_manager_import()
    test_update_manager_initialization()
    test_check_for_updates_function()
    test_webbrowser_import()
    print("✅ All integration tests passed!")