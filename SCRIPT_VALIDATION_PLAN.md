# Script Update Validation Plan

## 🎯 **Objective**
Validate that updated setup and run scripts work correctly without breaking existing functionality.

## 📋 **Pre-Update Backup Strategy**

### 1. Create Backup Copies
```bash
# Create backups before making changes
cp setup.command setup.command.backup
cp run.command run.command.backup
cp setup.bat setup.bat.backup
cp run.bat run.bat.backup
```

### 2. Document Current Working State
- ✅ Current macOS scripts are working
- ✅ App launches successfully with `./run.command`
- ✅ Unified update system works in GUI
- ✅ Requirements.txt dependencies are stable

## 🧪 **Validation Tests**

### Phase 1: Windows Script Validation (Safe to test - already updated)

#### Test 1: Hash Verification Logic
```cmd
# Test the new simplified hash checking
cd /path/to/project
run.bat
```
**Expected Result**: Should launch normally if dependencies haven't changed

#### Test 2: Dependency Change Detection
```cmd
# Temporarily modify requirements.txt to test detection
echo "# test comment" >> requirements.txt
run.bat
```
**Expected Result**: Should detect change and prompt to run setup.bat
```cmd
# Restore requirements.txt
git checkout requirements.txt
```

#### Test 3: Setup Script Functionality
```cmd
# Test setup process (in a test environment)
setup.bat
```
**Expected Result**: Should create .venv and install dependencies correctly

### Phase 2: macOS Script Validation (Before updating)

#### Test 1: Current Functionality Baseline
```bash
# Verify current script works
./run.command
```
**Expected Result**: App should launch normally

#### Test 2: Verify Obsolete Arguments Don't Break Anything
```bash
# Check if the --scripts-update-available argument causes issues
# (This tests what happens with the current obsolete code)
cd scripts
git fetch
# Check if any updates are detected
git status -uno
```

#### Test 3: Test Updated Script (After creating backup)
```bash
# After updating run.command, test it
./run.command
```
**Expected Result**: Should launch exactly the same as before

## 🔍 **Specific Validation Points**

### Critical Functionality Checks

1. **App Launch**
   - [ ] Streamlit starts on http://127.0.0.1:8501
   - [ ] No error messages in terminal
   - [ ] GUI loads completely

2. **Update System**
   - [ ] "🔄 Manual Check for Updates" button works
   - [ ] Update notifications appear when available
   - [ ] Script updates work through GUI

3. **Project Loading**
   - [ ] Can browse and load existing projects
   - [ ] Workflow steps display correctly
   - [ ] Terminal functionality works

4. **Dependencies**
   - [ ] All packages from requirements.txt load correctly
   - [ ] No import errors
   - [ ] Virtual environment activates properly

### Error Scenarios to Test

1. **Missing Setup**
   - Delete `.venv/install_receipt.txt`
   - Run script → Should prompt to run setup

2. **Changed Dependencies**
   - Modify `requirements.txt`
   - Run script → Should detect change and prompt for setup

3. **Missing Virtual Environment**
   - Rename `.venv` folder
   - Run script → Should fail gracefully with clear message

## 🚨 **Rollback Plan**

If any issues are found:

### Immediate Rollback
```bash
# Restore from backups
cp setup.command.backup setup.command
cp run.command.backup run.command
cp setup.bat.backup setup.bat
cp run.bat.backup run.bat
```

### Verification After Rollback
```bash
# Test that rollback works
./run.command  # Should work exactly as before
```

## 📊 **Success Criteria**

### ✅ **Must Pass All These Tests**

1. **Functional Equivalence**
   - Updated scripts launch app identically to current scripts
   - No new error messages or warnings
   - All existing functionality preserved

2. **Improved Reliability**
   - Windows hash checking is more reliable
   - No obsolete command-line arguments
   - Consistent behavior between macOS and Windows

3. **Update System Integration**
   - GUI update system works correctly
   - No conflicts with script update logic
   - Manual update cache clearing functions properly

### ⚠️ **Warning Signs to Watch For**

- App fails to start
- New error messages in terminal
- Update notifications stop working
- Hash verification fails incorrectly
- Virtual environment issues

## 🔧 **Testing Environment Setup**

### Option 1: Safe Testing (Recommended)
```bash
# Create a test copy of the entire project
cp -r /path/to/sip_lims_workflow_manager /path/to/sip_lims_workflow_manager_test
cd /path/to/sip_lims_workflow_manager_test
# Test all changes here first
```

### Option 2: In-Place Testing (With Backups)
```bash
# Create backups first, then test in original location
# This is what we've already done for Windows scripts
```

## 📝 **Test Results Documentation**

### Windows Scripts (Already Updated)
- [ ] setup.bat tested and working
- [ ] run.bat tested and working
- [ ] Hash verification improved
- [ ] Obsolete script update logic removed

### macOS Scripts (Pending Update)
- [ ] Current run.command baseline established
- [ ] Updated run.command tested
- [ ] Functionality comparison completed
- [ ] No regressions detected

## 🎉 **Final Validation**

Before considering the update complete:

1. **Cross-Platform Consistency**
   - Both Windows and macOS scripts behave identically
   - Same error messages and success flows
   - Consistent dependency checking

2. **Integration Testing**
   - Full workflow execution works
   - Update system functions properly
   - No conflicts between old and new logic

3. **User Experience**
   - Scripts are easier to understand and maintain
   - Error messages are clearer
   - Setup process is more reliable

## 🚀 **Deployment Recommendation**

1. **Phase 1**: Keep Windows updates (already done) ✅
2. **Phase 2**: Test macOS updates in safe environment
3. **Phase 3**: Apply macOS updates after validation
4. **Phase 4**: Document changes and update user guides

This staged approach ensures we can validate each change independently and rollback quickly if needed.