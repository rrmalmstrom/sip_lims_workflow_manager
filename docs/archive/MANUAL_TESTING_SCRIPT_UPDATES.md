# Manual Testing Guide: Script Update Notifications

## Overview

This guide explains how to manually verify that the new script update notification system is working correctly in the browser.

## Prerequisites

1. **Scripts Directory**: Ensure you have a `scripts/` directory that is a Git repository
2. **Running App**: The SIP LIMS Workflow Manager should be running via `run.command` or `run.bat`
3. **Browser Access**: App should be accessible at `http://127.0.0.1:8501`

## Testing Scenarios

### Scenario 1: Verify Script Update Checking is Active

**Expected Behavior**: The app should check for script updates every 30 minutes automatically.

**Steps to Test**:
1. **Launch the app**: Run `./run.command` (macOS) or `run.bat` (Windows)
2. **Open browser**: Navigate to `http://127.0.0.1:8501`
3. **Check sidebar**: Look for script update notifications in the left sidebar
4. **Wait and observe**: The system will check for updates automatically

**What to Look For**:
- ✅ **No notification initially**: If scripts are up-to-date, you should see no script update notification
- ✅ **App loads normally**: The main app functionality should work as expected
- ✅ **No errors**: Check browser console (F12) for any JavaScript errors

### Scenario 2: Force Script Update Check

**Expected Behavior**: You should be able to manually trigger a script update check.

**Steps to Test**:
1. **Open browser developer tools**: Press F12 and go to Console tab
2. **Clear Streamlit cache**: In the browser, press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) to hard refresh
3. **Check for immediate update check**: The app should check for script updates on startup

**What to Look For**:
- ✅ **Cache refresh works**: Page reloads completely
- ✅ **Update check occurs**: System checks for script updates during startup
- ✅ **No errors in console**: No JavaScript errors related to script updates

### Scenario 3: Simulate Script Updates Available

**Expected Behavior**: When script updates are available, a notification should appear in the sidebar.

**Steps to Test** (if you have access to the scripts repository):
1. **Make scripts repository behind**: 
   - Go to the `scripts/` directory in terminal
   - Run `git reset --hard HEAD~1` to go back one commit (this simulates being behind)
2. **Refresh the app**: Wait up to 30 minutes or restart the app
3. **Check sidebar**: Look for script update notification

**What to Look For**:
- ✅ **Update notification appears**: Should see "🔄 Script Updates Available" in sidebar
- ✅ **Clear messaging**: "New workflow scripts available!" message
- ✅ **Action buttons**: "📥 Update Scripts" and "🔄 Check Now" buttons
- ✅ **Script Status section**: Always visible "📜 Script Status" section in sidebar
- ✅ **Detailed timestamp**: Shows exact date/time and relative time (e.g., "2024-09-24 14:30:15 (5 minutes ago)")
- ✅ **Current status**: Shows "✅ Up to date", "🔄 Updates available", or "❌ Error checking for updates"

### Scenario 4: Test Manual Update Check

**Expected Behavior**: The "🔄 Check Now" button should force an immediate update check.

**Steps to Test**:
1. **Locate the button**: If no updates are available, you won't see the notification
2. **Use browser developer tools**: You can test the function directly
3. **Check browser console**: Look for any network activity or errors

**Alternative Testing Method**:
1. **Modify the cache TTL**: Temporarily change the cache TTL in `app.py` from 1800 to 10 seconds
2. **Restart the app**: This will make updates check every 10 seconds
3. **Observe frequent checking**: You should see more frequent update checks

### Scenario 5: Test Script Update Process

**Expected Behavior**: The "📥 Update Scripts" button should update scripts and show feedback.

**Steps to Test** (if updates are available):
1. **Click "📥 Update Scripts"**: Should show a spinner with "Updating scripts..."
2. **Wait for completion**: Should show success or error message
3. **Check notification disappears**: After successful update, notification should disappear
4. **Verify scripts updated**: Check `scripts/` directory for latest commits

**What to Look For**:
- ✅ **Progress indicator**: Spinner appears during update
- ✅ **Success message**: "✅ Scripts updated successfully!" appears
- ✅ **Notification clears**: Update notification disappears after success
- ✅ **Page refreshes**: App automatically refreshes after successful update

## Troubleshooting Common Issues

### Issue 1: No Script Update Notifications Ever Appear

**Possible Causes**:
- Scripts directory doesn't exist
- Scripts directory is not a Git repository
- Network connectivity issues
- Git not installed or not in PATH

**How to Diagnose**:
1. **Check scripts directory**: Verify `scripts/` folder exists in app directory
2. **Check Git repository**: Run `cd scripts && git status` in terminal
3. **Check network**: Try `cd scripts && git fetch` manually
4. **Check browser console**: Look for error messages in F12 developer tools

### Issue 2: Update Notifications Appear But Updates Fail

**Possible Causes**:
- Git permission issues
- Merge conflicts in scripts repository
- Network connectivity during update
- Scripts repository in detached HEAD state

**How to Diagnose**:
1. **Check Git status**: Run `cd scripts && git status` to see repository state
2. **Try manual update**: Run `cd scripts && git pull` to see error messages
3. **Check permissions**: Ensure write permissions to scripts directory
4. **Check for conflicts**: Look for merge conflict markers in files

### Issue 3: Updates Check Too Frequently or Not Frequently Enough

**Possible Causes**:
- Cache TTL configuration
- Browser caching issues
- Streamlit cache not working properly

**How to Diagnose**:
1. **Check cache TTL**: Look at `@st.cache_data(ttl=1800)` in `app.py`
2. **Clear browser cache**: Hard refresh with `Ctrl+Shift+R`
3. **Restart app**: Close and restart the Streamlit application

## Advanced Testing

### Testing with Mock Git Repository

If you want to test without affecting real scripts:

1. **Create test repository**:
   ```bash
   mkdir test_scripts
   cd test_scripts
   git init
   echo "test script" > test.py
   git add test.py
   git commit -m "Initial commit"
   ```

2. **Modify app temporarily**: Change `scripts_dir` path in `check_for_script_updates()` function

3. **Test update scenarios**: Create commits, reset HEAD, etc. to simulate different states

### Testing Error Scenarios

1. **Network timeout**: Disconnect internet during update check
2. **Permission errors**: Remove write permissions from scripts directory
3. **Invalid Git repository**: Delete `.git` folder from scripts directory
4. **Merge conflicts**: Create conflicting changes in scripts repository

## Expected User Experience

### Normal Operation
- **Seamless integration**: Script updates work without interrupting workflow
- **Always-visible status**: "📜 Script Status" section always shows current script status
- **Detailed timestamps**: Exact date/time with relative time for last check
- **Clear status indicators**: Visual icons show current status (✅ up to date, 🔄 updates available, ❌ error)
- **Clear notifications**: Users immediately see when updates are available
- **One-click updates**: Updates apply instantly with clear feedback
- **Manual check always available**: "🔄 Check for Script Updates" button always visible
- **No restart required**: App continues working after script updates

### Error Handling
- **Graceful degradation**: App continues working even if script updates fail
- **Clear error messages**: Users understand what went wrong and how to fix it
- **Recovery options**: Users can retry updates or seek help

## Verification Checklist

- [ ] App starts successfully with script update checking enabled
- [ ] "📜 Script Status" section always visible in sidebar
- [ ] Last checked timestamp shows exact date/time and relative time
- [ ] Status indicator shows current state (✅/🔄/❌)
- [ ] "🔄 Check for Script Updates" button always available
- [ ] No script update notification when scripts are up-to-date
- [ ] Script update notification appears when updates are available
- [ ] "📥 Update Scripts" button works and shows progress
- [ ] "🔄 Check Now" button forces immediate update check
- [ ] Success messages appear after successful updates
- [ ] Error messages are clear and helpful when updates fail
- [ ] App continues working normally regardless of script update status
- [ ] Browser console shows no JavaScript errors related to script updates
- [ ] Update notifications disappear after successful updates
- [ ] Timestamp updates after manual checks

## Performance Verification

- [ ] App startup time is not significantly affected
- [ ] UI remains responsive during update checks
- [ ] Update checks don't cause noticeable delays
- [ ] Memory usage remains stable with script update checking
- [ ] Network usage is reasonable (not excessive Git operations)

This manual testing guide ensures that the script update notification system works correctly and provides a good user experience.