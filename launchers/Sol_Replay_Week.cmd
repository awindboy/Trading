@echo off
setlocal
cd /d "%~dp0.."
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set RUN_ID=sol_v4_aug18_22_%%i
echo [V4] Sol closed-loop validation: Aug 18-22.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\test_mentor_ai_replay_v4.py || goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py preflight || goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py audit-truth --truth "output\mentor_aug18_22_truth_v1\funnel_truth.json" || goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py run --run-id "%RUN_ID%" --decision-provider codex-cli --start 2025-08-18T00:00:00Z --end 2025-08-23T00:00:00Z || goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare --candidate "output\mentor_ai_replay_v4_runs\%RUN_ID%\trades.csv" --truth "output\mentor_aug18_22_truth_v1\trades.csv" --start 2025-08-18T00:00:00Z --end 2025-08-23T00:00:00Z --output "output\mentor_ai_replay_v4_runs\%RUN_ID%\parity.csv" || goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_sandbox.ps1 scripts\mentor_ai_replay_v4.py compare-funnel --ledger "output\mentor_ai_replay_v4_runs\%RUN_ID%\decision_ledger.jsonl" --truth "output\mentor_aug18_22_truth_v1\funnel_truth.json" --output "output\mentor_ai_replay_v4_runs\%RUN_ID%\funnel_parity.csv" --write-sol-gate --trade-parity "output\mentor_ai_replay_v4_runs\%RUN_ID%\parity.csv" || goto :failed
echo [SOL GATE READY] Gemini_Replay_Week.cmd may now run.
pause
exit /b 0
:failed
echo [FAILED] Sol weekly validation did not pass.
pause
exit /b 1
