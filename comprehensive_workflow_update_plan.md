# Comprehensive SIP LIMS Workflow Manager Update Plan

## Overview
This document outlines the complete plan for updating the SIP LIMS Workflow Manager with:
1. **Workflow Changes**: Replace 3 scripts with 5 new scripts
2. **GUI Enhancements**: Add run counters and improved color scheme with undo-aware tracking

## Part 1: Workflow Structure Changes

### Scripts to Remove (Steps 4-6)
- **Step 4**: `calcSequinAddition.py` (Calculate Sequin Addition)
- **Step 5**: `merge.SIP.fraction.files.loop.py` (Merge Fraction Files)  
- **Step 6**: `make.library.creation.files.96.py` (Create Library Files)

### New Scripts to Add (Steps 4-8)
1. **Step 4**: `create.db.and.add.sequins.py` (allow_rerun: true)
2. **Step 5**: `select.fractions.for.clean.up.py` (allow_rerun: true)
3. **Step 6**: `generate.CsCl.cleanup.files.py` (allow_rerun: true)
4. **Step 7**: `process.post.DNA.quantification.py` (allow_rerun: true)
5. **Step 8**: `make.library.creation.files.condensed.plates.py` (no rerun)

### Updated workflow.yml Structure
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

  # ... remaining steps renumbered accordingly (11-21)
```

**Key Points:**
- No `snapshot_items` needed (complete snapshot system handles everything)
- No file inputs required for new scripts
- Steps 9+ are renumbered (+2 from original)

## Part 2: GUI Enhancements

### Enhanced Color Scheme
- **⚪ Pending**: Light blue (`st.info()`) - unchanged
- **⏳ Running**: Yellow/orange (`st.warning()`) - more visible
- **✅ Completed (no rerun)**: Green (`st.success()`) - unchanged  
- **🔄 Completed (rerunnable)**: Light green (custom styling) - distinguishes rerunnable
- **⏩ Skipped**: **Gray** (`st.markdown()` with gray styling) - distinct from pending

### Run Counter System

#### Undo-Aware Run Counting
The run count will be dynamically calculated from the current `_completion_order` array, ensuring it automatically adjusts when steps are undone:

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

#### Example Undo Behavior
```
Initial state: script run 3 times
_completion_order: ["step_4", "step_5", "step_4", "step_4"]
Display: "🔄 Create DB and Add Sequins (Run #3)" [Re-run (#4)]

After undo:
_completion_order: ["step_4", "step_5", "step_4"]  # Last entry removed
Display: "🔄 Create DB and Add Sequins (Run #2)" [Re-run (#3)]
```

### Enhanced Step Display Implementation

```python
def get_script_run_count(project, step_id):
    """Count script runs from current completion order."""
    completion_order = project.state_manager.get_completion_order()
    return completion_order.count(step_id)

# Enhanced step display logic:
with col1:
    if is_running_this_step:
        st.warning(f"⏳ {step_name} (Running...)")
    elif status == "completed":
        if step.get('allow_rerun', False):
            run_count = get_script_run_count(project, step_id)
            # Light green styling for rerunnable completed steps
            st.markdown(f"""
            <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #28a745;">
                🔄 {step_name} (Run #{run_count})
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ {step_name}")
    elif status == "skipped":
        # Gray styling for skipped steps
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; color: #6c757d;">
            ⏩ {step_name} - Completed outside workflow
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"⚪ {step_name}")

# Enhanced re-run button:
if status == "completed" and step.get('allow_rerun', False):
    run_count = get_script_run_count(project, step_id)
    button_text = f"Re-run (#{run_count + 1})"
    if st.button(button_text, key=f"rerun_{step_id}", disabled=rerun_button_disabled):
        # ... existing rerun logic
```

## Part 3: Implementation Strategy

### Phase 1: Workflow Structure Update
1. **Backup current configuration**
   - Save `templates/workflow.yml`
   - Document current step IDs for reference

2. **Update workflow.yml**
   - Replace steps 4-6 with new steps 4-8
   - Renumber subsequent steps
   - Add `allow_rerun: true` to appropriate steps

3. **Test new scripts**
   - Verify all 5 new scripts exist in `/Users/RRMalmstrom/Desktop/sip_scripts_dev`
   - Test basic execution

### Phase 2: GUI Enhancements
1. **Add run counter function**
   - Implement `get_script_run_count()` 
   - Test with existing projects

2. **Update step display logic**
   - Implement new color scheme
   - Add run counters for rerunnable steps
   - Test undo behavior with run counts

3. **Enhanced re-run buttons**
   - Show next run number
   - Verify proper incrementing

### Phase 3: Integration Testing
1. **End-to-end workflow testing**
   - Test complete workflow with new scripts
   - Verify run counters work correctly
   - Test undo functionality with run counts

2. **Migration testing**
   - Test existing projects with new workflow
   - Verify backward compatibility

## Part 4: Key Benefits

### Workflow Benefits
- **Updated Laboratory Process**: Reflects current lab procedures with new scripts
- **Improved Flexibility**: 4 of 5 new scripts allow re-runs for iterative work
- **Simplified Configuration**: No snapshot_items needed due to complete snapshot system

### GUI Benefits
- **Clear Run Tracking**: Users see exactly how many times each script has run
- **Undo-Aware Counters**: Run counts automatically adjust when steps are undone
- **Better Visual Distinction**: Different colors for different step types
- **Enhanced Usability**: Re-run buttons show next run number

### Technical Benefits
- **Leverages Existing Systems**: Uses current `_completion_order` tracking
- **Backward Compatible**: Works with existing projects
- **Maintainable**: Simple, clean implementation
- **Robust**: Automatically handles undo scenarios

## Part 5: Risk Mitigation

### Potential Issues
1. **Existing Projects**: May have workflow states referencing old step IDs
2. **Script Dependencies**: New scripts may have different requirements
3. **GUI Changes**: Custom HTML styling may need browser compatibility testing

### Mitigation Strategies
1. **Gradual Rollout**: Test in development environment first
2. **Backup Strategy**: Maintain ability to revert to previous workflow
3. **Documentation**: Clear upgrade instructions for existing projects
4. **Testing**: Comprehensive testing with various project states

## Next Steps

1. **Review and approve this comprehensive plan**
2. **Begin Phase 1 implementation in development environment**
3. **Test workflow changes with sample projects**
4. **Implement GUI enhancements**
5. **Conduct integration testing**
6. **Plan production deployment strategy**

This plan addresses both the immediate workflow needs and the enhanced user experience requirements while maintaining system reliability and backward compatibility.