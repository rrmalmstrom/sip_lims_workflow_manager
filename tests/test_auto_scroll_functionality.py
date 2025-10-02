import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from pathlib import Path
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestAutoScrollRemoval(unittest.TestCase):
    """
    Test suite to verify that auto-scroll functionality has been properly removed.
    Auto-scroll was causing usability issues and has been intentionally removed.
    """

    def test_scroll_to_top_function_removed(self):
        """Test that scroll_to_top function has been removed from app.py."""
        # Read the app.py file
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Verify that scroll_to_top function definition is not present
        self.assertNotIn('def scroll_to_top():', app_content,
                        "scroll_to_top function should be removed")

    def test_scroll_to_top_calls_removed(self):
        """Test that scroll_to_top() calls have been removed from button handlers."""
        # Read the app.py file
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Verify that scroll_to_top() calls are not present
        self.assertNotIn('scroll_to_top()', app_content,
                        "scroll_to_top() calls should be removed from button handlers")

    def test_run_button_handler_no_scroll_call(self):
        """Test that the Run button handler does not contain scroll_to_top() call."""
        # Read the app.py file
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Look for the Run button handler
        run_button_pattern = 'if st.button("Run"'
        self.assertIn(run_button_pattern, app_content, "Run button handler not found")
        
        # Find the Run button section and verify scroll_to_top is NOT called
        run_button_index = app_content.find(run_button_pattern)
        self.assertNotEqual(run_button_index, -1, "Run button handler not found")
        
        # Look for scroll_to_top call within 500 characters after the Run button
        run_section = app_content[run_button_index:run_button_index + 500]
        self.assertNotIn('scroll_to_top()', run_section,
                        "scroll_to_top() should not be called in Run button handler")

    def test_rerun_button_handler_no_scroll_call(self):
        """Test that the Re-run button handler does not contain scroll_to_top() call."""
        # Read the app.py file
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Look for the Re-run button handler
        rerun_button_pattern = 'if st.button("Re-run"'
        self.assertIn(rerun_button_pattern, app_content, "Re-run button handler not found")
        
        # Find the Re-run button section and verify scroll_to_top is NOT called
        rerun_button_index = app_content.find(rerun_button_pattern)
        self.assertNotEqual(rerun_button_index, -1, "Re-run button handler not found")
        
        # Look for scroll_to_top call within 800 characters after the Re-run button
        rerun_section = app_content[rerun_button_index:rerun_button_index + 800]
        self.assertNotIn('scroll_to_top()', rerun_section,
                        "scroll_to_top() should not be called in Re-run button handler")

    def test_auto_scroll_removal_comment_present(self):
        """Test that a comment indicating auto-scroll removal is present."""
        # Read the app.py file
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Verify that removal comment is present
        self.assertIn('Auto-scroll functionality removed', app_content,
                     "Comment about auto-scroll removal should be present")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)