@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "APP=%CD%\all-in-one-1406"
set "INPUT=%CD%\PRIVATE_INPUTS"
set "STATE=%CD%\LOCAL_STATE"
set "BACKUP=%CD%\BACKUPS"
set "MODEL=qwen2.5vl:7b"
if defined LOP2_LOCAL_MODEL set "MODEL=%LOP2_LOCAL_MODEL%"
if not exist "%APP%\.venv\Scripts\python.exe" (
  echo Missing Python environment; run CHECK_ONLY.bat first.
  pause & exit /b 2
)
if not exist "%INPUT%\SOURCE_1406.csv" (
  echo Missing source manifest. Do not delete PRIVATE_INPUTS.
  pause & exit /b 3
)
echo [CANARY RETRY] Reusing stored Vision checkpoint when available.
echo [IMPORTANT] Close Excel records.csv before continuing.
"%APP%\.venv\Scripts\python.exe" "%APP%\windows_runner.py" --input-dir "%INPUT%" --state-dir "%STATE%" --backup-dir "%BACKUP%" --mode canary --canary-id SGK_B001_K1_E01 --model "%MODEL%" --max-items 1 --chunk-size 1 --retry-exceptions --status-file "%STATE%\summary.json"
set "RC=%ERRORLEVEL%"
echo.
echo Result code: %RC%. Check LOCAL_STATE\records.csv (open a COPY, not the live file).
pause
exit /b %RC%
