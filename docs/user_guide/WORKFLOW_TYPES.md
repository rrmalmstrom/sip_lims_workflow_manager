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
The SPS-CE workflow is a focused 9-step process for SPS library creation with Fragment Analyzer integration.

### Workflow Steps (9 Total)
1. **Initiate Project & Make Sort Plate Labels**: Create the standardized project folder structure, read `sample_metadata.csv`, generate barcode labels for sort plates, create plate layout CSVs, and initialize `project_summary.db`. Supports re-runs to add additional plates.
2. **Process WGA Results**: Read WGA (Whole Genome Amplification) kinetics summary files, filter to passing samples, sort by amplification quality, and generate `summary_MDA_results.csv`.
3. **Read WGA Summary & Make SPITS**: Read `summary_MDA_results.csv`, assign Illumina indexes, generate the JGI SPITS sequencing submission CSV, and update `project_summary.db` with master plate data.
4. **Make Illumina Index and FA Files**: Generate index files and Fragment Analyzer inputs
5. **First FA Output Analysis**: Analyze initial Fragment Analyzer results
6. **Decision: Second Attempt Needed?**: Determine if additional rework is required
7. **Rework First Attempt**: Rework samples based on analysis
8. **Second FA Output Analysis**: Analyze second round results
9. **Conclude FA Analysis and Generate ESP Smear File**: Finalize analysis and generate submission files

### Use Cases
- SPS library creation workflows
- Fragment Analyzer integration
- Iterative sample rework processes
- Decision-based workflow branching

### Repository
- **Scripts**: `SPS_library_creation_scripts`
- **Location**: `~/.sip_lims_workflow_manager/sps-ce_scripts`

## Capsule Sorting Workflow

### Overview
The Capsule Sorting workflow is a focused 6-step process for capsule sorting and preparation for downstream analysis.

### Workflow Steps (6 Total)
1. **Initiate Project / Make Sort Labels**: Set up project structure and generate sorting labels
2. **Generate Lib Creation Files**: Create library preparation files and configurations
3. **Analyze FA data**: Analyze Fragment Analyzer data for quality control
4. **Create SPITS file**: Generate SPITS (Sample Preparation Information Tracking System) files
5. **Process Grid Tables & Generate Barcodes**: Process grid table data and generate barcode information
6. **Verify Scanning & Generate ESP Files**: Verify scanning results and generate ESP (Electronic Sample Processing) files

### Use Cases
- Capsule sorting and preparation workflows
- Single-cell sorting preparation
- Downstream analysis preparation
- Quality control and verification processes

### Repository
- **Scripts**: `capsule-single-cell-sort-scripts`
- **Location**: `~/.sip_lims_workflow_manager/capsule-sorting_scripts`

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

### When to Use Capsule Sorting Workflow
- Capsule sorting and preparation processes
- Single-cell sorting preparation
- Downstream analysis preparation workflows
- Quality control and verification processes

## Technical Implementation

### Backward Compatibility
- **Existing SIP users**: No changes required - workflows continue to work identically
- **Default behavior**: System defaults to SIP workflow if no type is specified
- **Migration**: No migration required for existing projects

### Workflow Switching
- Users can switch between workflow types by restarting the application
- Each workflow type maintains separate script repositories and configurations
- No cross-contamination between workflow types

### Execution Modes
Both workflow types support:
- **Production Mode**: Automated script management and native Python execution
- **Development Mode**: Local script directory mounting for development and testing
- **Native Performance**: Direct Python execution for optimal performance and debugging capabilities