#!/usr/bin/env python3
"""
Test-Driven Development tests for deterministic build implementation
Tests the complete deterministic build workflow before committing
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path

class TestDeterministicBuild:
    """Test suite for deterministic build implementation"""
    
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
    
    def test_required_files_exist(self):
        """Test that all required files for deterministic build exist"""
        required_files = [
            "Dockerfile",
            "conda-lock.txt", 
            "requirements-lock.txt",
            "archive/environment-docker-final-validated.yml",
            "build_and_push.sh",
            "DEVELOPMENT_WORKFLOW.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        passed = len(missing_files) == 0
        message = f"Missing files: {missing_files}" if missing_files else "All required files present"
        self.log_test("Required files exist", passed, message)
        return passed
    
    def test_dockerfile_uses_deterministic_approach(self):
        """Test that Dockerfile uses deterministic build approach"""
        dockerfile_path = self.project_root / "Dockerfile"
        
        if not dockerfile_path.exists():
            self.log_test("Dockerfile deterministic check", False, "Dockerfile not found")
            return False
        
        content = dockerfile_path.read_text()
        
        # Check for pinned base image
        has_pinned_base = "@sha256:" in content
        
        # Check for lock file usage
        uses_conda_lock = "conda-lock.txt" in content
        uses_requirements_lock = "requirements-lock.txt" in content
        
        # Check for deterministic label
        has_deterministic_label = "com.sip-lims.build-type" in content and "deterministic" in content
        
        all_checks = [has_pinned_base, uses_conda_lock, uses_requirements_lock, has_deterministic_label]
        passed = all(all_checks)
        
        issues = []
        if not has_pinned_base:
            issues.append("No pinned base image (@sha256)")
        if not uses_conda_lock:
            issues.append("Not using conda-lock.txt")
        if not uses_requirements_lock:
            issues.append("Not using requirements-lock.txt")
        if not has_deterministic_label:
            issues.append("Missing deterministic build label")
        
        message = f"Issues: {issues}" if issues else "Dockerfile properly configured for deterministic builds"
        self.log_test("Dockerfile uses deterministic approach", passed, message)
        return passed
    
    def test_lock_files_valid(self):
        """Test that lock files are valid and contain packages"""
        conda_lock_path = self.project_root / "conda-lock.txt"
        requirements_lock_path = self.project_root / "requirements-lock.txt"
        
        issues = []
        
        # Test conda-lock.txt
        if conda_lock_path.exists():
            conda_content = conda_lock_path.read_text()
            if not conda_content.strip():
                issues.append("conda-lock.txt is empty")
            elif "https://conda.anaconda.org" not in conda_content:
                issues.append("conda-lock.txt doesn't contain conda URLs")
        else:
            issues.append("conda-lock.txt missing")
        
        # Test requirements-lock.txt
        if requirements_lock_path.exists():
            req_content = requirements_lock_path.read_text()
            if not req_content.strip():
                issues.append("requirements-lock.txt is empty")
            elif "==" not in req_content:
                issues.append("requirements-lock.txt doesn't contain pinned versions")
        else:
            issues.append("requirements-lock.txt missing")
        
        passed = len(issues) == 0
        message = f"Issues: {issues}" if issues else "Lock files are valid"
        self.log_test("Lock files are valid", passed, message)
        return passed
    
    def test_build_script_executable(self):
        """Test that build script exists and is executable"""
        script_path = self.project_root / "build_and_push.sh"
        
        if not script_path.exists():
            self.log_test("Build script executable", False, "build_and_push.sh not found")
            return False
        
        is_executable = os.access(script_path, os.X_OK)
        message = "Script is executable" if is_executable else "Script is not executable (run: chmod +x build_and_push.sh)"
        self.log_test("Build script executable", is_executable, message)
        return is_executable
    
    def test_github_actions_removed(self):
        """Test that GitHub Actions workflow was removed"""
        workflow_path = self.project_root / ".github/workflows/docker-build.yml"
        removed = not workflow_path.exists()
        
        message = "GitHub Actions workflow removed" if removed else "GitHub Actions workflow still exists"
        self.log_test("GitHub Actions workflow removed", removed, message)
        return removed
    
    def test_docker_available(self):
        """Test that Docker is available for building"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            docker_available = result.returncode == 0
            message = f"Docker version: {result.stdout.strip()}" if docker_available else "Docker not available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            docker_available = False
            message = "Docker command not found"
        
        self.log_test("Docker available", docker_available, message)
        return docker_available
    
    def test_dry_run_build_script(self):
        """Test build script syntax without actually building"""
        script_path = self.project_root / "build_and_push.sh"
        
        if not script_path.exists():
            self.log_test("Build script syntax", False, "Script not found")
            return False
        
        try:
            # Test bash syntax
            result = subprocess.run(["bash", "-n", str(script_path)], 
                                  capture_output=True, text=True, timeout=10)
            syntax_ok = result.returncode == 0
            message = "Script syntax is valid" if syntax_ok else f"Syntax error: {result.stderr}"
        except subprocess.TimeoutExpired:
            syntax_ok = False
            message = "Script syntax check timed out"
        
        self.log_test("Build script syntax", syntax_ok, message)
        return syntax_ok
    
    def run_all_tests(self):
        """Run all tests and return overall result"""
        print("🧪 Running TDD tests for deterministic build implementation")
        print("=" * 60)
        
        tests = [
            self.test_required_files_exist,
            self.test_dockerfile_uses_deterministic_approach,
            self.test_lock_files_valid,
            self.test_build_script_executable,
            self.test_github_actions_removed,
            self.test_docker_available,
            self.test_dry_run_build_script
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
        
        print("=" * 60)
        print(f"📊 Test Results: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 All tests passed! Ready for implementation.")
            return True
        else:
            print("❌ Some tests failed. Fix issues before proceeding.")
            return False

if __name__ == "__main__":
    tester = TestDeterministicBuild()
    success = tester.run_all_tests()
    exit(0 if success else 1)