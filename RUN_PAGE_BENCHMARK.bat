@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "ROOT=%CD%"
set "PY=%ROOT%\all-in-one-1406\.venv\Scripts\python.exe"
set "MODEL=qwen2.5vl:7b"
if not "%~1"=="" set "MODEL=%~1"
if not exist "%PY%" (echo Missing Python venv & pause & exit /b 2)
echo V2.4 experimental page benchmark. No change to production checkpoint.
echo Only run when RUN_ALL is NOT running. Model: %MODEL%
"%PY%" "%ROOT%\all-in-one-1406\page_benchmark.py" --input-dir "%ROOT%\PRIVATE_INPUTS" --output-dir "%ROOT%\PAGE_BENCHMARK\results" --model "%MODEL%" --max-ids 3
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Page benchmark failed with error %RC%
pause
exit /b %RC%
