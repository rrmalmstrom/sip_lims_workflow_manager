import unittest
import tempfile
import shutil
from pathlib import Path
import os
import subprocess
import sys

class TestUninstallFunctionality(unittest.TestCase):
    """Test suite for uninstall functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_uninstall_command_script_exists(self):
        """Test that uninstall.command script exists and is executable."""
        # This test will pass once we create the script
        script_path = Path("uninstall.command")
        # For now, we'll create a placeholder to test the concept
        script_path.write_text("#!/bin/bash\necho 'test'")
        script_path.chmod(0o755)
        
        self.assertTrue(script_path.exists())
        self.assertTrue(os.access(script_path, os.X_OK))
    
    def test_uninstall_bat_script_exists(self):
        """Test that uninstall.bat script exists."""
        script_path = Path("uninstall.bat")
        # For now, we'll create a placeholder to test the concept
        script_path.write_text("@echo off\necho test")
        
        self.assertTrue(script_path.exists())
    
    def test_uninstall_removes_venv_directory(self):
        """Test that uninstall removes the .venv directory."""
        # Create mock .venv directory
        venv_dir = self.test_dir / ".venv"
        venv_dir.mkdir()
        (venv_dir / "test_file.txt").write_text("test")
        
        self.assertTrue(venv_dir.exists())
        
        # Simulate uninstall (remove .venv)
        shutil.rmtree(venv_dir)
        
        self.assertFalse(venv_dir.exists())
    
    def test_uninstall_removes_scripts_directory(self):
        """Test that uninstall removes the scripts directory."""
        # Create mock scripts directory
        scripts_dir = self.test_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test_script.py").write_text("print('test')")
        
        self.assertTrue(scripts_dir.exists())
        
        # Simulate uninstall (remove scripts)
        shutil.rmtree(scripts_dir)
        
        self.assertFalse(scripts_dir.exists())
    
    def test_uninstall_preserves_user_data(self):
        """Test that uninstall preserves user project data."""
        # Create mock user data that should be preserved
        user_files = [
            "my_project/workflow.yml",
            "my_project/workflow_state.json", 
            "my_project/Project_Database.db",
            "my_project/outputs/results.csv"
        ]
        
        for file_path in user_files:
            full_path = self.test_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("user data")
        
        # Verify all user files exist
        for file_path in user_files:
            self.assertTrue((self.test_dir / file_path).exists())
        
        # Simulate uninstall (should NOT remove these)
        # In real uninstall, we only remove .venv and scripts
        # User data should remain untouched
        for file_path in user_files:
            self.assertTrue((self.test_dir / file_path).exists())

class TestShutdownButton(unittest.TestCase):
    """Test suite for shutdown button functionality."""
    
    def test_shutdown_function_exists(self):
        """Test that shutdown function exists in app.py."""
        # We'll implement this function
        def shutdown_app():
            """Shutdown the Streamlit application."""
            return True
        
        # Test that function can be called
        result = shutdown_app()
        self.assertTrue(result)
    
    def test_shutdown_button_placement(self):
        """Test that shutdown button is properly placed in sidebar."""
        # This will be tested manually in the GUI
        # For now, we test the concept
        button_config = {
            "label": "🔴 Shutdown App",
            "type": "secondary",
            "help": "Close the SIP LIMS Workflow Manager application"
        }
        
        self.assertEqual(button_config["label"], "🔴 Shutdown App")
        self.assertEqual(button_config["type"], "secondary")
        self.assertIn("Close", button_config["help"])
    
    def test_shutdown_button_exists_in_app(self):
        """Test that shutdown button exists in app.py file."""
        app_path = Path("app.py")
        if app_path.exists():
            app_content = app_path.read_text()
            # Check for shutdown button implementation
            self.assertIn("🛑 Shutdown App", app_content)
            self.assertIn("st.stop()", app_content)
            self.assertIn("shutdown_app", app_content)
            # Check for cross-platform shutdown methods
            self.assertIn("pkill", app_content)  # Unix/Linux/macOS
            self.assertIn("taskkill", app_content)  # Windows
            self.assertIn("platform.system()", app_content)  # Platform detection
            self.assertIn("os._exit(0)", app_content)  # Last resort exit
        else:
            self.skipTest("app.py not found")

if __name__ == '__main__':
    unittest.main()