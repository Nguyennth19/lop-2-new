@echo off
setlocal
cd /d "%~dp0"
echo IMPORTANT: close any RUN_ALL window before restoring.
echo Existing LOCAL_STATE will be preserved in a timestamped sibling folder.
choice /m "Restore BACKUPS to LOCAL_STATE?"
if errorlevel 2 exit /b 1
if exist "all-in-one-1406\.venv\Scripts\python.exe" (set "PYEXE=all-in-one-1406\.venv\Scripts\python.exe") else (set "PYEXE=python")
"%PYEXE%" "all-in-one-1406\restore_tool.py" --state-dir LOCAL_STATE --backup-dir BACKUPS --confirm
pause