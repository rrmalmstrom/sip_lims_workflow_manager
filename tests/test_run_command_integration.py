#!/usr/bin/env python3
"""
Test Run Command Integration

This test verifies that the updated run.command properly integrates
the update detection system and handles different modes correctly.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

class RunCommandIntegrationTester:
    """Test the integrated run.command functionality."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []
        self.original_dir = os.getcwd()
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
    
    def test_update_detector_availability(self):
        """Test that the update detector is available and functional."""
        print("\n🔍 Testing Update Detector Availability...")
        
        try:
            # Test that update detector can be imported and run
            result = subprocess.run(
                [sys.executable, "src/update_detector.py", "--summary"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.log_test(
                "Update detector CLI availability",
                result.returncode == 0,
                f"Exit code: {result.returncode}, Output length: {len(result.stdout)} chars"
            )
            
            if result.returncode == 0:
                # Check if output contains expected JSON structure
                import json
                try:
                    data = json.loads(result.stdout)
                    has_required_fields = all(key in data for key in ["timestamp", "docker", "scripts"])
                    
                    self.log_test(
                        "Update detector JSON output structure",
                        has_required_fields,
                        f"Contains required fields: {has_required_fields}"
                    )
                except json.JSONDecodeError:
                    self.log_test(
                        "Update detector JSON output structure",
                        False,
                        "Output is not valid JSON"
                    )
            
        except Exception as e:
            self.log_test("Update detector availability", False, f"Exception: {e}")
    
    def test_run_command_syntax(self):
        """Test that run.command has valid bash syntax."""
        print("\n📝 Testing Run Command Syntax...")
        
        try:
            # Test bash syntax
            result = subprocess.run(
                ["bash", "-n", "run.command"],
                capture_output=True,
                text=True
            )
            
            self.log_test(
                "Run command bash syntax",
                result.returncode == 0,
                f"Syntax check exit code: {result.returncode}" + (f", Errors: {result.stderr}" if result.stderr else "")
            )
            
        except Exception as e:
            self.log_test("Run command syntax", False, f"Exception: {e}")
    
    def test_docker_compose_syntax(self):
        """Test that docker-compose.yml has valid syntax."""
        print("\n🐳 Testing Docker Compose Syntax...")
        
        try:
            # Test docker-compose syntax
            result = subprocess.run(
                ["docker-compose", "config"],
                capture_output=True,
                text=True
            )
            
            self.log_test(
                "Docker compose syntax",
                result.returncode == 0,
                f"Config validation exit code: {result.returncode}" + (f", Errors: {result.stderr}" if result.stderr else "")
            )
            
        except Exception as e:
            self.log_test("Docker compose syntax", False, f"Exception: {e}")
    
    def test_function_definitions(self):
        """Test that all required functions are defined in run.command."""
        print("\n🔧 Testing Function Definitions...")
        
        try:
            with open("run.command", "r") as f:
                content = f.read()
            
            required_functions = [
                "check_docker_updates",
                "check_and_download_scripts", 
                "production_auto_update",
                "choose_developer_mode",
                "select_development_script_path",
                "handle_mode_and_updates"
            ]
            
            missing_functions = []
            for func in required_functions:
                if f"{func}()" not in content:
                    missing_functions.append(func)
            
            self.log_test(
                "Required function definitions",
                len(missing_functions) == 0,
                f"Missing functions: {missing_functions}" if missing_functions else "All functions present"
            )
            
        except Exception as e:
            self.log_test("Function definitions", False, f"Exception: {e}")
    
    def test_environment_variable_handling(self):
        """Test that environment variables are properly set."""
        print("\n🌍 Testing Environment Variable Handling...")
        
        try:
            # Test that the script sets expected environment variables
            with open("run.command", "r") as f:
                content = f.read()
            
            expected_exports = [
                "export SCRIPTS_PATH",
                "export APP_ENV", 
                "export DOCKER_IMAGE"
            ]
            
            missing_exports = []
            for export in expected_exports:
                if export not in content:
                    missing_exports.append(export)
            
            self.log_test(
                "Environment variable exports",
                len(missing_exports) == 0,
                f"Missing exports: {missing_exports}" if missing_exports else "All exports present"
            )
            
        except Exception as e:
            self.log_test("Environment variable handling", False, f"Exception: {e}")
    
    def test_docker_image_configuration(self):
        """Test that Docker image configuration is properly handled."""
        print("\n🐳 Testing Docker Image Configuration...")
        
        try:
            with open("docker-compose.yml", "r") as f:
                content = f.read()
            
            # Check for DOCKER_IMAGE environment variable usage
            has_docker_image_var = "${DOCKER_IMAGE:-" in content
            has_ghcr_default = "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest" in content
            
            self.log_test(
                "Docker image environment variable",
                has_docker_image_var,
                f"Uses DOCKER_IMAGE variable: {has_docker_image_var}"
            )
            
            self.log_test(
                "GHCR default image",
                has_ghcr_default,
                f"Has GHCR default: {has_ghcr_default}"
            )
            
        except Exception as e:
            self.log_test("Docker image configuration", False, f"Exception: {e}")
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up: {temp_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up {temp_dir}: {e}")
    
    def run_integration_tests(self):
        """Run all integration tests."""
        print("🎯 Starting Run Command Integration Tests")
        print("=" * 60)
        print("Testing the integrated update detection system")
        print("=" * 60)
        
        # Run all test scenarios
        self.test_update_detector_availability()
        self.test_run_command_syntax()
        self.test_docker_compose_syntax()
        self.test_function_definitions()
        self.test_environment_variable_handling()
        self.test_docker_image_configuration()
        
        # Generate summary report
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 OVERALL RESULT:", "✅ ALL INTEGRATION TESTS PASSED" if failed_tests == 0 else f"❌ {failed_tests} INTEGRATION TESTS FAILED")
        
        # Cleanup
        self.cleanup()
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = RunCommandIntegrationTester()
    success = tester.run_integration_tests()
    sys.exit(0 if success else 1)