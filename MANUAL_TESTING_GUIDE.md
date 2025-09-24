# Manual Testing Guide: UpdateManager Integration

## Overview
This guide will help you manually test the UpdateManager integration in the Streamlit app to verify that update notifications are working correctly.

## Step 0: Choose Your Testing Method

### Option A: Use the Project's Virtual Environment (Recommended)
If you want to use the project's setup scripts:
1. **Run setup first** (only needed once):
   ```bash
   ./setup.command
   ```
2. **Then use the run script**:
   ```bash
   ./run.command
   ```

### Option B: Direct Testing (Simpler for Testing)
If you just want to test the UpdateManager integration quickly:
1. **Install dependencies directly**:
   ```bash
   pip install streamlit requests
   ```
2. **Run the app directly**:
   ```bash
   streamlit run app.py
   ```

**For this testing guide, we'll use Option B (Direct Testing) as it's simpler.**

## Step 1: Stop Any Currently Running App Instances

### Method 1: Terminal-Based Shutdown
If you have the app running in a terminal:
1. **Go to the terminal window** where Streamlit is running
2. **Press `Ctrl+C`** (Windows/Linux) or **`Cmd+C`** (Mac)
3. **Wait for confirmation** - you should see:
   ```
   Stopping...
   ^C
   ```
4. **Verify the command prompt returns** (e.g., `$` or `>`)

### Method 2: Close Browser and Check Processes
1. **Close all browser tabs** showing the app (usually `http://localhost:8501`)
2. **Check for running Streamlit processes**:
   
   **On Mac/Linux:**
   ```bash
   ps aux | grep streamlit
   ```
   
   **On Windows:**
   ```cmd
   tasklist | findstr streamlit
   ```

3. **Kill any remaining processes** if found:
   
   **On Mac/Linux:**
   ```bash
   pkill -f streamlit
   ```
   
   **On Windows:**
   ```cmd
   taskkill /f /im python.exe
   ```

### Method 3: Check Port Availability
Test if port 8501 is free:
```bash
# On Mac/Linux:
lsof -i :8501

# On Windows:
netstat -an | findstr :8501
```
If you see any output, the port is still in use.

## Step 2: Verify Prerequisites

### Check Dependencies
Make sure all required packages are installed:
```bash
pip install -r requirements.txt
```

### Verify Configuration Files
1. **Check that `config/version.json` exists**:
   ```bash
   cat config/version.json
   ```
   Should show:
   ```json
   {
     "version": "0.9.0"
   }
   ```

2. **If the file doesn't exist, create it**:
   ```bash
   mkdir -p config
   echo '{"version": "0.9.0"}' > config/version.json
   ```

## Step 3: Start the Updated App

### Quick Setup (if not done already)
```bash
# Install required packages
pip install streamlit requests

# Verify installation
python -c "import streamlit; print('✅ Streamlit installed')"
```

### Launch Command
```bash
streamlit run app.py
```

### Expected Startup Behavior
1. **Terminal output** should show:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   Network URL: http://192.168.x.x:8501
   ```

2. **Browser should automatically open** to `http://localhost:8501`
   - If it doesn't open automatically, manually navigate to `http://localhost:8501`

3. **Wait for the app to fully load** (may take 10-30 seconds on first run)

## Step 4: Verify Update Notification

### What to Look For
In the **left sidebar**, at the **top of the Controls section**, you should see:

```
🔄 Update Available
Update Available: v1.0.0
Current version: v0.9.0
[📥 Download Update]
```

### If You See the Update Notification ✅
**SUCCESS!** The integration is working correctly.

### If You DON'T See the Update Notification ❌
Check the following:

1. **Refresh the browser page** (F5 or Ctrl+R)
2. **Check the terminal** for any error messages
3. **Verify internet connection** - the app needs to reach Google Drive
4. **Check the version file**:
   ```bash
   cat config/version.json
   ```
   Should show version "0.9.0" (lower than remote version "1.0.0")

## Step 5: Test Download Button Functionality

### Click the Download Button
1. **Click the "📥 Download Update" button** in the sidebar
2. **Expected behavior**:
   - Your default browser should open a new tab/window
   - The Google Drive download should start automatically
   - In the Streamlit app, you should see: "✅ Download started in your browser!"

### If Download Doesn't Work
1. **Check browser popup blockers** - may be blocking the new window
2. **Try the direct URL manually**:
   ```
   https://drive.google.com/uc?id=1pRsUbaKoieuInH67ghExSZw7p2I64-FQ&export=download
   ```

## Step 6: Test Different Scenarios

### Scenario A: No Update Available
1. **Stop the app** (`Ctrl+C`)
2. **Edit the version file**:
   ```bash
   echo '{"version": "1.1.0"}' > config/version.json
   ```
3. **Restart the app**:
   ```bash
   streamlit run app.py
   ```
4. **Expected result**: No update notification should appear

### Scenario B: Reset to Show Updates
1. **Stop the app** (`Ctrl+C`)
2. **Reset the version file**:
   ```bash
   echo '{"version": "0.9.0"}' > config/version.json
   ```
3. **Restart the app**:
   ```bash
   streamlit run app.py
   ```
4. **Expected result**: Update notification should reappear

## Step 7: Troubleshooting Common Issues

### Issue: "Address already in use"
**Solution**: Another instance is still running
```bash
# Kill all Streamlit processes
pkill -f streamlit
# Wait 30 seconds, then try again
streamlit run app.py
```

### Issue: No update notification appears
**Checklist**:
- [ ] Internet connection working?
- [ ] `config/version.json` exists with version "0.9.0"?
- [ ] Any error messages in terminal?
- [ ] Browser cache cleared? (Ctrl+Shift+R)

### Issue: Download button doesn't work
**Checklist**:
- [ ] Popup blocker disabled?
- [ ] Default browser set correctly?
- [ ] Can you access the URL manually?

## Step 8: Verify Integration Success

### Success Criteria ✅
- [ ] App starts without errors
- [ ] Update notification appears in sidebar
- [ ] Shows "Update Available: v1.0.0"
- [ ] Shows "Current version: v0.9.0"
- [ ] Download button opens browser to Google Drive
- [ ] Success message appears after clicking download

### Quick Verification Command
Test the UpdateManager directly:
```bash
python -c "
from src.update_manager import UpdateManager
manager = UpdateManager()
manager.remote_version_url = 'https://drive.google.com/uc?id=1pRsUbaKoieuInH67ghExSZw7p2I64-FQ&export=download'
result = manager.check_for_updates()
print(f'✅ Local: {result[\"local_version\"]}, Remote: {result[\"remote_version\"]}, Update Available: {result[\"update_available\"]}')
"
```

Expected output:
```
✅ Local: 0.9.0, Remote: 1.0.0, Update Available: True
```

## Summary
1. **Stop** any running instances (`Ctrl+C`)
2. **Verify** config files exist
3. **Start** the app (`streamlit run app.py`)
4. **Look** for update notification in sidebar
5. **Test** download button functionality
6. **Verify** success criteria are met

If all steps pass, the UpdateManager integration is working correctly!