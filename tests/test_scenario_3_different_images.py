#!/usr/bin/env python3
"""
Test Scenario 3: Local and remote Docker images are different
This creates a controlled test where we simulate having different local vs remote images
"""

import sys
import subprocess
import json
sys.path.insert(0, '.')
from src.update_detector import UpdateDetector

def test_scenario_3():
    print("=== SCENARIO 3: TESTING DIFFERENT LOCAL VS REMOTE IMAGES ===")
    
    detector = UpdateDetector()
    tag = 'feature-sps-workflow-manager-generalization'
    
    print("\n1. First, let's see what we currently have...")
    
    # Check current local image
    local_digest = detector.get_local_docker_image_digest(tag)
    print(f"Current local digest: {local_digest[:20] if local_digest else 'None'}...")
    
    # Check remote image
    remote_digest = detector.get_remote_docker_image_digest(tag)
    print(f"Current remote digest: {remote_digest[:20] if remote_digest else 'None'}...")
    
    if local_digest and remote_digest:
        if local_digest == remote_digest:
            print("✅ Images currently match - we need to create a difference")
            
            print("\n2. Creating a different local image scenario...")
            print("   Strategy: Pull a different tag and retag it to simulate an older local image")
            
            # Try to pull the 'main' tag and retag it as our test tag
            print("   - Pulling main branch image...")
            pull_result = subprocess.run([
                'docker', 'pull', 'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main'
            ], capture_output=True, text=True)
            
            if pull_result.returncode == 0:
                print("   - Successfully pulled main image")
                
                # Remove the current local image
                print(f"   - Removing current local image: {tag}")
                subprocess.run([
                    'docker', 'rmi', f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'
                ], capture_output=True, text=True)
                
                # Retag main as our test tag to simulate an older local image
                print(f"   - Retagging main as {tag} to simulate older local image")
                retag_result = subprocess.run([
                    'docker', 'tag', 
                    'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main',
                    f'ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{tag}'
                ], capture_output=True, text=True)
                
                if retag_result.returncode == 0:
                    print("   ✅ Successfully created different local image")
                    
                    print("\n3. Testing update detection with different images...")
                    
                    # Test the update detection
                    result = detector.check_docker_image_update(tag=tag)
                    
                    print(f"\n=== SCENARIO 3 RESULTS ===")
                    print(f"Update available: {result.get('update_available')}")
                    print(f"Reason: {result.get('reason')}")
                    print(f"Local digest: {result.get('local_digest', 'None')[:20] if result.get('local_digest') else 'None'}...")
                    print(f"Remote digest: {result.get('remote_digest', 'None')[:20] if result.get('remote_digest') else 'None'}...")
                    
                    # Verify the digests are actually different
                    new_local_digest = detector.get_local_docker_image_digest(tag)
                    new_remote_digest = detector.get_remote_docker_image_digest(tag)
                    
                    print(f"\n=== DIGEST VERIFICATION ===")
                    print(f"Local digest:  {new_local_digest[:20] if new_local_digest else 'None'}...")
                    print(f"Remote digest: {new_remote_digest[:20] if new_remote_digest else 'None'}...")
                    print(f"Are different: {new_local_digest != new_remote_digest if new_local_digest and new_remote_digest else 'Cannot compare'}")
                    
                    if result.get('update_available') == True and 'differs' in result.get('reason', ''):
                        print("\n✅ SUCCESS: Scenario 3 works correctly!")
                        print("   - Detected that local and remote images are different")
                        print("   - Correctly identified update is needed")
                        return True
                    else:
                        print("\n❌ ISSUE: Scenario 3 not working as expected")
                        print(f"   Expected: update_available=True with 'differs' in reason")
                        print(f"   Got: update_available={result.get('update_available')}, reason={result.get('reason')}")
                        return False
                else:
                    print("   ❌ Failed to retag image")
                    return False
            else:
                print("   ❌ Failed to pull main image")
                print(f"   Error: {pull_result.stderr}")
                return False
        else:
            print("✅ Images are already different - perfect for testing!")
            
            print("\n2. Testing update detection with different images...")
            result = detector.check_docker_image_update(tag=tag)
            
            print(f"\n=== SCENARIO 3 RESULTS ===")
            print(f"Update available: {result.get('update_available')}")
            print(f"Reason: {result.get('reason')}")
            print(f"Local digest: {result.get('local_digest', 'None')[:20] if result.get('local_digest') else 'None'}...")
            print(f"Remote digest: {result.get('remote_digest', 'None')[:20] if result.get('remote_digest') else 'None'}...")
            
            if result.get('update_available') == True and 'differs' in result.get('reason', ''):
                print("\n✅ SUCCESS: Scenario 3 works correctly!")
                return True
            else:
                print("\n❌ ISSUE: Scenario 3 not working as expected")
                return False
    else:
        print("❌ Cannot test - missing local or remote image")
        return False

if __name__ == "__main__":
    success = test_scenario_3()
    print(f"\n=== FINAL RESULT ===")
    print(f"Scenario 3 test: {'PASSED' if success else 'FAILED'}")