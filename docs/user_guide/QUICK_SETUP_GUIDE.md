# SIP LIMS Workflow Manager - Quick Setup Guide

This guide will walk you through the one-time setup process for the SIP LIMS Workflow Manager.

## 1. Prerequisites

You must install two pieces of software to use this application.

### Docker Desktop
The application runs in a standardized Docker container to ensure perfect consistency across all computers.
1.  **Download:** Go to the official Docker website and download the installer for your operating system:
    *   [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
    *   [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2.  **Install and Run:** Follow the on-screen instructions to complete the installation. After installation, **start the Docker Desktop application**. You should see a whale icon in your menu bar (macOS) or system tray (Windows).

### Git
Git is used to automatically download and update the scientific workflow scripts.
1.  **Download:** Go to the [official Git website](https://git-scm.com/downloads) and download the installer for your operating system.
2.  **Install:** Run the installer, accepting the default options.

---

## 2. One-Time Application Setup

Once Docker Desktop is installed and running, you need to build the application's local environment. This is a one-time process.

### Download and Extract
-   Download the latest `sip_lims_workflow_manager` .zip file from the latest release on GitHub.
-   Extract it to a permanent location on your computer (e.g., your Desktop or Documents folder).

### Build the Docker Image (One-time only)
This step uses the included source code to build the application's Docker image on your computer. This process happens entirely on your machine.

-   **On macOS:** Double-click `setup_docker.command`.
-   **On Windows:** Double-click `setup_docker.bat`.

A terminal window will open and show the progress. Once it is complete, the application is ready to use.

---

## 3. Launch the Application

After the one-time setup is complete, you can start the application at any time:

-   **On macOS:** Double-click `run.command`.
-   **On Windows:** Double-click `run.bat`.

The application will start inside a Docker container. The first time you run it, it will automatically download the latest scientific workflow scripts. The user interface will then open automatically in your default web browser.