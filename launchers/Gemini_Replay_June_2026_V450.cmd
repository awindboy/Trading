@echo off
setlocal
cd /d "%~dp0.."

set "DATASET=output\datasets\GOLD_M1_2023-12-01_2026-08-12.npz"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set "RUN_ID=gemini_v476_june2026_delivery_local_sl_lite_%%i"

echo.
echo  ======================================================================
echo    MENTOR AI REPLAY V4.76  ^|  GOLD  ^|  JUNE 2026  ^|  DELIVERY LOCAL SL
echo  ======================================================================
echo    Model      : gemini-3.5-flash-lite / low / ultra-high
echo    H1 history : 2023-12-01 onward; old M5/M15 cannot be external TP
echo    Replay     : 2026-06-01 00:00 UTC - 2026-07-01 00:00 UTC
echo    Run ID     : %RUN_ID%
echo  ======================================================================
echo.

if not exist "%DATASET%" (
  echo [BLOCKED] Combined long-history dataset is missing: %DATASET%
  echo Run scripts\merge_m1_npz.py before starting this replay.
  goto :failed
)

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 -m py_compile scripts\mentor_ai_replay_v4.py scripts\mentor_replay_v4_core.py
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py run --run-id "%RUN_ID%" --decision-provider gemini --dataset "%DATASET%" --warmup-start 2023-12-01T00:00:00Z --start 2026-06-01T00:00:00Z --end 2026-07-01T00:00:00Z --follow-through-days 10 --gemini-model gemini-3.5-flash-lite --gemini-thinking-level low --gemini-media-resolution MEDIA_RESOLUTION_ULTRA_HIGH --maximum-api-calls-per-run 400 --maximum-tokens-per-run 5000000 --diagnostic-bypass-sol-gate
if errorlevel 1 goto :failed

echo.
echo [COMPLETE] output\mentor_ai_replay_v4_runs\%RUN_ID%
pause
exit /b 0

:failed
echo.
echo [PAUSED OR FAILED] Run ID: %RUN_ID%
pause
exit /b 1
