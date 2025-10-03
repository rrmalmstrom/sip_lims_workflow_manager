@echo off
echo --- Starting SIP LIMS Workflow Manager ---

REM NOTE: The old environment checks are removed. The new setup process is robust.

REM Activate the conda environment
call conda activate sip-lims
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment 'sip-lims'.
    echo Please ensure the setup script has been run successfully.
    pause
    exit /b 1
)

echo --- Using Python from: ---
where python

REM Launch Streamlit with localhost-only configuration
echo Launching application in 'sip-lims' environment...
streamlit run app.py --server.headless=true --server.address=127.0.0.1