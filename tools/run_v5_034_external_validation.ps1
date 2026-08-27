param(
  [string]$Python = "python",
  [string]$DataMap = ".\config\v5_034_external_data_map.local.json",
  [string]$OutDir = ".\v5_034_external_results"
)
$ErrorActionPreference = "Stop"
& $Python ".\scripts\v5_034_first_cross_validation.py" --data-map $DataMap --out-dir $OutDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "V5-034 external validation replay complete."
Write-Host "Summary: $OutDir\V5_034_VALIDATION_SUMMARY.json"
