# D-147 EXIT ARCHITECTURE RESEARCH V1 — apply / validate

Target repository:

```text
awindboy/Trading
required HEAD: c541b19d68ac1589575bfaf1ab07abf1ee296a09
target build: 1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1
```

The package is fail-closed and idempotent. For every tracked target it regenerates the exact expected D-147 result from committed `HEAD:<path>` and accepts only:

```text
exact committed HEAD
or
exact generated D-147 output
```

Any other local edit aborts. `AGENTS.md` and `EA_SPEC.md` are not modified. `2021` remains untouched.

## Apply

Extract this folder anywhere inside the Trading repository and run from the repository root:

```powershell
python .\Trading_D147_EXIT_ARCHITECTURE_RESEARCH_V1\tools\apply_d147_exit_architecture.py
```

If your launcher is `py`:

```powershell
py .\Trading_D147_EXIT_ARCHITECTURE_RESEARCH_V1\tools\apply_d147_exit_architecture.py
```

Expected final message:

```text
D-147 exit-architecture research variant applied successfully.
Build: 1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1
Baseline control: V1_EXIT_ORIGINAL
```

If HEAD differs, do not force the package. Re-check/push the current repository and rebuild against the new HEAD.

## Implemented modes

### `V1_EXIT_ORIGINAL`

No D-147 post-fill action. Existing frozen server SL + structural TP behavior remains the baseline control.

### `V1_EXIT_R_STEP_TRAILING`

R is permanently frozen from actual fill to the original normalized strategy SL:

```text
+1R -> SL 0R
+2R -> SL +1R
+3R -> SL +2R
...
```

The structural TP remains attached.

### `V1_EXIT_R_STEP_PARTIAL`

At every newly reached integer R, close 50% of the **current remaining** volume. The percentage is hard-frozen and is not an optimization input.

Original SL and structural TP remain attached. If broker minimum/step volume prevents a true partial, the EA does not substitute a full close; partial management is disabled for that remainder and the original SL/TP continue.

Partial mode aggregates all exit deals when calculating final `realized_net_money`.

## First validation

### 1. Compile

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required:

```text
0 errors
```

### 2. ORIGINAL baseline parity

Before testing profitability, prove `V1_EXIT_ORIGINAL` is behaviorally identical to D-146.

Recommended settings:

```text
Model: Every tick based on real ticks
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
InpEnableEdgeAudit = false
InpExitManagementMode = V1_EXIT_ORIGINAL
```

Run the same GOLD period as the baseline and compare:

```powershell
python tools\compare_d147_original_baseline.py <D146_BASELINE.csv> <D147_ORIGINAL.csv>
```

Required:

```text
D147 ORIGINAL PARITY: PASS
```

The comparator removes only `EA_START`, `D147_*`, and `EDGE_AUDIT_*` diagnostic rows. All remaining rows must be identical.

## GOLD 2025 three-mode test

Only after ORIGINAL parity:

```text
A = V1_EXIT_ORIGINAL
B = V1_EXIT_R_STEP_TRAILING
C = V1_EXIT_R_STEP_PARTIAL
```

Use identical Strategy Tester settings and unique CSV filenames. Keep `InpEnableEdgeAudit=false` for this performance comparison.

Summarize each:

```powershell
python tools\summarize_d147_exit_architecture.py <ledger.csv>
```

Compare:

```text
realized net win rate
average winner net R
average loser net R
net expectancy R/trade
gross price-P&L expectancy R/trade
closed-trade max drawdown R
longest loss streak
LONG / SHORT split
large-winner dependence
D147 action rejections
partial-volume infeasibility
unresolved trades
```

A partial-exit trade counts as a winner only if final `realized_net_money / actual_fill_risk_money > 0`.

## Research boundary

This package deliberately does **not** add:

```text
M30 progress threshold
remaining-room threshold
PB exit
outward-refresh gate
Entry filter
fixed 1R/2R TP replacement
partial-fraction optimizer
```

D-147 isolates exit architecture. `Fill -> +1R` Entry survival remains a separate problem.

After clean GOLD results, expand to the existing development panel as needed:

```text
GOLD 2023
GOLD 2024
GOLD 2025
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

Do not use 2021.
