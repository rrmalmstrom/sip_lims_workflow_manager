# Unified Python Docker Launcher

## Overview

The **Unified Python Docker Launcher** (`run.py`) is a cross-platform replacement for the platform-specific scripts [`run.mac.command`](../run.mac.command) and [`run.windows.bat`](../run.windows.bat). This single Python script provides consistent functionality across Windows, macOS, and Linux platforms.

## Key Benefits

### ✅ **Eliminates Windows Batch Problems**
- **No Variable Scoping Issues**: Python variables work consistently across all contexts
- **Robust Error Handling**: Python exceptions vs fragile batch error codes
- **Native JSON Processing**: No more fragile parsing with external calls
- **Consistent String Operations**: Python string methods work reliably
- **Cross-Platform Path Handling**: `pathlib` handles all platforms uniformly

### ✅ **Leverages Existing Infrastructure**
- **Reuses [`utils/branch_utils.py`](../utils/branch_utils.py)**: No code duplication
- **Integrates [`src/update_detector.py`](../src/update_detector.py)**: Existing update logic
- **Uses [`src/scripts_updater.py`](../src/scripts_updater.py)**: Script management
- **Maintains [`docker-compose.yml`](../docker-compose.yml)**: No container changes

### ✅ **Improves User Experience**
- **Rich CLI Interface**: Click provides excellent user interaction (with fallback)
- **Better Error Messages**: Clear, actionable error reporting
- **Progress Indicators**: Visual feedback for long operations
- **Consistent Behavior**: Same experience across all platforms
- **Command Line Options**: Advanced users can skip prompts

### ✅ **Simplifies Maintenance**
- **Single Codebase**: One script instead of bash + batch
- **Easier Testing**: Python unit tests vs platform-specific testing
- **Better Documentation**: Python docstrings and type hints
- **Version Control**: Single file to track changes

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                 Unified Python Launcher                     │
├─────────────────────────────────────────────────────────────┤
│  run.py (Single entry point for all platforms)             │
│  ├── CLI Interface (Click-based with argparse fallback)    │
│  ├── Platform Detection & Adaptation                       │
│  ├── Docker Container Orchestration                        │
│  ├── Update Detection & Management                         │
│  └── User Interaction Management                           │
├─────────────────────────────────────────────────────────────┤
│                 Existing Infrastructure                     │
│  ├── utils/branch_utils.py (Branch detection)              │
│  ├── src/update_detector.py (Docker image updates)         │
│  ├── src/scripts_updater.py (Script repository updates)    │
│  └── docker-compose.yml (Container configuration)          │
├─────────────────────────────────────────────────────────────┤
│                 Platform Adapters                          │
│  ├── Windows: User ID mapping, path handling               │
│  ├── macOS: User ID detection, Docker for Mac             │
│  └── Linux: Permissions, Docker engine compatibility       │
└─────────────────────────────────────────────────────────────┘
```

### Key Classes

1. **`DockerLauncher`**: Main orchestrator class
2. **`PlatformAdapter`**: Platform-specific adaptations
3. **`UserInterface`**: Rich CLI interface with Click/fallback
4. **`ContainerManager`**: Docker container lifecycle management
5. **`UpdateManager`**: Integration with existing update systems

## Usage

### Basic Usage

```bash
# Interactive mode (prompts for all inputs)
python run.py

# With conda environment
conda activate sip-lims && python run.py
```

### Command Line Options

```bash
# Specify workflow type
python run.py --workflow-type sip

# Skip update checks
python run.py --no-updates

# Development mode with local scripts
python run.py --mode development --scripts-path /path/to/scripts

# Full specification
python run.py --workflow-type sps-ce --project-path /path/to/project --mode production
```

### Help and Version

```bash
# Show help
python run.py --help

# Show version
python run.py --version
```

## Platform Compatibility

### Dependency Handling

The launcher automatically detects and adapts to available dependencies:

- **With Click**: Full rich interface with colors, progress bars, and enhanced prompts
- **Without Click**: Fallback to standard library with basic colored output

### Platform-Specific Features

#### Windows
- **User ID Mapping**: Uses standard Docker Desktop mapping (1000:1000)
- **Path Handling**: Properly handles Windows path separators and drive letters
- **Environment Variables**: Configurable via `DOCKER_USER_ID`/`DOCKER_GROUP_ID`

#### macOS
- **User ID Detection**: Uses `os.getuid()`/`os.getgid()`
- **Drag-and-Drop Support**: Handles escaped paths from Finder
- **Docker for Mac**: Compatible with Docker Desktop

#### Linux
- **Native Docker**: Works with Docker Engine
- **User Permissions**: Proper user/group ID mapping
- **Path Handling**: Native Unix path support

## Migration from Legacy Scripts

### For Users

**Old Way:**
```bash
# macOS
./run.mac.command

# Windows
run.windows.bat
```

**New Way:**
```bash
# All platforms
python run.py
```

### For Developers

The unified launcher maintains complete feature parity with the legacy scripts:

1. **Branch-aware Docker images**: ✅ Maintained
2. **Workflow type selection**: ✅ Maintained  
3. **Developer/Production modes**: ✅ Maintained
4. **Update detection**: ✅ Enhanced
5. **Container management**: ✅ Improved
6. **Error handling**: ✅ Significantly improved

## Workflow

### 1. Environment Validation
- Check Docker availability and status
- Validate Git repository state
- Display branch information

### 2. User Interaction
- Workflow type selection (SIP/SPS-CE)
- Mode detection (Developer/Production)
- Project folder selection
- Scripts folder selection (if development mode)

### 3. Update Management
- Fatal sync error checking
- Repository updates
- Docker image updates
- Scripts updates

### 4. Container Launch
- Environment variable preparation
- Container cleanup
- Docker Compose execution

## Error Handling

### Robust Error Recovery
- **Import Failures**: Graceful fallback to standard library
- **Docker Issues**: Clear error messages with troubleshooting hints
- **Path Problems**: Automatic path normalization and validation
- **Update Failures**: Non-blocking warnings with continuation options

### User-Friendly Messages
- **Color-coded Output**: Errors (red), warnings (yellow), success (green)
- **Actionable Guidance**: Specific steps to resolve issues
- **Context Information**: Relevant details for troubleshooting

## Testing

### Cross-Platform Testing
```bash
# Test help functionality
python run.py --help

# Test with different Python environments
python3 run.py --version
conda activate sip-lims && python run.py --version

# Test argument parsing
python run.py --workflow-type sip --no-updates
```

### Validation Checklist
- [ ] Works with system Python (fallback mode)
- [ ] Works with conda environment (Click mode)
- [ ] Handles missing dependencies gracefully
- [ ] Provides consistent user experience
- [ ] Maintains feature parity with legacy scripts

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'click'"
**Solution**: The launcher automatically falls back to standard library. This is normal behavior.

#### "Docker is not running"
**Solution**: Start Docker Desktop and try again.

#### "Not in a valid Git repository"
**Solution**: Ensure you're running from the project root directory.

#### Path issues on Windows
**Solution**: Use forward slashes or double backslashes in paths.

### Debug Mode
```bash
# Run with Python verbose mode for debugging
python -v run.py --help
```

## Future Enhancements

### Planned Features
- [ ] Configuration file support
- [ ] Logging to file
- [ ] Plugin system for custom workflows
- [ ] GUI wrapper for non-technical users

### Performance Optimizations
- [ ] Cached dependency detection
- [ ] Parallel update checking
- [ ] Optimized Docker operations

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Include comprehensive docstrings
- Maintain cross-platform compatibility

### Testing Requirements
- Test on Windows, macOS, and Linux
- Test with and without Click dependency
- Validate all command-line options
- Ensure feature parity with legacy scripts

## Conclusion

The Unified Python Docker Launcher represents a significant improvement over the legacy platform-specific scripts. It eliminates Windows batch limitations, provides a consistent user experience across platforms, and leverages the existing Python infrastructure for better maintainability and reliability.

**Key Achievement**: Single, robust, cross-platform solution that replaces fragile platform-specific scripts while maintaining complete feature parity and improving user experience.