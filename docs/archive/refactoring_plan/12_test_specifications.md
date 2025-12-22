# 12 - Test Specifications for TDD Approach

## Overview
This document outlines the test specifications for the refactoring effort, following a Test-Driven Development (TDD) approach. Since no existing test suite was found, this plan will also establish a foundational testing structure for the project using `pytest`.

## Testing Framework and Structure
- **Framework**: `pytest` (as indicated by `pytest.ini`).
- **Test Directory**: A new `tests/` directory will be created in the project root.
- **File Naming**: Test files will be named `test_*.py` (e.g., `test_core.py`).
- **Test Functions**: Test functions will be named `test_*`.
- **Fixtures**: `pytest` fixtures will be used for setting up test conditions (e.g., creating temporary files and directories). These will be located in `tests/conftest.py`.

### Proposed Test Directory Structure
```
sip_lims_workflow_manager/
├── tests/
│   ├── conftest.py         # Fixtures and test setup helpers
│   ├── test_app.py         # Tests for app.py logic
│   ├── test_core.py        # Tests for src/core.py
│   ├── test_git_update.py  # Tests for src/git_update_manager.py
│   └── test_scripts.py     # Integration tests for shell scripts
└── ...
```

## Test Specifications

### 1. Test Suite for `config/developer.marker` System
**File**: `tests/test_scripts.py`

-   **`test_dev_mode_detection`**:
    -   **Given**: A temporary `config/developer.marker` file is created.
    -   **When**: The `detect_mode` function in the shell scripts is executed.
    -   **Then**: The function must return "developer".

-   **`test_prod_mode_detection`**:
    -   **Given**: The `config/developer.marker` file does not exist.
    -   **When**: The `detect_mode` function in the shell scripts is executed.
    -   **Then**: The function must return "production".

### 2. Test Suite for `setup` Scripts
**File**: `tests/test_scripts.py`

-   **`test_setup_dev_mode_online`**:
    -   **Given**: Developer mode is active. The user is simulated to select "online" mode.
    -   **When**: The `setup.command`/`setup.bat` script is run.
    -   **Then**: The script must attempt to clone/pull both `sip_scripts_prod` and `sip_scripts_dev` repositories.

-   **`test_setup_dev_mode_offline`**:
    -   **Given**: Developer mode is active. The user is simulated to select "offline" mode.
    -   **When**: The `setup.command`/`setup.bat` script is run.
    -   **Then**: The script must **not** perform any `git clone` or `git pull` operations.

-   **`test_setup_prod_mode`**:
    -   **Given**: Production mode is active.
    -   **When**: The `setup.command`/`setup.bat` script is run.
    -   **Then**: The script must automatically attempt to clone/pull only the `sip_scripts_prod` repository.

### 3. Test Suite for `run` Scripts
**File**: `tests/test_scripts.py`

-   **`test_run_dev_mode_select_dev_scripts`**:
    -   **Given**: Developer mode is active. The user is simulated to select "development scripts".
    -   **When**: The `run.command`/`run.bat` script is run.
    -   **Then**: The `streamlit run` command must be called with the `--script-path` argument pointing to `../sip_scripts_dev`.

-   **`test_run_dev_mode_select_prod_scripts`**:
    -   **Given**: Developer mode is active. The user is simulated to select "production scripts".
    -   **When**: The `run.command`/`run.bat` script is run.
    -   **Then**: The `streamlit run` command must be called with the `--script-path` argument pointing to `../sip_scripts_prod`.

-   **`test_run_prod_mode`**:
    -   **Given**: Production mode is active.
    -   **When**: The `run.command`/`run.bat` script is run.
    -   **Then**: The `streamlit run` command must be automatically called with the `--script-path` argument pointing to `../sip_scripts_prod`.

### 4. Test Suite for `app.py` Modifications
**File**: `tests/test_app.py`

-   **`test_argument_parser_with_script_path`**:
    -   **Given**: The application is launched with `--script-path ../some/path`.
    -   **When**: `parse_script_path_argument()` is called.
    -   **Then**: The function must return a `Path` object equivalent to `../some/path`.

-   **`test_argument_parser_no_script_path`**:
    -   **Given**: The application is launched without a `--script-path` argument.
    -   **When**: `parse_script_path_argument()` is called.
    -   **Then**: The function must return the default `Path('scripts')`.

### 5. Test Suite for `src/core.py` Modifications
**File**: `tests/test_core.py`

-   **`test_project_init_with_external_script_path`**:
    -   **Given**: A `Project` is instantiated with an external `script_path`.
    -   **When**: The `Project` object is created.
    -   **Then**: `project.script_path` must match the external path, and `project.script_runner.script_path` must also match.

-   **`test_project_init_no_script_path`**:
    -   **Given**: A `Project` is instantiated without a `script_path`.
    -   **When**: The `Project` object is created.
    -   **Then**: `project.script_path` must default to `project_path / 'scripts'`.

-   **`test_script_execution_uses_correct_context`**:
    -   **Given**: A `Project` with an external `script_path`.
    -   **When**: `project.run_step()` is called.
    -   **Then**: The `ScriptRunner` must be invoked to run the script from the external `script_path`, but the script's working directory must be the `project_path`.

### 6. Test Suite for `src/git_update_manager.py` Refactoring
**File**: `tests/test_git_update.py`

-   **`test_create_manager_for_dev_scripts`**:
    -   **Given**: `create_update_manager` is called for `repo_type="scripts"` with a `script_path` pointing to the development scripts repository.
    -   **When**: The `GitUpdateManager` is created.
    -   **Then**: The manager's configuration must use the `sip_scripts_dev` repository URL.

-   **`test_create_manager_for_prod_scripts`**:
    -   **Given**: `create_update_manager` is called for `repo_type="scripts"` with a `script_path` pointing to the production scripts repository.
    -   **When**: The `GitUpdateManager` is created.
    -   **Then**: The manager's configuration must use the `sip_scripts_prod` repository URL.

-   **`test_app_update_manager_unaffected`**:
    -   **Given**: `create_update_manager` is called for `repo_type="application"`.
    -   **When**: The `GitUpdateManager` is created.
    -   **Then**: The manager's configuration must use the main `sip_lims_workflow_manager` repository URL, regardless of any `script_path`.

## Test Implementation Notes
-   **Mocking**: `subprocess.run`, `requests.get`, and user input (`read`) will be mocked using `pytest`'s `monkeypatch` fixture to isolate tests from external dependencies and user interaction.
-   **Filesystem**: The `pyfakefs` library or `pytest`'s `tmp_path` fixture will be used to create a virtual filesystem for testing file creation, deletion, and path logic without affecting the actual disk.
-   **Fixtures (`tests/conftest.py`)**:
    -   `dev_mode_project`: A fixture to create a temporary project structure with the `developer.marker` file.
    -   `prod_mode_project`: A fixture to create a temporary project structure without the marker file.
    -   `mock_repositories`: A fixture to create fake local git repositories for testing `git pull` and `git clone` logic.

This test plan provides a robust TDD framework for implementing the required changes, ensuring that each new piece of logic is covered by a test and that existing functionality is not broken.