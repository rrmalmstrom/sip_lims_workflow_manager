# Deterministic Development Workflow

## Simple Git-Based Environment Management with Separate Scripts

This is the **industry standard** approach for managing deterministic builds during development.

## Available Scripts

### 1. **`build_image_from_lock_files.sh`**
- Builds local Docker image from existing lock files
- Creates: `sip-lims-workflow-manager:latest` (local)
- Use: When you want to build from current stable lock files

### 2. **`push_image_to_github.sh`**
- Tags and pushes local image to GitHub Container Registry
- Creates: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest` (remote)
- Use: After building and testing locally

### 3. **`generate_lock_files.sh`**
- Extracts lock files from a working Docker image
- Creates: New `conda-lock.txt` and `requirements-lock.txt`
- Use: During development when you want to freeze new package versions

## Your Development Workflow

### 1. **Stable Production (main branch)**
```bash
# Your main branch has working lock files
git checkout main
./build_image_from_lock_files.sh    # Build from stable locks
./push_image_to_github.sh           # Push to users
```

### 2. **Experiment Safely (feature branches)**
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

# Build deterministic image from new lock files
./build_image_from_lock_files.sh

# Test locally using development mode
./run.command  # Choose development mode, uses sip-lims-workflow-manager:latest
```

### 3. **If Experiment Works**
```bash
# Commit the new lock files
git add conda-lock.txt requirements-lock.txt archive/environment-docker-final-validated.yml
git commit -m "Add new package XYZ"

# Merge to main
git checkout main
git merge experiment/new-package

# Build and push to users
./build_image_from_lock_files.sh
./push_image_to_github.sh
```

### 4. **If Experiment Fails**
```bash
# Just switch back to main - git handles everything
git checkout main

# Your stable lock files are automatically restored
# No complex version management needed!
```

## Integration with run.command

### **Production Mode**
- Uses: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest` (remote)
- Auto-updates from GitHub Container Registry
- For end users

### **Development Mode**
- Uses: `sip-lims-workflow-manager:latest` (local)
- Uses your locally built image
- For testing new builds

## Key Benefits

✅ **Deterministic**: Lock files ensure exact same packages every time
✅ **Safe**: Git branches let you experiment without losing stable state
✅ **Clear Separation**: Build vs Push vs Lock Generation are separate steps
✅ **Local Testing**: Test locally before pushing to users
✅ **Industry Standard**: Standard git workflow everyone knows

## Quick Reference

```bash
# Build from current lock files
./build_image_from_lock_files.sh

# Test locally
./run.command  # Choose development mode

# Push to users
./push_image_to_github.sh

# Create new lock files (during development)
./generate_lock_files.sh
```

## That's It!

No complex version management scripts. Clear separation of build, test, and deploy steps. Simple and reliable.