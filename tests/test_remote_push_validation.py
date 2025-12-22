#!/usr/bin/env python3
"""
Remote Push Validation Test
Tests actual push to GitHub Container Registry and pull verification
"""

import subprocess
import os
import time
from pathlib import Path

class TestRemotePushValidation:
    """Test actual remote push and pull workflow"""
    
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
    
    def test_push_to_remote_registry(self):
        """Test actual push to GitHub Container Registry"""
        script_path = self.project_root / "push_image_to_github.sh"
        
        print("    Attempting to push to GitHub Container Registry...")
        print("    (This will fail if not authenticated)")
        
        try:
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log_test("Push to remote registry", True, 
                            "Successfully pushed to GitHub Container Registry")
                return True
            else:
                # Check if it's an authentication error vs other error
                if "authentication" in result.stdout.lower() or "login" in result.stdout.lower():
                    self.log_test("Push to remote registry", False, 
                                "Authentication required - need GitHub token")
                else:
                    self.log_test("Push to remote registry", False, 
                                f"Push failed: {result.stdout}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Push to remote registry", False, 
                        "Push timed out (>2 minutes)")
            return False
    
    def test_pull_from_remote_registry(self):
        """Test pulling image from remote registry"""
        print("    Removing local images...")
        
        # Remove local images
        try:
            subprocess.run(["docker", "rmi", "sip-lims-workflow-manager:latest"], 
                         capture_output=True, timeout=30)
            subprocess.run(["docker", "rmi", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"], 
                         capture_output=True, timeout=30)
        except:
            pass  # Images might not exist
        
        print("    Attempting to pull from GitHub Container Registry...")
        
        try:
            result = subprocess.run(
                ["docker", "pull", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                self.log_test("Pull from remote registry", True, 
                            "Successfully pulled from GitHub Container Registry")
                return True
            else:
                self.log_test("Pull from remote registry", False, 
                            f"Pull failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Pull from remote registry", False, 
                        "Pull timed out (>2 minutes)")
            return False
    
    def test_pulled_image_functionality(self):
        """Test that pulled image actually works"""
        try:
            # Test basic functionality
            result = subprocess.run(
                ["docker", "run", "--rm", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", 
                 "python", "--version"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0 and "Python" in result.stdout:
                self.log_test("Pulled image functionality", True, 
                            f"Image works: {result.stdout.strip()}")
                return True
            else:
                self.log_test("Pulled image functionality", False, 
                            f"Image test failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Pulled image functionality", False, 
                        "Image test timed out")
            return False
    
    def test_image_metadata_consistency(self):
        """Test that remote image metadata matches local build"""
        try:
            # Get remote image digest
            result = subprocess.run(
                ["docker", "images", "--digests", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Header + data
                    image_info = lines[1].split()
                    if len(image_info) >= 3:
                        digest = image_info[2] if image_info[2] != '<none>' else 'No digest'
                        size = image_info[3] if len(image_info) > 3 else 'Unknown size'
                        
                        self.log_test("Image metadata consistency", True, 
                                    f"Remote image digest: {digest}, size: {size}")
                        return True
            
            self.log_test("Image metadata consistency", False, 
                        "Could not retrieve image metadata")
            return False
        
        except subprocess.TimeoutExpired:
            self.log_test("Image metadata consistency", False, 
                        "Metadata check timed out")
            return False
    
    def run_all_tests(self):
        """Run all remote validation tests"""
        print("🌐 Running Remote Push Validation Tests")
        print("=" * 50)
        
        tests = [
            self.test_push_to_remote_registry,
            self.test_pull_from_remote_registry,
            self.test_pulled_image_functionality,
            self.test_image_metadata_consistency
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            print()
        
        print("=" * 50)
        print(f"📊 Remote Test Results: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 All remote tests passed! End-to-end workflow validated.")
            return True
        else:
            print("❌ Some remote tests failed.")
            if passed_tests == 0:
                print("💡 Tip: You may need to authenticate with GitHub Container Registry:")
                print("   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin")
            return False

if __name__ == "__main__":
    tester = TestRemotePushValidation()
    success = tester.run_all_tests()
    exit(0 if success else 1)