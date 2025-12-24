#!/usr/bin/env python3
"""
Test script to validate Windows batch logic on Mac
This simulates the key parts of the Windows batch utilities to ensure they work correctly
"""

import os
import sys
import subprocess
from pathlib import Path

def test_git_repository():
    """Test Git repository validation"""
    print("Testing Git repository validation...")
    try:
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True, check=True)
        print("✅ Git repository validated")
        return True
    except subprocess.CalledProcessError:
        print("❌ Not in a Git repository")
        return False

def test_python_utilities():
    """Test Python utilities import and execution"""
    print("Testing Python utilities...")
    
    # Add current directory to Python path
    sys.path.insert(0, '.')
    
    try:
        from utils.branch_utils import (
            get_current_branch,
            get_docker_tag_for_current_branch,
            get_local_image_name_for_current_branch,
            get_remote_image_name_for_current_branch
        )
        
        # Test each function
        current_branch = get_current_branch()
        print(f"✅ Current branch: {current_branch}")
        
        docker_tag = get_docker_tag_for_current_branch()
        print(f"✅ Docker tag: {docker_tag}")
        
        local_image = get_local_image_name_for_current_branch()
        print(f"✅ Local image: {local_image}")
        
        remote_image = get_remote_image_name_for_current_branch()
        print(f"✅ Remote image: {remote_image}")
        
        return {
            'CURRENT_BRANCH': docker_tag,
            'LOCAL_IMAGE_NAME': local_image,
            'REMOTE_IMAGE_NAME': remote_image
        }
        
    except Exception as e:
        print(f"❌ Python utilities failed: {e}")
        return None

def test_fallback_logic():
    """Test fallback logic using git commands"""
    print("Testing fallback logic...")
    
    try:
        # Get branch name using git
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
        
        # Simple sanitization (mimicking Windows batch logic)
        sanitized = branch.replace(' ', '-').replace('/', '-').replace('\\', '-')
        
        # Generate fallback image names
        local_image = f"sip-lims-workflow-manager:{sanitized}"
        remote_image = f"ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{sanitized}"
        
        print(f"✅ Fallback branch: {branch}")
        print(f"✅ Fallback sanitized: {sanitized}")
        print(f"✅ Fallback local image: {local_image}")
        print(f"✅ Fallback remote image: {remote_image}")
        
        return {
            'CURRENT_BRANCH': sanitized,
            'LOCAL_IMAGE_NAME': local_image,
            'REMOTE_IMAGE_NAME': remote_image
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Fallback logic failed: {e}")
        return None

def simulate_windows_batch_utilities():
    """Simulate the complete Windows batch utilities logic"""
    print("=" * 60)
    print("SIMULATING WINDOWS BATCH UTILITIES LOGIC")
    print("=" * 60)
    
    # Step 1: Validate Git repository
    if not test_git_repository():
        return False
    
    print()
    
    # Step 2: Try Python utilities
    python_result = test_python_utilities()
    
    if python_result:
        print("\n✅ Python utilities succeeded - using Python results")
        return python_result
    
    print("\n⚠️  Python utilities failed - trying fallback")
    
    # Step 3: Try fallback logic
    fallback_result = test_fallback_logic()
    
    if fallback_result:
        print("\n✅ Fallback logic succeeded - using fallback results")
        return fallback_result
    
    print("\n❌ All methods failed")
    return False

def test_docker_compose_variables(variables):
    """Test that the variables would work with docker-compose"""
    print("\n" + "=" * 60)
    print("TESTING DOCKER-COMPOSE COMPATIBILITY")
    print("=" * 60)
    
    required_vars = ['CURRENT_BRANCH', 'LOCAL_IMAGE_NAME', 'REMOTE_IMAGE_NAME']
    
    for var in required_vars:
        if var in variables and variables[var]:
            print(f"✅ {var}: {variables[var]}")
        else:
            print(f"❌ {var}: Missing or empty")
            return False
    
    # Test that docker-compose.yml would work with these variables
    print(f"\n📋 Docker-compose would use:")
    print(f"   DOCKER_IMAGE: {variables['REMOTE_IMAGE_NAME']}")
    print(f"   Image tag: {variables['CURRENT_BRANCH']}")
    
    return True

def main():
    """Main test function"""
    print("Windows Batch Logic Test")
    print("Testing on:", sys.platform)
    print("Working directory:", os.getcwd())
    print()
    
    # Simulate the Windows batch utilities
    result = simulate_windows_batch_utilities()
    
    if not result:
        print("\n❌ OVERALL TEST FAILED")
        return 1
    
    # Test docker-compose compatibility
    if not test_docker_compose_variables(result):
        print("\n❌ DOCKER-COMPOSE COMPATIBILITY FAILED")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("The Windows batch logic should work correctly!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())