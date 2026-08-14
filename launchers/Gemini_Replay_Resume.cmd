@echo off
setlocal
cd /d "%~dp0.."
if not "%~1"=="" (
  set "SOURCE_RUN=%~1"
) else (
  for /f "delims=" %%i in ('python scripts\mentor_ai_replay_v4.py latest-resume-source') do set "SOURCE_RUN=%%i"
)
if "%SOURCE_RUN%"=="" goto :missing

echo [LOCAL AUDIT] V4 scripted regression and preflight...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\test_mentor_ai_replay_v4.py
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight
if errorlevel 1 goto :failed
echo [RESUME] %SOURCE_RUN%
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py run --run-id "%SOURCE_RUN%" --resume
if errorlevel 1 goto :failed
echo [COMPLETE] output\mentor_ai_replay_v4_runs\%SOURCE_RUN%
pause
exit /b 0

:missing
echo [FAILED] No incomplete V4 run was found.
pause
exit /b 1

:failed
echo [FAILED] Resume stopped without a reproducibility claim.
pause
exit /b 1
