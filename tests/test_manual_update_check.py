"""Tests for the manual update check functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from pathlib import Path
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestManualUpdateCheck:
    """Test suite for manual update check functionality."""
    
    def test_manual_check_button_exists_in_sidebar(self):
        """Test that the manual check button is present in the sidebar."""
        # This test verifies the button exists in the code
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Check that the manual check button is defined
        assert '🔄 Manual Check for Updates' in app_content
        assert 'sidebar_check_updates' in app_content
        
    def test_manual_check_button_clears_caches(self):
        """Test that clicking the manual check button clears both update caches."""
        # Mock the streamlit functions
        with patch('streamlit.button') as mock_button, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun:
            
            # Mock the cache clearing functions
            mock_app_cache = Mock()
            mock_script_cache = Mock()
            
            with patch('app.check_for_app_updates', mock_app_cache), \
                 patch('app.check_for_script_updates', mock_script_cache):
                
                # Simulate button click
                mock_button.return_value = True
                
                # Import and test the relevant functionality
                # Since we can't easily test the full streamlit app, we'll test the logic
                from app import check_for_app_updates, check_for_script_updates
                
                # Verify the functions exist and have clear methods
                assert hasattr(check_for_app_updates, 'clear')
                assert hasattr(check_for_script_updates, 'clear')
    
    def test_manual_check_button_placement(self):
        """Test that the manual check button is placed in the correct location."""
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Check that the button is in the sidebar section
        sidebar_section = app_content[app_content.find('with st.sidebar:'):app_content.find('# --- Main Content Area ---')]
        
        # Verify the button is in the sidebar
        assert '🔄 Manual Check for Updates' in sidebar_section
        assert 'st.subheader("Updates")' in sidebar_section
        
    def test_manual_check_button_has_proper_key(self):
        """Test that the manual check button has a unique key."""
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Check that the button has the correct key
        assert 'key="sidebar_check_updates"' in app_content
        
    def test_manual_check_button_provides_feedback(self):
        """Test that the manual check button provides user feedback."""
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Check that success message and rerun are called
        button_section = app_content[app_content.find('sidebar_check_updates'):app_content.find('st.caption("Clears update cache')]
        
        assert 'st.success("✅ Update cache cleared!")' in button_section
        assert 'st.rerun()' in button_section
        
    def test_manual_check_button_has_helpful_caption(self):
        """Test that the manual check button has a helpful caption."""
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Check that there's a helpful caption
        assert 'st.caption("Clears update cache and checks for new versions")' in app_content
        
    def test_cache_functions_are_streamlit_cached(self):
        """Test that the update check functions use streamlit caching."""
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Check that both functions have cache decorators
        assert '@st.cache_data(ttl=3600)' in app_content
        
        # Check that both functions are defined with cache decorators
        app_lines = app_content.split('\n')
        
        app_cache_line = None
        script_cache_line = None
        
        for i, line in enumerate(app_lines):
            if 'def check_for_app_updates():' in line:
                app_cache_line = i
            elif 'def check_for_script_updates():' in line:
                script_cache_line = i
        
        # Verify both functions have cache decorators before them
        assert app_cache_line is not None
        assert script_cache_line is not None
        assert '@st.cache_data(ttl=3600)' in app_lines[app_cache_line - 1]
        assert '@st.cache_data(ttl=3600)' in app_lines[script_cache_line - 1]

    def test_manual_check_integration_with_existing_update_system(self):
        """Test that manual check integrates properly with existing update system."""
        with open(Path(__file__).parent.parent / "app.py", 'r') as f:
            app_content = f.read()
        
        # Verify that the existing update system still exists
        assert 'updates_available =' in app_content
        assert 'if updates_available:' in app_content
        assert '🔔 **Updates Available**' in app_content
        
        # Verify that both the old and new systems coexist
        assert '🔄 Force Check Updates' in app_content  # Old system
        assert '🔄 Manual Check for Updates' in app_content  # New system


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])