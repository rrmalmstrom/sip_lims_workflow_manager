@echo off
REM Branch utilities for Windows batch scripts
REM Provides simple wrapper functions that call Python utilities for branch detection and Docker tag generation
REM This is the Windows equivalent of utils/branch_utils.sh

REM Get the directory where this script is located
set "UTILS_DIR=%~dp0"
for %%i in ("%UTILS_DIR%..") do set "PROJECT_ROOT=%%~fi"

REM ============================================================================
REM SIMPLE UTILITY FUNCTIONS (No complex function dispatch)
REM ============================================================================

REM Get current branch tag using Python utilities with fallback
REM Note: Git validation moved to after directory setup to match Mac behavior
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_docker_tag_for_current_branch; print(get_docker_tag_for_current_branch())" 2^>nul') do set "CURRENT_BRANCH=%%i"
if "%CURRENT_BRANCH%"=="" (
    REM Fallback to git command
    for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "FALLBACK_BRANCH=%%i"
    if not "%FALLBACK_BRANCH%"=="" (
        REM Simple sanitization for Docker tag
        set "CURRENT_BRANCH=%FALLBACK_BRANCH%"
        set "CURRENT_BRANCH=%CURRENT_BRANCH: =-%"
        set "CURRENT_BRANCH=%CURRENT_BRANCH:/=-%"
        set "CURRENT_BRANCH=%CURRENT_BRANCH:\=-%"
    ) else (
        echo Error: Failed to detect current branch >&2
        exit /b 1
    )
)

REM Get local image name
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_local_image_name_for_current_branch; print(get_local_image_name_for_current_branch())" 2^>nul') do set "LOCAL_IMAGE_NAME=%%i"
if "%LOCAL_IMAGE_NAME%"=="" (
    set "LOCAL_IMAGE_NAME=sip-lims-workflow-manager:%CURRENT_BRANCH%"
)

REM Get remote image name
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_remote_image_name_for_current_branch; print(get_remote_image_name_for_current_branch())" 2^>nul') do set "REMOTE_IMAGE_NAME=%%i"
if "%REMOTE_IMAGE_NAME%"=="" (
    set "REMOTE_IMAGE_NAME=ghcr.io/rrmalmstrom/sip_lims_workflow_manager:%CURRENT_BRANCH%"
)

REM Export variables to parent script (this is the key difference from functions)
endlocal & (
    set "CURRENT_BRANCH=%CURRENT_BRANCH%"
    set "LOCAL_IMAGE_NAME=%LOCAL_IMAGE_NAME%"
    set "REMOTE_IMAGE_NAME=%REMOTE_IMAGE_NAME%"
)

exit /b 0

REM ============================================================================
REM VALIDATION FUNCTIONS
REM ============================================================================

:validate_git_repository
REM Validate if we're in a Git repository (matches Mac version behavior)
git rev-parse --git-dir >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Not in a Git repository >&2
    exit /b 1
)
exit /b 0

:get_current_branch
REM Get current branch name (matches bash version)
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_current_branch; print(get_current_branch())" 2^>nul') do set "BRANCH_RESULT=%%i"
if "%BRANCH_RESULT%"=="" (
    REM Fallback to git command
    for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH_RESULT=%%i"
)
echo %BRANCH_RESULT%
exit /b 0

:get_current_branch_tag
REM Get Docker tag for current branch (matches bash version)
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_docker_tag_for_current_branch; print(get_docker_tag_for_current_branch())" 2^>nul') do set "TAG_RESULT=%%i"
echo %TAG_RESULT%
exit /b 0

:get_local_image_name
REM Get local Docker image name with branch tag (matches bash version)
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_local_image_name_for_current_branch; print(get_local_image_name_for_current_branch())" 2^>nul') do set "LOCAL_IMAGE_RESULT=%%i"
echo %LOCAL_IMAGE_RESULT%
exit /b 0

:get_remote_image_name
REM Get remote Docker image name with branch tag (matches bash version)
for /f "delims=" %%i in ('python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_remote_image_name_for_current_branch; print(get_remote_image_name_for_current_branch())" 2^>nul') do set "REMOTE_IMAGE_RESULT=%%i"
echo %REMOTE_IMAGE_RESULT%
exit /b 0

:get_branch_info
REM Get comprehensive branch information (matches bash version)
python3 -c "import sys; sys.path.insert(0, '%PROJECT_ROOT%'); from utils.branch_utils import get_branch_info; info = get_branch_info(); [print(f'{key}={value}') for key, value in info.items()]" 2>nul
exit /b %errorlevel%

REM ============================================================================
REM FALLBACK FUNCTIONS (Pure Batch Implementation)
REM ============================================================================

:get_current_branch_fallback
setlocal
REM Try git command directly
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "branch=%%i"
set "git_exit_code=%errorlevel%"

if %git_exit_code% equ 0 (
    if "%branch%"=="HEAD" (
        REM Detached HEAD - get short SHA
        for /f "delims=" %%i in ('git rev-parse --short HEAD 2^>nul') do set "sha=%%i"
        if not "%sha%"=="" (
            echo detached-%sha%
            endlocal & exit /b 0
        )
    ) else (
        echo %branch%
        endlocal & exit /b 0
    )
)

echo Error: Could not detect branch >&2
endlocal & exit /b 1

:sanitize_branch_for_docker_tag_fallback
setlocal
set "branch=%1"

if "%branch%"=="" (
    echo Error: Branch name cannot be empty >&2
    endlocal & exit /b 1
)

REM Convert to lowercase and replace invalid characters
set "tag=%branch%"
REM Simple character replacement for Windows batch
set "tag=%tag: =-%"
set "tag=%tag:/=-%"
set "tag=%tag:\=-%"
set "tag=%tag:_=-%"

REM Convert to lowercase (basic approach)
for %%i in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    call set "tag=%%tag:%%i=%%i%%"
)
for %%i in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do (
    call set "tag=%%tag:%%i=%%i%%"
)

REM Remove leading and trailing dashes
:trim_start
if "%tag:~0,1%"=="-" (
    set "tag=%tag:~1%"
    goto trim_start
)
:trim_end
if "%tag:~-1%"=="-" (
    set "tag=%tag:~0,-1%"
    goto trim_end
)

if "%tag%"=="" (
    echo Error: Branch name resulted in empty tag >&2
    endlocal & exit /b 1
)

echo %tag%
endlocal & exit /b 0

:get_current_branch_tag_robust
setlocal
REM Try Python utilities first
call :get_current_branch_tag >nul 2>&1
if %errorlevel% equ 0 (
    call :get_current_branch_tag
    endlocal & exit /b 0
)

echo Warning: Python utilities failed, using fallback method >&2

REM Fallback to batch implementation
call :get_current_branch_fallback >temp_branch.txt 2>nul
if %errorlevel% equ 0 (
    set /p fallback_branch=<temp_branch.txt
    del temp_branch.txt >nul 2>&1
    call :sanitize_branch_for_docker_tag_fallback "!fallback_branch!" >temp_tag.txt 2>nul
    if %errorlevel% equ 0 (
        set /p fallback_tag=<temp_tag.txt
        del temp_tag.txt >nul 2>&1
        echo !fallback_tag!
        endlocal & exit /b 0
    )
    del temp_tag.txt >nul 2>&1
)
del temp_branch.txt >nul 2>&1

echo Error: All branch detection methods failed >&2
endlocal & exit /b 1

REM ============================================================================
REM TEST FUNCTION
REM ============================================================================

:test_branch_utils
echo Testing branch utilities...

REM Test Git repository validation
call :validate_git_repository
if %errorlevel% neq 0 (
    echo ❌ Not in a Git repository
    exit /b 1
)
echo ✅ Git repository validated

REM Test branch detection
call :get_current_branch >temp_branch_test.txt 2>nul
if %errorlevel% equ 0 (
    set /p test_branch=<temp_branch_test.txt
    echo ✅ Current branch: !test_branch!
) else (
    echo ❌ Branch detection failed
    del temp_branch_test.txt >nul 2>&1
    exit /b 1
)
del temp_branch_test.txt >nul 2>&1

REM Test tag generation
call :get_current_branch_tag >temp_tag_test.txt 2>nul
if %errorlevel% equ 0 (
    set /p test_tag=<temp_tag_test.txt
    echo ✅ Docker tag: !test_tag!
) else (
    echo ❌ Tag generation failed
    del temp_tag_test.txt >nul 2>&1
    exit /b 1
)
del temp_tag_test.txt >nul 2>&1

REM Test image name generation
call :get_local_image_name >temp_local_test.txt 2>nul
set "local_exit=%errorlevel%"
call :get_remote_image_name >temp_remote_test.txt 2>nul
set "remote_exit=%errorlevel%"

if %local_exit% equ 0 if %remote_exit% equ 0 (
    set /p test_local=<temp_local_test.txt
    set /p test_remote=<temp_remote_test.txt
    echo ✅ Local image: !test_local!
    echo ✅ Remote image: !test_remote!
) else (
    echo ❌ Image name generation failed
    del temp_local_test.txt >nul 2>&1
    del temp_remote_test.txt >nul 2>&1
    exit /b 1
)
del temp_local_test.txt >nul 2>&1
del temp_remote_test.txt >nul 2>&1

echo ✅ All branch utilities working correctly
exit /b 0

REM ============================================================================
REM MAIN EXECUTION (if script is run directly)
REM ============================================================================

REM If script is run directly, run tests
if "%1"=="test" (
    call :test_branch_utils
    exit /b %errorlevel%
)

REM If called with a function name, execute that function
if not "%1"=="" (
    call :%1 %2 %3 %4 %5
    exit /b %errorlevel%
)

REM Default: show usage
echo Usage: branch_utils.bat [function_name] [args...]
echo Available functions:
echo   validate_git_repository
echo   get_current_branch
echo   get_current_branch_tag
echo   get_local_image_name
echo   get_remote_image_name
echo   get_current_branch_tag_robust
echo   test_branch_utils
exit /b 0