# Docker Documentation

## 📋 Quick Start

**New to the system?** Start here:
- **[Branch-Aware Docker Workflow](BRANCH_AWARE_DOCKER_WORKFLOW.md)** - Complete guide to the new branch-aware system

## 📚 Documentation Index

### Current Documentation (Updated)
- **[Branch-Aware Docker Workflow](BRANCH_AWARE_DOCKER_WORKFLOW.md)** - Complete workflow guide for the new branch-aware system
- **[Docker Compose Configuration](DOCKER_COMPOSE_CONFIGURATION.md)** - Docker Compose setup and configuration

### Legacy Documentation (Outdated)
⚠️ **Note**: The following documents contain outdated information and reference the old `:latest` tag system:

- **[Docker Development Workflow Guide](DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md)** - ⚠️ **OUTDATED** - Still references `:latest` tags
- **[Docker Environment Compatibility Issue](docker_environment_compatibility_issue.md)** - ⚠️ **OUTDATED** - May contain outdated troubleshooting info

## 🔄 Migration Status

The SIP LIMS Workflow Manager has been upgraded to a **branch-aware Docker system**:

### ✅ What's New
- **Automatic Branch Detection**: Scripts auto-detect your current Git branch
- **Branch-Specific Images**: Each branch gets its own Docker images
- **Isolated Development**: Work on development branches without affecting main
- **Smart Update Detection**: Compares branch-specific images with branch-specific Git commits

### 📦 Image Naming
- **Old System**: `sip-lims-workflow-manager:latest` (all branches)
- **New System**: `sip-lims-workflow-manager:<branch-tag>` (branch-specific)

### 🔧 Scripts Enhanced
All scripts are now branch-aware:
- `build/build_image_from_lock_files.sh` - Builds branch-specific images
- `build/push_image_to_github.sh` - Pushes to branch-specific registry locations
- Platform-specific run scripts - Use branch-specific images and update detection:
  - **macOS**: `run.mac.command`
  - **Windows**: `run.windows.bat`

## 🚀 Getting Started

1. **Read the new workflow guide**: [Branch-Aware Docker Workflow](BRANCH_AWARE_DOCKER_WORKFLOW.md)
2. **Switch to your desired branch**: `git checkout your-branch`
3. **Build branch-specific image**: `./build/build_image_from_lock_files.sh`
4. **Test locally**:
   - **macOS**: `./run.mac.command` (choose development mode)
   - **Windows**: `./run.windows.bat` (choose development mode)
5. **Push when ready**: `./build/push_image_to_github.sh`

## 🔍 Key Concepts

### Branch-to-Tag Mapping
```
main → main
analysis/esp-docker-adaptation → analysis-esp-docker-adaptation
feature/new-analysis → feature-new-analysis
```

### Docker Image Tagging
When you push, you'll see two local images:
1. `sip-lims-workflow-manager:analysis-esp-docker-adaptation` (original)
2. `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:analysis-esp-docker-adaptation` (tagged copy)

This is **normal Docker behavior** - both have the same Image ID.

## 📖 Related Documentation

- **[Developer Architecture Guide](../developer_guide/BRANCH_AWARE_ARCHITECTURE.md)** - Technical implementation details
- **[User Guide](../user_guide/)** - End-user documentation
- **[Troubleshooting](../user_guide/TROUBLESHOOTING.md)** - Common issues and solutions

## 🏗️ Documentation Cleanup Needed

The following legacy documents should be updated or archived:
- [ ] Update `DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md` to reflect branch-aware system
- [ ] Review `docker_environment_compatibility_issue.md` for current relevance
- [ ] Consider consolidating or archiving outdated content