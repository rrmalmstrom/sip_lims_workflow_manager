@echo off
echo --- Setting up LIMS Workflow Manager ---

REM Check for Python
python --version 2>NUL
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo Cloning or updating the script repository...
set "GIT_SSH_COMMAND=ssh -i .ssh/deploy_key -o IdentitiesOnly=yes"
IF EXIST scripts (
    cd scripts
    git pull
    cd ..
) ELSE (
    git clone git@github.com:rrmalmstrom/sip_scripts.git scripts
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