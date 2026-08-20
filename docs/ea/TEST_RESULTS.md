# EA Validation and Research Evidence Ledger

Date recorded: 2026-08-20
Repository base checked before this update: `2ce911297ea2f5b8d26f0ba78d2ac132445ac0a8`

This file keeps the current high-value execution and research evidence. Historical results remain valid unless explicitly marked contaminated or superseded.

## Calculation convention

Canonical price R:

```text
risk_distance = abs(actual_fill - frozen_strategy_SL)

LONG R  = (actual_exit - actual_fill) / risk_distance
SHORT R = (actual_fill - actual_exit) / risk_distance
```

Using the absolute denominator is required so rare fill-through-stop cases remain losses rather than changing sign mathematically.

Other conventions:

```text
year attribution = entry/fill year
execution-divergent symbol-year = not final profitability evidence
late-year entry cohort should be allowed to reach terminal exit
```

## 1. Historical D-135A 2025 GOLD execution regression

Identity:

```text
build = 1.91
phase = D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX
SL = ROOT_OB_DISTAL_20
period = 2025
Every tick based on real ticks
```

Ledger:

```text
rows = 234,277
SHA-256 = 1bd119c4d3aea9ab759a24541de71be01d0379fa948927bede2a1dae5b9d7b65
```

Execution result:

```text
geometry ready = 74
pending accepted = 73
pending canceled = 15
filled = 58
closed = 58
opposite-direction conflict = 1
execution divergence = 0
```

Classification:

```text
D-135 performance optimization = PASS
D-135A canceled-pending lifecycle hotfix = PASS for this 2025 fixture
D-134 execution-lifecycle parity = PASS
```

Runtime improved from roughly nine hours in D-134 to about seven minutes in D-135A-class execution.

## 2. Historical 2023–2024 execution edge case

The prior two-year run exposed a still-unfixed recoverable cancellation case:

```text
2023-12-20 LONG pending accepted
2023-12-22 strategy cancellation required
broker cancel rejected
retcode 10018 / Market closed
2024-01-05 stale pending later filled
-> FILLED_AFTER_STRATEGY_CANCELLATION
-> EXECUTION_DIVERGENCE
```

This issue is confirmed again across multiple 2025 symbols in Section 7.

## 3. Historical Gold baseline annual evidence

Clean build-1.91 attribution previously used for regime discovery:

| Year | Clean closed trades | Wins | Total R | Mean R |
|---|---:|---:|---:|---:|
| 2023 | 70 | 23 | +44.937806R | +0.641969R |
| 2024 | 55 | 5 | -35.555410R | -0.646462R |
| 2025 | 58 | 14 | +8.680565R | +0.149665R |

Continuation-only:

```text
2023: 64 trades / +48.308745R
2024: 48 trades / -28.452965R
2025: 51 trades / +15.936463R
```

This evidence motivated regime research because the same baseline was strongly unstable by year.

## 4. Frozen Regime Research V1 Development evidence

Parent:

`M30_CLEAN_PERSISTENT`

Direct 2023–2025:

```text
46 trades / 15 wins
+45.436530R
mean +0.987751R
Max DD -11.204262R
longest losing streak 11
execution divergence = 0
```

Frozen Expansion:

`M30_CLEAN_PERSISTENT_EXPANDING`

Direct 2023–2025:

```text
24 trades / 13 wins
+49.797314R
mean +2.074888R
PF ≈ 5.4352
Max DD -5.173397R
longest losing streak 5
execution divergence = 0
```

All 24 Expansion trades were exact Parent members with identical R.

Expansion removed:

```text
22 Parent trades
2 wins / 20 losses
-4.360784R
mean -0.198217R
```

This remains valid Development evidence.

## 5. Frozen Regime Research V1 2022 first sealed OOS

Baseline continuation:

```text
72 trades / 15 wins
-14.476581R
mean -0.201064R
Max DD -20.764118R
longest losing streak 18
```

Parent:

```text
16 trades / 3 wins
-3.825354R
mean -0.239085R
Max DD -5.741120R
longest losing streak 5
```

Frozen Expansion:

```text
6 trades / 1 win
+0.994756R
mean +0.165793R
Max DD -3.012334R
longest losing streak 3
execution divergence = 0
```

Pre-registered classification:

```text
2022 FIRST SEALED OOS = PASS
Expansion incremental support vs Parent = PASS
```

Caveat:

```text
6 trades
1 winner ≈ +6.02R
5 losses ≈ -5.03R
```

This is transfer evidence, not broad robustness proof.

## 6. 2025 18-symbol NO-GATE source

User-provided bundle analyzed directly:

```text
ALL.zip
bytes = 6,847,884
SHA-256 = 9408fd91c70a2a75e55888f43fa915652cd5b3b24b10415b536b49d74a9ea6eb
files = 18 CSV
```

Symbols:

```text
BTCUSD CADCHF CADJPY CHFJPY EURCAD EURCHF EURGBP EURJPY EURUSD
GBPCAD GBPCHF GBPJPY GBPUSD GOLD SILVER USDCAD USDCHF USDJPY
```

All files identify:

```text
build = 1.92R1L3
phase = REGIME_RESEARCH_V1_MULTI_SYMBOL_RISK_SIZING
regime_mode = BASELINE_NO_REGIME_GATE
event_log_mode = RESEARCH_COMPACT
position_sizing_mode = FIXED_RISK_MONEY
fixed_risk_money = 100
SL = ROOT_OB_DISTAL_20
strategy_semantics = D134_EXECUTION_CORE_UNCHANGED
```

Aggregate funnel:

```text
PLANs = 22,272
geometry ready = 1,957
NO_R = 112
exposure blocked = 157
execution infeasible = 107
orders accepted = 1,681
positions filled = 1,477
pending canceled = 199
cancel rejected = 3
execution divergences = 8
positions closed = 1,463
```

Tester-end state:

```text
filled - closed = 14 open filled positions
active execution = 17
```

The 2025-origin cohort is right-censored and should later be terminalized beyond year-end.

## 7. 2025 cross-symbol execution divergences

### Recoverable cancel rejection followed by stale fill — 3

```text
EURGBP:
cancel rejected 2025-02-03
retcode 10018 / Market closed
stale order filled 2025-03-06

GBPUSD:
cancel rejected 2025-02-03
retcode 10018 / Market closed
stale order filled 2025-02-04

USDCHF:
cancel rejected 2025-07-28
retcode 10018 / Market closed
stale order filled later 2025-07-28
```

Conclusion:

```text
recoverable pending-cancel retry is a cross-symbol lifecycle defect
```

### Pending disappeared without fill or strategy-cancel proof — 5

```text
EURCAD order 42   — 2025-04-07
GBPJPY order 144  — 2025-07-29
GBPUSD order 130  — 2025-08-14
GBPJPY order 224  — 2025-11-11
GBPUSD order 213  — 2025-12-22
```

Conclusion:

```text
this is a second execution defect class
root cause not yet proven
```

Contaminated symbol-years:

```text
EURCAD
EURGBP
GBPJPY
GBPUSD
USDCHF
```

Do not use their year-level profitability as final strategy evidence until re-run after the lifecycle fix.

## 8. Raw 18-symbol closed result — diagnostic only

```text
1,463 trades
246 TP / 1,217 SL
win rate = 16.8148%
Total = -418.221912R
Mean = -0.285866R
R PF ≈ 0.6686
```

Continuation:

```text
1,310 trades
219 wins
-390.519384R
mean -0.298106R
PF ≈ 0.6542
```

This is diagnostic because five symbols are execution-contaminated.

## 9. Divergence-free 13-symbol panel

Symbols:

```text
BTCUSD CADCHF CADJPY CHFJPY EURCHF EURJPY EURUSD
GBPCAD GBPCHF GOLD SILVER USDCAD USDJPY
```

All scopes:

```text
1,023 trades
187 wins
18.2796%
-193.184127R
mean -0.188841R
PF ≈ 0.7768
```

Continuation:

```text
901 trades
165 wins
18.3130%
-179.573032R
mean -0.199304R
PF ≈ 0.7637
```

Reversal:

```text
122 trades
22 wins
18.0328%
-13.611095R
mean -0.111566R
PF ≈ 0.8714
```

## 10. Strategy-planned barrier rescore

For the divergence-free continuation trades:

```text
TP deal -> +planned_R
SL deal -> -1R
```

This intentionally removes execution-price overshoot and money-layer effects.

Result:

```text
901 trades
165 TP
planned-barrier total = -166.492129R
mean = -0.184786R
```

Conclusion:

> Execution realism is not the main cause of the negative expectancy.  
> The planned Entry/SL/TP decisions are already negative as a set.

## 11. Stylized barrier-null diagnostic

Diagnostic only:

```text
P(TP first) = 1 / (1 + planned_R)
```

901 divergence-free continuation trades:

```text
expected wins = 205.7306
actual wins = 165

expected TP rate = 22.8336%
actual TP rate = 18.3130%
```

Independence-only Poisson-binomial:

```text
P(X <= 165) ≈ 0.0003157
```

Do not use this as final inference because trades are correlated and markets are not zero-drift Brownian barriers.

Use it as evidence that the baseline fails a first weak null benchmark.

## 12. Direction split

LONG:

```text
460 trades / 101 wins
actual WR 21.9565%
null WR 23.0821%
planned-barrier -4.181063R
canonical -13.361419R
```

SHORT:

```text
441 trades / 64 wins
actual WR 14.5125%
null WR 22.5744%
planned-barrier -162.311067R
canonical -166.211613R
```

SHORT independence-only diagnostic:

```text
expected wins = 99.5530
actual = 64
P(X <= 64) ≈ 0.00000603
```

Classification:

```text
LONG 2025 base edge = NOT DEMONSTRATED
SHORT 2025 base edge = STRONG NEGATIVE-EDGE WARNING
```

No permanent direction veto is authorized.

## 13. H1-state split

| H1 state | Trades | Wins | Actual WR | Null WR | Planned-barrier R | Canonical R |
|---|---:|---:|---:|---:|---:|---:|
| BULLISH | 355 | 80 | 22.54% | 23.65% | -1.4545R | -8.6640R |
| BEARISH | 329 | 46 | 13.98% | 22.78% | -139.8579R | -141.9049R |
| TRANSITION | 217 | 39 | 17.97% | 21.58% | -25.1797R | -29.0041R |

The mature H1 bearish continuation path is the dominant negative cluster.

## 14. Planned-R split

| Planned R | Trades | Wins | Actual WR | Null WR | Planned-barrier R | Canonical R |
|---|---:|---:|---:|---:|---:|---:|
| 1–2R | 217 | 68 | 31.34% | 40.89% | -47.9764R | -52.5583R |
| 2–4R | 251 | 53 | 21.12% | 26.16% | -44.6526R | -47.3145R |
| 4–8R | 247 | 31 | 12.55% | 15.12% | -41.7568R | -43.8615R |
| 8–16R | 137 | 13 | 9.49% | 8.68% | +16.8937R | +15.7447R |
| 16R+ | 49 | 0 | 0.00% | 4.30% | -49.0000R | -51.5835R |

Do not turn the 16R+ observation into a new threshold without independent confirmation.

## 15. Per-symbol divergence-free continuation

| Symbol | Trades | Wins | WR | Null WR | Canonical R |
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

Positive = 3/13. Negative = 10/13.

## 16. Trigger-chain timing

Among the 901 divergence-free continuation trades:

```text
PLAN -> Root contact:
median 10.73h / p90 88.97h / max 683.50h

Root contact -> Sweep:
median 2.33h / p90 11.65h / max 81.45h

Sweep -> CHoCH:
median 2.03h / p90 13.07h / max 100.02h

FVG selection -> Fill:
median 0.85h / p90 15.63h / max 142.66h
```

This is evidence for a causal-ownership audit, not for arbitrary time thresholds.

## 17. Fixed-risk sizing check

Across the 18-symbol run:

```text
target risk = $100
planned risk intentionally normalized downward to volume step
no intended over-target planned-risk behavior observed in the closed-trade reconstruction
```

Cross-symbol strategy comparison should remain primarily R-based because coarse volume steps can under-use the $100 target materially on some symbols.

## 18. Current evidence classification

The project can now support the following statements:

```text
Frozen Regime V1 historical evidence = preserved.
2022 first OOS PASS = preserved.

2025 18-symbol NO-GATE baseline =
broad negative result.

Divergence-free continuation =
negative across 10/13 symbols.

Execution defects =
real and must be fixed,
but do not explain the main negative expectancy.

Base continuation predictive edge =
NOT DEMONSTRATED.

Bearish continuation =
strongest negative-edge warning.
```

The next strategy research step is not another filter search.

It is `EDGE_AUDIT_V1`.
