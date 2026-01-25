"""
Test suite to analyze and document the Mac + VNC baseline (commit 3d5ac82)
This documents what we're preserving before integrating Docker-era enhancements.
"""

import pytest
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_baseline_file_structure():
    """Verify all expected baseline files are present"""
    base_path = Path(__file__).parent.parent
    
    # Core application files that should exist
    expected_files = [
        'app.py',
        'src/core.py', 
        'src/logic.py',
        'src/workflow_utils.py',
        'src/git_update_manager.py',
        'src/scripts_updater.py',
        'templates/sip_workflow.yml',
        'templates/sps_workflow.yml'
    ]
    
    for file_path in expected_files:
        full_path = base_path / file_path
        assert full_path.exists(), f"Missing baseline file: {file_path}"
        print(f"✅ Found baseline file: {file_path}")

def test_docker_files_absent():
    """Verify Docker-specific files are NOT present in baseline"""
    base_path = Path(__file__).parent.parent
    
    # Docker files that should NOT exist in baseline
    docker_files = [
        'src/smart_sync.py',
        'src/debug_logger.py', 
        'src/fatal_sync_checker.py',
        'docker-compose.yml',
        'Dockerfile',
        'entrypoint.sh'
    ]
    
    for file_path in docker_files:
        full_path = base_path / file_path
        assert not full_path.exists(), f"Docker file should not exist in baseline: {file_path}"
        print(f"✅ Confirmed Docker file absent: {file_path}")

def test_workflow_utils_functionality():
    """Test that multi-workflow utilities work in baseline"""
    try:
        from workflow_utils import (
            get_workflow_template_path,
            get_workflow_type_display, 
            validate_workflow_type
        )
        
        # Test workflow type validation
        assert validate_workflow_type('sip') == True
        assert validate_workflow_type('sps-ce') == True
        assert validate_workflow_type('invalid') == False
        
        # Test workflow display
        display = get_workflow_type_display()
        assert display is not None
        
        print("✅ Multi-workflow utilities work correctly")
        
    except ImportError as e:
        pytest.fail(f"Could not import workflow utilities: {e}")

def test_git_update_manager_functionality():
    """Test that Git update manager works in baseline"""
    try:
        from git_update_manager import GitUpdateManager, get_repository_config
        
        # Test repository config
        config = get_repository_config('sip')
        assert 'repo_url' in config
        assert 'api_url' in config
        
        # Test GitUpdateManager initialization
        manager = GitUpdateManager('scripts', Path.cwd())
        assert manager is not None
        
        print("✅ Git update manager works correctly")
        
    except ImportError as e:
        pytest.fail(f"Could not import git update manager: {e}")

def test_scripts_updater_functionality():
    """Test that scripts updater works in baseline"""
    try:
        from scripts_updater import ScriptsUpdater
        
        # Test ScriptsUpdater initialization
        updater = ScriptsUpdater('sip')
        assert updater is not None
        
        print("✅ Scripts updater works correctly")
        
    except ImportError as e:
        pytest.fail(f"Could not import scripts updater: {e}")

def test_core_imports():
    """Test that core.py imports work without Docker dependencies"""
    try:
        from core import Project, Workflow
        
        # Test basic class instantiation
        workflow_path = Path(__file__).parent.parent / 'templates' / 'sip_workflow.yml'
        if workflow_path.exists():
            workflow = Workflow(workflow_path)
            assert workflow is not None
            
        print("✅ Core classes import and instantiate correctly")
        
    except ImportError as e:
        pytest.fail(f"Could not import core classes: {e}")

def test_logic_imports():
    """Test that logic.py imports work without Docker dependencies"""
    try:
        from logic import StateManager, SnapshotManager, ScriptRunner
        
        # Test basic class instantiation
        test_path = Path('/tmp/test_state.json')
        state_manager = StateManager(test_path)
        assert state_manager is not None
        
        print("✅ Logic classes import and instantiate correctly")
        
    except ImportError as e:
        pytest.fail(f"Could not import logic classes: {e}")

def test_baseline_templates():
    """Test that workflow templates exist and are valid"""
    base_path = Path(__file__).parent.parent
    
    # Test SIP template
    sip_template = base_path / 'templates' / 'sip_workflow.yml'
    assert sip_template.exists(), "SIP workflow template missing"
    
    # Test SPS-CE template  
    sps_template = base_path / 'templates' / 'sps_workflow.yml'
    assert sps_template.exists(), "SPS-CE workflow template missing"
    
    # Test template content
    import yaml
    with open(sip_template) as f:
        sip_data = yaml.safe_load(f)
        assert 'steps' in sip_data
        assert len(sip_data['steps']) > 0
        
    with open(sps_template) as f:
        sps_data = yaml.safe_load(f)
        assert 'steps' in sps_data
        assert len(sps_data['steps']) > 0
        
    print("✅ Workflow templates are valid")

if __name__ == "__main__":
    # Run tests to document baseline state
    pytest.main([__file__, "-v"])