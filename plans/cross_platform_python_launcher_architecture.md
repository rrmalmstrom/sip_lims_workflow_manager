# Cross-Platform Python Launcher Architecture

## Executive Summary

**RECOMMENDATION: Replace platform-specific scripts with a unified Python launcher**

The current [`run.windows.bat`](../run.windows.bat) and [`run.mac.command`](../run.mac.command) approach has fundamental architectural problems that can be completely eliminated by using a cross-platform Python solution. This approach leverages the existing Python infrastructure already required by the project.

## Current Problems with Platform-Specific Scripts

### Windows Batch Limitations
1. **Variable Scoping Issues**: Batch `endlocal`/`setlocal` doesn't work like bash variable scoping
2. **Error Handling Mismatch**: Batch error patterns don't match bash patterns
3. **String Processing Limitations**: Complex string operations are fragile in batch
4. **JSON Processing Issues**: No native JSON support, requires external Python calls
5. **Function Call Patterns**: Batch labels/goto don't work like bash functions

### Maintenance Burden
1. **Duplicate Logic**: Same functionality implemented twice in different languages
2. **Testing Complexity**: Need to validate on both platforms separately
3. **Feature Parity**: Keeping both scripts synchronized is error-prone
4. **Documentation Overhead**: Platform-specific instructions and troubleshooting

## Proposed Solution: Unified Python Launcher

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Cross-Platform Launcher                  │
├─────────────────────────────────────────────────────────────┤
│  run.py (Single Python script for all platforms)           │
│  ├── Platform Detection (Windows/macOS/Linux)              │
│  ├── User Interface (CLI with rich formatting)             │
│  ├── Docker Management (unified across platforms)          │
│  ├── Update Detection (existing Python infrastructure)     │
│  └── Error Handling (consistent across platforms)          │
├─────────────────────────────────────────────────────────────┤
│                    Platform Adapters                        │
│  ├── Windows: File path handling, Docker Desktop detection │
│  ├── macOS: User ID detection, Docker for Mac integration  │
│  └── Linux: User permissions, Docker engine compatibility  │
├─────────────────────────────────────────────────────────────┤
│                    Existing Infrastructure                  │
│  ├── utils/branch_utils.py (already cross-platform)       │
│  ├── src/update_detector.py (already cross-platform)      │
│  ├── src/scripts_updater.py (already cross-platform)      │
│  └── docker-compose.yml (already cross-platform)          │
└─────────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Single Source of Truth**: One script with all logic
2. **Consistent User Experience**: Same interface across all platforms
3. **Robust Error Handling**: Python's exception handling vs batch/bash limitations
4. **Rich User Interface**: Better prompts, progress indicators, colored output
5. **Easier Testing**: Single codebase to test and validate
6. **Better Maintainability**: One script to update and debug

## Technical Implementation Strategy

### 1. Entry Point Strategy

Instead of platform-specific scripts, provide multiple entry points:

```
# Cross-platform Python launcher
run.py                    # Main launcher script

# Platform-specific convenience wrappers (minimal)
run.bat                   # Windows: @echo off && python run.py %*
run.command              # macOS: #!/bin/bash && python3 run.py "$@"
run.sh                   # Linux: #!/bin/bash && python3 run.py "$@"
```

### 2. Python Dependencies

The launcher would use only standard library modules to avoid dependency issues:

```python
import os
import sys
import platform
import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, List
```

### 3. Platform Detection and Adaptation

```python
class PlatformAdapter:
    """Base class for platform-specific adaptations"""
    
    @staticmethod
    def detect_platform() -> str:
        """Detect current platform"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    
    @staticmethod
    def get_user_ids() -> Dict[str, str]:
        """Get user/group IDs for Docker mapping"""
        # Platform-specific implementation
        pass
    
    @staticmethod
    def validate_docker() -> bool:
        """Check if Docker is available and running"""
        # Platform-specific Docker validation
        pass
```

### 4. User Interface Strategy

Use Python's built-in capabilities for rich user interaction:

```python
class UserInterface:
    """Cross-platform user interface with rich formatting"""
    
    def __init__(self):
        self.use_colors = self._supports_colors()
    
    def _supports_colors(self) -> bool:
        """Detect if terminal supports colors"""
        return (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            os.environ.get('TERM') != 'dumb'
        )
    
    def success(self, message: str):
        """Print success message with formatting"""
        if self.use_colors:
            print(f"\033[92m✅ {message}\033[0m")
        else:
            print(f"✅ {message}")
    
    def error(self, message: str):
        """Print error message with formatting"""
        if self.use_colors:
            print(f"\033[91m❌ {message}\033[0m")
        else:
            print(f"❌ {message}")
    
    def prompt_choice(self, question: str, choices: List[str]) -> str:
        """Interactive choice prompt with validation"""
        # Robust input handling with validation
        pass
    
    def prompt_path(self, message: str, validate_exists: bool = True) -> Path:
        """Path input with drag-and-drop support and validation"""
        # Cross-platform path handling
        pass
```

## Detailed Implementation Plan

### Phase 1: Core Launcher Infrastructure

1. **Create `run.py`** with basic structure:
   - Platform detection
   - Command-line argument parsing
   - Basic user interface
   - Integration with existing Python utilities

2. **Platform Adapters** for:
   - User ID detection (Windows vs Unix)
   - Docker validation (Docker Desktop vs Docker Engine)
   - Path handling (Windows vs Unix paths)

3. **Error Handling Strategy**:
   - Consistent error messages across platforms
   - Graceful fallbacks when components fail
   - Clear troubleshooting guidance

### Phase 2: Feature Migration

1. **Branch Detection**: Use existing [`utils/branch_utils.py`](../utils/branch_utils.py)
2. **Update Detection**: Use existing [`src/update_detector.py`](../src/update_detector.py)
3. **Script Management**: Use existing [`src/scripts_updater.py`](../src/scripts_updater.py)
4. **Docker Management**: Unified docker-compose integration

### Phase 3: User Experience Enhancement

1. **Rich Prompts**: Better than current bash/batch prompts
2. **Progress Indicators**: Show progress during updates
3. **Validation Feedback**: Clear success/error states
4. **Help System**: Built-in help and troubleshooting

### Phase 4: Testing and Validation

1. **Cross-Platform Testing**: Single test suite for all platforms
2. **Integration Testing**: With existing Docker infrastructure
3. **User Acceptance Testing**: Lab member validation
4. **Performance Testing**: Startup time and responsiveness

## Migration Strategy

### Immediate Benefits
- **No Windows Batch Debugging**: Eliminate all batch-specific issues
- **Consistent Behavior**: Same logic on all platforms
- **Better Error Messages**: Python exception handling vs batch error codes
- **Easier Development**: Single codebase to maintain

### Backward Compatibility
- Keep existing scripts as thin wrappers during transition
- Gradual migration allows testing without disruption
- Clear migration path for users

### Risk Mitigation
- **Python Availability**: Python 3 is already required by the project
- **Dependency Management**: Use only standard library modules
- **Fallback Strategy**: Keep minimal platform scripts as backup
- **Testing Strategy**: Comprehensive cross-platform validation

## User Experience Comparison

### Current Experience (Platform-Specific)
```
Windows: Double-click run.windows.bat
  - Batch script limitations
  - Poor error messages
  - Platform-specific bugs

macOS: Double-click run.mac.command  
  - Bash script complexity
  - Different behavior than Windows
  - Maintenance burden
```

### Proposed Experience (Unified)
```
All Platforms: python run.py
  - Consistent interface
  - Rich error messages
  - Single codebase
  - Better user guidance
```

## Technical Requirements

### Python Version
- **Minimum**: Python 3.7 (already required by project)
- **Recommended**: Python 3.8+ for better typing support

### Dependencies
- **Standard Library Only**: No additional pip installs required
- **Existing Project Dependencies**: Leverage current Python infrastructure

### Platform Support
- **Windows 10/11**: With Python 3.7+
- **macOS 10.15+**: With Python 3.7+
- **Linux**: Ubuntu 18.04+ or equivalent

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create basic `run.py` structure
- [ ] Implement platform detection
- [ ] Create user interface framework
- [ ] Basic integration with existing utilities

### Week 2: Feature Implementation
- [ ] Migrate branch detection logic
- [ ] Implement update detection integration
- [ ] Add Docker management functionality
- [ ] Create workflow selection interface

### Week 3: Platform Adaptation
- [ ] Windows-specific adaptations
- [ ] macOS-specific adaptations
- [ ] Linux compatibility testing
- [ ] Cross-platform validation

### Week 4: Testing and Refinement
- [ ] Comprehensive testing on all platforms
- [ ] User experience refinement
- [ ] Documentation updates
- [ ] Migration strategy implementation

## Success Metrics

1. **Functionality Parity**: All current features work identically across platforms
2. **User Experience**: Improved prompts, error messages, and guidance
3. **Maintainability**: Single codebase reduces maintenance burden by 50%
4. **Reliability**: Eliminate Windows batch-specific failures
5. **Testing Coverage**: Single test suite covers all platforms

## Conclusion

**The unified Python launcher approach eliminates all the fundamental problems with the current Windows batch implementation while providing a superior user experience across all platforms.**

This strategy leverages the existing Python infrastructure, provides better error handling, and creates a single source of truth for the launcher logic. The migration can be done incrementally with minimal risk to existing users.

**Recommendation: Proceed with the unified Python launcher implementation rather than attempting to fix the Windows batch limitations.**