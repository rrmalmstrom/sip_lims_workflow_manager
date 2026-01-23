#!/usr/bin/env python3
"""
Test Enhanced Debug Analyzer

This script tests the updated debug analysis scripts to ensure they properly
handle the new Smart Sync features: fail-fast behavior, three-factor validation,
and cleanup operations.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.debug_logger import SmartSyncDebugLogger, LogLevel
from debug_log_analyzer import SmartSyncLogAnalyzer


def generate_test_debug_log(log_file: Path):
    """Generate a comprehensive test debug log with new Smart Sync features."""
    print(f"🧪 Generating test debug log: {log_file}")
    
    # Initialize debug logger
    logger = SmartSyncDebugLogger(
        log_file=log_file,
        console_output=False,
        log_level=LogLevel.DEBUG
    )
    
    # Simulate Smart Sync detection
    logger.log_smart_sync_detection(
        project_path=Path("Z:/test_project"),
        detected=True,
        platform_name="Windows",
        network_drive="Z:",
        local_staging="C:/temp/sip_workflow/test_project"
    )
    
    # Simulate environment setup
    logger.log_environment_setup(
        network_path=Path("Z:/test_project"),
        local_path=Path("C:/temp/sip_workflow/test_project"),
        env_vars={
            "SMART_SYNC_ENABLED": "true",
            "NETWORK_PROJECT_PATH": "Z:/test_project",
            "LOCAL_PROJECT_PATH": "C:/temp/sip_workflow/test_project"
        },
        success=True
    )
    
    # Simulate sync operations
    logger.log_sync_operation(
        sync_type="initial_sync",
        direction="network_to_local",
        files_affected=25,
        duration=2.5,
        success=True,
        files_copied=25,
        total_size="15MB"
    )
    
    # Simulate sync patterns
    logger.log_sync_pattern(
        pattern_type="pre_step_sync",
        step_id="step_1",
        direction="network_to_local",
        success=True,
        duration=0.8,
        files_synced=3
    )
    
    # Simulate three-factor validation - SUCCESS case
    logger.log_three_factor_validation(
        step_id="step_1",
        exit_code=0,
        marker_file_exists=True,
        sync_success=True,
        overall_success=True,
        script_name="test_script.py",
        execution_time=5.2
    )
    
    # Simulate post-step sync
    logger.log_sync_pattern(
        pattern_type="post_step_sync",
        step_id="step_1",
        direction="local_to_network",
        success=True,
        duration=1.2,
        files_synced=5
    )
    
    # Simulate three-factor validation - PARTIAL FAILURE case
    logger.log_three_factor_validation(
        step_id="step_2",
        exit_code=0,
        marker_file_exists=False,  # Missing marker file
        sync_success=True,
        overall_success=False,
        script_name="failing_script.py",
        execution_time=3.1
    )
    
    # Simulate fail-fast trigger - Excel file locked
    logger.log_fail_fast_trigger(
        trigger_type="excel_file_locked",
        details={
            "file_path": "Z:/test_project/data/results.xlsx",
            "lock_owner": "DESKTOP-ABC123\\user",
            "retry_attempts": 3
        },
        recovery_attempted=True
    )
    
    # Simulate fail-fast trigger - Network disconnection
    logger.log_fail_fast_trigger(
        trigger_type="network_disconnection",
        details={
            "network_path": "Z:/test_project",
            "error_code": "ERROR_NETWORK_UNREACHABLE",
            "last_successful_operation": "pre_step_sync"
        },
        recovery_attempted=False
    )
    
    # Simulate cleanup operations
    logger.log_cleanup_operation(
        operation_type="temporary_files",
        target_path="C:/temp/sip_workflow/test_project/.temp",
        success=True,
        files_removed=12,
        errors_encountered=[],
        cleanup_duration=0.3
    )
    
    logger.log_cleanup_operation(
        operation_type="local_staging_directory",
        target_path="C:/temp/sip_workflow/test_project",
        success=True,
        files_removed=45,
        errors_encountered=[],
        cleanup_duration=1.8
    )
    
    # Simulate a failed cleanup
    logger.log_cleanup_operation(
        operation_type="orphaned_processes",
        target_path="docker_container_cleanup",
        success=False,
        files_removed=0,
        errors_encountered=["Container still running: sip_workflow_container"],
        cleanup_duration=0.1
    )
    
    # Simulate more sync operations for statistics
    for i in range(3, 6):
        logger.log_sync_pattern(
            pattern_type="pre_step_sync",
            step_id=f"step_{i}",
            direction="network_to_local",
            success=True,
            duration=0.5 + (i * 0.1),
            files_synced=2
        )
        
        logger.log_three_factor_validation(
            step_id=f"step_{i}",
            exit_code=0,
            marker_file_exists=True,
            sync_success=True,
            overall_success=True,
            script_name=f"script_{i}.py",
            execution_time=2.0 + i
        )
        
        logger.log_sync_pattern(
            pattern_type="post_step_sync",
            step_id=f"step_{i}",
            direction="local_to_network",
            success=True,
            duration=0.7 + (i * 0.1),
            files_synced=3
        )
    
    # Final sync
    logger.log_sync_operation(
        sync_type="final_sync",
        direction="local_to_network",
        files_affected=15,
        duration=1.8,
        success=True,
        files_copied=15,
        total_size="8MB"
    )
    
    # Close logger
    logger.close()
    print(f"✅ Test debug log generated with comprehensive Smart Sync data")


def test_enhanced_analyzer(log_file: Path):
    """Test the enhanced debug analyzer with the generated log."""
    print(f"\n🔍 Testing Enhanced Debug Analyzer")
    print("=" * 50)
    
    try:
        # Initialize analyzer
        analyzer = SmartSyncLogAnalyzer(log_file)
        
        # Run all analyses
        print("📊 Running performance analysis...")
        perf_results = analyzer.analyze_performance()
        
        print("🔍 Running error analysis...")
        error_results = analyzer.analyze_errors()
        
        print("🔄 Running Smart Sync operations analysis...")
        sync_results = analyzer.analyze_smart_sync_operations()
        
        print("⚡ Running fail-fast patterns analysis...")
        fail_fast_results = analyzer.analyze_fail_fast_patterns()
        
        print("🎯 Running three-factor validations analysis...")
        three_factor_results = analyzer.analyze_three_factor_validations()
        
        print("🧹 Running cleanup operations analysis...")
        cleanup_results = analyzer.analyze_cleanup_operations()
        
        print("📅 Running timeline analysis...")
        timeline_results = analyzer.generate_timeline_analysis()
        
        print("📋 Generating summary report...")
        summary_results = analyzer.generate_summary_report()
        
        # Print summary
        analyzer.print_summary()
        
        # Validate results
        print(f"\n✅ VALIDATION RESULTS")
        print("=" * 30)
        
        # Check Smart Sync operations
        assert len(sync_results['sync_operations']) > 0, "No sync operations found"
        assert len(sync_results['sync_patterns']) > 0, "No sync patterns found"
        print(f"✓ Found {len(sync_results['sync_operations'])} sync operations")
        print(f"✓ Found {len(sync_results['sync_patterns'])} sync patterns")
        
        # Check fail-fast analysis
        assert len(fail_fast_results['timeline']) > 0, "No fail-fast events found"
        assert fail_fast_results['total_events'] == 2, f"Expected 2 fail-fast events, got {fail_fast_results['total_events']}"
        assert fail_fast_results['recovery_attempts'] == 1, f"Expected 1 recovery attempt, got {fail_fast_results['recovery_attempts']}"
        print(f"✓ Found {fail_fast_results['total_events']} fail-fast events")
        print(f"✓ Recovery success rate: {fail_fast_results['recovery_success_rate']:.1f}%")
        
        # Check three-factor validation analysis
        assert len(three_factor_results['timeline']) > 0, "No three-factor validations found"
        assert three_factor_results['total_validations'] == 5, f"Expected 5 validations, got {three_factor_results['total_validations']}"
        assert three_factor_results['successful_validations'] == 4, f"Expected 4 successful validations, got {three_factor_results['successful_validations']}"
        print(f"✓ Found {three_factor_results['total_validations']} three-factor validations")
        print(f"✓ Three-factor success rate: {three_factor_results['success_rate']:.1f}%")
        
        # Check cleanup analysis
        assert len(cleanup_results['cleanup_timeline']) > 0, "No cleanup operations found"
        assert cleanup_results['total_operations'] == 3, f"Expected 3 cleanup operations, got {cleanup_results['total_operations']}"
        assert cleanup_results['successful_operations'] == 2, f"Expected 2 successful cleanups, got {cleanup_results['successful_operations']}"
        print(f"✓ Found {cleanup_results['total_operations']} cleanup operations")
        print(f"✓ Cleanup success rate: {cleanup_results['success_rate']:.1f}%")
        
        # Check enhanced Smart Sync metrics
        assert 'three_factor_success_rate' in sync_results, "Missing three-factor success rate"
        assert 'cleanup_success_rate' in sync_results, "Missing cleanup success rate"
        assert 'fail_fast_recovery_rate' in sync_results, "Missing fail-fast recovery rate"
        print(f"✓ Enhanced Smart Sync metrics present")
        
        # Export analysis for inspection
        output_file = analyzer.export_analysis(format='json')
        print(f"✓ Analysis exported to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_debug_logger_new_functions():
    """Test the new debug logger functions directly."""
    print(f"\n🧪 Testing New Debug Logger Functions")
    print("=" * 40)
    
    try:
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_log = Path(f.name)
        
        # Test logger initialization
        logger = SmartSyncDebugLogger(
            log_file=temp_log,
            console_output=False,
            log_level=LogLevel.DEBUG
        )
        
        # Test new logging functions
        logger.log_fail_fast_trigger(
            trigger_type="test_trigger",
            details={"test": "data"},
            recovery_attempted=True
        )
        
        logger.log_three_factor_validation(
            step_id="test_step",
            exit_code=0,
            marker_file_exists=True,
            sync_success=True,
            overall_success=True
        )
        
        logger.log_cleanup_operation(
            operation_type="test_cleanup",
            target_path="/test/path",
            success=True,
            files_removed=5
        )
        
        logger.log_sync_pattern(
            pattern_type="test_pattern",
            step_id="test_step",
            direction="test_direction",
            success=True,
            duration=1.0
        )
        
        logger.close()
        
        # Verify log file contains expected entries
        with open(temp_log, 'r') as f:
            log_content = f.read()
            
        assert 'Fail-fast triggered' in log_content, "Fail-fast logging not working"
        assert 'Three-factor validation' in log_content, "Three-factor logging not working"
        assert 'Cleanup successful' in log_content, "Cleanup logging not working"
        assert 'Sync pattern completed' in log_content, "Sync pattern logging not working"
        
        print("✅ All new debug logger functions working correctly")
        
        # Cleanup
        temp_log.unlink()
        return True
        
    except Exception as e:
        print(f"❌ Debug logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 Enhanced Debug Analyzer Test Suite")
    print("=" * 60)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory(prefix="smart_sync_debug_test_") as temp_dir:
        temp_dir = Path(temp_dir)
        log_file = temp_dir / "test_debug.log"
        
        # Test 1: Debug logger new functions
        test1_success = test_debug_logger_new_functions()
        
        # Test 2: Generate comprehensive test log
        generate_test_debug_log(log_file)
        
        # Test 3: Enhanced analyzer
        test2_success = test_enhanced_analyzer(log_file)
        
        # Summary
        print(f"\n🎯 TEST SUMMARY")
        print("=" * 30)
        print(f"Debug Logger Functions: {'✅ PASS' if test1_success else '❌ FAIL'}")
        print(f"Enhanced Analyzer: {'✅ PASS' if test2_success else '❌ FAIL'}")
        
        overall_success = test1_success and test2_success
        print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '💥 SOME TESTS FAILED'}")
        
        return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)