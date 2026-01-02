# Docker Build Strategy Executive Summary

## Overview

The SIP LIMS Workflow Manager uses a sophisticated **branch-aware deterministic Docker system** that creates separate, reproducible Docker images for different Git branches. This strategy enables safe development while maintaining stable production environments through precise version control integration.

## Critical Development Workflow Order

### Development Sequence (IMPORTANT)

The update detection logic requires a specific order to maintain SHA synchronization:

1. **Make code changes** on development branch
2. **Test locally** using development mode
3. **Generate new lock files** (if packages changed): `./build/generate_lock_files.sh`
4. **Commit all changes**: `git add . && git commit -m "Description"`
5. **Push Git changes**: `git push origin your-branch`
6. **Build Docker image**: `./build/build_image_from_lock_files.sh`
7. **Push Docker image**: `./build/push_image_to_github.sh`
8. **Test final image** locally
9. **Merge to main** when ready for production

### Why This Order Matters

The update detector compares:
- **Local**: SHA embedded in Docker image (from when image was built)
- **Remote**: Current HEAD SHA from Git branch

If you build the Docker image before committing to Git, the image SHA will be older than the remote Git SHA, causing false "update available" notifications.

## Core Architecture

### 1. Deterministic Lock Files System

The foundation of reproducible builds relies on exact package specifications:

- **[`conda-lock.txt`](../conda-lock.txt)**: Contains 44 conda packages with specific build hashes and URLs
- **[`requirements-lock.txt`](../requirements-lock.txt)**: Contains 65 pip packages with exact version pins
- **[`Dockerfile`](../Dockerfile)**: Uses SHA-pinned base image (`continuumio/miniconda3@sha256:...`) and lock files
- **[`build/base-image-info.txt`](../build/base-image-info.txt)**: Tracks base image SHA for reproducibility

### 2. Branch-Aware Image Naming

Each Git branch automatically maps to its own Docker image namespace:

| Git Branch | Docker Tag | Local Image | Remote Image |
|------------|------------|-------------|--------------|
| `main` | `main` | `sip-lims-workflow-manager:main` | `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main` |
| `analysis/esp-docker-adaptation` | `analysis-esp-docker-adaptation` | `sip-lims-workflow-manager:analysis-esp-docker-adaptation` | `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation` |

This isolation prevents development work from affecting production users.

### 3. Build Pipeline Scripts

Three core scripts manage the Docker lifecycle:

#### [`build/generate_lock_files.sh`](../build/generate_lock_files.sh)
- Extracts exact package versions from a working Docker image
- Creates new lock files when dependencies change
- Ensures deterministic package specifications

#### [`build/build_image_from_lock_files.sh`](../build/build_image_from_lock_files.sh)
- Builds local Docker image using current lock files
- Embeds Git commit SHA as Docker image labels
- Creates branch-specific image tags automatically

#### [`build/push_image_to_github.sh`](../build/push_image_to_github.sh)
- Tags local image for GitHub Container Registry
- Pushes to branch-specific remote location
- Makes image available for production users

### 4. Intelligent Update Detection

The [`src/update_detector.py`](../src/update_detector.py) system provides sophisticated version comparison:

#### Key Comparison Logic
- **Local SHA**: Extracted from Docker image labels (`com.sip-lims.commit-sha`)
- **Remote SHA**: Current HEAD commit from GitHub API for the branch
- **Chronology Checking**: Uses Git ancestry and timestamp comparison
- **Safety Features**: Warns when chronology is uncertain

#### Update Decision Process
1. Compare local Docker image SHA vs remote Git branch HEAD SHA
2. Use `git merge-base` to determine chronological order
3. Fallback to timestamp comparison if ancestry check fails
4. Require user confirmation when chronology is uncertain

### 5. Run Scripts with Auto-Update

The [`run.mac.command`](../run.mac.command) and [`run.windows.bat`](../run.windows.bat) scripts:

- Auto-detect current Git branch
- Select appropriate Docker image (local vs remote)
- Check for updates using SHA comparison
- Support both production (auto-update) and development (local build) modes

## Version Control Integration

### Git Commit SHA as Source of Truth

- Docker images are labeled with the exact Git commit SHA they were built from
- Update detection uses Git commit SHAs rather than Docker image timestamps
- This ensures Docker images stay synchronized with Git repository state
- Enables precise tracking of what code version is running in production

### Branch Isolation Benefits

- **Developers**: Can work on feature branches without affecting main branch users
- **Users**: Always get stable, tested images from main branch
- **Testing**: Each branch can have its own Docker image for isolated testing
- **Rollback**: Easy to revert to previous commit/image combinations

## Safety and Reliability Features

### Deterministic Builds
- Lock files ensure identical package versions across all environments
- SHA-pinned base image prevents base image drift
- Reproducible builds enable reliable testing and deployment

### Chronology Protection
- Prevents overwriting newer local versions with older remote versions
- Git ancestry checking provides reliable chronological ordering
- User confirmation required when chronology cannot be determined

### Branch Safety
- Development branches isolated from production
- No accidental overwrites of main branch images
- Clear separation between local development and remote production images

## Production vs Development Modes

### Production Mode
- Uses remote Docker images (`ghcr.io/rrmalmstrom/sip_lims_workflow_manager:<branch>`)
- Automatic updates when new images are available
- Centralized script management
- Suitable for end users

### Development Mode
- Uses local Docker images (`sip-lims-workflow-manager:<branch>`)
- No automatic updates (uses local builds)
- Local script development
- Suitable for developers testing changes

## Summary

This Docker build strategy provides:

✅ **Reproducible Environments**: Lock files ensure identical package versions  
✅ **Branch Isolation**: Safe development without affecting production  
✅ **Intelligent Updates**: SHA-based version comparison with chronology checking  
✅ **Developer Flexibility**: Local development mode with branch-specific images  
✅ **User Safety**: Production mode with automatic, safe updates  
✅ **Version Synchronization**: Git commits and Docker images stay aligned  

The system balances developer productivity with production stability through careful orchestration of Git version control, Docker image management, and intelligent update detection.