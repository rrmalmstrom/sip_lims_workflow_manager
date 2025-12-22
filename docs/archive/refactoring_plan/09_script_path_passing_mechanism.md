# 09 - Script Path Passing Mechanism Design

## Overview
Comprehensive design for the mechanism that passes script path information from shell scripts through Streamlit to the Python application components.

## Data Flow Architecture

### Complete Path Flow
```
1. Shell Script (run.command/run.bat)
   ↓ [Mode Detection & User Choice]
2. Script Path Selection
   ↓ [Command Line Argument]
3. Streamlit Launch
   ↓ [Argument Parsing]
4. App.py (Python Application)
   ↓ [Session State Storage]
5. Project Class (src/core.py)
   ↓ [Constructor Parameter]
6. ScriptRunner (src/logic.py)
   ↓ [Script Execution]
7. Script Execution Context
```

## Component-by-Component Design

### 1. Shell Script Layer (run.command/run.bat)

#### Mode Detection and Path Selection
```bash
# Bash implementation
select_script_path() {
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        # Developer choice logic
        echo "Choose script source:"
        echo "1) Development scripts (../sip_scripts_workflow_gui)"
        echo "2) Production scripts (../sip_scripts_production)"
        read -p "Enter choice: " choice
        
        case $choice in
            1) SCRIPT_PATH="../sip_scripts_workflow_gui" ;;
            2) SCRIPT_PATH="../sip_scripts_production" ;;
            *) SCRIPT_PATH="../sip_scripts_production" ;;
        esac
    else
        # Production automatic selection
        SCRIPT_PATH="../sip_scripts_production"
    fi
    
    # Validation
    if [ ! -d "$SCRIPT_PATH" ]; then
        echo "ERROR: Script directory not found: $SCRIPT_PATH"
        exit 1
    fi
}
```

#### Streamlit Launch with Arguments
```bash
# Launch command with script path
launch_application() {
    streamlit run app.py \
        --server.headless=true \
        --server.address=127.0.0.1 \
        -- \
        --script-path="$SCRIPT_PATH"
}
```

### 2. Streamlit Argument Separation

#### Command Structure
```bash
streamlit run app.py [STREAMLIT_OPTIONS] -- [APP_OPTIONS]
```

#### Argument Separation Rules
- **Before `--`**: Streamlit configuration arguments
- **After `--`**: Application-specific arguments
- **Streamlit Options**: `--server.headless=true`, `--server.address=127.0.0.1`
- **App Options**: `--script-path="../sip_scripts_production"`

### 3. Python Application Layer (app.py)

#### Argument Parsing Implementation
```python
import argparse
from pathlib import Path

def parse_script_path_argument():
    """
    Parse command line arguments to extract script path.
    Uses argparse with known args to avoid Streamlit conflicts.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--script-path',
        type=str,
        default='scripts',
        help='Path to scripts directory'
    )
    
    try:
        # Parse only known args to avoid Streamlit conflicts
        args, unknown = parser.parse_known_args()
        
        # Convert to Path and validate
        script_path = Path(args.script_path)
        
        # Validation with fallback
        if not script_path.exists():
            print(f"Warning: Script path not found: {script_path}")
            print("Falling back to default 'scripts' directory")
            return Path("scripts")
        
        return script_path
        
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        print("Using default 'scripts' directory")
        return Path("scripts")

# Global initialization
SCRIPT_PATH = parse_script_path_argument()
```

#### Session State Integration
```python
def main():
    # Initialize session state with script path
    if 'script_path' not in st.session_state:
        st.session_state.script_path = SCRIPT_PATH
    
    # Debug information for transparency
    if st.session_state.script_path != Path("scripts"):
        st.sidebar.info(f"📁 External scripts: {st.session_state.script_path}")
```

### 4. Project Class Integration (src/core.py)

#### Constructor Modification
```python
class Project:
    def __init__(self, project_path: Path, script_path: Path = None, load_workflow: bool = True):
        self.path = project_path
        self.script_path = script_path or (project_path / "scripts")
        
        # Pass script path to ScriptRunner
        self.script_runner = ScriptRunner(
            project_path=self.path,
            script_path=self.script_path
        )
```

#### All Project Instantiation Points
```python
# Pattern for all Project instantiations in app.py
st.session_state.project = Project(
    project_path=project_path,
    script_path=st.session_state.script_path
)
```

### 5. ScriptRunner Integration (src/logic.py)

#### Constructor Enhancement
```python
class ScriptRunner:
    def __init__(self, project_path: Path, script_path: Path = None):
        self.project_path = project_path  # Execution context
        self.script_path = script_path or (project_path / "scripts")  # Script source
        
        # Initialize execution environment
        self.setup_execution_environment()
    
    def run(self, script_name: str, args: list = None):
        """
        Execute script from script_path in project_path context.
        """
        # Source script from script_path
        script_file = self.script_path / script_name
        
        if not script_file.exists():
            raise FileNotFoundError(f"Script not found: {script_file}")
        
        # Execute in project_path context (working directory)
        self.execute_script_in_project_context(script_file, args)
```

## Error Handling Strategy

### 1. Shell Script Level Errors
```bash
# Missing script directory
validate_script_path() {
    if [ ! -d "$SCRIPT_PATH" ]; then
        echo "❌ ERROR: Script directory not found: $SCRIPT_PATH"
        echo ""
        echo "💡 SOLUTION:"
        echo "   1. Run setup.command to initialize repositories"
        echo "   2. Check internet connection"
        echo "   3. Verify setup completed successfully"
        echo ""
        exit 1
    fi
}

# Invalid user input
get_validated_choice() {
    local attempts=0
    local max_attempts=3
    
    while [ $attempts -lt $max_attempts ]; do
        read -p "Enter choice (1 or 2): " choice
        case $choice in
            1|2) echo "$choice"; return 0 ;;
            *) 
                echo "Invalid choice. Please enter 1 or 2."
                attempts=$((attempts + 1))
                ;;
        esac
    done
    
    echo "Too many invalid attempts. Using production scripts."
    echo "2"
}
```

### 2. Python Application Level Errors
```python
def handle_script_path_errors(script_path: Path) -> Path:
    """
    Handle various script path error conditions.
    
    Args:
        script_path: The attempted script path
        
    Returns:
        Valid script path (with fallback if necessary)
    """
    # Check if path exists
    if not script_path.exists():
        print(f"Warning: Script path does not exist: {script_path}")
        
        # Try fallback to nested scripts
        fallback_path = Path("scripts")
        if fallback_path.exists():
            print(f"Using fallback path: {fallback_path}")
            return fallback_path
        
        # Last resort: create empty path info
        print("No script directory available - some features may not work")
        return script_path  # Return original for error display
    
    # Check if path is a directory
    if not script_path.is_dir():
        print(f"Warning: Script path is not a directory: {script_path}")
        return Path("scripts")
    
    # Check if directory contains scripts
    scripts = list(script_path.glob("*.py"))
    if not scripts:
        print(f"Warning: No Python scripts found in: {script_path}")
        # Continue anyway - directory might be populated later
    
    return script_path
```

### 3. Component Integration Errors
```python
def validate_component_integration():
    """
    Validate that script path is properly passed through all components.
    """
    checks = []
    
    # Check session state
    if 'script_path' in st.session_state:
        checks.append("✅ Session state: script_path present")
    else:
        checks.append("❌ Session state: script_path missing")
    
    # Check project integration
    if st.session_state.get('project'):
        project = st.session_state.project
        if hasattr(project, 'script_path'):
            checks.append("✅ Project: script_path configured")
        else:
            checks.append("❌ Project: script_path missing")
    
    return checks
```

## Test Specifications (TDD)

### End-to-End Integration Tests
```python
# Test 1: Complete path flow
def test_complete_script_path_flow():
    # Given: run.command executed with developer mode choice 1
    # When: application launches and project is loaded
    # Then: project should use ../sip_scripts_workflow_gui
    # And: script execution should work from external path

# Test 2: Production mode flow
def test_production_mode_script_path_flow():
    # Given: run.command executed without developer marker
    # When: application launches automatically
    # Then: project should use ../sip_scripts_production
    # And: no user prompts should appear

# Test 3: Argument parsing
def test_streamlit_argument_separation():
    # Given: streamlit launched with -- separator
    # When: app.py parses arguments
    # Then: should correctly extract --script-path
    # And: should not interfere with Streamlit arguments

# Test 4: Error handling
def test_missing_script_directory_handling():
    # Given: script path points to non-existent directory
    # When: application attempts to use script path
    # Then: should show clear error messages
    # And: should provide actionable solutions
```

### Component Integration Tests
```python
# Test 5: Session state integration
def test_session_state_script_path():
    # Given: script path parsed from arguments
    # When: session state is initialized
    # Then: script_path should be stored correctly
    # And: should persist across Streamlit reruns

# Test 6: Project integration
def test_project_script_path_integration():
    # Given: session state contains script_path
    # When: Project is instantiated
    # Then: should receive script_path parameter
    # And: should configure ScriptRunner correctly

# Test 7: ScriptRunner integration
def test_script_runner_path_handling():
    # Given: ScriptRunner configured with external script_path
    # When: script execution is requested
    # Then: should source script from external path
    # And: should execute in project context
```

## Security Considerations

### Path Validation
```python
def validate_script_path_security(script_path: Path) -> bool:
    """
    Validate script path for security concerns.
    
    Args:
        script_path: Path to validate
        
    Returns:
        True if path is safe to use
    """
    # Convert to absolute path for validation
    abs_path = script_path.resolve()
    
    # Check for path traversal attempts
    if ".." in str(abs_path):
        print("Warning: Path traversal detected in script path")
        return False
    
    # Ensure path is within expected locations
    allowed_patterns = [
        "sip_scripts_workflow_gui",
        "sip_scripts_production",
        "scripts"
    ]
    
    path_str = str(abs_path).lower()
    if not any(pattern in path_str for pattern in allowed_patterns):
        print(f"Warning: Script path outside expected locations: {abs_path}")
        return False
    
    return True
```

### Argument Sanitization
```python
def sanitize_script_path_argument(raw_path: str) -> str:
    """
    Sanitize script path argument to prevent injection attacks.
    
    Args:
        raw_path: Raw path string from command line
        
    Returns:
        Sanitized path string
    """
    # Remove potentially dangerous characters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "{", "}"]
    sanitized = raw_path
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    # Normalize path separators
    sanitized = sanitized.replace("\\", "/")
    
    # Remove multiple consecutive slashes
    while "//" in sanitized:
        sanitized = sanitized.replace("//", "/")
    
    return sanitized
```

## Performance Considerations

### Caching Strategy
```python
# Cache script path validation results
@functools.lru_cache(maxsize=10)
def cached_script_path_validation(script_path_str: str) -> bool:
    """Cache script path validation results to avoid repeated filesystem checks."""
    return validate_script_path_security(Path(script_path_str))

# Cache available scripts list
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_available_scripts(script_path_str: str) -> list:
    """Cache list of available scripts to improve UI responsiveness."""
    script_path = Path(script_path_str)
    if script_path.exists():
        return [script.name for script in script_path.glob("*.py")]
    return []
```

### Lazy Loading
```python
class LazyScriptPathValidator:
    """Lazy validation of script paths to improve startup performance."""
    
    def __init__(self, script_path: Path):
        self.script_path = script_path
        self._validated = None
        self._scripts_cache = None
    
    @property
    def is_valid(self) -> bool:
        if self._validated is None:
            self._validated = self.script_path.exists() and self.script_path.is_dir()
        return self._validated
    
    @property
    def available_scripts(self) -> list:
        if self._scripts_cache is None and self.is_valid:
            self._scripts_cache = list(self.script_path.glob("*.py"))
        return self._scripts_cache or []
```

## Benefits of This Design

### For Developers
- ✅ Clear, traceable path from shell script to execution
- ✅ Flexible script source selection per session
- ✅ Comprehensive error handling with actionable messages
- ✅ Easy debugging with validation and logging

### For Production Users
- ✅ Transparent, automatic script path management
- ✅ No changes to user experience
- ✅ Reliable error handling and fallbacks
- ✅ Consistent behavior across sessions

### For Maintenance
- ✅ Clear separation of concerns between components
- ✅ Comprehensive test coverage for integration points
- ✅ Security validation and sanitization
- ✅ Performance optimization with caching

## Implementation Phases

### Phase 1: Shell Script Integration
- Implement mode detection and script path selection
- Add validation and error handling
- Test shell script argument passing

### Phase 2: Python Argument Parsing
- Implement argument parsing in app.py
- Add session state integration
- Test Streamlit argument separation

### Phase 3: Component Integration
- Modify Project and ScriptRunner classes
- Update all instantiation points
- Test end-to-end script path flow

### Phase 4: Error Handling and Security
- Implement comprehensive error handling
- Add security validation
- Add performance optimizations

This design provides a robust, secure, and maintainable mechanism for passing script path information through all layers of the application while preserving existing functionality and providing clear error handling.