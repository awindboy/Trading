# V9 Next Research Contract — Terminal State Table Stability and Oracle-Regret Decomposition

Date: `2026-09-16`
Status: `ACTIVE SHADOW STRATEGY-RESEARCH CONTRACT`
Production authority: `NONE`
Strategy authority change: `NONE`
Market: `GOLD# ONLY`

## 1. Objective

The terminal research now has a coherent repeat-HA state hypothesis:

```text
primary participation loss
+ opposite structural pressure gain
+ mature survived-reversal cycle
+ strong current reversal delivery
```

The next task is not to add more indicators.

It is:

> Determine whether this state representation is stable and causally useful, or whether the observed best combination is mostly consumed-data combination selection.

The literal answer sheet is:

```text
TRUE LAST ACCEPTED CHILD
-> first completed opposite-color H4 HA after that Child
-> close all still-open route Children
```

The corrected current answer sheet contains `157` routes.

## 2. Frozen comparators

Do not change the prototype strategy authority.

For the current research ledger:

```text
COMMON BASE
693 Children
PnL +7,210.31
PF 1.5655
DD 1,700.62

LITERAL ORACLE
693 Children
157 Oracle routes
PnL +19,827.81
PF 3.6176
DD 856.81
```

2025-2026 repeat-state reporting slice:

```text
450 Children
BASE +5,307.95
ORACLE +16,476.18
99 Oracle routes
43 repeat-cycle Oracle routes
```

## 3. Current representation hypotheses

### H1 — primary participation loss

Measure route-relative loss of same-side H4 liquidity participation between opposite-HA opportunities.

Do not replace it with a fixed Child count or fixed time rule.

### H2 — opposite structural pressure gain

Measure route-relative increase in opposite-side liquidity threat.

### H3 — cycle maturity

Use `CycleMin` only where a real previous opposite-HA episode exists.

Never fabricate CycleMin on FIRST-HA1 routes.

### H4 — reversal delivery

Use Pressure / transformed-HA / LTF delivery as causal reversal-quality coordinates.

### H5 — PHA/NHA and position damage

Keep these as secondary coordinates, especially for FIRST-HA1 / no-cycle cases.

## 4. Current observed benchmarks

Discrimination-first repeat state:

```text
SAME_PARTICIPATION_LOSS + RESILIENT_PRESSURE
mean walk-forward AUC 0.749
2025 0.768
2026 0.730
```

Consumed-data economic best:

```text
SAME_PARTICIPATION_LOSS
+ OPP_PRESSURE_GAIN
+ CYCLE_MIN
+ RESILIENT_PRESSURE

2025-2026
PnL +9,528.95
BASE delta +4,221.00
Oracle recovery 37.79%
EXACT 23
EARLY 8
LATE 5
```

Nested prior-only combination-selection control:

```text
PnL +6,064.84
BASE delta +756.89
Oracle recovery 6.78%
EXACT 9
EARLY 8
LATE 8
```

The gap between these two results is the main research problem.

## 5. Required next work — repeat-state lane

### A. Route-regret decomposition

For the observed four-state representation, produce route-level:

```text
BASE_ROUTE_PNL
ORACLE_ROUTE_PNL
CANDIDATE_ROUTE_PNL
ORACLE_GAIN
CANDIDATE_GAIN
ORACLE_REGRET
MATCH / EARLY / LATE / MISS
```

Rank by economic regret, not error count.

### B. Explain the EARLY routes

For every EARLY route reconstruct:

```text
previous opposite HA
survival after that HA
primary re-extension
same-side liquidity changes
opposite liquidity changes
CycleMin
Pressure / LTF delivery
open Child damage
PHA/NHA state
later accepted Child chronology
```

No future price may be used in a live feature.

### C. Explain repeat-state Oracle misses

There are `43` 2025-2026 Oracle routes with cycle state available.
The observed best combination matches `23` exactly.

Explain the remaining repeat-state oracle opportunities before adding new feature families.

### D. Stability

Test whether the same semantic decomposition works under:

- prior-only scaling;
- fixed feature definitions;
- fixed combination;
- year splits;
- both directions;
- route-regret weighting;
- actual executable H4 Bid/Ask.

Do not optimize a new threshold independently for each year/direction.

## 6. Required next work — FIRST-HA1 lane

FIRST-HA1 / no-prior-opposite-HA routes cannot use CycleMin.

Study only causal states available at that event:

```text
absolute / Child-relative H4 liquidity geometry
position damage
reversal delivery
PHA close penetration / body accumulation
current route participation state
```

Do not substitute:

```text
Nth Child
fixed elapsed time
future Child count
future route outcome
```

for missing cycle history.

## 7. Combination policy

Before screening a new combination, state its semantic reason.

Preferred order:

1. single state;
2. two-state interaction;
3. three-state interaction;
4. only then four-state interaction.

Every comparison must report:

```text
ORACLE denominator counts
EXACT / total Oracle
EARLY / total Oracle
LATE / total Oracle
MISS / total Oracle
FALSE_NO_ORACLE
BASE / candidate / ORACLE PnL
Oracle recovery
PF / DD
right-tail P90 / P95 / max
```

AUC is secondary.

## 8. Model controls

Mechanical percentile/rank representations remain the primary baseline.

Logistic / shallow Tree / HGB may be used only on the exact same causal variables and timestamps.

Model complexity is not an excuse to hide state semantics.

## 9. Leakage rules

Never use:

- true last Child;
- future Child count;
- future challenge;
- later HA / price that is not yet completed;
- eventual route PnL;
- oracle timestamp;
- post-stop Child resurrection.

An accidental future reveal contaminates the interval. Do not repair it with hindsight trades.

## 10. Promotion gate

No terminal candidate can alter strategy authority until it has:

- a fixed causal state definition;
- meaningful oracle-gap recovery after combination-selection controls;
- stable year/direction behavior;
- preserved right tail;
- actual-tick executable replay;
- forward-demo evidence.

Until then, prototype exits remain unchanged.
