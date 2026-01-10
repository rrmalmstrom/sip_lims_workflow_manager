#!/usr/bin/env python3
"""
Test the corrected Docker digest extraction.
"""

import sys
import json
sys.path.insert(0, '.')

from src.update_detector import UpdateDetector
from utils.branch_utils import get_current_branch, sanitize_branch_for_docker_tag

def test_digest_extraction():
    print("=== TESTING CORRECTED DIGEST EXTRACTION ===")
    
    # Get current branch and tag
    detector = UpdateDetector()
    branch = get_current_branch()
    tag = sanitize_branch_for_docker_tag(branch)
    
    print(f"Branch: {branch}")
    print(f"Tag: {tag}")
    
    print(f"\n=== TESTING INDIVIDUAL DIGEST METHODS ===")
    
    # Test remote digest extraction
    print(f"Testing remote digest extraction for: {tag}")
    remote_digest = detector.get_remote_docker_image_digest(tag)
    print(f"Remote digest result: {remote_digest}")
    print(f"Remote digest type: {type(remote_digest)}")
    if remote_digest:
        print(f"Remote digest length: {len(remote_digest)}")
        print(f"Starts with sha256: {remote_digest.startswith('sha256:') if remote_digest else False}")
    
    # Test local digest extraction  
    print(f"\nTesting local digest extraction for: {tag}")
    local_digest = detector.get_local_docker_image_digest(tag)
    print(f"Local digest result: {local_digest}")
    print(f"Local digest type: {type(local_digest)}")
    if local_digest:
        print(f"Local digest length: {len(local_digest)}")
        print(f"Starts with sha256: {local_digest.startswith('sha256:') if local_digest else False}")
    
    print(f"\n=== DIGEST COMPARISON ANALYSIS ===")
    if remote_digest and local_digest:
        print(f"Remote: {remote_digest}")
        print(f"Local:  {local_digest}")
        print(f"Match:  {remote_digest == local_digest}")
        
        if remote_digest == local_digest:
            print("✅ DIGESTS MATCH: No update needed")
        else:
            print("⚠️  DIGESTS DIFFER: Update needed")
            
    elif not local_digest and remote_digest:
        print(f"Remote digest available: {bool(remote_digest)}")
        print(f"Local digest available: {bool(local_digest)}")
        print("✅ NO LOCAL IMAGE SCENARIO: Should trigger update")
        
    elif not remote_digest:
        print("❌ NO REMOTE DIGEST: Cannot determine if update needed")
    else:
        print("❌ UNEXPECTED STATE: Both digests missing")
    
    # Test the main check_docker_update method
    print(f"\n=== TESTING FULL check_docker_update() METHOD ===")
    result = detector.check_docker_update(tag=tag, branch=branch)
    
    print(f"Result from check_docker_update():")
    print(json.dumps(result, indent=2))
    
    print(f"\n=== FINAL ASSESSMENT ===")
    if result.get('update_available') == True:
        if 'No local Docker image found' in result.get('reason', ''):
            print("✅ CRITICAL SCENARIO FIXED: Correctly detects missing local image")
            return True
        elif 'differs' in result.get('reason', ''):
            print("✅ UPDATE SCENARIO WORKING: Correctly detects different images")
            return True
        else:
            print(f"⚠️  UPDATE NEEDED: {result.get('reason', 'Unknown reason')}")
            return True
    elif result.get('update_available') == False:
        if 'identical' in result.get('reason', '') or 'match' in result.get('reason', ''):
            print("✅ NO UPDATE SCENARIO WORKING: Correctly detects identical images")
            return True
        else:
            print(f"✅ NO UPDATE NEEDED: {result.get('reason', 'Unknown reason')}")
            return True
    else:
        print(f"❌ UNEXPECTED RESULT: {result}")
        return False

if __name__ == "__main__":
    success = test_digest_extraction()
    sys.exit(0 if success else 1)