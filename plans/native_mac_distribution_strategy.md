# Native Mac Distribution Strategy - SIP LIMS Workflow Manager

## Executive Summary

This plan implements a native Mac distribution strategy inspired by the December 2025 pre-Docker implementation, enhanced with deterministic environment management using the current lock files. The strategy combines the simplicity of the historical approach with the reproducibility of the current Docker-based lock file system.

## Historical Analysis

### December 2025 Implementation (Pre-Docker)
- **Environment**: [`environment.yml`](historical_environment.yml) with `sip-lims` conda environment
- **Setup**: [`setup.command`](historical_setup.command) - one-time conda environment + repository setup
- **Launch**: [`run.command`](historical_run.command) - simple bash launcher with mode detection
- **Distribution**: ZIP file with double-click setup and launch scripts

### Current Implementation (Post-Docker Removal)
- **Environment**: [`conda-lock.txt`](conda-lock.txt) + [`requirements-lock.txt`](requirements-lock.txt) for deterministic builds
- **Launch**: [`run.py`](run.py) - sophisticated Python launcher with CLI interface
- **Integration**: Git-based update system, workflow type support, comprehensive error handling

## Key Insights

### Environment Management Evolution
1. **Historical**: `environment.yml` with pinned versions but potential for conda solver variations
2. **Current**: Lock files provide exact package URLs and hashes for 100% reproducibility
3. **Optimal**: Hybrid approach using lock files for deterministic setup with environment.yml fallback

### Distribution Strategy Comparison
1. **Historical**: Simple, user-friendly, double-click setup
2. **Current**: Sophisticated but requires technical knowledge
3. **Optimal**: Combine historical simplicity with current robustness

## Proposed Hybrid Strategy

### 1. Deterministic Environment Management

**Primary Method**: Use Mac-specific lock files for 100% reproducibility
```bash
# Create environment from exact Mac lock files
conda create --name sip-lims --file conda-lock-mac.txt
pip install -r requirements-lock-mac-optimized.txt
```

**Key Benefits**:
- **100% Deterministic**: Exact package URLs and build hashes
- **Mac-Optimized**: Generated from working `sip-lims` environment on Mac
- **No Conda Solver**: Zero dependency resolution, exact package installation
- **Validated**: 26/27 tests pass, full functionality confirmed

### 2. Simplified Setup Script

**New [`setup.command`](setup.command)** - Combines historical simplicity with current determinism:

```bash
#!/bin/bash
# SIP LIMS Workflow Manager Setup - Native Mac Distribution
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🧬 Setting up SIP LIMS Workflow Manager for Mac"

# Environment name aligned with current codebase
ENV_NAME="sip-lims"

# Check conda installation
if ! command -v conda &> /dev/null; then
    echo "❌ ERROR: Conda not found"
    echo "📥 Please install Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda found"

# Create deterministic environment
if conda env list | grep -q "^$ENV_NAME\s"; then
    echo "🔄 Environment '$ENV_NAME' exists. Updating..."
    conda env remove --name "$ENV_NAME" --yes
fi

echo "🏗️  Creating deterministic environment from Mac lock files..."
conda create --name "$ENV_NAME" --file conda-lock-mac.txt --yes
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"
pip install -r requirements-lock-mac-optimized.txt

echo "✅ Environment '$ENV_NAME' created successfully"
echo "🚀 Setup complete! Run './run.command' to launch the application"
```

### 3. Simplified Launch Script

**New [`run.command`](run.command)** - Bridges historical simplicity with current functionality:

```bash
#!/bin/bash
# SIP LIMS Workflow Manager Launcher - Native Mac Distribution
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🧬 Starting SIP LIMS Workflow Manager"

# Environment name aligned with current codebase
ENV_NAME="sip-lims"

# Check if environment exists
if ! conda env list | grep -q "^$ENV_NAME\s"; then
    echo "❌ Environment '$ENV_NAME' not found"
    echo "🔧 Please run './setup.command' first"
    exit 1
fi

# Activate environment and delegate to run.py
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

echo "✅ Environment activated: $CONDA_DEFAULT_ENV"
echo "🚀 Launching workflow manager..."

# Delegate to the sophisticated run.py with all its features
python run.py "$@"
```

### 4. Distribution Architecture

```
sip_lims_workflow_manager/
├── setup.command                      # One-time setup (new)
├── run.command                        # Simple launcher (new)
├── run.py                             # Sophisticated launcher (existing)
├── conda-lock-mac.txt                 # Mac-specific conda packages (30 packages)
├── requirements-lock-mac-optimized.txt # Mac-specific pip packages (64 packages)
├── app.py                             # Main Streamlit application
├── src/                               # Application source code
├── templates/                         # Workflow templates
├── docs/                              # Documentation
└── MAC_LOCK_FILES_ANALYSIS.md         # Lock files documentation
```

## User Experience Workflows

### New User Setup (Simple Path)
1. **Download**: Get `sip_lims_workflow_manager.zip` from GitHub releases
2. **Extract**: Unzip to permanent location (Desktop/Documents)
3. **Setup**: Double-click `setup.command` (one-time, 2-3 minutes)
4. **Launch**: Double-click `run.command` (daily use)

### Advanced User Setup (Full Control)
1. **Download**: Clone repository or download ZIP
2. **Setup**: Run `python run.py --help` to see all options
3. **Launch**: Use `python run.py` with specific arguments

### Developer Setup
1. **Clone**: `git clone` repository
2. **Environment**: Use existing `conda-lock.txt` and `requirements-lock.txt`
3. **Launch**: Use `python run.py` with developer options

## Integration with Current Codebase

### Preserve Existing Functionality
- **Keep [`run.py`](run.py)**: All current CLI functionality, update system, error handling
- **Keep Git Integration**: [`src/git_update_manager.py`](src/git_update_manager.py), [`src/scripts_updater.py`](src/scripts_updater.py)
- **Keep Workflow System**: Templates, core logic, all current features

### Add Distribution Layer
- **Add [`setup.command`](setup.command)**: Simple one-time setup for non-technical users
- **Add [`run.command`](run.command)**: Simple launcher that delegates to [`run.py`](run.py)
- **Add [`environment.yml`](environment.yml)**: Generated from lock files for compatibility

### Environment Strategy
- **Primary**: Use existing `conda-lock.txt` + `requirements-lock.txt` for deterministic builds
- **Fallback**: Generate `environment.yml` from lock files for broader compatibility
- **Environment**: Use `sip-lims` environment name (consistent with current codebase)

## Implementation Plan

### Phase 1: Environment Strategy (Coding Agent)
1. **Generate Modern environment.yml**: Extract packages from lock files
2. **Create setup.command**: Deterministic environment creation script
3. **Test Environment Creation**: Validate both lock file and environment.yml methods
4. **Update Documentation**: Environment setup instructions

### Phase 2: Distribution Scripts (Coding Agent)
1. **Create run.command**: Simple launcher that delegates to run.py
2. **Update run.py**: Ensure compatibility with simple launcher
3. **Test Integration**: Verify setup.command → run.command → run.py workflow
4. **Create Distribution Package**: ZIP file structure for releases

### Phase 3: Documentation and Testing (Debugging Agent)
1. **User Testing**: Test complete setup workflow with non-technical users
2. **Documentation**: Create user-friendly setup guides
3. **Release Preparation**: GitHub releases with ZIP packages
4. **Validation**: Ensure all current functionality preserved

## Benefits of This Approach

### For Users
- **Simple Setup**: Double-click scripts for setup and launch
- **Deterministic**: Exact same environment every time
- **Familiar**: Similar to December 2025 approach users may remember
- **Robust**: All current features and error handling preserved

### For Developers
- **Flexible**: Can use simple scripts or advanced run.py options
- **Maintainable**: Builds on existing codebase without major changes
- **Testable**: Clear separation between distribution layer and core functionality
- **Upgradeable**: Easy to enhance either layer independently

### For Distribution
- **User-Friendly**: Non-technical users can set up easily
- **Professional**: Technical users have full control
- **Reliable**: Deterministic environments prevent "works on my machine" issues
- **Scalable**: Can distribute via GitHub releases, email, or other channels

## Migration from Current State

### Immediate Changes Needed
1. **Add setup.command**: New file for environment setup
2. **Add run.command**: New file for simple launching
3. **Generate environment.yml**: Extract from current lock files
4. **Update Documentation**: Add simple setup instructions

### No Breaking Changes
- **Keep run.py**: All existing functionality preserved
- **Keep Lock Files**: Continue using for deterministic builds
- **Keep Git Integration**: All update mechanisms preserved
- **Keep Workflow System**: All templates and core logic unchanged

### Gradual Enhancement
1. **Phase 1**: Add distribution scripts alongside existing system
2. **Phase 2**: Test with users and gather feedback
3. **Phase 3**: Refine based on real-world usage
4. **Phase 4**: Consider additional enhancements (auto-updates, etc.)

## Success Criteria

### Technical
- [ ] Deterministic environment creation from lock files
- [ ] Simple setup.command creates working environment
- [ ] Simple run.command launches application correctly
- [ ] All existing run.py functionality preserved
- [ ] Git-based updates continue working

### User Experience
- [ ] Non-technical users can set up in under 5 minutes
- [ ] Setup process requires minimal technical knowledge
- [ ] Launch process is single-click simple
- [ ] Error messages are clear and actionable
- [ ] Documentation is user-friendly

### Distribution
- [ ] ZIP package contains all necessary files
- [ ] GitHub releases provide easy download
- [ ] Setup works on clean Mac systems
- [ ] No external dependencies beyond Miniconda
- [ ] Consistent behavior across different Mac configurations

This strategy provides a clear path forward that honors the simplicity of the historical approach while leveraging the robustness and determinism of the current implementation.