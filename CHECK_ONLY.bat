@echo off
setlocal
cd /d "%~dp0"
set "APP=%~dp0all-in-one-1406"
where py >nul 2>&1
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
if not exist "%APP%\.venv\Scripts\python.exe" %PYTHON% -m venv "%APP%\.venv"
if not exist "%APP%\.venv\Scripts\python.exe" (echo Python 3.11 or newer is required. & pause & exit /b 2)
"%APP%\.venv\Scripts\python.exe" -m pip install -r "%APP%\requirements-windows.txt"
if errorlevel 1 (echo Dependency installation failed. & pause & exit /b 3)
"%APP%\.venv\Scripts\python.exe" "%APP%\windows_runner.py" --input-dir "%~dp0PRIVATE_INPUTS" --state-dir "%~dp0LOCAL_STATE" --mode preflight --status-file "%~dp0LOCAL_STATE\summary.json"
pause