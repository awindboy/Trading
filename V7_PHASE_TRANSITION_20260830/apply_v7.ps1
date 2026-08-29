param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$ExpectedHead = "102791741620ca6cffe061f077d83116a1e46c09"
$ActualHead = (git rev-parse HEAD).Trim()
if ($ActualHead -ne $ExpectedHead) {
    throw "FAIL-CLOSED: expected HEAD $ExpectedHead but found $ActualHead"
}

$status = git status --porcelain
# if ($status) {
#     throw "FAIL-CLOSED: working tree is not clean. Commit/stash local changes first."
# }

function Assert-Blob([string]$Path, [string]$Expected) {
    $Actual = (git hash-object -- $Path).Trim()
    if ($Actual -ne $Expected) {
        throw "FAIL-CLOSED: unexpected blob for $Path. Expected $Expected, got $Actual"
    }
}

Assert-Blob "AGENTS.md" "4c632516dd59f0da4c58d5b4f0f1c1a8a83ad3eb"
Assert-Blob "docs/ea/HANDOFF.md" "e4e6b7d08df3fa46fc8467141e07620359e73001"
Assert-Blob "docs/ea/DECISIONS.md" "629ccad5bb999e6ed6cc686a5da5c4eb7b2e2bf6"
Assert-Blob "docs/ea/v6/AGENTS_V6.md" "2feeefb3a8ed035a43a658e3cebb6dbe2b0d5aa8"
Assert-Blob "docs/ea/v6/HANDOFF_V6.md" "6bd23fd18d0d468cdadd20d52c10bd1241cc74d7"
Assert-Blob "docs/ea/v6/BACKLOG_V6.md" "996ca8c1126da80afec2540932a4c0994b649b0c"

$PkgRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $PkgRoot "payload"
$Patches = Join-Path $PkgRoot "patches"

# 1) Replace active HANDOFF completely.
Copy-Item (Join-Path $Payload "docs/ea/HANDOFF.md") "docs/ea/HANDOFF.md" -Force

# 2) Copy new V7 and V6-final files/ledgers.
New-Item -ItemType Directory -Force -Path "docs/ea/v7" | Out-Null
New-Item -ItemType Directory -Force -Path "ledgers/v7" | Out-Null

Get-ChildItem (Join-Path $Payload "docs/ea/v7") -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path "docs/ea/v7" $_.Name) -Force
}
Copy-Item (Join-Path $Payload "docs/ea/v6/V6_FINAL_VALIDATION_AND_CLOSE.md") "docs/ea/v6/V6_FINAL_VALIDATION_AND_CLOSE.md" -Force
Get-ChildItem (Join-Path $Payload "ledgers/v7") -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path "ledgers/v7" $_.Name) -Force
}

# 3) Replace stale root V6 active routing block with V7 active + V6 closed.
$agents = [System.IO.File]::ReadAllText((Resolve-Path "AGENTS.md"))
$pattern = '(?s)\A> \*\*V6 ACTIVE ROUTING.*?GOLD# 2021 remains untouched\.\r?\n\r?\n'
$newHeader = [System.IO.File]::ReadAllText((Join-Path $Patches "AGENTS_NEW_HEADER.md"))
if ($agents -notmatch $pattern) {
    throw "FAIL-CLOSED: could not locate expected root V6 routing header."
}
$agents = [regex]::Replace($agents, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $newHeader }, 1)
[System.IO.File]::WriteAllText((Resolve-Path "AGENTS.md"), $agents, [System.Text.UTF8Encoding]::new($false))

# 4) Prepend V6 closed banner to historical V6 routing docs.
$banner = [System.IO.File]::ReadAllText((Join-Path $Patches "V6_CLOSED_BANNER.md"))
foreach ($p in @("docs/ea/v6/AGENTS_V6.md","docs/ea/v6/HANDOFF_V6.md","docs/ea/v6/BACKLOG_V6.md")) {
    $txt = [System.IO.File]::ReadAllText((Resolve-Path $p))
    if ($txt -notmatch 'V6 CLOSED — 2026-08-30') {
        [System.IO.File]::WriteAllText((Resolve-Path $p), $banner + $txt, [System.Text.UTF8Encoding]::new($false))
    }
}

# 5) Append global decisions once.
$decPath = Resolve-Path "docs/ea/DECISIONS.md"
$dec = [System.IO.File]::ReadAllText($decPath)
if ($dec -match 'D073-D080 — V6 close / V7 phase transition') {
    throw "FAIL-CLOSED: V7 global decision block already exists."
}
$append = [System.IO.File]::ReadAllText((Join-Path $Patches "DECISIONS_APPEND.md"))
[System.IO.File]::WriteAllText($decPath, $dec + $append, [System.Text.UTF8Encoding]::new($false))

Write-Host ""
Write-Host "V7 transition applied successfully."
Write-Host "Expected next steps:"
Write-Host "  git diff --check"
Write-Host "  git diff --stat"
Write-Host "  review docs/ea/HANDOFF.md and docs/ea/v7/"
Write-Host "  git add AGENTS.md docs/ea ledgers/v7"
Write-Host "  git commit -m 'V7 Double-B context KTR research transition'"
Write-Host "  git push"
