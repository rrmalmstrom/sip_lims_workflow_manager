# SIP LIMS Workflow Manager Documentation

Welcome to the central documentation for the SIP LIMS Workflow Manager. This guide provides a comprehensive overview of the application, from user setup to advanced development topics.

## 🚀 What's New

**Branch-Aware Docker System**: The workflow manager now automatically manages separate Docker images for different Git branches, enabling isolated development and safer experimentation.

## 📖 User Guide

For users of the application, this section provides everything you need to get started and use the workflow manager effectively.

-   **[Quick Setup Guide](user_guide/QUICK_SETUP_GUIDE.md)**: A step-by-step guide to installing and configuring the application for the first time.
-   **[Features Guide](user_guide/FEATURES.md)**: A detailed explanation of the application's features, including conditional workflows, "skip to step," and the granular undo system.
-   **[Troubleshooting Guide](user_guide/TROUBLESHOOTING.md)**: A guide to help you resolve common issues.

## 👨‍💻 Developer Guide

This section is for developers who are contributing to the project. It contains detailed technical information about the application's architecture and implementation.

-   **[System Architecture](developer_guide/ARCHITECTURE.md)**: A high-level overview of the application's architecture, design principles, and technology stack.
-   **[Branch-Aware Docker Architecture](developer_guide/BRANCH_AWARE_ARCHITECTURE.md)**: 🆕 Technical implementation details of the new branch-aware Docker system.
-   **[Update System](developer_guide/ARCHITECTURE.md#decoupled-repository-architecture)**: An explanation of the Git-based system for managing both application and script updates.
-   **[FA Results Archiving](developer_guide/fa_results_archiving.md)**: Technical documentation for the Fragment Analyzer results archiving system that preserves experimental data during workflow operations.

## 🐳 Docker Documentation

Complete guides for Docker-based development and deployment workflows.

-   **[Branch-Aware Docker Workflow](Docker_docs/BRANCH_AWARE_DOCKER_WORKFLOW.md)**: 🆕 Complete guide to the new branch-aware Docker system - **Start here for Docker workflows**.
-   **[Docker Documentation Index](Docker_docs/README.md)**: Overview of all Docker documentation with migration status.
-   **[Docker Compose Configuration](Docker_docs/DOCKER_COMPOSE_CONFIGURATION.md)**: Technical documentation for the Docker Compose setup, including volume mounting, environment variables, and resource configuration.

### Legacy Docker Documentation
⚠️ **Note**: Some Docker documentation contains outdated information:
-   **[Docker Development Workflow](Docker_docs/DOCKER_DEVELOPMENT_WORKFLOW_GUIDE.md)**: ⚠️ **OUTDATED** - Still references old `:latest` tag system. Use the new Branch-Aware Docker Workflow instead.

## 🗄️ Archive

Outdated and historical documents are kept in the [archive](archive/) for reference. This includes documentation from the transition period when the application was converted from a Conda-based to Docker-based workflow.