# Environment Configurations

This directory contains all environment-related files organized by platform and purpose.

## Directory Structure

### 📱 `mac/` - Native Mac Distribution
**Used by:** [`setup.command`](../setup.command) for Native Mac Distribution

- **`conda-lock-mac.txt`** - Mac-specific conda packages (30 packages, osx-arm64)
- **`requirements-lock-mac-optimized.txt`** - Optimized pip packages (64 packages)
- **`requirements-lock-mac.txt`** - Full pip packages (67 packages, includes legacy)
- **`MAC_LOCK_FILES_ANALYSIS.md`** - Technical analysis and validation documentation

### 🐳 `docker/` - Docker Distribution  
**Used by:** Docker build system and [`run.py`](../run.py) for cross-platform distribution

- **`conda-lock.txt`** - Linux-specific conda packages for Docker containers
- **`requirements-lock.txt`** - Linux-specific pip packages for Docker containers

### 📚 `historical/` - Historical Reference
**Used by:** Reference and comparison purposes

- **`historical_environment.yml`** - Original December 2025 environment specification
- **`historical_setup.command`** - Original setup script (pre-deterministic)
- **`historical_run.command`** - Original run script (pre-deterministic)

## Usage

### For Native Mac Distribution
The [`setup.command`](../setup.command) script automatically uses:
```bash
conda create --name sip-lims --file environments/mac/conda-lock-mac.txt
pip install -r environments/mac/requirements-lock-mac-optimized.txt
```

### For Docker Distribution
The Docker build system uses:
```bash
conda create --name sip-lims --file environments/docker/conda-lock.txt
pip install -r environments/docker/requirements-lock.txt
```

## Key Benefits

- **🎯 Platform-Specific**: Each platform gets optimized packages
- **🔒 Deterministic**: Exact package versions and build hashes
- **📁 Organized**: Clear separation by platform and purpose
- **📖 Documented**: Complete analysis and validation documentation
- **🔄 Maintainable**: Easy to update and manage different environments

## Lock File Generation

- **Mac Lock Files**: Generated from working `sip-lims` environment on Mac
- **Docker Lock Files**: Generated from Docker containers for Linux compatibility
- **Historical Files**: Preserved from December 2025 implementation for reference

See [`MAC_LOCK_FILES_ANALYSIS.md`](mac/MAC_LOCK_FILES_ANALYSIS.md) for detailed technical analysis.