@echo off
setlocal
cd /d "%~dp0.."
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set RUN_ID=sol_v4_aug21_%%i
set PACKET_ID=%RUN_ID%_fixed_plan

echo.
echo  ================================================================
echo    MENTOR AI REPLAY V4  ^|  SOL VALIDATION AUG 21
echo  ================================================================
echo    Future-blind closed-loop run. Gemini is not called.
echo    A Gemini gate is written only after full causal parity.
echo    Run ID: %RUN_ID%
echo  ================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\test_mentor_ai_replay_v4.py
if errorlevel 1 goto :failed_local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight
if errorlevel 1 goto :failed_local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py audit-truth --truth "output\mentor_aug21_truth_v3\funnel_truth.json"
if errorlevel 1 goto :failed_local
echo [FIXED PACKET] Sol PLAN at 2025-08-21 17:00 UTC...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py fixed-packet --phase PLAN --as-of 2025-08-21T17:00:00Z --packet-id "%PACKET_ID%" --decision-provider codex-cli
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare-fixed-plan --state "output\mentor_ai_replay_v4_fixed_packets\%PACKET_ID%\state.json" --truth "output\mentor_aug21_truth_v3\funnel_truth.json" --trade-id AG21-001 --output "output\mentor_ai_replay_v4_fixed_packets\%PACKET_ID%\map_parity.json"
if errorlevel 1 goto :failed
echo [CLOSED LOOP] Starting the full future-blind day...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py run --run-id "%RUN_ID%" --decision-provider codex-cli --start 2025-08-21T00:00:00Z --end 2025-08-22T00:00:00Z
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare --candidate "output\mentor_ai_replay_v4_runs\%RUN_ID%\trades.csv" --truth "output\mentor_aug21_truth_v3\trades.csv" --start 2025-08-21T00:00:00Z --end 2025-08-22T00:00:00Z --output "output\mentor_ai_replay_v4_runs\%RUN_ID%\parity.csv"
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare-funnel --ledger "output\mentor_ai_replay_v4_runs\%RUN_ID%\decision_ledger.jsonl" --truth "output\mentor_aug21_truth_v3\funnel_truth.json" --output "output\mentor_ai_replay_v4_runs\%RUN_ID%\funnel_parity.csv" --write-sol-gate --trade-parity "output\mentor_ai_replay_v4_runs\%RUN_ID%\parity.csv"
if errorlevel 1 goto :failed
echo.
echo  [SOL GATE READY] Gemini_Replay_Run.cmd may now use the same period.
pause
exit /b 0

:failed_local
echo.
echo  [BLOCKED] Local V4 checks failed before Sol.
pause
exit /b 1

:failed
echo.
echo  [FAILED] Sol did not earn a Gemini validation gate.
pause
exit /b 1
