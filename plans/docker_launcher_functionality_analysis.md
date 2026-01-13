# Docker Launcher Functionality Analysis

## Executive Summary

The [`run.mac.command`](../run.mac.command) and [`run.windows.bat`](../run.windows.bat) scripts are **Docker container orchestrators** that set up and launch a prebuilt Docker image containing the LIMS workflow manager. The workflow manager application itself is fully contained within the Docker image - the run scripts only handle the **host-side setup and container orchestration**.

## Core Launcher Responsibilities

### 1. Docker Image Management (Branch-Aware)

**Purpose**: Ensure the correct Docker image is available and up-to-date for the current Git branch.

**Key Functions**:
- **Branch Detection**: Use [`utils/branch_utils.py`](../utils/branch_utils.py) to detect current Git branch
- **Image Name Generation**: Create branch-specific image names:
  - Local: `sip-lims-workflow-manager:{branch-tag}`
  - Remote: `ghcr.io/rrmalmstrom/sip_lims_workflow_manager:{branch-tag}`
- **Update Detection**: Use [`src/update_detector.py`](../src/update_detector.py) to check for image updates
- **Image Cleanup**: Stop/remove old containers before launching new ones

**Current Implementation**:
```bash
# Mac version
CURRENT_BRANCH=$(get_current_branch_tag)
LOCAL_IMAGE_NAME=$(get_local_image_name)
REMOTE_IMAGE_NAME=$(get_remote_image_name)
```

```batch
# Windows version
call "%DIR%utils\branch_utils.bat"
REM Sets: CURRENT_BRANCH, LOCAL_IMAGE_NAME, REMOTE_IMAGE_NAME
```

### 2. Volume Mounting Strategy

**Purpose**: Mount host directories into the container for data persistence and script access.

**Required Volumes**:

1. **Project Data Volume**:
   - **Host Path**: User-selected project folder (drag-and-drop)
   - **Container Path**: `/data`
   - **Purpose**: Project files, workflow state, results
   - **Access**: Read-write

2. **Scripts Volume**:
   - **Host Path**: Workflow-specific scripts directory
   - **Container Path**: `/workflow-scripts`
   - **Purpose**: Python workflow scripts
   - **Access**: Read-only (in production)

**Current Implementation**:
```yaml
# docker-compose.yml
volumes:
  - type: bind
    source: ${PROJECT_PATH}
    target: /data
  - type: bind
    source: ${SCRIPTS_PATH}
    target: /workflow-scripts
```

### 3. Environment Variable Configuration

**Purpose**: Pass configuration and metadata to the containerized application.

**Required Environment Variables**:

| Variable | Purpose | Source |
|----------|---------|--------|
| `PROJECT_NAME` | Display name for project | Extracted from project path |
| `PROJECT_PATH` | Host project path | User selection |
| `SCRIPTS_PATH` | Host scripts path | Mode-dependent |
| `WORKFLOW_TYPE` | Workflow type (sip/sps-ce) | User selection |
| `APP_ENV` | Environment mode | production/development |
| `DOCKER_IMAGE` | Image to use | Branch-aware selection |
| `USER_ID` | Host user ID | Platform-specific detection |
| `GROUP_ID` | Host group ID | Platform-specific detection |

### 4. User Interface & Interaction

**Purpose**: Collect user inputs and provide feedback during setup.

**Required User Interactions**:

1. **Workflow Type Selection**:
   ```
   🧪 Select workflow type:
   1) SIP (Stable Isotope Probing)
   2) SPS-CE (Single Particle Sorting - Cell Enrichment)
   ```

2. **Mode Selection** (for developers):
   ```
   🔧 Developer mode detected
   Choose your workflow mode:
   1) Production mode (auto-updates, centralized scripts)
   2) Development mode (local scripts, no auto-updates)
   ```

3. **Project Folder Selection**:
   ```
   Please drag and drop your project folder here, then press Enter:
   ```

4. **Scripts Folder Selection** (development mode):
   ```
   Please drag and drop your {workflow_type} workflow development scripts folder here:
   ```

### 5. Update Detection & Management

**Purpose**: Ensure all components are up-to-date before launching.

**Update Checks**:

1. **Fatal Sync Error Check**:
   - Use [`src/fatal_sync_checker.py`](../src/fatal_sync_checker.py)
   - Prevent launching with corrupted state

2. **Workflow Manager Repository Updates**:
   - Check if local repository is behind remote
   - Auto-update if no local changes

3. **Docker Image Updates**:
   - Use [`src/update_detector.py`](../src/update_detector.py)
   - Compare local vs remote image digests
   - Handle chronology uncertainty warnings

4. **Workflow Scripts Updates**:
   - Use [`src/scripts_updater.py`](../src/scripts_updater.py)
   - Update workflow-specific script repositories

### 6. Container Lifecycle Management

**Purpose**: Manage Docker container startup, monitoring, and cleanup.

**Container Operations**:

1. **Pre-launch Cleanup**:
   ```bash
   # Stop and remove existing workflow manager containers
   docker stop $container_ids
   docker rm $container_ids
   ```

2. **Container Launch**:
   ```bash
   # Use docker-compose for orchestration
   docker-compose up
   ```

3. **Health Monitoring**:
   ```yaml
   # docker-compose.yml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

## Platform-Specific Differences

### macOS Implementation ([`run.mac.command`](../run.mac.command))

**Strengths**:
- Robust bash functions with proper error handling
- Clean variable scoping and function composition
- Reliable user input processing
- Comprehensive error messages

**Key Patterns**:
```bash
# Function-based architecture
source "$DIR/utils/branch_utils.sh"
validate_git_repository
CURRENT_BRANCH=$(get_current_branch_tag)

# Clean user input processing
PROJECT_PATH=$(echo "$PROJECT_PATH" | tr -d '\r\n' | sed "s/'//g" | xargs)

# Proper user ID detection
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
```

### Windows Implementation ([`run.windows.bat`](../run.windows.bat))

**Current Problems**:
- Complex variable scoping with `endlocal`/`setlocal`
- Fragile JSON parsing without proper error handling
- Inconsistent error handling patterns
- String processing limitations

**Key Issues**:
```batch
REM Variable export pattern that doesn't work reliably
endlocal & (
    set "CURRENT_BRANCH=%CURRENT_BRANCH%"
    set "LOCAL_IMAGE_NAME=%LOCAL_IMAGE_NAME%"
    set "REMOTE_IMAGE_NAME=%REMOTE_IMAGE_NAME%"
)

REM Complex JSON parsing
for /f "delims=" %%i in ('python3 -c "import sys, json; data = json.load(open('temp_update_result.json')); print('true' if data.get('update_available', False) else 'false')" 2^>nul') do set "UPDATE_AVAILABLE=%%i"
```

## Cross-Platform Python Solution Analysis

### Feasibility Assessment

**✅ HIGHLY FEASIBLE** - The launcher functionality is well-suited for a unified Python implementation:

1. **Docker Operations**: Python's `subprocess` module handles Docker commands consistently across platforms
2. **File Operations**: Python's `pathlib` provides cross-platform path handling
3. **User Interface**: Click library provides excellent cross-platform CLI interfaces
4. **JSON Processing**: Native Python JSON handling eliminates parsing issues
5. **Environment Variables**: Python's `os.environ` works identically across platforms

### Key Advantages of Python Solution

1. **Eliminates Batch Limitations**:
   - No variable scoping issues
   - Robust error handling with exceptions
   - Native JSON processing
   - Consistent string operations

2. **Leverages Existing Infrastructure**:
   - [`utils/branch_utils.py`](../utils/branch_utils.py) already exists
   - [`src/update_detector.py`](../src/update_detector.py) already exists
   - [`src/scripts_updater.py`](../src/scripts_updater.py) already exists

3. **Improved User Experience**:
   - Rich terminal formatting with Click
   - Better error messages and guidance
   - Consistent behavior across platforms
   - Progress indicators for long operations

4. **Simplified Maintenance**:
   - Single codebase instead of two
   - Easier testing and validation
   - Consistent feature parity

### Implementation Strategy

**Core Architecture**:
```python
# Unified launcher structure
class DockerLauncher:
    def __init__(self):
        self.platform = self.detect_platform()
        self.branch_utils = BranchUtils()
        self.update_detector = UpdateDetector()
        self.scripts_updater = ScriptsUpdater()
    
    def launch(self):
        # 1. Validate environment
        self.validate_docker()
        self.validate_git_repository()
        
        # 2. Detect branch and generate image names
        self.setup_branch_info()
        
        # 3. User interactions
        workflow_type = self.select_workflow_type()
        mode = self.detect_mode()
        project_path, scripts_path = self.handle_mode_selection(mode)
        
        # 4. Update checks and management
        self.perform_updates(workflow_type)
        
        # 5. Launch container
        self.launch_docker_container(project_path, scripts_path, workflow_type)
```

**Platform Adaptation**:
```python
class PlatformAdapter:
    @staticmethod
    def get_user_ids():
        if platform.system() == "Windows":
            return {"USER_ID": "1000", "GROUP_ID": "1000"}
        else:
            return {
                "USER_ID": str(os.getuid()),
                "GROUP_ID": str(os.getgid())
            }
    
    @staticmethod
    def validate_docker():
        # Cross-platform Docker validation
        try:
            subprocess.run(["docker", "info"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
```

## Conclusion

**The Docker launcher functionality is perfectly suited for a unified Python implementation.** The current run scripts are essentially:

1. **Environment Setup Scripts** - collecting paths and configuration
2. **Docker Orchestrators** - launching containers with proper volume mounts
3. **Update Managers** - ensuring components are current

All of these functions can be implemented more reliably and maintainably in Python, leveraging the existing Python infrastructure already built for the project. The workflow manager application itself remains unchanged within the Docker container.

**Recommendation**: Proceed with unified Python launcher implementation to eliminate Windows batch limitations while maintaining all current functionality.