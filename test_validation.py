#!/usr/bin/env python3
"""
Manual validation test script for Capsule Sorting workflow implementation.
Tests the core functionality without interactive prompts.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path to find src modules
sys.path.insert(0, str(Path(__file__).parent))

def test_workflow_validation():
    """Test the validate_workflow_type function."""
    print("🧪 Testing Workflow Type Validation...")
    
    # Import the function
    from launcher.run import validate_workflow_type
    
    # Test valid workflow types
    test_cases = [
        ('sip', 'sip'),
        ('SIP', 'sip'),
        ('sip-lims', 'sip'),
        ('sps-ce', 'sps-ce'),
        ('SPS-CE', 'sps-ce'),
        ('sps', 'sps-ce'),
        ('capsule-sorting', 'capsule-sorting'),
        ('CAPSULE-SORTING', 'capsule-sorting'),
        ('capsule_sorting', 'capsule-sorting'),
    ]
    
    for input_val, expected in test_cases:
        try:
            result = validate_workflow_type(input_val)
            if result == expected:
                print(f"✅ '{input_val}' -> '{result}' (expected: '{expected}')")
            else:
                print(f"❌ '{input_val}' -> '{result}' (expected: '{expected}')")
        except SystemExit:
            print(f"❌ '{input_val}' caused SystemExit (unexpected)")
    
    # Test invalid workflow types (should cause SystemExit)
    invalid_cases = ['invalid', '', None]
    for invalid_val in invalid_cases:
        try:
            result = validate_workflow_type(invalid_val)
            print(f"❌ '{invalid_val}' should have caused SystemExit but returned: '{result}'")
        except SystemExit:
            print(f"✅ '{invalid_val}' correctly caused SystemExit")
        except Exception as e:
            print(f"❌ '{invalid_val}' caused unexpected error: {e}")

def test_dynamic_title():
    """Test the dynamic title generation."""
    print("\n🧪 Testing Dynamic Title Generation...")
    
    # Import the function
    from app import get_dynamic_title
    
    # Test different workflow types
    test_cases = [
        ('SIP', '🧪 SIP LIMS Workflow Manager'),
        ('SPS-CE', '🧪 SPS-CE LIMS Workflow Manager'),
        ('CAPSULE-SORTING', '🧪 Capsule Sorting LIMS Workflow Manager'),
        ('', '🧪 SIP LIMS Workflow Manager'),  # fallback
        ('INVALID', '🧪 SIP LIMS Workflow Manager'),  # fallback
    ]
    
    for workflow_type, expected_title in test_cases:
        # Set environment variable
        if workflow_type:
            os.environ['WORKFLOW_TYPE'] = workflow_type
        else:
            os.environ.pop('WORKFLOW_TYPE', None)
        
        try:
            result = get_dynamic_title()
            if result == expected_title:
                print(f"✅ WORKFLOW_TYPE='{workflow_type}' -> '{result}'")
            else:
                print(f"❌ WORKFLOW_TYPE='{workflow_type}' -> '{result}' (expected: '{expected_title}')")
        except Exception as e:
            print(f"❌ WORKFLOW_TYPE='{workflow_type}' caused error: {e}")
    
    # Clean up environment
    os.environ.pop('WORKFLOW_TYPE', None)

def test_template_loading():
    """Test that the Capsule Sorting template exists and is valid."""
    print("\n🧪 Testing Template Loading...")
    
    template_path = Path("templates/CapsuleSorting_workflow.yml")
    
    if not template_path.exists():
        print(f"❌ Template file does not exist: {template_path}")
        return
    
    print(f"✅ Template file exists: {template_path}")
    
    try:
        import yaml
        with open(template_path, 'r') as f:
            workflow_data = yaml.safe_load(f)
        
        # Validate structure
        if workflow_data.get('workflow_name') == "Capsule Sorting":
            print("✅ Workflow name is correct")
        else:
            print(f"❌ Workflow name incorrect: {workflow_data.get('workflow_name')}")
        
        steps = workflow_data.get('steps', [])
        if len(steps) == 6:
            print("✅ Correct number of steps (6)")
        else:
            print(f"❌ Incorrect number of steps: {len(steps)}")
        
        # Validate required scripts
        expected_scripts = [
            "initiate_project_folder_and_make_sort_plate_labels.py",
            "generate_lib_creation_files.py",
            "capsule_fa_analysis.py",
            "create_capsule_spits.py",
            "process_grid_tables_and_generate_barcodes.py",
            "verify_scanning_and_generate_ESP_files.py"
        ]
        
        actual_scripts = [step.get('script') for step in steps]
        if actual_scripts == expected_scripts:
            print("✅ All required scripts are present and in correct order")
        else:
            print(f"❌ Script mismatch:")
            print(f"   Expected: {expected_scripts}")
            print(f"   Actual:   {actual_scripts}")
        
        print("✅ Template file is valid YAML and contains expected structure")
        
    except Exception as e:
        print(f"❌ Error loading template: {e}")

def test_workflow_utils():
    """Test workflow utilities support for capsule-sorting."""
    print("\n🧪 Testing Workflow Utils...")
    
    try:
        from src.workflow_utils import get_workflow_template_path, validate_workflow_type as utils_validate
        
        # Test template path resolution
        os.environ['WORKFLOW_TYPE'] = 'capsule-sorting'
        try:
            template_path = get_workflow_template_path()
            if template_path.name == 'CapsuleSorting_workflow.yml':
                print("✅ get_workflow_template_path() returns correct template for capsule-sorting")
            else:
                print(f"❌ get_workflow_template_path() returned: {template_path.name}")
        except Exception as e:
            print(f"❌ get_workflow_template_path() failed: {e}")
        finally:
            os.environ.pop('WORKFLOW_TYPE', None)
        
        # Test validation function
        if utils_validate('capsule-sorting'):
            print("✅ validate_workflow_type() accepts capsule-sorting")
        else:
            print("❌ validate_workflow_type() rejects capsule-sorting")
            
    except ImportError as e:
        print(f"❌ Failed to import workflow_utils: {e}")
    except Exception as e:
        print(f"❌ Error testing workflow_utils: {e}")

def main():
    """Run all validation tests."""
    print("🚀 Starting Manual Validation Tests for Capsule Sorting Implementation")
    print("=" * 70)
    
    test_workflow_validation()
    test_dynamic_title()
    test_template_loading()
    test_workflow_utils()
    
    print("\n" + "=" * 70)
    print("✅ Manual validation tests completed!")

if __name__ == "__main__":
    main()