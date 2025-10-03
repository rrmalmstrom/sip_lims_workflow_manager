@echo off
echo --- Setting up SIP LIMS Workflow Manager ---

REM Check for Python
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

REM Check Python version (basic check)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

echo Setting up SSH key permissions...
REM Ensure SSH keys have correct permissions (required by SSH/Git)
REM Note: Windows permissions are handled differently, but we ensure the files exist
if exist .ssh\scripts_deploy_key (
    echo Scripts SSH key found.
)
if exist .ssh\app_deploy_key (
    echo App SSH key found.
)

echo Cloning or updating the script repository...
set "GIT_SSH_COMMAND=ssh -i .ssh/scripts_deploy_key -o IdentitiesOnly=yes"
IF EXIST scripts (
    cd scripts
    git pull
    cd ..
) ELSE (
    git clone git@github.com:rrmalmstrom/sip_scripts_workflow_gui.git scripts
)
set "GIT_SSH_COMMAND="

echo --- Conda Environment Setup ---

REM 1. Check if conda is installed
conda --version >NUL 2>NUL
if errorlevel 1 (
    echo ERROR: Conda is not installed or not in your PATH.
    echo Please install Miniconda or Anaconda and ensure it's added to your shell's PATH.
    pause
    exit /b 1
)

echo Conda found. Proceeding with environment setup...

REM 2. Create or update the environment from the lock file
conda env list | findstr /B "sip-lims " >NUL
if %errorlevel%==0 (
    echo Environment 'sip-lims' already exists. Updating...
    conda env update --name sip-lims --file environment.yml --prune
) ELSE (
    echo Environment 'sip-lims' not found. Creating...
    conda env create -f environment.yml
)

if errorlevel 1 (
    echo ERROR: Failed to create or update the conda environment.
    pause
    exit /b 1
)

echo.
echo ✅ Conda environment 'sip-lims' is up to date.

echo.
echo.
echo ✅ Setup completed successfully!
echo You can now run the application using run.bat.
pause