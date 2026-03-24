# Feature Documentation

This directory contains documentation for specific features and functionality within the sip_lims_workflow_manager.

## Contents

### Active Feature Documentation

- **[`fa_results_archiving.md`](fa_results_archiving.md)** - Fragment Analyzer results archiving implementation
  - Documents how FA data is preserved during undo operations
  - Describes the archival mechanism for maintaining data integrity

- **[`step_18_19_cyclical_workflow_analysis.md`](step_18_19_cyclical_workflow_analysis.md)** - Cyclical QC workflow analysis
  - Documents the cyclical QC workflow between pooling steps 18 and 19
  - Describes workflow behavior and state management for iterative QC processes

- **[`script_analysis_summary.md`](script_analysis_summary.md)** - Python pooling workflow scripts analysis
  - Documents the functionality and data flow of pooling workflow scripts
  - Provides analysis of script interactions and dependencies

## Feature Status

All documented features are **actively used** in the current Mac-native implementation and are maintained as part of the core workflow functionality.

## Related Documentation

- **Main Architecture**: [`../ARCHITECTURE.md`](../ARCHITECTURE.md) - Overall system architecture
- **Distribution**: [`../DISTRIBUTION_PACKAGE_SUMMARY.md`](../DISTRIBUTION_PACKAGE_SUMMARY.md) - Package distribution details
- **Workflow Types**: [`../../user_guide/WORKFLOW_TYPES.md`](../../user_guide/WORKFLOW_TYPES.md) - User-facing workflow documentation

## Implementation References

These features are implemented in:
- [`src/core.py`](../../../src/core.py) - Core workflow engine
- [`src/logic.py`](../../../src/logic.py) - Workflow logic and state management
- [`src/workflow_utils.py`](../../../src/workflow_utils.py) - Workflow utilities
- [`templates/`](../../../templates/) - Workflow template definitions