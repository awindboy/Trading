$ErrorActionPreference = 'Stop'

$ExpectedHead = '03d0e893d74e23779a9188e9e91fd0659837dc03'
$ExpectedBlobs = @{
    'AGENTS.md' = '5096c764164e694c3a22fb86cd3012a4374fc094'
    'docs/ea/HANDOFF.md' = 'e9d4afea71f715b1bce583832791023b109080a0'
    'docs/ea/v6/AGENTS_V6.md' = 'bf8f23d2d4c3654970859acd0f40b43fd090cc55'
    'docs/ea/v6/BACKLOG_V6.md' = '61bd96dc6e2b4f8a0b18f5c57a6d6396cf97573f'
    'docs/ea/v6/DECISIONS_V6.md' = '8b0917238b283d3537fe9256bfedfa9e4255c4a5'
    'docs/ea/v6/HANDOFF_V6.md' = '589e7fa0c9b94bcc334df2dfecc54dfe4c22887f'
    'docs/ea/v6/RESEARCH_STATE_V6.md' = '4dbf9c870b19e97623740c020691526a46c7724e'
    'docs/ea/v6/V6_000_RESEARCH_CONTRACT.md' = '43d9e0d725f65fbf16e130b8c20a6e794e2aa4cb'
    'docs/ea/v6/V6_001A_CONTEXT_INFORMATION_AUDIT.md' = '2d1c70baebfb3779368c5356e2d29884a36c10cc'
    'docs/ea/v6/V6_FAILURE_MAP_V3_V4_V5.md' = 'ae35c231739ea6c1bcfe947a229ba186f40134d8'
    'docs/ea/v6/V6_NEXT_SESSION_OPERATING_PROTOCOL.md' = '46655e68d7c632d880d5a729aba6f74e18b921af'
}

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

# Find the repository by walking upward from the script location.
# Do not parse `git rev-parse --show-toplevel` output because Windows PowerShell
# can mojibake Korean path names from native-command output (e.g. 문서 -> 臾몄꽌).
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cursor = [System.IO.DirectoryInfo]::new($PackRoot)
$RepoRoot = $null

while ($null -ne $Cursor) {
    $Candidate = $Cursor.FullName
    $Inside = (& git -C $Candidate rev-parse --is-inside-work-tree 2>$null)
    if ($LASTEXITCODE -eq 0 -and ($Inside | Select-Object -First 1).Trim() -eq 'true') {
        $RepoRoot = $Candidate
        break
    }
    $Cursor = $Cursor.Parent
}

if (-not $RepoRoot) {
    Fail 'Could not find a Git repository by walking upward from the apply script.'
}

Set-Location -LiteralPath $RepoRoot

$Head = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($Head -ne $ExpectedHead) {
    Fail "HEAD mismatch. Expected $ExpectedHead, got $Head. Rebuild the pack from latest GitHub state."
}

$Dirty = git status --porcelain
if ($Dirty) {
    Fail "Working tree is not clean. Commit/stash local changes before applying this pack.`n$Dirty"
}

# Compare committed blobs, not working-tree bytes, so core.autocrlf cannot create false mismatches.
foreach ($Entry in $ExpectedBlobs.GetEnumerator()) {
    $Path = $Entry.Key
    $ExpectedBlob = $Entry.Value
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Missing expected file: $Path"
    }
    $ActualBlob = (git rev-parse "HEAD:$Path").Trim()
    if ($ActualBlob -ne $ExpectedBlob) {
        Fail "Committed blob mismatch for $Path. Expected $ExpectedBlob, got $ActualBlob."
    }
}

$NewFiles = @(
    'docs/ea/v6/V6_000A_V3_V5_LINEAGE_AND_FAILURE_SYNTHESIS.md',
    'docs/ea/v6/V6_001_CONTEXT_MEASUREMENT_REGISTRY.md'
)
foreach ($Path in $NewFiles) {
    if (Test-Path -LiteralPath $Path) {
        Fail "New-file collision: $Path already exists."
    }
}

$PayloadRoot = Join-Path $PackRoot 'payload'
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$AgentsPath = Join-Path $RepoRoot 'AGENTS.md'
$RootHandoffPath = Join-Path $RepoRoot 'docs/ea/HANDOFF.md'
$AgentsText = [System.IO.File]::ReadAllText($AgentsPath, [System.Text.Encoding]::UTF8)
$HandoffText = [System.IO.File]::ReadAllText($RootHandoffPath, [System.Text.Encoding]::UTF8)

$AgentsEol = if ($AgentsText.Contains("`r`n")) { "`r`n" } else { "`n" }
$HandoffEol = if ($HandoffText.Contains("`r`n")) { "`r`n" } else { "`n" }

$OldAgentsLines = @(
    '> **V6 ACTIVE ROUTING — 2026-08-28 / EVENT-CONDITIONED GENERALIZATION RESEARCH**  '
    '> Active research uses `docs/ea/v6/AGENTS_V6.md` and `docs/ea/v6/HANDOFF_V6.md`.  '
    '> Primary market remains GOLD#. Final economics remain WR >=50%, average positive NET R >=2R, cost-adjusted EV >0.  '
    '> V6 exists to solve V3''s period/market generalization failure without repeating V4''s no-learning pattern: meaningful causal event anchor + raw multi-TF state + controlled context/generalization tests.  '
    '> Current phase is `V6-001A SAME-CAPACITY CROSS-MARKET CONTEXT INFORMATION AUDIT`: compare real `GOLD+XAUEUR+USDJPY` against exact 30-channel `GOLDx3` placebo before any adaptation or strategy design. No production authority exists.  '
    '> GOLD 2022 is consumed falsification data; GOLD# 2021 remains untouched.'
)
$NewAgentsLines = @(
    '> **V6 ACTIVE ROUTING — 2026-08-28 / CONTEXT-MEASUREMENT GENERALIZATION RESEARCH**  '
    '> Active research uses `docs/ea/v6/AGENTS_V6.md` and `docs/ea/v6/HANDOFF_V6.md`.  '
    '> Primary market remains GOLD#. Final economics remain WR >=50%, average positive NET R >=2R, cost-adjusted EV >0.  '
    '> V6 exists to solve V3''s period/market generalization failure by testing preregistered causal indicator/context measurements while controlling V3 multiplicity, V4 no-learning, and V5 research-direction failures.  '
    '> Current phase is `V6-001 CONTEXT-MEASUREMENT HYPOTHESIS REGISTRY / PRE-OUTCOME DESIGN`. Read `V6_000A_V3_V5_LINEAGE_AND_FAILURE_SYNTHESIS.md` and `V6_001_CONTEXT_MEASUREMENT_REGISTRY.md`. `V6-001A` is a queued cross-market child, not the definition or fatal gate of V6. No production authority exists.  '
    '> GOLD 2022 is consumed falsification data; GOLD# 2021 remains untouched.'
)
$OldHandoffLines = @(
    '> **V6 ACTIVE ROUTING — 2026-08-28 / EVENT-CONDITIONED GENERALIZATION**  '
    '> Current phase: `V6-001A SAME-CAPACITY CROSS-MARKET CONTEXT INFORMATION AUDIT`.  '
    '> V6 keeps GOLD# as the primary discovery market and treats V3 validation collapse plus V4 no-learning as explicit design constraints.  '
    '> Immediate task: exact broad-event parity -> recover/freeze the late-V5 context probe -> compare real `GOLD+XAUEUR+USDJPY` against same-dimensional `GOLDx3` placebo in 2024 and 2025.  '
    '> No best-TF/model selection, no adaptation, no strategy/EA change before the context-information claim is classified. GOLD 2022 is consumed falsification data; GOLD# 2021 remains closed.'
)
$NewHandoffLines = @(
    '> **V6 ACTIVE ROUTING — 2026-08-28 / CONTEXT-MEASUREMENT GENERALIZATION**  '
    '> Current phase: `V6-001 CONTEXT-MEASUREMENT HYPOTHESIS REGISTRY / PRE-OUTCOME DESIGN`.  '
    '> V6 keeps GOLD# as the primary research market and treats V3 validation collapse, V3 multiplicity risk, V4 no-learning, and V5 payoff/transfer/research-direction failures as explicit design constraints.  '
    '> Immediate task: read the V3/V5 lineage synthesis -> finalize the semantic indicator/context registry -> map families to V3 failure modes -> qualify causal data/sample density -> freeze outcome-blind child order and family budget -> activate one child. `V6-001A` remains a queued preregistered cross-market child and must not be treated as the entire V6 mandate.  '
    '> No indicator/window/threshold tournament, no adaptation rescue, and no strategy/EA change from information-stage evidence. GOLD 2022 is consumed falsification data; GOLD# 2021 remains closed.'
)

$OldAgents = ($OldAgentsLines -join $AgentsEol) + $AgentsEol + $AgentsEol
$NewAgents = ($NewAgentsLines -join $AgentsEol) + $AgentsEol + $AgentsEol
$OldHandoff = ($OldHandoffLines -join $HandoffEol) + $HandoffEol + $HandoffEol
$NewHandoff = ($NewHandoffLines -join $HandoffEol) + $HandoffEol + $HandoffEol

if (-not $AgentsText.StartsWith($OldAgents)) {
    Fail 'AGENTS.md top routing block differs from the verified source. No files changed.'
}
if (-not $HandoffText.StartsWith($OldHandoff)) {
    Fail 'docs/ea/HANDOFF.md top routing block differs from the verified source. No files changed.'
}

# All checks passed. Perform writes.
$AgentsText = $NewAgents + $AgentsText.Substring($OldAgents.Length)
$HandoffText = $NewHandoff + $HandoffText.Substring($OldHandoff.Length)
[System.IO.File]::WriteAllText($AgentsPath, $AgentsText, $Utf8NoBom)
[System.IO.File]::WriteAllText($RootHandoffPath, $HandoffText, $Utf8NoBom)

$ReplacementFiles = @(
    'docs/ea/v6/AGENTS_V6.md'
    'docs/ea/v6/BACKLOG_V6.md'
    'docs/ea/v6/DECISIONS_V6.md'
    'docs/ea/v6/HANDOFF_V6.md'
    'docs/ea/v6/RESEARCH_STATE_V6.md'
    'docs/ea/v6/V6_000A_V3_V5_LINEAGE_AND_FAILURE_SYNTHESIS.md'
    'docs/ea/v6/V6_000_RESEARCH_CONTRACT.md'
    'docs/ea/v6/V6_001A_CONTEXT_INFORMATION_AUDIT.md'
    'docs/ea/v6/V6_001_CONTEXT_MEASUREMENT_REGISTRY.md'
    'docs/ea/v6/V6_FAILURE_MAP_V3_V4_V5.md'
    'docs/ea/v6/V6_NEXT_SESSION_OPERATING_PROTOCOL.md'
)
foreach ($Rel in $ReplacementFiles) {
    $Source = Join-Path $PayloadRoot $Rel
    $Dest = Join-Path $RepoRoot $Rel
    $DestDir = Split-Path -Parent $Dest
    if (-not (Test-Path -LiteralPath $DestDir)) {
        New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
    }
    $Content = [System.IO.File]::ReadAllText($Source, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText($Dest, $Content, $Utf8NoBom)
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    Fail 'git diff --check failed. Review changes before committing.'
}

Write-Host ''
Write-Host 'V6 documentation reset applied successfully.'
Write-Host 'No commit or push was performed.'
Write-Host ''
git diff --stat
Write-Host ''
Write-Host 'Review with: git diff'
Write-Host 'Then commit/push when satisfied.'
