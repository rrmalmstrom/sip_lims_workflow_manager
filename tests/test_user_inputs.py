import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import yaml

from src.core import Project

class TestUserInput(unittest.TestCase):

    def setUp(self):
        self.test_project_path = Path("test_project_for_inputs")
        # Remove directory if it exists, then create it
        if self.test_project_path.exists():
            shutil.rmtree(self.test_project_path)
        self.test_project_path.mkdir()
        
        # The script runner looks for scripts in the main `scripts` directory
        self.scripts_path = Path("scripts")
        self.scripts_path.mkdir(exist_ok=True)

        # Create a dummy script in the main scripts directory
        self.script_path = self.scripts_path / "dummy_script.py"
        with open(self.script_path, "w") as f:
            f.write("import sys\n")
            f.write("print(f'Arguments: {sys.argv[1:]}')\n")

        # Create a workflow.yml with inputs
        self.workflow_data = {
            "workflow_name": "Test Workflow",
            "steps": [
                {
                    "id": "step_with_inputs",
                    "name": "Step with Inputs",
                    "script": "dummy_script.py",
                    "snapshot_items": [],
                    "inputs": [
                        {"type": "file", "name": "Input File 1", "arg": "--file1"},
                        {"type": "file", "name": "Input File 2", "arg": ""}
                    ]
                }
            ]
        }
        with open(self.test_project_path / "workflow.yml", "w") as f:
            yaml.dump(self.workflow_data, f)

    def tearDown(self):
        # Clean up the dummy script first
        if self.script_path.exists():
            self.script_path.unlink()
        # Clean up test project directory with more robust cleanup
        if self.test_project_path.exists():
            shutil.rmtree(self.test_project_path, ignore_errors=True)

    @patch('subprocess.Popen')
    def test_run_step_with_user_inputs(self, mock_popen):
        # Arrange
        project = Project(self.test_project_path)
        step_id = "step_with_inputs"
        user_inputs = {
            f"{step_id}_input_0": "/path/to/file1.txt",
            f"{step_id}_input_1": "/path/to/file2.txt"
        }
        
        # Act
        project.run_step(step_id, user_inputs=user_inputs)

        # Assert
        mock_popen.assert_called_once()
        call_args, call_kwargs = mock_popen.call_args
        command = call_args[0]

        # Check that the command contains the script path and arguments
        self.assertIn("dummy_script.py", str(command))
        self.assertIn("--file1", str(command))
        self.assertIn("/path/to/file1.txt", str(command))
        self.assertIn("/path/to/file2.txt", str(command))

if __name__ == '__main__':
    unittest.main()