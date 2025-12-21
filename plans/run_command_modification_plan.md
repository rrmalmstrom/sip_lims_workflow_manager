# run.command Modification Plan

## Current Analysis
The current [`run.command`](../run.command) has some functionality we need but is missing the core update detection logic.

## What to KEEP (works correctly):
- Developer mode detection via `config/developer.marker` (lines 18-24)
- User ID detection for permissions (lines 12-16)
- Docker-compose architecture (line 125)
- Project path drag-drop functionality (lines 89-112)

## What to ADD (completely new functionality):

### 1. Production User Auto-Update Flow
**Currently missing - needs to be added**
- Check local Docker image version vs GitHub Container Registry
- Auto-pull newer Docker image if available
- Check/create `~/.sip_lims_workflow_manager/scripts` directory
- Auto-download scripts from GitHub if missing/outdated
- Set `SCRIPTS_PATH` to centralized location
- No user prompts - completely silent

### 2. Docker Image Update Detection
**Currently missing - needs to be added**
- Compare local Docker image commit SHA vs remote
- Use `docker inspect` to get local image labels
- Use GitHub API to get latest commit SHA
- Auto-pull if different

### 3. Scripts Auto-Download
**Currently missing - needs to be added**
- Download scripts to `~/.sip_lims_workflow_manager/scripts`
- Compare local commit SHA vs remote
- Extract from GitHub zip download
- Store commit SHA for future comparisons

### 4. Developer Mode Choice
**Currently missing - needs to be added**
- When developer marker detected, ask: "Production mode or Development mode?"
- Production mode: Same behavior as regular production users (auto-updates)
- Development mode: Skip updates, prompt for local scripts path

## What to MODIFY (existing functionality):

### 5. Current Script Path Selection (lines 28-74)
**Current behavior:** Always prompts developers for `../sip_scripts_dev` vs `../sip_scripts_prod`
**New behavior:** 
- Only prompt in developer development mode
- In developer production mode, use auto-updates instead
- In regular production mode, no prompts at all

### 6. Production User Behavior
**Current behavior:** Production users get prompted for script paths like developers
**New behavior:** Production users get silent auto-updates with no prompts

## Implementation Order:
1. Add Docker image update detection functions
2. Add scripts auto-download functions  
3. Add production user auto-update flow
4. Modify developer mode to include production/development choice
5. Update script path selection to only apply in development mode

## Dependencies:
- GitHub Actions workflow to publish pre-built Docker images
- Dockerfile modifications to include commit SHA labels
- GitHub Container Registry setup