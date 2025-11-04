# Phase 3: Decision Steps Implementation Plan

## **Executive Summary**

This document outlines the implementation of decision steps using Python scripts that integrate seamlessly with the existing workflow execution system. This approach leverages the proven script execution path that already works perfectly for regular steps, avoiding the Streamlit UI refresh issues that caused previous implementation attempts to fail.

---

## **Problem Analysis**

### **Previous Implementation Failure**
The debugging summary shows that the previous attempt to implement decision steps using Streamlit UI callbacks failed due to persistent UI refresh issues, even when using the "correct" Streamlit patterns like `on_click` callbacks with `st.rerun()`.

### **Why Regular Steps Work**
Regular workflow steps work perfectly because they follow this proven execution path:
1. User clicks "Run" button → [`run_step()`](../src/core.py:220)
2. Script executes → Creates `.success` marker file  
3. Script completes → [`handle_step_result()`](../src/core.py:262) updates `workflow_state.json`
4. UI refreshes → Shows updated state correctly

### **The Insight**
Instead of fighting Streamlit's UI refresh system, we can **leverage the existing, proven script execution system** by making decisions into regular steps that call Python scripts.

---

## **Solution Design: Script-Based Decision Steps**

### **Core Concept**
Decision steps become regular workflow steps that:
- Call a Python script (like any other step)
- Script presents the decision in the terminal
- User makes choice via terminal input
- Script updates `workflow_state.json` based on choice
- Script creates success marker when complete
- Existing workflow system handles everything else automatically

### **Benefits of This Approach**
✅ **Uses proven execution path** - Same as all working steps  
✅ **Leverages existing UI refresh logic** - No custom button handling  
✅ **Creates proper snapshots** - Automatic via existing `run_step()` logic  
✅ **Updates `_completion_order`** - Automatic via existing state management  
✅ **Integrates with undo system** - Works exactly like any other step  
✅ **User-friendly terminal interaction** - Clear prompts and feedback  
✅ **No Streamlit UI complexity** - Avoids the refresh issues entirely

---

## **Implementation Architecture**

### **1. Workflow.yml Structure**

**Current Conditional System:**
```yaml
  - id: rework_second_attempt
    name: "10. Third Attempt Library Creation"
    script: "emergency.third.attempt.rework.py"
    conditional:
      trigger_script: "second.FA.output.analysis.py"
      prompt: "Do you want to run a third attempt at library creation?"
      target_step: "conclude_fa_analysis"
```

**New Decision Step System:**
```yaml
  - id: second_fa_analysis
    name: "9. Analyze Library QC (2nd)"
    script: "second.FA.output.analysis.py"
    snapshot_items: ["outputs/Lib.info.csv"]

  - id: third_attempt_decision
    name: "Decision: Third Library Creation Attempt"
    script: "decision_third_attempt.py"
    snapshot_items: ["workflow_state.json"]

  - id: rework_second_attempt
    name: "10. Third Attempt Library Creation"
    script: "emergency.third.attempt.rework.py"
    snapshot_items: ["outputs/"]

  - id: third_fa_analysis
    name: "11. Analyze Library QC (3rd)"
    script: "emergency.third.FA.output.analysis.py"
    snapshot_items: ["outputs/Lib.info.csv"]

  - id: conclude_fa_analysis
    name: "12. Conclude FA analysis"
    script: "conclude.all.fa.analysis.py"
    snapshot_items: ["outputs/Lib.info.csv"]
```

### **2. Decision Script Template**

**File: `scripts/decision_third_attempt.py`**
```python
#!/usr/bin/env python3
"""
Decision Script: Third Library Creation Attempt

This script presents a decision point to the user and updates the workflow
state based on their choice. It integrates seamlessly with the existing
workflow execution system.
"""

import json
import sys
from pathlib import Path

def main():
    """Main decision logic"""
    print_decision_header()
    choice = get_user_choice()
    update_workflow_state(choice)
    print_completion_message(choice)

def print_decision_header():
    """Display the decision prompt to the user"""
    print("\n" + "="*60)
    print("🔄 WORKFLOW DECISION POINT")
    print("="*60)
    print("\n📊 You've completed the second library QC analysis.")
    print("\n❓ QUESTION: Do you want to run a third attempt at library creation?")
    print("\n📋 Your options:")
    print("   ✅ YES = Run third attempt (Steps 10-11: Library creation + QC)")
    print("   ❌ NO  = Skip to conclusion (Step 12: Conclude analysis)")
    print("\n" + "-"*60)

def get_user_choice():
    """Get and validate user input"""
    while True:
        try:
            choice = input("\n🎯 Enter your choice (Y/N): ").strip().upper()
            
            if choice in ['Y', 'YES']:
                print(f"\n✅ You chose: YES - Running third attempt")
                return "yes"
            elif choice in ['N', 'NO']:
                print(f"\n✅ You chose: NO - Skipping to conclusion")
                return "no"
            else:
                print("❌ Invalid input. Please enter Y (Yes) or N (No)")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Decision cancelled by user")
            sys.exit(1)
        except EOFError:
            print("\n\n⚠️  No input received")
            sys.exit(1)

def update_workflow_state(choice):
    """
    Update workflow_state.json based on user choice.
    
    IMPORTANT: This function does NOT update _completion_order directly.
    The workflow manager will automatically add this decision step to
    _completion_order when it detects the script completion via the
    existing handle_step_result() -> update_state() -> StateManager.update_step_state() chain.
    
    This approach leverages the proven Phase 1 completion order system.
    """
    state_file = Path("workflow_state.json")
    
    # Load current state
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
    else:
        state = {}
    
    print(f"\n📝 Updating workflow state...")
    
    if choice == "yes":
        # Enable third attempt steps
        state["rework_second_attempt"] = "pending"
        state["third_fa_analysis"] = "pending"
        # conclude_fa_analysis remains pending (will be set after step 11)
        print("   ✅ Enabled Step 10: Third Attempt Library Creation")
        print("   ✅ Enabled Step 11: Analyze Library QC (3rd)")
        
    else:  # choice == "no"
        # Skip third attempt steps, go directly to conclusion
        state["rework_second_attempt"] = "skipped"
        state["third_fa_analysis"] = "skipped"
        state["conclude_fa_analysis"] = "pending"
        print("   ⏭️  Skipped Step 10: Third Attempt Library Creation")
        print("   ⏭️  Skipped Step 11: Analyze Library QC (3rd)")
        print("   ✅ Enabled Step 12: Conclude FA Analysis")
    
    # Save updated state
    # NOTE: We do NOT update _completion_order here - the workflow manager handles that
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print("   💾 Workflow state saved successfully")
    print("   🔄 Workflow manager will add this step to completion order automatically")

def create_success_marker():
    """Create success marker file (required by workflow manager)"""
    status_dir = Path(".workflow_status")
    status_dir.mkdir(exist_ok=True)
    
    success_file = status_dir / "decision_third_attempt.success"
    success_file.touch()
    
    print("   ✅ Success marker created")

def print_completion_message(choice):
    """Display completion message"""
    create_success_marker()
    
    print("\n" + "="*60)
    print("🎉 DECISION COMPLETED")
    print("="*60)
    
    if choice == "yes":
        print("\n📋 Next steps:")
        print("   1️⃣  Step 10 will be available to run")
        print("   2️⃣  After Step 10, Step 11 will become available")
        print("   3️⃣  After Step 11, Step 12 will become available")
    else:
        print("\n📋 Next steps:")
        print("   1️⃣  Step 12 will be available to run immediately")
        print("   ⏭️  Steps 10-11 have been skipped")
    
    print(f"\n🔄 Return to the workflow manager to continue...")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
```

### **3. Integration Points**

#### **A. Workflow Template Update**
- Update [`templates/workflow.yml`](../templates/workflow.yml) to use decision steps instead of conditional logic
- Remove conditional configuration from existing steps
- Add new decision steps with descriptive names (no numbering required)

#### **B. Validation Logic Update**
- Update [`validate_workflow_yaml()`](../app.py:112) to allow steps without `script` field (if needed)
- Ensure decision steps are treated as regular steps by validation

#### **C. UI Display Logic**
- Decision steps appear as regular steps in the workflow UI
- Show "Run" button like any other step
- Terminal interaction handles the decision logic

#### **D. Undo Integration**
- Decision steps create snapshots automatically via existing `run_step()` logic
- Undoing a decision step restores to before the decision was made
- User sees the decision prompt again after undo
- Integrates perfectly with Phase 1's `_completion_order` system

---

## **Implementation Steps**

### **Phase 3A: Core Decision Script ✅ COMPLETED**
- [x] Create `decision_third_attempt.py` script
- [x] Test script independently (outside workflow)
- [x] Verify workflow state updates work correctly
- [x] Test success marker creation

### **Phase 3B: Workflow Integration ✅ COMPLETED**
- [x] Update `templates/workflow.yml` to use decision step
- [x] Remove conditional logic from existing steps
- [x] Test decision step execution in workflow manager
- [x] Verify UI refresh works correctly
- [x] Test both YES and NO decision paths
- [x] Verify undo functionality with decision steps

### **Phase 3C: Conditional System Removal ✅ COMPLETED**
- [x] Remove conditional handling code from `src/core.py`
- [x] Remove conditional UI logic from `app.py`
- [x] Clean up unused conditional methods
- [x] Update workflow validation for decision steps
- [x] Test application functionality after removal

### **Phase 3D: Testing & Polish 📋 PENDING**
- [ ] Comprehensive workflow testing with decision steps
- [ ] Performance testing and optimization
- [ ] Documentation updates
- [ ] User guide updates for decision steps
- [ ] Final integration testing

---

## **Detailed Implementation**

### **1. Decision Script Features**

#### **User Experience Design**
```
============================================================
🔄 WORKFLOW DECISION POINT
============================================================

📊 You've completed the second library QC analysis.

❓ QUESTION: Do you want to run a third attempt at library creation?

📋 Your options:
   ✅ YES = Run third attempt (Steps 10-11: Library creation + QC)
   ❌ NO  = Skip to conclusion (Step 12: Conclude analysis)

------------------------------------------------------------

🎯 Enter your choice (Y/N): Y

✅ You chose: YES - Running third attempt

📝 Updating workflow state...
   ✅ Enabled Step 10: Third Attempt Library Creation
   ✅ Enabled Step 11: Analyze Library QC (3rd)
   💾 Workflow state saved successfully
   ✅ Success marker created

============================================================
🎉 DECISION COMPLETED
============================================================

📋 Next steps:
   1️⃣  Step 10 will be available to run
   2️⃣  After Step 10, Step 11 will become available
   3️⃣  After Step 11, Step 12 will become available

🔄 Return to the workflow manager to continue...
============================================================
```

#### **Error Handling**
- **Invalid Input**: Clear error messages, re-prompt
- **Keyboard Interrupt (Ctrl+C)**: Graceful exit without state corruption
- **File I/O Errors**: Detailed error messages with recovery suggestions
- **Missing State File**: Create new state file with proper structure

#### **State Management**
- **Atomic Updates**: Load → Modify → Save in single operation
- **Backup Creation**: Optional backup before state changes
- **Validation**: Verify state file structure after updates
- **Logging**: Optional logging to `.workflow_logs/` for debugging

### **2. Workflow State Updates**

#### **Decision: YES (Run Third Attempt)**
```json
{
  "setup_plates": "completed",
  "ultracentrifuge_transfer": "completed",
  "plot_dna_conc": "completed",
  "calc_sequin_addition": "completed",
  "merge_sip_fractions": "completed",
  "make_library_creation_files": "completed",
  "first_fa_analysis": "completed",
  "rework_first_attempt": "completed",
  "second_fa_analysis": "completed",
  "third_attempt_decision": "completed",
  "rework_second_attempt": "pending",
  "third_fa_analysis": "pending",
  "conclude_fa_analysis": "pending",
  "_completion_order": [
    "setup_plates",
    "ultracentrifuge_transfer",
    "plot_dna_conc",
    "calc_sequin_addition",
    "merge_sip_fractions",
    "make_library_creation_files",
    "first_fa_analysis",
    "rework_first_attempt",
    "second_fa_analysis",
    "third_attempt_decision"
  ]
}
```

#### **Decision: NO (Skip to Conclusion)**
```json
{
  "setup_plates": "completed",
  "ultracentrifuge_transfer": "completed",
  "plot_dna_conc": "completed",
  "calc_sequin_addition": "completed",
  "merge_sip_fractions": "completed",
  "make_library_creation_files": "completed",
  "first_fa_analysis": "completed",
  "rework_first_attempt": "completed",
  "second_fa_analysis": "completed",
  "third_attempt_decision": "completed",
  "rework_second_attempt": "skipped",
  "third_fa_analysis": "skipped",
  "conclude_fa_analysis": "pending",
  "_completion_order": [
    "setup_plates",
    "ultracentrifuge_transfer",
    "plot_dna_conc",
    "calc_sequin_addition",
    "merge_sip_fractions",
    "make_library_creation_files",
    "first_fa_analysis",
    "rework_first_attempt",
    "second_fa_analysis",
    "third_attempt_decision"
  ]
}
```

### **3. Undo Behavior**

#### **Undo Scenarios**
1. **User completes decision → Undo**: Returns to before decision, shows decision prompt again
2. **User completes Step 10 → Undo**: Returns to after decision (Step 10 pending)
3. **User completes Step 12 (after NO) → Undo**: Returns to after decision (Step 12 pending)

#### **Undo Integration with Phase 1**
- Decision steps create snapshots via existing `run_step()` logic
- `_completion_order` tracks decision completion chronologically
- [`perform_undo()`](../app.py:206) works identically for decision steps
- No special undo logic needed - leverages existing system

---

## **Migration Strategy**

### **Workflow State Management Compatibility**

#### **No Breaking Changes to Existing System**
The decision step approach is **fully compatible** with existing workflow state management:

**Existing State Management (Unchanged):**
- [`StateManager.load()`](../src/logic.py:31) and [`StateManager.save()`](../src/logic.py:38) - No changes needed
- [`StateManager.get_step_state()`](../src/logic.py:43) - Works identically for decision steps
- [`StateManager.update_step_state()`](../src/logic.py:53) - Handles decision steps automatically
- [`StateManager.get_completion_order()`](../src/logic.py:48) - Returns completion order including decisions

**Decision Steps Integration:**
- Decision steps appear in workflow state file like any other step
- `_completion_order` includes decision steps in chronological order
- Undo system treats decision steps identically to regular steps
- UI displays decision steps as regular workflow steps

#### **State File Structure Compatibility**
**Before Decision Steps (Current Format):**
```json
{
  "setup_plates": "completed",
  "second_fa_analysis": "completed",
  "rework_second_attempt": "pending",
  "_completion_order": ["setup_plates", "second_fa_analysis"]
}
```

**After Decision Steps (Enhanced Format):**
```json
{
  "setup_plates": "completed",
  "second_fa_analysis": "completed",
  "third_attempt_decision": "completed",
  "rework_second_attempt": "pending",
  "_completion_order": ["setup_plates", "second_fa_analysis", "third_attempt_decision"]
}
```

**Key Points:**
- ✅ Same JSON structure - just additional step entries
- ✅ `_completion_order` format unchanged - just includes decision steps
- ✅ Existing steps unaffected - same status values and behavior
- ✅ File format backward compatible - old projects continue working

### **Backward Compatibility**
- Existing projects with conditional logic continue to work
- New projects use decision step format
- Gradual migration path available
- No changes to core state management classes

### **Template Updates**
```yaml
# OLD: Conditional system
- id: rework_second_attempt
  conditional:
    trigger_script: "second.FA.output.analysis.py"
    prompt: "Do you want to run a third attempt?"
    target_step: "conclude_fa_analysis"

# NEW: Decision step system  
- id: third_attempt_decision
  name: "Decision: Third Library Creation Attempt"
  script: "decision_third_attempt.py"
  snapshot_items: ["workflow_state.json"]
```

### **Code Cleanup**
After successful implementation, remove:
- [`check_for_conditional_triggers()`](../src/core.py:186)
- [`should_show_conditional_prompt()`](../src/core.py:116)
- [`handle_conditional_decision()`](../src/core.py:132)
- Conditional UI logic in [`app.py`](../app.py:1070-1092)

---

## **Testing Strategy**

### **Unit Tests**
- **Decision Script**: Test state updates, error handling, input validation
- **Workflow Integration**: Test decision step execution in workflow context
- **Undo Logic**: Test undo behavior with decision steps

### **Integration Tests**
- **Complete Workflow**: Test full workflow with decision step
- **State Consistency**: Verify state file integrity after decisions
- **UI Refresh**: Confirm UI updates correctly after decision completion

### **Manual Test Scenarios**
1. **Happy Path**: Complete workflow with YES decision
2. **Skip Path**: Complete workflow with NO decision  
3. **Undo Testing**: Test undo at various points around decision
4. **Error Handling**: Test invalid input, interruption, file errors
5. **Edge Cases**: Test with corrupted state files, missing directories

---

## **Success Criteria**

### **Functional Requirements**
- ✅ Decision steps execute like regular workflow steps
- ✅ Terminal interaction is clear and user-friendly
- ✅ Workflow state updates correctly based on user choice
- ✅ Undo functionality works seamlessly with decision steps
- ✅ UI refreshes properly after decision completion

### **Non-Functional Requirements**
- ✅ No Streamlit UI refresh issues
- ✅ Consistent with existing workflow execution patterns
- ✅ Robust error handling and input validation
- ✅ Clear user feedback and progress indication

### **User Experience Goals**
- ✅ Decision process feels natural and integrated
- ✅ Clear understanding of consequences for each choice
- ✅ Ability to undo decisions and try different paths
- ✅ Consistent behavior with other workflow steps

---

## **Risk Mitigation**

### **Potential Risks**
1. **Terminal Input Issues**: Problems with input handling in different environments
2. **State File Corruption**: Errors during state file updates
3. **Script Execution Failures**: Decision script crashes or hangs
4. **User Confusion**: Unclear decision prompts or consequences

### **Mitigation Strategies**
1. **Robust Input Handling**: Comprehensive error handling and validation
2. **Atomic State Updates**: Safe file operations with backup/restore
3. **Timeout Mechanisms**: Prevent hanging on input operations
4. **Clear Documentation**: Detailed user guides and help text

---

## **Future Enhancements**

### **Potential Additions**
- **Multiple Choice Decisions**: Support for more than Yes/No options
- **Conditional Dependencies**: More complex decision trees
- **Decision History**: Track decision history for reporting
- **Decision Templates**: Reusable decision script templates

### **Advanced Features**
- **Decision Validation**: Validate decisions against project state
- **Decision Recommendations**: AI-powered decision suggestions
- **Decision Rollback**: Advanced undo with decision-specific logic
- **Decision Analytics**: Track decision patterns across projects

---

## **Conclusion**

This script-based approach to decision steps leverages the existing, proven workflow execution system instead of fighting Streamlit's UI refresh limitations. By making decisions into regular workflow steps that call Python scripts, we achieve:

- **Seamless Integration**: Works exactly like existing workflow steps
- **Robust State Management**: Leverages Phase 1's completion order system
- **Perfect Undo Support**: No special logic needed - works automatically
- **User-Friendly Experience**: Clear terminal interaction with rich feedback
- **Maintainable Code**: Simple, testable, and follows existing patterns

The solution is elegant, practical, and builds on the solid foundation established in Phase 1, ensuring reliable operation without the complexity that caused previous implementation attempts to fail.

---

## **Document Metadata**

**Version**: 1.0  
**Date**: November 4, 2025  
**Status**: Ready for Implementation  
**Dependencies**: Phase 1 (Simplified Undo System) - Complete  
**Priority**: High (Current implementation priority)  
**Estimated Effort**: 3-4 weeks development + testing