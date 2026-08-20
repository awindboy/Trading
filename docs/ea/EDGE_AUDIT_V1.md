# EDGE_AUDIT_V1 Measurement Contract

Last updated: 2026-08-20
Repository base: `260d14e714bbd635448d466d12d848b9ef80ba39`
Prepared build: `1.92R1L4`
Phase: `BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW`
Strategy authority: **NONE**
Validation: **PREPARED / COMPILE + AUDIT-OFF/AUDIT-ON PARITY PENDING**

## Purpose

The current question is not which filter improves the strategy. It is:

> At what point, if any, does the deterministic pipeline contain predictive information about future price?

D-142A measures this without changing the strategy being measured.

## Non-authority contract

The audit may observe and log only. It cannot:

```text
authorize / reject / rank / delay / resize / merge / cancel
change direction / Entry / SL / TP / exposure state
```

Audit output is a separate CSV. Audit file-open failure disables only the audit.

## Why MAP uses cadence sampling

MAP is persistent state. Measuring only MAP transition events would bias the sample toward moments of structural change.

D-142A therefore samples the final highest active MAP once per H1 wall-clock cadence after the complete same-timestamp MTF group.

The intended funnel is:

```text
MAP hourly state
        ↓ selected subset
PLAN = MAP + eligible Root + objective family
        ↓
ROOT_CONTACT
        ↓
SWEEP
        ↓
CHOCH
        ↓
FVG
        ↓
ACTUAL_FILL
```

PLAN must not be mislabeled as pure MAP evidence.

## Snapshot stages

- `MAP`: final highest active H1, otherwise mature M30; reference is the M1 close available at that timestamp.
- `PLAN`: existing scenario PLAN freeze; reference is `plan_reference_price`.
- `ROOT_CONTACT`: Root-contact M1 bar close.
- `SWEEP`: accepted D-127 Sweep bar close; current `SEQUENCE_ONLY` semantics remain unchanged.
- `CHOCH`: accepted D-127 protected-break CHoCH bar close.
- `FVG`: decision-cycle close at unique widest causal-fresh FVG selection.
- `ACTUAL_FILL`: actual fill price, logged for identity/joining in D-142A.

## Forward labels — D-142A

For `MAP` through `FVG`, fixed wall-clock horizons are:

```text
15m
1h
4h
24h
```

Only subsequently completed M1 bars may update the path.

Output:

```text
signed_return_pct
mfe_pct
mae_pct
```

MAE is negative.

If a target falls in a market/session gap, use only the last causally available close at or before the target. `end_lag_seconds` records how stale that mark is. A future reopening price is never backdated to the target.

## Same-timestamp causality

At timestamp `T`, the M1 bar that has just completed must update **old** audit snapshots before any new MAP/PLAN/Contact/Sweep/CHoCH/FVG snapshot at `T` is created.

Therefore the audit receives the completed M1 bar at the beginning of the timestamp group, before the strategy processes new facts in that group.

A CHoCH/FVG snapshot cannot use the bar that created it as its own future MFE/MAE.

## Why ACTUAL_FILL exact virtuals are deferred

Actual fills can occur inside an M1 bar. M1 OHLC cannot prove fill-before-extreme ordering inside that minute.

D-142A therefore logs fill identity only and does **not** pretend M1 data provides exact fill-to-horizon or 1R/2R/3R first-hit ordering.

After D-142A proves zero strategy impact, D-142B may add Strategy Tester tick-order shadow barriers:

```text
same direction 1R / 2R / 3R
flipped direction 1R / 2R / 3R
```

This separation keeps the first instrumentation change narrow and auditable.

## CSV schema

```text
observed_at
event
stage
symbol
stage_at
snapshot_id
scenario_id
scope
direction
reference_price
horizon_seconds
value1
value2
value3
detail
```

For `FORWARD_LABEL`:

```text
value1 = signed_return_pct
value2 = mfe_pct
value3 = mae_pct
```

## Required parity test

Run the same short fixture twice:

```text
A. InpEnableEdgeAudit = false
B. InpEnableEdgeAudit = true
```

Everything else must be identical.

Required same main-strategy path:

```text
PLAN / Root Contact / Sweep / CHoCH / FVG
Entry / SL / TP / contributor merge
pending / fill / cancel / close / divergence
```

Only B may create the separate edge-audit CSV.

Any strategy difference invalidates D-142A research output.

## Recommended first smoke

```text
GOLD
2025-01-01 ~ 2025-01-31
Every tick based on real ticks
BASELINE_NO_REGIME_GATE
FIXED_RISK_MONEY = 100
ROOT_OB_DISTAL_20
```

After parity, a first mixed edge panel should include:

```text
GOLD
BTCUSD
GBPCAD
CADJPY
SILVER
USDJPY
```

This intentionally contains previous positive and strongly negative continuation symbols.

## Interpretation

```text
MAP ≈ null
-> re-evaluate the fundamental direction hypothesis.

MAP positive, PLAN/contact stronger
-> Root/context selection may add information.

PLAN/contact positive, Sweep/CHoCH deteriorate
-> trigger timing / causal ownership becomes the primary suspect.

CHOCH positive, FVG deteriorates
-> FVG selection/retest timing becomes the suspect.
```

Do not add a SHORT veto, RR cap, time cutoff, PD veto, generic score, or restore D-126 wholesale from this first audit.

## 2021

`2021` remains untouched.
