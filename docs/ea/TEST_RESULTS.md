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

---

## 2026-08-20 — D-142A parity PASS and first six-symbol front-end audit

### GOLD January parity smoke

D-142A `1.92R1L4` was run with identical GOLD January 2025 conditions, first with `InpEnableEdgeAudit=false`, then `true`.

The two main strategy ledgers were byte-identical:

```text
SHA-256 = db4e312e6699dc162a873f83289ec1221bb030b50a2945a320c830e6f793ea60
```

Stage counts, scenario identities/timestamps, forward-label completeness, right-censor accounting, and basic MFE/MAE causal consistency also passed. D-142A shadow instrumentation is therefore accepted as non-authoritative measurement infrastructure.

### First 2025 contrast panel

```text
BTCUSD / CADJPY / GBPCAD / GOLD / SILVER / USDJPY
```

Audit population:

```text
MAP = 35,284
PLAN = 7,589
ROOT_CONTACT = 4,809
SWEEP = 3,753
CHOCH = 1,746
FVG = 1,550
ACTUAL_FILL = 519
execution divergence = 0 in these six runs
```

Front-end continuation timing:

```text
owner start -> Root causal structure median: LONG 39.5h / SHORT 48.5h
PLAN -> Root contact median:              LONG  6.5h / SHORT  9.0h
owner age at Root contact median:         LONG 59h   / SHORT 73h
```

Every paired PLAN/contact retained the same owner ID, active-map TF, H1 state, M30 state, and scenario direction. This rules out a simple map-flip-with-stale-plan explanation.

For H1-active hourly MAP states, future raw 24h return after LONG states was lower than after SHORT states on all six symbols. 42/60 comparable symbol-month blocks showed the same inverse ordering. Because hourly states are serially dependent, this is a research warning rather than a standalone significance claim.

At Root contact, continuation 24h direction correctness was approximately `54.5%` LONG / `49.5%` SHORT versus `53.3%` LONG / `38.7%` SHORT at PLAN, and mean signed 24h response from contact was positive for both directions. This supports a new distinction between local Root reaction and sustained higher-timeframe continuation.

Decision: move the next instrumentation step upstream to D-143 front-end causal audit before implementing fill-barrier or CHoCH strategy variants.

---

## 2026-08-21 — D-144 GOLD exact-tick result and D-145 transition

The first D-144 run was restricted to GOLD 2025 because the multi-stage exact-tick barrier population increased tester time by roughly 9x while file size increased only about 15%, indicating per-tick tracker fan-out as the dominant cost.

Continuation actual fills:

```text
51 fills
structural TP = 14 wins / 27.45%
+1R before SL = 30 / 58.82%
+1.5R before SL = 25 / 49.02%
+2R before SL = 20 / 39.22%

+1R direction split:
LONG 21 / 35 = 60.00%
SHORT 9 / 16 = 56.25%
```

Among 37 continuation trades that eventually lost under the existing structural objective, 16 first reached +1R, 11 reached +1.5R, and 7 reached +2R. This demonstrates that the low structural-TP win rate is not equivalent to a uniformly wrong filled direction.

The result is one symbol-year and does not establish a fixed TP. D-145 therefore measures the causal difference between `+1R then exhaust before 2R` and `+1R then reach 2R+`, while removing the D-144 multi-stage barrier fan-out.

---

## 2026-08-21 — D-145 runner generalization panel

Research identity:

```text
build = 1.92R1L7
phase = RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT
strategy authority = NONE
```

Development/generalization panel:

```text
GOLD 2023
GOLD 2024
GOLD 2025
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

Continuation exact-tick outcomes:

| Market-year | Fill | +1R | +2R | +3R | P(+2R | +1R) |
|---|---:|---:|---:|---:|---:|
| GOLD 2023 | 64 | 35 | 27 | 22 | 77.1% |
| GOLD 2024 | 52 | 24 | 17 | 10 | 70.8% |
| GOLD 2025 | 51 | 30 | 20 | 16 | 66.7% |
| BTCUSD 2025 | 114 | 54 | 40 | 34 | 75.5%* |
| SILVER 2025 | 45 | 18 | 7 | 6 | 38.9% |
| CADJPY 2025 | 111 | 30 | 18 | 10 | 60.0% |

`*` One BTCUSD +1R trade is right-censored for the +2R outcome and is excluded from the conditional denominator.

Aggregate:

```text
fills = 437
+1R successes = 191
resolved +1R successes for +2R comparison = 190
+2R successes = 129
P(+2R | +1R) = 67.9%
```

2025 cross-market Entry-survival warning:

```text
GOLD    30/51  = 58.8%
BTCUSD  54/114 = 47.4%
SILVER  18/45  = 40.0%
CADJPY  30/111 = 27.0%
total   132/321 = 41.1%
```

Therefore D-145 does not solve the final >=50% Entry/win-rate requirement.

Primary runner finding:

At first +1R, median M30 protected-to-current-external range progress was lower for eventual +2R runners in all six market-year aggregate cells:

```text
GOLD23   1.061 -> 0.691
GOLD24   0.867 -> 0.644
GOLD25   0.918 -> 0.796
BTC25    0.955 -> 0.788
SILVER25 0.946 -> 0.724
CADJPY25 0.770 -> 0.565
```

Direction-level consistency:

```text
11 / 11 comparable market-year x direction cells
```

Coverage:

```text
190 resolved +1R conditional trades
147 with valid comparable scenario-direction M30 range
```

Supporting evidence:

Risk-normalized remaining distance to current M30 external was larger for runners in all six aggregate cells, but this measure contains the Fill-to-SL risk denominator and is secondary to range progress.

Negative/generalization findings:

```text
M30 net advance = unstable
FVG timing/displacement = unstable
+1R speed = unstable
simple progression/PB = weak
M1 continuation = inconsistent
standalone M30 expansion = insufficient cross-market consistency
clean-path / low-MAE rule = contradicted by runners often taking more pre-1R MAE
```

Most important interpretation boundary:

```text
M30 maturity @ +1R may describe +1R -> +2R continuation.
It is NOT a proven Fill -> +1R Entry filter.
```

Classification:

```text
D-145 cross-market runner relationship = PROMISING / GENERALIZED DESCRIPTIVELY
causal exit authority = NOT ESTABLISHED
Entry-survival solution = NOT ESTABLISHED
fixed-R TP promotion = NOT AUTHORIZED
```

Next measurement: D-146 post-+1R M30 continuation-state audit.

## D-146 GOLD 2025 continuation-state audit — preliminary validated ledger

Source: user-provided GOLD 2025 unified event ledger, analyzed 2026-08-21.

```text
continuation fills = 51
+1R = 30 / 51 = 58.82%
+2R = 20 / 51 = 39.22%
+2R | +1R = 20 / 30 = 66.67%
D146 T0 = 30
D146 terminals = 30
D146 censored = 0
execution divergence = 0
```

D-145 relation reproduced: valid-range +2R runners had lower +1R M30 progress (median 0.796 vs 0.918) and more remaining external room (0.954R vs 0.232R).

Ten trades reached +1R and then failed before +2R; their post-+1R peak total-R levels were approximately 1.083, 1.219, 1.246, 1.364, 1.463, 1.518, 1.560, 1.737, 1.746, 1.893. This confirms material post-fill giveback and motivates D-147 exit-architecture research, but does not authorize a fixed TP.

See `D146_CONTINUATION_STATE_AUDIT.md` for instrumentation caveats. D-147 performance results are pending local compile/parity and MT5 Strategy Tester runs.

## D-147 GOLD 2025 exit-architecture comparison

Analyzed 2026-08-21 from user-provided Strategy Tester ledgers.

```text
ORIGINAL  : 58 trades, WR 24.14%, expectancy +0.095R, total +5.532R, max DD 23.00R
TRAILING  : 58 trades, WR 29.31%, expectancy -0.008R, total -0.478R, max DD 9.35R
PARTIAL   : 58 trades, WR 43.10%, expectancy +0.118R, total +6.864R, max DD 9.00R
```

Continuation-only:

```text
ORIGINAL  51 trades / 14 winners / WR 27.45% / expectancy +0.254R
TRAILING  51 trades / 16 winners / WR 31.37% / expectancy +0.015R
PARTIAL   51 trades / 24 winners / WR 47.06% / expectancy +0.187R
```

The `<1R` failure population was exactly 21 continuation trades and did not change across exit modes. This is now the D-148 Entry-survival taxonomy population.

PARTIAL improved every one of the 16 ORIGINAL continuation trades that first reached +1R but later realized a loss; 10/16 became positive net trades. However large winners were materially haircut, so continuation-state-aware partial management is recorded only as a future research idea.

D147 compact action rows were suppressed; action-level execution QA is not claimed from these ledgers.

## D-147 / D-148 solution-research handoff evidence — 2026-08-21

D-147 GOLD 2025 continuation control vs mechanical partial:

```text
ORIGINAL: 51 trades / WR 27.45% / expectancy +0.254R / avg winner +3.827R / max DD 19.53R
PARTIAL:  51 trades / WR 47.06% / expectancy +0.187R / avg winner +1.402R / max DD 7.66R
```

Mechanical partial materially improved realized win shape and drawdown but cut large winners. This motivates D149 SP rather than promotion of the repeated 50%-remaining staircase.

D-148 clean GOLD 2023-2025 continuation taxonomy:

```text
167 fills
89 immediate +1R = 53.3%
78 normalized-SL first = 46.7%
27 / 78 SL-first later recovered original +1R before H1/M30 map-support loss = 34.6%
51 / 78 lost map support before recovery = 65.4%
18 / 27 recovery cases had original Root invalidated before recovery
9 / 27 retained original Root through recovery
```

Interpretation: do not try to turn every SL into a winner. Separate true structural failure, local-source failure/re-entry opportunity, and the smaller same-Root timing/SL-sensitivity class. D149 EM addresses repeated correlated episode exposure; D149 SP addresses +1R giveback.

## 2026-08-21 — D-149 GOLD 2025 SP / EM V1 result and V2 handoff

User-provided ledgers:

```text
GOLD_SP.csv
GOLD_EM.csv
GOLD_SPEM.csv
```

All three D149 ledgers passed the supplied D149 integrity analyzer and reported:

```text
execution divergence = 0
cancel rejected = 0
unresolved = 0
```

Continuation performance:

| Variant | Trades | Wins | WR | Avg winner | Avg loser | Expectancy | Total | Max DD | Longest nonpositive streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ORIGINAL control | 51 | 14 | 27.45% | +3.827R | -1.099R | +0.254R | +12.934R | 19.53R | 11 |
| SP V1 | 51 | 22 | 43.14% | +1.880R | -0.872R | +0.315R | +16.071R | 11.05R | 6 |
| EM V1 | 29 | 8 | 27.59% | +4.842R | -1.067R | +0.563R | +16.339R | 15.13R | 14 |
| SP+EM V1 | 30 | 13 | 43.33% | +2.256R | -0.775R | +0.538R | +16.149R | 8.29R | 7 |

The EM expectancy numbers are not sufficient for promotion because EM V1 removed a large share of trades and worsened its isolated longest streak. It must be judged by membership and streak behavior, not only expectancy per remaining trade.

### SP V1

Continuation +1R state counts:

```text
STRONG_RUNNER = 11
DEFAULT = 19
```

Observed +2R / BE trigger:

```text
STRONG_RUNNER 9/11 = 81.8%
DEFAULT       4/19 = 21.1%
```

This supports the D145/D146 structural strong-state concept for runner management on GOLD 2025.

SP V1 still exposed two economic defects:

1. Five continuation DEFAULT trades that had reached +1R still finished slightly negative after the 50% partial / remainder outcome and costs/slippage.
2. One STRONG trade reached +2R and moved the remainder to Fill BE but still closed aggregate-negative (`exit profit +22.48`, `swap -32.05`, net `-9.57`, approximately `-0.105R`). Static price BE is therefore not sufficient for the stated no-negative-lock intent under carry.

SP V2 addresses these defects without changing the strong-state threshold.

### EM V1

```text
same-episode concurrent blocks = 20
first-loss/no-refresh blocks = 6
```

Mapping the blocked scenario IDs back to the clean ORIGINAL population:

```text
concurrency blocks -> 17 baseline fills / 5 winners / 12 losers / about -0.259R total
no-refresh blocks  ->  5 baseline fills / 1 winner  /  4 losers / about -3.146R total
```

The concurrency rule therefore removed many opportunities for little net loss avoidance and is rejected for V2. The post-failure fresh-delivery gate remains promising.

The EM-only longest streak was 14, demonstrating that the dominant long loss cluster can cross owner episodes. EM V2 therefore moves the primary risk unit from `same owner episode` to `global consecutive Entry-survival failures` while retaining a local fresh-delivery gate.

### D148 / loss-cluster context retained

Clean GOLD 2023-2025 D148 continuation:

```text
167 fills
89 immediate +1R = 53.3%
78 SL-first = 46.7%
27/78 recovered original +1R before H1/M30 support loss = 34.6%
51/78 lost map support first = 65.4%
18/27 recovery cases invalidated the original Root first
9/27 kept the original Root through recovery
```

Long realized-loss streaks are not a single Entry-failure population: earlier sequence analysis found both repeated structural exposure and +1R giveback inside the streaks. This is why SP and EM remain separate controls.

Classification:

```text
SP V1 = PROMISING / KEEP AS CONTROL
EM V1 = DEMOTED / KEEP AS NEGATIVE CONTROL
SP V2 = IMPLEMENTED / VALIDATION PENDING
EM V2 = IMPLEMENTED / VALIDATION PENDING
baseline authority = UNCHANGED
```

## 2026-08-22 — D-149 V2 cross-market handoff into continuation-only V2

GOLD 2025 SP+EM V2 ledger SHA-256: `7969c8de223893bc6a5aec23f0077395aea3c3c69e71997111608c9676bbc4d9`. Continuation: 41 closed / 22 wins / WR 53.66% / avg winner +1.515R / expectancy +0.331R / total +13.555R / max DD 6.05R / longest nonpositive streak 3. The same run's reversal lane was 7/7 losses, about -7.40R.

BTCUSD 2025 SP+EM V2 ledger SHA-256: `9ffb7c5aa1ac2a238f1fbebf08ed357d7ceb024dd11564520dbd442e8bfada7e`. Continuation closed population: 63 / 25 wins / WR 39.68% / avg winner +1.137R / expectancy -0.163R / total -10.262R / max DD 11.25R / streak 7. Reversal was 19/19 losses, about -19.68R. One continuation fill remained unresolved at tester end, so BTC is diagnostic rather than final profitability evidence.

Common structural conclusion: SP can convert +1R survivors to winners, but Entry survival can still dominate results; +2R -> near-cost-BE often surrenders too much open profit; M30 room-rich state remains promising for runner discrimination. EM V2 helped GOLD shape but has a BTC generalization warning. D-150 therefore separates a continuation-only V2 line and removes reversal contamination from future solution research.

## 2026-08-22 — V2 continuation-only bootstrap evidence and D-151 handoff

Latest GitHub fork identity before D-151 package:

```text
HEAD = ad39986173568fe3b96d7dc9cadf793cd2f77aef
V2 = 2.00R0L0 / V2_CONTINUATION_ONLY_BOOTSTRAP
```

### GOLD 2025 V2 SP+EM clean second run

The user-provided `GOLD(7).csv` contained two appended tester runs. The second `$100 fixed-risk` run was isolated for analysis.

```text
42 closed continuation trades
22 winners
WR = 52.38%
avg winner = +1.515R
avg loser = -1.039R
expectancy = +0.299R/trade
total = +12.550R
max closed-trade DD = 6.05R
longest nonpositive streak = 3
reversal PLAN/fill/close = 0/0/0
execution divergence = 0
cancel rejected = 0
unresolved = 0
```

At first +1R:

```text
STRONG:  6/8 reached +2R = 75.0%
DEFAULT: 3/16 reached +2R = 18.75%
```

One January GOLD stop gap realized approximately `-2.47R` despite nominal 1R geometry. This is retained as real execution/tail-risk evidence and is not normalized away.

### BTCUSD 2025 inherited D149 SP+EM diagnostic

Continuation closed cohort:

```text
63 closed
25 winners
WR = 39.68%
avg winner = +1.137R
avg loser = -1.018R
expectancy = -0.163R/trade
total = -10.262R
max closed-trade DD = 11.25R
longest nonpositive streak = 7
```

The run was right-censored by one open continuation fill and predates the continuation-only V2 fork, so it remains diagnostic rather than final V2 evidence.

### Interpretation

GOLD and BTC support the same decomposition:

```text
1. pre-+1R Entry survival is a separate bottleneck;
2. M30 room/maturity at +1R remains a promising runner discriminator;
3. +2R -> near-cost-BE leaves too much realized-profit giveback;
4. EM has not yet generalized cleanly enough for baseline promotion.
```

D-151 therefore adds shadow causal instrumentation before D-152 strategy variants are designed.

## 2026-08-22 — D-151 GOLD/BTC SP-only evidence for D-152

User-provided clean D151 SP-only ledgers:

```text
GOLD(10).csv
53 fills / 53 closes
WR 52.83%
avg winner +1.373R
expectancy +0.228R
total +12.063R
+1R 30/53 = 56.6%
STRONG +2R 9/11 = 81.8%
DEFAULT +2R 3/19 = 15.8%

BTCUSD(6).csv
127 fills / 126 closes / 1 actual right-censor
closed WR 44.44%
avg winner +1.103R
expectancy -0.066R
total -8.337R
+1R 59/127 = 46.5%
STRONG +2R 15/18 = 83.3%
DEFAULT +2R 17/41 = 41.5%
```

Closed +1R cohort positive conversion: GOLD 93.3%, BTC 94.8%. Final >=+1R within the +1R cohort: GOLD 43.3%, BTC 36.2%.

D151 post-+2R shadow: a hypothetical fixed +1R floor at +2R would have allowed only 2/6 eventual GOLD +5R paths and 7/15 BTC +5R paths to survive. Four BTC shadow structural-TP winners actually closed below +1R under current cost-BE before later shadow recovery; GOLD had zero such cases. This cross-market divergence motivates controlled profit-bank variants rather than a universal tighter SL.

Counterfactual substitutions are diagnostic only, not realized strategy evidence. Replacing causally-known range-available DEFAULT trades by their first +1R execution price improved aggregate R by about +0.94R on GOLD and +2.71R on BTC in these ledgers, but the benefit was direction-concentrated, so it is tested as a research variant only.

## D-152 SP V3 automated matrix — 2026-08-22

Batch artifact:

```text
Trading_D152_SP_V3_20260822_044945.zip
SHA256 e28cc77bb7c6419b958fdd77873a1e81fdf546ab9f52c7c776532cdf0e607d37
```

Test universe:

```text
GOLD / BTCUSD
2025.01.01 -> 2025.12.31
M1
Every tick based on real ticks
EM OFF
D151 audit ON
6 SP modes x 2 symbols = 12 runs
```

Integrity:

```text
all terminal return codes = 0
EA_START / EA_STOP present
execution divergence = 0
pending cancel rejection = 0
```

Provisional leader: `V3E BANK_2R_LOCK_ONE`.

GOLD V3E:

```text
53 closed
WR 52.83%
final >= +1R 33.96%
avg winner +1.328R
expectancy +0.203R
total +10.783R
max closed-R DD 6.807R
```

BTCUSD V3E:

```text
127 fills / 125 closed / 2 right-censored
WR 44.00% on closed
final >= +1R 32.80%
avg winner +1.225R
expectancy -0.022R
total -2.750R
max closed-R DD 14.233R
```

No censored trade is imputed.

Detailed matrix and interpretation:
`docs/ea/v2/D152_SP_V3_RESULTS.md`
