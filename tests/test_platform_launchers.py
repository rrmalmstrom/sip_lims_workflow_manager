#!/usr/bin/env python3
"""
Test suite for platform-specific launchers (run.mac.command and run.windows.bat)

This test validates the launcher scripts without requiring the actual platforms.
"""

import pytest
import subprocess
import os
from pathlib import Path


class TestPlatformLaunchers:
    """Test platform-specific launcher scripts."""
    
    def test_mac_launcher_exists_and_executable(self):
        """Test that macOS launcher exists and is executable."""
        mac_launcher = Path("run.mac.command")
        
        assert mac_launcher.exists(), "run.mac.command should exist"
        assert os.access(mac_launcher, os.X_OK), "run.mac.command should be executable"
    
    def test_windows_launcher_exists(self):
        """Test that Windows launcher exists."""
        windows_launcher = Path("run.windows.bat")
        
        assert windows_launcher.exists(), "run.windows.bat should exist"
    
    def test_mac_launcher_syntax(self):
        """Test macOS launcher bash syntax."""
        mac_launcher = Path("run.mac.command")
        
        # Use bash -n to check syntax without executing
        result = subprocess.run(
            ["bash", "-n", str(mac_launcher)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Bash syntax error in run.mac.command: {result.stderr}"
    
    def test_mac_launcher_content(self):
        """Test macOS launcher contains expected content."""
        mac_launcher = Path("run.mac.command")
        content = mac_launcher.read_text()
        
        # Check for key components
        assert "#!/bin/bash" in content, "Should have bash shebang"
        assert "python3 run.py" in content, "Should call python3 run.py"
        assert '"$@"' not in content, "Should NOT pass through command line arguments"
        assert "%*" not in content, "Should NOT contain Windows-style argument passing"
        assert "SIP LIMS Workflow Manager - macOS Launcher" in content, "Should have proper title"
        assert "Press any key to close" in content, "Should pause at end"
    
    def test_windows_launcher_content(self):
        """Test Windows launcher contains expected content."""
        windows_launcher = Path("run.windows.bat")
        content = windows_launcher.read_text()
        
        # Check for key components
        assert "@echo off" in content, "Should have echo off"
        assert 'run.py' in content, "Should call run.py"
        assert '%*' not in content, "Should NOT pass through command line arguments"
        assert '"$@"' not in content, "Should NOT contain bash-style argument passing"
        assert "SIP LIMS Workflow Manager - Windows Launcher" in content, "Should have proper title"
        assert "pause" in content, "Should pause at end"
        assert "python3" in content or "python" in content, "Should try to find Python"
    
    def test_mac_launcher_calls_run_py_without_flags(self):
        """Test that macOS launcher calls run.py with no flags."""
        mac_launcher = Path("run.mac.command")
        content = mac_launcher.read_text()
        
        # Find the line that calls python3 run.py
        lines = content.split('\n')
        python_lines = [line for line in lines if 'python3 run.py' in line and not line.strip().startswith('#')]
        
        assert len(python_lines) == 1, "Should have exactly one python3 run.py call"
        python_line = python_lines[0].strip()
        
        # Should be exactly "python3 run.py" with no additional arguments
        assert python_line == 'python3 run.py', f"Should call 'python3 run.py' with no args, but found: '{python_line}'"
    
    def test_windows_launcher_calls_run_py_without_flags(self):
        """Test that Windows launcher calls run.py with no flags."""
        windows_launcher = Path("run.windows.bat")
        content = windows_launcher.read_text()
        
        # Find the line that calls run.py
        lines = content.split('\n')
        python_lines = [line for line in lines if 'run.py' in line and 'PYTHON_CMD' in line and not line.strip().startswith('REM')]
        
        assert len(python_lines) == 1, "Should have exactly one run.py call"
        python_line = python_lines[0].strip()
        
        # Should be exactly "%PYTHON_CMD%" run.py with no additional arguments
        expected = '"%PYTHON_CMD%" run.py'
        assert python_line == expected, f"Should call '{expected}' with no args, but found: '{python_line}'"
    
    def test_launchers_have_error_handling(self):
        """Test that both launchers have proper error handling."""
        mac_launcher = Path("run.mac.command")
        windows_launcher = Path("run.windows.bat")
        
        mac_content = mac_launcher.read_text()
        windows_content = windows_launcher.read_text()
        
        # macOS launcher should check for Python 3
        assert "command -v python3" in mac_content, "macOS launcher should check for python3"
        assert "Python 3 is not installed" in mac_content, "macOS launcher should have Python error message"
        
        # Windows launcher should check for Python
        assert "python3 --version" in windows_content, "Windows launcher should check for python3"
        assert "python --version" in windows_content, "Windows launcher should check for python"
        assert "Python is not installed" in windows_content, "Windows launcher should have Python error message"
        
        # Both should check for run.py
        assert 'run.py' in mac_content and 'not found' in mac_content, "macOS launcher should check for run.py"
        assert 'run.py' in windows_content and 'not exist' in windows_content, "Windows launcher should check for run.py"
    
    def test_launchers_have_proper_exit_codes(self):
        """Test that launchers handle exit codes properly."""
        mac_launcher = Path("run.mac.command")
        windows_launcher = Path("run.windows.bat")
        
        mac_content = mac_launcher.read_text()
        windows_content = windows_launcher.read_text()
        
        # macOS launcher should capture and return exit code
        assert "EXIT_CODE=$?" in mac_content, "macOS launcher should capture exit code"
        assert "exit $EXIT_CODE" in mac_content, "macOS launcher should return exit code"
        
        # Windows launcher should capture and return exit code
        assert "EXIT_CODE=!errorlevel!" in windows_content, "Windows launcher should capture exit code"
        assert "exit /b !EXIT_CODE!" in windows_content, "Windows launcher should return exit code"


class TestLauncherIntegration:
    """Integration tests for launcher functionality."""
    
    def test_mac_launcher_dry_run(self):
        """Test macOS launcher with a dry run approach."""
        # We can't fully test without running, but we can verify the script structure
        mac_launcher = Path("run.mac.command")
        
        # Check that the script would find run.py
        assert Path("run.py").exists(), "run.py should exist for launcher to find"
        
        # Verify the launcher is in the same directory as run.py
        assert mac_launcher.parent == Path("run.py").parent, "Launcher should be in same directory as run.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])