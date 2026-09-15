# V9 Terminal State Table Research Checkpoint

Date: `2026-09-16`
Status: `CONSUMED-DATA SHADOW RESEARCH / LITERAL ORACLE 157 / NOT STRATEGY AUTHORITY`
Market: `GOLD# ONLY`
Base GitHub HEAD: `f57e10c670666dd763152e6302d0952f9a7a2f5d`

## 1. Objective

This checkpoint consolidates the strongest terminal-stage ideas studied so far into a common causal state table and asks:

> Which combination best distinguishes a normal opposite-H4-HA pullback from a terminal opposite-H4-HA event, and which combination produces the best chronological terminal-exit economics?

The answer sheet is the corrected literal oracle from:

`V9_ALL_TO_CHALLENGE_ACTUAL_TICK_LEDGER_REBUILD_20260916.md`

The strategy prototype is unchanged.

## 2. Evaluation frame

Common comparable cohort:

```text
191 routes
693 closed Children

BASE +7,210.31 / PF 1.5655 / DD 1,700.62
LITERAL ORACLE +19,827.81 / PF 3.6176 / DD 856.81
```

For state-combination walk-forward comparison, the main reporting slice is 2025-2026:

```text
450 Children
BASE +5,307.95
LITERAL ORACLE +16,476.18
99 Oracle routes
```

2025 state scaling uses prior 2024 history.
2026 state scaling uses prior 2024-2025 history.

All supplied periods are consumed. These are not untouched OOS results.

## 3. Earlier ideas re-tested on the new actual-tick ledger

### 3.1 Cycle / repeat-HA state

For repeated opposite HA1 events:

```text
Extension
= favorable primary re-extension after the previous opposite HA1
  normalized by completed H4 ATR180

Giveback
= distance from that re-extension extreme back to the current opposite HA1
  normalized by ATR180

CycleMin = min(Extension, Giveback)
```

On the rebuilt event population, prior findings remained directionally valid.
Post-HA `ConfirmedCycle2` improved discrimination but waiting two completed H4 bars harmed exit economics.

Coefficient-free immediate `CycleMin > 0` screening:

```text
PnL +9,124.82
BASE delta +1,914.51
DD 1,627.67
```

This threshold is not authority.

### 3.2 Pressure / transformed HA

The exact old Pressure coefficients were not frozen in authority.
A robustness family was re-tested instead of inventing one coefficient set.

Transformed HA / Pressure remained useful primarily as a **reversal-quality coordinate**, not as a replacement HA event generator.

Current reproducible research Pressure representation uses:

```text
Location = (C - (H+L)/2) / ((H-L)/2)
Size = (H-L) / ATR180
PressureClose = Location * tanh(k * Size)
PressureOpen = recursive prior Pressure state
PressureBody = PressureClose - PressureOpen
PressureFlow2 = two-bar PressureBody flow
```

No exact `k/lambda` is promoted.

### 3.3 LTF delivery

Inside each H4 opposite-HA bar, M5/M15/M30 HA and raw price paths were reconstructed causally.

The useful signal was not simple opposite-color count.
More useful coordinates were:

```text
opposite directional efficiency
opposite HA body delivery
late-vs-early persistence
primary-side wick suppression
```

LTF morphology alone improved BASE only modestly and created costly EARLY exits.
Its role is best interpreted as reversal-delivery quality.

### 3.4 Position damage

At each H4 HA decision the study marked every still-alive Child with actual finalized Bid/Ask.

Useful damage coordinates:

```text
max single Child unrealized loss / Child entry ATR180
sum of losing-Child losses / Child entry ATR180
losing Child count / fraction
```

On consumed-data threshold diagnostics, loss **depth** was materially more useful than loss-Child count.

Example diagnostic only:

```text
max single Child loss >= 0.75 ATR
PnL +9,547.00
BASE delta +2,336.69
DD 1,639.02
```

The `0.75` value was observed on consumed data and must not become authority.

## 4. PHA / NHA state

Definitions:

```text
PHA = contiguous primary-color H4 HA run immediately before an opposite HA1
NHA = contiguous opposite-color H4 HA run beginning at that HA1
```

The most useful geometry was not raw NHA high-low range by itself.

More useful coordinates:

```text
NHA close penetration
= how much of the PHA progress has been surrendered by current opposite-HA close

NHA body accumulation / PHA range
= cumulative opposite HA body delivery relative to PHA range
```

For terminal-vs-false-early episodes, median `NHA range / PHA range` was consistently larger in terminal episodes:

```text
             false early   terminal
NHA1            0.239        0.338
NHA2            0.326        0.451
NHA3            0.422        0.495
NHA4            0.448        0.558
```

But waiting for NHA range to cross a threshold was economically too late.
PHA/NHA is therefore a state coordinate, not a standalone exit authority.

## 5. Historical liquidity / location families reconstructed

The earlier terminal-combination checkpoint found useful information in:

```text
H4 liquidity distance ratio
Child-relative opposite-liquidity movement
H4 Donchian primary location
H1 primary-aligned RSI
HA opposite body strength
```

These were rebuilt against the new actual-tick ledger.

A particularly strong route-relative raw coordinate survived:

```text
current HA1 same-side active H4 liquidity count
-
previous HA1 same-side active H4 liquidity count
```

Oriented so that same-side participation loss is more terminal-like:

```text
AUC 2024 0.774
AUC 2025 0.714
AUC 2026 0.752
```

This is stronger and more stable than most absolute indicator coordinates.

## 6. State families

The current state-table vocabulary is:

### SAME_PARTICIPATION_LOSS

Route-relative primary participation deterioration from the previous opposite HA1:

```text
same-side active H4 liquidity decreases
and/or
nearest same-side H4 destination becomes farther
```

### OPP_PRESSURE_GAIN

Route-relative opposite structural pressure:

```text
opposite-side active H4 liquidity increases
and/or
nearest opposite H4 destination becomes closer
```

### CYCLE_MIN

Maturity of the survived-reversal -> primary re-extension -> giveback cycle.

### REVERSAL_PRESSURE

Current opposite PressureFlow without CycleMin weighting.

### RESILIENT_PRESSURE

Research representation:

```text
ResilientPressure
= opposite PressureFlow * CycleMin / (1 + CycleMin)
```

This is a research representation only; no coefficient threshold is frozen.

### POSITION_DAMAGE

Current alive-Child unrealized damage, era normalized.

### DELIVERY

Pressure / transformed-HA / LTF directional-delivery family.

### PHA_NHA

Current PHA-to-NHA close/body/range damage state.

### OLD_BEST3

Rebuilt form of the previous proof-of-concept family:

```text
Child-relative opposite-H4-liquidity pressure
+ H4 Donchian primary-location loss
+ opposite HA body strength / ATR180
```

## 7. Single-state economics on repeat-HA1 population

2025-2026 full Child-ledger replay with prior-history operating-point selection:

| State | PnL | Delta vs BASE | Oracle recovery | PF | DD |
|---|---:|---:|---:|---:|---:|
| SAME_PARTICIPATION_LOSS | +7,139.44 | +1,831.49 | 16.40% | 1.781 | 1,994.19 |
| OPP_PRESSURE_GAIN | +7,096.48 | +1,788.53 | 16.01% | 1.736 | 1,138.86 |
| OLD_BEST3 | +6,819.72 | +1,511.77 | 13.54% | 1.702 | 1,681.59 |
| RESILIENT_PRESSURE | +6,711.11 | +1,403.16 | 12.56% | 1.704 | 2,295.99 |
| POSITION_DAMAGE | +6,167.47 | +859.52 | 7.70% | 1.677 | 1,612.24 |

Classification AUC and economic value are not identical; EARLY route regret dominates.

## 8. Best discrimination combination

Among repeat-HA1 state-family combinations, the strongest stable EXACT-vs-EARLY discrimination was:

```text
SAME_PARTICIPATION_LOSS
+
RESILIENT_PRESSURE
```

Walk-forward AUC:

```text
2025 0.768
2026 0.730
mean 0.749
minimum-year AUC 0.730
```

2025-2026 economics:

```text
PnL +7,387.79
BASE delta +2,079.84
Oracle recovery 18.62%
PF 1.795
DD 1,693.61

EXACT 12 / 99 total Oracle
EARLY 4
LATE 1
MISS 82
FALSE_NO_ORACLE 1
```

This is the current strongest **discrimination-first** state pair.

## 9. Best observed consumed-data economic combination

After screening combinations of the previously successful state families, the best observed consumed-data repeat-state combination was:

```text
SAME_PARTICIPATION_LOSS
+
OPP_PRESSURE_GAIN
+
CYCLE_MIN
+
RESILIENT_PRESSURE
```

### 2025

```text
BASE +2,848.16
CANDIDATE +4,902.92
LITERAL ORACLE +8,083.61

BASE delta +2,054.76
Oracle recovery 39.25%
PF 2.606
DD 607.97

EXACT 15 / 58 total Oracle
EARLY 5
LATE 3
MISS 35
FALSE 0
```

### 2026

```text
BASE +2,459.79
CANDIDATE +4,626.03
LITERAL ORACLE +8,392.57

BASE delta +2,166.24
Oracle recovery 36.51%
PF 1.828
DD 1,529.50

EXACT 8 / 41 total Oracle
EARLY 3
LATE 2
MISS 28
FALSE 1
```

### 2025-2026 pooled

```text
BASE      +5,307.95
CANDIDATE +9,528.95
ORACLE   +16,476.18

BASE delta +4,221.00
Oracle recovery 37.79%
PF 2.103
WR 47.33%
DD 1,529.50

EXACT 23 / 99 = 23.23%
EARLY 8
LATE 5
MISS 63
FALSE_NO_ORACLE 1
```

Only `43` of the `99` 2025-2026 Oracle routes have repeat-cycle state available at the oracle event.
Within that applicable repeat-Oracle subset, exact matches are:

```text
23 / 43 = 53.49%
```

This result is **not a promoted rule**.

## 10. Ablation

Removing one state from the observed best combination:

```text
FULL                                           +4,221
without RESILIENT_PRESSURE                     +2,819
without CYCLE_MIN                              +1,923
without SAME_PARTICIPATION_LOSS                +1,114
without OPP_PRESSURE_GAIN                        +693
```

The four dimensions are therefore not explained by one trivial component on this consumed screen.

## 11. Non-redundant control

Because `ResilientPressure` already contains `CycleMin`, a clean screen split it into pure reversal pressure and cycle state.

Strong non-redundant combinations remained:

```text
SAME_PARTICIPATION_LOSS
+ OPP_PRESSURE_GAIN
+ REVERSAL_PRESSURE
+ LTF_DELIVERY

2025-2026 BASE delta +3,521.01
both years positive
```

and:

```text
SAME_PARTICIPATION_LOSS
+ OPP_PRESSURE_GAIN
+ CYCLE_MIN
+ REVERSAL_PRESSURE

BASE delta +3,330.11
both years positive
```

Therefore the observed structure is not solely an artifact of counting `CycleMin` twice.

## 12. Critical overfit control

The `+4,221 / 37.8%` combination was identified after comparing many combinations on consumed 2025-2026 outcomes.

To test selection instability, the combination itself was chosen using prior history only:

```text
2025 combination chosen using 2024 only
2026 combination chosen using 2024-2025 only
```

Nested prior-only selection produced:

```text
PnL +6,064.84
BASE delta +756.89
Oracle recovery 6.78%
PF 1.642
DD 2,344.84

EXACT 9
EARLY 8
LATE 8
```

Therefore:

> The four-state combination is the strongest current consumed-data representation hypothesis, not validated future performance.

This warning is mandatory in any handoff.

## 13. Current interpretation

The strongest common structure across the research is:

```text
previous opposite HA did not terminate the Journey
-> primary re-extended
-> a mature giveback cycle formed
-> same-side H4 participation deteriorated
-> opposite structural pressure increased
-> current opposite reversal delivery became strong
-> terminal probability increased
```

This is materially more coherent than adding a generic indicator to HA1.

## 14. FIRST-HA1 unresolved lane

`CycleMin` / route-relative prior-HA transition features require a previous opposite HA event.

2025-2026:

```text
99 literal Oracle routes
43 Oracle routes have repeat-cycle state
56 do not
```

Therefore the current best repeat-state representation cannot solve the entire terminal problem.

FIRST-HA1 / no-prior-opposite-HA routes remain a separate research lane where:

```text
position damage
delivery quality
PHA/NHA close penetration/body accumulation
absolute / Child-relative H4 liquidity state
```

must be studied without fabricating a fake CycleMin.

## 15. Research conclusion

Current priority is **not more broad feature mining**.

The next work is:

1. route-regret decomposition of the repeat-state best representation;
2. explain the `EARLY 8`, `LATE 5`, and repeat-state Oracle misses;
3. determine why the best consumed combination is not selected stably in nested prior-only tests;
4. preserve the repeat-state representation if it survives;
5. separately solve FIRST-HA1 routes;
6. only then consider actual-tick EA implementation of a promoted terminal candidate.

No strategy authority change is made by this checkpoint.
