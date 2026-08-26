param(
  [string]$Python = "python",
  [string]$Prepared = ".\v4_001_prepared",
  [string]$R1Out = ".\v4_001_r1_stage_a",
  [string]$R2Out = ".\v4_001_r2_jepa_stage_a"
)
$ErrorActionPreference = "Stop"
& $Python .\tools\check_cuda.py
foreach ($p in @($R1Out,$R2Out)) {
  if (Test-Path $p) { throw "FAIL-CLOSED: output directory already exists: $p. Move/archive it before an official run." }
}
Write-Host "=== R1 supervised CausalPatchPolicy ==="
& $Python .\scripts\v4_001_stage_a.py `
  --prepared $Prepared `
  --config .\config\v4_001_baseline.json `
  --out $R1Out `
  --batch-size 32 `
  --effective-batch-size 256 `
  --workers 0
& $Python .\scripts\v4_001_stage_a_verdict.py --stage-a $R1Out
& $Python .\scripts\v4_001_collect_stage_a_results.py --stage-a $R1Out --out .\V4_001_R1_RESULT_BUNDLE.zip
Write-Host "=== R2 self-supervised MarketJEPA + linear probe ==="
& $Python .\scripts\v4_001_jepa_stage_a.py `
  --prepared $Prepared `
  --base-config .\config\v4_001_baseline.json `
  --jepa-config .\config\v4_001_jepa.json `
  --out $R2Out `
  --pretrain-batch-size 8 `
  --encode-batch-size 32 `
  --workers 0
& $Python .\scripts\v4_001_stage_a_verdict.py --stage-a $R2Out
& $Python .\scripts\v4_001_collect_stage_a_results.py --stage-a $R2Out --out .\V4_001_R2_RESULT_BUNDLE.zip
& $Python .\scripts\v4_001_tournament_summary.py --r1 $R1Out --r2 $R2Out --out .\V4_001_TOURNAMENT_SUMMARY.json
Write-Host "TOURNAMENT RUN COMPLETE"
Write-Host "Upload: V4_001_R1_RESULT_BUNDLE.zip, V4_001_R2_RESULT_BUNDLE.zip, V4_001_TOURNAMENT_SUMMARY.json"
