# D-149 SMART PARTIAL + EPISODE MANAGEMENT — apply / validate

Target repository state:

```text
repo: awindboy/Trading
required Git HEAD: e449bc68b9e57bd7bd4170279057fddeb429985d
commit: docs: ready to D-148
target build: 1.95R1L11 / SP_EM_RESEARCH_V1
baseline control: V1_EXIT_ORIGINAL + V1_EM_OFF
2021: KEEP UNTOUCHED
```

This package implements two **independent controlled research toggles** while preserving the D134 baseline control.

## Smart Partial (SP)

New exit mode:

```text
V1_EXIT_SMART_PARTIAL
```

At first observed +1R, the M30 state is frozen causally.

```text
STRONG_RUNNER:
  current M30 external is at/beyond original +2R
  -> close 25% once at/after +1R
  -> keep ~75% for structural TP

DEFAULT / M30 range unavailable:
  -> close 50% once at/after +1R
```

There are no repeated integer-R partials in SP. At first observed +2R or higher:

```text
remaining SL -> actual Fill price (break-even)
```

The frozen structural TP remains. If the broker temporarily rejects/disallows the BE modification it is retried. Broker cost/slippage can still make a BE residual deal slightly negative in money terms; the strategy-price SL is moved to Fill.

## Episode Management (EM)

New independent input:

```text
V1_EM_OFF
V1_EM_CAUSAL_EPISODE_V1
```

Episode identity:

```text
frozen active_map_tf + frozen owner_id + direction
```

Rules:

```text
same episode: at most one live pending/filled exposure

first net non-positive close:
  no immediate retry
  require fresh same-direction map delivery after the loss

H1-led episode refresh:
  same-owner H1 BOS
  OR new same-direction M30 INITIAL_BOS/BOS

M30-led episode refresh:
  same-owner M30 BOS

one refreshed retry is allowed
second consecutive net non-positive close:
  hard lock that owner episode
new owner:
  new episode, fresh state

positive aggregate realized-net close:
  reset consecutive loss count
```

There is no time cooldown, owner-age threshold, PB-count threshold, or quality score.

## Apply

Extract this folder anywhere inside the Trading repository and run from any directory inside that repository:

```powershell
python .\Trading_D149_SP_EM_RESEARCH_V1\tools\apply_d149_sp_em_research.py
```

or:

```powershell
py .\Trading_D149_SP_EM_RESEARCH_V1\tools\apply_d149_sp_em_research.py
```

The installer is fail-closed and idempotent. It requires the exact HEAD/blob state used to build this package and refuses unexpected local edits. It does not modify `AGENTS.md`, `docs/ea/EA_SPEC.md`, or `mt5/experts/EdgeAuditV1.mqh`.

Expected success message:

```text
D-149 SP + EM research variant applied successfully.
Build: 1.95R1L11 / SP_EM_RESEARCH_V1
Baseline control: V1_EXIT_ORIGINAL + V1_EM_OFF
Primary matrix: ORIGINAL/OFF, SMART_PARTIAL/OFF, ORIGINAL/EM, SMART_PARTIAL/EM
```

## Local validation

### 1. Compile

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required:

```text
0 errors
```

### 2. Baseline-control parity

Run a short GOLD fixture with:

```text
InpExitManagementMode = V1_EXIT_ORIGINAL
InpEpisodeManagementMode = V1_EM_OFF
InpEnableEdgeAudit = false
```

Use the same other settings as the D-148 ORIGINAL baseline, then compare:

```powershell
python tools\compare_d149_baseline.py <D148_ORIGINAL.csv> <D149_ORIGINAL_EM_OFF.csv>
```

Required:

```text
D149 BASELINE CONTROL PARITY: PASS
```

### 3. GOLD 2025 four-run matrix

Use identical tester conditions:

```text
Model: Every tick based on real ticks
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
InpEnableEdgeAudit = false
```

Run:

```text
A  ORIGINAL      + EM_OFF
B  SMART_PARTIAL + EM_OFF
C  ORIGINAL      + CAUSAL_EPISODE_V1
D  SMART_PARTIAL + CAUSAL_EPISODE_V1
```

Use a unique CSV file for each run. Summarize each:

```powershell
python tools\summarize_d149_sp_em.py <ledger.csv>
```

Do not interpret profitability if there is any execution divergence or unresolved in-scope execution.

### 4. Multi-year validation

After GOLD 2025 behavior is understood, repeat the same A/B/C/D matrix for GOLD 2023 and clean GOLD 2024. Do not tune the SP fractions, 1R room boundary, or EM two-loss policy from GOLD 2025 before that comparison.

## D-148 audit guard

The D-148 shadow audit remains in the source but is valid only for unchanged control behavior. The D-149 build rejects initialization if:

```text
InpEnableEdgeAudit=true
```

while SP or EM is active. For D-149 performance research, keep audit OFF.

## Files installed/updated

```text
mt5/experts/MentorDeterministicV1EA.mq5

docs/ea/HANDOFF.md
docs/ea/STRATEGY_RESEARCH_STATE.md
docs/ea/BACKLOG.md
docs/ea/DECISIONS.md
docs/ea/TEST_RESULTS.md
docs/ea/D147_EXIT_ARCHITECTURE_RESEARCH.md
docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md
docs/ea/D149_SP_EM_RESEARCH_V1.md

tools/summarize_d149_sp_em.py
tools/compare_d149_baseline.py
```

The package deliberately keeps the old ORIGINAL, R_STEP_TRAILING, and R_STEP_PARTIAL numeric identities unchanged.
