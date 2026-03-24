# Developer Guide

This directory contains technical documentation for developers working on the sip_lims_workflow_manager project.

## Current Documentation Structure

### Core Architecture
- **[`ARCHITECTURE.md`](ARCHITECTURE.md)** - Complete system architecture documentation
  - Mac-native implementation details
  - Core components and data flow
  - Workflow management system
  - Git-based update mechanism

- **[`DISTRIBUTION_PACKAGE_SUMMARY.md`](DISTRIBUTION_PACKAGE_SUMMARY.md)** - Distribution package documentation
  - Native Mac distribution approach
  - Package structure and validation
  - Setup and deployment procedures

### Feature Documentation
- **[`features/`](features/)** - Specific feature implementations
  - Fragment Analyzer results archiving
  - Cyclical workflow analysis
  - Script analysis and documentation

## Documentation Reorganization (March 24, 2026)

This developer guide has been significantly reorganized to focus on current, relevant documentation:

### What Was Kept
- **2 Core Documents**: Current Mac-native architecture and distribution
- **3 Feature Documents**: Active functionality documentation
- **Total**: 5 focused, current documents

### What Was Archived
- **4 Docker-related documents** → [`../archive/docker_legacy/`](../archive/docker_legacy/)
- **8 Implementation plans** → [`../archive/implementation_plans/`](../archive/implementation_plans/)
- **Total**: 12 obsolete/historical documents archived

## System Overview

The sip_lims_workflow_manager is now a **100% Mac-native application** with:

- **Native Python Execution** - No container runtime required
- **83% Performance Improvement** - 30s → 5s startup time
- **Sophisticated Workflow Engine** - Atomic state management with undo/redo
- **Git-Based Updates** - Automatic repository and script management
- **Three Workflow Types** - SIP, SPS-CE, and Capsule Sorting

## Getting Started

1. **Read the Architecture**: Start with [`ARCHITECTURE.md`](ARCHITECTURE.md) for system overview
2. **Understand Distribution**: Review [`DISTRIBUTION_PACKAGE_SUMMARY.md`](DISTRIBUTION_PACKAGE_SUMMARY.md) for deployment
3. **Explore Features**: Browse [`features/`](features/) for specific functionality details

## Related Documentation

- **User Guide**: [`../user_guide/`](../user_guide/) - End-user documentation
- **Archive**: [`../archive/`](../archive/) - Historical documentation
- **Plans**: [`../../plans/`](../../plans/) - Implementation plans and strategies

## Development Environment

For setting up a development environment:
- **Setup Script**: [`../../setup.command`](../../setup.command) - Environment initialization
- **Run Script**: [`../../run.command`](../../run.command) - Application launcher
- **Source Code**: [`../../src/`](../../src/) - Core implementation

## Contributing

When adding new documentation:
1. **Core Architecture Changes** → Update [`ARCHITECTURE.md`](ARCHITECTURE.md)
2. **New Features** → Add to [`features/`](features/) directory
3. **Historical Plans** → Archive in [`../archive/implementation_plans/`](../archive/implementation_plans/)
4. **Docker-related** → Archive in [`../archive/docker_legacy/`](../archive/docker_legacy/)