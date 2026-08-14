@echo off
setlocal
cd /d "%~dp0.."

set "PYTHON_EXE="
for %%P in (python.exe py.exe) do (
  if not defined PYTHON_EXE where %%P >nul 2>nul && set "PYTHON_EXE=%%P"
)

if not defined PYTHON_EXE (
  echo [FAILED] Python was not found.
  pause
  exit /b 1
)

echo ================================================================
echo   MENTOR AI LIVE V4  ^|  MT5 CLOSED-M1 SHADOW OBSERVER
echo ================================================================
echo   Strategy authority : AGENTS.md
echo   Execution           : SHADOW ONLY ^(no broker orders^)
echo   Waiting             : Local event monitor ^(zero API tokens^)
echo   PLAN model          : Lite continuation / Flash owner authority
echo   TRIGGER model       : Gemini Flash ^(no Lite downgrade^)
echo   Quota handling      : State frozen, zero-token retry wait
echo ================================================================
echo.

if /i "%~1"=="preflight" (
  %PYTHON_EXE% scripts\mentor_ai_live_v4.py --preflight-only
) else (
  %PYTHON_EXE% scripts\mentor_ai_live_v4.py
)

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo [FAILED] Live shadow observer stopped with code %EXIT_CODE%.
  pause
)
exit /b %EXIT_CODE%
