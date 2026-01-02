#!/usr/bin/env python3
"""
TDD Test Suite for New Deterministic Build Workflow
Tests all aspects of the new script-based deterministic build system
"""

import subprocess
import os
import tempfile
import shutil
import json
from pathlib import Path

class TestNewDeterministicWorkflow:
    """Comprehensive test suite for new deterministic build workflow"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_results = []
    
    def log_test(self, test_name, passed, message=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append((test_name, passed, message))
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def test_build_script_exists_and_executable(self):
        """Test that build_image_from_lock_files.sh exists and is executable"""
        script_path = self.project_root / "build" / "build_image_from_lock_files.sh"
        
        if not script_path.exists():
            self.log_test("Build script exists", False, "build_image_from_lock_files.sh not found")
            return False
        
        is_executable = os.access(script_path, os.X_OK)
        message = "Script is executable" if is_executable else "Script is not executable"
        self.log_test("Build script executable", is_executable, message)
        return is_executable
    
    def test_push_script_exists_and_executable(self):
        """Test that push_image_to_github.sh exists and is executable"""
        script_path = self.project_root / "build" / "push_image_to_github.sh"
        
        if not script_path.exists():
            self.log_test("Push script exists", False, "push_image_to_github.sh not found")
            return False
        
        is_executable = os.access(script_path, os.X_OK)
        message = "Script is executable" if is_executable else "Script is not executable"
        self.log_test("Push script executable", is_executable, message)
        return is_executable
    
    def test_build_script_validates_prerequisites(self):
        """Test that build script properly validates prerequisites"""
        script_path = self.project_root / "build" / "build_image_from_lock_files.sh"
        
        # Test with missing lock files (backup and remove temporarily)
        conda_lock_backup = None
        requirements_lock_backup = None
        
        try:
            # Backup lock files
            if (self.project_root / "conda-lock.txt").exists():
                conda_lock_backup = (self.project_root / "conda-lock.txt").read_text()
                (self.project_root / "conda-lock.txt").unlink()
            
            # Run script and expect failure
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True, timeout=10)
            
            # Should fail with missing conda-lock.txt
            if result.returncode != 0 and "conda-lock.txt not found" in result.stdout:
                self.log_test("Build script validates missing conda-lock.txt", True, 
                            "Correctly detects missing conda-lock.txt")
                validation_passed = True
            else:
                self.log_test("Build script validates missing conda-lock.txt", False, 
                            f"Unexpected result: {result.stdout}")
                validation_passed = False
        
        except subprocess.TimeoutExpired:
            self.log_test("Build script validates missing conda-lock.txt", False, 
                        "Script timed out")
            validation_passed = False
        
        finally:
            # Restore lock files
            if conda_lock_backup:
                (self.project_root / "conda-lock.txt").write_text(conda_lock_backup)
        
        return validation_passed
    
    def test_push_script_validates_local_image(self):
        """Test that push script validates local image exists"""
        script_path = self.project_root / "build" / "push_image_to_github.sh"
        
        # Remove local image if it exists
        try:
            subprocess.run(["docker", "rmi", "sip-lims-workflow-manager:latest"], 
                         capture_output=True, timeout=10)
        except:
            pass  # Image might not exist
        
        try:
            # Run push script without local image
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True, timeout=10)
            
            # Should fail with missing local image
            if result.returncode != 0 and "Local image" in result.stdout and "not found" in result.stdout:
                self.log_test("Push script validates missing local image", True, 
                            "Correctly detects missing local image")
                return True
            else:
                self.log_test("Push script validates missing local image", False, 
                            f"Unexpected result: {result.stdout}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Push script validates missing local image", False, 
                        "Script timed out")
            return False
    
    def test_build_script_creates_local_image(self):
        """Test that build script successfully creates local image"""
        script_path = self.project_root / "build" / "build_image_from_lock_files.sh"
        
        # Remove existing local image
        try:
            subprocess.run(["docker", "rmi", "sip-lims-workflow-manager:latest"], 
                         capture_output=True, timeout=10)
        except:
            pass  # Image might not exist
        
        try:
            # Run build script
            print("    Running build script (this may take a while)...")
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Check if image was created
                check_result = subprocess.run(
                    ["docker", "images", "sip-lims-workflow-manager:latest", "--format", "{{.Repository}}"],
                    capture_output=True, text=True, timeout=10
                )
                
                if "sip-lims-workflow-manager" in check_result.stdout:
                    self.log_test("Build script creates local image", True, 
                                "Successfully built sip-lims-workflow-manager:latest")
                    return True
                else:
                    self.log_test("Build script creates local image", False, 
                                "Image not found after build")
                    return False
            else:
                self.log_test("Build script creates local image", False, 
                            f"Build failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Build script creates local image", False, 
                        "Build script timed out (>5 minutes)")
            return False
    
    def test_push_script_tags_image(self):
        """Test that push script properly tags image for GitHub registry"""
        script_path = self.project_root / "build" / "push_image_to_github.sh"
        
        # Check if local image exists
        try:
            check_result = subprocess.run(
                ["docker", "images", "sip-lims-workflow-manager:latest", "--format", "{{.Repository}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if "sip-lims-workflow-manager" not in check_result.stdout:
                self.log_test("Push script tags image", False, 
                            "Local image not available for tagging test")
                return False
        except:
            self.log_test("Push script tags image", False, 
                        "Could not check for local image")
            return False
        
        # Remove any existing GitHub registry tag
        try:
            subprocess.run(["docker", "rmi", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"], 
                         capture_output=True, timeout=10)
        except:
            pass  # Tag might not exist
        
        try:
            # Run push script (it will fail at push but should succeed at tagging)
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True, timeout=60)
            
            # Check if image was tagged (regardless of push failure)
            check_result = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", "--format", "{{.Repository}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if "ghcr.io/rrmalmstrom/sip_lims_workflow_manager" in check_result.stdout:
                self.log_test("Push script tags image", True, 
                            "Successfully tagged image for GitHub registry")
                return True
            else:
                self.log_test("Push script tags image", False, 
                            "Image was not properly tagged")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Push script tags image", False, 
                        "Push script timed out")
            return False
    
    def test_workflow_integration_with_run_command(self):
        """Test that the workflow integrates properly with run.command"""
        run_script = self.project_root / "run.command"
        
        if not run_script.exists():
            self.log_test("Workflow integration with run.command", False, 
                        "run.command not found")
            return False
        
        # Check that run.command references the correct image names
        content = run_script.read_text()
        
        has_production_image = "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest" in content
        has_development_image = "sip-lims-workflow-manager:latest" in content
        
        if has_production_image and has_development_image:
            self.log_test("Workflow integration with run.command", True, 
                        "run.command properly references both production and development images")
            return True
        else:
            missing = []
            if not has_production_image:
                missing.append("production image reference")
            if not has_development_image:
                missing.append("development image reference")
            
            self.log_test("Workflow integration with run.command", False, 
                        f"Missing: {', '.join(missing)}")
            return False
    
    def test_documentation_updated(self):
        """Test that documentation reflects new workflow"""
        doc_file = self.project_root / "DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md"
        
        if not doc_file.exists():
            self.log_test("Documentation updated", False, 
                        "DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md not found")
            return False
        
        content = doc_file.read_text()
        
        # Check for key elements of new workflow
        has_build_script = "build/build_image_from_lock_files.sh" in content
        has_push_script = "build/push_image_to_github.sh" in content
        has_generate_script = "build/generate_lock_files.sh" in content
        has_integration_info = "run.command" in content
        
        if all([has_build_script, has_push_script, has_generate_script, has_integration_info]):
            self.log_test("Documentation updated", True, 
                        "Documentation properly describes new workflow")
            return True
        else:
            missing = []
            if not has_build_script:
                missing.append("build script reference")
            if not has_push_script:
                missing.append("push script reference")
            if not has_generate_script:
                missing.append("generate script reference")
            if not has_integration_info:
                missing.append("run.command integration")
            
            self.log_test("Documentation updated", False, 
                        f"Missing: {', '.join(missing)}")
            return False
    
    def run_all_tests(self):
        """Run all tests and return overall result"""
        print("🧪 Running TDD tests for new deterministic build workflow")
        print("=" * 70)
        
        tests = [
            self.test_build_script_exists_and_executable,
            self.test_push_script_exists_and_executable,
            self.test_build_script_validates_prerequisites,
            self.test_push_script_validates_local_image,
            self.test_build_script_creates_local_image,
            self.test_push_script_tags_image,
            self.test_workflow_integration_with_run_command,
            self.test_documentation_updated
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
        
        print("=" * 70)
        print(f"📊 Test Results: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 All tests passed! New deterministic workflow is ready.")
            return True
        else:
            print("❌ Some tests failed. Fix issues before proceeding.")
            return False

if __name__ == "__main__":
    tester = TestNewDeterministicWorkflow()
    success = tester.run_all_tests()
    exit(0 if success else 1)