# V10 Research State

Date: `2026-09-16`
Status: `ACTIVE HA-PRIMARY SHADOW RESEARCH / NO PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`

## 1. Generation boundary

V9 is closed as an active research generation.

V10 exists because the primary research authority changed from Grammar-centric entry with HA terminal research to HA-centric participation with Grammar / STD / SLOW / liquidity as context.

See:

`../v9/V9_RESEARCH_CLOSURE_AND_V10_TRANSITION_20260916.md`

## 2. Current baseline clock

Current shadow execution representation:

```text
FAST H4 HA
w=2
alpha=0.25

HC = (O+H+L+2C)/5
HO_t = 0.25*HO_(t-1) + 0.75*HC_(t-1)
```

This is not promoted authority.

Default shadow exit comparator:

```text
first completed opposite-color FAST H4 HA
```

Individual Child risk:

```text
causal H1 structural SL
ERA_RISK <= 4 screening
M1 first-touch stop screening
```

## 3. Current benchmark universe

2025-2026 H1-eligible FAST participation opportunities:

```text
2,489
ALL1 PnL +10,007.27
PF 1.368
DD 2,034.28
+253.72R
```

Future-only early-third answer sheet:

```text
567 Oracle bars
PnL +23,344.73
PF 15.157
DD 148.81
+733.18R
```

## 4. Current representation findings

Early-third predictability:

```text
STD H4 HA          mean AUC 0.850
Smooth STD H4 HA   mean AUC 0.849
SLOW H4 HA         mean AUC 0.847
FAST H4 HA         mean AUC 0.822
```

Strongest current single LTF families:

```text
M15 FAST HA body flow ~0.64 AUC
M30 FAST HA body flow ~0.63 AUC
H1 standard HA body  ~0.62 AUC
```

H4 FAST clock + compact MTF phase information improves the weaker 2026 early-zone AUC modestly.

## 5. Current probability decomposition

Current useful conceptual heads:

```text
P_EARLY / P_RUNWAY
P_WIN
P_STD_SUPPORT
```

Interpretation:

- `P_EARLY / P_RUNWAY`: is the current FAST run still early enough / capable of substantial further extension?
- `P_WIN`: does a new Child look economically healthy under structural risk?
- `P_STD_SUPPORT`: does standard H4 HA support the current FAST direction, accounting for its own early-run state?

Diagnostic unbounded product:

```text
P_EARLY * P_WIN * P_STD_SUPPORT
```

with normalized / rounded sizing reached:

```text
PnL +18,316.55
PF 1.676
+517.17R
```

but allowed orders up to 12 units and therefore is not an acceptable final policy.

## 6. Current bounded research candidate

Consumed-data research diagnostic:

```text
score = P_RUNWAY(3x) * P_WIN * P_STD_SUPPORT

prior-history quartile mapping
bottom 50% -> 0
50-75%    -> 1 unit
top 25%   -> 3 units
```

2025-2026:

```text
entries 1,159
lot-units 2,313
PnL +14,827.57
PF 1.553
DD 2,638.04
+388.88R
max order 3 units
max concurrent 12 units
```

Oracle-bar classification:

```text
true Oracle bars 567
captured 456
recall 80.4%
precision 39.3%
```

The main remaining problem is false-positive reduction without destroying Oracle recall or trend right tail.

## 7. Runway result

Relative runway labels:

```text
L >= m*k
```

become easier to classify as `m` becomes extreme, but economic value does not monotonically follow AUC.

Examples under the same bounded diagnostic:

```text
m=2  PnL +15,020.83 / PF 1.592 / DD 3,777.67
m=3  PnL +14,827.57 / PF 1.553 / DD 2,638.04
m=4  PnL +13,576.33 / PF 1.562 / DD 2,373.42
m=8  PnL +11,241.12 / PF 1.497 / DD 1,637.43
```

Do not convert one `m` into a hidden rule.

## 8. Current state-machine hypothesis

The emerging semantic structure is:

```text
FAST PHA begins
-> Oracle-like score rises
-> FRONT-LOAD exposure
-> score remains strong
-> CONTINUATION state
-> add only if runway / economic quality still justify it
-> score deteriorates
-> STOP-ADDING
-> first opposite FAST HA
-> EXIT
```

Observed score transition:

```text
TOP_NEW
Oracle rate ~50.9%
average Child PnL +5.83

TOP_PERSIST
Oracle rate ~31.8%
average Child PnL +12.24
```

Therefore “early Oracle position” and “confirmed profitable continuation” are not the same state.

## 9. Robustness warning

Run-level bootstrap for the bounded `m=3` diagnostic vs ALL1:

```text
observed delta +4,820.30
pooled P(delta>0) 88.7%
95% interval -3,207 to +12,363

2025:
95% interval +410 to +6,474
P(delta>0) 98.6%

2026:
95% interval -6,028 to +8,112
P(delta>0) 67.1%
```

The improvement is not yet uniformly stable.

Right-tail concentration remains material.

## 10. Current next objective

Primary next contract:

`V10_NEXT_RESEARCH_CONTRACT_ORACLE_PARTICIPATION_20260916.md`
