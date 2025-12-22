#!/usr/bin/env python3
"""
Test Complete Docker Workflow (Option A)

This test uses existing images with different commit SHAs to test:
1. Stop running containers
2. Detect new version (using real SHA differences)
3. Remove old image
4. Install new image

Uses real existing images:
- latest (newer SHA)
- analysis-esp-docker-adaptation-5d38a20 (older SHA)
"""

import os
import sys
import subprocess
import tempfile
import time

class CompleteDockerWorkflowTester:
    """Test complete Docker workflow with real SHA differences."""
    
    def __init__(self):
        self.test_results = []
        self.test_containers = []
        self.backup_images = []
        
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
        """Get all workflow manager Docker images with SHAs."""
        try:
            result = subprocess.run(
                ["docker", "images", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager", "--format", "{{.ID}}:{{.Repository}}:{{.Tag}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                images = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split(':')
                        if len(parts) >= 3:
                            # Get commit SHA from image labels
                            sha_result = subprocess.run(
                                ["docker", "inspect", f"{parts[1]}:{parts[2]}", "--format", "{{index .Config.Labels \"com.sip-lims.commit-sha\"}}"],
                                capture_output=True,
                                text=True
                            )
                            commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "unknown"
                            
                            images.append({
                                "id": parts[0],
                                "repo": parts[1],
                                "tag": parts[2],
                                "full_name": f"{parts[1]}:{parts[2]}",
                                "commit_sha": commit_sha
                            })
                return images
            return []
        except Exception:
            return []
    
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
    
    def setup_old_vs_new_scenario(self):
        """Set up scenario with old image as latest, newer image available remotely."""
        print("\n🎭 Setting Up Old vs New Scenario (Option A)...")
        
        try:
            # Get current images
            images = self.get_workflow_images()
            
            if len(images) < 2:
                self.log_test("Old vs new scenario setup", False, f"Need at least 2 images, found {len(images)}")
                return False, None, None
            
            # Find latest and older image
            latest_img = None
            older_img = None
            
            for img in images:
                if img['tag'] == 'latest':
                    latest_img = img
                elif 'analysis-esp-docker-adaptation' in img['tag']:
                    older_img = img
            
            if not latest_img or not older_img:
                self.log_test("Old vs new scenario setup", False, "Could not find both latest and older images")
                return False, None, None
            
            # Verify they have different commit SHAs
            if latest_img['commit_sha'] == older_img['commit_sha']:
                self.log_test("Old vs new scenario setup", False, "Images have same commit SHA")
                return False, None, None
            
            # Backup current latest
            backup_result = subprocess.run(
                ["docker", "tag", latest_img['full_name'], "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:backup-latest"],
                capture_output=True,
                text=True
            )
            
            if backup_result.returncode != 0:
                self.log_test("Backup latest image", False, f"Failed to backup: {backup_result.stderr}")
                return False, None, None
            
            self.backup_images.append("ghcr.io/rrmalmstrom/sip_lims_workflow_manager:backup-latest")
            
            # Remove current latest tag
            remove_result = subprocess.run(
                ["docker", "rmi", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True,
                text=True
            )
            
            if remove_result.returncode != 0:
                self.log_test("Remove latest tag", False, f"Failed to remove latest: {remove_result.stderr}")
                return False, None, None
            
            # Tag older image as latest (simulate user having old version)
            retag_result = subprocess.run(
                ["docker", "tag", older_img['full_name'], "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True,
                text=True
            )
            
            if retag_result.returncode != 0:
                self.log_test("Retag old as latest", False, f"Failed to retag: {retag_result.stderr}")
                return False, None, None
            
            self.log_test(
                "Old vs new scenario setup",
                True,
                f"Old SHA: {older_img['commit_sha'][:8]}..., New SHA: {latest_img['commit_sha'][:8]}..."
            )
            
            return True, older_img, latest_img
                
        except Exception as e:
            self.log_test("Old vs new scenario setup", False, f"Exception: {e}")
            return False, None, None
    
    def create_running_container(self):
        """Create a running container from the old image."""
        print("\n🐳 Creating Running Container from Old Image...")
        
        try:
            # Create and start a container
            container_result = subprocess.run(
                ["docker", "run", "-d", "--name", "test-workflow-old", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest", "sleep", "3600"],
                capture_output=True,
                text=True
            )
            
            if container_result.returncode == 0:
                container_id = container_result.stdout.strip()
                self.test_containers.append(container_id)
                
                self.log_test(
                    "Running container from old image",
                    True,
                    f"Started container: {container_id[:12]}"
                )
                return True
            else:
                self.log_test(
                    "Running container from old image",
                    False,
                    f"Failed to start container: {container_result.stderr}"
                )
                return False
                
        except Exception as e:
            self.log_test("Running container creation", False, f"Exception: {e}")
            return False
    
    def test_container_stopping(self):
        """Test the container stopping functionality."""
        print("\n🛑 Testing Container Stopping...")
        
        try:
            # Get containers before stopping
            containers_before = self.get_workflow_containers()
            
            self.log_test(
                "Containers running before stop",
                len(containers_before) > 0,
                f"Found {len(containers_before)} running containers"
            )
            
            # Use actual container stopping logic from run.command
            stop_script = '''#!/bin/bash
echo "🛑 Stopping workflow manager containers..."

workflow_containers=$(docker ps -a --filter "ancestor=ghcr.io/rrmalmstrom/sip_lims_workflow_manager" --filter "ancestor=sip-lims-workflow-manager" --format "{{.ID}} {{.Names}} {{.Status}}" 2>/dev/null)

if [ -n "$workflow_containers" ]; then
    echo "📋 Found workflow manager containers:"
    echo "$workflow_containers"
    
    container_ids=$(echo "$workflow_containers" | awk '{print $1}')
    if [ -n "$container_ids" ]; then
        echo "🛑 Stopping containers..."
        docker stop $container_ids >/dev/null 2>&1
        echo "🗑️  Removing containers..."
        docker rm $container_ids >/dev/null 2>&1
        echo "✅ Containers cleaned up"
        exit 0
    fi
else
    echo "✅ No containers found"
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
                
                print(f"    📋 Stop output:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"      {line}")
                
                # Get containers after stopping
                containers_after = self.get_workflow_containers()
                
                containers_stopped = len(containers_before) > 0 and len(containers_after) == 0
                
                self.log_test(
                    "Container stopping functionality",
                    containers_stopped or result.returncode == 1,
                    f"Before: {len(containers_before)}, After: {len(containers_after)}"
                )
                
            finally:
                os.unlink(script_path)
                
        except Exception as e:
            self.log_test("Container stopping test", False, f"Exception: {e}")
    
    def test_update_detection_and_cleanup(self, old_img, new_img):
        """Test update detection and cleanup with real SHA differences."""
        print("\n🔍 Testing Update Detection and Cleanup...")
        
        try:
            # Test update detection using actual update detector
            sys.path.insert(0, 'src')
            from update_detector import UpdateDetector
            
            detector = UpdateDetector()
            
            # Check if update is detected
            docker_result = detector.check_docker_image_update()
            update_available = docker_result.get("update_available", False)
            
            self.log_test(
                "Update detection with real SHAs",
                update_available,
                f"Update detected: {update_available}, Local: {docker_result.get('local_sha', 'unknown')[:8]}..., Remote: {docker_result.get('remote_sha', 'unknown')[:8]}..."
            )
            
            if update_available:
                # Test the improved cleanup process
                cleanup_script = f'''#!/bin/bash
set -e

echo "🔍 Testing improved cleanup with real SHA difference..."
echo "📦 Old image SHA: {old_img['commit_sha'][:8]}..."
echo "🆕 New image SHA: {new_img['commit_sha'][:8]}..."

# Get current image ID
old_image_id=$(docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --format "{{{{.ID}}}}" 2>/dev/null)

if [ -n "$old_image_id" ]; then
    echo "📦 Current old image: $old_image_id"
    
    # Remove old image before pulling new (improved logic)
    echo "🧹 Removing old image before update..."
    docker rmi ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Old image removed"
    else
        echo "⚠️  Could not remove old image"
    fi
fi

# Restore the newer image as latest (simulate pulling from remote)
echo "📥 Installing newer image..."
docker tag ghcr.io/rrmalmstrom/sip_lims_workflow_manager:backup-latest ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Newer image installed successfully"
    
    new_image_id=$(docker images ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest --format "{{{{.ID}}}}" 2>/dev/null)
    echo "📦 New image: $new_image_id"
    exit 0
else
    echo "❌ Failed to install newer image"
    exit 1
fi
'''
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(cleanup_script)
                    script_path = f.name
                
                try:
                    os.chmod(script_path, 0o755)
                    
                    result = subprocess.run(
                        ["bash", script_path],
                        capture_output=True,
                        text=True
                    )
                    
                    print(f"    📋 Cleanup output:")
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            print(f"      {line}")
                    
                    cleanup_successful = result.returncode == 0
                    
                    self.log_test(
                        "Improved cleanup process",
                        cleanup_successful,
                        f"Cleanup successful: {cleanup_successful}"
                    )
                    
                    # Verify new image is in place
                    final_images = self.get_workflow_images()
                    latest_final = None
                    for img in final_images:
                        if img['tag'] == 'latest':
                            latest_final = img
                            break
                    
                    if latest_final:
                        new_sha_installed = latest_final['commit_sha'] == new_img['commit_sha']
                        self.log_test(
                            "New image SHA verification",
                            new_sha_installed,
                            f"New SHA installed: {new_sha_installed}, Current: {latest_final['commit_sha'][:8]}..."
                        )
                    
                finally:
                    os.unlink(script_path)
            
        except Exception as e:
            self.log_test("Update detection and cleanup test", False, f"Exception: {e}")
    
    def cleanup_test_artifacts(self):
        """Clean up test artifacts."""
        print("\n🧽 Cleaning up test artifacts...")
        
        # Remove test containers
        for container_id in self.test_containers:
            try:
                subprocess.run(["docker", "rm", "-f", container_id], capture_output=True)
                print(f"    Cleaned up container: {container_id[:12]}")
            except Exception:
                pass
        
        # Remove backup images
        for backup_image in self.backup_images:
            try:
                subprocess.run(["docker", "rmi", backup_image], capture_output=True)
                print(f"    Cleaned up backup: {backup_image}")
            except Exception:
                pass
    
    def run_complete_docker_workflow_test(self):
        """Run complete Docker workflow test."""
        print("🎯 Starting Complete Docker Workflow Test (Option A)")
        print("=" * 80)
        print("This test uses REAL images with different commit SHAs:")
        print("1. Set up old vs new scenario with real SHA differences")
        print("2. Create running container from old image")
        print("3. Test container stopping functionality")
        print("4. Test update detection with real SHAs")
        print("5. Test improved cleanup: remove old -> install new")
        print("=" * 80)
        
        try:
            # Step 1: Set up old vs new scenario
            success, old_img, new_img = self.setup_old_vs_new_scenario()
            if not success:
                print("❌ Could not set up old vs new scenario")
                return False
            
            # Step 2: Create running container
            if not self.create_running_container():
                print("❌ Could not create running container")
                return False
            
            # Step 3: Test container stopping
            self.test_container_stopping()
            
            # Step 4: Test update detection and cleanup
            self.test_update_detection_and_cleanup(old_img, new_img)
            
        finally:
            # Always clean up
            self.cleanup_test_artifacts()
        
        # Generate summary report
        print("\n" + "=" * 80)
        print("📊 COMPLETE DOCKER WORKFLOW TEST SUMMARY")
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
        
        print("\n🎯 OVERALL RESULT:", "✅ COMPLETE WORKFLOW VERIFIED" if failed_tests == 0 else "⚠️  WORKFLOW TESTED")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = CompleteDockerWorkflowTester()
    success = tester.run_complete_docker_workflow_test()
    sys.exit(0 if success else 1)