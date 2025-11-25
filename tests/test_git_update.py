import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.git_update_manager import create_update_managers, detect_script_repository_config, GitUpdateManager

def test_create_manager_for_dev_scripts(tmp_path):
    """
    Tests that the factory function creates a manager for the dev scripts repo.
    """
    # ARRANGE
    dev_scripts_path = tmp_path / "sip_scripts_dev"
    dev_scripts_path.mkdir()

    # ACT
    managers = create_update_managers(script_path=dev_scripts_path)
    manager = managers["scripts"]

    # ASSERT
    assert manager.repo_path == dev_scripts_path
    assert "sip_scripts_workflow_gui" in manager.config["repo_url"]

def test_create_manager_for_prod_scripts(tmp_path):
    """
    Tests that the factory function creates a manager for the prod scripts repo.
    """
    # ARRANGE
    prod_scripts_path = tmp_path / "sip_scripts_production"
    prod_scripts_path.mkdir()

    # ACT
    managers = create_update_managers(script_path=prod_scripts_path)
    manager = managers["scripts"]

    # ASSERT
    assert manager.repo_path == prod_scripts_path
    assert "sip_scripts_workflow_gui" in manager.config["repo_url"]  # Both use same repo URL now

def test_create_manager_app_unaffected(tmp_path):
    """
    Tests that the app update manager is not affected by script_path.
    """
    # ARRANGE
    app_path = tmp_path / "sip_lims_workflow_manager"
    app_path.mkdir()

    # ACT
    # Pass a script_path to ensure it's ignored for 'application' type
    managers = create_update_managers(base_path=app_path, script_path=tmp_path / "some_other_path")
    manager = managers["app"]

    # ASSERT
    assert manager.repo_path == app_path
    assert "sip_lims_workflow_manager" in manager.config["repo_url"]

def test_detect_repo_config():
    """Tests the repository configuration detection logic."""
    dev_path = Path("/some/path/sip_scripts_dev")
    prod_path = Path("/some/path/sip_scripts_production")
    other_path = Path("/some/path/other_scripts")

    dev_config = detect_script_repository_config(dev_path)
    prod_config = detect_script_repository_config(prod_path)
    other_config = detect_script_repository_config(other_path)

    assert "sip_scripts_workflow_gui" in dev_config["repo_url"]
    assert "sip_scripts_workflow_gui" in prod_config["repo_url"]  # Both use same repo URL now
    # Default case
    assert "sip_scripts_workflow_gui" in other_config["repo_url"]