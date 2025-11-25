# Detailed Implementation Steps for SIP LIMS Workflow Manager Update

## Overview
This document provides step-by-step implementation instructions for updating the SIP LIMS Workflow Manager with new scripts and GUI enhancements.

## Phase 1: Workflow Changes

### Step 1: Create Feature Branch
```bash
cd /Users/RRMalmstrom/Desktop/sip_lims_workflow_manager
git checkout -b feature/condensed-plates-workflow
git push -u origin feature/condensed-plates-workflow
```

### Step 2: Backup Current Configuration
```bash
# Create backup of current workflow template
cp templates/workflow.yml templates/workflow.yml.backup
```

### Step 3: Update templates/workflow.yml

Replace the current workflow with the new structure:

```yaml
workflow_name: "SIP Fractionation and Library Prep"
steps:
  - id: setup_plates
    name: "1. Setup Plates & DB"
    script: "setup.isotope.and.FA.plates.py"

  - id: ultracentrifuge_transfer
    name: "2. Create Ultracentrifuge Tubes"
    script: "ultracentrifuge.transfer.py"
    allow_rerun: true
    inputs:
      - type: file
        name: "Sample List"
        arg: ""

  - id: plot_dna_conc
    name: "3. Plot DNA/Density (QC)"
    script: "plot_DNAconc_vs_Density.py"
    allow_rerun: true

  - id: create_db_sequins
    name: "4. Create DB and Add Sequins"
    script: "create.db.and.add.sequins.py"
    allow_rerun: true

  - id: select_fractions_cleanup
    name: "5. Select Fractions for Cleanup"
    script: "select.fractions.for.clean.up.py"
    allow_rerun: true

  - id: generate_cscl_cleanup
    name: "6. Generate CsCl Cleanup Files"
    script: "generate.CsCl.cleanup.files.py"
    allow_rerun: true

  - id: process_post_dna_quant
    name: "7. Process Post-DNA Quantification"
    script: "process.post.DNA.quantification.py"
    allow_rerun: true

  - id: make_library_condensed
    name: "8. Create Library Files (Condensed Plates)"
    script: "make.library.creation.files.condensed.plates.py"

  - id: first_fa_analysis
    name: "9. Analyze Library QC (1st)"
    script: "first.FA.output.analysis.py"

  - id: rework_first_attempt
    name: "10. Second Attempt Library Creation"
    script: "rework.first.attempt.py"

  - id: second_fa_analysis
    name: "11. Analyze Library QC (2nd)"
    script: "second.FA.output.analysis.py"

  - id: third_attempt_decision
    name: "Decision: Third Library Creation Attempt"
    script: "decision_third_attempt.py"

  - id: rework_second_attempt
    name: "12. Third Attempt Library Creation"
    script: "emergency.third.attempt.rework.py"

  - id: third_fa_analysis
    name: "13. Analyze Library QC (3rd)"
    script: "emergency.third.FA.output.analysis.py"

  - id: conclude_fa_analysis
    name: "14. Conclude FA analysis"
    script: "conclude.all.fa.analysis.py"

  - id: make_clarity_summary
    name: "15. Make Clarity Summary"
    script: "make.clarity.summary.py"

  - id: generate_pool_tool
    name: "16. Generate Pool Assignment Tool"
    script: "generate_pool_assignment_tool.py"

  - id: run_pooling_preparation
    name: "17. Prepare Pools"
    script: "run.pooling.preparation.py"

  - id: pool_fa12_analysis
    name: "18. Analyze Pool QC Results"
    script: "pool.FA12.analysis.py"
    allow_rerun: true

  - id: rework_pooling
    name: "19. Rework Pools & Finalize"
    script: "rework.pooling.steps.py"
    allow_rerun: true
  
  - id: transfer_pools
    name: "20. Transfer Pools to Final Tubes"
    script: "transfer.pools.to.final.tubes.py"
```

### Step 4: Verify New Scripts Exist
```bash
# Check that all 5 new scripts exist in the dev scripts directory
ls -la /Users/RRMalmstrom/Desktop/sip_scripts_dev/create.db.and.add.sequins.py
ls -la /Users/RRMalmstrom/Desktop/sip_scripts_dev/select.fractions.for.clean.up.py
ls -la /Users/RRMalmstrom/Desktop/sip_scripts_dev/generate.CsCl.cleanup.files.py
ls -la /Users/RRMalmstrom/Desktop/sip_scripts_dev/process.post.DNA.quantification.py
ls -la /Users/RRMalmstrom/Desktop/sip_scripts_dev/make.library.creation.files.condensed.plates.py
```

### Step 5: Test Individual Scripts
Create a test project and verify each new script can execute:

```bash
# Create test directory
mkdir -p ~/Desktop/test_condensed_workflow
cd ~/Desktop/test_condensed_workflow

# Test each script individually (dry run)
python /Users/RRMalmstrom/Desktop/sip_scripts_dev/create.db.and.add.sequins.py --help
python /Users/RRMalmstrom/Desktop/sip_scripts_dev/select.fractions.for.clean.up.py --help
python /Users/RRMalmstrom/Desktop/sip_scripts_dev/generate.CsCl.cleanup.files.py --help
python /Users/RRMalmstrom/Desktop/sip_scripts_dev/process.post.DNA.quantification.py --help
python /Users/RRMalmstrom/Desktop/sip_scripts_dev/make.library.creation.files.condensed.plates.py --help
```

### Step 6: Run Existing Tests
```bash
# Run existing test suite to ensure no regressions
cd /Users/RRMalmstrom/Desktop/sip_lims_workflow_manager
python -m pytest tests/ -v
```

### Step 7: Test Complete Workflow
1. Start the workflow manager in developer mode
2. Create a new test project using the updated workflow
3. Run through steps 1-8 to test the new script sequence
4. Verify each script completes successfully
5. Test re-run functionality on steps 4-7

### Step 8: Test Undo Functionality
1. Run several steps including re-runs
2. Test undo operations at various points
3. Verify workflow state consistency after undo
4. Confirm `_completion_order` array updates correctly

### Step 9: Commit Phase 1 Changes
```bash
git add templates/workflow.yml
git commit -m "feat: Update workflow with 5 new condensed plates scripts

- Replace steps 4-6 with new steps 4-8
- Add create.db.and.add.sequins.py (rerunnable)
- Add select.fractions.for.clean.up.py (rerunnable)  
- Add generate.CsCl.cleanup.files.py (rerunnable)
- Add process.post.DNA.quantification.py (rerunnable)
- Add make.library.creation.files.condensed.plates.py
- Renumber subsequent steps accordingly"
```

## Phase 2: GUI Enhancements

### Step 10: Add Run Counter Function
Add to `app.py` (around line 55, after helper functions):

```python
def get_script_run_count(project, step_id):
    """
    Count how many times a script has been completed.
    This count automatically adjusts when steps are undone since it reads
    from the current _completion_order array in workflow_state.json.
    """
    completion_order = project.state_manager.get_completion_order()
    return completion_order.count(step_id)
```

### Step 11: Add Tests for Run Counter Function
Create `tests/test_run_counter.py`:

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from src.core import Project
from app import get_script_run_count

class TestRunCounter:
    """Test the get_script_run_count function."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create minimal workflow.yml
        workflow_content = """
workflow_name: "Test Workflow"
steps:
  - id: test_step
    name: "Test Step"
    script: "test_script.py"
    allow_rerun: true
"""
        workflow_file = temp_dir / "workflow.yml"
        workflow_file.write_text(workflow_content)
        
        # Create scripts directory
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test_script.py").write_text('print("test")')
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_run_count_zero_initially(self, temp_project):
        """Test that run count is 0 for steps that haven't been completed."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        count = get_script_run_count(project, "test_step")
        assert count == 0
    
    def test_run_count_after_completion(self, temp_project):
        """Test that run count increases after step completion."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Simulate step completion
        project.update_state("test_step", "completed")
        count = get_script_run_count(project, "test_step")
        assert count == 1
        
        # Simulate re-run
        project.update_state("test_step", "completed")
        count = get_script_run_count(project, "test_step")
        assert count == 2
    
    def test_run_count_after_undo(self, temp_project):
        """Test that run count decreases after undo operations."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        
        # Complete step twice
        project.update_state("test_step", "completed")
        project.update_state("test_step", "completed")
        assert get_script_run_count(project, "test_step") == 2
        
        # Simulate undo by removing last completion from order
        state = project.state_manager.load()
        completion_order = state.get("_completion_order", [])
        if completion_order and completion_order[-1] == "test_step":
            completion_order.pop()
            project.state_manager.save(state)
        
        # Count should decrease
        assert get_script_run_count(project, "test_step") == 1
    
    def test_run_count_nonexistent_step(self, temp_project):
        """Test that run count is 0 for non-existent steps."""
        project = Project(temp_project, script_path=temp_project / "scripts")
        count = get_script_run_count(project, "nonexistent_step")
        assert count == 0
```

### Step 12: Update Step Display Logic
Replace the step display section (around lines 1015-1022) in `app.py`:

```python
with col1:
    if is_running_this_step:
        st.warning(f"⏳ {step_name} (Running...)")  # Changed to warning for visibility
    elif status == "completed":
        if step.get('allow_rerun', False):
            run_count = get_script_run_count(project, step_id)
            # Light green styling for re-runnable completed steps
            st.markdown(f"""
            <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #28a745;">
                🔄 {step_name} (Run #{run_count})
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ {step_name}")  # Standard green for non-rerunnable
    elif status == "skipped":
        # Gray styling for skipped steps
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; color: #6c757d;">
            ⏩ {step_name} - Completed outside workflow
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"⚪ {step_name}")
```

### Step 13: Enhance Re-run Buttons
Update the re-run button section (around line 1080) in `app.py`:

```python
# Show Re-run button for completed steps that allow re-runs
if status == "completed" and step.get('allow_rerun', False):
    # Check if all required inputs for re-run are filled
    rerun_button_disabled = run_button_disabled
    if 'inputs' in step:
        step_inputs = st.session_state.user_inputs.get(step_id, {})
        required_inputs = step['inputs']
        if len(step_inputs) < len(required_inputs) or not all(step_inputs.values()):
            rerun_button_disabled = True
    
    # Additional check: disable if project setup is not complete
    if not project.has_workflow_state():
        rerun_button_disabled = True
    
    # Enhanced button text with run count
    run_count = get_script_run_count(project, step_id)
    button_text = f"Re-run (#{run_count + 1})"
    
    if st.button(button_text, key=f"rerun_{step_id}", disabled=rerun_button_disabled):
        # Clear the rerun flag so inputs get cleared again next time
        if f"rerun_inputs_cleared_{step_id}" in st.session_state:
            del st.session_state[f"rerun_inputs_cleared_{step_id}"]
        
        st.session_state.running_step_id = step_id
        st.session_state.terminal_output = ""
        step_user_inputs = st.session_state.user_inputs.get(step_id, {})
        start_script_thread(project, step_id, step_user_inputs)
        st.rerun()  # Force immediate rerun to show terminal
```

### Step 14: Run Tests for GUI Enhancements
```bash
# Run the new run counter tests
python -m pytest tests/test_run_counter.py -v

# Run all tests to ensure no regressions
python -m pytest tests/ -v
```

### Step 15: Test GUI Enhancements Manually
1. Create a new test project
2. Run several steps including re-runs
3. Verify run counters display correctly
4. Test color scheme changes
5. Verify undo operations update run counters properly
6. Test enhanced re-run buttons

### Step 16: Test Undo with Run Counters
Specific test scenarios:
1. Run step 4 once → shows "Run #1"
2. Re-run step 4 → shows "Run #2", button shows "Re-run (#3)"
3. Undo → should show "Run #1", button shows "Re-run (#2)"
4. Run step 5 → step 4 still shows "Run #1"
5. Undo step 5 → step 4 still shows "Run #1"

### Step 17: Commit Phase 2 Changes
```bash
git add app.py tests/test_run_counter.py
git commit -m "feat: Add GUI enhancements with run counters and improved colors

- Add undo-aware run counter system using _completion_order
- Implement enhanced color scheme:
  * Running steps: yellow/orange for visibility
  * Completed rerunnable: light green
  * Skipped: gray styling
- Enhanced re-run buttons show next run number
- Run counters automatically adjust during undo operations
- Add lightweight tests for get_script_run_count function"
```

## Phase 3: Final Testing and Deployment

### Step 18: Comprehensive Testing
1. **End-to-End Workflow Test**
   - Create fresh test project
   - Run complete workflow steps 1-20
   - Test re-runs on steps 2, 3, 4, 5, 6, 7, 18, 19
   - Verify all scripts execute successfully

2. **Undo Functionality Test**
   - Test undo at various workflow points
   - Verify run counters update correctly
   - Test undo after re-runs
   - Confirm workflow state consistency

3. **GUI Enhancement Test**
   - Verify all color changes work correctly
   - Test run counter display accuracy
   - Confirm enhanced re-run buttons function properly

4. **Automated Test Suite**
   ```bash
   # Run complete test suite
   python -m pytest tests/ -v --tb=short
   ```

### Step 19: Documentation Update
Update relevant documentation files:
- Update workflow step count in README.md
- Document new scripts in user guide
- Update any hardcoded step references

### Step 20: Merge to Main
```bash
# Final commit if needed
git add .
git commit -m "docs: Update documentation for new workflow structure"

# Switch to main and merge
git checkout main
git merge feature/condensed-plates-workflow
git push origin main

# Clean up feature branch
git branch -d feature/condensed-plates-workflow
git push origin --delete feature/condensed-plates-workflow
```

## Success Criteria

### Phase 1 Success Criteria
- [ ] All 5 new scripts execute without errors
- [ ] Complete workflow runs from steps 1-20
- [ ] Undo functionality works with new workflow
- [ ] Re-run capability works on steps 4-7
- [ ] Workflow state tracking functions correctly
- [ ] All existing tests pass

### Phase 2 Success Criteria
- [ ] Run counters display correctly for all rerunnable steps
- [ ] Run counters update properly during undo operations
- [ ] Color scheme changes are visible and distinct
- [ ] Enhanced re-run buttons show correct next run number
- [ ] Skipped steps display in gray
- [ ] New run counter tests pass
- [ ] All existing tests continue to pass

### Overall Success Criteria
- [ ] New laboratory workflow is fully functional
- [ ] GUI provides clear visual feedback on script execution history
- [ ] Undo system maintains consistency with run counters
- [ ] No regression in existing functionality
- [ ] System is ready for production laboratory use

## Rollback Procedures

If issues are discovered during testing:

1. **Phase 1 Rollback**
   ```bash
   git checkout main
   cp templates/workflow.yml.backup templates/workflow.yml
   ```

2. **Phase 2 Rollback**
   ```bash
   git revert <commit-hash-of-gui-changes>
   ```

3. **Complete Rollback**
   ```bash
   git checkout main
   git branch -D feature/condensed-plates-workflow
   ```

## Testing Strategy Summary

This implementation leverages the existing robust test framework:

- **Existing Tests**: Comprehensive coverage of undo functionality and `_completion_order` system
- **New Tests**: Lightweight tests specifically for `get_script_run_count()` function
- **Manual Testing**: GUI verification and end-to-end workflow validation
- **Regression Testing**: Full test suite run after each phase

The testing approach follows TDD principles by adding tests for new functionality while relying on the existing comprehensive test coverage for core systems.