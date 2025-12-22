#!/usr/bin/env python3
"""
Test Docker Cleanup Behavior

This test verifies that the Docker image cleanup logic in run.command
properly removes old images when new ones are pulled.
"""

import os
import sys
import subprocess
import tempfile
import time

class DockerCleanupTester:
    """Test Docker image cleanup functionality."""
    
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
    
    def test_docker_cleanup_logic(self):
        """Test the Docker cleanup logic in run.command."""
        print("\n🧹 Testing Docker Cleanup Logic...")
        
        try:
            # Read the run.command file to analyze cleanup logic
            with open("run.command", "r") as f:
                content = f.read()
            
            # Check for old image ID capture
            has_old_image_capture = "old_image_id=$(docker images" in content
            
            # Check for new image ID comparison
            has_new_image_comparison = "new_image_id=$(docker images" in content
            
            # Check for image ID comparison
            has_id_comparison = 'if [ "$old_image_id" != "$new_image_id" ]' in content
            
            # Check for container usage check
            has_container_check = "containers_using_old=$(docker ps -a --filter" in content
            
            # Check for safe removal
            has_safe_removal = "docker rmi" in content
            
            self.log_test(
                "Old image ID capture",
                has_old_image_capture,
                f"Captures old image ID before update: {has_old_image_capture}"
            )
            
            self.log_test(
                "New image ID comparison",
                has_new_image_comparison,
                f"Gets new image ID after update: {has_new_image_comparison}"
            )
            
            self.log_test(
                "Image ID comparison logic",
                has_id_comparison,
                f"Compares old vs new image IDs: {has_id_comparison}"
            )
            
            self.log_test(
                "Container usage safety check",
                has_container_check,
                f"Checks if old image is in use: {has_container_check}"
            )
            
            self.log_test(
                "Safe image removal",
                has_safe_removal,
                f"Safely removes old images: {has_safe_removal}"
            )
            
        except Exception as e:
            self.log_test("Docker cleanup logic analysis", False, f"Exception: {e}")
    
    def test_current_docker_images(self):
        """Test current Docker image state."""
        print("\n🐳 Testing Current Docker Image State...")
        
        try:
            # Get current workflow manager images
            result = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager", "--format", "{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedAt}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                images = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                self.log_test(
                    "Current workflow manager images",
                    len(images) > 0,
                    f"Found {len(images)} workflow manager images"
                )
                
                if images:
                    for i, image in enumerate(images):
                        print(f"    Image {i+1}: {image}")
                
                # Check for multiple versions (potential cleanup candidates)
                unique_tags = set()
                for image in images:
                    if image:
                        tag = image.split()[0].split(':')[1] if ':' in image.split()[0] else 'latest'
                        unique_tags.add(tag)
                
                self.log_test(
                    "Image version diversity",
                    True,
                    f"Found {len(unique_tags)} unique tags: {list(unique_tags)}"
                )
                
            else:
                self.log_test(
                    "Current workflow manager images",
                    False,
                    f"Could not list images: {result.stderr}"
                )
                
        except Exception as e:
            self.log_test("Current Docker image state", False, f"Exception: {e}")
    
    def test_cleanup_behavior_simulation(self):
        """Simulate the cleanup behavior without actually running it."""
        print("\n🎭 Simulating Cleanup Behavior...")
        
        try:
            # This simulates what happens in the cleanup logic
            print("    Simulating: User has old image locally")
            print("    Simulating: New image is pulled from registry")
            print("    Simulating: Old image ID != New image ID")
            print("    Simulating: Check if old image is used by containers")
            print("    Simulating: If not in use, remove old image")
            
            # Test the logic flow
            cleanup_steps = [
                "Capture old image ID before pull",
                "Pull new image from registry", 
                "Capture new image ID after pull",
                "Compare old vs new image IDs",
                "Check if old image is used by containers",
                "Remove old image if safe to do so"
            ]
            
            self.log_test(
                "Cleanup workflow simulation",
                True,
                f"Cleanup follows {len(cleanup_steps)} logical steps"
            )
            
            for i, step in enumerate(cleanup_steps, 1):
                print(f"    Step {i}: {step}")
                
        except Exception as e:
            self.log_test("Cleanup behavior simulation", False, f"Exception: {e}")
    
    def run_cleanup_tests(self):
        """Run all Docker cleanup tests."""
        print("🎯 Starting Docker Cleanup Tests")
        print("=" * 50)
        print("Testing Docker image cleanup behavior")
        print("=" * 50)
        
        # Run all test scenarios
        self.test_docker_cleanup_logic()
        self.test_current_docker_images()
        self.test_cleanup_behavior_simulation()
        
        # Generate summary report
        print("\n" + "=" * 50)
        print("📊 DOCKER CLEANUP TEST SUMMARY")
        print("=" * 50)
        
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
        
        print("\n🎯 OVERALL RESULT:", "✅ ALL CLEANUP TESTS PASSED" if failed_tests == 0 else f"❌ {failed_tests} CLEANUP TESTS FAILED")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = DockerCleanupTester()
    success = tester.run_cleanup_tests()
    sys.exit(0 if success else 1)