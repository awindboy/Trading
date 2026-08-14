@echo off
setlocal
cd /d "%~dp0.."

echo.
echo  ======================================================================
echo    MENTOR AI REPLAY  ^|  ADD OR REPLACE GEMINI KEY SLOT 2
echo  ======================================================================
echo    The key is entered invisibly and stays only in the local secret file.
echo  ======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py keys add --slot 2
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py keys status
echo.
echo [READY] Gemini key slot 2 is configured.
echo [READY] HTTP 429 on one paid-project key will switch to the other slot automatically.
echo [INFO]  Logs expose slot numbers only; API key values are never printed.
pause
exit /b 0

:failed
echo.
echo [FAILED] The second key was not saved.
pause
exit /b 1
