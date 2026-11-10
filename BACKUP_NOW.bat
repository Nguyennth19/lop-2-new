@echo off
setlocal
cd /d "%~dp0"
if exist "all-in-one-1406\.venv\Scripts\python.exe" (set "PYEXE=all-in-one-1406\.venv\Scripts\python.exe") else (set "PYEXE=python")
"%PYEXE%" "all-in-one-1406\backup_tool.py" --state-dir LOCAL_STATE --backup-dir BACKUPS --campaign lop2-local-1406-v1
pause