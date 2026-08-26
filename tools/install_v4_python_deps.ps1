param(
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $PSScriptRoot "..\requirements-v4-tournament.txt")
& $Python (Join-Path $PSScriptRoot "check_cuda.py")
Write-Host "V4 CORE DEPENDENCIES PASS"
