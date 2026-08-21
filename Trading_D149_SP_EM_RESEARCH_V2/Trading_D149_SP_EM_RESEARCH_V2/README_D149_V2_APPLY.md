# D-149 SP / EM Research V2 — apply and test

Target repository: `awindboy/Trading`  
Required exact HEAD: `b3068c0b445005fe455405ed18fb1f82198231df`  
Target build: `1.96R1L12 / SP_EM_RESEARCH_V2`

This package first records the completed GOLD 2025 D149 V1 evidence in the project documents, then adds V2 research modes while retaining all V1 modes and the ORIGINAL + EM_OFF baseline control.

## Apply

From the local Trading repository root, after extracting this package beside/under the repository:

```powershell
python .\Trading_D149_SP_EM_RESEARCH_V2\tools\apply_d149_sp_em_research_v2.py
```

or:

```powershell
py .\Trading_D149_SP_EM_RESEARCH_V2\tools\apply_d149_sp_em_research_v2.py
```

The installer is fail-closed. It verifies exact Git HEAD and committed blob identities, refuses unknown local edits, and does not modify `AGENTS.md`, `EA_SPEC.md`, or `EdgeAuditV1.mqh`.

## What the package changes

Updated:

```text
mt5/experts/MentorDeterministicV1EA.mq5
docs/ea/HANDOFF.md
docs/ea/STRATEGY_RESEARCH_STATE.md
docs/ea/BACKLOG.md
docs/ea/DECISIONS.md
docs/ea/TEST_RESULTS.md
docs/ea/D149_SP_EM_RESEARCH_V1.md
```

Added:

```text
docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md
tools/summarize_d149_sp_em_v2.py
```

Unchanged/verified:

```text
AGENTS.md
docs/ea/EA_SPEC.md
mt5/experts/EdgeAuditV1.mqh
```

## New research modes

SP V1 remains:

```text
V1_EXIT_SMART_PARTIAL
```

SP V2 adds:

```text
V1_EXIT_SMART_PARTIAL_V2
```

EM V1 remains:

```text
V1_EM_CAUSAL_EPISODE_V1
```

EM V2 adds:

```text
V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

Do not use EdgeAudit with research exit/EM modes. `InpEnableEdgeAudit=false` for D149 V2 tests.

## First validation — compile

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required:

```text
0 errors
```

## Control parity

Run a short GOLD control with:

```text
InpExitManagementMode    = V1_EXIT_ORIGINAL
InpEpisodeManagementMode = V1_EM_OFF
InpEnableEdgeAudit       = false
```

Use the same conditions as the prior D149/D148 control and compare with:

```powershell
python tools\compare_d149_baseline.py <prior_control.csv> <D149_V2_control.csv>
```

Required:

```text
D149 BASELINE CONTROL PARITY: PASS
```

## GOLD 2025 V2 matrix

Common settings:

```text
Every tick based on real ticks
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
InpEnableEdgeAudit = false
```

### B2 — SP V2 isolated

```text
InpExitManagementMode    = V1_EXIT_SMART_PARTIAL_V2
InpEpisodeManagementMode = V1_EM_OFF
```

Suggested file:

```text
GOLD_SPV2.csv
```

### C2 — EM V2 isolated

```text
InpExitManagementMode    = V1_EXIT_ORIGINAL
InpEpisodeManagementMode = V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

Suggested file:

```text
GOLD_EMV2.csv
```

### D2 — SP V2 + EM V2

```text
InpExitManagementMode    = V1_EXIT_SMART_PARTIAL_V2
InpEpisodeManagementMode = V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

Suggested file:

```text
GOLD_SPV2_EMV2.csv
```

Analyze each:

```powershell
python tools\summarize_d149_sp_em_v2.py GOLD_SPV2.csv
python tools\summarize_d149_sp_em_v2.py GOLD_EMV2.csv
python tools\summarize_d149_sp_em_v2.py GOLD_SPV2_EMV2.csv
```

Required first:

```text
D149 V2 LEDGER INTEGRITY: PASS
execution_divergences=0
cancel_rejected=0
unresolved=0
```

## Interpretation priorities

SP V2 must be judged against both ORIGINAL and SP V1. Important checks:

```text
continuation WR
avg winner
expectancy
total R
DD
loss streak
DEFAULT final-net protection
STRONG winner preservation
cost-adjusted BE actual final-net results
volume-granularity full-close fallbacks
```

EM V2 must not be judged only by expectancy per remaining trade. Important checks:

```text
longest genuine/realized loss streak
quarantine entry/release count
real trades blocked during quarantine
shadow armed/filled/+1R/SL/canceled/censored
requalification winner sacrificed in shadow
local no-refresh blocks
remaining losses after quarantine caused by positions already open before trigger
```

If GOLD 2025 is coherent, rerun the same frozen V2 on GOLD 2023 and 2024 before changing constants. Do not touch 2021.
