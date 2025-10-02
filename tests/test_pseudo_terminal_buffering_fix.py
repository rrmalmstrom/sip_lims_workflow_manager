"""
Test suite for pseudo-terminal buffering issue fix.

This test reproduces the specific issue where terminal output shows 
"Waiting for script output..." but the script prompts are actually 
available in the queue and not being displayed until user interaction.
"""

import pytest
import time
import queue
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from logic import ScriptRunner


class TestPseudoTerminalBufferingIssue:
    """
    Test suite specifically targeting the buffering issue where:
    1. Script produces output (like prompts)
    2. Output sits in queue but isn't displayed 
    3. User sees "Waiting for script output..." instead of actual prompts
    4. Output only becomes visible after user interaction (clicking Send Input)
    """
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temp directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_current_polling_logic_misses_queued_output(self):
        """
        FAILING TEST: Reproduces the exact issue described.
        
        This test simulates the current app.py polling logic (lines 492-499)
        and demonstrates that it only retrieves one item from the queue per cycle,
        leaving subsequent output (like prompts) invisible to the user.
        """
        # Simulate ScriptRunner with output queue containing multiple items
        mock_runner = Mock()
        mock_runner.output_queue = queue.Queue()
        
        # Simulate a script that produces initialization output followed by a prompt
        # This is the exact scenario described in the issue
        mock_runner.output_queue.put("Script starting...\n")
        mock_runner.output_queue.put("Loading configuration...\n") 
        mock_runner.output_queue.put("Enter the minimum volume for sample matrix tubes (default 60ul): ")
        
        # Simulate current app.py polling logic (single attempt per UI cycle)
        terminal_output = ""
        try:
            output = mock_runner.output_queue.get_nowait()
            if output is not None:
                terminal_output += output
                # DEBUG: Add logging to see what we got
                print(f"DEBUG: Current polling retrieved: '{output}'")
        except queue.Empty:
            pass  # No new output
        
        # ASSERTION: This demonstrates the problem
        # Current logic only gets the first item, leaving the prompt invisible
        assert terminal_output == "Script starting...\n"
        
        # The critical prompt is still in the queue, invisible to user
        remaining_items = []
        while not mock_runner.output_queue.empty():
            try:
                item = mock_runner.output_queue.get_nowait()
                remaining_items.append(item)
            except queue.Empty:
                break
        
        # DEBUG: Show what's left in queue
        print(f"DEBUG: Items left in queue: {remaining_items}")
        
        # This is the bug - the prompt is there but not displayed!
        assert "Enter the minimum volume" in str(remaining_items)
        assert len(remaining_items) == 2  # Two items left behind
        
        # User sees "Waiting for script output..." instead of the actual prompt
        # This is exactly the issue described in the problem statement
    
    def test_enhanced_polling_logic_retrieves_all_output(self):
        """
        PASSING TEST: Demonstrates the proposed fix.
        
        Enhanced polling logic that checks the queue multiple times
        to ensure all available output is retrieved in a single UI cycle.
        """
        # Same setup as above
        mock_runner = Mock()
        mock_runner.output_queue = queue.Queue()
        
        # Same script output scenario
        mock_runner.output_queue.put("Script starting...\n")
        mock_runner.output_queue.put("Loading configuration...\n")
        mock_runner.output_queue.put("Enter the minimum volume for sample matrix tubes (default 60ul): ")
        
        # ENHANCED polling logic (proposed fix)
        terminal_output = ""
        output_received = False
        
        # Poll multiple times with small delays to catch all queued output
        for attempt in range(10):  # Increased from 3 to 10 attempts
            try:
                output = mock_runner.output_queue.get_nowait()
                if output is not None:
                    terminal_output += output
                    output_received = True
                    # DEBUG: Show what we're collecting
                    print(f"DEBUG: Enhanced polling attempt {attempt + 1} retrieved: '{output}'")
            except queue.Empty:
                if output_received:
                    # If we got some output, wait a tiny bit and try again
                    # This handles cases where output arrives in quick succession
                    time.sleep(0.01)
                    continue
                else:
                    break  # No output available, stop polling
        
        # ASSERTION: Enhanced logic gets ALL output including the prompt
        expected_full_output = (
            "Script starting...\n"
            "Loading configuration...\n" 
            "Enter the minimum volume for sample matrix tubes (default 60ul): "
        )
        assert terminal_output == expected_full_output
        
        # Queue should be empty now
        assert mock_runner.output_queue.qsize() == 0
        
        # DEBUG: Confirm we got the critical prompt
        assert "Enter the minimum volume" in terminal_output
        print(f"DEBUG: Full terminal output: '{terminal_output}'")
    
    def test_real_script_runner_output_timing(self):
        """
        Test with actual ScriptRunner to understand real-world timing issues.
        
        This test uses mocking to simulate the PTY reading behavior and
        verify that output appears in the queue as expected.
        """
        with patch('subprocess.Popen') as mock_popen, \
             patch('pty.openpty') as mock_openpty, \
             patch('os.read') as mock_read, \
             patch('select.select') as mock_select:
            
            # Setup mocks for PTY operations
            mock_openpty.return_value = (10, 11)  # master_fd, slave_fd
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Still running
            mock_popen.return_value = mock_process
            
            # Simulate script producing output in sequence
            output_sequence = [
                b"Initializing...\n",
                b"Enter the minimum volume for sample matrix tubes (default 60ul): "
            ]
            mock_read.side_effect = output_sequence
            mock_select.return_value = ([10], [], [])  # Data always ready
            
            # Create and start ScriptRunner
            script_runner = ScriptRunner(self.temp_dir)
            script_runner.run("test_script.py")
            
            # Give the reader thread time to process output
            time.sleep(0.1)
            
            # Check that output appears in queue
            collected_output = []
            while True:
                try:
                    output = script_runner.output_queue.get_nowait()
                    if output is not None:
                        collected_output.append(output)
                        # DEBUG: Show what ScriptRunner produced
                        print(f"DEBUG: ScriptRunner output: '{output}'")
                except queue.Empty:
                    break
            
            # Verify we got the expected output
            assert len(collected_output) >= 1
            full_output = "".join(collected_output)
            
            # The critical test - prompt should be available immediately
            assert "Enter the minimum volume" in full_output
            
            # Clean up
            script_runner.stop()
    
    def test_select_timeout_affects_responsiveness(self):
        """
        Test how the select() timeout in ScriptRunner affects output responsiveness.
        
        Current code uses 0.02s timeout. This test verifies that's appropriate
        for immediate output visibility.
        """
        with patch('subprocess.Popen') as mock_popen, \
             patch('pty.openpty') as mock_openpty, \
             patch('select.select') as mock_select:
            
            # Setup mocks
            mock_openpty.return_value = (10, 11)
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # Track select() calls to verify timeout values
            select_calls = []
            def track_select_calls(*args):
                select_calls.append(args)
                return ([], [], [])  # No data ready
            
            mock_select.side_effect = track_select_calls
            
            # Start ScriptRunner
            script_runner = ScriptRunner(self.temp_dir)
            script_runner.run("test_script.py")
            
            # Give time for multiple select calls
            time.sleep(0.1)
            
            # Verify select was called with appropriate timeout
            assert len(select_calls) > 0
            
            # Check the timeout value used (should be 0.02 based on current code)
            if select_calls:
                timeout_used = select_calls[0][3]  # Fourth argument is timeout
                # DEBUG: Show actual timeout
                print(f"DEBUG: Select timeout used: {timeout_used}")
                
                # Timeout should be small for responsiveness
                assert timeout_used <= 0.1, f"Select timeout too large: {timeout_used}"
                
                # Current implementation uses 0.02s - verify this is reasonable
                assert timeout_used == 0.02, f"Expected 0.02s timeout, got {timeout_used}"
            
            # Clean up
            script_runner.stop()


class TestPollingLogicComparison:
    """
    Direct comparison between current and enhanced polling logic.
    """
    
    def test_current_vs_enhanced_polling_side_by_side(self):
        """
        Side-by-side comparison of current vs enhanced polling logic.
        
        This test clearly demonstrates the difference in behavior.
        """
        # Setup identical queue scenarios
        current_queue = queue.Queue()
        enhanced_queue = queue.Queue()
        
        # Add identical output to both queues
        test_outputs = [
            "Starting script execution...\n",
            "Configuring environment...\n", 
            "Enter the minimum volume for sample matrix tubes (default 60ul): ",
            "Waiting for user input...\n"
        ]
        
        for output in test_outputs:
            current_queue.put(output)
            enhanced_queue.put(output)
        
        # === CURRENT POLLING LOGIC (from app.py lines 492-499) ===
        current_terminal_output = ""
        try:
            output = current_queue.get_nowait()
            if output is not None:
                current_terminal_output += output
        except queue.Empty:
            pass
        
        # === ENHANCED POLLING LOGIC (proposed fix) ===
        enhanced_terminal_output = ""
        output_received = False
        
        for attempt in range(10):  # Multiple attempts
            try:
                output = enhanced_queue.get_nowait()
                if output is not None:
                    enhanced_terminal_output += output
                    output_received = True
            except queue.Empty:
                if output_received:
                    time.sleep(0.01)  # Small delay, then try again
                    continue
                else:
                    break
        
        # === COMPARISON RESULTS ===
        print(f"DEBUG: Current logic retrieved: '{current_terminal_output}'")
        print(f"DEBUG: Enhanced logic retrieved: '{enhanced_terminal_output}'")
        print(f"DEBUG: Current queue remaining: {current_queue.qsize()}")
        print(f"DEBUG: Enhanced queue remaining: {enhanced_queue.qsize()}")
        
        # Current logic only gets first item
        assert current_terminal_output == "Starting script execution...\n"
        assert current_queue.qsize() == 3  # 3 items left behind
        
        # Enhanced logic gets everything
        expected_full = "".join(test_outputs)
        assert enhanced_terminal_output == expected_full
        assert enhanced_queue.qsize() == 0  # All items retrieved
        
        # Most importantly - enhanced logic gets the critical prompt
        assert "Enter the minimum volume" in enhanced_terminal_output
        assert "Enter the minimum volume" not in current_terminal_output


if __name__ == "__main__":
    # Run tests with verbose output to see debug messages
    pytest.main([__file__, "-v", "-s"])