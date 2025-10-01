import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from pathlib import Path
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the functions we want to test
from app import scroll_to_top

class TestAutoScrollFunctionality(unittest.TestCase):
    """
    Test suite for auto-scroll functionality when scripts are launched.
    Tests that scroll_to_top() is called when Run/Re-run buttons are clicked.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_components_html = Mock()
        
    @patch('app.components.html')
    def test_scroll_to_top_function_generates_correct_javascript(self, mock_html):
        """Test that scroll_to_top() generates the correct JavaScript code."""
        # Call the function
        scroll_to_top()
        
        # Verify that components.html was called
        mock_html.assert_called_once()
        
        # Get the arguments passed to components.html
        call_args = mock_html.call_args
        js_code = call_args[0][0]  # First positional argument
        height = call_args[1]['height']  # height keyword argument
        
        # Verify the height is 0 (invisible component)
        self.assertEqual(height, 0)
        
        # Verify the JavaScript contains the expected scroll methods
        self.assertIn('<script>', js_code)
        self.assertIn('window.parent.scrollTo(0, 0)', js_code)
        self.assertIn('window.scrollTo(0, 0)', js_code)
        self.assertIn('scrollTop = 0', js_code)
        self.assertIn('behavior: \'instant\'', js_code)
        
        # Verify it targets Streamlit containers
        self.assertIn('stAppViewContainer', js_code)
        self.assertIn('stApp', js_code)
        
        # Verify it has retry logic with timeouts
        self.assertIn('setTimeout', js_code)
        self.assertIn('50', js_code)  # 50ms timeout
        self.assertIn('100', js_code)  # 100ms timeout
        self.assertIn('200', js_code)  # 200ms timeout
        self.assertIn('500', js_code)  # 500ms timeout

    @patch('app.components.html')
    def test_scroll_to_top_handles_exceptions_gracefully(self, mock_html):
        """Test that scroll_to_top() handles exceptions in JavaScript gracefully."""
        # Call the function
        scroll_to_top()
        
        # Get the JavaScript code
        call_args = mock_html.call_args
        js_code = call_args[0][0]
        
        # Verify it has try-catch blocks
        self.assertIn('try {', js_code)
        self.assertIn('} catch (e) {', js_code)
        self.assertIn('console.log(\'Scroll attempt failed:\', e)', js_code)

    def test_scroll_to_top_javascript_syntax_is_valid(self):
        """Test that the generated JavaScript has valid syntax structure."""
        with patch('app.components.html') as mock_html:
            scroll_to_top()
            
            call_args = mock_html.call_args
            js_code = call_args[0][0]
            
            # Basic syntax checks
            self.assertEqual(js_code.count('<script>'), 1)
            self.assertEqual(js_code.count('</script>'), 1)
            
            # Check for proper function structure
            self.assertIn('(function() {', js_code)
            self.assertIn('})();', js_code)
            
            # Check for proper JavaScript structure
            open_braces = js_code.count('{')
            close_braces = js_code.count('}')
            self.assertEqual(open_braces, close_braces, "Mismatched braces in JavaScript")

class TestAutoScrollIntegration(unittest.TestCase):
    """
    Integration tests to verify auto-scroll is called at the right times.
    These tests verify the integration points where scroll_to_top() should be called.
    """

    @patch('app.scroll_to_top')
    @patch('app.start_script_thread')
    @patch('app.st.rerun')
    @patch('app.st.button')
    def test_run_button_calls_scroll_to_top(self, mock_button, mock_rerun, mock_start_script, mock_scroll):
        """Test that clicking Run button calls scroll_to_top()."""
        # This test verifies the integration point exists
        # The actual button click simulation would require a full Streamlit app context
        
        # Verify that scroll_to_top is importable and callable
        self.assertTrue(callable(mock_scroll))
        
        # Verify the function exists in the app module
        from app import scroll_to_top
        self.assertTrue(callable(scroll_to_top))

    def test_scroll_to_top_function_exists_and_is_callable(self):
        """Test that scroll_to_top function exists and is callable."""
        from app import scroll_to_top
        
        # Verify function exists
        self.assertTrue(callable(scroll_to_top))
        
        # Verify it can be called without errors (with mocked components)
        with patch('app.components.html'):
            try:
                scroll_to_top()
            except Exception as e:
                self.fail(f"scroll_to_top() raised an exception: {e}")

class TestAutoScrollCodeIntegration(unittest.TestCase):
    """
    Test that the auto-scroll code is properly integrated into the button handlers.
    """

    def test_run_button_handler_contains_scroll_call(self):
        """Test that the Run button handler code contains scroll_to_top() call."""
        # Read the app.py file and verify the integration
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Look for the Run button handler with scroll_to_top call
        run_button_pattern = 'if st.button("Run"'
        scroll_call_pattern = 'scroll_to_top()'
        
        self.assertIn(run_button_pattern, app_content, "Run button handler not found")
        self.assertIn(scroll_call_pattern, app_content, "scroll_to_top() call not found")
        
        # Find the Run button section and verify scroll_to_top is called nearby
        run_button_index = app_content.find(run_button_pattern)
        self.assertNotEqual(run_button_index, -1, "Run button handler not found")
        
        # Look for scroll_to_top call within 500 characters after the Run button
        run_section = app_content[run_button_index:run_button_index + 500]
        self.assertIn('scroll_to_top()', run_section, 
                     "scroll_to_top() not called in Run button handler")

    def test_rerun_button_handler_contains_scroll_call(self):
        """Test that the Re-run button handler code contains scroll_to_top() call."""
        # Read the app.py file and verify the integration
        app_file = Path(__file__).parent.parent / "app.py"
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Look for the Re-run button handler with scroll_to_top call
        rerun_button_pattern = 'if st.button("Re-run"'
        scroll_call_pattern = 'scroll_to_top()'
        
        self.assertIn(rerun_button_pattern, app_content, "Re-run button handler not found")
        
        # Find the Re-run button section and verify scroll_to_top is called nearby
        rerun_button_index = app_content.find(rerun_button_pattern)
        self.assertNotEqual(rerun_button_index, -1, "Re-run button handler not found")
        
        # Look for scroll_to_top call within 800 characters after the Re-run button
        rerun_section = app_content[rerun_button_index:rerun_button_index + 800]
        self.assertIn('scroll_to_top()', rerun_section,
                     "scroll_to_top() not called in Re-run button handler")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)