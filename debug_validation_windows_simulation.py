#!/usr/bin/env python3
"""
Smart Sync Debug Validation Script for Windows Simulation

This script validates the Smart Sync debug logging implementation by simulating
Windows network drive scenarios on macOS. It tests all logging components and
validates that debug information is properly captured.

Usage:
    # Enable debug logging and run validation
    export SMART_SYNC_DEBUG=true
    export SMART_SYNC_DEBUG_LEVEL=DEBUG
    python debug_validation_windows_simulation.py

Features:
- Simulates Windows network drive detection
- Tests Smart Sync manager initialization
- Validates all logging components
- Generates comprehensive debug reports
- Verifies log file structure and content
"""

import os
import sys
import tempfile
import shutil
import json
import platform
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock
import subprocess

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.debug_logger import (
    SmartSyncDebugLogger, DebugTestValidator, LogLevel,
    debug_context, log_info, log_error, log_warning,
    debug_enabled, get_debug_level, close_debug_logger
)


class WindowsSimulationValidator:
    """
    Validates Smart Sync debug logging by simulating Windows scenarios.
    """
    
    def __init__(self, test_dir: Path = None):
        """Initialize the validation environment."""
        self.test_dir = test_dir or Path(tempfile.mkdtemp(prefix="smart_sync_debug_test_"))
        self.network_drive_path = self.test_dir / "network_drive" / "Z_drive"
        self.local_staging_path = self.test_dir / "local_staging" / "C_temp"
        self.log_file = self.test_dir / ".smart_sync_debug.log"
        
        # Create test directory structure
        self.network_drive_path.mkdir(parents=True, exist_ok=True)
        self.local_staging_path.mkdir(parents=True, exist_ok=True)
        
        # Test results
        self.test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "debug_entries": [],
            "performance_data": {}
        }
        
        print(f"🧪 Windows Simulation Test Environment: {self.test_dir}")
        print(f"📁 Simulated Network Drive: {self.network_drive_path}")
        print(f"💾 Simulated Local Staging: {self.local_staging_path}")
        print(f"📝 Debug Log File: {self.log_file}")
    
    def setup_windows_environment(self):
        """Set up environment variables to simulate Windows Smart Sync scenario."""
        os.environ["SMART_SYNC_DEBUG"] = "true"
        os.environ["SMART_SYNC_DEBUG_LEVEL"] = "DEBUG"
        os.environ["SMART_SYNC_ENABLED"] = "true"
        os.environ["NETWORK_PROJECT_PATH"] = str(self.network_drive_path)
        os.environ["LOCAL_PROJECT_PATH"] = str(self.local_staging_path)
        
        print("✅ Windows environment variables configured")
    
    def create_test_project(self):
        """Create a test project structure in the simulated network drive."""
        # Create workflow file
        workflow_content = """
workflow_name: "Test Smart Sync Workflow"
steps:
  - id: "step1"
    name: "Test Step 1"
    script: "test_script.py"
    snapshot_items: ["data/"]
  - id: "step2"
    name: "Test Step 2"
    script: "test_script2.py"
"""
        
        workflow_file = self.network_drive_path / "workflow.yml"
        with open(workflow_file, 'w') as f:
            f.write(workflow_content)
        
        # Create test data
        data_dir = self.network_drive_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        test_file = data_dir / "test_data.txt"
        with open(test_file, 'w') as f:
            f.write("Test data for Smart Sync validation")
        
        # Create scripts directory
        scripts_dir = self.network_drive_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        print("✅ Test project structure created")
    
    def test_debug_logger_initialization(self):
        """Test debug logger initialization and basic functionality."""
        self.test_results["tests_run"] += 1
        
        try:
            # Test logger creation
            logger = SmartSyncDebugLogger(
                log_file=self.log_file,
                console_output=True,
                log_level=LogLevel.DEBUG
            )
            
            # Test basic logging
            logger.info("Test info message", test_param="test_value")
            logger.debug("Test debug message", debug_param=123)
            logger.warning("Test warning message", warning_param=True)
            logger.error("Test error message", error_param="test_error")
            
            # Test operation timer
            with logger.operation_timer("test_operation", test_context="validation") as op_id:
                import time
                time.sleep(0.1)  # Simulate work
            
            logger.close()
            
            # Validate log file exists and has content
            if not self.log_file.exists():
                raise AssertionError("Log file was not created")
            
            with open(self.log_file, 'r') as f:
                log_content = f.read()
                if not log_content.strip():
                    raise AssertionError("Log file is empty")
            
            self.test_results["tests_passed"] += 1
            print("✅ Debug logger initialization test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Debug logger initialization: {e}")
            print(f"❌ Debug logger initialization test failed: {e}")
    
    def test_windows_detection_simulation(self):
        """Test Windows detection logic with mocked platform."""
        self.test_results["tests_run"] += 1
        
        try:
            # Mock Windows platform detection
            with patch('platform.system', return_value='Windows'):
                with patch('os.path.exists') as mock_exists:
                    # Simulate Z: drive detection
                    mock_exists.side_effect = lambda path: str(path).startswith('Z:')
                    
                    # Test detection logging
                    with debug_context("windows_detection_test") as debug_logger:
                        if debug_logger:
                            debug_logger.info("Simulating Windows detection",
                                            platform="Windows",
                                            network_drive="Z:",
                                            project_path=str(self.network_drive_path))
                        
                        log_info("Windows Smart Sync detection simulation",
                                platform="Windows",
                                detected=True,
                                network_path=str(self.network_drive_path))
            
            self.test_results["tests_passed"] += 1
            print("✅ Windows detection simulation test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Windows detection simulation: {e}")
            print(f"❌ Windows detection simulation test failed: {e}")
    
    def test_smart_sync_manager_logging(self):
        """Test Smart Sync manager initialization and operation logging."""
        self.test_results["tests_run"] += 1
        
        try:
            # Import Smart Sync components
            from src.smart_sync import SmartSyncManager
            
            # Create Smart Sync manager
            sync_manager = SmartSyncManager(
                self.network_drive_path,
                self.local_staging_path
            )
            
            # Test initial sync logging
            with debug_context("initial_sync_test") as debug_logger:
                if debug_logger:
                    debug_logger.info("Testing initial sync logging",
                                    network_path=str(self.network_drive_path),
                                    local_path=str(self.local_staging_path))
                
                # Simulate initial sync (this will be logged by SmartSyncManager)
                sync_success = sync_manager.initial_sync()
                
                log_info("Initial sync test completed",
                        success=sync_success,
                        network_path=str(self.network_drive_path),
                        local_path=str(self.local_staging_path))
            
            self.test_results["tests_passed"] += 1
            print("✅ Smart Sync manager logging test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Smart Sync manager logging: {e}")
            print(f"❌ Smart Sync manager logging test failed: {e}")
    
    def test_workflow_integration_logging(self):
        """Test workflow integration logging with mocked Project class."""
        self.test_results["tests_run"] += 1
        
        try:
            # Import core components
            from src.core import Project
            
            # Create project with Smart Sync enabled
            project = Project(self.network_drive_path, load_workflow=True)
            
            # Test workflow step logging
            with debug_context("workflow_step_test") as debug_logger:
                if debug_logger:
                    debug_logger.info("Testing workflow step integration",
                                    project_path=str(self.network_drive_path),
                                    smart_sync_enabled=project.smart_sync_manager is not None)
                
                # Test step execution logging (without actually running scripts)
                if project.workflow and project.workflow.steps:
                    step = project.workflow.steps[0]
                    step_id = step['id']
                    
                    log_info("Workflow step execution test",
                            step_id=step_id,
                            step_name=step.get('name', 'Unknown'),
                            smart_sync_enabled=project.smart_sync_manager is not None)
            
            self.test_results["tests_passed"] += 1
            print("✅ Workflow integration logging test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Workflow integration logging: {e}")
            print(f"❌ Workflow integration logging test failed: {e}")
    
    def test_container_launch_logging(self):
        """Test container launch logging simulation."""
        self.test_results["tests_run"] += 1
        
        try:
            # Mock container launch scenario
            with debug_context("container_launch_test") as debug_logger:
                if debug_logger:
                    debug_logger.info("Testing container launch logging",
                                    project_path=str(self.network_drive_path),
                                    docker_path=str(self.local_staging_path),
                                    smart_sync_enabled=True)
                
                # Simulate Smart Sync environment setup
                sync_env = {
                    "SMART_SYNC_ENABLED": "true",
                    "NETWORK_PROJECT_PATH": str(self.network_drive_path),
                    "LOCAL_PROJECT_PATH": str(self.local_staging_path),
                    "PROJECT_PATH": str(self.local_staging_path)
                }
                
                log_info("Container launch: Smart Sync enabled",
                        original_path=str(self.network_drive_path),
                        docker_path=str(self.local_staging_path),
                        sync_environment=sync_env)
                
                # Simulate container launch success
                log_info("Container launch completed successfully",
                        environment_variables=sync_env)
            
            self.test_results["tests_passed"] += 1
            print("✅ Container launch logging test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Container launch logging: {e}")
            print(f"❌ Container launch logging test failed: {e}")
    
    def test_error_scenario_logging(self):
        """Test error scenario logging and recovery tracking."""
        self.test_results["tests_run"] += 1
        
        try:
            # Test various error scenarios
            with debug_context("error_scenario_test") as debug_logger:
                
                # Test sync failure
                log_error("Simulated sync failure",
                         sync_type="incremental_sync_down",
                         error="Network connection timeout",
                         retry_count=3)
                
                # Test permission error
                log_error("Simulated permission error",
                         operation="file_copy",
                         source_path=str(self.network_drive_path / "test.txt"),
                         dest_path=str(self.local_staging_path / "test.txt"),
                         error="Permission denied")
                
                # Test recovery scenario
                log_info("Error recovery attempt",
                        recovery_action="retry_with_elevated_permissions",
                        attempt_number=2)
                
                if debug_logger:
                    debug_logger.error("Test error with context",
                                     error_type="validation_test",
                                     context="error_scenario_testing")
            
            self.test_results["tests_passed"] += 1
            print("✅ Error scenario logging test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Error scenario logging: {e}")
            print(f"❌ Error scenario logging test failed: {e}")
    
    def validate_log_file_structure(self):
        """Validate the structure and content of the debug log file."""
        self.test_results["tests_run"] += 1
        
        try:
            if not self.log_file.exists():
                raise AssertionError("Debug log file does not exist")
            
            # Use DebugTestValidator to analyze log file
            validator = DebugTestValidator(self.log_file)
            
            # Check for required log entries
            info_entries = validator.get_entries_by_level("INFO")
            debug_entries = validator.get_entries_by_level("DEBUG")
            error_entries = validator.get_entries_by_level("ERROR")
            
            if len(info_entries) == 0:
                raise AssertionError("No INFO level entries found")
            
            if len(debug_entries) == 0:
                raise AssertionError("No DEBUG level entries found")
            
            # Validate JSON structure
            for entry in validator.entries:
                required_fields = ["session_id", "timestamp", "level", "message"]
                for field in required_fields:
                    if field not in entry:
                        raise AssertionError(f"Missing required field: {field}")
            
            # Store debug entries for analysis
            self.test_results["debug_entries"] = validator.entries
            
            # Get performance data
            self.test_results["performance_data"] = validator.get_performance_data()
            
            self.test_results["tests_passed"] += 1
            print(f"✅ Log file structure validation passed ({len(validator.entries)} entries)")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Log file structure validation: {e}")
            print(f"❌ Log file structure validation failed: {e}")
    
    def test_performance_monitoring(self):
        """Test performance monitoring and timing functionality."""
        self.test_results["tests_run"] += 1
        
        try:
            # Test operation timing
            with debug_context("performance_test") as debug_logger:
                if debug_logger:
                    with debug_logger.operation_timer("test_sync_operation", 
                                                     files_count=100,
                                                     operation_type="incremental") as op_id:
                        import time
                        time.sleep(0.2)  # Simulate sync work
                    
                    with debug_logger.operation_timer("test_file_operation",
                                                     file_size="1MB",
                                                     operation_type="copy") as op_id:
                        time.sleep(0.1)  # Simulate file operation
            
            # Test performance logging functions
            log_info("Performance test: Sync operation completed",
                    duration=0.2,
                    files_processed=100,
                    throughput="500 files/sec")
            
            self.test_results["tests_passed"] += 1
            print("✅ Performance monitoring test passed")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["failures"].append(f"Performance monitoring: {e}")
            print(f"❌ Performance monitoring test failed: {e}")
    
    def generate_debug_report(self):
        """Generate a comprehensive debug validation report."""
        report = {
            "validation_summary": {
                "total_tests": self.test_results["tests_run"],
                "passed": self.test_results["tests_passed"],
                "failed": self.test_results["tests_failed"],
                "success_rate": (self.test_results["tests_passed"] / self.test_results["tests_run"] * 100) if self.test_results["tests_run"] > 0 else 0
            },
            "test_environment": {
                "platform": platform.system(),
                "python_version": sys.version,
                "test_directory": str(self.test_dir),
                "log_file": str(self.log_file),
                "debug_enabled": debug_enabled(),
                "debug_level": get_debug_level().value
            },
            "failures": self.test_results["failures"],
            "debug_log_analysis": {
                "total_entries": len(self.test_results["debug_entries"]),
                "entries_by_level": {},
                "performance_data": self.test_results["performance_data"]
            }
        }
        
        # Analyze debug entries by level
        for entry in self.test_results["debug_entries"]:
            level = entry.get("level", "UNKNOWN")
            if level not in report["debug_log_analysis"]["entries_by_level"]:
                report["debug_log_analysis"]["entries_by_level"][level] = 0
            report["debug_log_analysis"]["entries_by_level"][level] += 1
        
        # Save report
        report_file = self.test_dir / "debug_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 Debug Validation Report Generated: {report_file}")
        return report
    
    def cleanup(self):
        """Clean up test environment."""
        try:
            # Close debug logger
            close_debug_logger()
            
            # Clean up environment variables
            for var in ["SMART_SYNC_DEBUG", "SMART_SYNC_DEBUG_LEVEL", 
                       "SMART_SYNC_ENABLED", "NETWORK_PROJECT_PATH", "LOCAL_PROJECT_PATH"]:
                if var in os.environ:
                    del os.environ[var]
            
            print(f"🧹 Test environment cleaned up")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("\n🚀 Starting Smart Sync Debug Validation Tests")
        print("=" * 60)
        
        # Setup
        self.setup_windows_environment()
        self.create_test_project()
        
        # Run tests
        self.test_debug_logger_initialization()
        self.test_windows_detection_simulation()
        self.test_smart_sync_manager_logging()
        self.test_workflow_integration_logging()
        self.test_container_launch_logging()
        self.test_error_scenario_logging()
        self.test_performance_monitoring()
        self.validate_log_file_structure()
        
        # Generate report
        report = self.generate_debug_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {report['validation_summary']['total_tests']}")
        print(f"Passed: {report['validation_summary']['passed']}")
        print(f"Failed: {report['validation_summary']['failed']}")
        print(f"Success Rate: {report['validation_summary']['success_rate']:.1f}%")
        
        if report['failures']:
            print(f"\n❌ Failures:")
            for failure in report['failures']:
                print(f"  - {failure}")
        
        print(f"\n📝 Debug Log Entries: {report['debug_log_analysis']['total_entries']}")
        for level, count in report['debug_log_analysis']['entries_by_level'].items():
            print(f"  - {level}: {count}")
        
        print(f"\n📁 Test Files:")
        print(f"  - Log File: {self.log_file}")
        print(f"  - Report: {self.test_dir / 'debug_validation_report.json'}")
        
        # Cleanup
        self.cleanup()
        
        return report['validation_summary']['success_rate'] == 100.0


def main():
    """Main validation function."""
    print("🧪 Smart Sync Debug Validation - Windows Simulation")
    print("=" * 60)
    
    # Check if debug logging is enabled
    if not debug_enabled():
        print("⚠️ Debug logging is not enabled!")
        print("Please set environment variables:")
        print("  export SMART_SYNC_DEBUG=true")
        print("  export SMART_SYNC_DEBUG_LEVEL=DEBUG")
        print("\nOr run with:")
        print("  SMART_SYNC_DEBUG=true SMART_SYNC_DEBUG_LEVEL=DEBUG python debug_validation_windows_simulation.py")
        return False
    
    # Run validation
    validator = WindowsSimulationValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n🎉 All validation tests passed!")
        return True
    else:
        print("\n💥 Some validation tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)