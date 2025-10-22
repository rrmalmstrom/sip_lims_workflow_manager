# 07 - Core.py Modifications for Dynamic Script Paths

## Overview
Plan for modifying `src/core.py` to support external script paths while preserving all existing functionality and maintaining the project working directory for script execution.

## Current Core.py Analysis

### Key Components Requiring Modification
- **Line 35**: `def __init__(self, project_path: Path, load_workflow: bool = True)` - Add script_path parameter
- **Line 41**: `self.script_runner = ScriptRunner(self.path)` - Pass script_path to ScriptRunner
- **Line 256**: `self.script_runner.run(step["script"], args=args)` - Script execution (no change needed)

### Working Directory Preservation
**CRITICAL**: Script execution must continue to run in the PROJECT directory context, not the script source directory. The script_path only affects WHERE scripts are sourced from.

## Required Modifications

### 1. Modify Project Class Constructor
```python
# MODIFIED: Project class __init__ method (Line 35)
class Project:
    """
    Represents a single project folder, containing a workflow, its state,
    and all associated data. It coordinates the StateManager, SnapshotManager,
    and ScriptRunner.
    """
    def __init__(self, project_path: Path, script_path: Path = None, load_workflow: bool = True):
        self.path = project_path
        self.script_path = script_path or (project_path / "scripts")  # Default to nested
        self.workflow_file_path = self.path / "workflow.yml"
        
        self.state_manager = StateManager(self.path / "workflow_state.json")
        self.snapshot_manager = SnapshotManager(self.path, self.path / ".snapshots")
        # MODIFIED: Pass script_path to ScriptRunner
        self.script_runner = ScriptRunner(self.path, script_path=self.script_path)
        
        if load_workflow:
            if not self.workflow_file_path.is_file():
                raise FileNotFoundError(f"Workflow file not found at {self.workflow_file_path}")
            self.workflow = Workflow(self.workflow_file_path)
        else:
            self.workflow = None
```

### 2. Add Script Path Validation
```python
# NEW: Add script path validation method
def validate_script_path(self) -> bool:
    """
    Validate that the script path exists and contains scripts.
    Returns True if valid, False otherwise.
    """
    if not self.script_path.exists():
        print(f"Warning: Script path does not exist: {self.script_path}")
        return False
    
    if not self.script_path.is_dir():
        print(f"Warning: Script path is not a directory: {self.script_path}")
        return False
    
    # Check for Python scripts
    python_scripts = list(self.script_path.glob("*.py"))
    if not python_scripts:
        print(f"Warning: No Python scripts found in: {self.script_path}")
        return False
    
    return True

# NEW: Add to Project class
class Project:
    # ... existing methods ...
    
    def get_script_path(self) -> Path:
        """Get the configured script path."""
        return self.script_path
    
    def get_available_scripts(self) -> list[Path]:
        """Get list of available Python scripts."""
        if not self.script_path.exists():
            return []
        return list(self.script_path.glob("*.py"))
```

### 3. Preserve Script Execution Context
```python
# UNCHANGED: Script execution methods preserve project context
def run_step(self, step_id: str, user_inputs: Dict[str, Any] = None):
    """
    Starts a workflow step asynchronously for interactive execution.
    
    IMPORTANT: Script execution continues to run in PROJECT context,
    not script source context. Only script SOURCING uses external path.
    """
    # ... existing logic unchanged ...
    
    # Start the script asynchronously
    # ScriptRunner handles sourcing from script_path but executing in project context
    self.script_runner.run(step["script"], args=args)
```

## ScriptRunner Modifications Required

### Current ScriptRunner Interface
Based on the current usage in core.py, ScriptRunner needs to be modified to accept script_path:

```python
# REQUIRED: ScriptRunner constructor modification (in src/logic.py)
class ScriptRunner:
    def __init__(self, project_path: Path, script_path: Path = None):
        self.project_path = project_path  # WHERE scripts execute (working directory)
        self.script_path = script_path or (project_path / "scripts")  # WHERE scripts are sourced from
        # ... rest of initialization
    
    def run(self, script_name: str, args: list = None):
        """
        Run a script from script_path but execute in project_path context.
        
        Args:
            script_name: Name of script file (e.g., "my_script.py")
            args: Command line arguments for the script
        """
        # Source script from script_path
        script_file = self.script_path / script_name
        
        if not script_file.exists():
            raise FileNotFoundError(f"Script not found: {script_file}")
        
        # Execute script in project_path context (working directory)
        # Implementation details handled in ScriptRunner
        # ... existing execution logic with project_path as working directory
```

## Test Specifications (TDD)

### Test Cases
```python
# Test 1: Project initialization with script path
def test_project_with_custom_script_path():
    # Given: Project initialized with external script_path
    # When: Project is created
    # Then: script_runner should use external script_path for sourcing
    # And: project operations should use project_path for working directory

def test_project_default_script_path():
    # Given: Project initialized without script_path
    # When: Project is created
    # Then: script_runner should use project_path/scripts (current behavior)

# Test 2: Script path validation
def test_script_path_validation_valid():
    # Given: script_path points to directory with Python scripts
    # When: validate_script_path() is called
    # Then: should return True

def test_script_path_validation_invalid():
    # Given: script_path points to non-existent or empty directory
    # When: validate_script_path() is called
    # Then: should return False with appropriate warning

# Test 3: Working directory preservation
def test_script_execution_working_directory():
    # Given: Project with external script_path
    # When: script is executed via run_step()
    # Then: script should execute in project directory context
    # And: script should be sourced from external script_path

# Test 4: Backward compatibility
def test_backward_compatibility_nested_scripts():
    # Given: Project initialized without script_path (legacy mode)
    # When: Project operations occur
    # Then: should work exactly as before with nested scripts

# Test 5: Script discovery
def test_get_available_scripts():
    # Given: Project with external script_path containing scripts
    # When: get_available_scripts() is called
    # Then: should return list of scripts from external path
```

## Working Directory Guarantee

### Explicit Working Directory Management
```python
# NEW: Add working directory verification to Project class
class Project:
    def verify_execution_context(self) -> bool:
        """
        Verify that script execution will occur in correct project context.
        This is a safety check to ensure script_path changes don't affect execution context.
        """
        # Verify ScriptRunner is configured correctly
        if hasattr(self.script_runner, 'project_path'):
            return self.script_runner.project_path == self.path
        
        # Fallback verification
        return True
    
    def get_execution_info(self) -> dict:
        """
        Get information about script sourcing and execution context.
        Useful for debugging and verification.
        """
        return {
            'project_path': str(self.path),
            'script_source_path': str(self.script_path),
            'execution_context': str(self.path),  # Always project directory
            'script_sourcing': str(self.script_path)
        }
```

### Key Preservation Points
1. **Script Execution**: Always runs in project directory (self.path)
2. **File Operations**: All project file operations use self.path
3. **Working Directory**: ScriptRunner maintains project_path as working directory
4. **Script Sourcing**: Only the SOURCE of scripts changes (self.script_path)

## Error Handling Strategy

### Missing Script Path
```python
def handle_missing_script_path(self):
    """Handle case where script path doesn't exist."""
    if not self.script_path.exists():
        print(f"ERROR: Script path not found: {self.script_path}")
        print("Falling back to nested scripts directory")
        
        # Fallback to nested scripts
        fallback_path = self.path / "scripts"
        if fallback_path.exists():
            self.script_path = fallback_path
            print(f"Using fallback script path: {self.script_path}")
            return True
        else:
            print("ERROR: No script directory available")
            return False
    return True
```

### Script Not Found
```python
def find_script(self, script_name: str) -> Path:
    """
    Find a script file, with fallback logic.
    
    Args:
        script_name: Name of the script file
        
    Returns:
        Path to the script file
        
    Raises:
        FileNotFoundError: If script cannot be found
    """
    # Primary: Look in configured script path
    script_file = self.script_path / script_name
    if script_file.exists():
        return script_file
    
    # Fallback: Look in nested scripts (for transition period)
    fallback_file = self.path / "scripts" / script_name
    if fallback_file.exists():
        print(f"Warning: Using fallback script location for {script_name}")
        return fallback_file
    
    # Error: Script not found anywhere
    raise FileNotFoundError(
        f"Script '{script_name}' not found in:\n"
        f"  - {self.script_path}\n"
        f"  - {self.path / 'scripts'}"
    )
```

## Integration Points

### With App.py
- App.py passes script_path to Project constructor
- Project stores and uses script_path for script sourcing
- All project operations continue to use project_path

### With ScriptRunner
- Project passes both project_path and script_path to ScriptRunner
- ScriptRunner sources scripts from script_path
- ScriptRunner executes scripts in project_path context

### With Update System
- Project can provide script_path to update managers
- Updates occur in script_path location
- Project operations unaffected by update location

## Backward Compatibility

### Legacy Support
```python
# Backward compatibility for existing code
class Project:
    def __init__(self, project_path: Path, script_path: Path = None, load_workflow: bool = True):
        # ... initialization ...
        
        # Ensure backward compatibility
        if script_path is None:
            # Legacy behavior: use nested scripts
            self.script_path = project_path / "scripts"
        else:
            # New behavior: use external scripts
            self.script_path = script_path
```

### Migration Support
```python
def is_using_external_scripts(self) -> bool:
    """Check if project is using external script path."""
    nested_path = self.path / "scripts"
    return self.script_path != nested_path

def get_script_source_type(self) -> str:
    """Get description of script source type."""
    if self.is_using_external_scripts():
        return f"External: {self.script_path}"
    else:
        return "Nested: scripts/"
```

## Benefits

### For Developers
- ✅ Can use different script repositories
- ✅ Clear separation between script sourcing and execution
- ✅ All existing project operations work identically
- ✅ Easy to debug script sourcing vs execution issues

### For Production Users
- ✅ No changes to script execution behavior
- ✅ All project operations work exactly as before
- ✅ Working directory behavior unchanged
- ✅ Transparent script sourcing changes

### For Maintenance
- ✅ Clean separation of concerns
- ✅ Backward compatibility preserved
- ✅ Easy to test and verify
- ✅ Clear error handling and fallbacks

## Implementation Strategy

### Phase 1: Add Script Path Parameter
- Add script_path parameter to Project constructor
- Default to nested scripts for backward compatibility
- Test that existing functionality unchanged

### Phase 2: Modify ScriptRunner Integration
- Update ScriptRunner instantiation to pass script_path
- Verify script sourcing works from external path
- Ensure execution context remains in project directory

### Phase 3: Add Validation and Error Handling
- Implement script path validation
- Add fallback logic for missing scripts
- Test error scenarios and recovery

### Phase 4: Add Debugging and Information Methods
- Add methods to inspect script sourcing configuration
- Implement working directory verification
- Add comprehensive logging for troubleshooting

This approach ensures that the core Project class can source scripts from external directories while maintaining all existing behavior for project operations and script execution context.