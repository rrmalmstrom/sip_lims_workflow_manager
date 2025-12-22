# Docker Compose Configuration Guide

This document provides technical details about the Docker Compose configuration used by the SIP LIMS Workflow Manager, based on the actual `docker-compose.yml` file.

## Overview

The application uses Docker Compose to orchestrate the containerized workflow manager with volume mounting, environment variable management, and resource allocation.

## Service Configuration

### Image Selection
```yaml
image: ${DOCKER_IMAGE:-ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest}
```
- Uses environment variable `DOCKER_IMAGE` 
- Defaults to `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:latest` if not set
- `run.command` sets this to `sip-lims-workflow-manager:latest` for development mode

### Container and Port Configuration
```yaml
container_name: sip-lims-workflow-manager
ports:
  - "127.0.0.1:8501:8501"
```
- Fixed container name for easy identification
- Port 8501 (Streamlit default) bound to localhost only

### Volume Mounting
```yaml
volumes:
  # Project data volume - user's project directory
  - type: bind
    source: ${PROJECT_PATH:-.}
    target: /data
    bind:
      create_host_path: true
  
  # Scripts volume - centralized workflow scripts repository
  - type: bind
    source: ${SCRIPTS_PATH:-~/.sip_lims_workflow_manager/scripts}
    target: /workflow-scripts
    bind:
      create_host_path: true

working_dir: /data
```
- **Project Data**: `PROJECT_PATH` → `/data` (defaults to current directory)
- **Scripts**: `SCRIPTS_PATH` → `/workflow-scripts` (defaults to `~/.sip_lims_workflow_manager/scripts`)
- **Auto-Creation**: `create_host_path: true` creates directories if missing
- **Working Directory**: Container starts in `/data`

### Environment Variables
```yaml
environment:
  - APP_ENV=${APP_ENV:-production}
```
- Only `APP_ENV` is explicitly set in docker-compose.yml
- Defaults to `production` if not specified
- `run.command` sets this to `development` when in development mode

### Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```
- Uses Streamlit's built-in health endpoint `/_stcore/health`
- Checks every 30 seconds with 10-second timeout
- 3 retries before marking unhealthy
- 40-second grace period for startup

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```
- **Memory**: 2GB limit, 512MB reserved
- **CPU**: 2 cores limit, 0.5 cores reserved
- Designed for "scientific computing workloads" (per comment)

### Restart Policy
```yaml
restart: "no"
```
- No automatic restart (appropriate for "development tool" per comment)

### Network Configuration
```yaml
networks:
  - sip-lims-network

networks:
  sip-lims-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```
- Creates isolated bridge network
- Uses subnet `172.20.0.0/16`

## Environment Variables Set by run.command

Based on `run.command`, these variables are set before running docker-compose:

| Variable | Set By | Purpose |
|----------|--------|---------|
| `DOCKER_IMAGE` | `run.command` | Selects production vs development image |
| `PROJECT_PATH` | `run.command` | User's project directory (from drag-and-drop) |
| `SCRIPTS_PATH` | `run.command` | Scripts location (centralized or local dev) |
| `APP_ENV` | `run.command` | `production` or `development` |
| `USER_ID` | `run.command` | Host user ID (from `id -u`) |
| `GROUP_ID` | `run.command` | Host group ID (from `id -g`) |

Note: `USER_ID` and `GROUP_ID` are set by `run.command` but not explicitly used in `docker-compose.yml`. They may be used by the container's entrypoint script.

## Integration with run.command

The `run.command` script manages the Docker Compose lifecycle:

1. **Container Cleanup**: Stops and removes existing workflow manager containers
2. **Environment Setup**: Sets required environment variables
3. **Image Management**: Handles Docker image updates
4. **Launch**: Executes `docker-compose up`

This provides a seamless user experience without requiring Docker Compose knowledge.