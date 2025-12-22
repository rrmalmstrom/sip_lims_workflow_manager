# Branch-Aware Docker Workflow Guide

## Overview

The SIP LIMS Workflow Manager now uses a **branch-aware Docker system** that automatically creates separate Docker images for different Git branches. This enables developers to work on development branches while users get stable main branch images.

## Key Concepts

### Branch-to-Tag Mapping
- **Branch**: `main` → **Docker Tag**: `:main`
- **Branch**: `analysis/esp-docker-adaptation` → **Docker Tag**: `:analysis-esp-docker-adaptation`
- **Branch**: `feature/new-analysis` → **Docker Tag**: `:feature-new-analysis`

### Image Naming Convention
- **Local Images**: `sip-lims-workflow-manager:<branch-tag>`
- **Remote Images**: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:<branch-tag>`

### Docker Image Tagging Process
When you push an image, the system creates **two local copies**:
1. **Original**: `sip-lims-workflow-manager:analysis-esp-docker-adaptation`
2. **Tagged Copy**: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation`

Both have the same Image ID - this is standard Docker behavior and **not a problem**.

## Available Scripts

### 1. **`build_image_from_lock_files.sh`** (Branch-Aware)
- Builds local Docker image from existing lock files
- **Creates**: `sip-lims-workflow-manager:<current-branch-tag>` (local)
- **Auto-detects**: Current Git branch and generates appropriate tag
- **Use**: When you want to build from current stable lock files

**Example Output**:
```bash
🌿 Detecting branch and generating tags...
   ✅ Current branch: analysis/esp-docker-adaptation
   ✅ Docker tag: analysis-esp-docker-adaptation
   ✅ Local image: sip-lims-workflow-manager:analysis-esp-docker-adaptation
```

### 2. **`push_image_to_github.sh`** (Branch-Aware)
- Tags and pushes local image to GitHub Container Registry
- **Creates**: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:<current-branch-tag>` (remote)
- **Auto-detects**: Current Git branch and pushes to appropriate registry location
- **Use**: After building and testing locally

**Example Output**:
```bash
🏷️  Tagging image for GitHub Container Registry...
📤 Pushing to GitHub Container Registry...
   Registry: ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation
```

### 3. **`run.command`** (Branch-Aware)
- Automatically selects correct Docker image based on current branch
- **Production Mode**: Uses `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:<current-branch-tag>`
- **Development Mode**: Uses `sip-lims-workflow-manager:<current-branch-tag>`
- **Auto-detects**: Updates available by comparing local vs remote images

### 4. **`generate_lock_files.sh`**
- Extracts lock files from a working Docker image
- Creates: New `conda-lock.txt` and `requirements-lock.txt`
- Use: During development when you want to freeze new package versions

## Branch-Aware Development Workflow

### 1. **Stable Production (main branch)**
```bash
# Your main branch has working lock files
git checkout main
./build_image_from_lock_files.sh    # Build: sip-lims-workflow-manager:main
./push_image_to_github.sh           # Push: ghcr.io/.../sip_lims_workflow_manager:main
```

### 2. **Development Branch Work**
```bash
# Create or switch to development branch
git checkout analysis/esp-docker-adaptation

# Build branch-specific image
./build_image_from_lock_files.sh    # Build: sip-lims-workflow-manager:analysis-esp-docker-adaptation

# Test locally using development mode
./run.command  # Choose development mode, uses branch-specific local image

# Push to branch-specific remote location
./push_image_to_github.sh           # Push: ghcr.io/.../sip_lims_workflow_manager:analysis-esp-docker-adaptation
```

### 3. **Experiment Safely (feature branches)**
```bash
# Create experiment branch
git checkout -b experiment/new-package

# Modify environment
nano archive/environment-docker-final-validated.yml  # Add new package

# Build test image from environment.yml (manual docker build)
docker build -f - -t test-image . <<EOF
FROM continuumio/miniconda3@sha256:...
COPY archive/environment-docker-final-validated.yml ./environment.yml
RUN conda env create -f environment.yml
# ... rest of build steps ...
EOF

# Extract new lock files from test image
./generate_lock_files.sh

# Build deterministic image from new lock files (branch-aware)
./build_image_from_lock_files.sh    # Build: sip-lims-workflow-manager:experiment-new-package

# Test locally using development mode
./run.command  # Choose development mode, uses branch-specific image
```

### 4. **If Experiment Works**
```bash
# Commit the new lock files
git add conda-lock.txt requirements-lock.txt archive/environment-docker-final-validated.yml
git commit -m "Add new package XYZ"

# Push branch-specific image
./push_image_to_github.sh           # Push: ghcr.io/.../sip_lims_workflow_manager:experiment-new-package

# Merge to main
git checkout main
git merge experiment/new-package

# Build and push main branch image
./build_image_from_lock_files.sh    # Build: sip-lims-workflow-manager:main
./push_image_to_github.sh           # Push: ghcr.io/.../sip_lims_workflow_manager:main
```

## Update Detection System

### How It Works
The system compares:
- **Local**: SHA from pulled remote image (e.g., `ghcr.io/.../sip_lims_workflow_manager:analysis-esp-docker-adaptation`)
- **Remote**: Current Git commit SHA from GitHub API for current branch

### Update Scenarios
1. **No Update Needed**: Local and remote SHAs match
2. **Update Available**: Remote Git commit is newer than local image
3. **Local Ahead**: Local image is newer than remote Git commit (developer scenario)

### Branch-Aware Update Detection
```bash
# run.command automatically:
# 1. Detects current branch: analysis/esp-docker-adaptation
# 2. Checks for updates using branch-specific tag
# 3. Pulls from: ghcr.io/.../sip_lims_workflow_manager:analysis-esp-docker-adaptation
# 4. Compares with GitHub API for analysis/esp-docker-adaptation branch
```

## Integration with run.command

### **Production Mode** (Branch-Aware)
- **Uses**: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:<current-branch-tag>` (remote)
- **Auto-updates**: From GitHub Container Registry using branch-specific location
- **For**: End users and developers wanting latest branch-specific image

### **Development Mode** (Branch-Aware)
- **Uses**: `sip-lims-workflow-manager:<current-branch-tag>` (local)
- **Uses**: Your locally built branch-specific image
- **For**: Testing new builds before pushing

## Key Benefits

✅ **Branch Isolation**: Each branch has its own Docker images
✅ **Automatic Detection**: Scripts auto-detect current branch
✅ **Developer-Friendly**: Developers can work on dev branches without affecting main
✅ **User-Safe**: Users on main branch get stable images
✅ **Deterministic**: Lock files ensure exact same packages every time
✅ **Safe Experimentation**: Git branches let you experiment without losing stable state
✅ **Clear Separation**: Build vs Push vs Lock Generation are separate steps
✅ **Local Testing**: Test locally before pushing to users

## Docker Desktop Behavior

When you push an image, you'll see **two entries** in Docker Desktop:
1. `sip-lims-workflow-manager:analysis-esp-docker-adaptation`
2. `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation`

Both have the **same Image ID** - they're the same image data with different tags. This is **normal Docker behavior**.

## Quick Reference

```bash
# Build from current lock files (branch-aware)
./build_image_from_lock_files.sh

# Test locally (uses branch-specific image)
./run.command  # Choose development mode

# Push to branch-specific remote location
./push_image_to_github.sh

# Create new lock files (during development)
./generate_lock_files.sh

# Run with auto-updates (uses branch-specific remote image)
./run.command  # Choose production mode
```

## Branch Examples

| Git Branch | Docker Tag | Local Image | Remote Image |
|------------|------------|-------------|--------------|
| `main` | `main` | `sip-lims-workflow-manager:main` | `ghcr.io/.../sip_lims_workflow_manager:main` |
| `analysis/esp-docker-adaptation` | `analysis-esp-docker-adaptation` | `sip-lims-workflow-manager:analysis-esp-docker-adaptation` | `ghcr.io/.../sip_lims_workflow_manager:analysis-esp-docker-adaptation` |
| `feature/new-analysis` | `feature-new-analysis` | `sip-lims-workflow-manager:feature-new-analysis` | `ghcr.io/.../sip_lims_workflow_manager:feature-new-analysis` |

## That's It!

The branch-aware system automatically handles Docker image management based on your current Git branch. No manual tag specification needed - just run the scripts and they'll do the right thing!