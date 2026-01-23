# 🪟 **Windows Smart Sync Testing - SIMPLIFIED**

## 🎯 **What You Need to Do**

### **Step 1: Run the Test**
```cmd
# Navigate to your workflow manager directory
cd C:\path\to\sip_lims_workflow_manager

# Run with debug logging enabled
python run_debug.py --debug
```

### **Step 2: Follow the Prompts**
1. **Select workflow type**: Choose 1 (SIP) or 2 (SPS-CE)
2. **Enter your project path**: Drag and drop your network drive project folder (Z:\your\project)

### **Step 3: Let it Run**
- Watch for Smart Sync messages in the console
- Let the workflow complete (or stop it with Ctrl+C)

## 📁 **WHERE TO FIND ALL DEBUG FILES**

### **🎯 LOCATION 1: `debug_output\` folder (MAIN)**
In your workflow manager directory:

```
C:\path\to\sip_lims_workflow_manager\
└── debug_output\                    ← 🎯 LOOK HERE FIRST!
    ├── run_debug.log               ← Basic execution log
    ├── smart_sync_debug.log        ← Detailed Smart Sync log (JSON)
    └── smart_sync_debug_export_*.json ← Analysis reports (if created)
```

### **🎯 LOCATION 2: Your project directory**
In your network drive project folder:

```
Z:\your\project\
└── .workflow_logs\                  ← 🎯 LOOK HERE TOO!
    └── workflow_debug.log          ← Workflow step execution log
```

### **🎯 LOCATION 3: Windows staging area (if Smart Sync activated)**
If Smart Sync was used:

```
C:\temp\sip_workflow\your_project_name\
└── .sync_log.json                  ← 🎯 SYNC OPERATION DETAILS
```

### **Quick Check Commands**
```cmd
# Check main debug files
dir debug_output

# Check project workflow logs
dir Z:\your\project\.workflow_logs

# Check staging area (replace your_project_name)
dir C:\temp\sip_workflow\your_project_name
```

## 📤 **SEND ALL THESE FILES**

**Collect ALL debug files:**
```cmd
# Create a folder for results
mkdir test_results

# 1. Copy main debug files (ALWAYS EXIST)
copy debug_output\run_debug.log test_results\
copy debug_output\smart_sync_debug.log test_results\

# 2. Copy analysis reports (if they exist)
copy debug_output\smart_sync_debug_export_*.json test_results\ 2>nul

# 3. Copy workflow logs (replace Z:\your\project with your actual path)
copy Z:\your\project\.workflow_logs\workflow_debug.log test_results\ 2>nul

# 4. Copy sync logs (replace your_project_name with your actual project folder name)
copy C:\temp\sip_workflow\your_project_name\.sync_log.json test_results\ 2>nul

# 5. Add system info
systeminfo > test_results\system_info.txt
docker version > test_results\docker_info.txt 2>nul
```

**Then send the entire `test_results\` folder with ALL files.**

## ✅ **Success Indicators**

**Console should show:**
- ✅ "Smart Sync: Windows network drive detected"
- ✅ "Smart Sync: Creating local staging"
- ✅ "Smart Sync: Initial sync completed"

**Files should exist:**
- ✅ `debug_output\run_debug.log` (always created)
- ✅ `debug_output\smart_sync_debug.log` (created with --debug flag)

## 🚨 **If Something Goes Wrong**

**No `debug_output` folder?**
- Make sure you used the `--debug` flag
- Check you're in the right directory

**Empty log files?**
- The test might have failed early
- Send whatever files exist - they still contain useful info

**Can't find your project?**
- Use the full network path like `Z:\full\path\to\your\project`
- Make sure the network drive is accessible

---

## 🎯 **TL;DR - Just Do This:**

1. `cd C:\path\to\sip_lims_workflow_manager`
2. `python run_debug.py --debug`
3. Follow prompts, enter your Z:\ project path
4. After it finishes, collect ALL debug files:
   ```cmd
   mkdir test_results
   copy debug_output\*.* test_results\
   copy Z:\your\project\.workflow_logs\*.* test_results\ 2>nul
   copy C:\temp\sip_workflow\your_project_name\*.json test_results\ 2>nul
   systeminfo > test_results\system_info.txt
   ```
5. Send the entire `test_results\` folder

**That's it!** 🎉