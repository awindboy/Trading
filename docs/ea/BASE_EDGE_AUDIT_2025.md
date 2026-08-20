# 2025 Cross-Symbol Base Edge Audit

Date: 2026-08-20
Repository base: `260d14e714bbd635448d466d12d848b9ef80ba39`
Status: **ACTIVE RESEARCH EVIDENCE / STRATEGY AUTHORITY UNCHANGED**

## Purpose

This document records the first broad cross-symbol test of whether the current Mentor deterministic baseline signal itself has predictive edge.

It intentionally asks a more basic question than Regime Research V1:

> Before deciding which baseline trades to filter, does the underlying baseline signal outperform a weak null benchmark at all?

This document does not amend `AGENTS.md` or `EA_SPEC.md`.

## Source data

Bundle:

```text
ALL.zip
bytes = 6,847,884
SHA-256 = 9408fd91c70a2a75e55888f43fa915652cd5b3b24b10415b536b49d74a9ea6eb
18 CSV files
```

All runs:

```text
build = 1.92R1L3
regime_mode = BASELINE_NO_REGIME_GATE
position_sizing_mode = FIXED_RISK_MONEY
fixed risk target = $100
SL = ROOT_OB_DISTAL_20
strategy semantics = D134 execution core unchanged
```

Symbols:

```text
BTCUSD CADCHF CADJPY CHFJPY EURCAD EURCHF EURGBP EURJPY EURUSD
GBPCAD GBPCHF GBPJPY GBPUSD GOLD SILVER USDCAD USDCHF USDJPY
```

## Reconstructed trade population

Closed trades:

```text
1,463
TP = 246
SL = 1,217
```

All closed fills were joined to their scenario, strategy geometry, and close event.

Canonical R:

```text
risk = abs(actual_fill - frozen_strategy_SL)

LONG  = (actual_exit - actual_fill) / risk
SHORT = (actual_fill - actual_exit) / risk
```

The absolute denominator is necessary for rare fill-through-stop cases.

## Execution contamination

Eight execution divergences occurred across five symbols.

Contaminated symbol-years:

```text
EURCAD
EURGBP
GBPJPY
GBPUSD
USDCHF
```

Two defect classes exist:

```text
3 x recoverable broker cancel rejection -> stale fill
5 x pending disappeared without fill/cancel proof
```

These symbols are retained for execution diagnosis but excluded from the primary divergence-free edge panel.

## Raw 18-symbol result

```text
1,463 trades
246 wins
16.81%
-418.221912R
mean -0.285866R
PF ≈ 0.6686
```

Continuation:

```text
1,310 trades
219 wins
-390.519384R
mean -0.298106R
PF ≈ 0.6542
```

Raw performance is poor, but this is not the final edge conclusion because the panel contains execution contamination.

## Primary divergence-free panel

Thirteen symbols contain no execution divergence:

```text
BTCUSD CADCHF CADJPY CHFJPY EURCHF EURJPY EURUSD
GBPCAD GBPCHF GOLD SILVER USDCAD USDJPY
```

All scopes:

```text
1,023 trades
187 wins
-193.184127R
mean -0.188841R
PF ≈ 0.7768
```

Continuation:

```text
901 trades
165 wins
-179.573032R
mean -0.199304R
PF ≈ 0.7637
```

Reversal:

```text
122 trades
22 wins
-13.611095R
mean -0.111566R
PF ≈ 0.8714
```

The main research target is continuation because that is the dominant baseline scope and the scope used by Frozen Regime V1.

## Planned-barrier rescore

Execution-price effects can obscure whether a strategy signal was already bad before broker realism.

Therefore each divergence-free continuation trade was rescored only by the strategy's own frozen barriers:

```text
TP close -> +planned_R
SL close -> -1R
```

Result:

```text
901 trades
-166.492129R
mean -0.184786R
```

This remains strongly negative.

Conclusion:

> The negative 2025 cross-symbol continuation result is not primarily a slippage/swap/position-sizing artifact.

## First stylized null

For a zero-drift continuous process with stop distance 1 and target distance `planned_R`:

```text
P(TP first) = 1 / (1 + planned_R)
```

This is deliberately weak and idealized.

It ignores:

```text
drift
autocorrelation
volatility clustering
session structure
cross-symbol dependence
trade clustering
```

It is therefore a diagnostic baseline, not final statistical proof.

Trade-by-trade result:

```text
expected TP count = 205.7306
actual TP count = 165

expected rate = 22.8336%
actual rate = 18.3130%
```

Independence-only Poisson-binomial CDF:

```text
P(X <= 165) ≈ 0.0003157
```

Because independence is unrealistic, do not promote this p-value to a final significance claim.

The robust interpretation is simpler:

> The continuation strategy fails even a first weak RR-aware null diagnostic.

## LONG versus SHORT

### LONG continuation

```text
460 trades
101 wins

actual TP rate = 21.9565%
null TP rate = 23.0821%

planned-barrier R = -4.181063R
canonical R = -13.361419R
```

Interpretation:

```text
2025 LONG edge is not demonstrated.
It is approximately null-like under this first diagnostic.
```

### SHORT continuation

```text
441 trades
64 wins

actual TP rate = 14.5125%
null TP rate = 22.5744%

planned-barrier R = -162.311067R
canonical R = -166.211613R
```

Expected wins under the stylized trade-specific null:

```text
99.5530
```

Actual:

```text
64
```

Independence-only CDF:

```text
P(X <= 64) ≈ 0.00000603
```

Interpretation:

> Bearish continuation is the dominant base-edge failure in this 2025 cross-symbol sample.

This does not imply a timeless rule that SHORT should be disabled.

## H1-state evidence

| H1 state | Trades | Wins | Actual WR | Null WR | Planned-barrier R | Canonical R |
|---|---:|---:|---:|---:|---:|---:|
| BULLISH | 355 | 80 | 22.54% | 23.65% | -1.4545R | -8.6640R |
| BEARISH | 329 | 46 | 13.98% | 22.78% | -139.8579R | -141.9049R |
| TRANSITION | 217 | 39 | 17.97% | 21.58% | -25.1797R | -29.0041R |

The mature bearish H1 path explains most of the negative continuation result.

## Planned-R evidence

| Planned R | Trades | Wins | Actual WR | Null WR | Planned-barrier R | Canonical R |
|---|---:|---:|---:|---:|---:|---:|
| 1–2R | 217 | 68 | 31.34% | 40.89% | -47.9764R | -52.5583R |
| 2–4R | 251 | 53 | 21.12% | 26.16% | -44.6526R | -47.3145R |
| 4–8R | 247 | 31 | 12.55% | 15.12% | -41.7568R | -43.8615R |
| 8–16R | 137 | 13 | 9.49% | 8.68% | +16.8937R | +15.7447R |
| 16R+ | 49 | 0 | 0.00% | 4.30% | -49.0000R | -51.5835R |

The failure is not restricted to extremely distant targets.

The `16R+` bucket is a strong structural warning but is not sufficient evidence to add a max-R filter.

## Symbol breadth

| Symbol | Trades | Wins | Actual WR | Null WR | Canonical R |
|---|---:|---:|---:|---:|---:|
| BTCUSD | 112 | 28 | 25.00% | 22.37% | +15.6835R |
| CADCHF | 32 | 4 | 12.50% | 22.39% | -12.8645R |
| CADJPY | 111 | 9 | 8.11% | 21.00% | -61.1590R |
| CHFJPY | 66 | 15 | 22.73% | 23.17% | -9.5899R |
| EURCHF | 42 | 8 | 19.05% | 27.47% | -20.9184R |
| EURJPY | 76 | 15 | 19.74% | 21.66% | -10.5871R |
| EURUSD | 82 | 16 | 19.51% | 21.48% | -9.7424R |
| GBPCAD | 68 | 15 | 22.06% | 23.03% | +16.9811R |
| GBPCHF | 56 | 7 | 12.50% | 23.47% | -32.0104R |
| GOLD | 51 | 14 | 27.45% | 21.10% | +15.9365R |
| SILVER | 45 | 4 | 8.89% | 20.86% | -30.4628R |
| USDCAD | 79 | 14 | 17.72% | 25.31% | -24.4038R |
| USDJPY | 81 | 16 | 19.75% | 25.11% | -16.4358R |

Breadth:

```text
positive = 3
negative = 10
```

Removing the worst symbol does not turn the remaining panel into a convincing positive strategy.

## Causal timing

Closed divergence-free continuation trades show:

| Interval | Median | p90 | Maximum |
|---|---:|---:|---:|
| PLAN -> Root contact | 10.73h | 88.97h | 683.50h |
| Root contact -> Sweep | 2.33h | 11.65h | 81.45h |
| Sweep -> CHoCH | 2.03h | 13.07h | 100.02h |
| FVG -> Fill | 0.85h | 15.63h | 142.66h |

A long interval is not automatically invalid.

The evidence matters because the baseline's causal story is stronger than simple chronological ordering.

## D-127 strategy question

The current D-127 implementation intentionally separates detection from scenario sequencing.

Detector facts are generic.

Scenario acceptance is largely:

```text
Root contact
-> first later direction-compatible M1 Sweep
-> later same-direction M1 protected-break CHoCH
-> causal fresh FVG set
```

The following were intentionally removed from strategy authorization:

```text
Root reintersection at Sweep
Root-owned Sweep family
sweep-time opposite M1 trend
sweep-time protected-reference freeze
child authority
extra CHoCH strength filter
```

This simplification previously solved over-filtering and implementation complexity.

It has now become a research target because broad profitability evidence is weak.

The correct question is not:

```text
Which old filter should be put back?
```

The correct question is:

```text
At which stage does conditional future-price information improve,
stay unchanged,
or deteriorate?
```

## Targeted directional source audit

No obvious sign reversal was found in:

```text
bullish/bearish protected-break handling
bullish/bearish FVG detection
LONG/SHORT Entry side
Root-distal SL side
objective reward sign
BUY_LIMIT/SELL_LIMIT order type
```

Therefore a simple SHORT sign bug is not the current leading explanation.

A full directional code audit remains appropriate if stage results continue to show extreme asymmetry.

## Research-governance change

Immediate priority is changed from:

```text
Frozen Regime V1 final confirmation / promotion
```

to:

```text
BASE EDGE AUDIT
```

This is not a change to the frozen model itself.

It is a change in what the project must prove before promotion.

## EDGE_AUDIT_V1 contract direction

The next harness must be shadow-only.

### Stage snapshots

```text
PLAN
ROOT_CONTACT
SWEEP
CHOCH
FVG
ENTRY
```

### Forward labels

Recorded only after future data becomes available:

```text
15m
1h
4h
24h
signed forward return

MFE
MAE
```

No future label can affect live/test strategy decisions at the time of the snapshot.

### D-142B deferred — standardized virtual exits

This remains part of the full audit plan but is **not implemented in D-142A**. After D-142A parity, use the actual strategy fill as the virtual anchor:

```text
same direction:
1R TP / 1R SL
2R TP / 1R SL
3R TP / 1R SL

opposite-direction mirror:
same timestamp
same absolute risk distance
1R / 2R / 3R
```

Purpose:

```text
separate direction edge
from entry timing
from structural TP
from SL geometry
```

### Matched null and simple baselines

After audit instrumentation is stable:

```text
time-matched/random null
EMA trend-follow
RSI mean-reversion
MACD crossover
```

Use simple frozen specifications and identical comparison rules.

## Decision tree

### Map already fails

If Map-level forward outcomes do not beat matched controls:

```text
the fundamental directional structure hypothesis is unsupported
```

Do not waste effort tuning Sweep/FVG.

### Map/Root work, trigger stages fail

If edge exists at Map/Root but deteriorates after Sweep/CHoCH/FVG:

```text
the main defect is trigger timing / causal ownership / confirmation delay
```

Research exactly one trigger difference at a time.

### Future D-142B: Entry works, structural exits fail

If later standardized 1R/2R/3R tick-order outcomes are positive but frozen structural TP/SL is negative:

```text
signal is not the main defect
objective/SL geometry is
```

### Only a stable regime subset works

Then Frozen Regime V1 or a later pre-registered regime model becomes relevant again.

## 2021 preservation

Do not open 2021 now.

The base strategy is under structural audit.

2021 should remain available for the final strategy structure that survives this process.

## Current bottom line

The current evidence does **not** justify the statement:

```text
The baseline Mentor continuation strategy has a broad positive edge,
and only needs better regime filtering.
```

The supportable statement is:

```text
The Gold lineage produced a promising frozen regime subset,
but the 2025 18-symbol NO-GATE expansion shows that
the underlying continuation baseline itself has not demonstrated broad edge.

The strongest warning is bearish continuation.

The next task is to locate where predictive information appears or disappears
before any new filter or promotion decision.
```

## D-142A implementation checkpoint

Prepared build:

```text
1.92R1L4
BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW
```

MAP is persistent state, so it is sampled on an H1 cadence after the complete same-timestamp group rather than only at map transitions.

Prepared funnel:

```text
MAP hourly state
-> PLAN
-> ROOT_CONTACT
-> SWEEP
-> CHOCH
-> FVG
-> ACTUAL_FILL identity
```

MAP through FVG receives 15m / 1h / 4h / 24h signed-return, MFE, and MAE labels. Exact fill-time virtual barriers are intentionally deferred to D-142B so the first instrumentation change can be parity-tested in isolation.

Status: **D-142A parity PASS; first six-symbol 2025 panel analyzed.**


## D-142A six-symbol stage audit — front-end escalation

The first post-parity panel used BTCUSD, CADJPY, GBPCAD, GOLD, SILVER, and USDJPY. It confirmed that the audit population is large enough for stage research and revealed that the next question must move upstream from CHoCH to direction formation.

### Direction/Root timing

Continuation medians:

```text
owner start -> Root causal structure: LONG 39.5h / SHORT 48.5h
PLAN -> Root contact:              LONG  6.5h / SHORT  9.0h
owner age at Root contact:         LONG 59h   / SHORT 73h
```

One stable owner can generate many later Root/PLAN opportunities. Among continuation owner episodes, median PLAN count was 9, p90 43, maximum 166. This does not imply 166 trades, but it proves repeated opportunity inheritance under one persistent directional owner.

### H1 direction warning

For each of the six symbols, future raw 24h return following H1-LONG states was lower than following H1-SHORT states. 42/60 comparable symbol-month blocks had the same inverse ordering. This is the strongest current reason to inspect map formation/refresh before adding downstream trigger filters.

### Root contact is not equivalent to trend confirmation

For continuation scenarios, 24h direction correctness changed approximately from:

```text
PLAN:         LONG 53.3% / SHORT 38.7%
ROOT_CONTACT: LONG 54.5% / SHORT 49.5%
```

Mean signed 24h response from contact was positive for both LONG and SHORT. Root contact can therefore contain a local reaction even if the higher-timeframe directional owner is stale or wrong for the final objective horizon.

### D-143 hypothesis set

Do not convert the observations into owner-age or Root-count cutoffs. Instrument the causal variables first:

```text
INITIAL_BOS timing
continuation BOS timing/count
protected-swing update timing
latest protected break
owner age / last-BOS age
all Root creation identities and ordinals
Root origin/create delay
Root create -> PLAN delay
PLAN -> physical contact delay
all physical contacts, including NO_PREPLAN
H1 and M30 context at Root create/contact
```

Then test whether direction accuracy decays with age, refreshes after continuation BOS, changes by Root ordinal, or only appears as a short-lived reaction at contact.


## D-143 front-end causal panel follow-up

The unified D-143 six-symbol rerun confirms that the negative baseline is not explained by one downstream defect alone. H1/M30 bearish continuation structure is weak as a forward classifier, but Root Contact frequently recovers local scenario-direction response. The current chain then loses a large part of that response by CHoCH/FVG. Repeated scenarios from the same directional/structure premise materially amplify losing streaks, but one-trade-per-premise counterfactuals remain far below the desired win rate.

This moves the evidence gate from static front-end filtering to standardized exact-tick entry timing. D-144 measures the same-direction and flipped-direction first-hit outcomes at Root Contact, Sweep, CHoCH, FVG and actual Fill without changing any strategy rule.

---

## D-144 GOLD exact-tick runner clue

The first D-144 exact-tick barrier run was restricted to GOLD 2025 because the full stage barrier population made Strategy Tester roughly 9x slower. This one-symbol result is research evidence, not a strategy promotion.

Continuation actual fills:

| Outcome geometry | Wins / 51 | Hit rate |
| --- | ---: | ---: |
| current structural TP | 14 / 51 | 27.45% |
| +1R before -1R | 30 / 51 | 58.82% |
| +1.5R before -1R | 25 / 51 | 49.02% |
| +2R before -1R | 20 / 51 | 39.22% |

This does not justify selecting a fixed R from the table. It proves a more useful fact: a substantial fraction of current eventual losers first become profitable, and the transition from `1R reaction` to `multi-R delivery` is now a separable research problem.

D-145 therefore asks what market state distinguishes:

```text
Fill -> +1R -> SL before 2R
vs
Fill -> +1R -> 2R+
```

using only information causally known at Fill and at the first +1R touch.
