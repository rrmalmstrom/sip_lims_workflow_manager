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
5.  `make_ESP_smear_analysis_file.py`: Creates smear analysis files for the ESP system.
6.  `relabel_lib_plates_for_pooling.py`: Generates labels for relabeling plates for pooling.

### 1.4. Local Script Location

The "Capsule Sorting" scripts will be downloaded to and managed in the following local directory:

`~/.sip_lims_workflow_manager/capsule-sorting_scripts`


Each of the six "Capsule Sorting" Python scripts must be modified to create a success marker file upon successful completion. This is a critical integration point for the workflow manager.

The marker file should be created at `.workflow_status/<script_name>.success`.

#### Example Implementation:

```python
import sys
from pathlib import Path
from datetime import datetime

def create_success_marker():
    """Create success marker file for workflow manager integration."""
    script_name = Path(__file__).stem
    status_dir = Path(".workflow_status")
    status_dir.mkdir(exist_ok=True)
    success_file = status_dir / f"{script_name}.success"
    
    try:
        with open(success_file, "w") as f:
            f.write(f"SUCCESS: {script_name} completed at {datetime.now()}\n")
        print(f"✅ Success marker created: {success_file}")
    except Exception as e:
        print(f"❌ ERROR: Could not create success marker: {e}")
        print("Script failed - workflow manager integration requires success marker")
        sys.exit()
```


### 1.2. Workflow Configuration File (`CapsuleSorting_workflow.yml`)

A new workflow configuration file, `templates/CapsuleSorting_workflow.yml`, will be created. workflow_name: "Capsule Sorting"
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

  - id: integrate_esp
    name: "5. Generate ESP File"
    script: "make_ESP_smear_analysis_file.py"
    allow_rerun: false

  - id: relabel_plates
    name: "6. Relabel Plates for Pooling"
    script: "relabel_lib_plates_for_pooling.py"
    allow_rerun: false

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

- **`validate_workflow_type()`**: Add `'capsule-sorting'` to the list of valid workflow types.

  **Modification:**
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
          sys.exit(1)
  ```

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

- **`get_workflow_template_path()`**: Add `'capsule-sorting': 'CapsuleSorting_workflow.yml'` to the `template_mapping` dictionary.

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

- **`validate_workflow_type()`**: Add `'capsule-sorting'` to the list of valid workflow types.

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


## 4. Testing and Validation

To ensure the new "Capsule Sorting" workflow is implemented correctly and does not introduce any regressions, the following testing and validation strategy must be followed.

### 4.1. Test-Driven Development (TDD)

The coding agent must adopt a TDD approach. For each modification made to the existing codebase, a corresponding test must be created or updated to validate the change. New tests must be created for any new functions or classes.

-   **`launcher/run.py`**: New tests must be added to `tests/test_platform_launchers.py` to validate the new workflow selection and validation logic.
-   **`src/scripts_updater.py`**: The tests in `tests/test_scripts_updater.py` must be updated to include the new "Capsule Sorting" workflow and its repository.
-   **`src/workflow_utils.py`**: The tests in `tests/test_workflow_type_propagation.py` must be updated to validate the new "Capsule Sorting" workflow type.
-   **`app.py`**: New tests must be added to `tests/test_app.py` to validate the new dynamic title for the "Capsule Sorting" workflow.

### 4.2. Manual Validation

Once the automated tests are passing, you will perform manual validation to ensure the new workflow is working as expected. The following steps should be performed:

1.  **Launch the application** and select the "Capsule Sorting" workflow.
2.  **Verify the title** of the application is "Capsule Sorting LIMS Workflow Manager".
3.  **Create a new project** and verify that the `CapsuleSorting_workflow.yml` file is created correctly.
4.  **Run each step** of the "Capsule Sorting" workflow, verifying that each script completes successfully and that the UI updates accordingly.
5.  **Verify the success markers** are created in the `.workflow_status` directory after each step.
6.  **Test the `allow_rerun` functionality** for the steps where it is enabled.
7.  **Test the undo functionality** to ensure it correctly rolls back the workflow state.

### 4.4. Documentation

Coding agents should use the `mcp_context7` tool to get the latest documentation for any libraries or frameworks used in this project.
