# New Workflow Implementation Plan: Capsule Sorting

This document outlines the plan for integrating a new "Capsule Sorting" workflow into the `sip_lims_workflow_manager`.

## 1. New Workflow Definition: Capsule Sorting

The "Capsule Sorting" workflow is a six-step process for sorting and preparing capsules for downstream analysis. It is a highly automated workflow that relies on a central database and a series of Python scripts to process data and generate files for laboratory instruments.

### 1.1. Workflow Scripts

The "Capsule Sorting" workflow consists of the following six Python scripts:

1.  `initiate_project_folder_and_make_sort_plate_labels.py`: Initializes the project directory structure and generates barcode labels for the plates.
2.  `generate_lib_creation_files.py`: Creates library creation files, including index assignments and FA protocols.
3.  `capsule_fa_analysis.py`: Analyzes the output from the Fragment Analyzer to assess the quality of the libraries.
4.  `create_capsule_spits.py`: Generates SPITS files for submitting samples to JGI.
5.  `process_grid_tables_and_generate_barcodes.py`: Processes grid tables, extracts container barcode mapping, and generates Excel barcode scanning template with BarTender files.
6.  `verify_scanning_and_generate_ESP_files.py`: Validates barcode scanning verification and generates ESP smear analysis files (with mandatory safety gate - sys.exit() on any barcode mismatch).

### 1.4. Local Script Location

The "Capsule Sorting" scripts will be downloaded to and managed in the following local directory:

`~/.sip_lims_workflow_manager/capsule-sorting_scripts`

```


### 1.2. Workflow Configuration File (`CapsuleSorting_workflow.yml`)

A new workflow configuration file, `templates/CapsuleSorting_workflow.yml`, will be created:

```yaml
workflow_name: "Capsule Sorting"
steps:
  - id: init_project
    name: "1. Initiate Project / Make Sort Labels"
    script: "initiate_project_folder_and_make_sort_plate_labels.py"
    allow_rerun: true

  - id: prep_library
    name: "2. Generate Lib Creation Files"
    script: "generate_lib_creation_files.py"
    allow_rerun: true

  - id: analyze_quality
    name: "3. Analyze FA data"
    script: "capsule_fa_analysis.py"
    allow_rerun: true

  - id: select_plates
    name: "4. Create SPITS file"
    script: "create_capsule_spits.py"
    allow_rerun: false

  - id: process_grid_barcodes
    name: "5. Process Grid Tables & Generate Barcodes"
    script: "process_grid_tables_and_generate_barcodes.py"
    allow_rerun: false

  - id: verify_scanning_esp
    name: "6. Verify Scanning & Generate ESP Files"
    script: "verify_scanning_and_generate_ESP_files.py"
    allow_rerun: false
    
```



## 2. Core Application Modifications

To integrate the "Capsule Sorting" workflow, the following modifications must be made to the core application:

### 2.1. `launcher/run.py`

- **`interactive_workflow_selection()`**: Add `'capsule-sorting'` as an option in the `workflow_choices` dictionary.

  **Modification:**
  ```python
  def interactive_workflow_selection():
      '''Interactive workflow type selection.'''
      click.echo()
      click.secho("🧪 SIP LIMS Workflow Manager - Native Launcher", fg='blue', bold=True)
      click.echo()
      click.echo("Available workflow types:")
      click.echo("  1. SIP - Standard workflow")
      click.echo("  2. SPS-CE - SPS workflow")
      click.echo("  3. Capsule Sorting - Capsule Sorting workflow")
      click.echo()

      while True:
          choice = click.prompt("Select workflow type (1, 2, or 3)", type=str).strip()

          if choice == '1':
              return 'sip'
          elif choice == '2':
              return 'sps-ce'
          elif choice == '3':
              return 'capsule-sorting'
          else:
              click.secho(f"❌ Invalid choice '{choice}'. Please enter 1, 2, or 3.", fg='red')
              click.secho("❌ Terminating - invalid workflow selection", fg='red', bold=True)
              sys.exit(1)
  ```

- **`validate_workflow_type()`**: **CRITICAL FIX** - Replace dangerous fallback logic with strict validation.

  **Current Problem**: The function defaults to "sip" for invalid workflow types, which could cause users to accidentally run the wrong workflow.

  **Required Fix:**
  ```python
  def validate_workflow_type(workflow_type: str) -> str:
      '''Validate and normalize workflow type.'''
      if not workflow_type:
          click.secho("❌ ERROR: No workflow type provided.", fg='red', bold=True)
          sys.exit(1)

      workflow_type = workflow_type.lower().strip()

      if workflow_type in ['sip', 'sip-lims']:
          return "sip"
      elif workflow_type in ['sps', 'sps-ce', 'spsceq']:
          return "sps-ce"
      elif workflow_type in ['capsule-sorting', 'capsule_sorting']:
          return "capsule-sorting"
      else:
          click.secho(f"❌ ERROR: Unknown workflow type '{workflow_type}'", fg='red', bold=True)
          click.secho("Valid options: sip, sps-ce, capsule-sorting", fg='red')
          sys.exit(1)
  ```

  **Safety Improvement**: Eliminates dangerous fallback to "sip" that could cause laboratory safety issues.

### 2.2. `src/scripts_updater.py`

- **`WORKFLOW_REPOSITORIES`**: Add a new entry for `'capsule-sorting'` that maps to the `capsule-single-cell-sort-scripts` GitHub repository.

 **Modification:**
 ```python
 WORKFLOW_REPOSITORIES = {
     'sip': {
         'repo_name': 'sip_scripts_workflow_gui',
         'repo_owner': 'rrmalmstrom'
     },
     'sps-ce': {
         'repo_name': 'SPS_library_creation_scripts',
         'repo_owner': 'rrmalmstrom'
     },
     'capsule-sorting': {
         'repo_name': 'capsule-single-cell-sort-scripts',
         'repo_owner': 'rrmalmstrom'
     }
 }
 ```

### 2.3. `src/workflow_utils.py`

**CRITICAL**: This file has TWO functions that need updating for Capsule Sorting support.

- **`get_workflow_template_path()`**: Add `'capsule-sorting': 'CapsuleSorting_workflow.yml'` to the `template_mapping` dictionary and update validation.

  **Modification:**
  ```python
  def get_workflow_template_path():
      '''
      Get appropriate workflow template path based on WORKFLOW_TYPE environment variable.
      This is ONLY used when creating NEW projects - existing projects use their own workflow.yml.
      '''
      workflow_type = os.environ.get('WORKFLOW_TYPE')

      if not workflow_type:
          raise ValueError("WORKFLOW_TYPE environment variable is required but not set")

      workflow_type = workflow_type.lower()

      if workflow_type not in ['sip', 'sps-ce', 'capsule-sorting']:
          raise ValueError(f"Invalid WORKFLOW_TYPE '{workflow_type}'. Must be 'sip', 'sps-ce', or 'capsule-sorting'.")

      template_mapping = {
          'sip': 'sip_workflow.yml',
          'sps-ce': 'sps_workflow.yml',
          'capsule-sorting': 'CapsuleSorting_workflow.yml'
      }

      template_filename = template_mapping[workflow_type]
      app_dir = Path(__file__).parent.parent
      template_path = app_dir / "templates" / template_filename

      if not template_path.exists():
          raise FileNotFoundError(f"Workflow template not found: {template_path}")

      return template_path
  ```

- **`validate_workflow_type()`** (line 73): Add `'capsule-sorting'` to the list of valid workflow types.

  **Modification:**
  ```python
  def validate_workflow_type(workflow_type: str) -> bool:
      '''
      Validate if a workflow type is supported.
      '''
      if not workflow_type:
          return False
      return workflow_type.lower() in ['sip', 'sps-ce', 'capsule-sorting']
  ```

### 2.4. `app.py`

- **`get_dynamic_title()`**: Add a condition to return "Capsule Sorting LIMS Workflow Manager" when `WORKFLOW_TYPE` is `'CAPSULE-SORTING'`.

 **Modification:**
 ```python
 def get_dynamic_title() -> str:
     '''
     Generate dynamic title based on WORKFLOW_TYPE environment variable.
     '''
     workflow_type = os.environ.get('WORKFLOW_TYPE', '').strip().upper()

     if workflow_type == 'SIP':
         return "🧪 SIP LIMS Workflow Manager"
     elif workflow_type == 'SPS-CE':
         return "🧪 SPS-CE LIMS Workflow Manager"
     elif workflow_type == 'CAPSULE-SORTING':
         return "🧪 Capsule Sorting LIMS Workflow Manager"
     else:
         return "🧪 SIP LIMS Workflow Manager"
 ```

## 3. Missing Template File Creation

### 3.1. `templates/CapsuleSorting_workflow.yml`

A new workflow template file must be created at `templates/CapsuleSorting_workflow.yml`:

```yaml
workflow_name: "Capsule Sorting"
steps:
 - id: init_project
   name: "1. Initiate Project / Make Sort Labels"
   script: "initiate_project_folder_and_make_sort_plate_labels.py"
   allow_rerun: true

 - id: prep_library
   name: "2. Generate Lib Creation Files"
   script: "generate_lib_creation_files.py"
   allow_rerun: true

 - id: analyze_quality
   name: "3. Analyze FA data"
   script: "capsule_fa_analysis.py"
   allow_rerun: true

 - id: select_plates
   name: "4. Create SPITS file"
   script: "create_capsule_spits.py"
   allow_rerun: false

 - id: process_grid_barcodes
   name: "5. Process Grid Tables & Generate Barcodes"
   script: "process_grid_tables_and_generate_barcodes.py"
   allow_rerun: false
   notes: "Generates Excel barcode scanning template - manual scanning step required before next step"

 - id: verify_scanning_esp
   name: "6. Verify Scanning & Generate ESP Files"
   script: "verify_scanning_and_generate_ESP_files.py"
   allow_rerun: false
   notes: "Mandatory barcode verification - sys.exit() on ANY mismatch detected"
```

## 4. Repository Verification Requirements

### 4.1. Pre-Implementation Verification (CRITICAL)

Before implementing Capsule Sorting support, the following must be verified:

#### Repository Accessibility
- **Repository URL**: Confirm `rrmalmstrom/capsule-single-cell-sort-scripts` exists and is accessible
- **Branch Structure**: Verify proper Git branch organization and default branch
- **Permissions**: Validate read access for script download operations
- **Repository Status**: Confirm repository is active and maintained

#### Script Availability Verification
All six required scripts must exist in the repository:
- `initiate_project_folder_and_make_sort_plate_labels.py`
- `generate_lib_creation_files.py`
- `capsule_fa_analysis.py`
- `create_capsule_spits.py`
- `process_grid_tables_and_generate_barcodes.py`
- `verify_scanning_and_generate_ESP_files.py`

#### Success Marker Integration
All scripts must follow the workflow manager's success marker pattern:
```python
# Required at the end of each successful script
success_dir = Path(".workflow_status")
success_dir.mkdir(exist_ok=True)
success_file = success_dir / f"{Path(__file__).stem}.success"
success_file.touch()
```

### 4.2. Fallback Strategies
If repository verification reveals issues:
- **Repository Inaccessibility**: Implement local script management or alternative repository
- **Missing Scripts**: Coordinate with repository maintainer for script availability
- **Version Mismatches**: Update implementation plan to match available script versions
- **Documentation Gaps**: Create supplementary documentation for workflow manager integration


## 5. Testing and Validation

### 5.1. Required Test Updates

The following test files must be updated to include Capsule Sorting workflow support:

#### 5.1.1. `tests/test_platform_launchers.py`
- Add tests for 3rd workflow option in `interactive_workflow_selection()`
- Validate `validate_workflow_type()` accepts `'capsule-sorting'`
- Test workflow type normalization for various input formats

#### 5.1.2. `tests/test_scripts_updater.py`
- Add tests for `'capsule-sorting'` repository mapping in `WORKFLOW_REPOSITORIES`
- Validate ScriptsUpdater initialization with `'capsule-sorting'` workflow type
- Test script download and update functionality for Capsule Sorting repository

#### 5.1.3. `tests/test_workflow_type_propagation.py`
- Add tests for `'capsule-sorting'` workflow type in `get_workflow_template_path()`
- Test `validate_workflow_type()` function with `'capsule-sorting'` input
- Validate environment variable propagation for Capsule Sorting workflow

#### 5.1.4. `tests/test_app.py`
- Add tests for Capsule Sorting dynamic title in `get_dynamic_title()`
- Validate title generation when `WORKFLOW_TYPE='CAPSULE-SORTING'`

### 5.2. Manual Validation Steps

1. **Launch Application**: Select "Capsule Sorting" workflow from interactive menu
2. **Verify Title**: Confirm application title shows "Capsule Sorting LIMS Workflow Manager"
3. **Create New Project**: Verify `CapsuleSorting_workflow.yml` template is used
4. **Test Script Download**: Confirm scripts download from `capsule-single-cell-sort-scripts` repository
5. **Validate Workflow Steps**: Verify all 6 workflow steps display correctly
6. **Test Success Markers**: Confirm `.workflow_status` directory integration works

## 6. Implementation Priority

### 6.1. Phase 1: Core Integration (Week 1)
1. **Workflow Type Support** - Update all core files to recognize `'capsule-sorting'`
2. **Template File Creation** - Create `templates/CapsuleSorting_workflow.yml`
3. **Repository Verification** - Confirm script repository accessibility and script availability
4. **Basic Testing** - Update test files for third workflow support

### 6.2. Phase 2: Validation and Testing (Week 2)
1. **Integration Testing** - End-to-end workflow validation
2. **Repository Integration** - Test script downloading and execution
3. **Manual Validation** - Complete workflow testing
4. **Documentation Updates** - Update user guides and documentation

## 7. Risk Assessment

### 7.1. High Priority Risks

#### Repository Accessibility Risk
- **Risk**: `capsule-single-cell-sort-scripts` repository may not exist or be inaccessible
- **Impact**: Complete implementation failure, script download failures
- **Mitigation**: Verify repository accessibility before implementation begins

#### Script Availability Risk
- **Risk**: Required scripts may not exist in the repository
- **Impact**: Workflow execution failures, missing functionality
- **Mitigation**: Verify all 6 required scripts exist and follow success marker pattern

#### Template File Risk
- **Risk**: Missing `CapsuleSorting_workflow.yml` template file
- **Impact**: New project creation failures, workflow loading errors
- **Mitigation**: Create template file following existing patterns

### 7.2. Medium Priority Risks

#### Testing Coverage Risk
- **Risk**: Incomplete test coverage for third workflow type
- **Impact**: Undetected regressions, integration issues
- **Mitigation**: Comprehensive test updates across all relevant test files

#### Integration Complexity Risk
- **Risk**: Workflow manager integration may reveal unexpected issues
- **Impact**: Extended development time, potential system instability
- **Mitigation**: Phased implementation approach with thorough testing

### 4.4. Documentation

Coding agents should use the `mcp_context7` tool to get the latest documentation for any libraries or frameworks used in this project.

---

# Implementation Instructions for Coding Agent

This section provides comprehensive, step-by-step implementation instructions for a coding agent to implement the Capsule Sorting workflow integration following Test-Driven Development (TDD) principles.

## 1. Step-by-Step Implementation Approach

### Implementation Philosophy
- **ONE STEP AT A TIME**: Each step focuses on a single file or specific functionality
- **TDD MANDATORY**: Write tests first, implement code second
- **VALIDATION REQUIRED**: Each step must be validated before proceeding
- **CLEAR DEPENDENCIES**: Steps are ordered logically with explicit dependencies

### Progress Reporting Protocol
Before each step, the agent must:
1. **Explain the objective**: What will be accomplished in this step
2. **Justify the necessity**: Why this step is required for the overall goal
3. **Context integration**: How this step fits into the bigger implementation picture
4. **Dependency confirmation**: Verify all prerequisites are met

After each step, the agent must:
1. **Confirm completion**: Explicitly state what was accomplished
2. **Run validation tests**: Execute relevant tests and report results
3. **Integration check**: Verify the change doesn't break existing functionality
4. **Commit checkpoint**: Create a logical commit point for rollback if needed

## 2. TDD Implementation Guidelines

### Red-Green-Refactor Cycle
For each core file modification:

1. **RED**: Write failing tests first
   - Create test cases that define expected behavior
   - Run tests to confirm they fail (proving tests are valid)
   - Document the expected failure message

2. **GREEN**: Implement minimal code to pass tests
   - Write only enough code to make tests pass
   - Avoid over-engineering or premature optimization
   - Focus on meeting the test requirements exactly

3. **REFACTOR**: Improve code while maintaining green tests
   - Clean up implementation without changing behavior
   - Ensure all tests remain passing
   - Improve readability and maintainability

### Test-First Requirements
- **No implementation without tests**: Every code change must have corresponding tests
- **Test coverage validation**: Ensure new functionality is fully tested
- **Regression prevention**: Verify existing tests continue to pass

## 3. Detailed Implementation Steps

### Phase 1: Core Infrastructure Implementation

#### Step 1: Create Workflow Template File
**Objective**: Create [`templates/CapsuleSorting_workflow.yml`](templates/CapsuleSorting_workflow.yml) with the Capsule Sorting workflow definition.

**Prerequisites**: None (foundational step)

**TDD Approach**:
1. **Test First**: Create test in [`tests/test_workflow_type_propagation.py`](tests/test_workflow_type_propagation.py)
   ```python
   def test_capsule_sorting_template_exists():
       """Test that CapsuleSorting_workflow.yml template exists and is valid."""
       template_path = Path("templates/CapsuleSorting_workflow.yml")
       assert template_path.exists(), "CapsuleSorting_workflow.yml template must exist"
       
       with open(template_path, 'r') as f:
           workflow_data = yaml.safe_load(f)
       
       assert workflow_data['workflow_name'] == "Capsule Sorting"
       assert len(workflow_data['steps']) == 6
       
       # Verify all required scripts are defined
       expected_scripts = [
           "initiate_project_folder_and_make_sort_plate_labels.py",
           "generate_lib_creation_files.py",
           "capsule_fa_analysis.py",
           "create_capsule_spits.py",
           "process_grid_tables_and_generate_barcodes.py",
           "verify_scanning_and_generate_ESP_files.py"
       ]
       
       actual_scripts = [step['script'] for step in workflow_data['steps']]
       assert actual_scripts == expected_scripts
   ```

2. **Run Test**: Execute test to confirm it fails
   ```bash
   pytest tests/test_workflow_type_propagation.py::test_capsule_sorting_template_exists -v
   ```

3. **Implement**: Create [`templates/CapsuleSorting_workflow.yml`](templates/CapsuleSorting_workflow.yml) with exact content from plan

4. **Validate**: Re-run test to confirm it passes

**Verification Criteria**:
- [ ] Template file exists at correct path
- [ ] YAML is valid and parseable
- [ ] Contains all 6 required workflow steps
- [ ] Script names match exactly as specified
- [ ] Test passes successfully

---

#### Step 2: Update Workflow Utils for Template Mapping
**Objective**: Update [`src/workflow_utils.py`](src/workflow_utils.py) to support Capsule Sorting template mapping and validation.

**Prerequisites**: Step 1 completed (template file exists)

**TDD Approach**:
1. **Test First**: Add tests to [`tests/test_workflow_type_propagation.py`](tests/test_workflow_type_propagation.py)
   ```python
   def test_get_workflow_template_path_capsule_sorting():
       """Test workflow template path resolution for capsule-sorting."""
       import os
       from src.workflow_utils import get_workflow_template_path
       
       # Set environment variable
       os.environ['WORKFLOW_TYPE'] = 'capsule-sorting'
       
       try:
           template_path = get_workflow_template_path()
           assert template_path.name == 'CapsuleSorting_workflow.yml'
           assert template_path.exists()
       finally:
           # Clean up environment
           if 'WORKFLOW_TYPE' in os.environ:
               del os.environ['WORKFLOW_TYPE']

   def test_validate_workflow_type_capsule_sorting():
       """Test workflow type validation includes capsule-sorting."""
       from src.workflow_utils import validate_workflow_type
       
       assert validate_workflow_type('capsule-sorting') == True
       assert validate_workflow_type('CAPSULE-SORTING') == True
       assert validate_workflow_type('Capsule-Sorting') == True
       assert validate_workflow_type('invalid-workflow') == False
   ```

2. **Run Tests**: Execute tests to confirm they fail
   ```bash
   pytest tests/test_workflow_type_propagation.py::test_get_workflow_template_path_capsule_sorting -v
   pytest tests/test_workflow_type_propagation.py::test_validate_workflow_type_capsule_sorting -v
   ```

3. **Implement**: Update [`src/workflow_utils.py`](src/workflow_utils.py) functions:
   - Modify `get_workflow_template_path()` to include `'capsule-sorting': 'CapsuleSorting_workflow.yml'`
   - Update `validate_workflow_type()` to accept `'capsule-sorting'`
   - Add validation for the new workflow type

4. **Validate**: Re-run tests to confirm they pass

**Verification Criteria**:
- [ ] `get_workflow_template_path()` returns correct path for capsule-sorting
- [ ] `validate_workflow_type()` accepts capsule-sorting variants
- [ ] All existing tests continue to pass
- [ ] New tests pass successfully

---

#### Step 3: Update Scripts Updater Repository Configuration
**Objective**: Update [`src/scripts_updater.py`](src/scripts_updater.py) to include Capsule Sorting repository mapping.

**Prerequisites**: Step 2 completed (workflow utils updated)

**TDD Approach**:
1. **Test First**: Add tests to [`tests/test_scripts_updater.py`](tests/test_scripts_updater.py)
   ```python
   def test_workflow_repositories_includes_capsule_sorting():
       """Test that WORKFLOW_REPOSITORIES includes capsule-sorting mapping."""
       from src.scripts_updater import WORKFLOW_REPOSITORIES
       
       assert 'capsule-sorting' in WORKFLOW_REPOSITORIES
       
       capsule_config = WORKFLOW_REPOSITORIES['capsule-sorting']
       assert capsule_config['repo_name'] == 'capsule-single-cell-sort-scripts'
       assert capsule_config['repo_owner'] == 'rrmalmstrom'

   def test_scripts_updater_initialization_capsule_sorting():
       """Test ScriptsUpdater can be initialized with capsule-sorting workflow."""
       from src.scripts_updater import ScriptsUpdater
       
       # This should not raise an exception
       updater = ScriptsUpdater('capsule-sorting')
       assert updater.workflow_type == 'capsule-sorting'
   ```

2. **Run Tests**: Execute tests to confirm they fail
   ```bash
   pytest tests/test_scripts_updater.py::test_workflow_repositories_includes_capsule_sorting -v
   pytest tests/test_scripts_updater.py::test_scripts_updater_initialization_capsule_sorting -v
   ```

3. **Implement**: Update [`src/scripts_updater.py`](src/scripts_updater.py):
   - Add `'capsule-sorting'` entry to `WORKFLOW_REPOSITORIES` dictionary
   - Ensure ScriptsUpdater class handles the new workflow type

4. **Validate**: Re-run tests to confirm they pass

**Verification Criteria**:
- [ ] `WORKFLOW_REPOSITORIES` contains capsule-sorting mapping
- [ ] Repository configuration points to correct GitHub repository
- [ ] ScriptsUpdater initializes successfully with capsule-sorting
- [ ] All existing functionality remains intact

---

#### Step 4: Update Launcher Workflow Selection and Validation
**Objective**: Update [`launcher/run.py`](launcher/run.py) to support Capsule Sorting workflow selection and implement critical validation fixes.

**Prerequisites**: Steps 1-3 completed (infrastructure ready)

**TDD Approach**:
1. **Test First**: Add tests to [`tests/test_platform_launchers.py`](tests/test_platform_launchers.py)
   ```python
   def test_interactive_workflow_selection_capsule_sorting():
       """Test interactive workflow selection includes capsule-sorting option."""
       from unittest.mock import patch
       from launcher.run import interactive_workflow_selection
       
       # Mock user input selecting option 3
       with patch('click.prompt', return_value='3'):
           result = interactive_workflow_selection()
           assert result == 'capsule-sorting'

   def test_validate_workflow_type_capsule_sorting():
       """Test validate_workflow_type accepts capsule-sorting and variants."""
       from launcher.run import validate_workflow_type
       
       assert validate_workflow_type('capsule-sorting') == 'capsule-sorting'
       assert validate_workflow_type('CAPSULE-SORTING') == 'capsule-sorting'
       assert validate_workflow_type('capsule_sorting') == 'capsule-sorting'

   def test_validate_workflow_type_strict_validation():
       """Test that validate_workflow_type has strict validation (no fallback)."""
       from launcher.run import validate_workflow_type
       import pytest
       
       with pytest.raises(SystemExit):
           validate_workflow_type('invalid-workflow')
       
       with pytest.raises(SystemExit):
           validate_workflow_type('')
       
       with pytest.raises(SystemExit):
           validate_workflow_type(None)
   ```

2. **Run Tests**: Execute tests to confirm they fail
   ```bash
   pytest tests/test_platform_launchers.py::test_interactive_workflow_selection_capsule_sorting -v
   pytest tests/test_platform_launchers.py::test_validate_workflow_type_capsule_sorting -v
   pytest tests/test_platform_launchers.py::test_validate_workflow_type_strict_validation -v
   ```

3. **Implement**: Update [`launcher/run.py`](launcher/run.py):
   - Modify `interactive_workflow_selection()` to include option 3 for Capsule Sorting
   - **CRITICAL**: Replace `validate_workflow_type()` with strict validation (no fallback to 'sip')
   - Add proper error handling and sys.exit() for invalid inputs

4. **Validate**: Re-run tests to confirm they pass

**Verification Criteria**:
- [ ] Interactive selection offers 3 workflow options
- [ ] Option 3 correctly returns 'capsule-sorting'
- [ ] `validate_workflow_type()` accepts all capsule-sorting variants
- [ ] **CRITICAL**: No dangerous fallback to 'sip' for invalid inputs
- [ ] Proper error messages and sys.exit() for invalid workflows

---

#### Step 5: Update App Dynamic Title Generation
**Objective**: Update [`app.py`](app.py) to generate appropriate title for Capsule Sorting workflow.

**Prerequisites**: Steps 1-4 completed (workflow type support implemented)

**TDD Approach**:
1. **Test First**: Add tests to [`tests/test_app.py`](tests/test_app.py)
   ```python
   def test_get_dynamic_title_capsule_sorting():
       """Test dynamic title generation for Capsule Sorting workflow."""
       import os
       from app import get_dynamic_title
       
       # Test capsule-sorting title
       os.environ['WORKFLOW_TYPE'] = 'CAPSULE-SORTING'
       try:
           title = get_dynamic_title()
           assert title == "🧪 Capsule Sorting LIMS Workflow Manager"
       finally:
           if 'WORKFLOW_TYPE' in os.environ:
               del os.environ['WORKFLOW_TYPE']
       
       # Test case insensitivity
       os.environ['WORKFLOW_TYPE'] = 'capsule-sorting'
       try:
           title = get_dynamic_title()
           assert title == "🧪 Capsule Sorting LIMS Workflow Manager"
       finally:
           if 'WORKFLOW_TYPE' in os.environ:
               del os.environ['WORKFLOW_TYPE']
   ```

2. **Run Tests**: Execute tests to confirm they fail
   ```bash
   pytest tests/test_app.py::test_get_dynamic_title_capsule_sorting -v
   ```

3. **Implement**: Update [`app.py`](app.py):
   - Modify `get_dynamic_title()` to handle `'CAPSULE-SORTING'` workflow type
   - Return "🧪 Capsule Sorting LIMS Workflow Manager" for capsule-sorting

4. **Validate**: Re-run tests to confirm they pass

**Verification Criteria**:
- [ ] Dynamic title correctly generated for CAPSULE-SORTING
- [ ] Case insensitivity handled properly
- [ ] Existing workflow titles remain unchanged
- [ ] All app.py tests continue to pass

---

### Phase 2: Testing & Validation

#### Step 6: Comprehensive Test Suite Updates
**Objective**: Update all relevant test files to ensure comprehensive coverage of Capsule Sorting functionality.

**Prerequisites**: Phase 1 completed (all core files updated)

**Test Files to Update**:

1. **[`tests/test_workflow_type_propagation.py`](tests/test_workflow_type_propagation.py)**:
   - Environment variable propagation tests
   - Template path resolution tests
   - Workflow type validation tests

2. **[`tests/test_scripts_updater.py`](tests/test_scripts_updater.py)**:
   - Repository mapping tests
   - ScriptsUpdater initialization tests
   - Script download functionality tests

3. **[`tests/test_platform_launchers.py`](tests/test_platform_launchers.py)**:
   - Interactive workflow selection tests
   - Workflow type validation tests
   - Error handling tests

4. **[`tests/test_app.py`](tests/test_app.py)**:
   - Dynamic title generation tests
   - Environment variable handling tests

**Implementation Approach**:
1. **Audit existing tests**: Review current test coverage for workflow type handling
2. **Add missing tests**: Create tests for all new Capsule Sorting functionality
3. **Update existing tests**: Modify tests that enumerate workflow types
4. **Validate coverage**: Ensure all code paths are tested

**Verification Criteria**:
- [ ] All new functionality has corresponding tests
- [ ] Existing tests updated to include capsule-sorting
- [ ] Test coverage maintained or improved
- [ ] All tests pass successfully

---

#### Step 7: Integration Testing
**Objective**: Run comprehensive test suite and validate end-to-end functionality.

**Prerequisites**: Step 6 completed (all tests updated)

**Testing Protocol**:
1. **Unit Test Execution**:
   ```bash
   # Run all tests
   pytest -v
   
   # Run specific test categories
   pytest tests/test_workflow_type_propagation.py -v
   pytest tests/test_scripts_updater.py -v
   pytest tests/test_platform_launchers.py -v
   pytest tests/test_app.py -v
   ```

2. **Integration Test Scenarios**:
   - Workflow selection through interactive menu
   - Template file loading and parsing
   - Repository configuration validation
   - Dynamic title generation

3. **Regression Testing**:
   - Verify existing SIP workflow functionality
   - Verify existing SPS-CE workflow functionality
   - Confirm no breaking changes introduced

**Verification Criteria**:
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] No regressions in existing functionality
- [ ] Test coverage reports acceptable levels

---

#### Step 8: Manual Validation Testing
**Objective**: Perform manual end-to-end validation of Capsule Sorting workflow integration.

**Prerequisites**: Step 7 completed (automated tests passing)

**Manual Test Scenarios**:

1. **Workflow Selection Validation**:
   ```bash
   # Launch application and test interactive selection
   python launcher/run.py
   # Select option 3 (Capsule Sorting)
   # Verify correct workflow type is set
   ```

2. **Title Generation Validation**:
   - Confirm application title shows "🧪 Capsule Sorting LIMS Workflow Manager"
   - Verify title updates correctly based on workflow selection

3. **Template Loading Validation**:
   - Create new project with Capsule Sorting workflow
   - Verify `CapsuleSorting_workflow.yml` template is used
   - Confirm all 6 workflow steps are displayed correctly

4. **Repository Integration Validation**:
   - Test script download functionality (if repository is accessible)
   - Verify correct repository URL is used
   - Confirm script management works properly

**Verification Criteria**:
- [ ] Interactive workflow selection works correctly
- [ ] Dynamic title generation functions properly
- [ ] Template file loading succeeds
- [ ] Repository integration functions (if accessible)
- [ ] All workflow steps display correctly
- [ ] No errors or exceptions during normal operation

---

### Phase 3: Manual Step Integration (Future Implementation)

#### Step 9: Manual Step UI/UX Design (Placeholder)
**Objective**: Design and plan manual step integration for future implementation.

**Prerequisites**: Phases 1-2 completed (core functionality working)

**Design Considerations**:
- Manual barcode scanning step integration
- User interface for manual step completion
- Validation and verification workflows
- Safety gates and error handling

**Implementation Status**: **PLACEHOLDER FOR FUTURE DEVELOPMENT**

This step is included for completeness but is not part of the current implementation scope. The Capsule Sorting workflow includes manual steps that will require additional UI/UX development in future iterations.

---

## 4. Safety and Validation Requirements

### Verification Criteria for Each Step
Every implementation step must meet these criteria before proceeding:

1. **Functional Verification**:
   - All tests pass successfully
   - No new test failures introduced
   - Functionality works as specified

2. **Integration Verification**:
   - Existing functionality remains intact
   - No breaking changes to other workflows
   - Proper error handling implemented

3. **Code Quality Verification**:
   - Code follows project conventions
   - Proper documentation included
   - No security vulnerabilities introduced

### Rollback Instructions
If any step fails:

1. **Immediate Actions**:
   - Stop implementation immediately
   - Document the failure and error messages
   - Revert changes using git reset or checkout

2. **Failure Analysis**:
   - Identify root cause of failure
   - Determine if issue is in implementation or requirements
   - Plan corrective action

3. **Recovery Process**:
   - Fix identified issues
   - Re-run tests to confirm fix
   - Resume implementation from failed step

### Integration Testing Between Steps
After every 2-3 steps:

1. **Cross-Step Validation**:
   - Run full test suite
   - Verify integration between modified components
   - Test end-to-end workflow functionality

2. **Regression Testing**:
   - Confirm existing workflows still function
   - Verify no unintended side effects
   - Test edge cases and error conditions

### Final End-to-End Validation
Before considering implementation complete:

1. **Complete Workflow Test**:
   - Test full Capsule Sorting workflow selection
   - Verify all 6 steps display correctly
   - Confirm proper template loading

2. **Multi-Workflow Validation**:
   - Test switching between all three workflow types
   - Verify each workflow maintains its functionality
   - Confirm no cross-contamination between workflows

3. **Error Condition Testing**:
   - Test invalid workflow type handling
   - Verify proper error messages
   - Confirm graceful failure modes

---

## 5. Communication Protocol for Coding Agent

### Before Each Step Protocol
The coding agent must:

1. **State the objective clearly**:
   ```
   "I am about to implement Step X: [Objective]
   This step will modify [specific files] to [specific changes]
   This is necessary because [justification]"
   ```

2. **Confirm prerequisites**:
   ```
   "Prerequisites check:
   - Step X-1: ✅ Completed and validated
   - Required files: ✅ Accessible
   - Test environment: ✅ Ready"
   ```

3. **Explain the approach**:
   ```
   "Implementation approach:
   1. Write tests for [specific functionality]
   2. Run tests to confirm they fail
   3. Implement [specific changes]
   4. Validate tests pass
   5. Run integration tests"
   ```

### After Each Step Protocol
The coding agent must:

1. **Confirm completion**:
   ```
   "Step X completed successfully:
   - Tests written: ✅ [number] new tests
   - Implementation: ✅ [specific changes made]
   - Validation: ✅ All tests passing"
   ```

2. **Report test results**:
   ```
   "Test Results:
   - New tests: [X/X] passing
   - Existing tests: [Y/Y] passing
   - Coverage: [Z%] maintained/improved"
   ```

3. **Integration status**:
   ```
   "Integration Status:
   - No breaking changes detected
   - All workflows functioning correctly
   - Ready to proceed to next step"
   ```

### Issue Escalation Protocol
If any issues arise, the agent must:

1. **Immediate notification**:
   ```
   "⚠️ ISSUE DETECTED in Step X:
   Error: [specific error message]
   Impact: [description of impact]
   Requesting permission to proceed with troubleshooting"
   ```

2. **Wait for permission**: Do not proceed without explicit approval

3. **Provide options**:
   ```
   "Proposed resolution options:
   1. [Option 1 with pros/cons]
   2. [Option 2 with pros/cons]
   3. Rollback to previous step
   Which option should I pursue?"
   ```

---

## 6. Documentation and Context Requirements

### MCP Context7 Tool Usage
The coding agent should use the `mcp_context7` tool when:

1. **Library Documentation Needed**:
   - Working with YAML parsing libraries
   - Using pytest testing frameworks
   - Implementing click CLI functionality
   - Working with pathlib or file operations

2. **Best Practices Research**:
   - TDD implementation patterns
   - Python testing best practices
   - Configuration file management
   - Error handling strategies

3. **Framework-Specific Questions**:
   - Pytest fixture usage
   - Click command line interface patterns
   - YAML configuration best practices

### Code Documentation Requirements
All new code must include:

1. **Function Documentation**:
   ```python
   def function_name(param: type) -> return_type:
       """
       Brief description of function purpose.
       
       Args:
           param: Description of parameter
           
       Returns:
           Description of return value
           
       Raises:
           ExceptionType: Description of when exception is raised
       """
   ```

2. **Inline Comments**:
   - Explain complex logic
   - Document business rules
   - Clarify non-obvious implementations

3. **Test Documentation**:
   ```python
   def test_function_name():
       """Test description explaining what is being tested and why."""
   ```

### File Path Documentation
All file references must be documented as clickable links:

- Configuration files: [`templates/CapsuleSorting_workflow.yml`](templates/CapsuleSorting_workflow.yml)
- Source files: [`src/workflow_utils.py`](src/workflow_utils.py)
- Test files: [`tests/test_workflow_type_propagation.py`](tests/test_workflow_type_propagation.py)
- Launcher files: [`launcher/run.py`](launcher/run.py)

### Code Snippets and Examples
All code modifications must include:

1. **Exact code snippets** with proper syntax highlighting
2. **Line number references** where applicable
3. **Before/after comparisons** for modifications
4. **Complete function implementations** (no partial code)

---

## 7. Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] **Step 1**: Create [`templates/CapsuleSorting_workflow.yml`](templates/CapsuleSorting_workflow.yml)
  - [ ] Write tests first
  - [ ] Implement template file
  - [ ] Validate tests pass
  - [ ] Verify YAML structure

- [ ] **Step 2**: Update [`src/workflow_utils.py`](src/workflow_utils.py)
  - [ ] Write tests for template mapping
  - [ ] Write tests for validation function
  - [ ] Implement template mapping
  - [ ] Implement validation updates
  - [ ] Validate all tests pass

- [ ] **Step 3**: Update [`src/scripts_updater.py`](src/scripts_updater.py)
  - [ ] Write tests for repository mapping
  - [ ] Write tests for ScriptsUpdater initialization
  - [ ] Implement repository configuration
  - [ ] Validate functionality

- [ ] **Step 4**: Update [`launcher/run.py`](launcher/run.py)
  - [ ] Write tests for interactive selection
  - [ ] Write tests for strict validation
  - [ ] Implement workflow selection updates
  - [ ] **CRITICAL**: Implement strict validation (no fallback)
  - [ ] Validate error handling

- [ ] **Step 5**: Update [`app.py`](app.py)
  - [ ] Write tests for dynamic title
  - [ ] Implement title generation
  - [ ] Validate case handling

### Phase 2: Testing & Validation
- [ ] **Step 6**: Update comprehensive test suite
  - [ ] Update [`tests/test_workflow_type_propagation.py`](tests/test_workflow_type_propagation.py)
  - [ ] Update [`tests/test_scripts_updater.py`](tests/test_scripts_updater.py)
  - [ ] Update [`tests/test_platform_launchers.py`](tests/test_platform_launchers.py)
  - [ ] Update [`tests/test_app.py`](tests/test_app.py)
  - [ ] Validate test coverage

- [ ] **Step 7**: Integration testing
  - [ ] Run full test suite
  - [ ] Validate no regressions
  - [ ] Test cross-component integration
  - [ ] Verify error handling

- [ ] **Step 8**: Manual validation
  - [ ] Test interactive workflow selection
  - [ ] Verify dynamic title generation
  - [ ] Test template loading
  - [ ] Validate end-to-end functionality

### Phase 3: Future Planning
- [ ] **Step 9**: Manual step integration design (placeholder)
  - [ ] Document manual step requirements
  - [ ] Plan UI/UX integration
  - [ ] Design safety gates
  - [ ] Create future implementation roadmap

---

## 8. Success Criteria

### Implementation Success Metrics
The implementation is considered successful when:

1. **Functional Requirements Met**:
   - [ ] All 3 workflow types selectable via interactive menu
   - [ ] Capsule Sorting template loads correctly
   - [ ] Dynamic title generation works for all workflows
   - [ ] Repository configuration supports capsule-sorting
   - [ ] All 6 Capsule Sorting steps display correctly

2. **Quality Requirements Met**:
   - [ ] All tests pass (100% success rate)
   - [ ] No regressions in existing functionality
   - [ ] Code coverage maintained or improved
   - [ ] All safety validations implemented

3. **Integration Requirements Met**:
   - [ ] Seamless switching between workflow types
   - [ ] Proper error handling for invalid inputs
   - [ ] **CRITICAL**: No dangerous fallback behaviors
   - [ ] Consistent user experience across workflows

4. **Documentation Requirements Met**:
   - [ ] All code properly documented
   - [ ] Test cases clearly described
   - [ ] Implementation steps recorded
   - [ ] Future enhancement plans documented

### Acceptance Criteria
Before marking implementation complete:

1. **Technical Validation**:
   - All automated tests pass
   - Manual testing scenarios successful
   - No critical or high-severity issues
   - Performance impact acceptable

2. **User Experience Validation**:
   - Intuitive workflow selection
   - Clear error messages
   - Consistent interface behavior
   - Proper visual feedback

3. **Safety Validation**:
   - No accidental workflow execution
   - Proper input validation
   - Graceful error handling
   - Secure configuration management

---

This comprehensive implementation guide provides the coding agent with a complete roadmap for implementing Capsule Sorting workflow support while maintaining the highest standards of code quality, testing coverage, and user safety.
