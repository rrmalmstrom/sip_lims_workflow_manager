# Windows UNC Path Debug Instructions

## What This Is
This is a special debug version of the workflow manager that includes a potential fix for UNC network paths and comprehensive logging to verify the solution works on Windows.

## What You Need to Do

### Step 1: Run the Debug Script
1. **Download** the `run_debug.py` file to your workflow manager folder
2. **Open Command Prompt** in that folder
3. **Run the command**:
   ```cmd
   python run_debug.py
   ```

### Step 2: Test the Fix
1. **Select your workflow type** (SIP or SPS-CE) when prompted
2. **Drag and drop your project folder** when prompted
   - Use the same UNC path that was failing: `\\storage.jgi.lbl.gov\gentech\...`
3. **See if it works now** - this version includes a potential fix
   - If it works: Great! The fix is successful
   - If it still fails: The log will show us what's still wrong

### Step 3: Send the Log File
1. **Find the file** called `debug_log.txt` in the same folder
2. **Send this file** back to the developer
   - The file contains detailed technical information about what went wrong
   - No personal data is logged, only technical path processing details

## What the Debug Script Does
- **Logs every step** of path processing to `debug_log.txt`
- **Records all commands** run by the script (like `net use`)
- **Captures exact error details** when Docker fails
- **Shows what path** is actually being sent to Docker

## Important Notes
- ✅ **Safe to run** - this is just a diagnostic version
- ✅ **No changes made** - it only reads and logs information
- ✅ **Expected to fail** - we want it to fail so we can see why
- ✅ **Log file is safe** - contains only technical debugging info

## If You Get Stuck
- Make sure you're running from the correct folder (where run.py normally is)
- Make sure Python is installed and working
- The script should create `debug_log.txt` even if it fails
- Send whatever log file gets created, even if incomplete

## What Happens Next
The developer will analyze the log file to see:
- Whether your UNC path is being detected correctly
- If Windows drive mappings are being found
- What exact path Docker is receiving
- Where the conversion process is failing

This will help create a proper fix for the Windows UNC path issue.