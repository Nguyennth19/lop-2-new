@echo off
setlocal
cd /d "%~dp0"
if exist "all-in-one-1406\.venv\Scripts\python.exe" (set "PYEXE=all-in-one-1406\.venv\Scripts\python.exe") else (set "PYEXE=python")
"%PYEXE%" "all-in-one-1406\windows_runner.py" --input-dir PRIVATE_INPUTS --state-dir LOCAL_STATE --mode preflight --status-file LOCAL_STATE\summary.json
pause