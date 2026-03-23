# SIP LIMS Workflow Manager

A comprehensive laboratory workflow management system for Stable Isotope Probing (SIP) and Single Particle Sorts & Cell Enrichments (SPS-CE) workflows.

## 🚀 Quick Start

### 🍎 Mac Users (Recommended)
**Simple, one-click setup - no Docker required!**

1. **One-time setup**: Double-click `setup.command`
2. **Daily use**: Double-click `run.command`

### 🐳 All Platforms (Docker)
**Cross-platform setup using Docker containers**

```bash
./run.command
```

## 📋 Prerequisites

### For Mac Native Distribution
- **macOS** (Intel or Apple Silicon)
- **Miniconda**: [Download here](https://docs.conda.io/en/latest/miniconda.html)

### For Docker Distribution
- **Docker Desktop**: [Download here](https://www.docker.com/products/docker-desktop/)
- **Git**: [Download here](https://git-scm.com/downloads)
- **Python 3.10+**: [Download here](https://www.python.org/downloads/)

## 🧪 Supported Workflows

- **SIP (Stable Isotope Probing)**: 21-step comprehensive fractionation workflow
- **SPS-CE (Single Particle Sorts & Cell Enrichments)**: 6-step focused library creation workflow
- **Capsule Sorting**: 6-step capsule sorting and preparation workflow for downstream analysis

## 📖 Documentation

- **[Complete Setup Guide](docs/user_guide/QUICK_SETUP_GUIDE.md)**: Detailed installation instructions
- **[Features Guide](docs/user_guide/FEATURES.md)**: Application features and capabilities
- **[Workflow Types](docs/user_guide/WORKFLOW_TYPES.md)**: Detailed workflow documentation
- **[Troubleshooting](docs/user_guide/TROUBLESHOOTING.md)**: Common issues and solutions

## 🔧 Advanced Usage

```bash
./run.command --help          # Show all options
./run.command --updates       # Perform system updates
./run.command --version       # Check version
```

## 🆕 What's New

**Native Mac Distribution**: Simple double-click setup and launch for Mac users using deterministic conda environments. No Docker knowledge required!

**Multi-Workflow Support**: Choose between SIP and SPS-CE workflows with workflow-specific templates and step configurations.

## 🏗️ Architecture

- **Native Mac**: Uses deterministic conda environments with exact package versions
- **Docker**: Cross-platform containerized execution with reproducible builds
- **Git Integration**: Automatic updates for both application and workflow scripts
- **Streamlit Interface**: Modern web-based user interface

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For issues and questions:
1. Check the [Troubleshooting Guide](docs/user_guide/TROUBLESHOOTING.md)
2. Review the [Complete Documentation](docs/index.md)
3. Submit an issue on GitHub