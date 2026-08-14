@echo off
setlocal
cd /d "%~dp0.."
echo.
echo  ================================================================
echo    MENTOR AI REPLAY V4  ^|  GEMINI SETUP
echo  ================================================================
echo    API key stays in data\mentor_ai_replay_secret.json.
echo  ================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py setup
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight
if errorlevel 1 goto :failed
echo.
echo  [READY] V4 setup and preflight passed.
pause
exit /b 0

:failed
echo.
echo  [FAILED] Setup stopped before replay.
pause
exit /b 1
