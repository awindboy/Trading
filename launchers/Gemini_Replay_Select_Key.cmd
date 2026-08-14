@echo off
setlocal
cd /d "%~dp0.."

if "%~1"=="" (
  set /p SLOT=Select Gemini API key slot [1 or 2]: 
) else (
  set "SLOT=%~1"
)

if not "%SLOT%"=="1" if not "%SLOT%"=="2" (
  echo [FAILED] Slot must be 1 or 2.
  pause
  exit /b 2
)

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py keys select --slot %SLOT%
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight --api-key-slot %SLOT%
if errorlevel 1 goto :failed
echo.
echo [READY] Future new runs will use key slot %SLOT%.
pause
exit /b 0

:failed
echo.
echo [FAILED] Key slot selection failed.
pause
exit /b 1
