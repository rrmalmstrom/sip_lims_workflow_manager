#!/usr/bin/env python3
"""
Test the Docker update detection fix.
This simulates the exact call that run.mac.command makes.
"""

import sys
import json
sys.path.insert(0, '.')

from src.update_detector import UpdateDetector
from utils.branch_utils import get_current_branch, sanitize_branch_for_docker_tag

def test_docker_update_detection():
    print("=== TESTING DOCKER UPDATE DETECTION FIX ===")
    
    # Simulate the EXACT call that run.mac.command makes
    detector = UpdateDetector()
    branch = get_current_branch()
    tag = sanitize_branch_for_docker_tag(branch)
    
    print(f"Branch: {branch}")
    print(f"Tag: {tag}")
    
    # This is the EXACT call that run.mac.command makes on line 77
    result = detector.check_docker_update(tag=tag, branch=branch)
    
    print(f"\n=== RESULT FROM check_docker_update() ===")
    print(json.dumps(result, indent=2))
    
    # Test the critical scenarios
    print(f"\n=== SCENARIO ANALYSIS ===")
    
    if result.get('update_available') == True and 'No local Docker image found' in result.get('reason', ''):
        print("✅ CRITICAL SCENARIO FIXED: Correctly detects missing local image")
        return True
    elif result.get('update_available') == False and 'identical' in result.get('reason', ''):
        print("✅ NORMAL SCENARIO WORKING: Correctly detects identical images")
        return True
    elif result.get('update_available') == True and 'differs' in result.get('reason', ''):
        print("✅ UPDATE SCENARIO WORKING: Correctly detects different images")
        return True
    else:
        print("❌ ISSUE: Unexpected result")
        print(f"   update_available: {result.get('update_available')}")
        print(f"   reason: {result.get('reason')}")
        return False

if __name__ == "__main__":
    success = test_docker_update_detection()
    sys.exit(0 if success else 1)