#!/usr/bin/env python3
"""
Setup script to initialize Git tags for both repositories.
This script helps establish the initial versioning for the unified update system.
"""

import subprocess
import sys
from pathlib import Path
from src.git_update_manager import create_update_manager


def run_git_command(command, cwd=None, env=None):
    """Run a Git command and return the result."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(command)}")
        return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def check_repository_status():
    """Check the current status of both repositories."""
    print("=== Repository Status Check ===")
    
    # Check app repository
    print("\n📱 Application Repository:")
    app_path = Path(".")
    
    # Get current tags
    result = run_git_command(['git', 'tag', '--list'], cwd=app_path)
    if result and result.returncode == 0:
        tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
        print(f"  Current tags: {tags}")
        
        if tags:
            # Get latest tag
            latest_result = run_git_command(['git', 'describe', '--tags', '--abbrev=0'], cwd=app_path)
            if latest_result and latest_result.returncode == 0:
                print(f"  Latest tag: {latest_result.stdout.strip()}")
    else:
        print("  No tags found")
    
    # Check scripts repository
    print("\n📜 Scripts Repository:")
    scripts_path = Path("scripts")
    
    if scripts_path.exists():
        result = run_git_command(['git', 'tag', '--list'], cwd=scripts_path)
        if result and result.returncode == 0:
            tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
            print(f"  Current tags: {tags}")
            
            if not tags:
                print("  ⚠️  No tags found - will need to create initial tag")
        else:
            print("  ❌ Error checking tags")
    else:
        print("  ❌ Scripts directory not found")


def create_initial_script_tag():
    """Create an initial tag for the scripts repository."""
    print("\n=== Creating Initial Scripts Tag ===")
    
    scripts_path = Path("scripts")
    if not scripts_path.exists():
        print("❌ Scripts directory not found")
        return False
    
    # Check current status
    status_result = run_git_command(['git', 'status', '--porcelain'], cwd=scripts_path)
    if status_result and status_result.stdout.strip():
        print("⚠️  Scripts repository has uncommitted changes:")
        print(status_result.stdout)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Create initial tag
    initial_version = "v1.0.0"
    print(f"Creating initial tag: {initial_version}")
    
    # Create annotated tag
    tag_result = run_git_command([
        'git', 'tag', '-a', initial_version, 
        '-m', f'Initial release {initial_version}: Baseline scripts for unified update system'
    ], cwd=scripts_path)
    
    if tag_result and tag_result.returncode == 0:
        print(f"✅ Created local tag: {initial_version}")
        
        # Push tag to remote
        push_result = run_git_command([
            'git', 'push', 'origin', initial_version
        ], cwd=scripts_path)
        
        if push_result and push_result.returncode == 0:
            print(f"✅ Pushed tag to remote: {initial_version}")
            return True
        else:
            print(f"❌ Failed to push tag: {push_result.stderr if push_result else 'Unknown error'}")
            return False
    else:
        print(f"❌ Failed to create tag: {tag_result.stderr if tag_result else 'Unknown error'}")
        return False


def main():
    """Main setup function."""
    print("🚀 SIP LIMS Workflow Manager - Repository Setup")
    print("=" * 50)
    
    # Check current status
    check_repository_status()
    
    # Ask user what they want to do
    print("\n📋 Available Actions:")
    print("1. Create initial tag for scripts repository")
    print("2. Exit")
    
    choice = input("\nSelect an action (1-2): ").strip()
    
    if choice == "1":
        create_initial_script_tag()
    elif choice == "2":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    print("\n✅ Setup complete!")


if __name__ == "__main__":
    main()