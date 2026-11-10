@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "ROOT=%CD%"
set "PY=%ROOT%\all-in-one-1406\.venv\Scripts\python.exe"
if not exist "%PY%" (
 echo Missing virtual environment: %PY%
 pause
 exit /b 2
)
if not exist "%ROOT%\PRIVATE_INPUTS\SOURCE_1406.csv" (
 echo Missing PRIVATE_INPUTS\SOURCE_1406.csv
 pause
 exit /b 2
)
echo V2.4A: read-only mapping inventory - no Ollama calls, no SQLite edits.
"%PY%" "%ROOT%\all-in-one-1406\page_inventory.py" --input-dir "%ROOT%\PRIVATE_INPUTS" --output "%ROOT%\PAGE_BENCHMARK\page_inventory.json" --verify-source-hashes
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" echo Inventory saved to PAGE_BENCHMARK\page_inventory.json
if not "%RC%"=="0" echo Inventory failed with error %RC%
pause
exit /b %RC%
