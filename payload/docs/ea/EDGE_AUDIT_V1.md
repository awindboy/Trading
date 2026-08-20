# EDGE_AUDIT_V1 / D-145 Lightweight Runner Market-Context Measurement Contract

Last updated: 2026-08-21
Current research build: `1.92R1L7`
Current phase: `RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT`
Strategy authority: **NONE**

## Purpose

The audit measures where predictive information appears or disappears. It may observe and log only. It may not authorize, reject, delay, resize, merge, cancel, or otherwise change a strategy trade.

D-143 front-end and D-144 exact-tick stage audits are preserved below as historical measurement contracts. The active D-145 question is narrower: among actual fills that first reach +1R, what causally-known market background separates exhaustion before 2R from 2R+ directional delivery? D-145 therefore keeps only selected-FVG pre-fill displacement tracking and actual-filled runner tracking active on ticks.

## Unified ledger

D-143 uses only the normal:

```text
InpEventCsvFile
```

There is **no separate Edge Audit CSV input**.

The standard six-column schema remains:

```text
observed_at,event,timeframe,available_at,object_id,detail
```

Research rows are distinguished only by:

```text
event starts with EDGE_AUDIT_
```

Audit rows are written directly to the existing event handle and do not increment the baseline logger's row counters. This permits audit OFF/ON parity after filtering `EDGE_AUDIT_*` rows.

## Shadow populations

D-143 records:

```text
STRUCTURE_INITIAL_BOS  H1/M30
STRUCTURE_BOS          H1/M30 continuation BOS
STRUCTURE_PROTECTED_BREAK H1/M30
MAP                    hourly highest active map
ROOT_CREATED           every active Root created by H1/M30/M15 structure
PLAN                   baseline scenario PLAN
PHYSICAL_ROOT_CONTACT  every observed Root contact, including NO_PREPLAN
ROOT_CONTACT           preplanned scenario-bound contact
SWEEP
CHOCH
FVG
ACTUAL_FILL identity
```

The distinction between `PHYSICAL_ROOT_CONTACT` and `ROOT_CONTACT` is deliberate. It allows offline comparison of the complete Root-contact population against the subset selected by map/objective planning.

## Front-end causal fields

The audit records enough state to join direction formation to Root/PLAN/contact without hindsight:

```text
owner ID and owner start
owner age
last INITIAL_BOS
last continuation BOS
last same-direction BOS
last protected-swing update
last protected break
continuation-BOS count
compatible Root event/candidate ordinals under H1 and M30 owners
PLAN ordinal under the frozen active owner
Root TF / source recognizer / origin / creation timestamp
Root origin -> creation delay
H1 and M30 owner context at Root creation
Root creation -> PLAN/contact delay
PLAN -> contact delay
H1/M30 context at contact
PLAN-frozen owner vs current owner/direction
```

No owner-age, Root-count, or BOS-age cutoff is a strategy rule in D-143.

## Forward labels

For causal stages with a bar-close reference price:

```text
15m
1h
4h
24h
```

record:

```text
signed_return_pct
mfe_pct
mae_pct
```

Only subsequently completed M1 bars may contribute. If a target falls in a session gap, use the last causally available close at or before the target; never backdate the reopening price.

The M1 bar that creates a new same-timestamp strategy event is fed to existing snapshots **before** the new event snapshot is created, so a new snapshot cannot count its own creation bar as future excursion.

`ACTUAL_FILL` remains identity-only in this build. Exact tick-order 1R/1.5R/2R/3R virtual barriers are deferred until the front-end direction/Root problem is understood.

## Bootstrap

H1/M30 tracker state and active Root metadata are reconstructed during bootstrap so runtime ages and ordinals are causally correct. High-volume bootstrap research snapshots are not emitted. Runtime snapshots begin after bootstrap.

## Required parity test

Run the same short fixture twice:

```text
A. InpEnableEdgeAudit = false
B. InpEnableEdgeAudit = true
```

Use a different `InpEventCsvFile` name for A and B.

Compare after deleting/filtering all rows whose event starts with `EDGE_AUDIT_`. The remaining six-column rows must be exactly identical. Any remaining strategy-path difference invalidates D-143.

Recommended smoke:

```text
GOLD
2025-01-01 ~ 2025-01-31
Every tick based on real ticks
BASELINE_NO_REGIME_GATE
FIXED_RISK_MONEY = 100
ROOT_OB_DISTAL_20
```

## Post-parity research panel

```text
BTCUSD
CADJPY
GBPCAD
GOLD
SILVER
USDJPY
```

Only one unified CSV per symbol is needed.

## First questions

1. Does INITIAL_BOS itself predict its declared direction at 1h/4h/24h?
2. Does continuation BOS refresh that predictive edge or simply extend a stale owner?
3. Does direction accuracy decay with owner age or last-BOS age without arbitrary thresholds?
4. Do later compatible Roots under the same owner degrade versus early Roots?
5. Does Root contact create only short-horizon reaction or sustained continuation?
6. Is PLAN selecting better or worse Roots than the full physical-contact population?
7. Are H1 and M30 relationships symmetric across LONG/SHORT and across symbols/months?

Do not turn exploratory buckets into production cutoffs without cross-symbol/time validation.

## Explicit non-actions

D-143 does not:

```text
change AGENTS.md
change EA_SPEC.md
change Map/Root/Sweep/CHoCH/FVG definitions
add SHORT veto
add owner-age cutoff
add Root-count cutoff
add RR cap
add PD veto
restore D-126 filters
open 2021
```

`2021` remains untouched.


## D-144 exact-tick barrier extension

D-144 build identity:

```text
1.92R1L6
REACTION_ENTRY_BARRIER_AUDIT_V1_EXACT_TICK
```

The D-143 forward-label population remains unchanged. D-144 adds exact-tick virtual barrier trackers only; it does not change strategy state.

### Stage-comparison R

At a preplanned physical Root contact, the first tick at or after the causally available M1 contact close freezes:

```text
contact executable entry = Ask for LONG / Bid for SHORT
root distal = Root.bottom - 0.20*Root.width for LONG
              Root.top    + 0.20*Root.width for SHORT
contact_R = abs(contact executable entry - root distal)
```

This exact absolute `contact_R` is reused at `ROOT_CONTACT`, `SWEEP`, `CHOCH`, and `FVG`. Each later stage enters virtually at the first executable tick after that stage becomes known but keeps the same R distance. This isolates timing/information decay from changing stop geometry.

At each stage:

```text
SAME_DIRECTION
FLIPPED_DIRECTION

+1.0R vs -1R
+1.5R vs -1R
+2.0R vs -1R
```

LONG barriers are evaluated on Bid; SHORT barriers on Ask. Therefore target/stop ordering is exact to Strategy Tester tick order.

### ACTUAL_FILL R

For an actual fill:

```text
fill_R = abs(fill_price - normalized_sl)
```

SAME_DIRECTION uses the actual fill and risk. A flipped-direction mirror uses the same numeric fill/risk only as a direction-isolation research control and is explicitly labeled non-executable as an opposite market fill.

If `observed_at != fill_at` at whole-second precision, D-144 refuses to reconstruct exact fill barrier ordering and writes `EDGE_AUDIT_BARRIER_SKIPPED`.

### Events

```text
EDGE_AUDIT_CONTACT_RISK_ANCHOR
EDGE_AUDIT_BARRIER_ARMED
EDGE_AUDIT_BARRIER_ACTIVATED
EDGE_AUDIT_BARRIER_RESULT
EDGE_AUDIT_BARRIER_SKIPPED
EDGE_AUDIT_BARRIER_CENSORED
```

`EDGE_AUDIT_BARRIER_RESULT` is one row per target level. `TP_FIRST` and `SL_FIRST` are independent for each target. A 1R target can therefore win while the same path later loses the 1.5R/2R tests.

There is no arbitrary time cutoff. Unresolved trackers are right-censored only at tester termination.

---

## D-145 lightweight runner-context contract

D-144 multi-stage barriers are superseded for broad research runs because they impose excessive per-tick cost. D-145 keeps the unified event ledger but disables:

```text
hourly MAP forward labels
structure/Root population forward labels
Root Contact/Sweep/CHoCH/FVG virtual barriers
flipped-direction virtual barriers
```

Tick-active research objects are limited to:

```text
1. selected FVG waiting for actual Fill
   -> measure pre-fill directional displacement and adverse return

2. actual Fill
   -> measure exact 1R / 2R / 3R / structural-TP vs normalized SL
```

Snapshot A — `EDGE_AUDIT_RUNNER_FILL_SNAPSHOT` freezes current:

```text
scenario / direction / scope
actual fill / normalized SL / R geometry
Root / FVG identities and geometry
PLAN/Contact/Sweep/CHoCH/FVG elapsed times
selected-FVG -> Fill max favorable/adverse displacement
current highest map identity
H1/M30 owner/BOS/protected-break state
H1/M30 protected->external range position and remaining room in R
current 12-wave M30 progression, net directional advance, PB count, expansion
current M1 structure state
```

Snapshot B — `EDGE_AUDIT_RUNNER_1R_SNAPSHOT` freezes the same current background at the first exact +1R touch plus:

```text
Fill -> +1R elapsed time
R/hour descriptive speed
maximum adverse R before +1R
new same/opposite H1/M30/M1 structure-event counts since Fill
new same/opposite protected-break counts since Fill
```

No logged field has strategy authority. No threshold is selected by D-145.
