# Workflow Types Guide

The SIP LIMS Workflow Manager supports multiple laboratory workflow types, each optimized for specific laboratory processes.

## SIP (Stable Isotope Probing) Workflow

### Overview
The SIP workflow is a comprehensive 21-step process for stable isotope probing fractionation and library preparation.

### Workflow Steps (21 Total)
1. **Setup & Preparation** (Steps 1-7): Plate setup, ultracentrifuge transfer, QC plotting, database creation
2. **Library Creation** (Steps 8-13): Multiple attempts with QC analysis between each attempt
3. **Final Processing** (Steps 14-21): Summary generation, pool assignment, final QC, and tube transfer

### Use Cases
- Complete SIP fractionation workflows
- Library preparation with multiple QC checkpoints
- Complex multi-step laboratory processes requiring state management

### Repository
- **Scripts**: `sip_scripts_workflow_gui`
- **Location**: `~/.sip_lims_workflow_manager/sip_scripts`

## SPS-CE (SPS-Capillary Electrophoresis) Workflow

### Overview
The SPS-CE workflow is a focused 6-step process for SPS library creation with Fragment Analyzer integration.

### Workflow Steps (6 Total)
1. **Make Illumina Index and FA Files**: Generate index files and Fragment Analyzer inputs
2. **First FA Output Analysis**: Analyze initial Fragment Analyzer results
3. **Rework First Attempt**: Rework samples based on analysis
4. **Second FA Output Analysis**: Analyze second round results
5. **Decision: Second Attempt Needed?**: Determine if additional rework is required
6. **Conclude FA Analysis and Generate ESP Smear File**: Finalize analysis and generate submission files

### Use Cases
- SPS library creation workflows
- Fragment Analyzer integration
- Iterative sample rework processes
- Decision-based workflow branching

### Repository
- **Scripts**: `SPS_library_creation_scripts`
- **Location**: `~/.sip_lims_workflow_manager/sps-ce_scripts`

## Choosing the Right Workflow

### When to Use SIP Workflow
- Comprehensive fractionation processes
- Multi-step library preparation
- Complex QC and validation requirements
- Long-running laboratory processes

### When to Use SPS-CE Workflow
- Focused SPS library creation
- Fragment Analyzer-based workflows
- Iterative sample processing
- Decision-driven workflow progression

## Technical Implementation

### Backward Compatibility
- **Existing SIP users**: No changes required - workflows continue to work identically
- **Default behavior**: System defaults to SIP workflow if no type is specified
- **Migration**: No migration required for existing projects

### Workflow Switching
- Users can switch between workflow types by restarting the application
- Each workflow type maintains separate script repositories and configurations
- No cross-contamination between workflow types

### Development vs Production
Both workflow types support:
- **Production Mode**: Automated script management and Docker deployment
- **Development Mode**: Local script directory mounting for development and testing