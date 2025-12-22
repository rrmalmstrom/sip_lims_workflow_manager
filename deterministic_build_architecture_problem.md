# Deterministic Docker Build Architecture Problem

## Problem Summary

We successfully implemented a deterministic Docker build strategy to fix SQLAlchemy/SQLite compatibility issues, but discovered a fundamental architecture problem during GitHub Actions testing.

## What We Implemented

### ✅ Completed Successfully:
- **Replaced Dockerfile** with deterministic version using pinned base image SHA
- **Updated GitHub Actions workflow** with lock file validation and deterministic labels
- **Updated docker-compose.yml** for deterministic builds
- **Archived old files** (environment-docker-final-validated.yml, environment.yml)
- **Comprehensive documentation updates** across all guides
- **Committed and pushed** all changes to repository

### ❌ Critical Issue Discovered:
**GitHub Actions build failed** due to platform architecture mismatch

## The Core Problem

### Current Situation:
- **Local Development (Mac M1)**: Generates `conda-lock.txt` for `linux-aarch64` (ARM64)
- **GitHub Actions**: Builds for both `linux/amd64` AND `linux/arm64` platforms
- **Build Failure**: ARM64 conda packages cannot be used for AMD64 builds

### The Fundamental Challenge:
This creates a **development vs production inconsistency** - exactly what deterministic builds are supposed to prevent!

```
Your Mac (ARM64) → Generates ARM64 lock files
GitHub Actions    → Tries to build AMD64 + ARM64
Users            → Could be on either AMD64 or ARM64
```

## Error Details

GitHub Actions failed with:
```
Missing lock files required for deterministic builds:
- conda-lock.txt not found (actually: platform mismatch)
- requirements-lock.txt not found (actually: platform mismatch)

/opt/conda/envs/sip-lims-workflow-manager/bin/pip: import: not found
Syntax error: "(" unexpected (expecting "then")
```

**Root Cause**: Conda environment creation fails due to platform mismatch, so pip executable doesn't exist, causing shell to interpret Python code as shell script.

## Architecture Questions for Architect

### 1. Cross-Platform Determinism Paradox
**Question**: How do we achieve true determinism across platforms when:
- Local development is on ARM64 (Mac M1)
- GitHub Actions builds for both AMD64 and ARM64
- Users can be on either platform

**Current Options**:
- **A**: Platform-specific lock files (complex, multiple files to maintain)
- **B**: Revert to pinned environment.yml (simpler, but less deterministic)
- **C**: Different approach entirely

### 2. Development vs Production Consistency
**Question**: If local development builds ARM64 images but GitHub Actions builds AMD64+ARM64, how do we ensure development environment matches what users get?

**Implications**:
- Developer tests ARM64 image locally
- Users might get AMD64 image from GitHub
- Potential for platform-specific bugs

### 3. True Determinism vs Practical Determinism
**Question**: What level of determinism do we actually need?

**Options**:
- **Full Determinism**: Exact same packages, build hashes, everything identical
- **Version Determinism**: Same package versions, but platform-appropriate builds
- **Functional Determinism**: Same functionality, but platform-optimized packages

## Current State

### Files Modified:
- ✅ `Dockerfile`: Uses deterministic approach (but with platform-specific lock files)
- ✅ `.github/workflows/docker-build.yml`: Enhanced with validation
- ✅ `docker-compose.yml`: Updated for deterministic builds
- ✅ Documentation: Comprehensive updates
- ✅ Git: All changes committed and pushed

### Files Available:
- `conda-lock.txt`: ARM64-specific (causes GitHub Actions failure)
- `requirements-lock.txt`: ARM64-specific (causes GitHub Actions failure)
- `archive/environment-docker-final-validated.yml`: Cross-platform with exact versions

## Recommended Architect Decision Points

1. **Architecture Strategy**: Platform-specific vs cross-platform approach?
2. **Determinism Level**: Full vs version vs functional determinism?
3. **Development Workflow**: How to ensure dev/prod consistency?
4. **Build Strategy**: Single Dockerfile vs platform-specific builds?
5. **Lock File Strategy**: Multiple platform files vs single cross-platform file?

## Next Steps Pending Architect Decision

The implementation is 95% complete. We need architectural guidance on the cross-platform determinism strategy before proceeding with the final build fixes.