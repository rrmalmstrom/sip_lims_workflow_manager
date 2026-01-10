#!/usr/bin/env python3
"""
Fatal Sync Error Checker for Docker Images
Checks for repository/Docker image sync issues and exits with fatal error if found.
"""

import sys
import json
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.update_detector import UpdateDetector
from utils.branch_utils import get_current_branch, sanitize_branch_for_docker_tag

def check_fatal_sync_errors():
    """Check for fatal sync errors and exit if found."""
    try:
        detector = UpdateDetector()
        branch = get_current_branch()
        tag = sanitize_branch_for_docker_tag(branch)
        
        result = detector.check_docker_update(tag=tag, branch=branch)
        
        # Check for fatal sync error
        if result.get('fatal_sync_error', False):
            print("🚨 FATAL SYNC ERROR DETECTED 🚨")
            print("")
            print(f"❌ {result.get('error', 'Unknown fatal error')}")
            print(f"⚠️  {result.get('sync_warning', 'Sync issue detected')}")
            print(f"💥 {result.get('reason', 'Manual intervention required')}")
            print("")
            print("🛑 STOPPING EXECUTION - CANNOT CONTINUE")
            print("📞 Contact the development team to resolve this issue")
            print("")
            sys.exit(1)
        
        # Check for other errors that should be fatal (only if fatal_sync_error is not already True)
        elif result.get('error') and 'FATAL' in result.get('error', ''):
            print("🚨 FATAL ERROR DETECTED 🚨")
            print("")
            print(f"❌ {result.get('error')}")
            if result.get('reason'):
                print(f"💥 {result.get('reason')}")
            print("")
            print("🛑 STOPPING EXECUTION - CANNOT CONTINUE")
            sys.exit(1)
        
        # If we get here, no fatal errors detected
        print("✅ No fatal sync errors detected - continuing...")
        return 0
        
    except Exception as e:
        print(f"❌ ERROR: Failed to check for sync errors: {e}")
        print("⚠️  Continuing with caution...")
        return 0  # Don't fail on checker errors, just warn

if __name__ == "__main__":
    sys.exit(check_fatal_sync_errors())