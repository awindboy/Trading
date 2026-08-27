param(
  [string]$Python = "python",
  [string]$DataMap = ".\config\v5_034_external_data_map.local.json",
  [string]$OutDir = ".\v5_034_external_results"
)
$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Audit = Join-Path $OutDir "V5_034_INPUT_AUDIT.json"

# Phase 1: freeze raw identities and data-quality audit before outcome computation.
& $Python ".\scripts\v5_034_first_cross_validation.py" `
  --data-map $DataMap `
  --out-dir $OutDir `
  --preflight-only
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Phase 2: verify the frozen raw identities, then run the immutable candidate and gates.
& $Python ".\scripts\v5_034_first_cross_validation.py" `
  --data-map $DataMap `
  --out-dir $OutDir `
  --expected-audit $Audit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "V5-034 external validation replay complete."
Write-Host "Input audit: $Audit"
Write-Host "Summary: $OutDir\V5_034_VALIDATION_SUMMARY.json"
