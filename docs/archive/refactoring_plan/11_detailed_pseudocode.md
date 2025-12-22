# 11 - Detailed Pseudo-Code for All Script Modifications

## Overview
Comprehensive pseudo-code for all modifications required to implement the external script repository structure and developer/production mode functionality.

## 1. Setup Script Modifications (setup.command)

### Complete Modified setup.command
```bash
#!/bin/bash
# This script sets up the Conda environment for the SIP LIMS Workflow Manager.

# Exit on any error
set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Get the environment name from the first argument, or default to 'sip-lims'
ENV_NAME=${1:-sip-lims}

echo "--- Setting up SIP LIMS Workflow Manager: $ENV_NAME ---"

# NEW: Mode Detection Function
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# NEW: Create config directory and update .gitignore
setup_config_directory() {
    mkdir -p config
    update_gitignore
}

# NEW: Update .gitignore if needed
update_gitignore() {
    if ! grep -q "config/developer.marker" .gitignore; then
        echo "" >> .gitignore
        echo "# Developer Environment Configuration" >> .gitignore
        echo "# Exclude developer marker file to prevent distribution" >> .gitignore
        echo "config/developer.marker" >> .gitignore
        echo "" >> .gitignore
        echo "# Exclude local development config files" >> .gitignore
        echo "config/*.local" >> .gitignore
        echo "config/*.dev" >> .gitignore
        echo "config/local_*" >> .gitignore
        echo "✅ Updated .gitignore with developer configuration exclusions"
    fi
}

# NEW: Mode-aware script repository setup
setup_script_repositories() {
    MODE=$(detect_mode)
    echo "Detected mode: $MODE"
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        echo "Choose setup option:"
        echo "1) Work offline (skip remote repository updates)"
        echo "2) Connect to remotes to check for updates"
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1) 
                echo "Working offline - skipping repository updates"
                SKIP_REPOS=true
                ;;
            2) 
                echo "Connecting to remotes for updates"
                SKIP_REPOS=false
                ;;
            *) 
                echo "Invalid choice, defaulting to offline mode"
                SKIP_REPOS=true
                ;;
        esac
    else
        echo "🏭 Production mode detected - automatically updating repositories"
        SKIP_REPOS=false
    fi
    
    if [ "$SKIP_REPOS" = false ]; then
        setup_external_repositories
    fi
}

# NEW: External repository setup function
setup_external_repositories() {
    echo "Setting up external script repositories..."
    
    # Remove old nested scripts directory if it exists
    if [ -d "scripts" ]; then
        echo "Removing old nested scripts directory..."
        rm -rf scripts
    fi
    
    # Setup external script directories
    cd ..  # Go to parent directory
    
    # Always setup production scripts
    echo "Setting up production scripts..."
    if [ -d "sip_scripts_production" ]; then
        cd sip_scripts_production
        git pull
        cd ..
    else
        git clone https://github.com/rrmalmstrom/sip_scripts_production.git sip_scripts_production
    fi
    
    # Setup development scripts only in developer mode
    if [ "$MODE" = "developer" ]; then
        echo "Setting up development scripts..."
        if [ -d "sip_scripts_workflow_gui" ]; then
            cd sip_scripts_workflow_gui
            git pull
            cd ..
        else
            git clone https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git sip_scripts_workflow_gui
        fi
    fi
    
    cd sip_lims_workflow_manager  # Return to app directory
}

# NEW: Enhanced success messaging
show_completion_message() {
    MODE=$(detect_mode)
    
    echo ""
    if [ "$MODE" = "developer" ]; then
        echo "✅ Developer setup completed successfully!"
        echo "📁 Script repositories are located in sibling directories:"
        echo "   - ../sip_scripts_production (production scripts)"
        if [ "$SKIP_REPOS" = false ]; then
            echo "   - ../sip_scripts_workflow_gui (development scripts)"
        fi
        echo "🚀 You can now run the application using run.command"
        echo "💡 The run script will prompt you to choose between dev/prod scripts"
    else
        echo "✅ Production setup completed successfully!"
        echo "📁 Production scripts are located at: ../sip_scripts_production"
        echo "🚀 You can now run the application using run.command"
    fi
}

# MAIN EXECUTION FLOW

# NEW: Setup configuration
setup_config_directory

# MODIFIED: Script repository setup (replaces lines 16-24)
setup_script_repositories

# UNCHANGED: Conda Environment Setup (lines 26-45)
# --- Conda Environment Setup ---

# 1. Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed or not in your PATH."
    echo "Please install Miniconda or Anaconda and ensure it's added to your shell's PATH."
    exit 1
fi

echo "Conda found. Proceeding with environment setup..."

# 2. Create or update the environment from the lock file
if conda env list | grep -q "^$ENV_NAME\s"; then
    echo "Environment '$ENV_NAME' already exists. Updating..."
    # The --prune option removes packages that are no longer in the lock file
    conda env update --name "$ENV_NAME" --file environment.yml --prune
else
    echo "Environment '$ENV_NAME' not found. Creating..."
    conda env create --name "$ENV_NAME" -f environment.yml
fi

echo "✅ Conda environment '$ENV_NAME' is up to date."

# MODIFIED: Success messaging (replaces lines 47-51)
show_completion_message
```

## 2. Run Script Modifications (run.command)

### Complete Modified run.command
```bash
#!/bin/bash
# This script runs the SIP LIMS Workflow Manager application.

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "--- Starting SIP LIMS Workflow Manager ---"

# NEW: Mode Detection Function (same as setup.command)
detect_mode() {
    if [ -f "config/developer.marker" ]; then
        echo "developer"
    else
        echo "production"
    fi
}

# NEW: Script Path Selection Function
select_script_path() {
    MODE=$(detect_mode)
    
    if [ "$MODE" = "developer" ]; then
        echo "🔧 Developer mode detected"
        echo ""
        echo "Choose script source for this session:"
        echo "1) Development scripts (../sip_scripts_workflow_gui)"
        echo "2) Production scripts (../sip_scripts_production)"
        echo ""
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1) 
                SCRIPT_PATH="../sip_scripts_workflow_gui"
                echo "✅ Using development scripts from: $SCRIPT_PATH"
                ;;
            2) 
                SCRIPT_PATH="../sip_scripts_production"
                echo "✅ Using production scripts from: $SCRIPT_PATH"
                ;;
            *) 
                echo "⚠️  Invalid choice, defaulting to production scripts"
                SCRIPT_PATH="../sip_scripts_production"
                ;;
        esac
    else
        echo "🏭 Production mode - using production scripts"
        SCRIPT_PATH="../sip_scripts_production"
    fi
    
    # Verify script directory exists
    if [ ! -d "$SCRIPT_PATH" ]; then
        echo "❌ ERROR: Script directory not found: $SCRIPT_PATH"
        echo "Please run setup.command first to initialize script repositories."
        exit 1
    fi
    
    echo "📁 Script path: $SCRIPT_PATH"
}

# NEW: Enhanced Launch Function
launch_application() {
    echo "Launching application in 'sip-lims' environment..."
    echo "--- Using Python from: $(which python) ---"
    echo "--- Using scripts from: $SCRIPT_PATH ---"
    
    # Pass script path to the Python application
    streamlit run app.py --server.headless=true --server.address=127.0.0.1 -- --script-path="$SCRIPT_PATH"
}

# MAIN EXECUTION FLOW

# NEW: Call script path selection
select_script_path

# UNCHANGED: Conda environment activation (lines 13-15)
eval "$(conda shell.bash hook)"
conda activate sip-lims

# MODIFIED: Launch application with script path
launch_application
```

## 3. App.py Modifications

### Key Modifications to app.py
```python
# NEW: Add after line 14 (after imports)
import argparse
from pathlib import Path

def parse_script_path_argument():
    """
    Parse command line arguments to get script path.
    Uses argparse to handle Streamlit's argument passing format.
    """
    parser = argparse.ArgumentParser(add_help=False)  # Disable help to avoid conflicts
    parser.add_argument('--script-path', 
                       default='scripts', 
                       help='Path to scripts directory')
    
    # Parse only known args to avoid conflicts with Streamlit args
    try:
        args, unknown = parser.parse_known_args()
        script_path = Path(args.script_path)
        
        # Validate that script path exists
        if not script_path.exists():
            print(f"Warning: Script path does not exist: {script_path}")
            print("Falling back to default 'scripts' directory")
            script_path = Path("scripts")
            
        return script_path
    except Exception as e:
        print(f"Error parsing script path argument: {e}")
        print("Using default 'scripts' directory")
        return Path("scripts")

# Initialize script path globally
SCRIPT_PATH = parse_script_path_argument()

# MODIFIED: Update check_for_script_updates function (line 43)
@st.cache_data(ttl=3600)
def check_for_script_updates():
    """
    Check for script updates using the unified Git system.
    Uses the configured script path instead of hardcoded 'scripts' directory.
    """
    try:
        # Pass script path to update manager
        script_manager = create_update_manager("scripts", script_path=SCRIPT_PATH)
        return script_manager.check_for_updates()
    except Exception as e:
        return {
            'update_available': False,
            'current_version': None,
            'latest_version': None,
            'error': f"Failed to check for script updates: {str(e)}"
        }

# MODIFIED: Update update_scripts function (line 61)
def update_scripts():
    """Update scripts to latest version using configured script path."""
    try:
        script_manager = create_update_manager("scripts", script_path=SCRIPT_PATH)
        return script_manager.update_to_latest()
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to update scripts: {str(e)}"
        }

# MODIFIED: Add to main() function after state initialization (around line 543)
def main():
    st.title("🧪 SIP LIMS Workflow Manager")

    # --- State Initialization ---
    if 'project' not in st.session_state:
        st.session_state.project = None
    # ... existing state initialization ...
    
    # NEW: Initialize script path in session state
    if 'script_path' not in st.session_state:
        st.session_state.script_path = SCRIPT_PATH
        
    # Display script path info for debugging/transparency
    if st.session_state.script_path != Path("scripts"):
        st.sidebar.info(f"📁 Using external scripts: {st.session_state.script_path}")

# MODIFIED: All Project instantiation points
# Pattern for all Project instantiations:
st.session_state.project = Project(project_path, script_path=st.session_state.script_path)
# Or for restoration projects:
project_for_restore = Project(project_path, script_path=st.session_state.script_path, load_workflow=False)
```

## 4. Core.py Modifications

### Modified Project Class in src/core.py
```python
# MODIFIED: Project class __init__ method (Line 35)
class Project:
    """
    Represents a single project folder, containing a workflow, its state,
    and all associated data. It coordinates the StateManager, SnapshotManager,
    and ScriptRunner.
    """
    def __init__(self, project_path: Path, script_path: Path = None, load_workflow: bool = True):
        self.path = project_path
        self.script_path = script_path or (project_path / "scripts")  # Default to nested
        self.workflow_file_path = self.path / "workflow.yml"
        
        self.state_manager = StateManager(self.path / "workflow_state.json")
        self.snapshot_manager = SnapshotManager(self.path, self.path / ".snapshots")
        # MODIFIED: Pass script_path to ScriptRunner
        self.script_runner = ScriptRunner(self.path, script_path=self.script_path)
        
        if load_workflow:
            if not self.workflow_file_path.is_file():
                raise FileNotFoundError(f"Workflow file not found at {self.workflow_file_path}")
            self.workflow = Workflow(self.workflow_file_path)
        else:
            self.workflow = None

    # NEW: Add script path validation method
    def validate_script_path(self) -> bool:
        """
        Validate that the script path exists and contains scripts.
        Returns True if valid, False otherwise.
        """
        if not self.script_path.exists():
            print(f"Warning: Script path does not exist: {self.script_path}")
            return False
        
        if not self.script_path.is_dir():
            print(f"Warning: Script path is not a directory: {self.script_path}")
            return False
        
        # Check for Python scripts
        python_scripts = list(self.script_path.glob("*.py"))
        if not python_scripts:
            print(f"Warning: No Python scripts found in: {self.script_path}")
            return False
        
        return True

    # NEW: Add utility methods
    def get_script_path(self) -> Path:
        """Get the configured script path."""
        return self.script_path
    
    def get_available_scripts(self) -> list[Path]:
        """Get list of available Python scripts."""
        if not self.script_path.exists():
            return []
        return list(self.script_path.glob("*.py"))
```

## 5. Git Update Manager Modifications

### Modified src/git_update_manager.py
```python
# NEW: Add repository detection function
def detect_script_repository_config(script_path: Path) -> dict:
    """
    Detect which script repository configuration to use based on script path.
    
    Args:
        script_path: Path to the script directory
        
    Returns:
        Repository configuration dictionary
    """
    script_path_str = str(script_path).lower()
    
    # Check if this is the development repository
    if "workflow_gui" in script_path_str or "sip_scripts_workflow_gui" in script_path_str:
        return {
            "repo_url": "https://github.com/rrmalmstrom/sip_scripts_workflow_gui.git",
            "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_workflow_gui",
            "update_method": "releases",
            "current_version_source": "git_tags",
            "fallback_version_source": "commit_hash"
        }
    
    # Default to production repository
    return {
        "repo_url": "https://github.com/rrmalmstrom/sip_scripts_production.git",
        "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_production",
        "update_method": "releases",
        "current_version_source": "git_tags",
        "fallback_version_source": "commit_hash"
    }

# MODIFIED: create_update_manager function (Line 458)
def create_update_manager(repo_type: str, base_path: Path = None, script_path: Path = None) -> GitUpdateManager:
    """
    Create an appropriate update manager instance.
    
    Args:
        repo_type: Either "scripts" or "application"
        base_path: Base path for the application (defaults to parent of this file)
        script_path: Path to scripts directory (for script updates only)
    
    Returns:
        GitUpdateManager instance
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    if repo_type == "scripts":
        if script_path:
            repo_path = script_path
        else:
            # Default to external production scripts
            repo_path = base_path.parent / "sip_scripts_production"
    elif repo_type == "application":
        repo_path = base_path
    else:
        raise ValueError(f"Unknown repo_type: {repo_type}")
    
    return GitUpdateManager(repo_type, repo_path)

# MODIFIED: GitUpdateManager constructor
class GitUpdateManager:
    def __init__(self, repo_type: str, repo_path: Path, cache_ttl: int = 1800):
        """
        Initialize Git update manager.
        
        Args:
            repo_type: Either "scripts" or "application"
            repo_path: Path to the local repository
            cache_ttl: Cache time-to-live in seconds (default: 30 minutes)
        """
        self.repo_type = repo_type
        self.repo_path = Path(repo_path)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._last_check_time = None
        
        # MODIFIED: Dynamic repository configuration
        if repo_type == "scripts":
            # Detect configuration based on actual script path
            script_config = detect_script_repository_config(self.repo_path)
            self.repo_configs = {
                "scripts": script_config,
                "application": {
                    "repo_url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "version_file"
                }
            }
        else:
            # Application updates use static configuration
            self.repo_configs = {
                "scripts": {
                    "repo_url": "https://github.com/rrmalmstrom/sip_scripts_production.git",
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_scripts_production",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "commit_hash"
                },
                "application": {
                    "repo_url": "https://github.com/rrmalmstrom/sip_lims_workflow_manager.git",
                    "api_url": "https://api.github.com/repos/rrmalmstrom/sip_lims_workflow_manager",
                    "update_method": "releases",
                    "current_version_source": "git_tags",
                    "fallback_version_source": "version_file"
                }
            }
        
        if repo_type not in self.repo_configs:
            raise ValueError(f"Unknown repo_type: {repo_type}. Must be 'scripts' or 'application'")
        
        self.config = self.repo_configs[repo_type]
```

## 6. ScriptRunner Modifications (src/logic.py)

### Required ScriptRunner Modifications
```python
# MODIFIED: ScriptRunner constructor
class ScriptRunner:
    def __init__(self, project_path: Path, script_path: Path = None):
        self.project_path = project_path  # WHERE scripts execute (working directory)
        self.script_path = script_path or (project_path / "scripts")  # WHERE scripts are sourced from
        # ... rest of initialization
    
    def run(self, script_name: str, args: list = None):
        """
        Run a script from script_path but execute in project_path context.
        
        Args:
            script_name: Name of script file (e.g., "my_script.py")
            args: Command line arguments for the script
        """
        # Source script from script_path
        script_file = self.script_path / script_name
        
        if not script_file.exists():
            raise FileNotFoundError(f"Script not found: {script_file}")
        
        # Execute script in project_path context (working directory)
        # Implementation details handled in ScriptRunner
        # ... existing execution logic with project_path as working directory
```

## 7. .gitignore Modifications

### Updated .gitignore
```gitignore
# [Existing content remains unchanged]

# Developer Environment Configuration
# Exclude developer marker file to prevent distribution
config/developer.marker

# Exclude local development config files
config/*.local
config/*.dev
config/local_*
```

## Implementation Flow Summary

### Setup Process Flow
```
1. User runs setup.command/setup.bat
2. Script creates config/ directory
3. Script updates .gitignore if needed
4. Script detects mode (developer vs production)
5. If developer mode:
   - Prompt user for offline/online choice
   - If online: setup both dev and prod repositories
6. If production mode:
   - Automatically setup production repository only
7. Setup conda environment (unchanged)
8. Display mode-specific completion message
```

### Run Process Flow
```
1. User runs run.command/run.bat
2. Script detects mode (developer vs production)
3. If developer mode:
   - Prompt user to choose script source
   - Validate chosen directory exists
4. If production mode:
   - Automatically use production scripts
   - Validate directory exists
5. Activate conda environment (unchanged)
6. Launch streamlit with script-path argument
7. App.py parses script-path argument
8. App.py stores script_path in session state
9. All Project instances use external script_path
10. ScriptRunner sources from external path but executes in project context
```

### Error Handling Flow
```
1. Missing script directory:
   - Show clear error message
   - Suggest running setup script
   - Exit gracefully

2. Invalid user input:
   - Show warning
   - Use safe default (production scripts)
   - Continue execution

3. Argument parsing errors:
   - Log warning
   - Fall back to default 'scripts' directory
   - Continue execution

4. Repository access errors:
   - Show clear error message
   - Provide troubleshooting steps
   - Allow offline operation if possible
```

This pseudo-code provides a complete implementation guide for all the modifications needed to support the external script repository structure and developer/production mode functionality.