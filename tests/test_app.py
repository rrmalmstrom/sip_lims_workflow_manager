import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# This is a bit of a hack to allow importing app.py
# which is not a module.
with patch("streamlit.set_page_config"):
    with patch("streamlit.title"):
        with patch("streamlit.sidebar"):
             with patch("streamlit.expander"):
                from app import parse_script_path_argument

def test_argument_parser_with_script_path(tmp_path):
    """
    Tests that the argument parser correctly handles the --script-path argument.
    """
    # ARRANGE
    scripts_dir = tmp_path / "external_scripts"
    scripts_dir.mkdir()
    test_args = ["app.py", "--script-path", str(scripts_dir)]

    # ACT
    with patch.object(sys, "argv", test_args):
        parsed_path = parse_script_path_argument()

    # ASSERT
    assert parsed_path == scripts_dir

def test_argument_parser_no_script_path():
    """
    Tests that the argument parser defaults to 'scripts' when no path is provided.
    """
    # ARRANGE
    test_args = ["app.py"]

    # ACT
    with patch.object(sys, "argv", test_args):
        parsed_path = parse_script_path_argument()

    # ASSERT
    assert parsed_path == Path("scripts")

def test_argument_parser_invalid_path(tmp_path):
    """
    Tests that the argument parser falls back to the default 'scripts'
    directory when an invalid path is provided.
    """
    # ARRANGE
    invalid_path = tmp_path / "non_existent_scripts"
    test_args = ["app.py", "--script-path", str(invalid_path)]

    # ACT
    with patch.object(sys, "argv", test_args):
        parsed_path = parse_script_path_argument()

    # ASSERT
    assert parsed_path == Path("scripts")