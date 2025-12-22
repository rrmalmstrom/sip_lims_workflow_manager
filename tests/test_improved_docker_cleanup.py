#!/usr/bin/env python3
"""
Test Improved Docker Cleanup Logic

This test verifies the improved Docker cleanup logic:
1. Stop workflow containers first
2. Only clean up when update is detected
3. Clean up before pulling new image
"""

import os
import sys
import subprocess
import tempfile
import time

class ImprovedDockerCleanupTester:
    """Test the improved Docker cleanup logic."""
    
    def __init__(self):
        self.test_results = []
        
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
    
    def test_container_stopping_logic(self):
        """Test the container stopping logic in run.command."""
        print("\n🛑 Testing Container Stopping Logic...")
        
        try:
            # Read the run.command file to analyze container stopping logic
            with open("run.command", "r") as f:
                content = f.read()
            
            # Check for container stopping function
            has_stop_function = "stop_workflow_containers()" in content
            
            # Check for specific workflow manager container detection
            has_workflow_filter = '--filter "ancestor=ghcr.io/rrmalmstrom/sip_lims_workflow_manager"' in content
            has_local_filter = '--filter "ancestor=sip-lims-workflow-manager"' in content
            
            # Check for container stop and remove commands
            has_stop_command = "docker stop" in content
            has_remove_command = "docker rm" in content
            
            # Check that it's called early in the script
            has_early_call = "stop_workflow_containers" in content and content.find("stop_workflow_containers") < content.find("handle_mode_and_updates")
            
            self.log_test(
                "Container stopping function exists",
                has_stop_function,
                f"Function defined: {has_stop_function}"
            )
            
            self.log_test(
                "Workflow container detection",
                has_workflow_filter and has_local_filter,
                f"Detects both GHCR and local images: {has_workflow_filter and has_local_filter}"
            )
            
            self.log_test(
                "Container stop and remove commands",
                has_stop_command and has_remove_command,
                f"Has stop: {has_stop_command}, Has remove: {has_remove_command}"
            )
            
            self.log_test(
                "Early execution order",
                has_early_call,
                f"Called before updates: {has_early_call}"
            )
            
        except Exception as e:
            self.log_test("Container stopping logic analysis", False, f"Exception: {e}")
    
    def test_improved_cleanup_logic(self):
        """Test the improved cleanup logic in check_docker_updates."""
        print("\n🧹 Testing Improved Cleanup Logic...")
        
        try:
            # Read the run.command file to analyze improved cleanup logic
            with open("run.command", "r") as f:
                content = f.read()
            
            # Check that cleanup only happens when update is detected
            cleanup_in_update_block = 'if [ "$update_available" = "true" ]; then' in content and "Removing old Docker image before update" in content
            
            # Check that cleanup happens before pull
            cleanup_before_pull = content.find("Removing old Docker image before update") < content.find("docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest")
            
            # Check that old safety logic is removed
            no_container_check = "containers_using_old" not in content or content.count("containers_using_old") == 0
            
            # Check for simplified cleanup
            has_simple_rmi = "docker rmi ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest" in content
            
            self.log_test(
                "Cleanup only on update detection",
                cleanup_in_update_block,
                f"Cleanup only when update available: {cleanup_in_update_block}"
            )
            
            self.log_test(
                "Cleanup before pull",
                cleanup_before_pull,
                f"Cleanup happens before pull: {cleanup_before_pull}"
            )
            
            self.log_test(
                "Simplified cleanup logic",
                has_simple_rmi,
                f"Uses direct image removal: {has_simple_rmi}"
            )
            
            self.log_test(
                "Removed complex safety checks",
                no_container_check,
                f"No container usage checks (not needed): {no_container_check}"
            )
            
        except Exception as e:
            self.log_test("Improved cleanup logic analysis", False, f"Exception: {e}")
    
    def test_workflow_integration(self):
        """Test that the improved logic is properly integrated into the workflow."""
        print("\n🔄 Testing Workflow Integration...")
        
        try:
            # Read the run.command file
            with open("run.command", "r") as f:
                content = f.read()
            
            # Check execution order
            lines = content.split('\n')
            
            # Find key function calls
            detect_user_ids_line = -1
            stop_containers_line = -1
            handle_updates_line = -1
            
            for i, line in enumerate(lines):
                if "detect_user_ids" in line and not line.strip().startswith('#'):
                    detect_user_ids_line = i
                elif "stop_workflow_containers" in line and not line.strip().startswith('#'):
                    stop_containers_line = i
                elif "handle_mode_and_updates" in line and not line.strip().startswith('#'):
                    handle_updates_line = i
            
            # Check proper execution order
            proper_order = (detect_user_ids_line < stop_containers_line < handle_updates_line)
            
            self.log_test(
                "Proper execution order",
                proper_order,
                f"Order: detect_user_ids({detect_user_ids_line}) -> stop_containers({stop_containers_line}) -> handle_updates({handle_updates_line})"
            )
            
            # Check that docker-compose up happens after all setup
            docker_compose_line = -1
            for i, line in enumerate(lines):
                if "docker-compose up" in line:
                    docker_compose_line = i
                    break
            
            proper_compose_order = handle_updates_line < docker_compose_line
            
            self.log_test(
                "Docker compose after setup",
                proper_compose_order,
                f"docker-compose up({docker_compose_line}) after handle_updates({handle_updates_line})"
            )
            
        except Exception as e:
            self.log_test("Workflow integration analysis", False, f"Exception: {e}")
    
    def test_syntax_validation(self):
        """Test that the improved run.command has valid syntax."""
        print("\n📝 Testing Syntax Validation...")
        
        try:
            # Test bash syntax
            result = subprocess.run(
                ["bash", "-n", "run.command"],
                capture_output=True,
                text=True
            )
            
            self.log_test(
                "Bash syntax validation",
                result.returncode == 0,
                f"Syntax check exit code: {result.returncode}" + (f", Errors: {result.stderr}" if result.stderr else "")
            )
            
        except Exception as e:
            self.log_test("Syntax validation", False, f"Exception: {e}")
    
    def run_improved_cleanup_tests(self):
        """Run all improved Docker cleanup tests."""
        print("🎯 Starting Improved Docker Cleanup Tests")
        print("=" * 70)
        print("Testing the improved Docker cleanup logic:")
        print("1. Stop containers first")
        print("2. Clean only when update detected")
        print("3. Clean before pulling new image")
        print("=" * 70)
        
        # Run all test scenarios
        self.test_container_stopping_logic()
        self.test_improved_cleanup_logic()
        self.test_workflow_integration()
        self.test_syntax_validation()
        
        # Generate summary report
        print("\n" + "=" * 70)
        print("📊 IMPROVED CLEANUP TEST SUMMARY")
        print("=" * 70)
        
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
        
        print("\n🎯 OVERALL RESULT:", "✅ IMPROVED CLEANUP LOGIC VERIFIED" if failed_tests == 0 else f"❌ {failed_tests} TESTS FAILED")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = ImprovedDockerCleanupTester()
    success = tester.run_improved_cleanup_tests()
    sys.exit(0 if success else 1)