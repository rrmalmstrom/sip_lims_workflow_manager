#!/usr/bin/env python3
"""
Test script for decision_third_attempt.py

This test verifies that the decision script correctly updates workflow_state.json
and creates success markers based on user choices.
"""

import json
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path

def test_decision_script_yes():
    """Test decision script with YES choice"""
    print("Testing decision script with YES choice...")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create initial workflow state
        initial_state = {
            "setup_plates": "completed",
            "second_fa_analysis": "completed",
            "rework_second_attempt": "pending",
            "third_fa_analysis": "pending",
            "conclude_fa_analysis": "pending",
            "_completion_order": ["setup_plates", "second_fa_analysis"]
        }
        
        state_file = temp_path / "workflow_state.json"
        with open(state_file, 'w') as f:
            json.dump(initial_state, f, indent=2)
        
        # Create .workflow_status directory
        status_dir = temp_path / ".workflow_status"
        status_dir.mkdir()
        
        # Run decision script with YES input
        script_path = Path("/Users/RRMalmstrom/Desktop/sip_scripts_dev/decision_third_attempt.py")
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=temp_path,
            text=True
        )
        
        stdout, stderr = process.communicate(input="Y\n")
        
        print("Script output:")
        print(stdout)
        if stderr:
            print("Script errors:")
            print(stderr)
        
        # Verify workflow state was updated correctly
        with open(state_file, 'r') as f:
            updated_state = json.load(f)
        
        expected_state = {
            "setup_plates": "completed",
            "second_fa_analysis": "completed", 
            "rework_second_attempt": "pending",  # Should be enabled
            "third_fa_analysis": "pending",      # Should be enabled
            "conclude_fa_analysis": "pending",
            "_completion_order": ["setup_plates", "second_fa_analysis"]
        }
        
        assert updated_state == expected_state, f"State mismatch. Expected: {expected_state}, Got: {updated_state}"
        
        # Verify success marker was created
        success_file = status_dir / "decision_third_attempt.success"
        assert success_file.exists(), "Success marker was not created"
        
        print("✅ YES choice test passed!")

def test_decision_script_no():
    """Test decision script with NO choice"""
    print("Testing decision script with NO choice...")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create initial workflow state
        initial_state = {
            "setup_plates": "completed",
            "second_fa_analysis": "completed",
            "rework_second_attempt": "pending",
            "third_fa_analysis": "pending", 
            "conclude_fa_analysis": "pending",
            "_completion_order": ["setup_plates", "second_fa_analysis"]
        }
        
        state_file = temp_path / "workflow_state.json"
        with open(state_file, 'w') as f:
            json.dump(initial_state, f, indent=2)
        
        # Create .workflow_status directory
        status_dir = temp_path / ".workflow_status"
        status_dir.mkdir()
        
        # Run decision script with NO input
        script_path = Path("/Users/RRMalmstrom/Desktop/sip_scripts_dev/decision_third_attempt.py")
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=temp_path,
            text=True
        )
        
        stdout, stderr = process.communicate(input="N\n")
        
        print("Script output:")
        print(stdout)
        if stderr:
            print("Script errors:")
            print(stderr)
        
        # Verify workflow state was updated correctly
        with open(state_file, 'r') as f:
            updated_state = json.load(f)
        
        expected_state = {
            "setup_plates": "completed",
            "second_fa_analysis": "completed",
            "rework_second_attempt": "skipped",     # Should be skipped
            "third_fa_analysis": "skipped",         # Should be skipped
            "conclude_fa_analysis": "pending",      # Should be enabled
            "_completion_order": ["setup_plates", "second_fa_analysis"]
        }
        
        assert updated_state == expected_state, f"State mismatch. Expected: {expected_state}, Got: {updated_state}"
        
        # Verify success marker was created
        success_file = status_dir / "decision_third_attempt.success"
        assert success_file.exists(), "Success marker was not created"
        
        print("✅ NO choice test passed!")

def main():
    """Run all tests"""
    print("Running decision script tests...\n")
    
    try:
        test_decision_script_yes()
        print()
        test_decision_script_no()
        print()
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()