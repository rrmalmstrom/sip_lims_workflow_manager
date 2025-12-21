#!/usr/bin/env python3
"""
Test the standalone Docker updater functionality
"""

import subprocess
import json

def test_docker_updater():
    """Test the Docker updater functionality"""
    print("🐳 Testing Docker Updater")
    print("=" * 50)
    
    # Test 1: Check Docker updates
    print("\n🔍 Test 1: Check Docker image updates")
    result = subprocess.run([
        "python3", "src/update_detector.py", 
        "--check-docker"
    ], capture_output=True, text=True)
    
    print(f"Exit code: {result.returncode}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    # Parse and validate JSON response
    try:
        data = json.loads(result.stdout)
        required_fields = ["update_available", "local_sha", "remote_sha", "reason"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print(f"✅ All required fields present")
            print(f"   - Update available: {data.get('update_available')}")
            print(f"   - Local SHA: {data.get('local_sha', 'None')}")
            print(f"   - Remote SHA: {data.get('remote_sha', 'None')}")
            print(f"   - Reason: {data.get('reason')}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
    
    # Test 2: Get Docker summary
    print("\n📊 Test 2: Get Docker update summary")
    result = subprocess.run([
        "python3", "src/update_detector.py", 
        "--summary"
    ], capture_output=True, text=True)
    
    print(f"Exit code: {result.returncode}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    # Parse and validate summary JSON
    try:
        data = json.loads(result.stdout)
        required_fields = ["timestamp", "docker", "any_updates_available"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required summary fields: {missing_fields}")
        else:
            print(f"✅ All required summary fields present")
            print(f"   - Timestamp: {data.get('timestamp')}")
            print(f"   - Any updates: {data.get('any_updates_available')}")
            
            # Check docker sub-object
            docker_data = data.get('docker', {})
            if 'update_available' in docker_data:
                print(f"   - Docker update available: {docker_data.get('update_available')}")
            else:
                print(f"❌ Docker sub-object missing update_available field")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid summary JSON response: {e}")
    
    # Test 3: Default behavior (should show summary)
    print("\n📋 Test 3: Default behavior (no arguments)")
    result = subprocess.run([
        "python3", "src/update_detector.py"
    ], capture_output=True, text=True)
    
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print("✅ Default behavior produces output")
        try:
            json.loads(result.stdout)
            print("✅ Default output is valid JSON")
        except json.JSONDecodeError:
            print("❌ Default output is not valid JSON")
    else:
        print("❌ No output from default behavior")
    
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    print("\n✅ Docker updater test completed")

if __name__ == "__main__":
    test_docker_updater()