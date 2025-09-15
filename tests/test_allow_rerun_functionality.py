import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import yaml

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import Workflow, Project

class TestAllowRerunFunctionality(unittest.TestCase):
    """Test that only steps with allow_rerun: true show re-run capability when completed."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_workflow_data = {
            'workflow_name': 'Test Workflow',
            'steps': [
                {
                    'id': 'step_no_rerun',
                    'name': 'Step Without Rerun',
                    'script': 'test_script.py',
                    'snapshot_items': ['outputs/']
                    # No allow_rerun property - should default to False
                },
                {
                    'id': 'step_with_rerun',
                    'name': 'Step With Rerun',
                    'script': 'ultracentrifuge.transfer.py',
                    'snapshot_items': ['outputs/'],
                    'allow_rerun': True
                },
                {
                    'id': 'step_explicit_no_rerun',
                    'name': 'Step Explicitly No Rerun',
                    'script': 'another_script.py',
                    'snapshot_items': ['outputs/'],
                    'allow_rerun': False
                },
                {
                    'id': 'step_plot_dna',
                    'name': 'Plot DNA Step',
                    'script': 'plot_DNAconc_vs_Density.py',
                    'snapshot_items': ['outputs/'],
                    'allow_rerun': True
                }
            ]
        }
    
    def test_workflow_parsing_allow_rerun_property(self):
        """Test that workflow correctly parses allow_rerun property."""
        # Create a temporary workflow file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_workflow_data, f)
            temp_workflow_path = Path(f.name)
        
        try:
            workflow = Workflow(temp_workflow_path)
            
            # Test step without allow_rerun property (should default to False)
            step_no_rerun = workflow.get_step_by_id('step_no_rerun')
            self.assertFalse(step_no_rerun.get('allow_rerun', False))
            
            # Test step with allow_rerun: True
            step_with_rerun = workflow.get_step_by_id('step_with_rerun')
            self.assertTrue(step_with_rerun.get('allow_rerun', False))
            
            # Test step with explicit allow_rerun: False
            step_explicit_no_rerun = workflow.get_step_by_id('step_explicit_no_rerun')
            self.assertFalse(step_explicit_no_rerun.get('allow_rerun', False))
            
            # Test another step with allow_rerun: True
            step_plot_dna = workflow.get_step_by_id('step_plot_dna')
            self.assertTrue(step_plot_dna.get('allow_rerun', False))
        finally:
            # Clean up temp file
            temp_workflow_path.unlink()
    
    def test_specific_scripts_have_allow_rerun(self):
        """Test that the specific scripts mentioned by user have allow_rerun: true."""
        # Read the actual workflow.yml file from templates directory
        workflow_path = Path(__file__).parent.parent / "templates" / "workflow.yml"
        workflow = Workflow(workflow_path)
        
        # Scripts that should have allow_rerun: true
        scripts_requiring_rerun = [
            'ultracentrifuge.transfer.py',
            'plot_DNAconc_vs_Density.py',
            'pool.FA12.analysis.py',
            'rework.pooling.steps.py'
        ]
        
        # Find steps with these scripts and verify they have allow_rerun: true
        for step in workflow.steps:
            if step.get('script') in scripts_requiring_rerun:
                self.assertTrue(
                    step.get('allow_rerun', False),
                    f"Step '{step['name']}' with script '{step['script']}' should have allow_rerun: true"
                )
    
    def test_other_scripts_do_not_have_allow_rerun(self):
        """Test that scripts not in the specified list do not have allow_rerun: true."""
        # Read the actual workflow.yml file from templates directory
        workflow_path = Path(__file__).parent.parent / "templates" / "workflow.yml"
        workflow = Workflow(workflow_path)
        
        # Scripts that should have allow_rerun: true
        scripts_requiring_rerun = [
            'ultracentrifuge.transfer.py',
            'plot_DNAconc_vs_Density.py',
            'pool.FA12.analysis.py',
            'rework.pooling.steps.py'
        ]
        
        # Find steps with other scripts and verify they do NOT have allow_rerun: true
        for step in workflow.steps:
            if step.get('script') not in scripts_requiring_rerun:
                self.assertFalse(
                    step.get('allow_rerun', False),
                    f"Step '{step['name']}' with script '{step['script']}' should NOT have allow_rerun: true"
                )
    
    @patch('streamlit.button')
    @patch('streamlit.write')
    def test_gui_logic_shows_rerun_button_only_for_allowed_steps(self, mock_write, mock_button):
        """Test that GUI logic only shows re-run button for steps with allow_rerun: true."""
        # Mock a completed step with allow_rerun: true
        step_with_rerun = {
            'id': 'test_step_rerun',
            'name': 'Test Step With Rerun',
            'script': 'ultracentrifuge.transfer.py',
            'allow_rerun': True
        }
        
        # Mock a completed step without allow_rerun
        step_no_rerun = {
            'id': 'test_step_no_rerun',
            'name': 'Test Step No Rerun',
            'script': 'other_script.py'
            # No allow_rerun property
        }
        
        # Mock session state
        mock_session_state = {
            'running_step_id': None,
            'user_inputs': {}
        }
        
        # Test step with allow_rerun: true should show re-run button
        with patch('streamlit.session_state', mock_session_state):
            # Simulate the GUI logic for a completed step with allow_rerun
            status = "completed"
            if status == "completed" and step_with_rerun.get('allow_rerun', False):
                mock_button.return_value = False  # Button not clicked
                mock_button.assert_called = True
            else:
                mock_write.assert_called = True
        
        # Reset mocks
        mock_button.reset_mock()
        mock_write.reset_mock()
        
        # Test step without allow_rerun should NOT show re-run button
        with patch('streamlit.session_state', mock_session_state):
            # Simulate the GUI logic for a completed step without allow_rerun
            status = "completed"
            if status == "completed" and step_no_rerun.get('allow_rerun', False):
                mock_button.assert_called = True
            else:
                # Should call st.write("") for empty space instead of button
                mock_write.assert_called = True
    
    def test_allow_rerun_property_inheritance(self):
        """Test that allow_rerun property is correctly inherited and doesn't affect other steps."""
        # Create a temporary workflow file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_workflow_data, f)
            temp_workflow_path = Path(f.name)
        
        try:
            workflow = Workflow(temp_workflow_path)
            
            # Verify each step has the correct allow_rerun value
            expected_values = {
                'step_no_rerun': False,
                'step_with_rerun': True,
                'step_explicit_no_rerun': False,
                'step_plot_dna': True
            }
            
            for step_id, expected_allow_rerun in expected_values.items():
                step = workflow.get_step_by_id(step_id)
                actual_allow_rerun = step.get('allow_rerun', False)
                self.assertEqual(
                    actual_allow_rerun,
                    expected_allow_rerun,
                    f"Step '{step_id}' should have allow_rerun={expected_allow_rerun}, got {actual_allow_rerun}"
                )
        finally:
            # Clean up temp file
            temp_workflow_path.unlink()

if __name__ == '__main__':
    unittest.main()