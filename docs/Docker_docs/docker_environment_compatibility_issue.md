# Docker Environment Compatibility Issue - RESOLVED

## Problem Summary
**Date**: December 21, 2025
**Issue**: SQLite/SQLAlchemy import failure in production mode (Docker container) while working correctly in development mode (local Python environment)
**Status**: ✅ **RESOLVED** - Fixed with deterministic Docker build strategy

## Error Details
```
ImportError: /lib/aarch64-linux-gnu/libstdc++.so.6: version `CXXABI_1.3.15' not found (required by /opt/conda/envs/sip-lims-workflow-manager/lib/python3.9/lib-dynload/../.././libicui18n.so.78)
```

**Error Location**: Step 7 - `process.post.DNA.quantification.py` line 89 in `readSQLdb()` function  
**Failing Component**: SQLAlchemy `create_engine()` call attempting to import SQLite

## Root Cause Analysis
This is a **C++ standard library version mismatch** between:
- **Conda environment libraries** inside the Docker container
- **Host system libraries** that the conda environment depends on

The error `CXXABI_1.3.15' not found` indicates that the conda-installed packages require a newer version of the C++ standard library than what's available in the Docker container's base system.

## Script Version Verification
**✅ Scripts are NOT the problem** - All versions are identical:
- Development scripts: `/Users/RRMalmstrom/Desktop/sip_scripts_dev` → Commit `830ac79`
- Production scripts: `~/.sip_lims_workflow_manager/scripts` → Commit `830ac79`
- Remote repository: `origin/main` → Commit `830ac79`
- File diff: No differences found

## Environment Comparison
| Mode | Environment | Result |
|------|-------------|---------|
| **Development Mode** | Local Python environment | ✅ Works correctly |
| **Production Mode** | Docker container conda environment | ❌ Fails with CXXABI error |

## Technical Details
- **Docker Image**: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest`
- **Conda Environment**: `sip-lims-workflow-manager` (Python 3.9)
- **Affected Libraries**: SQLite3, SQLAlchemy, ICU (International Components for Unicode)
- **Architecture**: aarch64 (ARM64)

## Impact
- **Development workflow**: Unaffected - continues to work normally
- **Production workflow**: Affected - fails at database operations in step 7
- **Update system testing**: Not affected - Docker container starts and runs basic operations

## Potential Solutions
1. **Update Docker base image** to include newer C++ standard library
2. **Rebuild conda environment** with compatible library versions
3. **Pin specific library versions** that are compatible with the base system
4. **Use different base image** with better library compatibility
5. **Investigate conda-forge vs defaults channels** for package sources

## Investigation Needed
1. Check Docker base image C++ library versions
2. Examine conda environment package sources and versions
3. Test with different base images or library combinations
4. Verify if this affects other workflow steps beyond step 7

## Solution Implemented ✅

**Deterministic Docker Build Strategy** - Implemented December 21, 2025

### What Was Changed:
1. **Pinned Base Image**: `continuumio/miniconda3:latest` → `continuumio/miniconda3@sha256:4a2425c3ca891633e5a27280120f3fb6d5960a0f509b7594632cdd5bb8cbaea8`
2. **Exact Package Lock Files**: Replaced `environment-docker-final-validated.yml` with:
   - [`conda-lock.txt`](../conda-lock.txt) - Exact conda package versions
   - [`requirements-lock.txt`](../requirements-lock.txt) - Exact pip package versions
3. **Pinned System Dependencies**: All system packages now use exact versions
4. **Enhanced CI/CD**: Added validation for lock files in GitHub Actions

### Why This Fixes The Issue:
- **Eliminates Version Drift**: Exact package versions prevent library mismatches
- **Consistent C++ Libraries**: Pinned base image ensures compatible system libraries
- **Reproducible Builds**: Same exact environment every time, eliminating compatibility surprises

### Files Modified:
- [`Dockerfile`](../Dockerfile) - Now uses deterministic build process
- [`.github/workflows/docker-build.yml`](../.github/workflows/docker-build.yml) - Added lock file validation
- [`README.md`](../README.md) - Documents new deterministic approach

### Files Archived:
- `archive/environment-docker-final-validated.yml` - Replaced by lock files
- `archive/environment.yml` - No longer needed
- `archive/Dockerfile.deterministic` - Content moved to main Dockerfile

## Verification
The deterministic build has been tested and resolves the SQLAlchemy/SQLite compatibility issue while maintaining all functionality.

## Related Files
- [`Dockerfile`](../Dockerfile) - Deterministic Docker image configuration
- [`conda-lock.txt`](../conda-lock.txt) - Exact conda package versions
- [`requirements-lock.txt`](../requirements-lock.txt) - Exact pip package versions
- [`generate_lock_files.sh`](../generate_lock_files.sh) - Script to update lock files
- [`validate_lock_files.sh`](../validate_lock_files.sh) - Script to validate lock files