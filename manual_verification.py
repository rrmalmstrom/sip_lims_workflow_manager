#!/usr/bin/env python3
"""
Manual verification script for UpdateManager functionality.
Run this script to test various scenarios and verify the UpdateManager works correctly.
"""

import json
import os
import shutil
import sys
from src.update_manager import UpdateManager


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")


def backup_config():
    """Backup the original config file."""
    if os.path.exists("config/version.json"):
        shutil.copy("config/version.json", "config/version.json.backup")
        return True
    return False


def restore_config():
    """Restore the original config file."""
    if os.path.exists("config/version.json.backup"):
        shutil.move("config/version.json.backup", "config/version.json")


def create_test_config(version):
    """Create a test config with specified version."""
    config = {"version": version}
    with open("config/version.json", 'w') as f:
        json.dump(config, f, indent=2)


def test_basic_functionality():
    """Test basic UpdateManager functionality."""
    print_section("1. Basic Functionality Test")
    
    # Restore original config (9.9.9)
    restore_config()
    
    um = UpdateManager()
    result = um.check_for_updates()
    
    print(f"Local version: {result.get('local_version')}")
    print(f"Remote version: {result.get('remote_version')}")
    print(f"Update available: {result.get('update_available')}")
    print(f"Error: {result.get('error')}")
    
    if result.get('local_version') == "9.9.9" and result.get('update_available'):
        print("✅ PASS: Version 9.9.9 correctly shows update available")
    else:
        print("❌ FAIL: Version 9.9.9 should show update available")


def test_version_scenarios():
    """Test different version scenarios."""
    print_section("2. Version Comparison Tests")
    
    test_cases = [
        ("2.0.0", "Should show NO update (local > remote)"),
        ("1.0.0", "Should show NO update (local = remote)"),
        ("0.9.0", "Should show UPDATE available (local < remote)")
    ]
    
    for version, expected in test_cases:
        print(f"\nTesting local version: {version}")
        print(f"Expected: {expected}")
        
        create_test_config(version)
        um = UpdateManager()
        result = um.check_for_updates()
        
        if result.get('error'):
            print(f"❌ ERROR: {result.get('error')}")
        else:
            update_status = "UPDATE available" if result.get('update_available') else "NO update"
            print(f"Result: {update_status}")
            
            # Validate results
            if version == "2.0.0" and not result.get('update_available'):
                print("✅ PASS")
            elif version == "1.0.0" and not result.get('update_available'):
                print("✅ PASS")
            elif version == "0.9.0" and result.get('update_available'):
                print("✅ PASS")
            else:
                print("❌ FAIL")


def test_error_handling():
    """Test error handling scenarios."""
    print_section("3. Error Handling Tests")
    
    # Test invalid JSON
    print("\nTesting invalid JSON:")
    with open("config/version.json", 'w') as f:
        f.write("invalid json content")
    
    um = UpdateManager()
    result = um.check_for_updates()
    
    if result.get('error') == "Could not read local version":
        print("✅ PASS: Invalid JSON handled correctly")
    else:
        print("❌ FAIL: Invalid JSON not handled correctly")
    
    # Test missing file
    print("\nTesting missing config file:")
    if os.path.exists("config/version.json"):
        os.remove("config/version.json")
    
    result = um.check_for_updates()
    
    if result.get('error') == "Could not read local version":
        print("✅ PASS: Missing file handled correctly")
    else:
        print("❌ FAIL: Missing file not handled correctly")


def test_individual_methods():
    """Test individual methods."""
    print_section("4. Individual Method Tests")
    
    # Restore config for testing
    restore_config()
    um = UpdateManager()
    
    print("Testing get_local_version():")
    local_version = um.get_local_version()
    print(f"Local version: {local_version}")
    
    print("\nTesting get_remote_version():")
    remote_version = um.get_remote_version()
    print(f"Remote version: {remote_version}")
    
    if local_version and remote_version:
        print("\nTesting compare_versions():")
        comparison = um.compare_versions(local_version, remote_version)
        print(f"compare_versions('{local_version}', '{remote_version}') = {comparison}")
        
        if local_version == "9.9.9" and comparison:
            print("✅ PASS: Version 9.9.9 comparison works correctly")
        else:
            print("❌ FAIL: Version comparison issue")


def test_google_drive_url():
    """Test Google Drive URL directly."""
    print_section("5. Google Drive URL Test")
    
    try:
        import requests
        url = "https://drive.google.com/uc?id=1pRsUbaKoieuInH67ghExSZw7p2I64-FQ&export=download"
        
        print(f"Testing URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON Response: {json.dumps(data, indent=2)}")
                
                if 'latest_version' in data:
                    print("✅ PASS: Google Drive URL returns valid JSON with latest_version")
                else:
                    print("❌ FAIL: JSON missing latest_version key")
                    
            except json.JSONDecodeError:
                print("❌ FAIL: Response is not valid JSON")
                print(f"Raw response: {response.text[:200]}...")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")


def main():
    """Run all verification tests."""
    print("UpdateManager Manual Verification Script")
    print("This script will test various scenarios to verify functionality.")
    
    # Backup original config
    config_backed_up = backup_config()
    if not config_backed_up:
        print("Warning: No config/version.json found to backup")
    
    try:
        # Run all tests
        test_basic_functionality()
        test_version_scenarios()
        test_error_handling()
        test_individual_methods()
        test_google_drive_url()
        
        print_section("Verification Complete")
        print("All tests completed. Review the results above.")
        print("✅ = Test passed")
        print("❌ = Test failed")
        
    finally:
        # Always restore original config
        restore_config()
        print("\nOriginal config restored.")


if __name__ == "__main__":
    main()