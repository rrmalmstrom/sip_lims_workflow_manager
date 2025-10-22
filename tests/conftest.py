import pytest

# This file will contain shared fixtures for pytest.
# For example, fixtures to create temporary project structures.

@pytest.fixture
def tmp_project_path(tmp_path):
    """Creates a temporary project directory structure."""
    project_dir = tmp_path / "sip_lims_workflow_manager"
    project_dir.mkdir()
    (project_dir / "config").mkdir()
    return project_dir