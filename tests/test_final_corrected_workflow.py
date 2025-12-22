#!/usr/bin/env python3
"""
Final Corrected Workflow Test

This test validates the complete corrected workflow in the proper order:
1. Set up realistic scenario (old local image vs newer remote)
2. Test update detection BEFORE any updates
3. Test complete update process with proper cleanup
4. Verify final state

This addresses the real issues identified:
- Wrong test order (was testing detection after update)
- Broken image cleanup (dangling images)
- Proper SHA comparison logic
"""

import os
import sys
import subprocess
import tempfile
import time

class FinalWorkflowTester:
    """Test the final corrected workflow with proper order and cleanup."""
    
    def __init__(self):
        self.test_results = []
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
    
    def setup_realistic_scenario(self):
        """Set up realistic scenario: old local image vs newer remote."""
        print("\n🎭 Setting Up Realistic Scenario")
        
        try:
            # Clean up any existing state
            subprocess.run(["docker", "image", "prune", "-f"], capture_output=True)
            
            # Pull the older image and tag it as latest (simulate user having old version)
            print("    📥 Pulling older image to simulate user having old version...")
            pull_result = subprocess.run(
                ["docker", "pull", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation-5d38a20"],
                capture_output=True,
                text=True
            )
            
            if pull_result.returncode != 0:
                self.log_test("Pull older image", False, f"Failed to pull: {pull_result.stderr}")
                return False
            
            # Remove current latest if it exists
            subprocess.run(
                ["docker", "rmi", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True
            )
            
            # Tag older image as latest
            tag_result = subprocess.run(
                ["docker", "tag", 
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation-5d38a20",
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True,
                text=True
            )
            
            if tag_result.returncode != 0:
                self.log_test("Tag older as latest", False, f"Failed to tag: {tag_result.stderr}")
                return False
            
            # Verify setup
            inspect_result = subprocess.run(
                ["docker", "inspect", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", 
                 "--format", "{{index .Config.Labels \"com.sip-lims.commit-sha\"}}"],
                capture_output=True,
                text=True
            )
            
            local_sha = inspect_result.stdout.strip()
            
            self.log_test(
                "Realistic scenario setup",
                local_sha.startswith("5d38a204"),
                f"Local image SHA: {local_sha[:8]}... (should be old: 5d38a204...)"
            )
            
            return local_sha.startswith("5d38a204")
            
        except Exception as e:
            self.log_test("Realistic scenario setup", False, f"Exception: {e}")
            return False
    
    def test_update_detection_before_update(self):
        """Test update detection BEFORE any updates (correct order)."""
        print("\n🔍 Testing Update Detection BEFORE Update (Correct Order)")
        
        try:
            # Import corrected update detector
            sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
            from update_detector import UpdateDetector
            
            detector = UpdateDetector()
            
            # Test update detection
            result = detector.check_docker_image_update()
            
            # Verify detection results
            has_local_image = result.get("has_local_remote_image", False)
            update_available = result.get("update_available", False)
            local_sha = result.get("local_image_sha", "")
            remote_sha = result.get("remote_image_sha", "")
            
            self.log_test(
                "Local remote image detected",
                has_local_image,
                f"Has local remote image: {has_local_image}"
            )
            
            self.log_test(
                "Update detection works",
                update_available,
                f"Update available: {update_available}"
            )
            
            self.log_test(
                "SHA comparison correct",
                local_sha != remote_sha and len(local_sha) > 0 and len(remote_sha) > 0,
                f"Local: {local_sha[:8]}..., Remote: {remote_sha[:8]}..."
            )
            
            return update_available and has_local_image
            
        except Exception as e:
            self.log_test("Update detection before update", False, f"Exception: {e}")
            return False
    
    def test_corrected_update_process(self):
        """Test the corrected update process with proper cleanup."""
        print("\n🔄 Testing Corrected Update Process")
        
        try:
            # Get current state
            old_images_before = subprocess.run(
                ["docker", "images", "-q"],
                capture_output=True,
                text=True
            ).stdout.strip().split('\n')
            
            # Test the corrected update process using actual run.command logic
            update_script = '''#!/bin/bash
set -e

echo "🔍 Testing corrected update process..."

# Get current image ID
old_image_id=$(docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --format "{{.ID}}" 2>/dev/null)
echo "📦 Current old image: $old_image_id"

if [ -n "$old_image_id" ]; then
    echo "🧹 Removing old Docker image before update..."
    # Remove by tag first, then clean up any dangling images (CORRECTED LOGIC)
    docker rmi ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest >/dev/null 2>&1
    # Clean up dangling images to prevent disk space waste
    docker image prune -f >/dev/null 2>&1
    echo "✅ Old Docker image and dangling images cleaned up"
fi

# Pull new image
echo "📥 Pulling latest Docker image..."
docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ New image pulled successfully"
    
    new_image_id=$(docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --format "{{.ID}}" 2>/dev/null)
    echo "📦 New image: $new_image_id"
    exit 0
else
    echo "❌ Failed to pull new image"
    exit 1
fi
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(update_script)
                script_path = f.name
            
            try:
                os.chmod(script_path, 0o755)
                
                result = subprocess.run(
                    ["bash", script_path],
                    capture_output=True,
                    text=True
                )
                
                print(f"    📋 Update process output:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"      {line}")
                
                update_successful = result.returncode == 0
                
                self.log_test(
                    "Corrected update process",
                    update_successful,
                    f"Update successful: {update_successful}"
                )
                
                # Verify no dangling images left
                dangling_images = subprocess.run(
                    ["docker", "images", "--filter", "dangling=true", "-q"],
                    capture_output=True,
                    text=True
                ).stdout.strip()
                
                no_dangling = len(dangling_images) == 0
                
                self.log_test(
                    "No dangling images left",
                    no_dangling,
                    f"Dangling images: {'None' if no_dangling else 'Found some'}"
                )
                
                return update_successful and no_dangling
                
            finally:
                os.unlink(script_path)
                
        except Exception as e:
            self.log_test("Corrected update process", False, f"Exception: {e}")
            return False
    
    def test_final_state_verification(self):
        """Test final state verification."""
        print("\n✅ Testing Final State Verification")
        
        try:
            # Check final image SHA
            final_sha_result = subprocess.run(
                ["docker", "inspect", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest",
                 "--format", "{{index .Config.Labels \"com.sip-lims.commit-sha\"}}"],
                capture_output=True,
                text=True
            )
            
            final_sha = final_sha_result.stdout.strip()
            is_newer_sha = final_sha.startswith("139d2194")
            
            self.log_test(
                "Final image has newer SHA",
                is_newer_sha,
                f"Final SHA: {final_sha[:8]}... (should be newer: 139d2194...)"
            )
            
            # Verify update detection now shows no update needed
            sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
            from update_detector import UpdateDetector
            
            detector = UpdateDetector()
            final_result = detector.check_docker_image_update()
            
            no_update_needed = not final_result.get("update_available", True)
            
            self.log_test(
                "No update needed after update",
                no_update_needed,
                f"Update available: {final_result.get('update_available', 'unknown')}"
            )
            
            return is_newer_sha and no_update_needed
            
        except Exception as e:
            self.log_test("Final state verification", False, f"Exception: {e}")
            return False
    
    def run_final_corrected_workflow_test(self):
        """Run the final corrected workflow test."""
        print("🎯 Starting Final Corrected Workflow Test")
        print("=" * 80)
        print("This test validates the corrected workflow in proper order:")
        print("1. Set up realistic scenario (old local vs newer remote)")
        print("2. Test update detection BEFORE any updates")
        print("3. Test corrected update process with proper cleanup")
        print("4. Verify final state")
        print("=" * 80)
        
        try:
            # Step 1: Set up realistic scenario
            step1_success = self.setup_realistic_scenario()
            if not step1_success:
                print("❌ Cannot proceed without proper scenario setup")
                return False
            
            # Step 2: Test update detection BEFORE update (correct order)
            step2_success = self.test_update_detection_before_update()
            
            # Step 3: Test corrected update process
            step3_success = self.test_corrected_update_process()
            
            # Step 4: Test final state verification
            step4_success = self.test_final_state_verification()
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
        
        # Generate summary report
        print("\n" + "=" * 80)
        print("📊 FINAL CORRECTED WORKFLOW TEST SUMMARY")
        print("=" * 80)
        
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
        
        overall_success = failed_tests == 0
        print("\n🎯 OVERALL RESULT:", "✅ FINAL WORKFLOW FULLY CORRECTED!" if overall_success else "⚠️  WORKFLOW STILL HAS ISSUES")
        
        return overall_success

if __name__ == "__main__":
    tester = FinalWorkflowTester()
    success = tester.run_final_corrected_workflow_test()
    sys.exit(0 if success else 1)