"""
Workflow utilities for template selection and workflow type handling.
This module provides workflow-aware functionality that can be tested independently.
"""

import os
from pathlib import Path


def get_workflow_template_path():
    """
    Get appropriate workflow template path based on WORKFLOW_TYPE environment variable.
    This is ONLY used when creating NEW projects - existing projects use their own workflow.yml.
    
    Returns:
        Path: Path to the appropriate workflow template file
        
    Raises:
        ValueError: If WORKFLOW_TYPE is not set or is invalid
    """
    workflow_type = os.environ.get('WORKFLOW_TYPE')
    
    # Fail fast if WORKFLOW_TYPE is not set
    if not workflow_type:
        raise ValueError("WORKFLOW_TYPE environment variable is required but not set")
    
    workflow_type = workflow_type.lower()
    
    # Validate workflow type - fail fast if invalid
    if workflow_type not in ['sip', 'sps-ce']:
        raise ValueError(f"Invalid WORKFLOW_TYPE '{workflow_type}'. Must be 'sip' or 'sps-ce'.")
    
    # Map workflow type to template filename
    template_mapping = {
        'sip': 'sip_workflow.yml',
        'sps-ce': 'sps_workflow.yml'
    }
    
    template_filename = template_mapping[workflow_type]
    app_dir = Path(__file__).parent.parent
    template_path = app_dir / "templates" / template_filename
    
    # Verify template file exists - fail fast if missing
    if not template_path.exists():
        raise FileNotFoundError(f"Workflow template not found: {template_path}")
        
    return template_path


def get_workflow_type_display():
    """
    Get the workflow type for display purposes.
    
    Returns:
        str: Uppercase workflow type for display, or 'UNKNOWN' if not set
    """
    workflow_type = os.environ.get('WORKFLOW_TYPE')
    return workflow_type.upper() if workflow_type else 'UNKNOWN'


def validate_workflow_type(workflow_type: str) -> bool:
    """
    Validate if a workflow type is supported.
    
    Args:
        workflow_type: The workflow type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not workflow_type:
        return False
    return workflow_type.lower() in ['sip', 'sps-ce']