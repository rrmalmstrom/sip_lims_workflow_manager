#!/usr/bin/env python3
"""
Test the new scripts_updater.py functionality
"""

import tempfile
import subprocess
import os
import sys
from pathlib import Path

def test_scripts_updater():
    """Test the scripts updater functionality"""
    print("🧪 Testing Scripts Updater")
    print("=" * 50)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory(prefix="scripts_test_") as temp_dir:
        test_scripts_dir = os.path.join(temp_dir, "test_scripts")
        
        print(f"📁 Test directory: {test_scripts_dir}")
        
        # Test 1: Check scripts when directory doesn't exist
        print("\n🔍 Test 1: Check scripts when directory doesn't exist")
        result = subprocess.run([
            "python3", "src/scripts_updater.py", 
            "--check-scripts", 
            "--scripts-dir", test_scripts_dir,
            "--branch", "main"
        ], capture_output=True, text=True)
        
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Test 2: Update/clone scripts
        print("\n📥 Test 2: Clone scripts repository")
        result = subprocess.run([
            "python3", "src/scripts_updater.py", 
            "--update-scripts", 
            "--scripts-dir", test_scripts_dir,
            "--branch", "main"
        ], capture_output=True, text=True)
        
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Test 3: Check if directory was created and is a git repo
        print("\n📋 Test 3: Verify git repository was created")
        scripts_path = Path(test_scripts_dir)
        git_dir = scripts_path / ".git"
        
        if scripts_path.exists():
            print(f"✅ Scripts directory exists: {scripts_path}")
        else:
            print(f"❌ Scripts directory missing: {scripts_path}")
            
        if git_dir.exists():
            print(f"✅ Git repository created: {git_dir}")
        else:
            print(f"❌ Git repository missing: {git_dir}")
        
        # Test 4: Check scripts again (should be up to date)
        print("\n🔍 Test 4: Check scripts when up to date")
        result = subprocess.run([
            "python3", "src/scripts_updater.py", 
            "--check-scripts", 
            "--scripts-dir", test_scripts_dir,
            "--branch", "main"
        ], capture_output=True, text=True)
        
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Test 5: Get summary
        print("\n📊 Test 5: Get scripts summary")
        result = subprocess.run([
            "python3", "src/scripts_updater.py", 
            "--summary", 
            "--scripts-dir", test_scripts_dir,
            "--branch", "main"
        ], capture_output=True, text=True)
        
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    
    print("\n✅ Scripts updater test completed")

if __name__ == "__main__":
    test_scripts_updater()