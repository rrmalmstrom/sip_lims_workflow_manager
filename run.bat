@echo off
echo --- Starting SIP LIMS Workflow Manager ---

REM Check if setup was run
IF NOT EXIST .venv\install_receipt.txt (
    echo ERROR: Application has not been set up. Please run setup.bat.
    pause
    exit /b 1
)

REM Check if dependencies have changed by comparing hash files
REM Create current hash and compare with receipt
certutil -hashfile requirements.txt SHA256 > temp_current_hash.txt 2>nul
if errorlevel 1 (
    echo ERROR: Could not generate hash for requirements.txt
    pause
    exit /b 1
)

REM Compare the hash files (ignoring certutil header lines)
fc /b temp_current_hash.txt .venv\install_receipt.txt >nul 2>&1
if errorlevel 1 (
    echo ERROR: Dependencies have changed. Please run setup.bat again.
    del temp_current_hash.txt 2>nul
    pause
    exit /b 1
)

REM Clean up temporary file
del temp_current_hash.txt 2>nul

REM Activate virtual environment and run the application
call .venv\Scripts\activate.bat

REM Launch Streamlit with localhost-only configuration
streamlit run app.py --server.headless=true --server.address=127.0.0.1