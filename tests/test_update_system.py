#!/usr/bin/env python3
"""
Comprehensive Update System Test

Tests all aspects of the update detection and download system:
1. Version detection logic
2. Docker image update process
3. Scripts download process
4. Error handling
5. Integration scenarios
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

class UpdateSystemTester:
    """Comprehensive tester for the update detection system."""
    
    def __init__(self):
        self.detector = UpdateDetector()
        self.test_results = []
        self.temp_dirs = []
    
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
    
    def test_version_detection(self):
        """Test 1: Version Detection Logic"""
        print("\n🔍 Testing Version Detection Logic...")
        
        try:
            # Test local commit SHA detection
            local_sha = self.detector.get_local_commit_sha()
            self.log_test(
                "Local commit SHA detection",
                local_sha is not None and len(local_sha) == 40,
                f"SHA: {local_sha[:8]}..." if local_sha else "No SHA detected"
            )
            
            # Test remote commit SHA detection
            remote_sha = self.detector.get_remote_commit_sha("main")
            self.log_test(
                "Remote commit SHA detection",
                remote_sha is not None and len(remote_sha) == 40,
                f"SHA: {remote_sha[:8]}..." if remote_sha else "No SHA detected"
            )
            
            # Test Docker image commit SHA detection
            docker_sha = self.detector.get_docker_image_commit_sha()
            self.log_test(
                "Docker image commit SHA detection",
                docker_sha is not None and len(docker_sha) == 40,
                f"SHA: {docker_sha[:8]}..." if docker_sha else "No SHA detected"
            )
            
        except Exception as e:
            self.log_test("Version detection", False, f"Exception: {e}")
    
    def test_update_detection(self):
        """Test 2: Update Detection Logic"""
        print("\n🔄 Testing Update Detection Logic...")
        
        try:
            # Test Docker image update detection
            docker_result = self.detector.check_docker_image_update()
            self.log_test(
                "Docker image update detection",
                "update_available" in docker_result and "error" in docker_result,
                f"Update available: {docker_result.get('update_available')}, Error: {docker_result.get('error')}"
            )
            
            # Test scripts update detection
            scripts_result = self.detector.check_scripts_update()
            self.log_test(
                "Scripts update detection",
                "update_available" in scripts_result and "error" in scripts_result,
                f"Update available: {scripts_result.get('update_available')}, Error: {scripts_result.get('error')}"
            )
            
            # Test summary generation
            summary = self.detector.get_update_summary()
            self.log_test(
                "Update summary generation",
                "docker" in summary and "scripts" in summary and "any_updates_available" in summary,
                f"Any updates: {summary.get('any_updates_available')}"
            )
            
        except Exception as e:
            self.log_test("Update detection", False, f"Exception: {e}")
    
    def test_scripts_download(self):
        """Test 3: Scripts Download Process"""
        print("\n📥 Testing Scripts Download Process...")
        
        try:
            # Create temporary directory for download test
            test_dir = tempfile.mkdtemp(prefix="update_test_scripts_")
            self.temp_dirs.append(test_dir)
            
            # Test scripts download
            success = self.detector.download_scripts("main", test_dir)
            self.log_test(
                "Scripts download from GitHub",
                success,
                f"Downloaded to: {test_dir}" if success else "Download failed"
            )
            
            if success:
                # Check if files were actually downloaded
                downloaded_files = list(Path(test_dir).rglob("*.py"))
                self.log_test(
                    "Scripts file extraction",
                    len(downloaded_files) > 0,
                    f"Found {len(downloaded_files)} Python files"
                )
                
                # Check for expected directories
                expected_dirs = ["src", "utils", "tests"]
                found_dirs = [d.name for d in Path(test_dir).iterdir() if d.is_dir()]
                expected_found = [d for d in expected_dirs if d in found_dirs]
                self.log_test(
                    "Directory structure preservation",
                    len(expected_found) > 0,
                    f"Found directories: {found_dirs}"
                )
            
        except Exception as e:
            self.log_test("Scripts download", False, f"Exception: {e}")
    
    def test_docker_operations(self):
        """Test 4: Docker Operations"""
        print("\n🐳 Testing Docker Operations...")
        
        try:
            # Test Docker availability
            docker_available = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True
            ).returncode == 0
            
            self.log_test(
                "Docker availability",
                docker_available,
                "Docker is running" if docker_available else "Docker not available"
            )
            
            if docker_available:
                # Test Docker image inspection
                try:
                    result = subprocess.run(
                        ["docker", "inspect", "ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    inspect_data = json.loads(result.stdout)
                    labels = inspect_data[0]["Config"]["Labels"]
                    
                    has_commit_label = "com.sip-lims.commit-sha" in labels
                    self.log_test(
                        "Docker image label inspection",
                        has_commit_label,
                        f"Commit SHA label: {labels.get('com.sip-lims.commit-sha', 'Not found')[:8]}..." if has_commit_label else "No commit SHA label"
                    )
                    
                except subprocess.CalledProcessError:
                    self.log_test(
                        "Docker image inspection",
                        False,
                        "Could not inspect Docker image - may need to pull first"
                    )
            
        except Exception as e:
            self.log_test("Docker operations", False, f"Exception: {e}")
    
    def test_error_handling(self):
        """Test 5: Error Handling"""
        print("\n⚠️  Testing Error Handling...")
        
        try:
            # Test with invalid repository
            invalid_detector = UpdateDetector("invalid_user", "invalid_repo")
            
            # Test remote SHA with invalid repo
            invalid_sha = invalid_detector.get_remote_commit_sha()
            self.log_test(
                "Invalid repository handling",
                invalid_sha is None,
                "Correctly returned None for invalid repository"
            )
            
            # Test Docker image with invalid repo
            invalid_docker = invalid_detector.check_docker_image_update()
            self.log_test(
                "Invalid Docker image handling",
                invalid_docker.get("error") is not None or invalid_docker.get("remote_sha") is None,
                f"Error handling: {invalid_docker.get('error', 'No error, but no SHA')}"
            )
            
            # Test scripts download with invalid repo
            invalid_download = invalid_detector.download_scripts("main", tempfile.mkdtemp())
            self.log_test(
                "Invalid scripts download handling",
                not invalid_download,
                "Correctly failed for invalid repository"
            )
            
        except Exception as e:
            self.log_test("Error handling", False, f"Exception: {e}")
    
    def test_command_line_interface(self):
        """Test 6: Command Line Interface"""
        print("\n💻 Testing Command Line Interface...")
        
        try:
            # Test --summary command
            result = subprocess.run(
                ["python3", "src/update_detector.py", "--summary"],
                capture_output=True,
                text=True
            )
            
            summary_success = result.returncode == 0
            self.log_test(
                "CLI --summary command",
                summary_success,
                f"Exit code: {result.returncode}"
            )
            
            if summary_success:
                try:
                    summary_data = json.loads(result.stdout)
                    has_required_fields = all(key in summary_data for key in ["docker", "scripts", "any_updates_available"])
                    self.log_test(
                        "CLI JSON output format",
                        has_required_fields,
                        f"Required fields present: {has_required_fields}"
                    )
                except json.JSONDecodeError:
                    self.log_test("CLI JSON output format", False, "Invalid JSON output")
            
            # Test --check-docker command
            result = subprocess.run(
                ["python3", "src/update_detector.py", "--check-docker"],
                capture_output=True,
                text=True
            )
            
            self.log_test(
                "CLI --check-docker command",
                result.returncode == 0,
                f"Exit code: {result.returncode}"
            )
            
        except Exception as e:
            self.log_test("Command line interface", False, f"Exception: {e}")
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up {temp_dir}: {e}")
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        print("🧪 Starting Comprehensive Update System Test")
        print("=" * 50)
        
        # Run all test suites
        self.test_version_detection()
        self.test_update_detection()
        self.test_scripts_download()
        self.test_docker_operations()
        self.test_error_handling()
        self.test_command_line_interface()
        
        # Generate summary report
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY REPORT")
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
        
        print("\n🎯 OVERALL RESULT:", "✅ ALL TESTS PASSED" if failed_tests == 0 else f"❌ {failed_tests} TESTS FAILED")
        
        # Cleanup
        self.cleanup()
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = UpdateSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)