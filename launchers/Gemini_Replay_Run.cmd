@echo off
setlocal
cd /d "%~dp0.."
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set RUN_ID=gemini_v4_aug21_%%i

echo.
echo  ================================================================
echo    MENTOR AI REPLAY V4  ^|  GEMINI AUG 21
echo  ================================================================
echo    PLAN -^> child touch -^> TRIGGER_WATCH -^> local execution
echo    Sol parity gate is required before any Gemini request.
echo    Run ID: %RUN_ID%
echo  ================================================================
echo.

call :local_checks || goto :failed_local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py run --run-id "%RUN_ID%" --decision-provider gemini --benchmark-truth "output\mentor_aug21_truth_v3\funnel_truth.json" --start 2025-08-21T00:00:00Z --end 2025-08-22T00:00:00Z
if errorlevel 1 goto :failed
call :compare || goto :failed
echo.
echo  [COMPLETE] output\mentor_ai_replay_v4_runs\%RUN_ID%
pause
exit /b 0

:local_checks
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\test_mentor_ai_replay_v4.py || exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight || exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py audit-truth --truth "output\mentor_aug21_truth_v3\funnel_truth.json" || exit /b 1
exit /b 0

:compare
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare --candidate "output\mentor_ai_replay_v4_runs\%RUN_ID%\trades.csv" --truth "output\mentor_aug21_truth_v3\trades.csv" --start 2025-08-21T00:00:00Z --end 2025-08-22T00:00:00Z --output "output\mentor_ai_replay_v4_runs\%RUN_ID%\parity.csv" || exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare-funnel --ledger "output\mentor_ai_replay_v4_runs\%RUN_ID%\decision_ledger.jsonl" --truth "output\mentor_aug21_truth_v3\funnel_truth.json" --output "output\mentor_ai_replay_v4_runs\%RUN_ID%\funnel_parity.csv" || exit /b 1
exit /b 0

:failed_local
echo.
echo  [BLOCKED BEFORE API] V4 scripted regression or preflight failed.
pause
exit /b 1

:failed
echo.
echo  [FAILED] No reproducibility claim was made.
pause
exit /b 1
