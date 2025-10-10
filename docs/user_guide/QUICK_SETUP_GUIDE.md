# SIP LIMS Workflow Manager - Quick Setup Guide

This guide will walk you through the one-time setup process for the SIP LIMS Workflow Manager.

## 1. Prerequisite: Install Docker Desktop

This application runs in a standardized Docker container to ensure perfect consistency across all computers. You must install Docker Desktop to use it.

1.  **Download the installer:** Go to the official Docker website and download the installer for your operating system:
    *   [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
    *   [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2.  **Run the installer:** Follow the on-screen instructions to complete the installation.
3.  **Start Docker Desktop:** After installation, open the Docker Desktop application. You should see a whale icon in your menu bar (macOS) or system tray (Windows).

---

## 2. Application Setup

Once Docker Desktop is installed and running, you can set up the application.

### Download and Extract
-   Download the latest `sip_lims_workflow_manager` .zip file from the shared drive or GitHub.
-   Extract it to a permanent location on your computer (e.g., your Desktop or Documents folder).

### Run the Docker Setup Script (One-time only)
This script will check your Docker installation and guide you through logging into the private container registry where the application image is stored.

-   **On macOS:** Double-click `setup_docker.command`.
-   **On Windows:** Double-click `setup_docker.bat`.

The script will provide on-screen instructions for creating a GitHub Personal Access Token (PAT) and logging in. This is a necessary one-time step to pull the private Docker image.

---

## 3. Launch the Application

After the one-time setup is complete, you can start the application at any time:

-   **On macOS:** Double-click `run.command`.
-   **On Windows:** Double-click `run.bat`.

The application will start inside a Docker container, and the user interface will open automatically in your default web browser.