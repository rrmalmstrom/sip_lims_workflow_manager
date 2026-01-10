#!/usr/bin/env python3
"""
Test the critical scenario where no local Docker image exists.
This simulates the exact failing scenario that was reported.
"""

import sys
import json
import subprocess
sys.path.insert(0, '.')

from src.update_detector import UpdateDetector
from utils.branch_utils import get_current_branch, sanitize_branch_for_docker_tag

def test_no_local_image_scenario():
    print("=== TESTING CRITICAL SCENARIO: NO LOCAL IMAGE ===")
    
    # Get current branch and tag
    detector = UpdateDetector()
    branch = get_current_branch()
    tag = sanitize_branch_for_docker_tag(branch)
    
    print(f"Branch: {branch}")
    print(f"Tag: {tag}")
    
    # First, remove the local image to simulate the critical scenario
    print(f"\n=== REMOVING LOCAL IMAGE TO SIMULATE CRITICAL SCENARIO ===")
    remove_result = subprocess.run(
        ['docker', 'rmi', f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'],
        capture_output=True,
        text=True
    )
    
    if remove_result.returncode == 0:
        print("✅ Local image removed successfully")
    else:
        print(f"⚠️  Image removal result: {remove_result.stderr}")
        print("   (This is expected if image was already missing)")
    
    # Verify no local image exists
    print(f"\n=== VERIFYING NO LOCAL IMAGE EXISTS ===")
    check_result = subprocess.run(
        ['docker', 'inspect', f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'],
        capture_output=True,
        text=True
    )
    
    if check_result.returncode != 0:
        print("✅ Confirmed: No local image exists")
    else:
        print("❌ ERROR: Local image still exists!")
        return False
    
    # Test individual digest methods
    print(f"\n=== TESTING DIGEST METHODS WITH NO LOCAL IMAGE ===")
    
    local_digest = detector.get_local_docker_image_digest(tag)
    print(f"Local digest result: {local_digest}")
    
    remote_digest = detector.get_remote_docker_image_digest(tag)
    print(f"Remote digest result: {remote_digest}")
    print(f"Remote digest valid: {bool(remote_digest and remote_digest.startswith('sha256:'))}")
    
    # Test the main check_docker_update method
    print(f"\n=== TESTING check_docker_update() WITH NO LOCAL IMAGE ===")
    result = detector.check_docker_update(tag=tag, branch=branch)
    
    print(f"Result from check_docker_update():")
    print(json.dumps(result, indent=2))
    
    print(f"\n=== CRITICAL SCENARIO ASSESSMENT ===")
    
    # Check if the critical scenario is properly detected
    if result.get('update_available') == True:
        reason = result.get('reason', '')
        if 'No local Docker image found' in reason:
            print("✅ CRITICAL SCENARIO FIXED: Correctly detects missing local image")
            print("   - update_available: True")
            print("   - reason: Contains 'No local Docker image found'")
            return True
        elif 'differs' in reason or 'different' in reason:
            print("✅ UPDATE SCENARIO WORKING: Correctly detects need for update")
            print(f"   - reason: {reason}")
            return True
        else:
            print(f"⚠️  UPDATE NEEDED BUT UNEXPECTED REASON: {reason}")
            return True
    else:
        print("❌ CRITICAL SCENARIO STILL BROKEN:")
        print(f"   - update_available: {result.get('update_available')}")
        print(f"   - reason: {result.get('reason')}")
        print("   - Expected: update_available should be True when no local image exists")
        return False

if __name__ == "__main__":
    success = test_no_local_image_scenario()
    sys.exit(0 if success else 1)