# 02 - Developer Marker File System Design

## Overview
Design for a file-based system to distinguish between developer and production environments, enabling different behaviors for script repository management and user prompts.

## Marker File Specification

### Location
- **Path**: `config/developer.marker`
- **Full Path**: `sip_lims_workflow_manager/config/developer.marker`

### File Properties
- **Type**: Plain text file (optional content)
- **Size**: Can be empty or contain developer information
- **Purpose**: Presence indicates developer environment, absence indicates production

### Content Format (Optional)
```
# Developer Environment Marker
# Created: 2025-01-22
# Developer: [Developer Name]
# Purpose: Enables development mode features
```

## Mode Detection Logic

### Bash Implementation (macOS/Linux)
```bash
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}
```

### Batch Implementation (Windows)
```batch
:detect_mode
if exist "config\developer.marker" (
    set MODE=developer
) else (
    set MODE=production
)
goto :eof
```

## Behavior Differences by Mode

### Developer Mode (marker exists)
- **Setup Script**: Prompts user for offline vs online mode
- **Run Script**: Prompts user to choose between dev/prod scripts
- **Script Repositories**: Can access both development and production scripts
- **Updates**: Optional - user chooses whether to check for updates

### Production Mode (no marker)
- **Setup Script**: Automatically connects to remotes and updates
- **Run Script**: Automatically uses production scripts
- **Script Repositories**: Only production scripts available
- **Updates**: Automatic - always checks and applies updates

## Implementation Requirements

### Directory Creation
- Setup script must create `config/` directory if it doesn't exist
- Use `mkdir -p config` (bash) or `if not exist "config" mkdir config` (batch)

### Error Handling
- Handle missing config directory gracefully
- Provide clear error messages if marker file cannot be read
- Fallback to production mode if detection fails

## Test Specifications (TDD)

### Test Cases
```bash
# Test 1: Developer mode detection
test_developer_marker_exists() {
    # Given: config/developer.marker exists
    # When: detect_mode() is called
    # Then: should return "developer"
}

# Test 2: Production mode detection  
test_production_mode_no_marker() {
    # Given: config/developer.marker does not exist
    # When: detect_mode() is called
    # Then: should return "production"
}

# Test 3: Missing config directory
test_missing_config_directory() {
    # Given: config/ directory does not exist
    # When: detect_mode() is called
    # Then: should return "production" (safe default)
}

# Test 4: Marker file ignored by git
test_marker_file_ignored() {
    # Given: config/developer.marker exists
    # When: git status is checked
    # Then: file should not appear in untracked files
}
```

### Test Implementation Strategy
1. Create temporary test directories
2. Test with and without marker file
3. Verify mode detection returns correct values
4. Test cross-platform compatibility (bash/batch)

## Integration Points

### Setup Script Integration
- Call `detect_mode()` early in setup process
- Use result to determine repository setup behavior
- Create config directory before any marker file operations

### Run Script Integration  
- Call `detect_mode()` before script path selection
- Use result to determine user prompting vs automatic behavior
- Pass mode information to application if needed

### Git Integration
- Marker file must be added to `.gitignore`
- Prevents accidental distribution of developer markers
- Ensures clean production deployments

## Security Considerations

### File Permissions
- Marker file should have standard read permissions
- No special permissions required
- Safe to create/delete by user

### Content Security
- File content is optional and not parsed for logic
- No executable content or scripts
- Safe for version control exclusion

## Migration Strategy

### Phase 1: Add Detection Logic
- Add mode detection functions to setup/run scripts
- Default to production mode if marker not found
- No behavior changes yet

### Phase 2: Implement Mode-Specific Behavior
- Add developer prompts and choices
- Maintain production mode automation
- Test both modes thoroughly

### Phase 3: Documentation and Training
- Update user documentation
- Create developer setup instructions
- Provide marker file creation guidance

## Benefits

### For Developers
- ✅ Can choose script sources per session
- ✅ Can work offline when needed
- ✅ Clear distinction from production environment
- ✅ Easy to enable/disable developer features

### For Production Users
- ✅ No changes to current workflow
- ✅ Automatic updates and script management
- ✅ No confusing prompts or choices
- ✅ Reliable, consistent behavior

### For Maintenance
- ✅ Simple file-based detection
- ✅ No complex configuration parsing
- ✅ Easy to test and debug
- ✅ Cross-platform compatibility