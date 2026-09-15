# V10 HA-Primary Research Checkpoint

Date: `2026-09-16`
Status: `CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY`
Market: `GOLD# ONLY`

## 1. Objective

This checkpoint records the research performed after the HA-primary architecture became the main question.

The working question is:

> Can a causal HA-primary state approximate the future “early profitable participation” answer sheet closely enough to place exposure earlier and more efficiently than a Grammar-primary entry clock?

## 2. V9 predecessor reference

V9 2025-2026 comparator:

```text
Grammar BASE
450 Children
PnL +5,307.95
PF 1.515
DD 1,700.62

V9 Literal Exit Oracle
PnL +16,476.18
PF 3.799
DD 856.81
```

V10 does not claim direct superiority from these numbers because the participation universe is different.

## 3. Initial HA-primary result

FAST `w2/a0.25`, H1 structural risk eligibility, M1 first-touch stop screening:

```text
2,489 eligible FAST opportunities
PnL +10,007.27
PF 1.368
DD 2,034.28
+253.72R
```

This showed that HA-primary participation can produce more raw opportunity but needs substantial state selection.

## 4. FAST / STD / SLOW formula study

The transformed family used:

```text
HA_CLOSE(w) = (O+H+L+w*C)/(3+w)

HA_OPEN_t
= alpha*HA_OPEN_(t-1)
+ (1-alpha)*HA_CLOSE_(t-1)
```

Current semantic examples:

```text
FAST  = w2, alpha 0.25
STD   = w1, alpha 0.50
SLOW  = w2, alpha 0.75
```

Formula-level own early-third predictability:

| Formula | Mean AUC |
|---|---:|
| STD `w1/a0.50` | 0.850 |
| Smooth STD `w1/a0.75` | 0.849 |
| SLOW `w2/a0.75` | 0.847 |
| FAST `w2/a0.25` | 0.822 |
| Close-heavy FAST `w4/a0.25` | 0.808 |

Interpretation:

- FAST is useful for execution responsiveness.
- STD / slower HA better represent broader run location.
- one HA formula should not automatically own every semantic role.

## 5. Multi-timeframe HA study

Single-coordinate early-third discrimination was strongest around:

```text
M15 FAST HA body flow     ~0.64 AUC
M30 FAST HA body flow     ~0.63 AUC
H1 standard HA body       ~0.62 AUC
```

H4 FAST clock-only model:

```text
2025 AUC ~0.821
2026 AUC ~0.799
```

Compact MTF phase flags improved the weaker year modestly:

```text
2026 ~0.806
```

Throwing all MTF HA coordinates into one feature soup degraded results.

## 6. Participation Oracle

Answer sheet:

```text
k = current completed FAST HA number in its same-color run
L = final run length

EARLY_THIRD = 1 iff 3*k <= L
```

2025-2026:

```text
567 true early-third entries
PnL +23,344.73
PF 15.157
DD 148.81
+733.18R
```

This is future-only and impossible to use directly. Its purpose is to locate the information gap.

## 7. Direct Oracle-likeness model

A simple prior-only Logistic model using causal FAST state, Grammar, liquidity, Pressure/LTF, and H1 risk reached approximately:

```text
2025 AUC 0.818
2026 AUC 0.800
```

Probability-proportional sizing, normalized to approximately the same aggregate exposure, improved ALL1 but remained far from Oracle.

## 8. FAST / STD probability context

Using FAST execution while using STD early-zone probability as context materially improved exposure placement.

Example:

```text
FAST + STD probability sizing
PnL +13,046.22
PF 1.485
DD 1,878.83
+300.78R
```

This supported the role split:

```text
FAST -> execution
STD  -> maturity / location context
```

## 9. Two-head decomposition

The research separated:

```text
P_EARLY
= probability that the current FAST bar belongs to the final early portion

P_WIN
= probability that the new Child has positive structural-SL / FAST-NHA economics
```

`P_WIN` alone had only modest AUC:

```text
2025 ~0.582
2026 ~0.535
```

but the product materially improved sizing:

```text
P_EARLY * P_WIN
rounded normalized sizing:

PnL +15,819.03
PF 1.599
+482.57R
```

Interpretation:

A weak economic-quality head can still be useful when conditioning an already strong Oracle-likeness head.

## 10. Standard-HA directional support

Directional support was defined semantically:

```text
if STD direction == FAST direction:
    support = P_STD_EARLY
else:
    support = 1 - P_STD_EARLY
```

Diagnostic unbounded combination:

```text
P_EARLY
* P_WIN
* P_STD_SUPPORT
```

rounded normalized result:

```text
PnL +18,316.55
PF 1.676
DD 3,440.99
+517.17R
max single order 12 units
```

This is important information evidence but not an acceptable final sizing policy because exposure concentration becomes too large.

## 11. Bounded sizing

To prevent the unbounded product from hiding leverage, a consumed-data bounded diagnostic was tested.

Prior-history quartile map:

```text
bottom 50% -> 0
50-75%    -> 1 unit
top 25%   -> 3 units
```

with score:

```text
P_RUNWAY(3x) * P_WIN * P_STD_SUPPORT
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

Oracle similarity:

```text
true Oracle bars 567
captured 456

recall 80.4%
precision 39.3%
```

The next problem is primarily false-positive reduction.

## 12. Runway study

Relative survival answer sheets:

```text
L >= m*k
```

showed higher AUC for more extreme runway, but higher AUC did not mean higher economic value.

Under the same bounded diagnostic:

| m | Mean AUC | PnL | PF | DD |
|---:|---:|---:|---:|---:|
| 2 | 0.804 | +15,020.83 | 1.592 | 3,777.67 |
| 3 | 0.809 | +14,827.57 | 1.553 | 2,638.04 |
| 4 | 0.819 | +13,576.33 | 1.562 | 2,373.42 |
| 5 | 0.828 | +13,156.94 | 1.550 | 2,367.75 |
| 8 | 0.854 | +11,241.12 | 1.497 | 1,637.43 |

No `m` value is promoted.

## 13. Expected Oracle-count catch-up

The final early-third Oracle would place approximately:

```text
floor(L/3)
```

unit entries.

A causal state-conditioned expectation was built from:

```text
P(L>=3)
+ P(L>=6)
+ P(L>=9)
+ P(L>=12)
+ P(L>=15)
```

and exposure was added only to catch up to the expected target.

After equal-exposure normalization:

```text
PnL +14,011.52
PF 1.486
DD 1,761.01
+385.13R
```

This is structurally cleaner than a fixed “add every three bars” rule.

## 14. Cumulative bounded ladders

A state-based cumulative target was also tested:

```text
weak -> 0
medium -> 1 unit
strong -> 3 units
```

Exposure only increased toward the target; it was not retrospectively reduced.

A conservative `m=5` example:

```text
PnL +9,020.25
PF 1.516
DD 1,327.26
1,451 lot-units
max concurrent 3 units
```

An “always initial 1 unit, then state-confirmed 2/3 units” example:

```text
m=4
PnL +9,601.91
PF 1.450
DD 1,548.15
1,790 lot-units
max concurrent 3 units
```

These are policy-shape diagnostics, not rules.

## 15. TOP_NEW vs TOP_PERSIST

The score trajectory produced a useful distinction.

Pooled:

```text
TOP_NEW
N 448
Oracle rate 50.9%
Avg Child PnL +5.83

TOP_PERSIST
N 129
Oracle rate 31.8%
Avg Child PnL +12.24
```

Interpretation:

- `TOP_NEW` is more Oracle-like / front-load-like;
- `TOP_PERSIST` is less “early” but more economically continuation-like.

This supports a state machine rather than one static score.

## 16. Exit studies

With HA-primary participation, first opposite FAST HA remained the best current efficient exit comparator.

Examples:

```text
FAST immediate exit
PnL +8,739.25
PF 1.521
DD 1,833.27
Position-hours 28,277

SLOW-confirmed exit
PnL +3,138.52
PF 1.130
DD 3,635.60
Position-hours 51,352
```

Grammar-confirmed delayed exit produced:

```text
PnL +16,572.44
PF 1.530
DD 4,648.68
Position-hours 151,090
Max concurrent 46
```

but was dominated by a few large campaigns and extreme exposure. It remains a separate right-tail research lane, not the current base exit.

## 17. Robustness

Bounded `m=3` vs ALL1 run-level bootstrap:

```text
observed delta +4,820.30

pooled:
P(delta > 0) 88.7%
95% interval -3,207 to +12,363

2025:
P(delta > 0) 98.6%
95% interval +410 to +6,474

2026:
P(delta > 0) 67.1%
95% interval -6,028 to +8,112
```

The 2026 result is not yet stable.

Right-tail concentration also remains material.

## 18. Current interpretation

The research has moved from:

```text
"How many HA bars have survived?"
```

to:

```text
"How much runway is still plausible?"
"Is this new Child economically healthy?"
"Does broader STD HA context support the FAST direction?"
"Is the state newly strong or merely persistently strong?"
```

This is the current V10 research foundation.
