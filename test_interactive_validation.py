#!/usr/bin/env python3
"""
Interactive validation test for Capsule Sorting workflow implementation.
Tests the interactive workflow selection with simulated input.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Add parent directory to Python path to find src modules
sys.path.insert(0, str(Path(__file__).parent))

def test_interactive_workflow_selection():
    """Test the interactive workflow selection with simulated user input."""
    print("🧪 Testing Interactive Workflow Selection...")
    
    from launcher.run import interactive_workflow_selection
    
    # Test cases: (user_input, expected_result)
    test_cases = [
        ('1', 'sip'),
        ('2', 'sps-ce'),
        ('3', 'capsule-sorting'),
    ]
    
    for user_input, expected_result in test_cases:
        print(f"\n  Testing input '{user_input}' -> expected '{expected_result}'")
        
        # Mock click.prompt to return our test input
        with patch('launcher.run.click.prompt', return_value=user_input):
            # Capture output
            with patch('launcher.run.click.echo') as mock_echo, \
                 patch('launcher.run.click.secho') as mock_secho:
                
                try:
                    result = interactive_workflow_selection()
                    if result == expected_result:
                        print(f"    ✅ Input '{user_input}' correctly returned '{result}'")
                    else:
                        print(f"    ❌ Input '{user_input}' returned '{result}', expected '{expected_result}'")
                except Exception as e:
                    print(f"    ❌ Input '{user_input}' caused error: {e}")

def test_invalid_workflow_selection():
    """Test invalid workflow selection inputs."""
    print("\n🧪 Testing Invalid Workflow Selection...")
    
    from launcher.run import interactive_workflow_selection
    
    # Test invalid input that should cause SystemExit
    invalid_inputs = ['4', '0', 'invalid', 'abc']
    
    for invalid_input in invalid_inputs:
        print(f"\n  Testing invalid input '{invalid_input}'")
        
        # Mock click.prompt to return invalid input
        with patch('launcher.run.click.prompt', return_value=invalid_input):
            # Mock the output functions
            with patch('launcher.run.click.echo'), \
                 patch('launcher.run.click.secho'):
                
                try:
                    result = interactive_workflow_selection()
                    print(f"    ❌ Invalid input '{invalid_input}' should have caused SystemExit but returned: '{result}'")
                except SystemExit:
                    print(f"    ✅ Invalid input '{invalid_input}' correctly caused SystemExit")
                except Exception as e:
                    print(f"    ❌ Invalid input '{invalid_input}' caused unexpected error: {e}")

def test_scripts_updater_integration():
    """Test ScriptsUpdater integration with capsule-sorting."""
    print("\n🧪 Testing ScriptsUpdater Integration...")
    
    try:
        from src.scripts_updater import ScriptsUpdater, WORKFLOW_REPOSITORIES
        
        # Test that capsule-sorting is in the repository mapping
        if 'capsule-sorting' in WORKFLOW_REPOSITORIES:
            print("  ✅ capsule-sorting found in WORKFLOW_REPOSITORIES")
            
            config = WORKFLOW_REPOSITORIES['capsule-sorting']
            expected_repo = 'capsule-single-cell-sort-scripts'
            expected_owner = 'rrmalmstrom'
            
            if config['repo_name'] == expected_repo:
                print(f"  ✅ Repository name correct: {config['repo_name']}")
            else:
                print(f"  ❌ Repository name incorrect: {config['repo_name']} (expected: {expected_repo})")
            
            if config['repo_owner'] == expected_owner:
                print(f"  ✅ Repository owner correct: {config['repo_owner']}")
            else:
                print(f"  ❌ Repository owner incorrect: {config['repo_owner']} (expected: {expected_owner})")
        else:
            print("  ❌ capsule-sorting not found in WORKFLOW_REPOSITORIES")
        
        # Test ScriptsUpdater initialization
        try:
            updater = ScriptsUpdater('capsule-sorting')
            print("  ✅ ScriptsUpdater initialized successfully with capsule-sorting")
            
            # Check that the correct repository configuration is loaded
            if hasattr(updater, 'repo_name') and updater.repo_name == 'capsule-single-cell-sort-scripts':
                print("  ✅ ScriptsUpdater loaded correct repository name")
            else:
                print(f"  ❌ ScriptsUpdater repository name: {getattr(updater, 'repo_name', 'NOT SET')}")
                
        except Exception as e:
            print(f"  ❌ ScriptsUpdater initialization failed: {e}")
            
    except ImportError as e:
        print(f"  ❌ Failed to import ScriptsUpdater: {e}")

def test_environment_variable_propagation():
    """Test that environment variables are set correctly."""
    print("\n🧪 Testing Environment Variable Propagation...")
    
    from launcher.run import setup_environment_variables
    
    # Test setup with capsule-sorting workflow
    test_project_path = Path.cwd()
    test_scripts_path = "/test/scripts/path"
    
    # Mock click.echo to suppress output during testing
    with patch('launcher.run.click.echo'), patch('launcher.run.click.secho'):
        setup_environment_variables('capsule-sorting', test_project_path, test_scripts_path)
    
    # Check environment variables
    workflow_type = os.environ.get('WORKFLOW_TYPE')
    if workflow_type == 'CAPSULE-SORTING':
        print("  ✅ WORKFLOW_TYPE set correctly to 'CAPSULE-SORTING'")
    else:
        print(f"  ❌ WORKFLOW_TYPE incorrect: '{workflow_type}' (expected: 'CAPSULE-SORTING')")
    
    project_path = os.environ.get('PROJECT_PATH')
    if project_path == str(test_project_path):
        print("  ✅ PROJECT_PATH set correctly")
    else:
        print(f"  ❌ PROJECT_PATH incorrect: '{project_path}'")
    
    execution_mode = os.environ.get('EXECUTION_MODE')
    if execution_mode == 'native':
        print("  ✅ EXECUTION_MODE set correctly to 'native'")
    else:
        print(f"  ❌ EXECUTION_MODE incorrect: '{execution_mode}' (expected: 'native')")

def test_end_to_end_workflow_selection():
    """Test the complete workflow from selection to environment setup."""
    print("\n🧪 Testing End-to-End Workflow Selection...")
    
    # Test the complete flow for capsule-sorting
    from launcher.run import validate_workflow_type, setup_environment_variables
    from app import get_dynamic_title
    from src.workflow_utils import get_workflow_template_path
    
    # Step 1: Validate workflow type
    try:
        validated_type = validate_workflow_type('capsule-sorting')
        if validated_type == 'capsule-sorting':
            print("  ✅ Step 1: Workflow type validation successful")
        else:
            print(f"  ❌ Step 1: Workflow type validation failed: {validated_type}")
            return
    except Exception as e:
        print(f"  ❌ Step 1: Workflow type validation error: {e}")
        return
    
    # Step 2: Set up environment variables
    try:
        test_project_path = Path.cwd()
        with patch('launcher.run.click.echo'), patch('launcher.run.click.secho'):
            setup_environment_variables(validated_type, test_project_path, "/test/scripts")
        print("  ✅ Step 2: Environment variables setup successful")
    except Exception as e:
        print(f"  ❌ Step 2: Environment variables setup error: {e}")
        return
    
    # Step 3: Test dynamic title generation
    try:
        title = get_dynamic_title()
        expected_title = "🧪 Capsule Sorting LIMS Workflow Manager"
        if title == expected_title:
            print("  ✅ Step 3: Dynamic title generation successful")
        else:
            print(f"  ❌ Step 3: Dynamic title incorrect: '{title}' (expected: '{expected_title}')")
    except Exception as e:
        print(f"  ❌ Step 3: Dynamic title generation error: {e}")
    
    # Step 4: Test template path resolution
    try:
        template_path = get_workflow_template_path()
        if template_path.name == 'CapsuleSorting_workflow.yml' and template_path.exists():
            print("  ✅ Step 4: Template path resolution successful")
        else:
            print(f"  ❌ Step 4: Template path incorrect: {template_path}")
    except Exception as e:
        print(f"  ❌ Step 4: Template path resolution error: {e}")
    
    # Clean up environment
    for key in ['WORKFLOW_TYPE', 'PROJECT_PATH', 'SCRIPTS_PATH', 'EXECUTION_MODE', 'APP_ENV']:
        os.environ.pop(key, None)

def main():
    """Run all interactive validation tests."""
    print("🚀 Starting Interactive Validation Tests for Capsule Sorting Implementation")
    print("=" * 80)
    
    test_interactive_workflow_selection()
    test_invalid_workflow_selection()
    test_scripts_updater_integration()
    test_environment_variable_propagation()
    test_end_to_end_workflow_selection()
    
    print("\n" + "=" * 80)
    print("✅ Interactive validation tests completed!")

if __name__ == "__main__":
    main()