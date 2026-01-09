# Specific Code Changes with File Paths, Line Numbers, and Exact Modifications

## Overview

This document provides exact line-by-line modifications required for the workflow generalization implementation with critical WORKFLOW_TYPE propagation fixes. Each change includes the specific file path, line number, current code, and replacement code.

## Critical WORKFLOW_TYPE Propagation Requirements

**Essential Components That Must Be Updated:**
1. **docker-compose.yml**: Add WORKFLOW_TYPE environment variable and workflow-aware script mounting
2. **scripts_updater.py**: Make workflow-aware with repository mapping
3. **Run scripts**: Pass WORKFLOW_TYPE to scripts_updater.py calls
4. **Script path resolution**: Use workflow-specific directories throughout

## File 1: [`run.mac.command`](run.mac.command)

### Change 1.1: Add Workflow Selection Menu
**Location**: After line 12 (after the header echo statement)
**Action**: INSERT new lines

**Insert after line 12:**
```bash
# === WORKFLOW SELECTION ===
echo ""
echo "🔬 Select Laboratory Workflow:"
echo "1) SIP Fractionation and Library Prep"
echo "2) SPS-CE Library Creation"
echo ""
printf "Enter your choice (1 or 2): "
read workflow_choice
workflow_choice=$(echo "$workflow_choice" | tr -d '\r\n' | xargs)

case $workflow_choice in
    1)
        export WORKFLOW_TYPE="sip"
        echo "✅ Selected: SIP Fractionation and Library Prep"
        ;;
    2)
        export WORKFLOW_TYPE="sps-ce"
        echo "✅ Selected: SPS-CE Library Creation"
        ;;
    *)
        echo "❌ ERROR: Invalid choice '$workflow_choice'. Please enter 1 or 2."
        echo "Exiting."
        exit 1
        ;;
esac
echo ""
```

### Change 1.2: Update Script Path Generation
**Location**: Line 232
**Current Code:**
```bash
local scripts_dir="$HOME/.sip_lims_workflow_manager/scripts"
```

**Replace with:**
```bash
local scripts_dir="$HOME/.sip_lims_workflow_manager/${WORKFLOW_TYPE}_scripts"
```

### Change 1.3: Update Environment Variable Export
**Location**: After line 239 (after export SCRIPTS_PATH)
**Action**: INSERT new line

**Insert after line 239:**
```bash
export WORKFLOW_TYPE
```

## File 2: [`run.windows.bat`](run.windows.bat)

### Change 2.1: Add Workflow Selection Menu
**Location**: After the initial header section
**Action**: INSERT new lines

**Insert after header:**
```batch
REM === WORKFLOW SELECTION ===
echo.
echo Select Laboratory Workflow:
echo 1) SIP Fractionation and Library Prep
echo 2) SPS-CE Library Creation
echo.
set /p workflow_choice="Enter your choice (1 or 2): "

if "%workflow_choice%"=="1" (
    set WORKFLOW_TYPE=sip
    echo Selected: SIP Fractionation and Library Prep
) else if "%workflow_choice%"=="2" (
    set WORKFLOW_TYPE=sps-ce
    echo Selected: SPS-CE Library Creation
) else (
    echo ERROR: Invalid choice. Please enter 1 or 2.
    echo Exiting.
    exit /b 1
)
echo.
```

### Change 2.2: Update Script Path Generation
**Location**: Find the line that sets script path (similar to line 232 in mac version)
**Current Code:**
```batch
set SCRIPT_PATH=%USERPROFILE%\.sip_lims_workflow_manager\scripts
```

**Replace with:**
```batch
set SCRIPT_PATH=%USERPROFILE%\.sip_lims_workflow_manager\%WORKFLOW_TYPE%_scripts
```

## File 3: [`templates/workflow.yml`](templates/workflow.yml)

### Change 3.1: Rename File
**Action**: RENAME file
**From**: `templates/workflow.yml`
**To**: `templates/sip_workflow.yml`

**Command:**
```bash
cd templates
mv workflow.yml sip_workflow.yml
```

### Change 3.2: Create New SPS-CE Template
**Action**: CREATE new file
**File**: `templates/sps_workflow.yml`

**Content:**
```yaml
workflow_name: "SPS Library Creation"
workflow_type: "sps-ce"
steps:
  - id: make_illumina_index_fa_files
    name: "1. Make Illumina Index and FA Files"
    script: "SPS_make_illumina_index_and_FA_files_NEW.py"

  - id: first_fa_analysis
    name: "2. First FA Output Analysis"
    script: "SPS_first_FA_output_analysis_NEW.py"

  - id: decision_second_attempt
    name: "Decision: Second Attempt Needed?"
    script: "decision_second_attempt.py"

  - id: rework_first_attempt
    name: "3. Rework First Attempt"
    script: "SPS_rework_first_attempt_NEW.py"

  - id: second_fa_analysis
    name: "4. Second FA Output Analysis"
    script: "SPS_second_FA_output_analysis_NEW.py"

  - id: conclude_fa_analysis
    name: "5. Conclude FA Analysis and Generate ESP Smear File"
    script: "SPS_conclude_FA_analysis_generate_ESP_smear_file.py"
```

## File 3: [`docker-compose.yml`](docker-compose.yml)

### Change 3.1: Add WORKFLOW_TYPE Environment Variable
**Location**: Line 30 (in environment section)
**Action**: INSERT new line

**Current environment section (lines 28-31):**
```yaml
environment:
  - APP_ENV=${APP_ENV:-production}
  - PROJECT_NAME=${PROJECT_NAME:-data}
```

**Replace with:**
```yaml
environment:
  - APP_ENV=${APP_ENV:-production}
  - PROJECT_NAME=${PROJECT_NAME:-data}
  - WORKFLOW_TYPE=${WORKFLOW_TYPE:-sip}
```

### Change 3.2: Update Script Path Mounting to be Workflow-Aware
**Location**: Line 21 (scripts volume mounting)
**Current Code:**
```yaml
- type: bind
  source: ${SCRIPTS_PATH:-~/.sip_lims_workflow_manager/scripts}
  target: /workflow-scripts
  bind:
    create_host_path: true
```

**Replace with:**
```yaml
- type: bind
  source: ${SCRIPTS_PATH:-~/.sip_lims_workflow_manager/${WORKFLOW_TYPE:-sip}_scripts}
  target: /workflow-scripts
  bind:
    create_host_path: true
```

## File 4: [`src/scripts_updater.py`](src/scripts_updater.py)

### Change 4.1: Update Class Constructor for Workflow Awareness
**Location**: Lines 29-34
**Current Code:**
```python
def __init__(self, repo_owner: str = "rrmalmstrom", scripts_repo_name: str = "sip_scripts_workflow_gui"):
    self.repo_owner = repo_owner
    self.scripts_repo_name = scripts_repo_name
    self.github_api_base = "https://api.github.com"
    self.scripts_repo_url = f"https://github.com/{repo_owner}/{scripts_repo_name}.git"
```

**Replace with:**
```python
def __init__(self, workflow_type: str = "sip", repo_owner: str = "rrmalmstrom"):
    self.workflow_type = workflow_type
    self.repo_owner = repo_owner
    self.github_api_base = "https://api.github.com"
    
    # Workflow-specific repository mapping
    self.repo_config = self._get_repository_config()
    self.scripts_repo_name = self.repo_config['repo_name']
    self.scripts_repo_url = self.repo_config['repo_url']

def _get_repository_config(self) -> dict:
    """Get repository configuration based on workflow type"""
    repositories = {
        'sip': {
            'repo_name': 'sip_scripts_workflow_gui',
            'repo_url': f'https://github.com/{self.repo_owner}/sip_scripts_workflow_gui.git'
        },
        'sps-ce': {
            'repo_name': 'SPS_library_creation_scripts',
            'repo_url': 'https://github.com/rrmalmstrom/SPS_library_creation_scripts.git'
        }
    }
    return repositories.get(self.workflow_type, repositories['sip'])
```

### Change 4.2: Update Command Line Interface
**Location**: Lines 175-184
**Action**: ADD workflow-type argument and update instantiation

**Add after line 179:**
```python
parser.add_argument("--workflow-type", default="sip", help="Workflow type (sip or sps-ce)")
```

**Update line 183:**
```python
# Current:
updater = ScriptsUpdater()

# Replace with:
updater = ScriptsUpdater(workflow_type=args.workflow_type)
```

## File 5: [`app.py`](app.py)

### Change 4.1: Template Source Selection
**Location**: Lines 733-740 (template copying logic)
**Current Code** (approximate):
```python
template_source = Path("templates/workflow.yml")
```

**Replace with:**
```python
# Get workflow type from environment variable
workflow_type = os.environ.get('WORKFLOW_TYPE', 'sip')
template_source = Path(f"templates/{workflow_type}_workflow.yml")

# Validate template exists
if not template_source.exists():
    st.error(f"❌ Template not found: {template_source}")
    available_templates = list(Path('templates').glob('*_workflow.yml'))
    st.error(f"Available templates: {[t.name for t in available_templates]}")
    return False
```

### Change 4.2: Add Template Validation Function
**Location**: After existing imports at top of file
**Action**: INSERT new function

**Insert after imports:**
```python
def validate_workflow_template(template_path: Path) -> bool:
    """Validate workflow template has required fields"""
    try:
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
        
        required_fields = ['workflow_name', 'steps']
        for field in required_fields:
            if field not in template_data:
                st.error(f"Template missing required field: {field}")
                return False
        
        # Validate steps structure
        if not isinstance(template_data['steps'], list):
            st.error("Template 'steps' must be a list")
            return False
            
        for i, step in enumerate(template_data['steps']):
            required_step_fields = ['id', 'name', 'script']
            for field in required_step_fields:
                if field not in step:
                    st.error(f"Step {i} missing required field: {field}")
                    return False
        
        return True
    except Exception as e:
        st.error(f"Error validating template: {e}")
        return False
```

### Change 4.3: Update Template Copying Logic
**Location**: Lines 888-894 (template handling in setup)
**Action**: MODIFY existing template copying to include validation

**Find the template copying section and modify:**
```python
# Validate template before copying
if not validate_workflow_template(template_source):
    st.error("❌ Template validation failed")
    return False

# Copy template to project (always named workflow.yml in project)
template_dest = project_path / "workflow.yml"
shutil.copy2(template_source, template_dest)
st.success(f"✅ Copied {workflow_type} workflow template to project")
```

### Change 4.4: Add Import for os module
**Location**: Top of file with other imports
**Action**: ADD import if not present

**Add to imports:**
```python
import os
```

## File 5: [`src/git_update_manager.py`](src/git_update_manager.py)

### Change 5.1: Add Repository Configuration
**Location**: After existing imports
**Action**: INSERT new configuration

**Insert after imports:**
```python
# Workflow repository configuration
WORKFLOW_REPOSITORIES = {
    'sip': {
        'local_path': Path.home() / '.sip_lims_workflow_manager' / 'sip_scripts',
        'remote_url': 'https://github.com/rrmalmstrom/sip_lims_scripts.git'  # Update with actual URL
    },
    'sps-ce': {
        'local_path': Path.home() / '.sip_lims_workflow_manager' / 'sps-ce_scripts',
        'remote_url': 'https://github.com/rrmalmstrom/SPS_library_creation_scripts.git'
    }
}

def get_repository_config(workflow_type: str) -> dict:
    """Get repository configuration for workflow type"""
    return WORKFLOW_REPOSITORIES.get(workflow_type, WORKFLOW_REPOSITORIES['sip'])
```

### Change 5.2: Update Repository Update Logic
**Location**: Find the main update function (varies by implementation)
**Action**: MODIFY to use dynamic repository configuration

**Modify existing update function:**
```python
def update_scripts_repository(workflow_type: str = None):
    """Update scripts repository based on workflow type"""
    if workflow_type is None:
        workflow_type = os.environ.get('WORKFLOW_TYPE', 'sip')
    
    repo_config = get_repository_config(workflow_type)
    local_path = repo_config['local_path']
    remote_url = repo_config['remote_url']
    
    # Use existing update logic with dynamic paths
    # ... (keep existing implementation but use local_path and remote_url)
```

## File 6: SPS-CE Scripts - Add Success Markers

### Change 6.1: [`SPS_make_illumina_index_and_FA_files_NEW.py`](SPS_make_illumina_index_and_FA_files_NEW.py)
**Location**: End of main() function, before final return/exit
**Action**: INSERT success marker code

**Insert before final return:**
```python
# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/SPS_make_illumina_index_and_FA_files_NEW.success', 'w') as f:
    f.write('Script completed successfully')
```

### Change 6.2: [`SPS_first_FA_output_analysis_NEW.py`](SPS_first_FA_output_analysis_NEW.py)
**Location**: End of main() function, before final return/exit
**Action**: INSERT success marker code

**Insert before final return:**
```python
# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/SPS_first_FA_output_analysis_NEW.success', 'w') as f:
    f.write('Script completed successfully')
```

### Change 6.3: [`SPS_rework_first_attempt_NEW.py`](SPS_rework_first_attempt_NEW.py)
**Location**: End of main() function, before final return/exit
**Action**: INSERT success marker code

**Insert before final return:**
```python
# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/SPS_rework_first_attempt_NEW.success', 'w') as f:
    f.write('Script completed successfully')
```

### Change 6.4: [`SPS_second_FA_output_analysis_NEW.py`](SPS_second_FA_output_analysis_NEW.py)
**Location**: End of main() function, before final return/exit
**Action**: INSERT success marker code

**Insert before final return:**
```python
# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/SPS_second_FA_output_analysis_NEW.success', 'w') as f:
    f.write('Script completed successfully')
```

## File 7: Create New Decision Script

### Change 7.1: Create [`decision_second_attempt.py`](decision_second_attempt.py)
**Location**: `/Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts/decision_second_attempt.py`
**Action**: CREATE new file

**Complete File Content:**
```python
#!/usr/bin/env python3
"""
Decision Script: Second Library Creation Attempt (SPS-CE)

Adapted from SIP decision_third_attempt.py for SPS-CE workflow.
Presents decision point and updates workflow state.
"""

import json
import sys
import os
from pathlib import Path

def debug_print(message, level="INFO"):
    """Print debug messages with clear formatting"""
    print(f"[DEBUG-{level}] {message}")

def main():
    """Main decision logic"""
    debug_print("=== SPS-CE DECISION SCRIPT STARTED ===", "START")
    debug_print(f"Current working directory: {os.getcwd()}")
    debug_print(f"Script path: {__file__}")
    debug_print(f"Python version: {sys.version}")
    
    try:
        print_decision_header()
        choice = get_user_choice()
        update_workflow_state(choice)
        print_completion_message(choice)
        debug_print("=== SPS-CE DECISION SCRIPT COMPLETED SUCCESSFULLY ===", "SUCCESS")
    except Exception as e:
        debug_print(f"=== SPS-CE DECISION SCRIPT FAILED: {e} ===", "ERROR")
        debug_print(f"Exception type: {type(e).__name__}", "ERROR")
        import traceback
        debug_print(f"Traceback: {traceback.format_exc()}", "ERROR")
        raise

def print_decision_header():
    """Display the decision prompt to the user"""
    debug_print("Displaying decision header to user")
    print("\n" + "="*60)
    print("🔄 SPS-CE WORKFLOW DECISION POINT")
    print("="*60)
    print("\n📊 You've completed the first library QC analysis.")
    print("\n❓ QUESTION: Do you want to run a second attempt at library creation?")
    print("\n📋 Your options:")
    print("   ✅ YES = Run second attempt (Steps 3-4: Rework + QC)")
    print("   ❌ NO  = Skip to conclusion (Step 5: Conclude analysis)")
    print("\n" + "-"*60)
    debug_print("Decision header displayed successfully")

def get_user_choice():
    """Get and validate user input"""
    debug_print("Starting user input collection")
    attempt_count = 0
    
    while True:
        attempt_count += 1
        debug_print(f"Input attempt #{attempt_count}")
        
        try:
            debug_print("Prompting user for input...")
            choice = input("\n🎯 Enter your choice (Y/N): ").strip().upper()
            debug_print(f"User entered: '{choice}'")
            
            if choice in ['Y', 'YES']:
                print(f"\n✅ You chose: YES - Running second attempt")
                debug_print("User choice validated: YES")
                return "yes"
            elif choice in ['N', 'NO']:
                print(f"\n✅ You chose: NO - Skipping to conclusion")
                debug_print("User choice validated: NO")
                return "no"
            else:
                debug_print(f"Invalid input received: '{choice}'")
                print("❌ Invalid input. Please enter Y (Yes) or N (No)")
                
        except KeyboardInterrupt:
            debug_print("User cancelled with Ctrl+C", "ERROR")
            print("\n\n⚠️  Decision cancelled by user")
            sys.exit(1)
        except EOFError:
            debug_print("EOF received (no input)", "ERROR")
            print("\n\n⚠️  No input received")
            sys.exit(1)
        except Exception as e:
            debug_print(f"Unexpected error during input: {e}", "ERROR")
            raise

def update_workflow_state(choice):
    """
    Update workflow_state.json based on user choice for SPS-CE workflow.
    """
    debug_print(f"Starting workflow state update with choice: {choice}")
    state_file = Path("workflow_state.json")
    debug_print(f"State file path: {state_file.absolute()}")
    
    # Load current state
    debug_print("Loading current workflow state...")
    if state_file.exists():
        debug_print("State file exists, loading...")
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            debug_print(f"Loaded state with {len(state)} entries")
            debug_print(f"Current state keys: {list(state.keys())}")
        except Exception as e:
            debug_print(f"Error loading state file: {e}", "ERROR")
            raise
    else:
        debug_print("State file does not exist, creating new state", "WARN")
        state = {}
    
    print(f"\n📝 Updating workflow state...")
    debug_print("Applying state changes based on user choice...")
    
    if choice == "yes":
        debug_print("Applying YES choice - enabling second attempt steps")
        # Enable second attempt steps
        state["rework_first_attempt"] = "pending"
        state["second_fa_analysis"] = "pending"
        print("   ✅ Enabled Step 3: Rework First Attempt")
        print("   ✅ Enabled Step 4: Second FA Output Analysis")
        debug_print("YES choice state changes applied")
        
    else:  # choice == "no"
        debug_print("Applying NO choice - skipping to conclusion")
        # Skip second attempt steps, go directly to conclusion
        state["rework_first_attempt"] = "skipped"
        state["second_fa_analysis"] = "skipped"
        state["conclude_fa_analysis"] = "pending"
        print("   ⏭️  Skipped Step 3: Rework First Attempt")
        print("   ⏭️  Skipped Step 4: Second FA Output Analysis")
        print("   ✅ Enabled Step 5: Conclude FA Analysis")
        debug_print("NO choice state changes applied")
    
    # Save updated state
    debug_print("Saving updated state to file...")
    debug_print(f"Final state keys: {list(state.keys())}")
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        debug_print("State file saved successfully")
    except Exception as e:
        debug_print(f"Error saving state file: {e}", "ERROR")
        raise
    
    print("   💾 Workflow state saved successfully")
    print("   🔄 Workflow manager will add this step to completion order automatically")
    debug_print("Workflow state update completed")

def create_success_marker():
    """Create success marker file (required by workflow manager)"""
    debug_print("Creating success marker...")
    status_dir = Path(".workflow_status")
    debug_print(f"Status directory path: {status_dir.absolute()}")
    
    try:
        status_dir.mkdir(exist_ok=True)
        debug_print(f"Status directory created/verified: {status_dir.exists()}")
        
        success_file = status_dir / "decision_second_attempt.success"
        debug_print(f"Success marker path: {success_file.absolute()}")
        
        success_file.touch()
        debug_print(f"Success marker created: {success_file.exists()}")
        
        print("   ✅ Success marker created")
        debug_print("Success marker creation completed")
    except Exception as e:
        debug_print(f"Error creating success marker: {e}", "ERROR")
        raise

def print_completion_message(choice):
    """Display completion message"""
    debug_print("Displaying completion message and creating success marker")
    create_success_marker()
    
    debug_print("Displaying final completion message to user")
    print("\n" + "="*60)
    print("🎉 SPS-CE DECISION COMPLETED")
    print("="*60)
    
    if choice == "yes":
        debug_print("Showing YES completion message")
        print("\n📋 Next steps:")
        print("   1️⃣  Step 3 will be available to run")
        print("   2️⃣  After Step 3, Step 4 will become available")
        print("   3️⃣  After Step 4, Step 5 will become available")
    else:
        debug_print("Showing NO completion message")
        print("\n📋 Next steps:")
        print("   1️⃣  Step 5 will be available to run immediately")
        print("   ⏭️  Steps 3-4 have been skipped")
    
    print(f"\n🔄 Return to the workflow manager to continue...")
    print("="*60 + "\n")
    debug_print("Completion message displayed")

if __name__ == "__main__":
    main()
```

## Summary of Changes

### Files Modified:
1. **`run.mac.command`** - 3 changes (workflow selection, script path, environment export)
2. **`run.windows.bat`** - 2 changes (workflow selection, script path)
3. **`templates/workflow.yml`** - 1 rename to `sip_workflow.yml`
4. **`templates/sps_workflow.yml`** - 1 new file creation
5. **`app.py`** - 4 changes (template selection, validation function, copying logic, import)
6. **`src/git_update_manager.py`** - 2 changes (repository config, update logic)

### Files Created:
1. **`decision_second_attempt.py`** - Complete new script for SPS-CE workflow

### Files Modified in SPS-CE Repository:
1. **`SPS_make_illumina_index_and_FA_files_NEW.py`** - Add success marker
2. **`SPS_first_FA_output_analysis_NEW.py`** - Add success marker  
3. **`SPS_rework_first_attempt_NEW.py`** - Add success marker
4. **`SPS_second_FA_output_analysis_NEW.py`** - Add success marker

### Total Changes:
- **13 specific code modifications** with exact line numbers
- **1 new file creation** (decision script)
- **1 file rename** (template)
- **4 success marker additions** in SPS-CE scripts

All changes maintain backward compatibility for existing SIP workflows while enabling the new SPS-CE workflow functionality.