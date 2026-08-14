@echo off
setlocal
cd /d "%~dp0.."

set "DATASET=output\datasets\GOLD_M1_2023-12-01_2026-08-12.npz"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set "RUN_ID=gemini_v475_july2026_objective_promotion_lite_%%i"

echo.
echo  ======================================================================
echo    MENTOR AI REPLAY V4.75  ^|  GOLD  ^|  JULY 2026  ^|  OBJECTIVE PROMOTION
echo  ======================================================================
echo    Model      : gemini-3.5-flash-lite / low / ultra-high
echo    Replay     : 2026-07-01 00:00 UTC - 2026-08-01 00:00 UTC
echo    Warm-up    : 2023-12-01 00:00 UTC
echo    Run ID     : %RUN_ID%
echo  ======================================================================
echo.

if not exist "%DATASET%" (
  echo [BLOCKED] Combined long-history dataset is missing: %DATASET%
  echo A 2026-only MT5 export must not be written under the combined archive name.
  goto :failed_data
) else (
  echo [1/3] Dataset already exists: %DATASET%
)

echo [2/3] Running local compile and preflight checks...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 -m py_compile scripts\mentor_ai_replay_v4.py scripts\mentor_replay_v4_core.py scripts\export_mt5_m1_dataset.py
if errorlevel 1 goto :failed_local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight
if errorlevel 1 goto :failed_local

echo [3/3] Starting month replay. A quota or budget pause can be resumed later.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py run --run-id "%RUN_ID%" --decision-provider gemini --dataset "%DATASET%" --warmup-start 2023-12-01T00:00:00Z --start 2026-07-01T00:00:00Z --end 2026-08-01T00:00:00Z --follow-through-days 10 --gemini-model gemini-3.5-flash-lite --gemini-thinking-level low --gemini-media-resolution MEDIA_RESOLUTION_ULTRA_HIGH --maximum-api-calls-per-run 400 --maximum-tokens-per-run 5000000 --diagnostic-bypass-sol-gate
if errorlevel 1 goto :paused_or_failed

echo.
echo [COMPLETE] output\mentor_ai_replay_v4_runs\%RUN_ID%
pause
exit /b 0

:failed_data
echo.
echo [FAILED] Build the combined archive with scripts\merge_m1_npz.py first.
pause
exit /b 1

:failed_local
echo.
echo [BLOCKED BEFORE API] Local validation failed; no Gemini request was sent.
pause
exit /b 1

:paused_or_failed
echo.
echo [PAUSED OR FAILED] Run ID: %RUN_ID%
echo To resume this exact run later:
echo   launchers\Gemini_Replay_Resume.cmd %RUN_ID%
pause
exit /b 1
