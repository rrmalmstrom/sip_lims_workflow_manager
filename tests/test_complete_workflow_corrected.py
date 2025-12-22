#!/usr/bin/env python3
"""
Test Complete Workflow with Corrected Logic

This test validates the complete real-world workflow:
1. Stop containers FIRST (like run.command does)
2. Test corrected update detection (GitHub API, no pulling)
3. Test improved Docker update process (remove old → install new)
4. Verify final state

Uses the actual run.command logic order and corrected update detection.
"""

import os
import sys
import subprocess
import tempfile
import time

class CompleteWorkflowTester:
    """Test complete workflow with corrected logic and proper order."""
    
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
    
    def get_workflow_containers(self):
        """Get workflow manager containers."""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "ancestor=ghcr.io/rrmalmstrom/sip_lims_workflow_manager", "--format", "{{.ID}}:{{.Names}}:{{.Status}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split(':')
                        if len(parts) >= 3:
                            containers.append({
                                "id": parts[0],
                                "name": parts[1],
                                "status": ':'.join(parts[2:])
                            })
                return containers
            return []
        except Exception:
            return []
    
    def test_step_1_stop_containers_first(self):
        """Test Step 1: Stop containers FIRST (like run.command does)."""
        print("\n🧪 TEST 1: Stop Containers First (matching run.command logic)")
        
        try:
            # Check containers before stopping
            containers_before = self.get_workflow_containers()
            
            self.log_test(
                "Containers running before stop",
                len(containers_before) > 0,
                f"Found {len(containers_before)} containers (should be 1 test container)"
            )
            
            # Use actual stop_workflow_containers logic from run.command
            stop_script = '''#!/bin/bash
echo "🛑 Checking for running workflow manager containers..."

workflow_containers=$(docker ps -a --filter "ancestor=ghcr.io/rrmalmstrom/sip_lims_workflow_manager" --filter "ancestor=sip-lims-workflow-manager" --format "{{.ID}} {{.Names}} {{.Status}}" 2>/dev/null)

if [ -n "$workflow_containers" ]; then
    echo "📋 Found workflow manager containers:"
    echo "$workflow_containers" | while read container_id container_name status; do
        echo "    - $container_name ($container_id): $status"
    done
    
    container_ids=$(echo "$workflow_containers" | awk '{print $1}')
    if [ -n "$container_ids" ]; then
        echo "🛑 Stopping workflow manager containers..."
        docker stop $container_ids >/dev/null 2>&1
        echo "🗑️  Removing workflow manager containers..."
        docker rm $container_ids >/dev/null 2>&1
        echo "✅ Workflow manager containers cleaned up"
        exit 0
    fi
else
    echo "✅ No running workflow manager containers found"
    exit 1
fi
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(stop_script)
                script_path = f.name
            
            try:
                os.chmod(script_path, 0o755)
                
                result = subprocess.run(
                    ["bash", script_path],
                    capture_output=True,
                    text=True
                )
                
                print(f"    📋 Container stop output:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"      {line}")
                
                # Check containers after stopping
                containers_after = self.get_workflow_containers()
                
                containers_stopped = len(containers_before) > 0 and len(containers_after) == 0
                
                self.log_test(
                    "Container stopping (run.command logic)",
                    containers_stopped or result.returncode == 1,
                    f"Before: {len(containers_before)}, After: {len(containers_after)}"
                )
                
                return containers_stopped
                
            finally:
                os.unlink(script_path)
                
        except Exception as e:
            self.log_test("Container stopping test", False, f"Exception: {e}")
            return False
    
    def test_step_2_corrected_update_detection(self):
        """Test Step 2: Corrected update detection (GitHub API, no pulling)."""
        print("\n🧪 TEST 2: Corrected Update Detection (GitHub API, no pulling)")
        
        try:
            # Import corrected update detector
            sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
            from update_detector import UpdateDetector
            
            detector = UpdateDetector()
            
            # Get current images before detection
            images_before = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager", "--format", "{{.ID}}"],
                capture_output=True,
                text=True
            ).stdout.strip().split('\n')
            
            # Run corrected update detection
            result = detector.check_docker_image_update()
            
            # Get images after detection (should be same - no pulling during detection)
            images_after = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager", "--format", "{{.ID}}"],
                capture_output=True,
                text=True
            ).stdout.strip().split('\n')
            
            # Verify no new images were pulled during detection
            no_new_images = len(images_before) == len(images_after)
            
            self.log_test(
                "No pulling during detection",
                no_new_images,
                f"Images before: {len(images_before)}, after: {len(images_after)}"
            )
            
            # Verify update detection works
            update_detected = result.get("update_available", False)
            has_local_remote_image = result.get("has_local_remote_image", False)
            
            self.log_test(
                "Update detection functionality",
                update_detected and has_local_remote_image,
                f"Update available: {update_detected}, Has local remote image: {has_local_remote_image}"
            )
            
            # Verify SHA comparison
            local_sha = result.get("local_image_sha", "")
            remote_sha = result.get("remote_image_sha", "")
            
            self.log_test(
                "SHA comparison via GitHub API",
                local_sha != remote_sha and len(local_sha) > 0 and len(remote_sha) > 0,
                f"Local: {local_sha[:8]}..., Remote: {remote_sha[:8]}..."
            )
            
            return update_detected
            
        except Exception as e:
            self.log_test("Corrected update detection test", False, f"Exception: {e}")
            return False
    
    def test_step_3_improved_docker_update(self):
        """Test Step 3: Improved Docker update process (remove old → install new)."""
        print("\n🧪 TEST 3: Improved Docker Update Process (remove old → install new)")
        
        try:
            # Get current image ID
            old_image_result = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", "--format", "{{.ID}}"],
                capture_output=True,
                text=True
            )
            old_image_id = old_image_result.stdout.strip()
            
            self.log_test(
                "Current old image detected",
                len(old_image_id) > 0,
                f"Old image ID: {old_image_id[:12]}..."
            )
            
            # Test improved update process
            update_script = f'''#!/bin/bash
set -e

echo "🔍 Testing improved Docker update process..."
echo "📦 Current old image: {old_image_id[:12]}..."

# Remove old image BEFORE pulling new (improved logic)
echo "🧹 Removing old image before update..."
docker rmi ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Old image removed successfully"
else
    echo "⚠️  Could not remove old image"
fi

# Pull new image
echo "📥 Pulling latest Docker image..."
docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ New image pulled successfully"
    
    new_image_id=$(docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --format "{{{{.ID}}}}" 2>/dev/null)
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
                    "Improved update process",
                    update_successful,
                    f"Update successful: {update_successful}"
                )
                
                return update_successful
                
            finally:
                os.unlink(script_path)
                
        except Exception as e:
            self.log_test("Improved Docker update test", False, f"Exception: {e}")
            return False
    
    def test_step_4_verify_final_state(self):
        """Test Step 4: Verify final state."""
        print("\n🧪 TEST 4: Verify Final State")
        
        try:
            # Check final image
            final_image_result = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", "--format", "{{.ID}}"],
                capture_output=True,
                text=True
            )
            final_image_id = final_image_result.stdout.strip()
            
            self.log_test(
                "New image is tagged as latest",
                len(final_image_id) > 0,
                f"Final image ID: {final_image_id[:12]}..."
            )
            
            # Check SHA of final image
            sha_result = subprocess.run(
                ["docker", "inspect", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", "--format", "{{index .Config.Labels \"com.sip-lims.commit-sha\"}}"],
                capture_output=True,
                text=True
            )
            final_sha = sha_result.stdout.strip()
            
            # Should be the newer SHA (139d2194...)
            is_newer_sha = final_sha.startswith("139d2194")
            
            self.log_test(
                "Final image has newer SHA",
                is_newer_sha,
                f"Final SHA: {final_sha[:8]}... (should be 139d2194...)"
            )
            
            # Check no containers running
            final_containers = self.get_workflow_containers()
            
            self.log_test(
                "No containers running after update",
                len(final_containers) == 0,
                f"Final containers: {len(final_containers)}"
            )
            
            return is_newer_sha and len(final_containers) == 0
            
        except Exception as e:
            self.log_test("Final state verification", False, f"Exception: {e}")
            return False
    
    def run_complete_workflow_test(self):
        """Run complete workflow test with corrected logic."""
        print("🎯 Starting Complete Workflow Test (Corrected Logic)")
        print("=" * 80)
        print("This test validates the corrected workflow:")
        print("1. Stop containers FIRST (like run.command)")
        print("2. Corrected update detection (GitHub API, no pulling)")
        print("3. Improved Docker update (remove old → install new)")
        print("4. Verify final state")
        print("=" * 80)
        
        try:
            # Step 1: Stop containers first (like run.command)
            step1_success = self.test_step_1_stop_containers_first()
            
            # Step 2: Test corrected update detection
            step2_success = self.test_step_2_corrected_update_detection()
            
            # Step 3: Test improved Docker update process
            step3_success = self.test_step_3_improved_docker_update()
            
            # Step 4: Verify final state
            step4_success = self.test_step_4_verify_final_state()
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
        
        # Generate summary report
        print("\n" + "=" * 80)
        print("📊 COMPLETE WORKFLOW TEST SUMMARY (CORRECTED LOGIC)")
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
        
        print("\n🎯 OVERALL RESULT:", "✅ CORRECTED WORKFLOW VERIFIED" if failed_tests == 0 else "⚠️  WORKFLOW TESTED")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = CompleteWorkflowTester()
    success = tester.run_complete_workflow_test()
    sys.exit(0 if success else 1)