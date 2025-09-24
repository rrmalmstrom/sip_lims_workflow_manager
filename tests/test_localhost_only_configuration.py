import unittest
import os
from pathlib import Path


class TestLocalhostOnlyConfiguration(unittest.TestCase):
    """Test that run scripts are configured to only bind to localhost"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_root = Path(__file__).parent.parent
        self.run_command_path = self.project_root / "run.command"
        self.run_bat_path = self.project_root / "run.bat"
    
    def test_run_command_exists(self):
        """Test that run.command file exists"""
        self.assertTrue(self.run_command_path.exists(), "run.command file should exist")
    
    def test_run_bat_exists(self):
        """Test that run.bat file exists"""
        self.assertTrue(self.run_bat_path.exists(), "run.bat file should exist")
    
    def test_run_command_contains_localhost_binding(self):
        """Test that run.command contains --server.address=127.0.0.1"""
        with open(self.run_command_path, 'r') as f:
            content = f.read()
        
        # Check that both streamlit run commands contain the localhost binding
        streamlit_lines = [line for line in content.split('\n') if 'streamlit run' in line]
        
        self.assertGreater(len(streamlit_lines), 0, "Should contain streamlit run commands")
        
        for line in streamlit_lines:
            self.assertIn('--server.address=127.0.0.1', line, 
                         f"Streamlit command should bind to localhost only: {line}")
    
    def test_run_bat_contains_localhost_binding(self):
        """Test that run.bat contains --server.address=127.0.0.1"""
        with open(self.run_bat_path, 'r') as f:
            content = f.read()
        
        # Check that both streamlit run commands contain the localhost binding
        streamlit_lines = [line for line in content.split('\n') if 'streamlit run' in line]
        
        self.assertGreater(len(streamlit_lines), 0, "Should contain streamlit run commands")
        
        for line in streamlit_lines:
            self.assertIn('--server.address=127.0.0.1', line, 
                         f"Streamlit command should bind to localhost only: {line}")
    
    def test_run_command_maintains_other_parameters(self):
        """Test that run.command maintains existing parameters"""
        with open(self.run_command_path, 'r') as f:
            content = f.read()
        
        streamlit_lines = [line for line in content.split('\n') if 'streamlit run' in line]
        
        for line in streamlit_lines:
            # Should still have headless mode
            self.assertIn('--server.headless=true', line, 
                         f"Should maintain headless mode: {line}")
            # Should still have app.py
            self.assertIn('app.py', line, 
                         f"Should still run app.py: {line}")
    
    def test_run_bat_maintains_other_parameters(self):
        """Test that run.bat maintains existing parameters"""
        with open(self.run_bat_path, 'r') as f:
            content = f.read()
        
        streamlit_lines = [line for line in content.split('\n') if 'streamlit run' in line]
        
        for line in streamlit_lines:
            # Should still have headless mode
            self.assertIn('--server.headless=true', line, 
                         f"Should maintain headless mode: {line}")
            # Should still have app.py
            self.assertIn('app.py', line, 
                         f"Should still run app.py: {line}")
    
    def test_run_command_parameter_order(self):
        """Test that parameters are in correct order in run.command"""
        with open(self.run_command_path, 'r') as f:
            content = f.read()
        
        streamlit_lines = [line for line in content.split('\n') if 'streamlit run' in line]
        
        for line in streamlit_lines:
            # Find positions of key parameters
            app_pos = line.find('app.py')
            headless_pos = line.find('--server.headless=true')
            address_pos = line.find('--server.address=127.0.0.1')
            
            # Verify order: app.py should come first, then server parameters
            self.assertLess(app_pos, headless_pos, "app.py should come before server parameters")
            self.assertLess(app_pos, address_pos, "app.py should come before server parameters")
    
    def test_run_bat_parameter_order(self):
        """Test that parameters are in correct order in run.bat"""
        with open(self.run_bat_path, 'r') as f:
            content = f.read()
        
        streamlit_lines = [line for line in content.split('\n') if 'streamlit run' in line]
        
        for line in streamlit_lines:
            # Find positions of key parameters
            app_pos = line.find('app.py')
            headless_pos = line.find('--server.headless=true')
            address_pos = line.find('--server.address=127.0.0.1')
            
            # Verify order: app.py should come first, then server parameters
            self.assertLess(app_pos, headless_pos, "app.py should come before server parameters")
            self.assertLess(app_pos, address_pos, "app.py should come before server parameters")


if __name__ == '__main__':
    unittest.main()