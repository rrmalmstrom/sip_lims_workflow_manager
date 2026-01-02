# Enhanced Update Safety Features

## Overview

The SIP LIMS Workflow Manager now includes enhanced safety features to prevent accidental overwrites of newer local Docker images with older remote versions. This document describes the chronology uncertainty detection and user confirmation system.

## Problem Addressed

Previously, when the system couldn't determine whether a local or remote Docker image was newer, it would default to updating (potentially overwriting a newer local version with an older remote version). This could happen in scenarios like:

- No internet connection (can't check GitHub API)
- Git not available or repository corrupted
- GitHub API rate limiting
- Commits from different forks/repositories
- Network timeouts

## Solution: Chronology Uncertainty Detection

### New Update Detector Features

The [`UpdateDetector`](../src/update_detector.py) class now includes:

1. **Uncertainty Flags**: New fields in update check results:
   - `chronology_uncertain`: Boolean indicating if chronology could not be determined
   - `requires_user_confirmation`: Boolean indicating if user confirmation is needed
   - `warning`: User-friendly warning message about potential risks

2. **Enhanced Fallback Logic**: When both git ancestry and timestamp checks fail:
   - Sets uncertainty flags instead of blindly updating
   - Provides detailed warning messages
   - Requires explicit user confirmation

### Update Detection Hierarchy

The system uses a 3-layer approach to determine chronology:

1. **Git Ancestry Check** (Most Reliable)
   - Uses `git merge-base --is-ancestor` to check commit relationships
   - Handles linear history, branching, and merging scenarios
   - Returns definitive results when commits are in local git history

2. **Timestamp Comparison** (Fallback)
   - Compares commit timestamps via GitHub API
   - Used when git ancestry check fails
   - Less reliable due to rebasing, cherry-picking, etc.

3. **Uncertainty Detection** (Safety Net)
   - Triggered when both above methods fail
   - Sets uncertainty flags and requires user confirmation
   - Prevents automatic overwrites of potentially newer local versions

## User Experience

### Normal Update (No Uncertainty)

```bash
🔍 Checking for Docker image updates...
📦 Docker image update available - updating to latest version...
🧹 Removing old Docker image before update...
📥 Pulling Docker image for branch: main...
✅ Docker image updated successfully
```

### Uncertain Chronology (User Confirmation Required)

```bash
🔍 Checking for Docker image updates...

⚠️  **CHRONOLOGY WARNING**
   ⚠️  CHRONOLOGY UNCERTAIN: Cannot determine if local (a1b2c3d4...) or remote (f6e5d4c3...) is newer
   Local version might be newer than remote. Manual confirmation recommended before updating.

The system cannot determine if your local Docker image is newer or older than the remote version.
Proceeding with the update might overwrite a newer local version with an older remote version.

Do you want to proceed with the Docker image update? (y/N): 
```

### User Response Options

**If user cancels (types 'n' or presses Enter):**
```bash
❌ Docker image update cancelled by user
✅ Continuing with current local Docker image
```

**If user confirms (types 'y'):**
```bash
✅ User confirmed - proceeding with Docker image update...
🧹 Removing old Docker image before update...
📥 Pulling Docker image for branch: main...
✅ Docker image updated successfully
```

## Implementation Details

### Update Detector Changes

**New Result Fields:**
```python
{
    "update_available": bool,
    "local_sha": str,
    "remote_sha": str,
    "reason": str,
    "error": str,
    "chronology_uncertain": bool,        # NEW
    "requires_user_confirmation": bool,  # NEW
    "warning": str                       # NEW (when uncertain)
}
```

**Enhanced Fallback Logic:**
```python
# When chronology cannot be determined
result["update_available"] = True
result["chronology_uncertain"] = True
result["requires_user_confirmation"] = True
result["reason"] = "⚠️  CHRONOLOGY UNCERTAIN: Cannot determine if local (...) or remote (...) is newer"
result["warning"] = "Local version might be newer than remote. Manual confirmation recommended before updating."
result["error"] = "Could not determine commit chronology - git ancestry and timestamp checks both failed"
```

### Run Script Changes

Both [`run.mac.command`](../run.mac.command) and [`run.windows.bat`](../run.windows.bat) now include:

1. **Uncertainty Detection**: Parse JSON response for uncertainty flags
2. **User Prompting**: Display warning and prompt for confirmation
3. **Safe Defaults**: Default to "No" (cancel update) for safety
4. **Clear Messaging**: Explain risks and consequences to user

**Key Script Logic:**
```bash
if [ "$chronology_uncertain" = "true" ] && [ "$requires_confirmation" = "true" ]; then
    # Display warning and prompt user
    printf "Do you want to proceed with the Docker image update? (y/N): "
    read user_choice
    
    if [ "$user_choice" != "y" ] && [ "$user_choice" != "yes" ]; then
        echo "❌ Docker image update cancelled by user"
        echo "✅ Continuing with current local Docker image"
        return 0
    fi
fi
```

## Scenarios That Trigger Uncertainty

1. **No Internet Connection**
   - Git ancestry check may fail if commits not in local history
   - Timestamp check fails due to no GitHub API access

2. **Git Not Available**
   - Git command not found or repository corrupted
   - Both ancestry and timestamp checks fail

3. **GitHub API Issues**
   - Rate limiting, timeouts, or service unavailability
   - Timestamp comparison fails

4. **Different Repositories/Forks**
   - Local and remote commits from different repositories
   - Git ancestry check fails due to unrelated histories

5. **Network Timeouts**
   - Intermittent connectivity issues
   - API calls timeout or fail

## Testing

### Automated Tests

- **Unit Tests**: [`test_update_detector_uncertainty_warnings.py`](../tests/test_update_detector_uncertainty_warnings.py)
  - Tests uncertainty flag setting
  - Verifies warning messages
  - Checks all uncertainty scenarios

- **User Experience Tests**: [`test_user_experience_chronology_uncertainty.py`](../tests/test_user_experience_chronology_uncertainty.py)
  - Simulates complete user experience
  - Tests run script behavior
  - Validates user confirmation flow

- **Integration Tests**: Existing branch-aware tests continue to pass
  - Ensures backward compatibility
  - Verifies normal update flow unchanged

### Manual Testing

To test uncertainty scenarios manually:

```bash
# Simulate no internet (disconnect network)
./run.mac.command

# Simulate git issues (rename .git folder temporarily)
mv .git .git.backup
./run.mac.command
mv .git.backup .git
```

## Benefits

1. **Prevents Data Loss**: No more accidental overwrites of newer local versions
2. **User Control**: Users make informed decisions about uncertain updates
3. **Clear Communication**: Detailed warnings explain risks and consequences
4. **Safe Defaults**: System defaults to not updating when uncertain
5. **Backward Compatibility**: Normal update flow unchanged for certain scenarios

## Migration Notes

- **Existing Behavior**: Normal updates (when chronology is certain) work exactly as before
- **New Behavior**: Uncertain scenarios now prompt user instead of auto-updating
- **No Breaking Changes**: All existing functionality preserved
- **Enhanced Safety**: Additional protection against unintended overwrites

## Future Enhancements

Potential improvements for future versions:

1. **Local Git History Enhancement**: Better handling of shallow clones
2. **Offline Mode**: Cache previous update decisions for offline scenarios
3. **Configuration Options**: Allow users to set default behavior for uncertainty
4. **Detailed Logging**: Enhanced logging of update decisions and reasoning
5. **Recovery Tools**: Tools to help recover from accidental overwrites