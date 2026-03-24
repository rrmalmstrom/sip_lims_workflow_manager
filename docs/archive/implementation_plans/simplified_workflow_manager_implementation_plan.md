# Simplified Workflow Manager Implementation Plan

**Date:** November 3, 2025  
**Objective:** Simplify the SIP LIMS Workflow Manager by addressing undo complexity and state detection issues while avoiding previous implementation failures.

## **Background & Previous Failures**

### **Root Cause Analysis**
1. **Complex Undo System**: Current [`perform_undo()`](../app.py:206) function is 298 lines handling conditional steps, granular re-runs, and "after" snapshots
2. **File Loss Issue**: Manual undo uses "after" snapshots, losing user files added between steps
3. **Decision Step UI Refresh Failure**: Previous attempt to implement checkpoint/decision steps failed due to Streamlit UI refresh issues
4. **State Detection Inconsistencies**: Dual-state system (workflow_state.json + .success markers) occasionally gets out of sync

### **Strategic Approach**
- **Phase-based implementation** to avoid previous failures
- **Avoid decision step complexity** until core systems are solid
- **Focus on immediate benefits** (simplified undo) before tackling harder problems

---

## **Phase 1: Simplified Undo System** ⭐ **CURRENT PHASE**

### **🎯 Objectives**
- Eliminate "after" snapshots entirely
- Use only "before" snapshots for manual undo
- Preserve user files added between steps (for immediate do-overs)
- Dramatically simplify undo logic (298 → ~50 lines)
- Keep existing conditional system unchanged (avoid UI refresh issues)

### **🔧 Implementation Details**

#### **File 1: `src/core.py`**
**Change**: Remove "after" snapshot creation
- **Location**: [`handle_step_result()`](../src/core.py:301-304) method
- **Action**: DELETE lines 301-304:
```python
# Take an "after" snapshot when step completes successfully for granular undo
run_number = self.snapshot_manager.get_current_run_number(step_id)
if run_number > 0:
    self.snapshot_manager.take_complete_snapshot(f"{step_id}_run_{run_number}_after")
```

#### **File 2: `app.py`**
**Change**: Replace entire `perform_undo()` function
- **Location**: Lines 206-503 (298 lines)
- **Action**: REPLACE with simplified version (~50 lines)
- **New Logic**:
  1. Find last completed step
  2. Get current run number
  3. If multiple runs exist → restore to previous run's "before" snapshot
  4. If single run → restore to step's "before" snapshot and mark pending
  5. Handle success markers and state updates

#### **File 3: `src/logic.py`**
**Change 1**: Add helper method
```python
def remove_all_run_snapshots(self, step_id: str):
    """Remove all run snapshots for a step (used when undoing entire step)."""
```

**Change 2**: Update [`get_effective_run_number()`](../src/logic.py:141)
- **Current**: Uses "after" snapshots to determine state
- **New**: Use "before" snapshots instead

**Change 3**: Update [`remove_run_snapshots_from()`](../src/logic.py:167)
- **Current**: Handles "after" snapshots
- **New**: Handle only "before" snapshots

### **🧪 Testing Strategy**
1. **Single Undo - File Preservation**:
   - Run Step A → Add files → Run Step B → Undo once
   - ✅ Verify: Files preserved (captured in Step B's "before" snapshot)

2. **Double Undo - File Loss (Expected)**:
   - Continue from above → Undo again
   - ✅ Verify: Files gone (not in Step A's "before" snapshot)

3. **Granular Re-run Undo**:
   - Run step → Re-run step → Undo
   - ✅ Verify: Back to first run state, step remains "completed"

4. **Conditional Workflow Compatibility**:
   - Test undo with existing conditional steps
   - ✅ Verify: No UI refresh issues, conditional logic unchanged

### **📋 Implementation Checklist**
- [ ] Remove "after" snapshot creation in `src/core.py`
- [ ] Replace `perform_undo()` function in `app.py`
- [ ] Add `remove_all_run_snapshots()` method in `src/logic.py`
- [ ] Update `get_effective_run_number()` method in `src/logic.py`
- [ ] Update `remove_run_snapshots_from()` method in `src/logic.py`
- [ ] Test basic undo functionality
- [ ] Test granular undo functionality
- [ ] Test file preservation behavior
- [ ] Test conditional workflow compatibility
- [ ] Document changes

**Estimated Impact**: ~350 lines removed, ~100 lines added = **250 lines net reduction**

---

## **Phase 2: State Detection Auto-Sync** ⏳ **NEXT PHASE**

### **🎯 Objectives**
- Add defensive consistency checks between workflow_state.json and .success markers
- Automatically reconcile inconsistencies when loading projects
- Preserve current reliability while fixing edge cases
- Minimal disruption to existing functionality

### **🔧 Planned Implementation**
- Add state validation in [`Project.__init__()`](../src/core.py:35)
- Create auto-sync logic to reconcile inconsistencies
- Add diagnostic logging for state mismatches
- Preserve both state systems but make them self-healing

### **📋 Design Tasks** (To be completed after Phase 1)
- [ ] Analyze current state detection logic
- [ ] Design auto-sync algorithm
- [ ] Plan implementation approach
- [ ] Create testing strategy
- [ ] Document state reconciliation rules

---

## **Phase 3: Decision Steps (Optional Future)** 🔮 **FUTURE PHASE**

### **🎯 Objectives**
- Implement checkpoint/decision step functionality
- Solve Streamlit UI refresh issues
- Simplify conditional workflow logic
- Only attempt after core systems are solid

### **🔧 Planned Approach**
- Learn from Phase 1 simplified undo implementation
- Research Streamlit UI refresh solutions
- Design decision step architecture
- Implement with proper UI state management

### **📋 Research Tasks** (To be completed after Phase 2)
- [ ] Analyze previous decision step failure
- [ ] Research Streamlit UI refresh patterns
- [ ] Design decision step architecture
- [ ] Plan implementation strategy
- [ ] Create testing approach

---

## **Implementation Instructions for Code Agent**

### **Current Task: Phase 1 Implementation**
Please implement the Phase 1: Simplified Undo System according to the detailed specifications above.

### **Critical Instructions**
1. **Follow the exact implementation plan** - don't deviate from the specified changes
2. **Test thoroughly** - use the provided testing strategy
3. **Document all changes** - update code comments and commit messages
4. **Return to Architect mode** when Phase 1 is complete for Phase 2 planning

### **Success Criteria**
- [ ] All Phase 1 checklist items completed
- [ ] Tests pass for all scenarios
- [ ] No regression in existing functionality
- [ ] Code is cleaner and more maintainable
- [ ] Ready to proceed to Phase 2

### **Next Steps After Phase 1**
Return to Architect mode to:
1. Design Phase 2: State Detection Auto-Sync
2. Plan Phase 3: Decision Steps (if desired)
3. Create comprehensive testing strategy
4. Document architectural decisions

---

## **Notes & Constraints**

### **What We're NOT Changing (Phase 1)**
- Existing conditional workflow system
- UI rendering logic
- Decision step functionality
- State detection dual-system
- Snapshot creation timing

### **Key Design Principles**
- **Simplicity over complexity** - eliminate unnecessary features
- **Preserve user workflow** - don't break existing functionality
- **Learn from failures** - avoid previous implementation pitfalls
- **Phase-based approach** - tackle one problem at a time

### **Risk Mitigation**
- Keep existing conditional system to avoid UI refresh issues
- Maintain backward compatibility with existing projects
- Comprehensive testing before deployment
- Clear rollback plan if issues arise

---

**Document Version**: 1.0  
**Last Updated**: November 3, 2025  
**Status**: Phase 1 Ready for Implementation