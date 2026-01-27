# SIP LIMS Workflow Manager Documentation

Welcome to the central documentation for the SIP LIMS Workflow Manager. This guide provides a comprehensive overview of the application, from user setup to advanced development topics.

## 🚀 What's New

**Multi-Workflow Support**: The SIP LIMS Workflow Manager now supports multiple laboratory workflow types:

- **SIP (Stable Isotope Probing)**: 21-step comprehensive fractionation workflow
- **SPS-CE (Single Particle Sorts & Cell Enrichments)**: 6-step focused library creation workflow

### Quick Start

**🍎 Native Mac Distribution:**
1. Double-click `setup.command` (one-time setup)
2. Double-click `run.command` (daily use)
3. Select your workflow type when prompted
4. Start managing your laboratory workflow!

**Advanced Usage:**
- Use `./run.command --help` to see all available options
- Use `./run.command --version` to check the current version
- Use `./run.command --updates` to perform system updates

### Backward Compatibility

Existing SIP workflows continue to work exactly as before with zero changes required.

## 📖 User Guide

For users of the application, this section provides everything you need to get started and use the workflow manager effectively.

-   **[Quick Setup Guide](user_guide/QUICK_SETUP_GUIDE.md)**: A step-by-step guide to installing and configuring the application for the first time.
-   **[Workflow Types Guide](user_guide/WORKFLOW_TYPES.md)**: Comprehensive guide to supported workflow types (SIP and SPS-CE).
-   **[Features Guide](user_guide/FEATURES.md)**: A detailed explanation of the application's features, including conditional workflows, "skip to step," and the granular undo system.
-   **[Troubleshooting Guide](user_guide/TROUBLESHOOTING.md)**: A guide to help you resolve common issues.

## 👨‍💻 Developer Guide

This section is for developers who are contributing to the project. It contains detailed technical information about the application's architecture and implementation.

-   **[System Architecture](developer_guide/ARCHITECTURE.md)**: A high-level overview of the application's architecture, design principles, and technology stack.
-   **[Update System](developer_guide/ARCHITECTURE.md#decoupled-repository-architecture)**: An explanation of the Git-based system for managing both application and script updates.
-   **[FA Results Archiving](developer_guide/fa_results_archiving.md)**: Technical documentation for the Fragment Analyzer results archiving system that preserves experimental data during workflow operations.
-   **[Distribution Package Summary](developer_guide/DISTRIBUTION_PACKAGE_SUMMARY.md)**: Technical overview of the native Mac distribution package and components.

## 🗄️ Archive

Outdated and historical documents are kept in the [archive](archive/) for reference. This includes documentation from the transition period when the application was converted from a Docker-based to native Mac execution.

### Legacy Documentation

The [docker_legacy](archive/docker_legacy/) directory contains historical Docker-based implementation documentation that was replaced with native Mac execution in January 2026. This documentation is preserved for historical reference and understanding the system's evolution.