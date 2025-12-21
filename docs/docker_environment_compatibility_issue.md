# Docker Environment Compatibility Issue

## Problem Summary
**Date**: December 21, 2025  
**Issue**: SQLite/SQLAlchemy import failure in production mode (Docker container) while working correctly in development mode (local Python environment)

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

## Workaround
For immediate testing, use **development mode** which bypasses the Docker environment compatibility issue.

## Related Files
- [`Dockerfile`](../Dockerfile) - Docker image configuration
- [`environment-docker-final-validated.yml`](../environment-docker-final-validated.yml) - Conda environment specification
- [`process.post.DNA.quantification.py`](~/.sip_lims_workflow_manager/scripts/process.post.DNA.quantification.py) - Failing script (line 89)