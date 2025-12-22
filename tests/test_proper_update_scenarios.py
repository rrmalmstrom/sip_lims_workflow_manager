#!/usr/bin/env python3
"""
Proper Update Scenarios Test

This test simulates REAL user scenarios:
1. User has old local Docker image, newer version available remotely
2. User has old local scripts, newer version available remotely
3. Test the actual update detection and update process

This is the CORRECT way to test update detection.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add src to path to import update_detector
sys.path.insert(0, 'src')
from update_detector import UpdateDetector

class ProperUpdateScenarioTester:
    """Test update detection with proper old-local vs new-remote scenarios."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []
        self.original_dir = os.getcwd()
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
    
    def backup_current_latest_image(self):
        """Backup the current latest image so we can restore it later."""
        try:
            # Tag current latest as backup
            backup_result = subprocess.run(
                ["docker", "tag", 
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest",
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:test-backup"],
                capture_output=True,
                text=True
            )
            
            if backup_result.returncode == 0:
                self.backup_images.append("ghcr.io/rrmalmstrom/sip_lims_workflow_manager:test-backup")
                self.log_test("Backup current latest image", True, "Backed up as test-backup")
                return True
            else:
                self.log_test("Backup current latest image", False, f"Failed: {backup_result.stderr}")
                return False
        except Exception as e:
            self.log_test("Backup current latest image", False, f"Exception: {e}")
            return False
    
    def simulate_old_local_docker_scenario(self):
        """Simulate user having old local Docker image, test update detection."""
        print("\n🐳 Testing: User with OLD local Docker image vs NEW remote...")
        
        try:
            # Step 1: Remove current latest tag (simulate user doesn't have latest)
            remove_result = subprocess.run(
                ["docker", "rmi", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True,
                text=True
            )
            
            if remove_result.returncode != 0:
                self.log_test("Remove latest tag", False, f"Could not remove latest: {remove_result.stderr}")
                return
            
            self.log_test("Remove latest tag", True, "Removed latest tag to simulate old user")
            
            # Step 2: Tag the older image as latest (simulate user has old version as their "latest")
            tag_old_as_latest = subprocess.run(
                ["docker", "tag",
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation-5d38a20",
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True,
                text=True
            )
            
            if tag_old_as_latest.returncode != 0:
                self.log_test("Tag old as latest", False, f"Could not tag old as latest: {tag_old_as_latest.stderr}")
                return
            
            self.log_test("Tag old as latest", True, "Old image now tagged as latest (simulating user state)")
            
            # Step 3: Test update detection - should detect that local "latest" is old
            detector = UpdateDetector()
            
            # Get local image commit SHA (should be old)
            local_sha = detector.get_docker_image_commit_sha("latest")
            
            # Get remote commit SHA (should be newer)
            remote_sha = detector.get_remote_commit_sha("analysis/esp-docker-adaptation")
            
            self.log_test(
                "Get local vs remote SHAs",
                local_sha is not None and remote_sha is not None,
                f"Local: {local_sha[:8] if local_sha else 'None'}..., Remote: {remote_sha[:8] if remote_sha else 'None'}..."
            )
            
            # Step 4: Test update detection logic
            docker_result = detector.check_docker_image_update()
            update_available = docker_result.get("update_available", False)
            
            # Should detect update is available (local old != remote new)
            expected_update = local_sha != remote_sha
            
            self.log_test(
                "Docker update detection logic",
                update_available == expected_update,
                f"Update available: {update_available}, Expected: {expected_update}, SHAs different: {local_sha != remote_sha}"
            )
            
            # Step 5: Test the actual update process (pull newer version)
            if update_available:
                print("    Testing actual Docker update process...")
                
                # This would normally pull the latest, but we'll simulate by restoring our backup
                restore_result = subprocess.run(
                    ["docker", "tag",
                     "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:test-backup",
                     "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                    capture_output=True,
                    text=True
                )
                
                if restore_result.returncode == 0:
                    # Verify the update worked
                    new_local_sha = detector.get_docker_image_commit_sha("latest")
                    update_successful = new_local_sha == remote_sha
                    
                    self.log_test(
                        "Docker update process",
                        update_successful,
                        f"Update successful: {update_successful}, New local SHA: {new_local_sha[:8] if new_local_sha else 'None'}..."
                    )
                else:
                    self.log_test("Docker update process", False, "Could not restore newer image")
            
        except Exception as e:
            self.log_test("Old local Docker scenario", False, f"Exception: {e}")
    
    def simulate_old_local_scripts_scenario(self):
        """Simulate user having old local scripts, test update detection."""
        print("\n📜 Testing: User with OLD local scripts vs NEW remote...")
        
        try:
            # Create temp directory to simulate user's old scripts location
            old_scripts_dir = tempfile.mkdtemp(prefix="old_user_scripts_")
            self.temp_dirs.append(old_scripts_dir)
            
            print(f"Created simulated user scripts directory: {old_scripts_dir}")
            
            # Step 1: Clone repo and checkout old commit (simulate user's old scripts)
            clone_result = subprocess.run(
                ["git", "clone", ".", old_scripts_dir],
                capture_output=True,
                text=True,
                cwd=self.original_dir
            )
            
            if clone_result.returncode != 0:
                self.log_test("Clone for old scripts simulation", False, f"Clone failed: {clone_result.stderr}")
                return
            
            # Get commit history to find an old commit
            commits_result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                cwd=old_scripts_dir
            )
            
            if commits_result.returncode != 0:
                self.log_test("Get commits for old scripts", False, "Could not get commit history")
                return
            
            commits = commits_result.stdout.strip().split('\n')
            if len(commits) < 3:
                self.log_test("Find old commit for scripts", False, "Not enough commits")
                return
            
            # Use 3rd commit back as old version
            old_commit_line = commits[2]
            old_commit_sha = old_commit_line.split()[0]
            
            # Checkout old commit
            checkout_result = subprocess.run(
                ["git", "checkout", old_commit_sha],
                capture_output=True,
                text=True,
                cwd=old_scripts_dir
            )
            
            if checkout_result.returncode != 0:
                self.log_test("Checkout old commit for scripts", False, f"Checkout failed: {checkout_result.stderr}")
                return
            
            self.log_test("Setup old scripts scenario", True, f"User has old scripts at commit {old_commit_sha}")
            
            # Step 2: Test update detection from old scripts directory
            os.chdir(old_scripts_dir)
            
            old_detector = UpdateDetector()
            
            # Get local SHA (should be old)
            local_sha = old_detector.get_local_commit_sha()
            
            # Get remote SHA (should be newer)
            remote_sha = old_detector.get_remote_commit_sha("analysis/esp-docker-adaptation")
            
            # Step 3: Test scripts update detection
            scripts_result = old_detector.check_scripts_update("analysis/esp-docker-adaptation")
            update_available = scripts_result.get("update_available", False)
            
            # Should detect update is available
            expected_update = local_sha != remote_sha
            
            self.log_test(
                "Scripts update detection logic",
                update_available == expected_update,
                f"Local: {local_sha[:8] if local_sha else 'None'}..., Remote: {remote_sha[:8] if remote_sha else 'None'}..., Update available: {update_available}"
            )
            
            # Step 4: Test actual scripts download/update process
            if update_available:
                print("    Testing actual scripts update process...")
                
                # Create download directory
                download_dir = tempfile.mkdtemp(prefix="scripts_update_test_")
                self.temp_dirs.append(download_dir)
                
                # Test download
                download_success = old_detector.download_scripts("analysis/esp-docker-adaptation", download_dir)
                
                self.log_test(
                    "Scripts update download",
                    download_success,
                    f"Downloaded to: {download_dir}" if download_success else "Download failed"
                )
                
                if download_success:
                    # Verify downloaded files
                    downloaded_files = list(Path(download_dir).rglob("*.py"))
                    
                    self.log_test(
                        "Scripts update verification",
                        len(downloaded_files) > 0,
                        f"Downloaded {len(downloaded_files)} Python files"
                    )
            
            # Return to original directory
            os.chdir(self.original_dir)
            
        except Exception as e:
            self.log_test("Old local scripts scenario", False, f"Exception: {e}")
            os.chdir(self.original_dir)
    
    def test_complete_update_workflow(self):
        """Test the complete update workflow from detection to completion."""
        print("\n🔄 Testing: Complete update workflow...")
        
        try:
            detector = UpdateDetector()
            
            # Get update summary
            summary = detector.get_update_summary()
            
            any_updates = summary.get("any_updates_available", False)
            docker_update = summary.get("docker_update_available", False)
            scripts_update = summary.get("scripts_update_available", False)
            
            self.log_test(
                "Update summary generation",
                summary is not None,
                f"Any updates: {any_updates}, Docker: {docker_update}, Scripts: {scripts_update}"
            )
            
            # Test CLI interface
            cli_result = subprocess.run(
                [sys.executable, "src/update_detector.py", "--summary"],
                capture_output=True,
                text=True,
                cwd=self.original_dir
            )
            
            self.log_test(
                "CLI interface test",
                cli_result.returncode == 0,
                f"CLI output length: {len(cli_result.stdout)} chars"
            )
            
        except Exception as e:
            self.log_test("Complete update workflow", False, f"Exception: {e}")
    
    def cleanup(self):
        """Clean up temporary directories and Docker images."""
        # Clean up temp directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up: {temp_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up {temp_dir}: {e}")
        
        # Clean up backup Docker images
        for backup_image in self.backup_images:
            try:
                subprocess.run(["docker", "rmi", backup_image], capture_output=True)
                print(f"Cleaned up Docker image: {backup_image}")
            except Exception as e:
                print(f"Warning: Could not clean up {backup_image}: {e}")
    
    def run_proper_scenarios(self):
        """Run all proper update scenario tests."""
        print("🎯 Starting PROPER Update Scenarios Test")
        print("=" * 70)
        print("This test simulates REAL user scenarios:")
        print("- User has OLD local versions")
        print("- Newer versions available remotely") 
        print("- Test update detection and update process")
        print("=" * 70)
        
        # Backup current state
        if not self.backup_current_latest_image():
            print("❌ Could not backup current state, aborting test")
            return False
        
        try:
            # Run all test scenarios
            self.simulate_old_local_docker_scenario()
            self.simulate_old_local_scripts_scenario()
            self.test_complete_update_workflow()
            
        finally:
            # Always restore original state
            print("\n🔄 Restoring original state...")
            restore_result = subprocess.run(
                ["docker", "tag",
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:test-backup",
                 "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                capture_output=True,
                text=True
            )
            
            if restore_result.returncode == 0:
                print("✅ Restored original latest image")
            else:
                print("❌ Warning: Could not restore original latest image")
        
        # Generate summary report
        print("\n" + "=" * 70)
        print("📊 PROPER SCENARIOS TEST SUMMARY")
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
        
        print("\n🎯 OVERALL RESULT:", "✅ ALL SCENARIOS PASSED" if failed_tests == 0 else f"❌ {failed_tests} SCENARIOS FAILED")
        
        # Cleanup
        self.cleanup()
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = ProperUpdateScenarioTester()
    success = tester.run_proper_scenarios()
    sys.exit(0 if success else 1)