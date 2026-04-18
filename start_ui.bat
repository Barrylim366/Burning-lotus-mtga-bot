@echo off
setlocal enabledelayedexpansion

rem One-click launcher for Windows. Creates a local .venv on first run,
rem installs requirements.txt, then starts ui.py. Later runs reuse the
rem venv and start instantly.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
set "VENV_DIR=%ROOT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%ROOT_DIR%\requirements.txt"
set "MARKER=%VENV_DIR%\.requirements.installed"

rem --- Locate a Python interpreter (py -3 is preferred on Windows) ---
set "PY_LAUNCHER="
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY_LAUNCHER=py -3"
) else (
    where python >nul 2>&1
    if !ERRORLEVEL!==0 (
        set "PY_LAUNCHER=python"
    )
)

if not defined PY_LAUNCHER (
    echo.
    echo [ERROR] Python 3 wurde nicht gefunden.
    echo Bitte Python 3.10 oder neuer installieren:
    echo     https://www.python.org/downloads/
    echo Beim Installer "Add Python to PATH" aktivieren.
    echo.
    pause
    exit /b 1
)

rem --- Create venv on first run ---
if not exist "%VENV_PYTHON%" (
    echo [INFO] Erstelle virtuelle Umgebung in "%VENV_DIR%" ...
    %PY_LAUNCHER% -m venv "%VENV_DIR%"
    if not exist "%VENV_PYTHON%" (
        echo [ERROR] Konnte .venv nicht anlegen.
        pause
        exit /b 1
    )
)

rem --- Install requirements if marker missing or requirements.txt newer ---
set "NEED_INSTALL=0"
if not exist "%MARKER%" set "NEED_INSTALL=1"
if exist "%MARKER%" (
    for %%I in ("%REQ_FILE%") do set "REQ_DATE=%%~tI"
    for %%I in ("%MARKER%") do set "MARK_DATE=%%~tI"
    if "!REQ_DATE!" GTR "!MARK_DATE!" set "NEED_INSTALL=1"
)

if "%NEED_INSTALL%"=="1" (
    echo [INFO] Installiere Abhaengigkeiten aus requirements.txt ...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    "%VENV_PYTHON%" -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo [ERROR] pip install ist fehlgeschlagen.
        pause
        exit /b 1
    )
    > "%MARKER%" echo installed
)

rem --- Start the UI ---
cd /d "%ROOT_DIR%"
"%VENV_PYTHON%" "%ROOT_DIR%\ui.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [WARN] ui.py endete mit Code %RC%.
    pause
)
exit /b %RC%
