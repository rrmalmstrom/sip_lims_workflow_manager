# Complete Deterministic Docker Build Solution

## The Problem: Multiple Sources of Non-Determinism
1. **Conda**: Build hashes change (libsqlite example)
2. **Pip**: Package versions can update between builds
3. **Base Docker Image**: `continuumio/miniconda3:latest` can change
4. **System packages**: apt-get can pull different versions

## Complete Solution: Multi-Layer Pinning Strategy

### 1. Pin Base Docker Image by SHA
```dockerfile
# Instead of:
# FROM continuumio/miniconda3:latest

# Use exact SHA:
FROM continuumio/miniconda3@sha256:4a2425c3ca891633e5a27280120f3fb6d5960a0f509b7594632cdd5bb8cbaea8
```

### 2. Generate Complete Environment Snapshot
Create a script to capture EVERYTHING from your working build:

```bash
#!/bin/bash
# generate_complete_lockfile.sh
docker run --rm sip-lims-workflow-manager:latest bash -c "
echo '=== CONDA PACKAGES WITH BUILD HASHES ==='
conda list --explicit > /tmp/conda-explicit.txt
cat /tmp/conda-explicit.txt

echo -e '\n=== PIP PACKAGES WITH EXACT VERSIONS ==='
pip freeze > /tmp/pip-freeze.txt
cat /tmp/pip-freeze.txt

echo -e '\n=== SYSTEM PACKAGE VERSIONS ==='
dpkg -l | grep '^ii' > /tmp/system-packages.txt
cat /tmp/system-packages.txt
" > complete_environment_snapshot.txt
```

### 3. Create Locked Environment Files

#### conda-explicit.yml (with build hashes)
```yaml
# Generated from: conda list --explicit
# This locks EVERY conda package with exact build hash
name: sip-lims-workflow-manager
channels:
  - conda-forge
  - defaults
dependencies:
  - https://conda.anaconda.org/conda-forge/linux-aarch64/python-3.9.23-h0819846_0_cpython.conda
  - https://conda.anaconda.org/conda-forge/linux-aarch64/libsqlite-3.51.1-h022381a_0.conda
  - https://conda.anaconda.org/conda-forge/linux-aarch64/git-2.51.0-pl5321h1beed63_1.conda
  # ... ALL packages with exact URLs and build hashes
```

#### requirements-locked.txt (exact pip versions)
```
# Generated from: pip freeze
altair==5.5.0
attrs==25.3.0
blinker==1.9.0
# ... ALL pip packages with exact versions
```

### 4. Updated Dockerfile for Complete Determinism
```dockerfile
# Pin base image by SHA
FROM continuumio/miniconda3@sha256:4a2425c3ca891633e5a27280120f3fb6d5960a0f509b7594632cdd5bb8cbaea8

# Pin system package versions
RUN apt-get update && apt-get install -y \
    git=1:2.39.2-1.1 \
    curl=7.88.1-10+deb12u14 \
    wget=1.21.3-1+b2 \
    && rm -rf /var/lib/apt/lists/*

# Use explicit conda environment (with build hashes)
COPY conda-explicit.yml .
RUN conda env create --file conda-explicit.yml

# Use locked pip requirements
COPY requirements-locked.txt .
RUN /opt/conda/envs/sip-lims-workflow-manager/bin/pip install -r requirements-locked.txt --no-deps
```

### 5. Automated Lock File Generation
```bash
#!/bin/bash
# update_lockfiles.sh - Run this when you want to update the environment

echo "Generating complete lock files from working image..."

# Generate conda explicit list
docker run --rm sip-lims-workflow-manager:latest bash -c "
conda list --explicit
" > conda-explicit.yml

# Generate pip freeze
docker run --rm sip-lims-workflow-manager:latest bash -c "
pip freeze
" > requirements-locked.txt

# Get base image SHA
docker inspect continuumio/miniconda3:latest | grep -A 1 "RepoDigests" | grep sha256 > base-image-sha.txt

echo "Lock files generated. Commit these to git for reproducible builds."
```

## Benefits of This Approach:
✅ **Complete Determinism**: Every package, every build hash, every version locked
✅ **Cross-Platform**: Works on any Docker platform
✅ **Version Control**: Lock files are committed to git
✅ **Rollback Capability**: Can revert to any previous working state
✅ **No Surprises**: Builds are identical regardless of when/where they run

## Implementation Steps:
1. Generate lock files from your working local image
2. Update Dockerfile to use lock files
3. Test build reproducibility
4. Commit lock files to version control
5. Update lock files only when intentionally updating dependencies