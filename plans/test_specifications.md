# Test Specifications and Validation Criteria

## Overview

This document provides comprehensive test specifications for validating the workflow generalization implementation with critical WORKFLOW_TYPE propagation testing. Tests are organized by type and include specific validation criteria, expected outcomes, and pass/fail conditions.

## Critical WORKFLOW_TYPE Propagation Tests (PRIORITY 1)

### Test Suite: WORKFLOW_TYPE Environment Propagation

**File**: `tests/test_workflow_type_propagation.py`

#### Test: Environment Variable Flow
```python
def test_workflow_type_propagation():
    """Test WORKFLOW_TYPE flows from run scripts to Docker to application"""
    # Test environment variable is set correctly
    # Test docker-compose receives WORKFLOW_TYPE
    # Test container environment includes WORKFLOW_TYPE
    # Test app.py reads WORKFLOW_TYPE correctly
```

#### Test: Script Path Resolution
```python
def test_workflow_specific_script_paths():
    """Test script paths are workflow-specific"""
    for workflow_type in ['sip', 'sps-ce']:
        with patch.dict(os.environ, {'WORKFLOW_TYPE': workflow_type}):
            expected_path = f"~/.sip_lims_workflow_manager/{workflow_type}_scripts"
            assert get_scripts_path() == expected_path
```

#### Test: Repository Management
```python
def test_workflow_repository_mapping():
    """Test correct repositories are used per workflow type"""
    sip_updater = ScriptsUpdater(workflow_type='sip')
    assert 'sip_scripts_workflow_gui' in sip_updater.scripts_repo_url
    
    sps_updater = ScriptsUpdater(workflow_type='sps-ce')
    assert 'SPS_library_creation_scripts' in sps_updater.scripts_repo_url
```

#### Test: Docker Volume Mounting
```python
def test_docker_volume_mounting():
    """Test Docker mounts correct workflow-specific directory"""
    # Test SCRIPTS_PATH environment variable construction
    # Test docker-compose volume mounting logic
    # Test container can access workflow-specific scripts
```

## Unit Tests

### Test Suite 1: Template System Tests

**File**: `tests/test_template_system.py`

#### Test 1.1: SIP Template Selection
```python
def test_sip_template_selection():
    """Test SIP workflow template selection and loading"""
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sip'}):
        template_path = get_template_path()
        assert template_path == Path("templates/sip_workflow.yml")
        assert template_path.exists()
```

**Expected Result**: Template path resolves to `sip_workflow.yml`
**Pass Criteria**: Function returns correct path and file exists

#### Test 1.2: SPS-CE Template Selection
```python
def test_sps_ce_template_selection():
    """Test SPS-CE workflow template selection and loading"""
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sps-ce'}):
        template_path = get_template_path()
        assert template_path == Path("templates/sps_workflow.yml")
        assert template_path.exists()
```

**Expected Result**: Template path resolves to `sps_workflow.yml`
**Pass Criteria**: Function returns correct path and file exists

#### Test 1.3: Template Validation
```python
def test_template_validation():
    """Test template structure validation"""
    for workflow_type in ['sip', 'sps-ce']:
        template_path = Path(f"templates/{workflow_type}_workflow.yml")
        assert validate_workflow_template(template_path) == True
```

**Expected Result**: Both templates pass validation
**Pass Criteria**: All required fields present, proper YAML structure

### Test Suite 2: Script Path Resolution Tests

**File**: `tests/test_script_path_resolution.py`

#### Test 2.1: SIP Script Path
```python
def test_sip_script_path():
    """Test SIP script path construction"""
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sip'}):
        expected_path = Path.home() / '.sip_lims_workflow_manager' / 'sip_scripts'
        actual_path = get_scripts_directory()
        assert actual_path == expected_path
```

**Expected Result**: Path resolves to `sip_scripts` directory
**Pass Criteria**: Correct path construction

#### Test 2.2: SPS-CE Script Path
```python
def test_sps_ce_script_path():
    """Test SPS-CE script path construction"""
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sps-ce'}):
        expected_path = Path.home() / '.sip_lims_workflow_manager' / 'sps-ce_scripts'
        actual_path = get_scripts_directory()
        assert actual_path == expected_path
```

**Expected Result**: Path resolves to `sps-ce_scripts` directory
**Pass Criteria**: Correct path construction

### Test Suite 3: Environment Variable Tests

**File**: `tests/test_environment_variables.py`

#### Test 3.1: WORKFLOW_TYPE Propagation
```python
def test_workflow_type_propagation():
    """Test WORKFLOW_TYPE environment variable propagation"""
    test_cases = ['sip', 'sps-ce']
    for workflow_type in test_cases:
        with patch.dict(os.environ, {'WORKFLOW_TYPE': workflow_type}):
            assert os.environ.get('WORKFLOW_TYPE') == workflow_type
```

**Expected Result**: Environment variable correctly set and accessible
**Pass Criteria**: Variable value matches expected workflow type

## Integration Tests

### Test Suite 4: End-to-End SIP Workflow Tests

**File**: `tests/integration/test_sip_workflow_e2e.py`

#### Test 4.1: SIP Project Creation
```python
def test_sip_project_creation():
    """Test complete SIP project creation workflow"""
    # Setup
    test_project_dir = create_temp_directory()
    
    # Test workflow selection
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sip'}):
        # Test template copying
        result = initialize_project(test_project_dir)
        assert result == True
        
        # Verify template copied correctly
        workflow_file = test_project_dir / 'workflow.yml'
        assert workflow_file.exists()
        
        # Verify template content
        with open(workflow_file) as f:
            workflow_data = yaml.safe_load(f)
        assert workflow_data['workflow_name'] == "SIP Fractionation and Library Prep"
```

**Expected Result**: SIP project created with correct template
**Pass Criteria**: Template copied, correct content, no errors

#### Test 4.2: SIP Workflow State Management
```python
def test_sip_workflow_state_management():
    """Test SIP workflow state progression"""
    # Test state file creation
    # Test step progression
    # Test success marker detection
    # Test undo/redo functionality
```

**Expected Result**: State management works correctly for SIP workflow
**Pass Criteria**: State transitions work, markers detected, undo/redo functional

### Test Suite 5: End-to-End SPS-CE Workflow Tests

**File**: `tests/integration/test_sps_ce_workflow_e2e.py`

#### Test 5.1: SPS-CE Project Creation
```python
def test_sps_ce_project_creation():
    """Test complete SPS-CE project creation workflow"""
    test_project_dir = create_temp_directory()
    
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sps-ce'}):
        result = initialize_project(test_project_dir)
        assert result == True
        
        workflow_file = test_project_dir / 'workflow.yml'
        assert workflow_file.exists()
        
        with open(workflow_file) as f:
            workflow_data = yaml.safe_load(f)
        assert workflow_data['workflow_name'] == "SPS Library Creation"
        assert len(workflow_data['steps']) == 6
```

**Expected Result**: SPS-CE project created with correct template
**Pass Criteria**: Template copied, 6 steps present, correct workflow name

#### Test 5.2: SPS-CE Decision Script Integration
```python
def test_sps_ce_decision_script():
    """Test SPS-CE decision script functionality"""
    # Test decision script execution
    # Test state updates for YES choice
    # Test state updates for NO choice
    # Test success marker creation
```

**Expected Result**: Decision script works correctly
**Pass Criteria**: State updates correctly, success markers created

### Test Suite 6: Workflow Switching Tests

**File**: `tests/integration/test_workflow_switching.py`

#### Test 6.1: Project Isolation
```python
def test_project_isolation():
    """Test that different workflow projects are isolated"""
    sip_project = create_temp_directory("sip_test")
    sps_project = create_temp_directory("sps_test")
    
    # Create SIP project
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sip'}):
        initialize_project(sip_project)
    
    # Create SPS-CE project
    with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sps-ce'}):
        initialize_project(sps_project)
    
    # Verify isolation
    sip_workflow = yaml.safe_load((sip_project / 'workflow.yml').read_text())
    sps_workflow = yaml.safe_load((sps_project / 'workflow.yml').read_text())
    
    assert sip_workflow['workflow_name'] != sps_workflow['workflow_name']
    assert len(sip_workflow['steps']) != len(sps_workflow['steps'])
```

**Expected Result**: Projects are completely isolated
**Pass Criteria**: Different templates, no cross-contamination

## System Tests

### Test Suite 7: Success Marker Tests

**File**: `tests/test_success_markers.py`

#### Test 7.1: SPS-CE Success Marker Validation
```python
def test_sps_ce_success_markers():
    """Test that all SPS-CE scripts create success markers"""
    required_scripts = [
        'SPS_make_illumina_index_and_FA_files_NEW.py',
        'SPS_first_FA_output_analysis_NEW.py',
        'SPS_rework_first_attempt_NEW.py',
        'SPS_second_FA_output_analysis_NEW.py',
        'decision_second_attempt.py'
    ]
    
    for script in required_scripts:
        # Mock script execution
        # Verify success marker created
        expected_marker = f".workflow_status/{Path(script).stem}.success"
        assert Path(expected_marker).exists()
```

**Expected Result**: All scripts create success markers
**Pass Criteria**: Success marker files created with correct names

### Test Suite 8: Docker Integration Tests

**File**: `tests/test_docker_integration.py`

#### Test 8.1: Environment Variable Passing
```python
def test_docker_environment_variables():
    """Test that WORKFLOW_TYPE passes through to Docker container"""
    # Test environment variable propagation to Docker
    # Test script path resolution in container
    # Test template access in container
```

**Expected Result**: Environment variables accessible in container
**Pass Criteria**: Variables available, paths resolve correctly

## Manual Test Scenarios

### Manual Test 1: Complete SIP Workflow
**Objective**: Verify SIP workflow unchanged (backward compatibility)

**Steps**:
1. Run `./run.mac.command`
2. Select "1) SIP Fractionation and Library Prep"
3. Create new project in test directory
4. Execute first 3 workflow steps
5. Verify success markers created
6. Test undo functionality
7. Verify state management

**Expected Results**:
- Workflow selection works
- SIP template copied correctly
- Scripts execute successfully
- Success markers created
- State management functional
- No behavioral changes from original

**Pass Criteria**: All functionality identical to pre-generalization behavior

### Manual Test 2: Complete SPS-CE Workflow
**Objective**: Verify new SPS-CE workflow functionality

**Steps**:
1. Run `./run.mac.command`
2. Select "2) SPS-CE Library Creation"
3. Create new project in test directory
4. Execute Step 1: Make Illumina Index and FA Files
5. Execute Step 2: First FA Output Analysis
6. Execute Step 3: Decision Script - test YES path
7. Execute Step 4: Rework First Attempt
8. Execute Step 5: Second FA Output Analysis
9. Execute Step 6: Conclude FA Analysis

**Expected Results**:
- SPS-CE workflow selection works
- SPS-CE template copied correctly
- All 6 steps execute successfully
- Decision script prompts correctly
- Conditional steps work (YES path)
- Success markers created for all steps

**Pass Criteria**: Complete SPS-CE workflow executes without errors

### Manual Test 3: SPS-CE Decision Script NO Path
**Objective**: Test conditional workflow skipping

**Steps**:
1. Create SPS-CE project
2. Execute Steps 1-2
3. Execute Decision Script - select NO
4. Verify Steps 4-5 skipped
5. Execute Step 6 directly

**Expected Results**:
- Decision script accepts NO choice
- Steps 4-5 marked as "skipped" in state
- Step 6 becomes available immediately
- Workflow completes successfully

**Pass Criteria**: Conditional skipping works correctly

### Manual Test 4: Error Handling
**Objective**: Test error scenarios and recovery

**Steps**:
1. Test invalid workflow selection (enter "3")
2. Test missing template files
3. Test missing script directories
4. Test script execution failures
5. Test Docker environment issues

**Expected Results**:
- Clear error messages displayed
- Graceful failure handling
- No system corruption
- Recovery possible

**Pass Criteria**: All error scenarios handled gracefully

## Performance Tests

### Performance Test 1: Startup Time
**Objective**: Verify no performance degradation

**Test**: Measure application startup time for both workflows
**Expected Result**: No significant increase in startup time
**Pass Criteria**: <5% increase in startup time

### Performance Test 2: Template Loading
**Objective**: Verify template selection doesn't impact performance

**Test**: Measure template loading and validation time
**Expected Result**: Template operations complete quickly
**Pass Criteria**: <100ms for template operations

## Validation Criteria Summary

### Critical Success Criteria
1. **Backward Compatibility**: SIP workflow unchanged
2. **New Functionality**: SPS-CE workflow fully functional
3. **Isolation**: No cross-contamination between workflows
4. **Success Markers**: All scripts create required markers
5. **State Management**: Workflow state correctly managed
6. **Error Handling**: Graceful failure and recovery

### Performance Criteria
1. **Startup Time**: <5% increase
2. **Memory Usage**: No significant increase
3. **Docker Performance**: No container startup delays

### Quality Criteria
1. **Test Coverage**: >90% code coverage
2. **Error Scenarios**: All error paths tested
3. **Documentation**: Complete user and developer docs
4. **Code Quality**: All linting and style checks pass

## Test Execution Strategy

### Phase 1: Unit Tests
- Run all unit tests
- Achieve >90% code coverage
- Fix any failing tests

### Phase 2: Integration Tests
- Run integration test suites
- Verify end-to-end functionality
- Test workflow switching

### Phase 3: Manual Testing
- Execute all manual test scenarios
- Document any issues found
- Verify user experience

### Phase 4: Performance Testing
- Run performance benchmarks
- Compare with baseline metrics
- Optimize if necessary

### Phase 5: User Acceptance Testing
- User validates SIP workflow unchanged
- User validates SPS-CE workflow functional
- User approves for production deployment

## Test Environment Setup

### Prerequisites
- Python 3.8+ with pytest
- Docker Desktop running
- Git repositories cloned
- Test data available

### Test Data Requirements
- Sample SIP project data
- Sample SPS-CE project data
- Mock script execution environments
- Test file fixtures

### Continuous Integration
- All tests run on every commit
- Performance benchmarks tracked
- Test results reported
- Deployment blocked on test failures