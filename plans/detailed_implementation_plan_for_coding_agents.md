# Detailed Implementation Plan: SIP LIMS Workflow Manager Generalization

## Executive Summary

This document provides comprehensive implementation instructions for coding agents to generalize the SIP LIMS workflow manager to support multiple laboratory processes (SIP and SPS-CE workflows) while maintaining full backward compatibility.

**Key Implementation Strategy**: Use workflow selection in run scripts, environment-driven template selection, and universal Docker image with workflow-specific script repositories.

## Implementation Overview

### Development Strategy
- **Branch-based Development**: Create development branches for both repositories
- **TDD Approach**: Test-Driven Development with comprehensive automated testing
- **Manual Validation Phase**: User validation before committing changes
- **Incremental Rollout**: Phased implementation with rollback capability

### Repository Structure
- **Main Repo**: `sip_lims_workflow_manager` (keep name unchanged)
- **SIP Scripts**: `~/.sip_lims_workflow_manager/sip_scripts` 
- **SPS-CE Scripts**: `~/.sip_lims_workflow_manager/sps-ce_scripts` (already cloned)

## Phase 1: Core Infrastructure Changes

### 1.1 Create Development Branches

**Workflow Manager Repository:**
```bash
cd /Users/RRMalmstrom/Desktop/sip_lims_workflow_manager
git checkout -b feature/workflow-generalization
git push -u origin feature/workflow-generalization
```

**SPS-CE Scripts Repository:**
```bash
cd /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts
git checkout -b feature/workflow-manager-integration
git push -u origin feature/workflow-manager-integration
```

### 1.2 Modify Run Scripts for Workflow Selection

**File: [`run.mac.command`](run.mac.command)**

**Location to Modify**: After branch detection but before mode detection (around line 35-40)

**Add Workflow Selection Menu:**
```bash
# Add after branch detection but before mode detection
echo ""
echo "Select Laboratory Workflow:"
echo "1) SIP Fractionation and Library Prep"
echo "2) SPS-CE Library Creation"
echo ""
read -p "Enter your choice (1 or 2): " workflow_choice

case $workflow_choice in
    1)
        export WORKFLOW_TYPE="sip"
        echo "Selected: SIP Fractionation and Library Prep"
        ;;
    2)
        export WORKFLOW_TYPE="sps-ce"
        echo "Selected: SPS-CE Library Creation"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
```

**Critical Script Path Modifications:**

**1. Production Auto-Update Function (Line 232):**
```bash
# Current line 232:
local scripts_dir="$HOME/.sip_lims_workflow_manager/scripts"

# Replace with:
local scripts_dir="$HOME/.sip_lims_workflow_manager/${WORKFLOW_TYPE}_scripts"
```

**2. Scripts Updater Calls (Lines 192, 207, 235):**
```bash
# Current calls:
python3 src/scripts_updater.py --check-scripts --scripts-dir "$scripts_dir" --branch "$branch"
python3 src/scripts_updater.py --update-scripts --scripts-dir "$scripts_dir" --branch "$branch"

# Replace with:
python3 src/scripts_updater.py --check-scripts --scripts-dir "$scripts_dir" --branch "$branch" --workflow-type "$WORKFLOW_TYPE"
python3 src/scripts_updater.py --update-scripts --scripts-dir "$scripts_dir" --branch "$branch" --workflow-type "$WORKFLOW_TYPE"
```

**File: [`run.windows.bat`](run.windows.bat)**

**Location to Modify**: After branch detection (around line 51) but before container management

**Add Workflow Selection Logic:**
```batch
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
    echo Invalid choice. Exiting.
    exit /b 1
)
```

**Critical Script Path Modifications:**

**1. Production Auto-Update Function (Line 271):**
```batch
REM Current line 271:
set "SCRIPTS_DIR=%USERPROFILE%\.sip_lims_workflow_manager\scripts"

REM Replace with:
set "SCRIPTS_DIR=%USERPROFILE%\.sip_lims_workflow_manager\%WORKFLOW_TYPE%_scripts"
```

**2. Scripts Updater Calls (Lines 240, 247, 274):**
```batch
REM Current calls:
python3 src/scripts_updater.py --check-scripts --scripts-dir "%SCRIPTS_DIR_ARG%" --branch "%BRANCH_ARG%"
python3 src/scripts_updater.py --update-scripts --scripts-dir "%SCRIPTS_DIR_ARG%" --branch "%BRANCH_ARG%"

REM Replace with:
python3 src/scripts_updater.py --check-scripts --scripts-dir "%SCRIPTS_DIR_ARG%" --branch "%BRANCH_ARG%" --workflow-type "%WORKFLOW_TYPE%"
python3 src/scripts_updater.py --update-scripts --scripts-dir "%SCRIPTS_DIR_ARG%" --branch "%BRANCH_ARG%" --workflow-type "%WORKFLOW_TYPE%"
```

### 1.3 Create Workflow Templates

**File: [`templates/sip_workflow.yml`](templates/sip_workflow.yml)**

**Action**: Rename existing [`templates/workflow.yml`](templates/workflow.yml) to [`templates/sip_workflow.yml`](templates/sip_workflow.yml)

```bash
cd templates
mv workflow.yml sip_workflow.yml
```

**File: [`templates/sps_workflow.yml`](templates/sps_workflow.yml)**

**Create New SPS-CE Template:**
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

### 1.4 Modify Template Copying Logic

**File: [`app.py`](app.py)**

**Locations to Modify:**
- Lines 733-740: Template copying in project initialization
- Lines 888-894: Template handling in setup
- Lines 932-936: Template processing
- Lines 985-988: Template validation

**Key Changes:**

**1. Template Source Selection (around line 735):**
```python
# Current logic:
template_source = Path("templates/workflow.yml")

# Replace with:
workflow_type = os.environ.get('WORKFLOW_TYPE', 'sip')
template_source = Path(f"templates/{workflow_type}_workflow.yml")

# Validate template exists
if not template_source.exists():
    st.error(f"Template not found: {template_source}")
    st.error(f"Available templates: {list(Path('templates').glob('*_workflow.yml'))}")
    return False
```

**2. Template Destination (keep unchanged):**
```python
# Always copy to project/workflow.yml regardless of source
template_dest = project_path / "workflow.yml"
```

**3. Add Template Validation:**
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

### 1.5 Update Git Update Manager

**File: [`src/git_update_manager.py`](src/git_update_manager.py)**

**Add Repository URL Mapping:**
```python
# Add to class or module level
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

**Update Repository Update Logic:**
```python
def update_scripts_repository(workflow_type: str = None):
    """Update scripts repository based on workflow type"""
    if workflow_type is None:
        workflow_type = os.environ.get('WORKFLOW_TYPE', 'sip')
    
    repo_config = get_repository_config(workflow_type)
    local_path = repo_config['local_path']
    remote_url = repo_config['remote_url']
    
    # Existing update logic using local_path and remote_url
    # ... (keep existing implementation but use dynamic paths)
```

### 1.6 Update Docker Compose Configuration

**File: [`docker-compose.yml`](docker-compose.yml)**

**Critical WORKFLOW_TYPE Propagation Fixes:**

**1. Add WORKFLOW_TYPE Environment Variable (Line 30):**
```yaml
# Current environment section (lines 28-31):
environment:
  - APP_ENV=${APP_ENV:-production}
  - PROJECT_NAME=${PROJECT_NAME:-data}

# Replace with:
environment:
  - APP_ENV=${APP_ENV:-production}
  - PROJECT_NAME=${PROJECT_NAME:-data}
  - WORKFLOW_TYPE=${WORKFLOW_TYPE:-sip}
```

**2. Update Script Path Mounting to be Workflow-Aware (Line 21):**
```yaml
# Current script volume mounting:
- type: bind
  source: ${SCRIPTS_PATH:-~/.sip_lims_workflow_manager/scripts}
  target: /workflow-scripts
  bind:
    create_host_path: true

# Replace with workflow-specific path:
- type: bind
  source: ${SCRIPTS_PATH:-~/.sip_lims_workflow_manager/${WORKFLOW_TYPE:-sip}_scripts}
  target: /workflow-scripts
  bind:
    create_host_path: true
```

### 1.7 Make Scripts Updater Workflow-Aware

**File: [`src/scripts_updater.py`](src/scripts_updater.py)**

**Add Workflow Repository Mapping:**

**1. Update Class Constructor (Lines 29-34):**
```python
# Current constructor:
def __init__(self, repo_owner: str = "rrmalmstrom", scripts_repo_name: str = "sip_scripts_workflow_gui"):
    self.repo_owner = repo_owner
    self.scripts_repo_name = scripts_repo_name
    self.github_api_base = "https://api.github.com"
    self.scripts_repo_url = f"https://github.com/{repo_owner}/{scripts_repo_name}.git"

# Replace with workflow-aware constructor:
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

**2. Update Command Line Interface (Lines 170-184):**
```python
# Add workflow-type argument:
parser.add_argument("--workflow-type", default="sip", help="Workflow type (sip or sps-ce)")

# Update ScriptsUpdater instantiation:
updater = ScriptsUpdater(workflow_type=args.workflow_type)
```

## Phase 2: SPS-CE Script Repository Updates

### 2.1 Add Success Markers to SPS-CE Scripts

**Critical Requirement**: All SPS-CE scripts need success markers for workflow manager integration. Based on analysis of existing SIP scripts, there are three distinct success marker implementation patterns.

**Scripts Requiring Success Markers:**
1. `SPS_make_illumina_index_and_FA_files_NEW.py`
2. `SPS_first_FA_output_analysis_NEW.py`
3. `SPS_rework_first_attempt_NEW.py`
4. `SPS_second_FA_output_analysis_NEW.py`
5. `decision_second_attempt.py` (new script)

### 2.1.1 Success Marker Implementation Patterns

**Pattern 1: Simple Success Marker (for most scripts)**
```python
# Add at the end of main() function or script execution
from pathlib import Path

# Create success marker to indicate script completed successfully
status_dir = Path.cwd() / ".workflow_status"
status_dir.mkdir(exist_ok=True)
success_file = status_dir / "{script_filename_without_extension}.success"
success_file.touch()
```

**Pattern 2: Robust Success Marker with Error Handling (recommended)**
```python
# Add at the end of main() function, before final return/exit
import datetime
from pathlib import Path

# SUCCESS MARKER: Create success marker file to indicate script completed successfully
script_name = Path(__file__).stem  # Use just the filename without extension
status_dir = Path(".workflow_status")
status_dir.mkdir(exist_ok=True)

# Remove any existing success file (for re-runs)
success_file = status_dir / f"{script_name}.success"
if success_file.exists():
    success_file.unlink()

# Create success marker file
try:
    with open(success_file, "w") as f:
        f.write(f"SUCCESS: {script_name} completed at {datetime.datetime.now()}")
    print(f"✓ Step {script_name} completed successfully")
except Exception as e:
    print(f"✗ Failed to create success marker: {e}")
    sys.exit(1)
```

**Pattern 3: Decision Script Success Marker (for decision scripts)**
```python
# Add as separate function and call from main completion logic
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
```

### 2.1.2 Detailed Script Modification Instructions

**Script 1: `SPS_make_illumina_index_and_FA_files_NEW.py`**
- **Location**: End of main() function or script execution
- **Pattern**: Use Pattern 2 (Robust Success Marker)
- **Success File**: `.workflow_status/SPS_make_illumina_index_and_FA_files_NEW.success`
- **Implementation**:
  ```python
  # Add at the very end of the script, after all processing is complete
  import datetime
  import sys
  from pathlib import Path
  
  # SUCCESS MARKER: Create success marker file to indicate script completed successfully
  script_name = Path(__file__).stem
  status_dir = Path(".workflow_status")
  status_dir.mkdir(exist_ok=True)
  
  success_file = status_dir / f"{script_name}.success"
  if success_file.exists():
      success_file.unlink()
  
  try:
      with open(success_file, "w") as f:
          f.write(f"SUCCESS: {script_name} completed at {datetime.datetime.now()}")
      print(f"✓ Step {script_name} completed successfully")
  except Exception as e:
      print(f"✗ Failed to create success marker: {e}")
      sys.exit(1)
  ```

**Script 2: `SPS_first_FA_output_analysis_NEW.py`**
- **Location**: End of main() function, after all file processing
- **Pattern**: Use Pattern 2 (Robust Success Marker)
- **Success File**: `.workflow_status/SPS_first_FA_output_analysis_NEW.success`
- **Special Considerations**: Ensure success marker is created only after all CSV files are processed and plots are generated
- **Implementation**: Same as Script 1, but ensure placement after all file I/O operations

**Script 3: `SPS_rework_first_attempt_NEW.py`**
- **Location**: End of main() function or script execution
- **Pattern**: Use Pattern 2 (Robust Success Marker)
- **Success File**: `.workflow_status/SPS_rework_first_attempt_NEW.success`
- **Implementation**: Same as Script 1

**Script 4: `SPS_second_FA_output_analysis_NEW.py`**
- **Location**: End of main() function, after all analysis is complete
- **Pattern**: Use Pattern 2 (Robust Success Marker)
- **Success File**: `.workflow_status/SPS_second_FA_output_analysis_NEW.success`
- **Implementation**: Same as Script 1

**Script 5: `decision_second_attempt.py` (New Script)**
- **Location**: Called from print_completion_message() function
- **Pattern**: Use Pattern 3 (Decision Script Success Marker)
- **Success File**: `.workflow_status/decision_second_attempt.success`
- **Implementation**: Create as separate function and integrate with completion logic

### 2.1.3 Success Marker Validation Requirements

**For All Scripts:**
1. **File Location**: Must be in `.workflow_status/` directory relative to project root
2. **File Naming**: Must match exact script filename (without .py extension) + `.success`
3. **File Content**: Should contain success message with timestamp
4. **Error Handling**: Must handle file creation errors gracefully
5. **Re-run Safety**: Must remove existing success files before creating new ones
6. **Path Handling**: Use `Path(__file__).stem` for consistent filename extraction

**Validation Checklist:**
- [ ] Success marker directory created with `exist_ok=True`
- [ ] Success file named correctly (script_name.success)
- [ ] Existing success files removed before creation
- [ ] Error handling for file creation failures
- [ ] Success confirmation printed to console
- [ ] Timestamp included in success file content

### 2.1.4 Testing Success Marker Implementation

**Unit Tests for Success Markers:**
```python
def test_success_marker_creation(self, temp_project_dir):
    """Test that success markers are created correctly"""
    # Run script
    result = subprocess.run([sys.executable, script_path],
                          cwd=temp_project_dir, capture_output=True)
    
    # Verify success marker exists
    success_file = temp_project_dir / ".workflow_status" / f"{script_name}.success"
    assert success_file.exists(), f"Success marker not created: {success_file}"
    
    # Verify success marker content
    content = success_file.read_text()
    assert "SUCCESS:" in content
    assert script_name in content
    assert "completed at" in content

def test_success_marker_rerun_safety(self, temp_project_dir):
    """Test that success markers are properly replaced on re-runs"""
    # Create existing success marker
    status_dir = temp_project_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    success_file = status_dir / f"{script_name}.success"
    success_file.write_text("OLD SUCCESS MARKER")
    
    # Run script
    subprocess.run([sys.executable, script_path], cwd=temp_project_dir)
    
    # Verify success marker was replaced
    content = success_file.read_text()
    assert "OLD SUCCESS MARKER" not in content
    assert "SUCCESS:" in content
```

**Specific Success Marker Files:**
- `SPS_make_illumina_index_and_FA_files_NEW.py` → `.workflow_status/SPS_make_illumina_index_and_FA_files_NEW.success`
- `SPS_first_FA_output_analysis_NEW.py` → `.workflow_status/SPS_first_FA_output_analysis_NEW.success`
- `SPS_rework_first_attempt_NEW.py` → `.workflow_status/SPS_rework_first_attempt_NEW.success`
- `SPS_second_FA_output_analysis_NEW.py` → `.workflow_status/SPS_second_FA_output_analysis_NEW.success`
- `decision_second_attempt.py` → `.workflow_status/decision_second_attempt.success`

### 2.2 External Repository Modification Workflow

**Repository**: `https://github.com/rrmalmstrom/SPS_library_creation_scripts.git`
**Local Path**: `/Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts`

### 2.2.1 Development Branch Strategy

**Create Feature Branch for Success Marker Integration:**
```bash
cd /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts
git checkout -b feature/workflow-manager-integration
git push -u origin feature/workflow-manager-integration
```

### 2.2.2 Script Modification Process

**Step 1: Backup Current Scripts**
```bash
# Create backup directory
mkdir -p backup_original_scripts
cp *.py backup_original_scripts/
git add backup_original_scripts/
git commit -m "Backup: Original scripts before workflow manager integration"
```

**Step 2: Apply Success Marker Modifications**
- Modify each script according to the detailed patterns above
- Test each script individually after modification
- Commit changes incrementally for easy rollback

**Step 3: Validation and Testing**
```bash
# Test each modified script
python SPS_make_illumina_index_and_FA_files_NEW.py --test-mode
python SPS_first_FA_output_analysis_NEW.py --test-mode
# ... etc for each script

# Verify success markers are created
ls -la .workflow_status/
```

### 2.2.3 Integration Testing Strategy

**Local Testing Before Repository Push:**
1. **Individual Script Testing**: Test each modified script in isolation
2. **Success Marker Validation**: Verify correct success marker creation
3. **Workflow Integration Testing**: Test with workflow manager
4. **Regression Testing**: Ensure original functionality unchanged

**Testing Commands:**
```bash
# Test success marker creation
cd /path/to/test/project
python /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts/SPS_make_illumina_index_and_FA_files_NEW.py
ls .workflow_status/SPS_make_illumina_index_and_FA_files_NEW.success

# Test workflow manager integration
cd /Users/RRMalmstrom/Desktop/sip_lims_workflow_manager
./run.mac.command
# Select SPS-CE workflow and test first script execution
```

### 2.2.4 Repository Update and Deployment

**Commit and Push Changes:**
```bash
cd /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts
git add .
git commit -m "Add workflow manager success markers to SPS-CE scripts

- Add success marker implementation to all SPS-CE scripts
- Use robust error handling pattern from SIP scripts
- Ensure compatibility with workflow manager completion detection
- Maintain backward compatibility with standalone script execution"

git push origin feature/workflow-manager-integration
```

**Merge to Main After Validation:**
```bash
# After successful testing and validation
git checkout main
git merge feature/workflow-manager-integration
git push origin main
```

### 2.2.5 Rollback Strategy

**If Issues Discovered:**
```bash
# Rollback to previous version
git checkout main
git revert <merge-commit-hash>
git push origin main

# Or restore from backup
cp backup_original_scripts/*.py .
git add *.py
git commit -m "Rollback: Restore original scripts due to integration issues"
git push origin main
```

### 2.3 Create Decision Script for SPS-CE

**File: `decision_second_attempt.py`**

**Location**: `/Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts/decision_second_attempt.py`

**Requirements**: Adapt the SIP [`decision_third_attempt.py`](../scripts/decision_third_attempt.py) script for SPS-CE workflow

**Key Adaptations:**
1. **Question Text**: "Do you want to run a second attempt at library creation?"
2. **Step References**: Update to SPS-CE step names
3. **State Management**: Use SPS-CE step IDs
4. **Success Marker**: Create `.workflow_status/decision_second_attempt.success`

**State Management Logic:**
```python
def update_workflow_state(choice):
    """Update workflow_state.json for SPS-CE decision"""
    state_file = Path("workflow_state.json")
    
    # Load current state
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
    else:
        state = {}
    
    if choice == "yes":
        # Enable second attempt steps
        state["rework_first_attempt"] = "pending"
        state["second_fa_analysis"] = "pending"
        print("   ✅ Enabled Step 3: Rework First Attempt")
        print("   ✅ Enabled Step 4: Second FA Output Analysis")
        
    else:  # choice == "no"
        # Skip second attempt steps, go directly to conclusion
        state["rework_first_attempt"] = "skipped"
        state["second_fa_analysis"] = "skipped"
        state["conclude_fa_analysis"] = "pending"
        print("   ⏭️  Skipped Step 3: Rework First Attempt")
        print("   ⏭️  Skipped Step 4: Second FA Output Analysis")
        print("   ✅ Enabled Step 5: Conclude FA Analysis")
    
    # Save updated state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
```

**Complete Script Structure:**
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

def main():
    """Main decision logic"""
    try:
        print_decision_header()
        choice = get_user_choice()
        update_workflow_state(choice)
        print_completion_message(choice)
    except Exception as e:
        print(f"ERROR: Decision script failed: {e}")
        raise

def print_decision_header():
    """Display the decision prompt to the user"""
    print("\n" + "="*60)
    print("🔄 SPS-CE WORKFLOW DECISION POINT")
    print("="*60)
    print("\n📊 You've completed the first library QC analysis.")
    print("\n❓ QUESTION: Do you want to run a second attempt at library creation?")
    print("\n📋 Your options:")
    print("   ✅ YES = Run second attempt (Steps 3-4: Rework + QC)")
    print("   ❌ NO  = Skip to conclusion (Step 5: Conclude analysis)")
    print("\n" + "-"*60)

def get_user_choice():
    """Get and validate user input"""
    while True:
        try:
            choice = input("\n🎯 Enter your choice (Y/N): ").strip().upper()
            
            if choice in ['Y', 'YES']:
                print(f"\n✅ You chose: YES - Running second attempt")
                return "yes"
            elif choice in ['N', 'NO']:
                print(f"\n✅ You chose: NO - Skipping to conclusion")
                return "no"
            else:
                print("❌ Invalid input. Please enter Y (Yes) or N (No)")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Decision cancelled by user")
            sys.exit(1)
        except EOFError:
            print("\n\n⚠️  No input received")
            sys.exit(1)

def create_success_marker():
    """Create success marker file (required by workflow manager)"""
    status_dir = Path(".workflow_status")
    
    try:
        status_dir.mkdir(exist_ok=True)
        success_file = status_dir / "decision_second_attempt.success"
        success_file.touch()
        print("   ✅ Success marker created")
    except Exception as e:
        print(f"Error creating success marker: {e}")
        raise

def print_completion_message(choice):
    """Display completion message"""
    create_success_marker()
    
    print("\n" + "="*60)
    print("🎉 DECISION COMPLETED")
    print("="*60)
    
    if choice == "yes":
        print("\n📋 Next steps:")
        print("   1️⃣  Step 3 will be available to run")
        print("   2️⃣  After Step 3, Step 4 will become available")
        print("   3️⃣  After Step 4, Step 5 will become available")
    else:
        print("\n📋 Next steps:")
        print("   1️⃣  Step 5 will be available to run immediately")
        print("   ⏭️  Steps 3-4 have been skipped")
    
    print(f"\n🔄 Return to the workflow manager to continue...")
    print("="*60 + "\n")

# ... (include update_workflow_state function as detailed above)

if __name__ == "__main__":
    main()
```

## Phase 3: Testing Strategy

### 3.1 Test-Driven Development (TDD) Approach

**Create Test Suite Structure:**
```
tests/
├── test_workflow_generalization.py
├── test_template_system.py
├── test_script_path_resolution.py
├── test_sps_ce_integration.py
├── test_decision_scripts.py
├── test_sps_ce_success_markers.py
└── integration/
    ├── test_end_to_end_sip.py
    ├── test_end_to_end_sps_ce.py
    ├── test_workflow_switching.py
    └── test_external_repository_integration.py
```

### 3.2 SPS-CE Success Marker Testing

**File: `tests/test_sps_ce_success_markers.py`**
```python
import pytest
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

class TestSPSCESuccessMarkers:
    """Test success marker implementation for all SPS-CE scripts"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sps_ce_scripts_path(self):
        """Path to SPS-CE scripts repository"""
        return Path.home() / '.sip_lims_workflow_manager' / 'sps-ce_scripts'
    
    def test_make_illumina_index_success_marker(self, temp_project_dir, sps_ce_scripts_path):
        """Test SPS_make_illumina_index_and_FA_files_NEW.py success marker"""
        script_path = sps_ce_scripts_path / 'SPS_make_illumina_index_and_FA_files_NEW.py'
        script_name = 'SPS_make_illumina_index_and_FA_files_NEW'
        
        # Run script in test mode (if available) or with minimal test data
        result = subprocess.run([sys.executable, str(script_path), '--test-mode'],
                              cwd=temp_project_dir, capture_output=True, text=True)
        
        # Verify success marker exists
        success_file = temp_project_dir / ".workflow_status" / f"{script_name}.success"
        assert success_file.exists(), f"Success marker not created: {success_file}"
        
        # Verify success marker content
        content = success_file.read_text()
        assert "SUCCESS:" in content
        assert script_name in content
        assert "completed at" in content
    
    def test_success_marker_rerun_safety(self, temp_project_dir, sps_ce_scripts_path):
        """Test that success markers are properly replaced on re-runs"""
        script_path = sps_ce_scripts_path / 'decision_second_attempt.py'
        script_name = 'decision_second_attempt'
        
        # Create existing success marker
        status_dir = temp_project_dir / ".workflow_status"
        status_dir.mkdir(exist_ok=True)
        success_file = status_dir / f"{script_name}.success"
        success_file.write_text("OLD SUCCESS MARKER")
        
        # Create minimal workflow state
        state_file = temp_project_dir / 'workflow_state.json'
        state_file.write_text('{"first_fa_analysis": "completed"}')
        
        # Run script
        subprocess.run([sys.executable, str(script_path)],
                      input='N\n', cwd=temp_project_dir, capture_output=True)
        
        # Verify success marker was replaced
        content = success_file.read_text()
        assert "OLD SUCCESS MARKER" not in content
        assert "SUCCESS:" in content or success_file.exists()
```

### 3.3 Unit Tests

**File: `tests/test_template_system.py`**
```python
import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

class TestTemplateSystem:
    def test_template_selection_sip(self):
        """Test SIP template selection"""
        with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sip'}):
            # Test template path resolution
            # Test template loading
            # Test template validation
            pass
    
    def test_template_selection_sps_ce(self):
        """Test SPS-CE template selection"""
        with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sps-ce'}):
            # Test template path resolution
            # Test template loading
            # Test template validation
            pass
    
    def test_template_copying(self):
        """Test template copying to project directory"""
        # Test source template selection
        # Test destination path (always workflow.yml)
        # Test file copying operation
        pass
    
    def test_invalid_workflow_type(self):
        """Test handling of invalid workflow type"""
        with patch.dict(os.environ, {'WORKFLOW_TYPE': 'invalid'}):
            # Test error handling
            # Test fallback behavior
            pass
```

**File: `tests/test_script_path_resolution.py`**
```python
class TestScriptPathResolution:
    def test_sip_script_path(self):
        """Test SIP script path resolution"""
        with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sip'}):
            # Test path construction
            # Test directory existence
            pass
    
    def test_sps_ce_script_path(self):
        """Test SPS-CE script path resolution"""
        with patch.dict(os.environ, {'WORKFLOW_TYPE': 'sps-ce'}):
            # Test path construction
            # Test directory existence
            pass
```

### 3.3 Integration Tests

**File: `tests/integration/test_end_to_end_sip.py`**
```python
class TestSIPWorkflowEndToEnd:
    def test_sip_project_creation(self):
        """Test complete SIP project creation"""
        # Test workflow selection
        # Test template copying
        # Test project initialization
        # Test first script execution
        pass
    
    def test_sip_workflow_progression(self):
        """Test SIP workflow step progression"""
        # Test step execution order
        # Test state management
        # Test success markers
        pass
```

**File: `tests/integration/test_end_to_end_sps_ce.py`**
```python
class TestSPSCEWorkflowEndToEnd:
    def test_sps_ce_project_creation(self):
        """Test complete SPS-CE project creation"""
        # Test workflow selection
        # Test template copying
        # Test project initialization
        pass
    
    def test_sps_ce_decision_script(self):
        """Test SPS-CE decision script functionality"""
        # Test decision prompt
        # Test state updates
        # Test conditional step enabling/skipping
        pass
    
    def test_sps_ce_success_marker_integration(self):
        """Test SPS-CE success markers work with workflow manager"""
        # Test workflow manager detects success markers
        # Test step progression based on success markers
        # Test failure handling when success markers missing
        pass
```

**File: `tests/integration/test_external_repository_integration.py`**
```python
class TestExternalRepositoryIntegration:
    def test_sps_ce_repository_access(self):
        """Test access to SPS-CE scripts repository"""
        # Test repository exists and is accessible
        # Test scripts are present and executable
        # Test success marker modifications are in place
        pass
    
    def test_repository_update_workflow(self):
        """Test repository update and script synchronization"""
        # Test scripts_updater works with SPS-CE repository
        # Test branch switching and updates
        # Test rollback capabilities
        pass
```

### 3.4 Manual Testing Scenarios

**Create Manual Test Plan:**

**Test Scenario 1: SIP Workflow (Backward Compatibility)**
1. Run `./run.mac.command`
2. Select "1) SIP Fractionation and Library Prep"
3. Create new project
4. Verify template copied correctly
5. Execute first few workflow steps
6. Verify success markers created
7. Verify state management works

**Test Scenario 2: SPS-CE Workflow (New Functionality)**
1. Run `./run.mac.command`
2. Select "2) SPS-CE Library Creation"
3. Create new project
4. Verify SPS-CE template copied
5. Execute workflow steps through decision point
6. Test both YES and NO decision paths
7. Verify conditional step execution
8. **Verify success markers created for each step**

**Test Scenario 3: SPS-CE Success Marker Validation**
1. Create SPS-CE project
2. Execute first script manually
3. Verify `.workflow_status/SPS_make_illumina_index_and_FA_files_NEW.success` created
4. Execute script again, verify success marker replaced
5. Delete success marker, run workflow manager, verify failure detection
6. Restore success marker, verify workflow progression

**Test Scenario 4: Workflow Switching**
1. Create SIP project, verify isolation
2. Exit application
3. Create SPS-CE project, verify isolation
4. Verify no cross-contamination between projects

**Test Scenario 5: Error Handling**
1. Test invalid workflow selection
2. Test missing templates
3. Test missing script repositories
4. Test script execution failures
5. **Test missing success markers**
6. **Test corrupted success marker files**

**Test Scenario 6: External Repository Integration**
1. Test SPS-CE repository cloning and updates
2. Test script modifications are preserved during updates
3. Test rollback to original scripts if needed
4. Test branch switching between feature and main branches

## Implementation Order and Process

### Phase A: SPS-CE Script Modifications (FIRST PRIORITY)

**Why Start Here:**
- Independent of workflow manager changes
- Can be tested in isolation
- Establishes foundation for workflow manager integration
- Allows validation of success marker patterns before main implementation

**Step A1: Prepare SPS-CE Repository**
```bash
cd /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts
git checkout -b feature/workflow-manager-integration
git push -u origin feature/workflow-manager-integration
```

**Step A2: Backup Original Scripts**
```bash
mkdir -p backup_original_scripts
cp *.py backup_original_scripts/
git add backup_original_scripts/
git commit -m "Backup: Original scripts before workflow manager integration"
```

**Step A3: Modify Scripts with Success Markers**
1. **`SPS_make_illumina_index_and_FA_files_NEW.py`** - Add Pattern 2 (Robust Success Marker)
2. **`SPS_first_FA_output_analysis_NEW.py`** - Add Pattern 2 (Robust Success Marker)
3. **`SPS_rework_first_attempt_NEW.py`** - Add Pattern 2 (Robust Success Marker)
4. **`SPS_second_FA_output_analysis_NEW.py`** - Add Pattern 2 (Robust Success Marker)
5. **`decision_second_attempt.py`** - Create new script with Pattern 3 (Decision Script Success Marker)

**Step A4: Test Each Modified Script**
```bash
# Test each script individually
python SPS_make_illumina_index_and_FA_files_NEW.py --test-mode
ls .workflow_status/SPS_make_illumina_index_and_FA_files_NEW.success

# Repeat for each script
```

**Step A5: Commit and Push SPS-CE Changes**
```bash
git add .
git commit -m "Add workflow manager success markers to SPS-CE scripts

- Add success marker implementation to all SPS-CE scripts
- Use robust error handling pattern from SIP scripts
- Ensure compatibility with workflow manager completion detection
- Maintain backward compatibility with standalone script execution"

git push origin feature/workflow-manager-integration
```

**Step A6: Merge to Main and Update Remote**
```bash
# After validation
git checkout main
git merge feature/workflow-manager-integration
git push origin main
```

**Step A7: Verify SPS-CE Scripts Are Up-to-Date**
```bash
# Ensure local repository is synchronized with remote
cd /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts
git pull origin main
```

### Phase B: Workflow Manager Modifications (SECOND PRIORITY)

**Why After SPS-CE Scripts:**
- SPS-CE scripts with success markers are now available
- Can test workflow manager changes against working SPS-CE scripts
- Reduces complexity by having one stable foundation

**Step B1: Create Workflow Manager Feature Branch**
```bash
cd /Users/RRMalmstrom/Desktop/sip_lims_workflow_manager
git checkout -b feature/workflow-generalization
git push -u origin feature/workflow-generalization
```

**Step B2: Implement Core Infrastructure Changes**
1. **Run Script Modifications** - Add workflow selection menus
2. **Template System** - Create SPS-CE template and selection logic
3. **Docker Configuration** - Add WORKFLOW_TYPE environment variable
4. **Scripts Updater** - Make workflow-aware for repository management

**Step B3: Implement Application Logic Changes**
1. **[`app.py`](app.py)** - Template selection based on WORKFLOW_TYPE
2. **[`src/git_update_manager.py`](src/git_update_manager.py)** - Repository mapping
3. **[`src/scripts_updater.py`](src/scripts_updater.py)** - Workflow-aware updates

**Step B4: Test Workflow Manager Changes**
1. **Unit Tests** - Template system, script path resolution
2. **Integration Tests** - End-to-end workflow testing
3. **Manual Testing** - Both SIP and SPS-CE workflows

### Phase C: Integration Testing and Validation (FINAL PHASE)

**Step C1: End-to-End Testing**
1. Test SIP workflow (backward compatibility)
2. Test SPS-CE workflow (new functionality)
3. Test workflow switching
4. Test error handling scenarios

**Step C2: Success Marker Integration Validation**
1. Verify workflow manager detects SPS-CE success markers
2. Test step progression based on success markers
3. Test failure handling when success markers missing

**Step C3: Repository Integration Testing**
1. Test SPS-CE repository updates work correctly
2. Test branch switching and script synchronization
3. Verify rollback capabilities

### Critical Implementation Dependencies

**Dependency Chain:**
1. **SPS-CE Scripts MUST be modified first** - Provides success markers for workflow manager
2. **SPS-CE Repository MUST be updated** - Ensures scripts_updater can access modified scripts
3. **Workflow Manager Changes** - Can then rely on working SPS-CE scripts with success markers

**Why This Order is Critical:**
- **Isolation**: SPS-CE script changes can be tested independently
- **Foundation**: Success markers provide the integration point for workflow manager
- **Validation**: Each phase can be validated before moving to the next
- **Rollback**: Each phase can be rolled back independently if issues arise
- **Debugging**: Problems can be isolated to specific phases

### Rollback Strategy by Phase

**Phase A Rollback (SPS-CE Scripts):**
```bash
cd /Users/RRMalmstrom/.sip_lims_workflow_manager/sps-ce_scripts
cp backup_original_scripts/*.py .
git add *.py
git commit -m "Rollback: Restore original scripts"
git push origin main
```

**Phase B Rollback (Workflow Manager):**
```bash
cd /Users/RRMalmstrom/Desktop/sip_lims_workflow_manager
git checkout main
git revert <merge-commit-hash>
git push origin main
```

**Phase C Rollback (Integration Issues):**
- Rollback Phase B changes
- Keep Phase A changes (SPS-CE scripts work independently)
- Debug integration issues in isolation

## Summary: SPS-CE Success Marker Implementation

### What Was Added to the Implementation Plan

**1. Comprehensive Success Marker Analysis**
- Analyzed 3 distinct success marker patterns from existing SIP scripts
- Documented exact implementation requirements for each pattern
- Identified optimal patterns for different script types

**2. Detailed SPS-CE Script Modification Plan**
- **5 scripts requiring modifications**: All SPS-CE workflow scripts
- **3 implementation patterns**: Simple, Robust, and Decision script patterns
- **Specific code examples**: Exact code to add to each script
- **Error handling**: Robust error handling and re-run safety

**3. External Repository Workflow**
- **Branch strategy**: Feature branch for SPS-CE script modifications
- **Testing approach**: Individual script testing before integration
- **Backup strategy**: Original script preservation
- **Rollback plan**: Multiple rollback options at each phase

**4. Implementation Order (Critical)**
- **Phase A**: SPS-CE script modifications FIRST
- **Phase B**: Workflow manager modifications SECOND
- **Phase C**: Integration testing and validation FINAL
- **Dependency chain**: Each phase builds on the previous

**5. Comprehensive Testing Strategy**
- **Unit tests**: Success marker creation and validation
- **Integration tests**: Workflow manager compatibility
- **Manual testing**: 6 detailed test scenarios including success marker validation
- **Repository integration tests**: External repository workflow validation

### Key Success Factors

**1. Success Marker Patterns**
- **Pattern 2 (Robust)** recommended for most SPS-CE scripts
- **Pattern 3 (Decision)** for decision scripts
- **Consistent naming**: `{script_name}.success` in `.workflow_status/`
- **Error handling**: Graceful failure when success markers can't be created

**2. Implementation Order**
- **SPS-CE scripts FIRST** - Provides foundation for workflow manager
- **Repository updates** - Ensures scripts are available for workflow manager
- **Workflow manager changes** - Can rely on working SPS-CE scripts

**3. Testing and Validation**
- **Individual script testing** before integration
- **Success marker validation** at each step
- **Backward compatibility** verification for SIP workflows
- **End-to-end testing** of complete SPS-CE workflow

### Ready for Implementation

The implementation plan now includes:
- ✅ **Complete success marker implementation details**
- ✅ **Exact code patterns for each SPS-CE script**
- ✅ **Step-by-step modification process**
- ✅ **External repository workflow**
- ✅ **Comprehensive testing strategy**
- ✅ **Clear implementation order and dependencies**
- ✅ **Rollback strategies for each phase**

**Next Step**: Begin Phase A - SPS-CE Script Modifications

## Critical WORKFLOW_TYPE Propagation Flow

### Complete Data Flow Architecture

**User Selection → Environment Variables → Docker → Application:**

1. **User Selects Workflow** (run.mac.command / run.windows.bat)
   - User chooses SIP or SPS-CE
   - `WORKFLOW_TYPE` environment variable set (`sip` or `sps-ce`)

2. **Script Path Resolution** (run scripts)
   - `SCRIPTS_PATH` becomes `~/.sip_lims_workflow_manager/${WORKFLOW_TYPE}_scripts`
   - Scripts updater called with `--workflow-type` parameter

3. **Docker Environment** (docker-compose.yml)
   - `WORKFLOW_TYPE` passed as environment variable to container
   - Workflow-specific script directory mounted to `/workflow-scripts`

4. **Application Logic** (app.py)
   - Reads `WORKFLOW_TYPE` from environment
   - Selects correct template: `templates/${WORKFLOW_TYPE}_workflow.yml`
   - Copies to project as `workflow.yml`

5. **Script Repository Management** (scripts_updater.py)
   - Repository selection based on workflow type
   - SIP: `sip_scripts_workflow_gui` repository
   - SPS-CE: `SPS_library_creation_scripts` repository

### Validation Checkpoints

**Environment Variable Propagation:**
- [ ] `WORKFLOW_TYPE` exported in run scripts
- [ ] `WORKFLOW_TYPE` passed to docker-compose
- [ ] `WORKFLOW_TYPE` available in container environment
- [ ] `WORKFLOW_TYPE` used by app.py for template selection

**Script Path Management:**
- [ ] Workflow-specific directories created
- [ ] Correct repository cloned/updated per workflow type
- [ ] Docker volume mounts correct script directory
- [ ] Scripts accessible within container

**Repository Update Logic:**
- [ ] SIP workflow updates SIP scripts repository
- [ ] SPS-CE workflow updates SPS-CE scripts repository
- [ ] No cross-contamination between workflow types
- [ ] Error handling for missing repositories

## Implementation Notes

### Critical Success Factors

1. **WORKFLOW_TYPE Propagation**: Must flow from user selection through all system components
2. **Repository Isolation**: Ensure workflow-specific script management and updates
3. **Success Markers**: Essential for workflow manager integration
4. **Template Validation**: Prevent runtime errors with malformed templates
5. **Docker Environment**: Correct environment variables and volume mounting
6. **Error Handling**: Graceful degradation for missing components
7. **Testing**: Comprehensive coverage prevents regressions

### Common Pitfalls to Avoid

1. **Path Resolution**: Ensure script paths work across platforms
2. **Template Copying**: Always copy to `workflow.yml` in project
3. **State Management**: Don't break existing state file format
4. **Docker Integration**: Verify environment variables pass through
5. **Success Markers**: Must match exact script filename pattern

### Performance Considerations

1. **Template Loading**: Cache templates to avoid repeated file I/O
2. **Script Path Validation**: Check paths exist before execution
3. **State File Updates**: Atomic writes to prevent corruption
4. **Docker Startup**: No additional overhead from generalization

## Conclusion

This implementation plan provides comprehensive instructions for generalizing the SIP LIMS workflow manager to support multiple laboratory processes. The approach maintains full backward compatibility while enabling clean extension to new workflows.

**Key Benefits:**
- **Zero Breaking Changes**: Existing SIP workflows unaffected
- **Clean Architecture**: Workflow-agnostic core with process-specific extensions
- **Easy Maintenance**: Clear separation of concerns
- **Future Extensibility**: Framework for additional laboratory processes

**Implementation Timeline:**
- **Phase 1**: Core infrastructure (2-3 days)
- **Phase 2**: SPS-CE integration (2-3 days)
- **Phase 3**: Testing (2-3 days)
- **Phase 4**: Validation and deployment (1-2 days)

**Total Estimated Effort**: 7-11 days for complete implementation and validation.

---

**Document Version**: 1.0  
**Created**: January 8, 2026  
**Target Audience**: Coding Agents  
**Prerequisites**: Comprehensive architectural analysis completed  
**Next Steps**: Begin Phase 1 implementation with TDD approach