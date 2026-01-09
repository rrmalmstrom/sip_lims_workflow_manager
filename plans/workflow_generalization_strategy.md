# Workflow Manager Generalization Strategy

## Overview
Strategy to generalize the SIP LIMS Workflow Manager to support multiple laboratory processes while maintaining backward compatibility and avoiding migration complexity.

## Core Strategy Decisions

### Repository and Naming
- **Keep main repository name**: `sip_lims_workflow_manager` (avoid migration pain)
- **Change UI title**: "SIP LIMS Workflow Manager" → "LIMS Workflow Manager"
- **Keep Docker image name**: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager`

### Workflow Selection
- **Run script selection**: Add workflow choice before existing mode detection
  - `1` = SIP Fractionation and Library Prep
  - `2` = SPS-CE Workflow
- **Environment variable**: `WORKFLOW_TYPE=sip` or `WORKFLOW_TYPE=sps-ce`
- **Implementation**: Both [`run.mac.command`](run.mac.command) and [`run.windows.bat`](run.windows.bat)

### Template System
- **Current**: `templates/workflow.yml` (SIP-specific)
- **New structure**:
  - `templates/sip_workflow.yml` (rename current)
  - `templates/sps-ce_workflow.yml` (new template)
- **Project creation**: Copy appropriate template to `project/workflow.yml`
- **Runtime**: Always use `project/workflow.yml` (workflow-agnostic)

### Script Repository Structure
- **Current**: `$HOME/.sip_lims_workflow_manager/scripts`
- **New pattern**: `$HOME/.sip_lims_workflow_manager/{WORKFLOW_TYPE}_scripts`
- **Specific paths**:
  - SIP: `$HOME/.sip_lims_workflow_manager/sip_scripts`
  - SPS-CE: `$HOME/.sip_lims_workflow_manager/sps-ce_scripts`

### State Management
- **No changes needed**: `workflow_state.json` is generated dynamically from `workflow.yml`
- **No templates required**: State file created programmatically by `StateManager`

## Implementation Points

### Code Changes Required
1. **Template copying logic** in [`app.py`](app.py) (lines 733-740, 888-894, 932-936, 985-988)
2. **Script path generation** in [`run.mac.command`](run.mac.command) (line 232)
3. **Repository URL mapping** in [`src/git_update_manager.py`](src/git_update_manager.py)

### Workflow Flow
1. User runs script → Workflow selection prompt
2. Sets `WORKFLOW_TYPE` environment variable
3. Existing mode detection (production/developer)
4. Script repository selection based on `WORKFLOW_TYPE`
5. Docker launch with `WORKFLOW_TYPE` passed to container
6. Project creation uses `WORKFLOW_TYPE` for template selection
7. Runtime uses project's local `workflow.yml` (workflow-agnostic)

## Next Analysis Areas
- WORKFLOW_TYPE variable usage throughout system
- Docker deterministic build system and lock files
- Impact of different workflow dependencies on Docker images
- Version control for Docker images (local vs remote)