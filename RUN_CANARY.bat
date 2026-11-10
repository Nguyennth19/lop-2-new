@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "APP=%~dp0all-in-one-1406"
set "INPUT=%~dp0PRIVATE_INPUTS"
set "STATE=%~dp0LOCAL_STATE"
set "BACKUP=%~dp0BACKUPS"
set "MODEL=qwen2.5vl:7b"
if defined LOP2_LOCAL_MODEL set "MODEL=%LOP2_LOCAL_MODEL%"
if not exist "%APP%\.venv\Scripts\python.exe" (
  echo ERROR: first run CHECK_ONLY.bat to set up Python dependencies.
  pause & exit /b 2
)
"%APP%\.venv\Scripts\python.exe" "%APP%\pc_readiness.py" --root "%~dp0" --model "%MODEL%" --report "%STATE%\pc_readiness.json"
if errorlevel 1 (echo PC READINESS FAILED. & pause & exit /b 2)
"%APP%\.venv\Scripts\python.exe" "%APP%\windows_runner.py" --input-dir "%INPUT%" --state-dir "%STATE%" --backup-dir "%BACKUP%" --mode preflight --status-file "%STATE%\summary.json"
if errorlevel 1 (echo SOURCE PREFLIGHT FAILED. & pause & exit /b 3)
echo.
echo Running ONE REAL-SOURCE canary: SGK_B001_K1_E01
"%APP%\.venv\Scripts\python.exe" "%APP%\windows_runner.py" --input-dir "%INPUT%" --state-dir "%STATE%" --backup-dir "%BACKUP%" --mode canary --canary-id SGK_B001_K1_E01 --model "%MODEL%" --max-items 1 --chunk-size 1 --status-file "%STATE%\summary.json"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
  echo.
  echo Canary processing completed. It may still be EXCEPTION or DRAFT_REVIEW_REQUIRED.
  echo Inspect LOCAL_STATE\records.csv and the saved original evidence before RUN_ALL.bat.
) else (
  echo Canary failed; its audit checkpoint is preserved. Do not start RUN_ALL.bat yet.
)
pause
exit /b %RC%