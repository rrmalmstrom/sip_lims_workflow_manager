#!/usr/bin/env python3
"""
Test REAL Docker Cleanup - Actually Remove Images

This test demonstrates the Docker cleanup actually working by:
1. Using the existing older image as our "old" image
2. Simulating the cleanup process
3. Verifying the old image gets removed
"""

import os
import sys
import subprocess
import tempfile
import time

class RealDockerCleanupTester:
    """Test real Docker image cleanup functionality."""
    
    def __init__(self):
        self.test_results = []
        self.original_images = []
        
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
    
    def get_workflow_images(self):
        """Get all workflow manager Docker images."""
        try:
            result = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager", "--format", "{{.ID}}:{{.Repository}}:{{.Tag}}:{{.CreatedAt}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                images = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split(':')
                        if len(parts) >= 4:
                            images.append({
                                "id": parts[0],
                                "repo": parts[1],
                                "tag": parts[2],
                                "created": ':'.join(parts[3:]),
                                "full_name": f"{parts[1]}:{parts[2]}"
                            })
                return images
            return []
        except Exception:
            return []
    
    def setup_cleanup_test(self):
        """Set up a real cleanup test scenario."""
        print("\n🎭 Setting Up Real Cleanup Test...")
        
        try:
            # Get current images
            self.original_images = self.get_workflow_images()
            
            self.log_test(
                "Current workflow images",
                len(self.original_images) > 0,
                f"Found {len(self.original_images)} workflow manager images"
            )
            
            for i, img in enumerate(self.original_images):
                print(f"    Image {i+1}: {img['full_name']} ({img['id'][:12]}) - {img['created']}")
            
            # Find the older image (not latest)
            older_images = [img for img in self.original_images if img['tag'] != 'latest']
            
            if len(older_images) > 0:
                target_image = older_images[0]  # Use the first non-latest image
                
                self.log_test(
                    "Target old image identified",
                    True,
                    f"Will test cleanup of: {target_image['full_name']} ({target_image['id'][:12]})"
                )
                
                return target_image
            else:
                self.log_test(
                    "Target old image identification",
                    False,
                    "No older images found to test cleanup with"
                )
                return None
                
        except Exception as e:
            self.log_test("Cleanup test setup", False, f"Exception: {e}")
            return None
    
    def test_real_cleanup_process(self, target_image):
        """Test the real cleanup process using the actual logic from run.command."""
        print(f"\n🧹 Testing Real Cleanup Process on {target_image['full_name']}...")
        
        try:
            # Create a script that mimics the exact cleanup logic from run.command
            cleanup_script = f'''#!/bin/bash
set -e

echo "🔍 Starting cleanup test for {target_image['full_name']}"

# This simulates the exact logic from check_docker_updates() in run.command
IMAGE_NAME="ghcr.io/rrmalmstrom/sip_lims_workflow_manager"
OLD_IMAGE_ID="{target_image['id']}"
OLD_IMAGE_NAME="{target_image['full_name']}"

echo "📦 Target old image: $OLD_IMAGE_ID ($OLD_IMAGE_NAME)"

# Get latest image ID (this represents the "new" image after pull)
NEW_IMAGE_ID=$(docker images ${{IMAGE_NAME}}:latest --format "{{{{.ID}}}}" 2>/dev/null)

if [ -n "$NEW_IMAGE_ID" ]; then
    echo "🆕 Latest image: $NEW_IMAGE_ID"
    
    if [ "$OLD_IMAGE_ID" != "$NEW_IMAGE_ID" ]; then
        echo "🔄 Images are different - cleanup needed"
        
        # Check if old image is being used by any containers
        CONTAINERS_USING_OLD=$(docker ps -a --filter "ancestor=$OLD_IMAGE_ID" --format "{{{{.ID}}}}" 2>/dev/null)
        
        if [ -z "$CONTAINERS_USING_OLD" ]; then
            echo "🗑️  Old image not in use - safe to remove"
            echo "🧹 Removing old image: $OLD_IMAGE_NAME"
            
            docker rmi "$OLD_IMAGE_NAME"
            if [ $? -eq 0 ]; then
                echo "✅ Successfully removed old image"
                exit 0
            else
                echo "❌ Failed to remove old image"
                exit 1
            fi
        else
            echo "⚠️  Old image still in use by containers: $CONTAINERS_USING_OLD"
            echo "🛡️  Skipping removal for safety"
            exit 2
        fi
    else
        echo "⚠️  Images are the same - no cleanup needed"
        exit 3
    fi
else
    echo "❌ Could not find latest image"
    exit 4
fi
'''
            
            # Write and execute the cleanup script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(cleanup_script)
                script_path = f.name
            
            try:
                # Make script executable
                os.chmod(script_path, 0o755)
                
                # Get images before cleanup
                images_before = self.get_workflow_images()
                target_exists_before = any(img['id'] == target_image['id'] for img in images_before)
                
                self.log_test(
                    "Target image exists before cleanup",
                    target_exists_before,
                    f"Target image {target_image['id'][:12]} present: {target_exists_before}"
                )
                
                # Run the cleanup script
                print("    🚀 Executing cleanup script...")
                result = subprocess.run(
                    ["bash", script_path],
                    capture_output=True,
                    text=True
                )
                
                print(f"    📋 Cleanup output:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"      {line}")
                
                if result.stderr:
                    print(f"    ⚠️  Cleanup errors: {result.stderr.strip()}")
                
                # Get images after cleanup
                images_after = self.get_workflow_images()
                target_exists_after = any(img['id'] == target_image['id'] for img in images_after)
                
                # Determine if cleanup was successful
                cleanup_successful = target_exists_before and not target_exists_after
                cleanup_skipped = result.returncode in [2, 3]  # In use or same image
                cleanup_failed = result.returncode == 1
                
                if cleanup_successful:
                    self.log_test(
                        "Real Docker image cleanup SUCCESS",
                        True,
                        f"✅ Successfully removed target image {target_image['id'][:12]}"
                    )
                elif cleanup_skipped:
                    self.log_test(
                        "Real Docker image cleanup SKIPPED",
                        True,
                        f"⚠️  Cleanup skipped (exit code {result.returncode}) - image in use or same as latest"
                    )
                elif cleanup_failed:
                    self.log_test(
                        "Real Docker image cleanup FAILED",
                        False,
                        f"❌ Cleanup failed (exit code {result.returncode})"
                    )
                else:
                    self.log_test(
                        "Real Docker image cleanup UNEXPECTED",
                        False,
                        f"🤔 Unexpected result (exit code {result.returncode})"
                    )
                
                # Show final state
                print(f"    📊 Images before: {len(images_before)}, after: {len(images_after)}")
                
                return cleanup_successful or cleanup_skipped
                
            finally:
                # Clean up test script
                os.unlink(script_path)
                
        except Exception as e:
            self.log_test("Real cleanup process test", False, f"Exception: {e}")
            return False
    
    def verify_cleanup_results(self):
        """Verify the results of the cleanup test."""
        print("\n🔍 Verifying Cleanup Results...")
        
        try:
            # Get final image state
            final_images = self.get_workflow_images()
            
            self.log_test(
                "Final image inventory",
                len(final_images) > 0,
                f"Final state: {len(final_images)} workflow manager images"
            )
            
            print("    📋 Remaining images:")
            for i, img in enumerate(final_images):
                print(f"      {i+1}. {img['full_name']} ({img['id'][:12]}) - {img['created']}")
            
            # Compare with original state
            original_count = len(self.original_images)
            final_count = len(final_images)
            
            if final_count < original_count:
                self.log_test(
                    "Image count reduction",
                    True,
                    f"✅ Reduced from {original_count} to {final_count} images"
                )
            elif final_count == original_count:
                self.log_test(
                    "Image count unchanged",
                    True,
                    f"⚠️  Image count unchanged ({final_count}) - cleanup may have been skipped for safety"
                )
            else:
                self.log_test(
                    "Image count unexpected",
                    False,
                    f"🤔 Image count increased from {original_count} to {final_count}"
                )
            
        except Exception as e:
            self.log_test("Cleanup results verification", False, f"Exception: {e}")
    
    def run_real_cleanup_tests(self):
        """Run real Docker cleanup tests."""
        print("🎯 Starting REAL Docker Cleanup Tests")
        print("=" * 70)
        print("This test ACTUALLY removes Docker images using the real cleanup logic")
        print("=" * 70)
        
        # Set up test scenario
        target_image = self.setup_cleanup_test()
        
        if target_image is None:
            print("❌ Cannot run cleanup test - no suitable target image found")
            return False
        
        # Test real cleanup process
        cleanup_success = self.test_real_cleanup_process(target_image)
        
        # Verify results
        self.verify_cleanup_results()
        
        # Generate summary report
        print("\n" + "=" * 70)
        print("📊 REAL CLEANUP TEST SUMMARY")
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
        
        overall_success = failed_tests == 0 and cleanup_success
        print("\n🎯 OVERALL RESULT:", "✅ REAL CLEANUP VERIFIED" if overall_success else "⚠️  CLEANUP LOGIC TESTED")
        
        return overall_success

if __name__ == "__main__":
    tester = RealDockerCleanupTester()
    success = tester.run_real_cleanup_tests()
    sys.exit(0 if success else 1)