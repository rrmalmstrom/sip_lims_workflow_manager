#!/usr/bin/env python3
"""
Test-Driven Development verification of SSH key architecture fix.

This test suite verifies that:
1. SSH key manager supports multiple keys
2. Git update manager uses correct keys per repository
3. Setup process works with new key architecture
4. Update functionality works with correct SSH keys
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import os
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ssh_key_manager import SSHKeyManager
from src.git_update_manager import GitUpdateManager, create_update_manager


class TestSSHKeyArchitectureFix(unittest.TestCase):
    """Test suite for SSH key architecture fix verification."""
    
    def setUp(self):
        """Set up test environment with temporary SSH directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.ssh_dir = Path(self.temp_dir) / ".ssh"
        self.ssh_dir.mkdir(parents=True)
        
        # Create mock SSH keys for testing
        self.create_mock_ssh_keys()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def create_mock_ssh_keys(self):
        """Create mock SSH key files for testing."""
        # Create scripts deploy key
        scripts_key = self.ssh_dir / "scripts_deploy_key"
        scripts_pub = self.ssh_dir / "scripts_deploy_key.pub"
        
        scripts_key.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nMOCK_SCRIPTS_KEY\n-----END OPENSSH PRIVATE KEY-----\n")
        scripts_pub.write_text("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMockScriptsKey scripts-repo-deploy-key\n")
        
        # Create app deploy key
        app_key = self.ssh_dir / "app_deploy_key"
        app_pub = self.ssh_dir / "app_deploy_key.pub"
        
        app_key.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nMOCK_APP_KEY\n-----END OPENSSH PRIVATE KEY-----\n")
        app_pub.write_text("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMockAppKey app-repo-deploy-key\n")
        
        # Set proper permissions
        scripts_key.chmod(0o600)
        app_key.chmod(0o600)
        scripts_pub.chmod(0o644)
        app_pub.chmod(0o644)
    
    def test_ssh_key_manager_supports_multiple_keys(self):
        """Test that SSH key manager can handle different key names."""
        # Test scripts key manager
        scripts_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="scripts_deploy_key")
        self.assertEqual(scripts_manager.key_name, "scripts_deploy_key")
        self.assertEqual(scripts_manager.private_key_path.name, "scripts_deploy_key")
        self.assertEqual(scripts_manager.public_key_path.name, "scripts_deploy_key.pub")
        
        # Test app key manager
        app_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="app_deploy_key")
        self.assertEqual(app_manager.key_name, "app_deploy_key")
        self.assertEqual(app_manager.private_key_path.name, "app_deploy_key")
        self.assertEqual(app_manager.public_key_path.name, "app_deploy_key.pub")
    
    def test_ssh_key_validation_works_with_new_keys(self):
        """Test that SSH key validation works with the new key architecture."""
        # Test scripts key validation
        scripts_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="scripts_deploy_key")
        validation = scripts_manager.validate_key_security()
        
        self.assertTrue(validation['valid'], f"Scripts key validation failed: {validation['issues']}")
        self.assertEqual(validation['key_info']['type'], 'ed25519')
        self.assertEqual(validation['key_info']['strength'], 'excellent')
        
        # Test app key validation
        app_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="app_deploy_key")
        validation = app_manager.validate_key_security()
        
        self.assertTrue(validation['valid'], f"App key validation failed: {validation['issues']}")
        self.assertEqual(validation['key_info']['type'], 'ed25519')
        self.assertEqual(validation['key_info']['strength'], 'excellent')
    
    def test_git_update_manager_uses_correct_keys(self):
        """Test that GitUpdateManager uses the correct SSH key based on repository type."""
        # Create temporary repo directories
        scripts_repo = Path(self.temp_dir) / "scripts"
        app_repo = Path(self.temp_dir) / "app"
        scripts_repo.mkdir()
        app_repo.mkdir()
        
        # Test scripts manager uses scripts key
        scripts_manager = GitUpdateManager("scripts", scripts_repo, cache_ttl=0)
        scripts_manager.ssh_manager.ssh_dir = self.ssh_dir  # Override for test
        self.assertEqual(scripts_manager.ssh_manager.key_name, "scripts_deploy_key")
        
        # Test app manager uses app key
        app_manager = GitUpdateManager("application", app_repo, cache_ttl=0)
        app_manager.ssh_manager.ssh_dir = self.ssh_dir  # Override for test
        self.assertEqual(app_manager.ssh_manager.key_name, "app_deploy_key")
    
    def test_create_update_manager_factory_function(self):
        """Test that the factory function creates managers with correct SSH keys."""
        # Mock the base path to use our temp directory
        original_file_path = Path(__file__).parent.parent
        
        # Test scripts manager creation
        scripts_manager = create_update_manager("scripts", base_path=Path(self.temp_dir))
        self.assertEqual(scripts_manager.repo_type, "scripts")
        self.assertEqual(scripts_manager.ssh_manager.key_name, "scripts_deploy_key")
        
        # Test application manager creation
        app_manager = create_update_manager("application", base_path=Path(self.temp_dir))
        self.assertEqual(app_manager.repo_type, "application")
        self.assertEqual(app_manager.ssh_manager.key_name, "app_deploy_key")
    
    def test_ssh_command_generation_uses_correct_keys(self):
        """Test that SSH commands are generated with the correct key paths."""
        # Test scripts SSH command
        scripts_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="scripts_deploy_key")
        scripts_cmd = scripts_manager.get_ssh_command()
        self.assertIn("scripts_deploy_key", scripts_cmd)
        self.assertNotIn("app_deploy_key", scripts_cmd)
        
        # Test app SSH command
        app_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="app_deploy_key")
        app_cmd = app_manager.get_ssh_command()
        self.assertIn("app_deploy_key", app_cmd)
        self.assertNotIn("scripts_deploy_key", app_cmd)
    
    def test_git_environment_variables_use_correct_keys(self):
        """Test that Git environment variables point to the correct SSH keys."""
        # Test scripts Git environment
        scripts_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="scripts_deploy_key")
        scripts_env = scripts_manager.create_git_env()
        self.assertIn("scripts_deploy_key", scripts_env['GIT_SSH_COMMAND'])
        
        # Test app Git environment
        app_manager = SSHKeyManager(ssh_dir=self.ssh_dir, key_name="app_deploy_key")
        app_env = app_manager.create_git_env()
        self.assertIn("app_deploy_key", app_env['GIT_SSH_COMMAND'])
    
    def test_repository_configuration_mapping(self):
        """Test that repository URLs are correctly mapped to SSH keys."""
        scripts_manager = GitUpdateManager("scripts", Path(self.temp_dir) / "scripts", cache_ttl=0)
        app_manager = GitUpdateManager("application", Path(self.temp_dir), cache_ttl=0)
        
        # Verify repository URLs
        self.assertEqual(
            scripts_manager.config['repo_url'], 
            "git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git"
        )
        self.assertEqual(
            app_manager.config['repo_url'], 
            "git@github.com:rrmalmstrom/sip_lims_workflow_manager.git"
        )
        
        # Verify SSH key mapping
        self.assertEqual(scripts_manager.ssh_manager.key_name, "scripts_deploy_key")
        self.assertEqual(app_manager.ssh_manager.key_name, "app_deploy_key")


class TestRealWorldIntegration(unittest.TestCase):
    """Integration tests using the actual project structure."""
    
    def setUp(self):
        """Set up for real-world testing."""
        self.project_root = Path(__file__).parent
        self.ssh_dir = self.project_root / ".ssh"
    
    def test_actual_ssh_keys_exist(self):
        """Test that the actual SSH keys exist and have correct permissions."""
        scripts_key = self.ssh_dir / "scripts_deploy_key"
        app_key = self.ssh_dir / "app_deploy_key"
        
        # Check keys exist
        self.assertTrue(scripts_key.exists(), "Scripts deploy key not found")
        self.assertTrue(app_key.exists(), "App deploy key not found")
        
        # Check permissions
        scripts_stat = scripts_key.stat()
        app_stat = app_key.stat()
        
        self.assertEqual(scripts_stat.st_mode & 0o777, 0o600, "Scripts key permissions incorrect")
        self.assertEqual(app_stat.st_mode & 0o777, 0o600, "App key permissions incorrect")
    
    def test_actual_update_managers_work(self):
        """Test that the actual update managers can be created and work."""
        try:
            # Test scripts manager
            scripts_manager = create_update_manager("scripts")
            self.assertEqual(scripts_manager.ssh_manager.key_name, "scripts_deploy_key")
            
            # Test app manager
            app_manager = create_update_manager("application")
            self.assertEqual(app_manager.ssh_manager.key_name, "app_deploy_key")
            
            print("✅ Update managers created successfully with correct SSH keys")
            
        except Exception as e:
            self.fail(f"Failed to create update managers: {e}")
    
    def test_ssh_key_validation_on_actual_keys(self):
        """Test SSH key validation on the actual deployed keys."""
        # Test scripts key
        scripts_manager = SSHKeyManager(key_name="scripts_deploy_key")
        scripts_validation = scripts_manager.validate_key_security()
        
        if not scripts_validation['valid']:
            self.fail(f"Scripts SSH key validation failed: {scripts_validation['issues']}")
        
        # Test app key
        app_manager = SSHKeyManager(key_name="app_deploy_key")
        app_validation = app_manager.validate_key_security()
        
        if not app_validation['valid']:
            self.fail(f"App SSH key validation failed: {app_validation['issues']}")
        
        print("✅ SSH key validation passed for both keys")


def run_comprehensive_test_suite():
    """Run the complete test suite and provide detailed results."""
    print("🧪 Running SSH Key Architecture Fix Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSSHKeyArchitectureFix))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        print("\n🎉 SSH key architecture fix is working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        if result.failures:
            print("\n💥 FAILURES:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback}")
        
        if result.errors:
            print("\n🚨 ERRORS:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback}")
        
        return False


if __name__ == "__main__":
    success = run_comprehensive_test_suite()
    sys.exit(0 if success else 1)