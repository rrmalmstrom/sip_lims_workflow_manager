#!/usr/bin/env python3
"""
Comprehensive validation test for the Docker update detection fix
Tests all scenarios and validates the order of operations fix
"""

import sys
import subprocess
import json
sys.path.insert(0, '.')
from src.update_detector import UpdateDetector

def test_comprehensive_validation():
    print("=== COMPREHENSIVE DOCKER UPDATE DETECTION VALIDATION ===")
    print("Testing all scenarios to ensure the fix works correctly\n")
    
    detector = UpdateDetector()
    tag = 'feature-sps-workflow-manager-generalization'
    branch = 'feature-sps-workflow-manager-generalization'
    
    # Test results tracking
    results = {
        'scenario_1_no_local': False,
        'scenario_2_images_match': False, 
        'scenario_3_images_differ': False,
        'order_of_operations': False
    }
    
    print("=" * 60)
    print("SCENARIO 1: No local Docker image exists")
    print("=" * 60)
    
    # Remove local image to test scenario 1
    print("1. Removing local image to simulate 'no local image' scenario...")
    subprocess.run(['docker', 'rmi', f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'], 
                   capture_output=True, text=True)
    
    # Test with no local image
    result1 = detector.check_docker_image_update(tag=tag, branch=branch)
    print(f"   Update available: {result1.get('update_available')}")
    print(f"   Reason: {result1.get('reason')}")
    
    if result1.get('update_available') == True and 'No local Docker image found' in result1.get('reason', ''):
        print("   ✅ SCENARIO 1: PASSED - Correctly detects missing local image")
        results['scenario_1_no_local'] = True
    else:
        print("   ❌ SCENARIO 1: FAILED - Does not detect missing local image correctly")
    
    print("\n" + "=" * 60)
    print("SCENARIO 2: Local and remote images match")
    print("=" * 60)
    
    # Pull image to test scenario 2
    print("2. Pulling remote image to test 'images match' scenario...")
    pull_result = subprocess.run(['docker', 'pull', f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'], 
                                capture_output=True, text=True)
    
    if pull_result.returncode == 0:
        print("   Successfully pulled remote image")
        
        # Test with matching images
        result2 = detector.check_docker_image_update(tag=tag, branch=branch)
        print(f"   Update available: {result2.get('update_available')}")
        print(f"   Reason: {result2.get('reason')}")
        
        if result2.get('update_available') == False and 'identical' in result2.get('reason', ''):
            print("   ✅ SCENARIO 2: PASSED - Correctly detects matching images")
            results['scenario_2_images_match'] = True
        else:
            print("   ❌ SCENARIO 2: FAILED - Does not detect matching images correctly")
    else:
        print("   ❌ Failed to pull remote image for testing")
    
    print("\n" + "=" * 60)
    print("SCENARIO 3: Local and remote images differ")
    print("=" * 60)
    
    # Create different local image for scenario 3
    print("3. Creating different local image to test 'images differ' scenario...")
    
    # Pull main branch and retag it
    main_pull = subprocess.run(['docker', 'pull', 'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main'], 
                              capture_output=True, text=True)
    
    if main_pull.returncode == 0:
        # Remove current local image
        subprocess.run(['docker', 'rmi', f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'], 
                      capture_output=True, text=True)
        
        # Retag main as our test tag
        retag_result = subprocess.run([
            'docker', 'tag', 
            'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main',
            f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'
        ], capture_output=True, text=True)
        
        if retag_result.returncode == 0:
            print("   Successfully created different local image")
            
            # Test with different images
            result3 = detector.check_docker_image_update(tag=tag, branch=branch)
            print(f"   Update available: {result3.get('update_available')}")
            print(f"   Reason: {result3.get('reason')}")
            
            if result3.get('update_available') == True and 'differs' in result3.get('reason', ''):
                print("   ✅ SCENARIO 3: PASSED - Correctly detects different images")
                results['scenario_3_images_differ'] = True
            else:
                print("   ❌ SCENARIO 3: FAILED - Does not detect different images correctly")
        else:
            print("   ❌ Failed to retag image for testing")
    else:
        print("   ❌ Failed to pull main image for testing")
    
    print("\n" + "=" * 60)
    print("ORDER OF OPERATIONS: Testing fatal sync check placement")
    print("=" * 60)
    
    # Test that fatal sync checker runs before updates
    print("4. Testing that fatal sync error check runs BEFORE updates...")
    
    # Read the run.mac.command file to verify the order
    try:
        with open('run.mac.command', 'r') as f:
            content = f.read()
        
        # Find the production_auto_update function
        lines = content.split('\n')
        production_start = -1
        fatal_check_line = -1
        repo_update_line = -1
        docker_update_line = -1
        
        for i, line in enumerate(lines):
            if 'production_auto_update()' in line:
                production_start = i
            elif production_start > -1 and 'fatal_sync_checker.py' in line:
                fatal_check_line = i
            elif production_start > -1 and 'check_workflow_manager_updates' in line:
                repo_update_line = i
            elif production_start > -1 and 'check_docker_updates' in line:
                docker_update_line = i
        
        if (fatal_check_line > -1 and repo_update_line > -1 and docker_update_line > -1 and
            fatal_check_line < repo_update_line and fatal_check_line < docker_update_line):
            print("   ✅ ORDER OF OPERATIONS: CORRECT")
            print(f"      Fatal sync check at line {fatal_check_line + 1}")
            print(f"      Repository update at line {repo_update_line + 1}")
            print(f"      Docker update at line {docker_update_line + 1}")
            results['order_of_operations'] = True
        else:
            print("   ❌ ORDER OF OPERATIONS: INCORRECT")
            print(f"      Fatal sync check at line {fatal_check_line + 1 if fatal_check_line > -1 else 'NOT FOUND'}")
            print(f"      Repository update at line {repo_update_line + 1 if repo_update_line > -1 else 'NOT FOUND'}")
            print(f"      Docker update at line {docker_update_line + 1 if docker_update_line > -1 else 'NOT FOUND'}")
    
    except Exception as e:
        print(f"   ❌ Failed to verify order of operations: {e}")
    
    print("\n" + "=" * 60)
    print("FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Docker update detection is fully fixed!")
        print("   ✅ Critical Docker update detection issue resolved")
        print("   ✅ All scenarios working correctly")
        print("   ✅ Order of operations fixed")
        print("   ✅ Core automatic update functionality restored")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) still failing - needs investigation")
        return False

if __name__ == "__main__":
    success = test_comprehensive_validation()
    exit(0 if success else 1)