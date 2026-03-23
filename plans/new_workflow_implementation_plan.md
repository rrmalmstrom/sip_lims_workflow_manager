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
