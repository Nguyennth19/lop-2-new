@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "APP=%~dp0all-in-one-1406"
set "STATE=%~dp0LOCAL_STATE"
set "MODEL=qwen2.5vl:7b"
if defined LOP2_LOCAL_MODEL set "MODEL=%LOP2_LOCAL_MODEL%"
where py >nul 2>&1
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
if exist "%APP%\.venv\Scripts\python.exe" (
  set "PYEXE=%APP%\.venv\Scripts\python.exe"
) else (
  set "PYEXE="
)
if defined PYEXE (
  "%PYEXE%" "%APP%\pc_readiness.py" --root "%CD%" --model "%MODEL%" --report "%STATE%\pc_readiness.json"
) else (
  %PYTHON% "%APP%\pc_readiness.py" --root "%CD%" --model "%MODEL%" --report "%STATE%\pc_readiness.json"
)
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo NOT READY. Read LOCAL_STATE\pc_readiness.json and resolve missing requirements.
  echo Review the checks above. Only install Ollama if the ollama check is BLOCKED.
) else (
  echo.
  echo PC READY for source verification and one-item canary.
  echo NEXT: CHECK_ONLY.bat, then RUN_CANARY.bat.
)
pause
exit /b %RC%