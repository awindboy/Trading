# D-134 Full-Year 2025 Test Result + D-135 Performance Regression Plan

Status: `D-134 FULL-YEAR IMPLEMENTATION CHECKPOINT / D-135 PERFORMANCE REGRESSION BASELINE`
Date recorded: `2026-08-19`

This file is a focused long-run supplement to `docs/ea/TEST_RESULTS.md`.
`HANDOFF.md` points to this record because the full-year run exposed both strategy evidence and an implementation-scalability defect that must be preserved together.

## 1. Source run

Uploaded event ledger:

```text
file = mentor_v1_structure_events(20260818-064307).csv
SHA-256 = 28ab4a4e6c2477989fb2d4b2768006e89c7b396d4508de8d464d41ca3edbc0e4
rows = 234,275
single EA_START = 1
single EA_STOP = 1
```

EA / execution identity:

```text
repository base commit = a6ad44e1aef64472f76dc45c1c0c336dbf7073f1
internal build = 1.80
phase = D134_HEDGING_SAME_DIRECTION_ADDON_EXECUTION
SL model = ROOT_OB_DISTAL_20
FVG-origin OB = baseline authority
same-entry multi-Root = contributor merge
same-direction independent add-ons = enabled
opposite-direction coexistence = blocked
account model = hedging contract
```

Tester interval:

```text
calendar year = 2025-01-01 ~ 2025-12-31
model = Every tick based on real ticks
user-reported wall-clock runtime ≈ 9 hours
```

The user observed long periods where Strategy Tester progress appeared stationary, followed by abrupt progress jumps. Prior January-scale tests normally completed in under roughly one minute.

## 2. Full-year causal / execution funnel

Observed counts:

```text
SCENARIO_PLANNED = 837
SCENARIO_ROOT_CONTACT_BOUND = 496
SCENARIO_SWEEP_ACCEPTED = 386
SCENARIO_CHOCH_ACCEPTED = 178
SCENARIO_FVG_SELECTED = 163

unique Entry opportunities = 79
execution geometry ready = 74
pending accepted = 73
filled = 58
closed = 58
pending canceled before fill = 15
```

Closed-result counts:

```text
TP = 14
SL = 44
win rate = 24.1%
```

Execution integrity:

```text
order reject = 0
cancel reject = 0
execution divergence = 0
opposite-direction exposure conflict = 1
```

Pending cancellation observations:

```text
objective delivered before fill = 10
all contributor Roots invalid = 3
single source Root invalid = 2
```

NO_TRADE / execution-opportunity failures observed after geometry formation:

```text
NO_COMMON_R_ELIGIBLE_OBJECTIVE = 4
NO_R_ELIGIBLE_OBJECTIVE = 1
OPPOSITE_DIRECTION_EXPOSURE_CONFLICT = 1
```

This full-year run therefore substantially extends D-133/D-134 lifecycle coverage beyond January, including merged contributors, same-direction hedging add-ons, all-contributor invalidation, and opposite-direction conflict handling.

## 3. Provisional performance research summary

The event CSV does not contain complete broker contract-value / commission / swap accounting. Dollar figures below use the same provisional research convention used during analysis for GOLD minimum-volume parity and are **gross estimates**, not broker-statement net PnL.

```text
filled trades = 58
TP = 14
SL = 44
win rate ≈ 24.1%
provisional gross profit ≈ +1,107.95 USD
provisional gross loss ≈ -842.31 USD
provisional gross net ≈ +265.64 USD
provisional gross profit factor ≈ 1.315
```

Risk-normalized result:

```text
realized total ≈ +8.68R
expectancy ≈ +0.150R / filled trade
R profit factor ≈ 1.187
median trade ≈ -1.00R
```

Observed closed-trade R drawdown:

```text
maximum ≈ -21.44R
```

The year was not uniformly profitable. December contained several large winners and contributed most of the positive annual gross result. This is consistent with a low-win-rate / large-payoff trend-following distribution, but it is not yet evidence of robust multi-year profitability.

## 4. Continuation versus reversal

Observed closed trades by scenario scope:

```text
EXTERNAL_CONTINUATION
fills = 51
TP = 14
SL = 37
realized ≈ +15.94R
provisional gross PnL ≈ +433.81 USD

EXTERNAL_REVERSAL
fills = 7
TP = 0
SL = 7
realized ≈ -7.26R
provisional gross PnL ≈ -168.17 USD
```

This is a **research flag**, not an automatic rule change. The reversal sample is still small, but it is currently the clearest strategy branch requiring later causal review once implementation performance is fixed.

## 5. D-134 same-direction add-ons

Same-direction add-ons were not uniformly harmful over the full year:

```text
add-on fills = 20
TP = 6
SL = 14
win rate ≈ 30.0%
realized ≈ +4.20R
provisional gross PnL ≈ +135.22 USD
```

Therefore the January-only negative impression was not sufficient evidence to revert D-134.

However, add-ons create correlated portfolio exposure. Observed maxima:

```text
maximum simultaneous filled positions = 4
maximum accepted exposure = 5
```

One April cluster carried three same-direction SHORT positions at once and all three stopped out. This is a future portfolio-risk-layer issue, not evidence that a valid later Root -> Sweep -> CHoCH -> FVG chain should be discarded at the signal layer.

## 6. Execution / slippage note

Execution divergence remained zero. Several SL exits nevertheless occurred beyond the strategy SL price under real-tick simulation. The largest previously inspected case was approximately `-2.47R` because the actual SL deal occurred materially beyond the frozen stop price.

Therefore future risk research must distinguish:

```text
strategy risk = Entry-to-frozen-SL distance
realized execution risk = actual fill-to-exit result
```

No rule change is authorized from this observation alone.

## 7. Performance scalability defect

The approximately nine-hour runtime is not consistent with simple linear growth from the January fixture. Static build-1.80 review found long-run hot paths repeatedly traversing historical append-only ledgers.

Primary defects:

```text
1. objective consumption polling:
   all historical objective candidates
   x candidate -> linear scenario lookup

2. historical scenario scans on M1 processing:
   old canceled/filled/no-trade scenarios remain in append-only ledger

3. historical Root-reaction scans:
   waiting and terminal trackers share one array

4. broker reconciliation on every tick:
   historical scenarios repeatedly rechecked
   HistorySelect / deal scans could repeat after terminal outcomes

5. exact pending / exact hedging position existence was not used as the cheap first gate

6. CSV FileFlush executed for every event row
```

The historical ledgers are required for audit. The defect is using them as runtime working sets.

Classification:

```text
strategy-rule defect = NO EVIDENCE
execution-integrity defect in observed run = NO
implementation scalability defect = YES
priority = FIX BEFORE MULTI-YEAR TESTING
```

## 8. D-135 prepared performance-only build

Target:

```text
internal build = 1.90
phase = D135_PERFORMANCE_WORKING_SET_OPTIMIZATION
strategy semantics = D134_UNCHANGED
default CSV = mentor_v1_d135_events.csv
```

Implemented optimization classes:

```text
- bounded WAITING/READY Root-reaction working sets
- bounded WAITING_SWEEP scenario working set
- bounded WAITING_CHOCH scenario working set
- bounded WAITING_EXECUTION_GEOMETRY working set
- bounded active broker-execution working set
- event-driven frozen-objective consumption propagation
- direct final-objective candidate reference
- active-liquidity strategy-consumed cache
- cheap Root-reaction state version in scenario-layer signature
- no ordinary-tick entry-history scan while exact pending order is live
- no ordinary-tick exit-history scan while exact hedging position is live
- terminal execution removed from active reconciliation working set
- CSV flush batching = 256 rows, with critical execution events and deinit flush retained
```

These are implementation optimizations only. They may not change Root, Sweep, CHoCH, FVG, merge, Entry, SL, TP, add-on, conflict, cancellation, fill, or close semantics.

## 9. D-135 acceptance test

Do **not** run the full year first.

First run the same January real-tick fixture with:

```text
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
account = hedging
```

Required D-134 parity targets:

```text
ROOT_CREATED = 108
SCENARIO_PLANNED = 78
SCENARIO_ROOT_CONTACT_BOUND = 36
SCENARIO_SWEEP_ACCEPTED = 33
SCENARIO_CHOCH_ACCEPTED = 18
SCENARIO_FVG_SELECTED = 18

unique Entry opportunities = 9
same-entry merge clusters = 4
pending accepted = 9
filled = 7
closed = 7
objective-before-fill cancel = 2
exposure-policy NO_TRADE = 0
execution divergence = 0
```

Also compare each unique opportunity's:

```text
selected FVG
Entry
merged SL
Final TP
pending / cancel / fill / close outcome
```

Performance criterion:

```text
semantic parity = mandatory
wall-clock runtime = record and compare with D-134 January baseline
material runtime reduction = required before adopting D-135 for long tests
```

If any strategy/execution result differs, D-135 fails regardless of speed and must not replace build 1.80 for research conclusions.
