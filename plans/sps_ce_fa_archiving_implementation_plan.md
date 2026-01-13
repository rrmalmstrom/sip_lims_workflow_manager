# SPS-CE Fragment Analyzer Quality Control (FAQC) Archiving Implementation Plan

## Executive Summary

This document provides a detailed technical implementation plan for adding Fragment Analyzer Quality Control (FAQC) archiving functionality to the SPS-CE workflow, based on the comprehensive analysis of both the working SIP implementation and the current SPS-CE state.

## Context Analysis

### Working SIP Implementation (Reference)
- **Location**: `/Users/RRMalmstrom/Desktop/sip_scripts_dev/`
- **Scripts**: [`first.FA.output.analysis.py`](../sip_scripts_dev/first.FA.output.analysis.py), [`second.FA.output.analysis.py`](../sip_scripts_dev/second.FA.output.analysis.py), [`emergency.third.FA.output.analysis.py`](../sip_scripts_dev/emergency.third.FA.output.analysis.py)
- **Archive Structure**: `archived_files/{first|second|third}_lib_attempt_fa_results/`
- **Integration**: Complete workflow manager integration with exclusion patterns in [`src/logic.py`](../src/logic.py)

### SPS-CE Current State (Target)
- **Location**: `/Users/RRMalmstrom/Desktop/Programming/Python/SPS_library_creation_scripts/`
- **Scripts**: [`SPS_first_FA_output_analysis_NEW.py`](../SPS_library_creation_scripts/SPS_first_FA_output_analysis_NEW.py), [`SPS_second_FA_output_analysis_NEW.py`](../SPS_library_creation_scripts/SPS_second_FA_output_analysis_NEW.py)
- **Directory Structure**: `B_first_attempt_fa_result/`, `D_second_attempt_fa_result/`
- **Archive Infrastructure**: Already exists (`ARCHIV_DIR = PROJECT_DIR / "archived_files"`)

## Implementation Plan

### 1. SPS-CE Script Modifications

#### 1.1 Enhanced `getFAfiles()` Function Modifications

**Target Files**: 
- [`SPS_first_FA_output_analysis_NEW.py`](../SPS_library_creation_scripts/SPS_first_FA_output_analysis_NEW.py) (lines 91-142)
- [`SPS_second_FA_output_analysis_NEW.py`](../SPS_library_creation_scripts/SPS_second_FA_output_analysis_NEW.py) (lines 103-189)

**Current Implementation Pattern**:
```python
def getFAfiles(first_dir):
    fa_files = []
    
    for direct in first_dir.iterdir():
        if direct.is_dir():
            nxt_dir = direct
            
            for fa in nxt_dir.iterdir():
                if fa.is_dir():
                    folder_path = fa
                    folder_name = fa.name.split(' ')[0]
                    
                    for file_path in fa.iterdir():
                        if file_path.name.endswith('Smear Analysis Result.csv'):
                            # Process file...
                            fa_files.append(f'{folder_name}.csv')
    
    return fa_files
```

**Required Enhancement Pattern** (based on SIP implementation):
```python
def getFAfiles(first_dir):
    fa_files = []
    fa_result_dirs_to_archive = []  # NEW: Track directories for archiving
    
    for direct in first_dir.iterdir():
        if direct.is_dir():
            nxt_dir = direct
            
            for fa in nxt_dir.iterdir():
                if fa.is_dir():
                    folder_path = fa
                    folder_name = fa.name.split(' ')[0]
                    
                    for file_path in fa.iterdir():
                        if file_path.name.endswith('Smear Analysis Result.csv'):
                            # Existing processing logic...
                            fa_files.append(f'{folder_name}.csv')
                            
                            # NEW: Track this directory for archiving
                            fa_result_dirs_to_archive.append(Path(fa.path))
    
    return fa_files, fa_result_dirs_to_archive  # NEW: Return both lists
```

#### 1.2 Archive Function Implementation

**Function to Add** (adapted from SIP implementation):
```python
def archive_fa_results(fa_result_dirs, archive_subdir_name):
    """Archive FA result directories to permanent storage"""
    if not fa_result_dirs:
        return
    
    # Create archive directory
    archive_base = PROJECT_DIR / "archived_files"
    archive_dir = archive_base / archive_subdir_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for result_dir in fa_result_dirs:
        if result_dir.exists():
            dest_path = archive_dir / result_dir.name
            
            # Handle existing archives (prevent nesting)
            if dest_path.exists():
                shutil.rmtree(dest_path)
                print(f"Removing existing archive: {result_dir.name}")
            
            # Move directory to archive
            shutil.move(str(result_dir), str(dest_path))
            print(f"Archived: {result_dir.name}")
            
            # Clean up empty parent directories
            parent_dir = result_dir.parent
            if parent_dir.exists():
                # Check if directory is empty (ignoring .DS_Store files)
                remaining_files = [f for f in parent_dir.iterdir() if f.name != '.DS_Store']
                if not remaining_files:
                    # Remove any .DS_Store files first
                    for ds_store in parent_dir.glob('.DS_Store'):
                        ds_store.unlink()
                    # Now remove the empty directory
                    parent_dir.rmdir()
                    print(f"Cleaned up empty directory: {parent_dir.name}")
```

#### 1.3 Main Program Integration Points

**SPS_first_FA_output_analysis_NEW.py** (lines 387-426):
```python
def main():
    print("Starting SPS First FA Output Analysis...")
    
    # MODIFIED: Update function call to receive both returns
    fa_files, fa_result_dirs_to_archive = getFAfiles(FIRST_DIR)
    
    # Existing processing logic...
    fa_lib_dict, fa_dest_plates = processFAfiles(fa_files)
    fa_df = pd.concat(fa_lib_dict.values(), ignore_index=True)
    lib_df = addFAresults(PROJECT_DIR, fa_df)
    fa_summary_df = findPassFailLibs(lib_df, fa_dest_plates)
    
    # Generate output file
    reduced_fa_df = fa_summary_df[['sample_id', 'Destination_Plate_Barcode','FA_Well','dilution_factor','ng/uL', 'nmole/L', 'Avg. Size', 'Passed_library', 'Redo_whole_plate']].copy()
    reduced_fa_df.sort_values(by=['Destination_Plate_Barcode', 'sample_id'], inplace=True)
    output_file = FIRST_DIR / 'reduced_fa_analysis_summary.txt'
    reduced_fa_df.to_csv(output_file, sep='\t', index=False)
    
    print(f"\nAnalysis complete. Results saved to: \n{output_file}")
    
    # NEW: Archive FA results before creating success marker
    if fa_result_dirs_to_archive:
        archive_fa_results(fa_result_dirs_to_archive, "first_lib_attempt_fa_results")
    
    # Create success marker for workflow manager integration
    create_success_marker()
```

**SPS_second_FA_output_analysis_NEW.py** (lines 506-550):
```python
def main():
    print("Starting SPS Second FA Output Analysis...")
    
    # MODIFIED: Update function call to receive both returns
    fa_files, fa_result_dirs_to_archive = getFAfiles(SECOND_DIR)
    
    # Existing processing logic...
    fa_lib_dict, fa_dest_plates = processFAfiles(fa_files)
    fa_df = pd.concat(fa_lib_dict.values(), ignore_index=True)
    lib_df = addFAresults(PROJECT_DIR, fa_df)
    fa_summary_df, double_fail_df = findPassFailLibs(lib_df, fa_dest_plates)
    
    # Generate output files
    reduced_fa_df = fa_summary_df[['sample_id', 'Redo_Destination_Plate_Barcode', 'Redo_FA_Well', 'Redo_dilution_factor',
                                  'Redo_ng/uL', 'Redo_nmole/L', 'Redo_Avg. Size', 'Redo_Passed_library',
                                  'Total_passed_attempts']].copy()
    reduced_fa_df.sort_values(by=['Redo_Destination_Plate_Barcode', 'sample_id'], inplace=True)
    
    output_file = SECOND_DIR / 'reduced_2nd_fa_analysis_summary.txt'
    reduced_fa_df.to_csv(output_file, sep='\t', index=False)
    
    double_fail_output = SECOND_DIR / 'double_failed_libraries.txt'
    double_fail_df.to_csv(double_fail_output, sep='\t', index=False)
    
    print(f"\nAnalysis complete.")
    
    # NEW: Archive FA results before creating success marker
    if fa_result_dirs_to_archive:
        archive_fa_results(fa_result_dirs_to_archive, "second_lib_attempt_fa_results")
    
    # Create success marker for workflow manager integration
    create_success_marker()
```

### 2. Archive Directory Structure

#### 2.1 SPS-CE Archive Naming Convention

**Archive Base Directory**: `archived_files/`

**SPS-CE Specific Archive Subdirectories**:
```
archived_files/
├── first_lib_attempt_fa_results/     # First attempt FA results (SPS-CE)
│   ├── PLATE1F 10-05-53/
│   └── PLATE2F 12-34-56/
└── second_lib_attempt_fa_results/    # Second attempt FA results (SPS-CE)
    ├── PLATE1F 14-22-11/
    └── PLATE2F 15-45-33/
```

**Comparison with SIP Structure**:
```
archived_files/
├── first_lib_attempt_fa_results/     # SIP First attempt
├── second_lib_attempt_fa_results/    # SIP Second attempt  
├── third_lib_attempt_fa_results/     # SIP Third attempt (emergency)
├── first_lib_attempt_fa_results/     # SPS-CE First attempt (SAME NAME)
└── second_lib_attempt_fa_results/    # SPS-CE Second attempt (SAME NAME)
```

**Note**: SPS-CE uses the same archive directory names as SIP for the first two attempts, ensuring consistency across workflows.

### 3. Workflow Manager Updates

#### 3.1 Modifications to [`src/logic.py`](../src/logic.py)

**Current FA Archive Exclusion Patterns** (lines 286-290):
```python
# FA result archive directories to exclude (preserve during undo)
fa_archive_patterns = {
    'first_lib_attempt_fa_results',
    'second_lib_attempt_fa_results',
    'third_lib_attempt_fa_results'
}
```

**Required Update**: No changes needed! The SPS-CE workflow uses the same archive directory names (`first_lib_attempt_fa_results`, `second_lib_attempt_fa_results`) as the first two SIP attempts, so the existing exclusion patterns already cover SPS-CE.

**Verification Points**:
- [`take_complete_snapshot()`](../src/logic.py#L268-L345) - Already excludes SPS-CE archives
- [`restore_complete_snapshot()`](../src/logic.py#L347-L463) - Already preserves SPS-CE archives

### 4. Documentation Updates

#### 4.1 Developer Guide Updates

**Target File**: [`docs/developer_guide/fa_results_archiving.md`](../docs/developer_guide/fa_results_archiving.md)

**Required Additions**:

```markdown
## SPS-CE Workflow Integration

The FA Results Archiving system has been extended to support the SPS-CE (SPS-Capillary Electrophoresis) workflow alongside the existing SIP workflow.

### SPS-CE Archive Structure

```
archived_files/
├── first_lib_attempt_fa_results/     # First attempt FA results (both SIP and SPS-CE)
└── second_lib_attempt_fa_results/    # Second attempt FA results (both SIP and SPS-CE)
```

### SPS-CE Script Modifications

#### Enhanced `getFAfiles()` Function
Both SPS-CE FA analysis scripts have been modified with enhanced `getFAfiles()` functions:

**SPS_first_FA_output_analysis_NEW.py**:
```python
def getFAfiles(first_dir):
    fa_files = []
    fa_result_dirs_to_archive = []  # Track directories for archiving
    
    for direct in first_dir.iterdir():
        if direct.is_dir():
            nxt_dir = direct
            for fa in nxt_dir.iterdir():
                if fa.is_dir():
                    # Process FA directories and track them
                    for file_path in fa.iterdir():
                        if file_path.name.endswith('Smear Analysis Result.csv'):
                            # Track this directory for archiving
                            fa_result_dirs_to_archive.append(Path(fa.path))
                            # ... existing processing logic
    
    return fa_files, fa_result_dirs_to_archive
```

#### Archive Function Integration
```python
def archive_fa_results(fa_result_dirs, archive_subdir_name):
    """Archive FA result directories to permanent storage"""
    # Same implementation as SIP workflow
    # Moves entire FA result directories to archived_files/{archive_subdir_name}/
```

#### Main Program Integration
```python
# Archive FA results before creating success marker
if fa_result_dirs_to_archive:
    archive_fa_results(fa_result_dirs_to_archive, "first_lib_attempt_fa_results")

# Create success marker
create_success_marker()
```

### Cross-Workflow Compatibility

The SPS-CE implementation uses the same archive directory names as SIP for the first two attempts:
- `first_lib_attempt_fa_results` (shared between SIP and SPS-CE)
- `second_lib_attempt_fa_results` (shared between SIP and SPS-CE)
- `third_lib_attempt_fa_results` (SIP only - emergency third attempt)

This design ensures:
1. **Unified exclusion patterns**: Workflow manager exclusions work for both workflows
2. **Consistent user experience**: Same archive structure across workflows
3. **No conflicts**: Different workflows can coexist in the same project
```

#### 4.2 User Guide Updates

**Target File**: [`docs/user_guide/FEATURES.md`](../docs/user_guide/FEATURES.md)

**Required Updates** (lines 130-156):

```markdown
## Fragment Analyzer (FA) Results Archiving

The workflow manager includes an intelligent archiving system for Fragment Analyzer results that preserves valuable data while maintaining workflow flexibility across both SIP and SPS-CE workflows.

-   **Automatic Archiving**: When FA analysis scripts complete successfully, they automatically move FA result directories to a permanent archive location (`archived_files/`).
-   **Multi-Workflow Support**: 
    -   **SIP Workflow**: Supports first, second, and emergency third attempt archiving
    -   **SPS-CE Workflow**: Supports first and second attempt archiving
-   **Persistent Archives**: Archived FA results are excluded from the undo system, ensuring that valuable experimental data is never lost during workflow operations.
-   **Smart Directory Management**:
    -   FA result directories are moved to organized archive folders (`first_lib_attempt_fa_results/`, `second_lib_attempt_fa_results/`, `third_lib_attempt_fa_results/`)
    -   Empty parent directories are automatically cleaned up after archiving
    -   Existing archives are replaced when scripts are re-run, preventing duplicate data accumulation
-   **Undo-Safe Operation**: While the workflow can be undone to previous states, archived FA results remain safely preserved and accessible in the archive folders.
-   **Transparent Process**: The archiving process provides clear console output showing which directories are being archived and cleaned up.

### Archive Structure
```
archived_files/
├── first_lib_attempt_fa_results/
│   ├── PLATE1F 10-05-53/          # SIP or SPS-CE first attempt results
│   └── PLATE2F 12-34-56/
├── second_lib_attempt_fa_results/
│   ├── PLATE1F 14-22-11/          # SIP or SPS-CE second attempt results
│   └── PLATE2F 15-45-33/
└── third_lib_attempt_fa_results/   # SIP only - emergency third attempt
    └── PLATE1F 16-12-45/
```

### Workflow-Specific Features

#### SPS-CE Workflow
- **Steps 2 & 5**: [`SPS_first_FA_output_analysis_NEW.py`](../../templates/sps_workflow.yml) and [`SPS_second_FA_output_analysis_NEW.py`](../../templates/sps_workflow.yml)
- **Archive Integration**: Automatic archiving after successful FA analysis completion
- **Directory Structure**: `B_first_attempt_fa_result/` → `first_lib_attempt_fa_results/`, `D_second_attempt_fa_result/` → `second_lib_attempt_fa_results/`

#### SIP Workflow  
- **Steps 8, 11, & 14**: First, second, and emergency third FA analysis scripts
- **Archive Integration**: Complete three-tier archiving system
- **Directory Structure**: `B_first_attempt_fa_result/` → `first_lib_attempt_fa_results/`, etc.

This feature ensures that your Fragment Analyzer data is always preserved across both SIP and SPS-CE workflows, even when using the workflow manager's powerful undo capabilities to iterate on your analysis parameters.
```

### 5. Testing Strategy

#### 5.1 Unit Tests for SPS-CE FA Archiving

**Test File**: `tests/test_sps_ce_fa_archiving.py`

**Test Cases**:
```python
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

class TestSPSCEFAArchiving:
    
    def test_enhanced_getFAfiles_returns_both_lists(self):
        """Test that enhanced getFAfiles returns both fa_files and fa_result_dirs_to_archive"""
        # Test implementation
        pass
    
    def test_archive_fa_results_creates_directory_structure(self):
        """Test that archive_fa_results creates proper directory structure"""
        # Test implementation
        pass
    
    def test_archive_fa_results_handles_existing_archives(self):
        """Test that existing archives are properly replaced"""
        # Test implementation
        pass
    
    def test_archive_fa_results_cleans_empty_directories(self):
        """Test that empty parent directories are cleaned up"""
        # Test implementation
        pass
    
    def test_first_attempt_archiving_integration(self):
        """Test full integration of first attempt FA archiving"""
        # Test implementation
        pass
    
    def test_second_attempt_archiving_integration(self):
        """Test full integration of second attempt FA archiving"""
        # Test implementation
        pass
```

#### 5.2 Integration Tests with Workflow Manager

**Test File**: `tests/test_sps_ce_workflow_manager_integration.py`

**Test Cases**:
```python
class TestSPSCEWorkflowManagerIntegration:
    
    def test_sps_ce_archives_excluded_from_snapshots(self):
        """Test that SPS-CE FA archives are excluded from workflow snapshots"""
        # Test implementation
        pass
    
    def test_sps_ce_archives_preserved_during_undo(self):
        """Test that SPS-CE FA archives are preserved during undo operations"""
        # Test implementation
        pass
    
    def test_mixed_sip_sps_ce_archive_handling(self):
        """Test that SIP and SPS-CE archives can coexist"""
        # Test implementation
        pass
```

#### 5.3 Validation Tests for Undo/Rollback Behavior

**Test Scenarios**:
1. **Archive Persistence**: Verify archives remain after workflow undo
2. **Directory Recreation**: Verify FA result directories are recreated from snapshots
3. **Cross-Workflow Compatibility**: Verify SIP and SPS-CE archives don't interfere

### 6. Implementation Sequence

#### Phase 1: Core Script Modifications
1. **Modify SPS_first_FA_output_analysis_NEW.py**:
   - Enhance `getFAfiles()` function (lines 91-142)
   - Add `archive_fa_results()` function
   - Update `main()` function integration (lines 387-426)

2. **Modify SPS_second_FA_output_analysis_NEW.py**:
   - Enhance `getFAfiles()` function (lines 103-189)
   - Add `archive_fa_results()` function  
   - Update `main()` function integration (lines 506-550)

#### Phase 2: Documentation Updates
3. **Update developer documentation** ([`docs/developer_guide/fa_results_archiving.md`](../docs/developer_guide/fa_results_archiving.md))
4. **Update user guide documentation** ([`docs/user_guide/FEATURES.md`](../docs/user_guide/FEATURES.md))

#### Phase 3: Testing Implementation
5. **Create unit tests** for SPS-CE FA archiving functionality
6. **Create integration tests** with workflow manager
7. **Validate undo/rollback behavior** with archived FA results

#### Phase 4: Validation and Rollback Planning
8. **Manual testing procedures** for each implementation step
9. **Automated test requirements** validation
10. **Rollback plan** if issues arise

### 7. Validation Criteria

#### 7.1 Success Criteria for Each Implementation Step

**Script Modifications**:
- [ ] Enhanced `getFAfiles()` functions return both `fa_files` and `fa_result_dirs_to_archive`
- [ ] `archive_fa_results()` function successfully moves FA directories to archive
- [ ] Main functions integrate archiving calls before success marker creation
- [ ] Scripts maintain backward compatibility with existing functionality

**Workflow Manager Integration**:
- [ ] Existing exclusion patterns in [`src/logic.py`](../src/logic.py) cover SPS-CE archives
- [ ] Snapshot creation excludes SPS-CE FA archive directories
- [ ] Snapshot restoration preserves SPS-CE FA archive directories
- [ ] Undo operations maintain archived FA results

**Documentation Updates**:
- [ ] Developer guide includes SPS-CE archiving implementation details
- [ ] User guide documents SPS-CE archiving features
- [ ] Documentation reflects cross-workflow compatibility

**Testing**:
- [ ] Unit tests validate individual archiving functions
- [ ] Integration tests validate workflow manager compatibility
- [ ] Manual testing confirms end-to-end functionality

#### 7.2 Manual Testing Procedures

**Test Procedure 1: First Attempt FA Archiving**
1. Set up SPS-CE project with FA result directories in `B_first_attempt_fa_result/`
2. Run `SPS_first_FA_output_analysis_NEW.py`
3. Verify FA result directories moved to `archived_files/first_lib_attempt_fa_results/`
4. Verify empty parent directories cleaned up
5. Verify success marker created

**Test Procedure 2: Second Attempt FA Archiving**
1. Set up SPS-CE project with FA result directories in `D_second_attempt_fa_result/`
2. Run `SPS_second_FA_output_analysis_NEW.py`
3. Verify FA result directories moved to `archived_files/second_lib_attempt_fa_results/`
4. Verify empty parent directories cleaned up
5. Verify success marker created

**Test Procedure 3: Workflow Manager Integration**
1. Complete Test Procedures 1 & 2
2. Use workflow manager undo functionality
3. Verify archived FA results remain in `archived_files/`
4. Verify workflow state properly restored
5. Verify no conflicts with existing SIP archives

#### 7.3 Automated Test Requirements

**Coverage Requirements**:
- [ ] 100% function coverage for new `archive_fa_results()` functions
- [ ] 100% line coverage for modified `getFAfiles()` functions
- [ ] 100% integration coverage for workflow manager exclusion patterns

**Performance Requirements**:
- [ ] Archive operations complete within 30 seconds for typical FA result sizes
- [ ] No significant impact on script execution time (< 5% increase)
- [ ] Memory usage remains within acceptable limits during archiving

### 8. Rollback Plan

#### 8.1 Rollback Triggers
- Script modifications cause FA analysis failures
- Archive operations fail or corrupt data
- Workflow manager integration issues
- Performance degradation beyond acceptable limits

#### 8.2 Rollback Procedures

**Phase 1 Rollback** (Script Modifications):
1. Revert [`SPS_first_FA_output_analysis_NEW.py`](../SPS_library_creation_scripts/SPS_first_FA_output_analysis_NEW.py) to original version
2. Revert [`SPS_second_FA_output_analysis_NEW.py`](../SPS_library_creation_scripts/SPS_second_FA_output_analysis_NEW.py) to original version
3. Remove any created archive directories
4. Validate original functionality restored

**Phase 2 Rollback** (Documentation):
1. Revert documentation changes
2. Remove references to SPS-CE archiving
3. Restore original feature descriptions

**Phase 3 Rollback** (Testing):
1. Remove test files
2. Revert any test configuration changes
3. Restore original test suite

#### 8.3 Data Recovery Procedures
- **Archive Recovery**: Manual restoration of archived FA results to original locations
- **Snapshot Recovery**: Use workflow manager snapshots to restore pre-implementation state
- **Backup Validation**: Verify all original FA data preserved during rollback

## Conclusion

This implementation plan provides a comprehensive roadmap for adding FA archiving functionality to the SPS-CE workflow while maintaining full compatibility with the existing SIP implementation. The plan leverages proven patterns from the working SIP implementation and ensures seamless integration with the workflow manager's undo system.

**Key Benefits**:
- **Unified Architecture**: Consistent archiving across SIP and SPS-CE workflows
- **Data Preservation**: Valuable FA results protected during workflow operations  
- **Backward Compatibility**: No impact on existing functionality
- **Comprehensive Testing**: Thorough validation of all integration points

**Implementation Timeline**: 
- **Phase 1**: 2-3 days (script modifications)
- **Phase 2**: 1 day (documentation updates)
- **Phase 3**: 2-3 days (testing implementation)
- **Phase 4**: 1-2 days (validation and rollback planning)

**Total Estimated Effort**: 6-9 days for complete implementation and validation.