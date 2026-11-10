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
if not exist "%INPUT%\SOURCE_1406.csv" (
  echo ERROR: Missing PRIVATE_INPUTS\SOURCE_1406.csv
  echo Extract the separate private source bundle beside RUN_ALL.bat.
  pause & exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
if not exist "%APP%\.venv\Scripts\python.exe" (
  echo Installing isolated Python environment...
  %PYTHON% -m venv "%APP%\.venv" || (echo Python 3.11 or newer is required. & pause & exit /b 2)
)
set "PYEXE=%APP%\.venv\Scripts\python.exe"
"%PYEXE%" -m pip install -r "%APP%\requirements-windows.txt" || (echo ERROR installing Python dependencies. & pause & exit /b 3)
echo Checking all 1406 candidate IDs and four original PDF hashes...
"%PYEXE%" "%APP%\windows_runner.py" --input-dir "%INPUT%" --state-dir "%STATE%" --backup-dir "%BACKUP%" --status-file "%STATE%\summary.json" --mode preflight
if errorlevel 1 (echo PRE-FLIGHT FAILED. No work started. & pause & exit /b 4)
echo.
echo Checking locally installed Ollama vision model: %MODEL%
echo For first setup install Ollama and run: ollama pull %MODEL%
echo No API key or paid cloud storage is needed.
"%PYEXE%" "%APP%\windows_runner.py" --input-dir "%INPUT%" --state-dir "%STATE%" --backup-dir "%BACKUP%" --status-file "%STATE%\summary.json" --mode run --model "%MODEL%" --chunk-size 5 --max-items 1406
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Run stopped. Local state remains saved; rerun RUN_ALL.bat to resume.
if "%RC%"=="0" echo Done traversing input. Inspect LOCAL_STATE\summary.json; draft results are not approved for release.
pause
exit /b %RC%