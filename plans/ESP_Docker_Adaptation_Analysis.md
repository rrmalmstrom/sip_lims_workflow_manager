# ESP Docker Adaptation Analysis

## Executive Summary

This document provides a comprehensive analysis for adapting the Docker strategy from the `main_docker_legacy` branch to the `feature/ESP-condense-plates-workflow` branch (v3.0.0). The analysis focuses on external Python script dependencies, workflow code changes, and Docker configuration requirements.

## Key Findings

### 1. External Script Dependencies Analysis

**Scripts Location**: `/Users/RRMalmstrom/Desktop/sip_scripts_dev`
**Total Scripts**: 25+ Python scripts

**Critical Dependencies Identified**:
- **pandas**: Data manipulation (✅ present in both environments)
- **numpy**: Numerical operations (✅ present in both environments)
- **matplotlib**: Plotting and visualization (✅ present in both environments)
- **seaborn**: Statistical visualization (✅ present in both environments)
- **sqlalchemy**: Database operations (✅ present in both environments)
- **PyPDF2**: PDF processing (✅ present in both environments)
- **openpyxl**: Excel file handling (✅ present in both environments)
- **xlrd, xlutils, xlwt**: Legacy Excel support (✅ present in both environments)

### 2. Environment Compatibility Analysis

**Status**: ✅ **FULLY COMPATIBLE**

**Environment.yml Comparison**:

| Component | Legacy Branch | ESP Branch | Status |
|-----------|---------------|------------|---------|
| Base Dependencies | 32 conda packages | 33 conda packages | ✅ Compatible |
| Python Packages | 65 pip packages | 66 pip packages | ✅ Compatible |
| **Key Difference** | Missing `appscript` | `appscript==1.3.0` | ✅ ESP superset |
| External Script Deps | All present | All present | ✅ Complete |

**ESP Branch Additions**:
- `appscript==1.3.0`: macOS automation library
- `libcxx==21.1.2`: Additional C++ library
- `libintl==0.25.1`: Internationalization library

**Impact**: The ESP environment is a **superset** of the legacy environment with all required dependencies.

### 3. Developer vs User Mode Implementation

**Detection Mechanism**:
- **File-based**: Presence of `config/developer.marker` (empty file)
- **Environment variable**: `APP_ENV` (defaults to 'production')

**Mode-Specific Behaviors**:

| Feature | Production Mode (Lab Users) | Development Mode (Developer) |
|---------|----------------------------|------------------------------|
| Update Checks | ✅ Enabled (app.py:1100-1133) | ❌ Disabled (app.py:1135) |
| Script Updates | 🔄 Automatic | 🔄 Manual |
| Script Path | `/workflow-scripts` | `/workflow-scripts` |
| Debug Info | Standard | Enhanced |

### 4. Workflow Architecture Compatibility

**ESP Workflow Structure** (20 steps):
1. Setup Plates & DB
2. Create Ultracentrifuge Tubes
3. Plot DNA/Density (QC)
4. Create DB and Add Sequins
5. Select Fractions for Cleanup
6. Generate CsCl Cleanup Files
7. Process Post-DNA Quantification
8. **Create Library Files (Condensed Plates)** ⭐
9. Analyze Library QC (1st)
10. Second Attempt Library Creation
11. Analyze Library QC (2nd)
12. Decision: Third Library Creation Attempt
13. Third Attempt Library Creation
14. Analyze Library QC (3rd)
15. Conclude FA analysis
16. Make Clarity Summary
17. Generate Pool Assignment Tool
18. Prepare Pools
19. Analyze Pool QC Results
20. Rework Pools & Finalize
21. Transfer Pools to Final Tubes

**Script Execution Mechanism**:
- **Path Resolution**: `/workflow-scripts` (unchanged from legacy)
- **Error Handling**: Comprehensive error messages (src/logic.py:594-602)
- **Volume Mount Strategy**: Two-volume architecture fully compatible

### 5. Docker Strategy Assessment

**Current Docker Implementation** (main_docker_legacy):
- **Base Image**: `continuumio/miniconda3:latest`
- **Two-Volume Architecture**:
  - Volume 1: User project data (varies per user)
  - Volume 2: External workflow scripts at `/workflow-scripts`
- **Environment Setup**: Complete Conda environment via environment.yml
- **Entry Point**: Script for environment activation

**ESP Branch Compatibility**: ✅ **FULLY COMPATIBLE**

The ESP branch workflow manager is designed to work with the exact same Docker architecture.

## Comprehensive Module Dependency Matrix

### External Scripts Dependencies vs Docker Environment

| Module | External Scripts Usage | Legacy Environment | ESP Environment | Docker Status |
|--------|----------------------|-------------------|-----------------|---------------|
| pandas | ✅ Heavy usage | ✅ v2.3.2 | ✅ v2.3.2 | ✅ Available |
| numpy | ✅ Heavy usage | ✅ v2.0.2 | ✅ v2.0.2 | ✅ Available |
| matplotlib | ✅ Plotting | ✅ v3.9.4 | ✅ v3.9.4 | ✅ Available |
| seaborn | ✅ Visualization | ✅ v0.13.2 | ✅ v0.13.2 | ✅ Available |
| sqlalchemy | ✅ Database ops | ✅ v2.0.43 | ✅ v2.0.43 | ✅ Available |
| PyPDF2 | ✅ PDF processing | ✅ v3.0.1 | ✅ v3.0.1 | ✅ Available |
| openpyxl | ✅ Excel files | ✅ v3.1.5 | ✅ v3.1.5 | ✅ Available |
| xlrd | ✅ Excel reading | ✅ v2.0.2 | ✅ v2.0.2 | ✅ Available |
| xlutils | ✅ Excel utilities | ✅ v2.0.0 | ✅ v2.0.0 | ✅ Available |
| xlwt | ✅ Excel writing | ✅ v1.3.0 | ✅ v1.3.0 | ✅ Available |
| xlwings | ✅ Excel automation | ✅ v0.33.15 | ✅ v0.33.15 | ✅ Available |
| requests | ✅ HTTP requests | ✅ v2.32.5 | ✅ v2.32.5 | ✅ Available |
| lxml | ✅ XML processing | ✅ v6.0.2 | ✅ v6.0.2 | ✅ Available |
| appscript | ❌ Not used | ❌ Missing | ✅ v1.3.0 | ✅ ESP Addition |

**Result**: 🎯 **100% Coverage** - All external script dependencies are satisfied in both environments.

## Implementation Plan

### Phase 1: Docker Infrastructure Adaptation (Low Risk)
**Estimated Time**: 2-4 hours

1. **Copy Docker Files** from `main_docker_legacy` to `feature/ESP-condense-plates-workflow`:
   - `Dockerfile`
   - `entrypoint.sh`
   - `setup_docker.bat` / `setup_docker.command`
   - `.dockerignore`

2. **Environment Integration**:
   - ESP `environment.yml` already contains all required dependencies
   - No changes needed - ESP environment is superset of legacy

3. **Developer Mode Configuration**:
   - Ensure `config/developer.marker` handling in Docker setup
   - Configure `APP_ENV` environment variable for production containers

### Phase 2: Configuration Updates (Medium Risk)
**Estimated Time**: 1-2 hours

1. **Production Container Setup**:
   ```dockerfile
   ENV APP_ENV=production
   ```

2. **Volume Mount Strategy**:
   ```bash
   # Volume 1: User project data
   -v /path/to/user/project:/app/project
   
   # Volume 2: External scripts (consistent across all users)
   -v ~/.sip_lims_workflow_manager/scripts:/workflow-scripts:ro
   ```

3. **Script Path Validation**:
   - Test script resolution at `/workflow-scripts`
   - Verify error handling for missing scripts

### Phase 3: Testing and Validation (Low Risk)
**Estimated Time**: 2-3 hours

1. **Build and Test**:
   ```bash
   docker build -t sip-lims-esp:latest .
   docker run -it --rm sip-lims-esp:latest
   ```

2. **Validation Checklist**:
   - ✅ Container startup and environment activation
   - ✅ External script path resolution
   - ✅ Developer vs production mode behavior
   - ✅ Volume mount functionality
   - ✅ Conda environment completeness

### Phase 4: Deployment Preparation (Low Risk)
**Estimated Time**: 1 hour

1. **Documentation Updates**:
   - Update setup scripts for ESP workflow
   - Document volume mount requirements
   - Create deployment guide

2. **Fallback Mechanisms**:
   - Script path resolution fallbacks
   - Error handling improvements

## Risk Assessment

### Low Risk Items ✅
- **Environment Compatibility**: All dependencies present, ESP is superset
- **Script Execution Mechanism**: Unchanged `/workflow-scripts` path
- **Two-Volume Architecture**: Fully compatible with ESP workflow
- **Workflow Structure**: 20 steps vs 19, same execution pattern

### Medium Risk Items ⚠️
- **Developer Mode Detection**: File-based detection in containerized environment
- **Volume Mount Configuration**: Different deployment scenarios
- **New ESP-Specific Scripts**: 20-step workflow vs 19-step legacy

### Mitigation Strategies
1. **Comprehensive Testing**: Both production and development modes
2. **Clear Documentation**: Volume mount requirements and setup
3. **Fallback Mechanisms**: Script path resolution alternatives
4. **Gradual Rollout**: Test with single user before full deployment

## Workflow Code Changes Analysis

### Key Differences Between Branches

**Developer vs User Mode Implementation**:
- **Detection**: File-based (`config/developer.marker`) + environment variable (`APP_ENV`)
- **Production Mode**: Full update checks, automatic script updates
- **Development Mode**: Update checks disabled, enhanced debugging
- **Docker Compatibility**: Both modes work with same container architecture

**Script Execution Changes**:
- **Path Resolution**: Consistent `/workflow-scripts` mount point
- **Error Handling**: Enhanced error messages for missing scripts
- **Volume Strategy**: Two-volume architecture maintained

**Workflow Structure Changes**:
- **Step Count**: 20 steps (ESP) vs 19 steps (legacy)
- **Focus**: "Condensed plates" methodology
- **New Steps**: Enhanced library creation and QC analysis
- **Execution**: Same script runner mechanism

## Conclusion

The Docker strategy from `main_docker_legacy` can be **successfully adapted** to `feature/ESP-condense-plates-workflow` with **minimal changes**. The ESP branch is specifically designed to work with the existing Docker architecture and includes all necessary dependencies for external script execution.

### Key Success Factors:
1. **100% Dependency Coverage**: All external script modules available
2. **Architecture Compatibility**: ESP designed for `/workflow-scripts` mount
3. **Environment Superset**: ESP environment includes all legacy dependencies plus additions
4. **Developer/User Mode Support**: Built-in production vs development distinction

### Recommended Next Steps:
1. ✅ **Proceed with Phase 1**: Copy Docker infrastructure files
2. ✅ **Test Environment**: Build and validate Docker image
3. ✅ **Deploy Gradually**: Start with development environment testing
4. ✅ **Document Process**: Create deployment and troubleshooting guides

**Overall Assessment**: 🎯 **LOW RISK, HIGH SUCCESS PROBABILITY**

The adaptation is straightforward due to the ESP branch's intentional compatibility with the Docker strategy and comprehensive dependency coverage.

## Technical Implementation Details

### Docker File Adaptation Strategy

1. **Base Image**: Keep `continuumio/miniconda3:latest`
2. **Environment File**: Use ESP `environment.yml` (superset of legacy)
3. **Entry Point**: Adapt `entrypoint.sh` for ESP-specific needs
4. **Volume Mounts**: Maintain two-volume architecture

### Environment Variable Configuration

```dockerfile
# Production mode for lab users
ENV APP_ENV=production

# Development mode for developer computer
# ENV APP_ENV=development
```

### Volume Mount Configuration

```yaml
# docker-compose.yml example
services:
  sip-lims-esp:
    image: sip-lims-esp:latest
    volumes:
      - ./user-project:/app/project
      - ~/.sip_lims_workflow_manager/scripts:/workflow-scripts:ro
    environment:
      - APP_ENV=production
```

This comprehensive analysis demonstrates that the Docker adaptation is not only feasible but also low-risk due to the ESP branch's intentional compatibility with the existing Docker strategy.