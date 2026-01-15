# Windows Testing Instructions for Smart Sync Implementation

## 🎯 **Overview**

This document provides step-by-step instructions for testing the Smart Sync Layer implementation on actual Windows systems with network drives. The Smart Sync system automatically detects Windows + network drive scenarios and creates local staging to bypass Docker Desktop's network drive limitations.

## 🚀 **Step 1: Getting the Smart Sync Code**

You currently have the main branch. The Smart Sync implementation is on the `feature/smart-sync-layer` branch. Here's how to get it:

```cmd
# Navigate to your workflow manager installation directory
cd C:\path\to\your\sip_lims_workflow_manager

# Fetch the new feature branch from remote
git fetch origin feature/smart-sync-layer

# Switch to the Smart Sync feature branch
git checkout feature/smart-sync-layer
```

### **Step 1.1: Verify Debug Components**

After updating, verify these new files exist:

```cmd
# Check for debug system files
dir src\debug_logger.py
dir debug_validation_windows_simulation.py
dir debug_log_analyzer.py

# If any are missing, you may need to switch branches or pull again
```

## 📁 **Step 2: Understanding Debug Output Organization**

All debug output is organized in a dedicated directory structure:

### **Debug File Locations**

```
your_project_directory\
├── .debug_output\                    # ← Main debug directory (auto-created)
│   ├── smart_sync_debug.log         # ← Primary debug log (JSON format)
│   ├── smart_sync_debug_export_*.json # ← Analysis reports
│   └── analysis_reports\             # ← Generated analysis files
├── .workflow_logs\                   # ← Workflow execution logs
│   └── workflow_debug.log           # ← Step-by-step workflow debugging
└── C:\temp\sip_workflow\project_name\  # ← Smart Sync staging area
    └── .sync_log.json               # ← Detailed sync operation logs
```

### **What Each Log File Contains**

1. **`.debug_output\smart_sync_debug.log`**
   - **Format**: Structured JSON entries with timestamps
   - **Contains**: All Smart Sync operations, performance metrics, error details
   - **Created**: When `SMART_SYNC_DEBUG=true` environment variable is set

2. **`.workflow_logs\workflow_debug.log`**
   - **Format**: Plain text with timestamps
   - **Contains**: Workflow step execution, rollback operations, success/failure tracking
   - **Created**: During workflow execution (always created)

3. **`C:\temp\sip_workflow\project_name\.sync_log.json`**
   - **Format**: JSON with sync statistics
   - **Contains**: File transfer details, sync performance, operation counts
   - **Created**: During Smart Sync operations in the local staging area

4. **`.debug_output\smart_sync_debug_export_*.json`**
   - **Format**: Comprehensive analysis report
   - **Contains**: Session summaries, performance analysis, recommendations
   - **Created**: When running the debug log analyzer tool

## 🧪 **Step 3: Understanding Debug Logging**

Debug logging will be enabled automatically using the `--debug` flag when running the workflow manager. This provides comprehensive logging of all Smart Sync operations without requiring manual environment variable setup.

**Debug logging automatically:**
- Creates `.debug_output\smart_sync_debug.log` in your project directory
- Tracks all Smart Sync operations with timestamps and performance metrics
- Provides detailed error information if issues occur
- Can be turned off by simply running without the `--debug` flag

## 🗂️ **Step 4: Navigate to Your Project on Network Drive**


### **Step 4.1: Verify Your Project Setup**

```cmd
# Navigate to your actual project on the network drive (replace Z: with your network drive)
cd Z:\path\to\your\real\project

# Verify you have a workflow file (workflow.yml, sip_workflow.yml, or sps_workflow.yml)
dir *.yml

# Note the full path to your project - you'll need this
echo %CD%
```

## 🏃 **Step 5: Run Smart Sync Test**

### **Step 5.1: Execute Test from Workflow Manager Directory**

**CRITICAL**: Run the workflow manager from its installation directory, NOT from your project directory.

```cmd
# Navigate to your workflow manager installation directory
cd C:\path\to\sip_lims_workflow_manager

# Run the workflow manager with debug logging enabled
python run.py --debug
```

### **Step 5.2: Follow the Interactive Prompts**

The workflow manager will guide you through:

1. **Workflow Type Selection**:
   ```
   🧪 Select workflow type:
   1) SIP (Stable Isotope Probing)
   2) SPS-CE (Single Particle Sorting - Cell Enrichment)
   Enter choice (1 or 2):
   ```

2. **Project Folder Selection**:
   ```
   📁 Project Folder Selection
   Please drag and drop your project folder here, then press Enter:
   Project path:
   ```
   **Enter your network drive project path**: `Z:\path\to\your\real\project`
   ```

### **Step 5.3: What to Look For During Execution**

You should see console output like:

```
🔍 Smart Sync: Windows network drive detected (Z:)
📁 Smart Sync: Creating local staging at C:\temp\sip_workflow\your_project_name
📥 Smart Sync: Initial sync starting...
📥 Smart Sync: Initial sync completed (X files copied)
🐳 Launching Docker container...
🔄 Smart Sync: Pre-step sync (network → local)
📤 Smart Sync: Post-step sync (local → network)
✅ Smart Sync: Final sync completed
🧹 Smart Sync: Cleanup completed
```

### **Step 5.4: Verify Debug Files Were Created**

After running, check that debug files were created in your project directory:

```cmd
# Navigate back to your project directory
cd Z:\path\to\your\real\project

# Check that debug output directory was created in your project
dir .debug_output

# Verify main debug log exists and has content
dir .debug_output\smart_sync_debug.log
type .debug_output\smart_sync_debug.log | more

# Check local staging area was created (replace your_project_name with your actual project folder name)
dir C:\temp\sip_workflow\your_project_name

# Verify sync log in staging area
dir C:\temp\sip_workflow\your_project_name\.sync_log.json
```

## 📊 **Step 6: Analyze Debug Results**

### **Step 6.1: Quick Analysis**

```cmd
# Run quick analysis on the debug log from your workflow manager directory
cd C:\path\to\sip_lims_workflow_manager
python debug_log_analyzer.py Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log --summary-only
```

**Expected Output:**
```
============================================================
🔍 SMART SYNC DEBUG LOG ANALYSIS SUMMARY
============================================================
📁 Log File: Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log
📊 Total Entries: XX
🔄 Total Sessions: 1

📈 OVERVIEW:
  • Operations: XX
  • Errors: 0
  • Sync Success Rate: 100.0%
  • Average Sync Duration: X.XXXs
============================================================
```

### **Step 6.2: Detailed Analysis**

```cmd
# Generate detailed analysis report
python debug_log_analyzer.py Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log --format txt --output test_results.txt

# View the report
type test_results.txt | more

# Generate JSON analysis for sharing
python debug_log_analyzer.py Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log --format json --output detailed_analysis.json
```

## ✅ **Step 7: Verify Success Criteria**

### **Must Pass Checks:**

1. **Smart Sync Detection**:
   ```cmd
   # Look for this in the console output or debug log
   findstr "Smart Sync.*detected" Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log
   ```

2. **Local Staging Created**:
   ```cmd
   # Verify staging directory exists (replace your_project_name)
   dir C:\temp\sip_workflow\your_project_name
   ```

3. **Files Synchronized**:
   ```cmd
   # Compare network and local staging (replace paths with your actual paths)
   dir Z:\path\to\your\real\project\data
   dir C:\temp\sip_workflow\your_project_name\data
   ```

4. **Docker Used Local Path**:
   ```cmd
   # Check Docker logs for mount points (should show C:\temp\, not Z:\)
   docker logs sip_workflow_manager 2>&1 | findstr "temp"
   ```

5. **Final Sync Completed**:
   ```cmd
   # Look for final sync messages
   findstr "Final sync completed" Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log
   ```

## 🚨 **Step 8: Troubleshooting Common Issues**

### **Issue: Smart Sync Not Detected**

**Symptoms**: No Smart Sync messages, workflow runs directly on network drive

**Troubleshooting**:
```cmd
# Check platform detection
python -c "import platform; print('Platform:', platform.system())"

# Verify project is on network drive
cd Z:\path\to\your\real\project
echo %CD%

# Check debug log for detection details
findstr "detection" .debug_output\smart_sync_debug.log
```

### **Issue: Permission Errors**

**Symptoms**: "Access denied" or "Permission denied" errors

**Solutions**:
1. Run Command Prompt as Administrator
2. Check network drive permissions:
   ```cmd
   icacls Z:\path\to\your\real\project
   ```
3. Verify Docker Desktop has access to C:\ drive

### **Issue: Debug Files Not Created**

**Symptoms**: No `.debug_output` directory or empty log files

**Check**:
```cmd
# Verify environment variables are set
echo %SMART_SYNC_DEBUG%
echo %SMART_SYNC_DEBUG_LEVEL%

# Re-set if needed
set SMART_SYNC_DEBUG=true
set SMART_SYNC_DEBUG_LEVEL=DEBUG
```

### **Issue: Sync Operations Fail**

**Symptoms**: Sync timeout or failure messages

**Troubleshooting**:
```cmd
# Check network connectivity
ping your-network-server

# Verify disk space
dir C:\temp

# Check for file locks (if you have Sysinternals tools)
handle.exe Z:\path\to\your\real\project
```

## 📤 **Step 9: Collecting Results for Analysis**

### **Files to Collect and Share**

```cmd
# Create results directory
mkdir debug_results

# 1. Main debug log
copy Z:\path\to\your\real\project\.debug_output\smart_sync_debug.log debug_results\

# 2. Analysis reports
copy test_results.txt debug_results\
copy detailed_analysis.json debug_results\

# 3. Workflow logs
copy Z:\path\to\your\real\project\.workflow_logs\workflow_debug.log debug_results\

# 4. Sync details (replace your_project_name)
copy C:\temp\sip_workflow\your_project_name\.sync_log.json debug_results\

# 5. System information
systeminfo > debug_results\system_info.txt
docker version > debug_results\docker_info.txt
```

### **Create Summary Report**

```cmd
# Create a summary of your test
echo Windows Smart Sync Test Results > debug_results\test_summary.txt
echo ================================ >> debug_results\test_summary.txt
echo. >> debug_results\test_summary.txt
echo Test Date: %DATE% %TIME% >> debug_results\test_summary.txt
echo Windows Version: >> debug_results\test_summary.txt
systeminfo | findstr "OS Name" >> debug_results\test_summary.txt
systeminfo | findstr "OS Version" >> debug_results\test_summary.txt
echo. >> debug_results\test_summary.txt
echo Network Drive Project: Z:\path\to\your\real\project >> debug_results\test_summary.txt
echo Workflow Manager: C:\path\to\sip_lims_workflow_manager >> debug_results\test_summary.txt
echo. >> debug_results\test_summary.txt
echo Test Results: >> debug_results\test_summary.txt
echo - Smart Sync Detected: [YES/NO] >> debug_results\test_summary.txt
echo - Local Staging Created: [YES/NO] >> debug_results\test_summary.txt
echo - Sync Operations Successful: [YES/NO] >> debug_results\test_summary.txt
echo - Docker Integration Working: [YES/NO] >> debug_results\test_summary.txt
echo - Final Cleanup Completed: [YES/NO] >> debug_results\test_summary.txt
```

## 🎯 **Expected Success Indicators**

### **Console Output Should Show**:
- ✅ Smart Sync detection for network drive
- ✅ Local staging directory creation
- ✅ Initial sync completion
- ✅ Docker container launch with local paths
- ✅ Pre/post-step sync operations
- ✅ Final sync and cleanup

### **Debug Log Should Contain**:
- ✅ JSON entries with structured operation data
- ✅ Performance timing information
- ✅ Success confirmations for all sync operations
- ✅ No ERROR level entries (warnings are OK)

### **File System Should Show**:
- ✅ `.debug_output\` directory in project
- ✅ `C:\temp\sip_workflow\project_name\` staging area
- ✅ Synchronized files in both locations
- ✅ Cleanup of staging area after completion

## 🔑 **Key Understanding: How run.py Works**

**IMPORTANT**: The workflow manager (`run.py`) is designed to:

1. **Run from its installation directory** (`C:\path\to\sip_lims_workflow_manager`)
2. **Prompt you to select your project folder** (which can be on a network drive like `Z:\`)
3. **Automatically detect if Smart Sync is needed** based on the project path you provide
4. **Create local staging and sync** if Windows + network drive is detected
5. **Launch Docker with the appropriate path** (local staging or original path)

This comprehensive testing will validate that Smart Sync works correctly on your Windows system and provide detailed debugging information for any issues encountered.