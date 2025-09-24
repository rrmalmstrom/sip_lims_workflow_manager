@echo off
echo --- Starting LIMS Workflow Manager ---

IF NOT EXIST .venv\install_receipt.txt (
    echo ERROR: Application has not been set up. Please run setup.bat.
    pause
    exit /b 1
)

certutil -hashfile requirements.txt SHA256 > .\.tmp_hash.txt
findstr /v "certutil" .\.tmp_hash.txt > .\.current_hash.txt
set /p CURRENT_HASH=<.\.current_hash.txt

set /p RECEIPT_HASH=<.\.venv\install_receipt.txt
findstr /v "certutil" .\.venv\install_receipt.txt > .\.tmp_receipt.txt
set /p RECEIPT_HASH=<.\.tmp_receipt.txt

del .\.tmp_hash.txt
del .\.current_hash.txt
del .\.tmp_receipt.txt

IF NOT "%CURRENT_HASH%"=="%RECEIPT_HASH%" (
    echo ERROR: Dependencies have changed. Please run setup.bat again.
    pause
    exit /b 1
)

echo Checking for script updates...
cd scripts
git fetch
for /f "tokens=*" %%a in ('git status -uno') do (
    set "UPDATE_STATUS=%%a"
    goto :check_status
)
:check_status
cd ..

call .venv\Scripts\activate.bat

if "%UPDATE_STATUS%"=="Your branch is behind" (
    streamlit run app.py --server.headless=true -- --scripts-update-available
) else (
    streamlit run app.py --server.headless=true
)