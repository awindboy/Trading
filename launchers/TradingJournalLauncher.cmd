@echo off
setlocal
chcp 65001 >nul
title XM MT5 Trading Journal Command Center
color 0B
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\run_python_sandbox.ps1" "%~dp0..\scripts\trading_journal_launcher.py" %*
echo.
echo Trading Journal Command Center has been closed.
echo Press any key to exit this window.
pause >nul
