@echo off
echo --- Setting up SIP LIMS Workflow Manager ---

REM Check for Python
python --version 2>NUL
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo Setting up SSH key permissions...
REM Ensure SSH keys have correct permissions (required by SSH/Git)
REM Note: Windows permissions are handled differently, but we ensure the files exist
if exist .ssh\scripts_deploy_key (
    echo Scripts SSH key found, ensuring proper access...
)
if exist .ssh\app_deploy_key (
    echo App SSH key found, ensuring proper access...
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
set GIT_SSH_COMMAND=

echo Creating virtual environment...
python -m venv .venv

echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo Creating installation receipt...
certutil -hashfile requirements.txt SHA256 > .venv\install_receipt.txt

echo.
echo Setup complete. You can now run the application using run.bat.
pause