# Enhanced Update Safety Features

## Overview

The SIP LIMS Workflow Manager includes comprehensive safety features to prevent dangerous synchronization issues and accidental overwrites. This document describes the fatal sync error detection, chronology uncertainty detection, and user confirmation systems.

## Problems Addressed

### 1. Fatal Sync Errors (Critical Safety Issue)

The most critical safety issue occurs when the repository has been updated but the Docker image hasn't been rebuilt, creating a dangerous mismatch between code and container environment. This can lead to:

- Running outdated Docker images with newer repository code
- Inconsistent behavior between development and production environments
- Silent failures due to missing dependencies or configuration changes
- Data corruption from incompatible code/environment combinations

### 2. Chronology Uncertainty (Update Safety Issue)

When the system couldn't determine whether a local or remote Docker image was newer, it would default to updating (potentially overwriting a newer local version with an older remote version). This could happen in scenarios like:

- No internet connection (can't check GitHub API)
- Git not available or repository corrupted
- GitHub API rate limiting
- Commits from different forks/repositories
- Network timeouts

## Solutions

### 1. Fatal Sync Error Detection (Primary Safety System)

The [`FatalSyncChecker`](../src/fatal_sync_checker.py) class provides critical safety validation by comparing repository commits with Docker image commits to detect dangerous synchronization mismatches.

**Key Features:**
- **Repository Commit Detection**: Gets current repository HEAD commit SHA
- **Docker Image Commit Detection**: Extracts commit SHA from Docker image labels
- **Sync Validation**: Compares repository and Docker image commits for mismatches
- **Fatal Error Prevention**: Blocks execution when dangerous sync errors are detected
- **Clear Error Messages**: Provides actionable guidance for resolving sync issues

**Integration Points:**
- Integrated at the beginning of [`production_auto_update()`](../run.mac.command) in both Mac and Windows scripts
- Runs before any Docker operations to prevent dangerous state execution
- Provides immediate feedback with clear resolution instructions

### 2. Chronology Uncertainty Detection (Secondary Safety System)

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

### Fatal Sync Error Detection (Critical Safety Check)

When a fatal sync error is detected, the system immediately blocks execution:

```bash
🔍 Checking for fatal sync errors...

❌ **FATAL SYNC ERROR DETECTED**
   Repository commit: a1b2c3d4e5f6789012345678901234567890abcd
   Docker image commit: f6e5d4c3b2a1098765432109876543210987fedc
   
   The repository has been updated but the Docker image has not been rebuilt.
   Running with this mismatch could cause serious issues.

   REQUIRED ACTIONS:
   1. Build a new Docker image: ./build/build_image_from_lock_files.sh
   2. Push the new image: ./build/push_image_to_github.sh
   3. Or pull the latest image: docker pull ghcr.io/rrmalmstrom/sip_lims_workflow_manager:main

❌ Execution blocked for safety. Please resolve the sync error and try again.
```

### Normal Update (No Uncertainty)

```bash
🔍 Checking for fatal sync errors...
✅ No fatal sync errors detected

🔍 Checking for Docker image updates...
📦 Docker image update available - updating to latest version...
🧹 Removing old Docker image before update...
📥 Pulling Docker image for branch: main...
✅ Docker image updated successfully
```

### Uncertain Chronology (User Confirmation Required)

```bash
🔍 Checking for fatal sync errors...
✅ No fatal sync errors detected

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

### Fatal Sync Checker Implementation

**Core Class:** [`FatalSyncChecker`](../src/fatal_sync_checker.py)

```python
class FatalSyncChecker:
    def check_fatal_sync_error(self, docker_tag: str) -> dict:
        """
        Check for fatal sync errors between repository and Docker image.
        
        Returns:
            dict: {
                "fatal_sync_error": bool,
                "repo_commit": str,
                "docker_commit": str,
                "error_message": str,
                "resolution_steps": list
            }
        """
```

**Key Methods:**
- `get_repository_commit_sha()`: Gets current repository HEAD commit
- `get_docker_image_commit_sha(tag)`: Extracts commit SHA from Docker image labels
- `check_fatal_sync_error(tag)`: Compares commits and detects mismatches

### Enhanced Update Detector Changes

**New Result Fields for Docker Image Updates:**
```python
{
    "update_available": bool,
    "local_digest": str,                 # NEW - Docker image digest
    "remote_digest": str,                # NEW - Remote image digest
    "local_sha": str,
    "remote_sha": str,
    "repo_sha": str,                     # NEW - Current repository commit
    "reason": str,
    "error": str,
    "sync_warning": str,                 # NEW - Fatal sync warnings
    "chronology_uncertain": bool,        # Existing
    "requires_user_confirmation": bool,  # Existing
    "warning": str                       # Existing (when uncertain)
}
```

**New Digest-Based Detection:**
```python
def check_docker_image_update(self, tag: str, branch: str = None) -> dict:
    """
    Enhanced Docker image update detection using digest comparison.
    
    Features:
    - Digest-based comparison for reliable image matching
    - Handles missing local images gracefully
    - Integrates with fatal sync error detection
    - Provides detailed error reporting
    """
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

#### Fatal Sync Error Tests
- **Unit Tests**: [`test_fatal_sync_checker.py`](../tests/test_fatal_sync_checker.py)
  - Tests fatal sync error detection logic
  - Validates repository and Docker image commit extraction
  - Verifies error message formatting and resolution steps
  - Tests edge cases (missing images, invalid commits, etc.)

#### Docker Update Detection Tests
- **Digest-Based Tests**: Multiple test files validate the enhanced Docker update detection:
  - [`test_comprehensive_validation.py`](../tests/test_comprehensive_validation.py) - End-to-end validation
  - [`test_digest_fix.py`](../tests/test_digest_fix.py) - Digest comparison validation
  - [`test_no_local_image.py`](../tests/test_no_local_image.py) - Missing local image scenarios
  - [`test_scenario_3_different_images.py`](../tests/test_scenario_3_different_images.py) - Image mismatch detection

#### Chronology Uncertainty Tests
- **Unit Tests**: [`test_update_detector_uncertainty_warnings.py`](../tests/test_update_detector_uncertainty_warnings.py)
  - Tests uncertainty flag setting
  - Verifies warning messages
  - Checks all uncertainty scenarios

- **User Experience Tests**: [`test_user_experience_chronology_uncertainty.py`](../tests/test_user_experience_chronology_uncertainty.py)
  - Simulates complete user experience
  - Tests run script behavior
  - Validates user confirmation flow

#### Integration Tests
- **Branch-Aware Tests**: Existing branch-aware tests continue to pass
  - Ensures backward compatibility
  - Verifies normal update flow unchanged
  - Tests cross-platform script consistency

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

1. **Critical Safety Protection**: Fatal sync error detection prevents dangerous repository/Docker mismatches
2. **Prevents Data Loss**: No more accidental overwrites of newer local versions
3. **Enhanced Reliability**: Digest-based Docker image comparison provides accurate update detection
4. **User Control**: Users make informed decisions about uncertain updates
5. **Clear Communication**: Detailed warnings explain risks and consequences
6. **Safe Defaults**: System defaults to not updating when uncertain
7. **Cross-Platform Consistency**: Both Mac and Windows scripts provide identical safety features
8. **Backward Compatibility**: Normal update flow unchanged for certain scenarios

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