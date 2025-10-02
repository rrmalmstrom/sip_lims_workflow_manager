@echo off
REM SIP LIMS Workflow Manager Uninstall Script
REM This script removes the virtual environment and cloned scripts
REM while preserving user project data.

echo === SIP LIMS Workflow Manager Uninstall ===
echo.
echo This will remove:
echo   - Python virtual environment (.venv\)
echo   - Cloned workflow scripts (scripts\)
echo   - SSH deploy key (.ssh\)
echo.
echo This will PRESERVE:
echo   - Your project folders and data
echo   - Workflow configurations
echo   - Database files
echo   - Output files
echo.

REM Confirmation prompt
set /p "confirm=Are you sure you want to uninstall? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Starting uninstall process...

REM Function to safely remove directory
:safe_remove
set "dir_path=%~1"
set "dir_name=%~2"

if exist "%dir_path%" (
    echo Removing %dir_name%...
    rmdir /s /q "%dir_path%" 2>nul
    if not exist "%dir_path%" (
        echo ✓ Successfully removed %dir_name%
    ) else (
        echo ✗ Failed to remove %dir_name%
        goto :error
    )
) else (
    echo ✓ %dir_name% not found ^(already removed^)
)
goto :eof

REM Remove virtual environment
call :safe_remove ".venv" "virtual environment"

REM Remove cloned scripts
call :safe_remove "scripts" "workflow scripts"

REM Remove SSH deploy key directory
call :safe_remove ".ssh" "SSH deploy key"

REM Remove any cached Python files
echo Removing Python cache files...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
)
echo ✓ Python cache files removed

REM Remove any .pyc files
echo Removing compiled Python files...
for /r . %%f in (*.pyc) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
    )
)
echo ✓ Compiled Python files removed

echo.
echo === Uninstall Summary ===
echo ✓ Virtual environment removed
echo ✓ Workflow scripts removed
echo ✓ SSH deploy key removed
echo ✓ Cache files cleaned up
echo.
echo Your project data has been preserved.
echo To reinstall, run setup.bat again.
echo.
echo Uninstall complete!
pause
goto :end

:error
echo.
echo An error occurred during uninstall.
echo Some files may not have been removed.
pause
exit /b 1

:end