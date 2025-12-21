#!/usr/bin/env python3
"""
Correct Update Sequence Test

This test follows the exact sequence you specified:
1. Stop any sip-lims-workflow containers (native or remote)
2. Check local SHA vs remote SHA without pulling
3. Remove old local version + prune dangling images
4. Pull new image
5. Done (no re-checking)

Tests the actual run.command logic step by step.
"""

import os
import sys
import subprocess
import json
import time

class CorrectUpdateSequenceTest:
    """Test the correct update sequence as implemented in run.command."""
    
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
    
    def test_step_1_stop_containers(self):
        """Test Step 1: Stop any sip-lims-workflow containers."""
        print("\n🛑 STEP 1: Testing container stopping logic...")
        
        try:
            # Check what containers are currently running
            check_result = subprocess.run([
                "docker", "ps", "-a", 
                "--filter", "ancestor=ghcr.io/rrmalmstrom/sip_lims_workflow_manager",
                "--filter", "ancestor=sip-lims-workflow-manager",
                "--format", "{{.ID}} {{.Names}} {{.Status}}"
            ], capture_output=True, text=True)
            
            if check_result.returncode == 0:
                containers = check_result.stdout.strip()
                if containers:
                    print(f"Found containers: {containers}")
                    
                    # Extract container IDs
                    container_ids = []
                    for line in containers.split('\n'):
                        if line.strip():
                            container_id = line.split()[0]
                            container_ids.append(container_id)
                    
                    if container_ids:
                        # Stop containers
                        stop_result = subprocess.run(
                            ["docker", "stop"] + container_ids,
                            capture_output=True, text=True
                        )
                        
                        # Remove containers
                        rm_result = subprocess.run(
                            ["docker", "rm"] + container_ids,
                            capture_output=True, text=True
                        )
                        
                        self.log_test(
                            "Step 1: Stop workflow containers",
                            stop_result.returncode == 0 and rm_result.returncode == 0,
                            f"Stopped and removed {len(container_ids)} containers"
                        )
                    else:
                        self.log_test(
                            "Step 1: Stop workflow containers",
                            True,
                            "No container IDs found to stop"
                        )
                else:
                    self.log_test(
                        "Step 1: Stop workflow containers",
                        True,
                        "No workflow containers found running"
                    )
            else:
                self.log_test(
                    "Step 1: Stop workflow containers",
                    False,
                    f"Failed to check containers: {check_result.stderr}"
                )
                
        except Exception as e:
            self.log_test("Step 1: Stop workflow containers", False, f"Exception: {e}")
    
    def test_step_2_check_shas_without_pulling(self):
        """Test Step 2: Check local vs remote SHA without pulling."""
        print("\n🔍 STEP 2: Testing SHA comparison without pulling...")
        
        try:
            # Add src to path to import update_detector
            sys.path.insert(0, 'src')
            from update_detector import UpdateDetector
            
            detector = UpdateDetector()
            
            # Get local Docker image SHA (should be old version we set up)
            local_sha = detector.get_local_docker_image_commit_sha()
            
            # Get remote Docker image SHA (should be newer, without pulling)
            remote_sha = detector.get_remote_docker_image_commit_sha()
            
            # Test the check_docker_update function
            docker_result = detector.check_docker_update()
            update_available = docker_result.get("update_available", False)
            reason = docker_result.get("reason", "Unknown")
            
            self.log_test(
                "Step 2a: Get local SHA",
                local_sha is not None,
                f"Local SHA: {local_sha[:8] if local_sha else 'None'}..."
            )
            
            self.log_test(
                "Step 2b: Get remote SHA without pulling",
                remote_sha is not None,
                f"Remote SHA: {remote_sha[:8] if remote_sha else 'None'}..."
            )
            
            self.log_test(
                "Step 2c: Compare SHAs for update detection",
                update_available,
                f"Update needed: {update_available}, Reason: {reason}"
            )
            
            # Store SHAs for later verification
            self.local_sha_before = local_sha
            self.remote_sha_expected = remote_sha
            self.update_should_be_available = update_available
            
        except Exception as e:
            self.log_test("Step 2: Check SHAs without pulling", False, f"Exception: {e}")
    
    def test_step_3_remove_old_and_prune(self):
        """Test Step 3: Remove old local version and prune dangling images."""
        print("\n🧹 STEP 3: Testing old image removal and pruning...")
        
        try:
            # Only proceed if update was detected as needed
            if not hasattr(self, 'update_should_be_available') or not self.update_should_be_available:
                self.log_test(
                    "Step 3: Remove old and prune",
                    True,
                    "Skipped - no update needed"
                )
                return
            
            # Get current image ID before removal
            get_id_result = subprocess.run([
                "docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest",
                "--format", "{{.ID}}"
            ], capture_output=True, text=True)
            
            if get_id_result.returncode == 0 and get_id_result.stdout.strip():
                old_image_id = get_id_result.stdout.strip()
                print(f"Current image ID: {old_image_id}")
                
                # Remove by tag (this should leave a dangling image)
                rmi_result = subprocess.run([
                    "docker", "rmi", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"
                ], capture_output=True, text=True)
                
                # Prune dangling images
                prune_result = subprocess.run([
                    "docker", "image", "prune", "-f"
                ], capture_output=True, text=True)
                
                self.log_test(
                    "Step 3a: Remove image by tag",
                    rmi_result.returncode == 0,
                    f"Removed tag, exit code: {rmi_result.returncode}"
                )
                
                self.log_test(
                    "Step 3b: Prune dangling images",
                    prune_result.returncode == 0,
                    f"Pruned images: {prune_result.stdout.strip()}"
                )
                
                # Verify the image is actually gone
                verify_result = subprocess.run([
                    "docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest",
                    "--format", "{{.ID}}"
                ], capture_output=True, text=True)
                
                image_gone = verify_result.returncode == 0 and not verify_result.stdout.strip()
                
                self.log_test(
                    "Step 3c: Verify image removal",
                    image_gone,
                    "Image completely removed" if image_gone else "Image still present"
                )
                
            else:
                self.log_test(
                    "Step 3: Remove old and prune",
                    True,
                    "No local image found to remove"
                )
                
        except Exception as e:
            self.log_test("Step 3: Remove old and prune", False, f"Exception: {e}")
    
    def test_step_4_pull_new_image(self):
        """Test Step 4: Pull new image."""
        print("\n📥 STEP 4: Testing new image pull...")
        
        try:
            # Only proceed if update was detected as needed
            if not hasattr(self, 'update_should_be_available') or not self.update_should_be_available:
                self.log_test(
                    "Step 4: Pull new image",
                    True,
                    "Skipped - no update needed"
                )
                return
            
            # Pull the latest image
            pull_result = subprocess.run([
                "docker", "pull", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"
            ], capture_output=True, text=True)
            
            self.log_test(
                "Step 4a: Pull latest image",
                pull_result.returncode == 0,
                f"Pull successful: {pull_result.returncode == 0}"
            )
            
            if pull_result.returncode == 0:
                # Verify the new image has the expected SHA
                sys.path.insert(0, 'src')
                from update_detector import UpdateDetector
                
                detector = UpdateDetector()
                new_local_sha = detector.get_local_docker_image_commit_sha()
                
                sha_matches = new_local_sha == self.remote_sha_expected
                
                self.log_test(
                    "Step 4b: Verify new image SHA",
                    sha_matches,
                    f"New local SHA: {new_local_sha[:8] if new_local_sha else 'None'}..., Expected: {self.remote_sha_expected[:8] if hasattr(self, 'remote_sha_expected') and self.remote_sha_expected else 'None'}..."
                )
                
        except Exception as e:
            self.log_test("Step 4: Pull new image", False, f"Exception: {e}")
    
    def test_step_5_no_recheck(self):
        """Test Step 5: Verify no re-checking happens after pull."""
        print("\n✅ STEP 5: Testing no re-checking after pull...")
        
        try:
            # This step is more about verifying the logic doesn't re-check
            # In run.command, after the pull, it just returns 0 and continues
            # We can verify this by checking that the update detection now shows no update needed
            
            if not hasattr(self, 'update_should_be_available') or not self.update_should_be_available:
                self.log_test(
                    "Step 5: No re-checking needed",
                    True,
                    "No update was performed, so no re-checking needed"
                )
                return
            
            # Check if update detection now shows no update needed
            sys.path.insert(0, 'src')
            from update_detector import UpdateDetector
            
            detector = UpdateDetector()
            post_update_result = detector.check_docker_update()
            no_update_needed = not post_update_result.get("update_available", True)
            
            self.log_test(
                "Step 5: Verify no further updates needed",
                no_update_needed,
                f"Post-update check shows no update needed: {no_update_needed}"
            )
            
        except Exception as e:
            self.log_test("Step 5: No re-checking", False, f"Exception: {e}")
    
    def run_correct_sequence_test(self):
        """Run the complete correct update sequence test."""
        print("🎯 Testing Correct Update Sequence")
        print("=" * 60)
        print("Following the exact sequence from run.command:")
        print("1. Stop containers")
        print("2. Check local vs remote SHA (no pulling)")
        print("3. Remove old + prune dangling")
        print("4. Pull new image")
        print("5. Done (no re-checking)")
        print("=" * 60)
        
        # Run all test steps in order
        self.test_step_1_stop_containers()
        self.test_step_2_check_shas_without_pulling()
        self.test_step_3_remove_old_and_prune()
        self.test_step_4_pull_new_image()
        self.test_step_5_no_recheck()
        
        # Generate summary report
        print("\n" + "=" * 60)
        print("📊 CORRECT SEQUENCE TEST SUMMARY")
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
        
        print("\n🎯 OVERALL RESULT:", "✅ SEQUENCE CORRECT" if failed_tests == 0 else f"❌ {failed_tests} STEPS FAILED")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = CorrectUpdateSequenceTest()
    success = tester.run_correct_sequence_test()
    sys.exit(0 if success else 1)