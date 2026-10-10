@echo off
setlocal
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

set "GUI_REQUEST="
if "%~1"=="" set "GUI_REQUEST=1"
if /i "%~1"=="--gui" if "%~2"=="" set "GUI_REQUEST=1"
if /i "%~1"=="-gui" if "%~2"=="" set "GUI_REQUEST=1"

if defined GUI_REQUEST (
    where pythonw >nul 2>&1
    if errorlevel 1 (
        echo ERROR: pythonw.exe was not found. Install Python with GUI support and retry. 1>&2
        exit /b 2
    )
    start "" /b pythonw -m doctranslate %*
    exit /b 0
)

set "PYTHON=python"
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python 3.11 or newer was not found. Install Python and retry. 1>&2
        exit /b 2
    )
    set "PYTHON=py -3"
)
%PYTHON% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)"
if errorlevel 1 (
    echo ERROR: Python 3.11 or newer is required. 1>&2
    exit /b 2
)
%PYTHON% -m doctranslate %*
exit /b %ERRORLEVEL%
