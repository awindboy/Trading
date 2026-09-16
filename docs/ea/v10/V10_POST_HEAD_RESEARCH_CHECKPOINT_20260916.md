# V10 Post-HEAD Research Checkpoint — Stagewise Participation, Extreme Danger, and Execution Gate

Date: `2026-09-16`  
Status: `POST-HEAD SESSION CHECKPOINT / CONSUMED-DATA SHADOW RESEARCH / NOT PRODUCTION AUTHORITY`  
Market: `GOLD# ONLY`  
Base GitHub main HEAD: `8f20e02065ab7a530d685d516a9efb928a592ead`  
Base commit message: `update V10`  
Production authority: `NONE`  
EA authority: `RESEARCH / DEMO ONLY`

## 0. Purpose

This checkpoint preserves the V10 research performed after GitHub HEAD `8f20e020...` and before the first bounded-m3 actual-tick diagnostic was analyzed.

The repository already preserved:

- HA-primary participation architecture;
- FAST / STD / SLOW H4 HA roles;
- H1 structural invalidation;
- M1 first-touch screening;
- early-third / runway answer sheets;
- bounded `m=3`, prior-history quartile `0/0/1/3` diagnostic;
- the original Oracle-participation next contract.

The post-HEAD session materially changed the research interpretation. V10 is no longer best described as one scalar Oracle-probability model. The strongest working architecture became stage-aware:

```text
FAST PHA #1
    |
    +-- Opportunity Head
    |     P_RUNWAY / P_WIN / STD support
    |
    +-- Danger Head
          extreme early-run downside
          -> ABSTAIN only when evidence is extreme

FAST PHA #2
    |
    +-- Persistence Head
          M15 / M30 / H1 internal delivery
          -> CONFIRM or STOP-ADDING

k3+
    |
    +-- marginal Child / runway economics

first opposite FAST H4 HA
    |
    -> campaign EXIT comparator
```

No threshold, model coefficient, lot map, or stage policy in this checkpoint is promoted.

## 1. Non-negotiable discipline

Continue to follow current V10 guardrails and inherited V9 causal replay rules.

Do not:

- use final FAST run length as live state;
- use future Child PnL as a feature;
- resurrect a stopped Child;
- widen a structural SL;
- repair accidental future reveal with hindsight trades;
- invent minimum-R, cooldown, retry-count, no-chase, Child-cap, or forced direction-balance rules;
- promote a consumed-data percentile merely because it worked;
- confuse a high AUC with a deployable trading action.

A stopped Child stays dead.

## 2. Frozen research baseline used by the post-HEAD studies

FAST H4 transformed HA:

```text
HC = (O + H + L + 2*C) / 5

HO_t
= 0.25 * HO_(t-1)
+ 0.75 * HC_(t-1)
```

Semantic roles:

```text
FAST H4
-> participation / execution clock
-> run segmentation
-> first opposite FAST H4 HA = default exit comparator

STD H4
-> maturity / support / broader run-location state

SLOW H4
-> broad regime / maturity context

M15 / M30 / H1 HA
-> internal delivery / persistence / fragmentation context

H1 liquidity
-> structural invalidation / structural risk

Grammar
-> structural context
-> no longer V10 primary entry clock
```

Risk screening baseline:

```text
ERA_SCALE
= previous completed H4 Wilder ATR180

ERA_RISK
= abs(entry - structural H1 SL) / ERA_SCALE

screen:
ERA_RISK <= 4
```

## 3. Persisted comparator set

### ALL1

```text
eligible FAST opportunities     2,489
PnL                           +10,007.27
PF                               1.368386
DD                             ~2,034.28
structural R                   +253.72R
```

### True early-third answer sheet

```text
k = current completed same-color FAST H4 index
L = final same-color FAST H4 run length

ORACLE_EARLY = 1 iff 3*k <= L
```

```text
Oracle bars                      567
PnL                           +23,344.73
PF                              15.1566
DD                              148.81
structural R                   +733.18R
```

`L` is future-only.

### Current exact reproducible bounded m=3 diagnostic

```text
score
= P_RUNWAY(3x)
* P_WIN
* P_STD_SUPPORT

prior-history quartile map:
bottom 50% -> 0 units
50-75%     -> 1 unit
top 25%    -> 3 units
```

```text
selected entry events          1,159
total units                    2,313
PnL                           +14,827.57
PF                               1.553395
DD                             2,638.04
structural R                  +388.88R
max single order                  3 units
max concurrent                   12 units
Oracle recall                    80.42%
Oracle precision                 39.34%
```

The bounded m=3 ledger remains the exact reproducible benchmark because its selected-entry ledger is persisted.

## 4. Economic decomposition: the problem is destructive false positives

One-unit economics:

```text
TRUE ORACLE
N               567
PnL          +23,344.73
PF             15.1566
WR              74.43%
R             +733.18R

NON-ORACLE
N             1,922
PnL          -13,337.46
PF              0.4773
WR              23.47%
R             -479.46R
```

Therefore:

```text
ALL1 +10,007.27
=
Oracle +23,344.73
+
non-Oracle -13,337.46
```

The primary economic objective became:

> preserve large-trend participation while removing the most destructive false-positive exposure.

Oracle purity alone is not the target.

## 5. Final FAST run-length decomposition

One-unit non-Oracle economics depend strongly on how long the run eventually survives:

| Final FAST run length | N | PnL | PF | Structural R |
|---|---:|---:|---:|---:|
| `L=1-2` | 545 | **-10,011.57** | 0.0118 | -328.51R |
| `L=3-5` | 679 | -8,116.29 | 0.1309 | -294.85R |
| `L=6-8` | 370 | -833.80 | 0.758 | -40.61R |
| `L=9-11` | 204 | **+2,090.02** | 2.307 | +64.19R |
| `L>=12` | 124 | **+3,534.18** | 4.520 | +120.33R |

Future-aware skip of only `L<=2` would recover roughly `+10,011.57`, about 75% of the ALL1-to-Oracle dollar gap.

This is an answer-sheet diagnostic only, but it localized the damage: very short FAST runs are disproportionately destructive.

## 6. Bounded m=3 false-positive decomposition

Selected Oracle exposure:

```text
456 events
994 units
PnL +35,840.41
PF 12.177
R +1,026.90R
```

Selected non-Oracle exposure:

```text
703 events
1,319 units
PnL -21,012.84
PF 0.1091
R -638.02R
```

Missed Oracle bars:

```text
111 events
hypothetical 1x PnL +6,901.92
R +261.03R
```

The dominant issue is therefore selected false-positive regret, not only missed Oracle recall.

## 7. Internal lower-timeframe organization

Only causally completed H1 / M30 / M15 HA information inside the current FAST H4 run was used.

Useful semantic families:

```text
aligned fraction
transition rate
same/opposite run length
max same/opposite streak
same-vs-opposite length advantage
current signed streak
directional body flow
run dominance
opposing-wick share
```

Broad feature soup was inferior to compact semantic families.

## 8. k1 STOP vs SURVIVE morphology

At FAST `k=1`, surviving runs showed more coherent lower-timeframe delivery than one-bar failures.

Representative medians:

```text
H1 aligned fraction:
STOP 0.75
SURVIVE 1.00

M30 aligned fraction:
STOP 0.625
SURVIVE 0.750

M15 aligned fraction:
STOP 0.562
SURVIVE 0.667
```

Directional body-flow medians also increased from STOP to SURVIVE across H1/M30/M15.

Interpretation:

> a FAST H4 candle can remain positive while its internal organization already shows fragility.

## 9. k2 STOP vs third-bar survival

At `k=2`, current lower-timeframe signed streak separated termination from continued FAST delivery more strongly:

```text
H1 signed streak median:
STOP    -1
SURVIVE +4

M30:
STOP    -1
SURVIVE +1.5

M15:
STOP    -1
SURVIVE +1
```

This supported a different semantic role for k2: persistence confirmation rather than the same loss model used at k1.

## 10. One-step survival was easier than full-run prediction

The framing changed from:

```text
at k1:
predict final L
```

to:

```text
at k1: will k2 exist?
at k2: will k3 exist?
at k3: will k4 exist?
...
```

Representative prior-only discrimination:

```text
k1 -> k2
compact LTF regime        mean AUC ~0.729
FLOW + PERSISTENCE        mean AUC ~0.733

k2 -> k3
core V10 state            mean AUC ~0.795
LTF FLOW + PERSISTENCE    mean AUC ~0.776

later stages:
k3 core                   ~0.703
k4 LTF compact            ~0.734
k5 core                   ~0.834
```

One-step hazard / survival is more tractable than solving an entire future run from k1.

## 11. Feature-family result

For k1 survival:

```text
FLOW + PERSISTENCE    ~0.733 AUC
FLOW_ONLY             ~0.711
PERSISTENCE_ONLY      ~0.684
LENGTH_ONLY           ~0.680
CHOP_ONLY             ~0.579
```

Strong individual coordinates included:

```text
M15 directional body sum    ~0.711
M15 body mean               ~0.708
M30 directional body sum    ~0.704
M30 body mean               ~0.700
M30 aligned fraction        ~0.667
M15 aligned fraction        ~0.661
```

Body delivery carried more information than color-transition count alone.

## 12. V9 morphology reused in the V10 question

V9 morphology concepts were retested under the V10 participation problem:

```text
body / ATR
body / total range
wick asymmetry
no-opposing-wick
body relative to recent history
opposite streak
prior primary streak
```

The shortest completed 4-hour internal window was usually strongest. Longer 8h / 16h / 24h morphology frequently diluted the signal.

Opposing-wick share was especially useful around k2:

```text
M15 4h opposing-wick share
k1 survival ~0.648 AUC
k2 survival ~0.754

M30 4h opposing-wick share
k1 ~0.640
k2 ~0.730
```

A weakening LTF state does not automatically authorize early exit of already-profitable Children.

## 13. Universal k1 down-sizing failed

A simple rule:

```text
k1 -> always smaller scout
```

reduced total economics.

ALL1 examples:

| k1 multiplier | PnL | PF | diagnostic DD | R |
|---:|---:|---:|---:|---:|
| 1.00 | +10,007 | 1.368 | 2,073 | +253.7R |
| 0.75 | +9,271 | 1.371 | 2,012 | +237.1R |
| 0.50 | +8,535 | 1.375 | 1,950 | +220.5R |
| 0.25 | +7,799 | 1.379 | 1,888 | +203.9R |
| 0 | +7,064 | 1.384 | 1,826 | +187.2R |

Bounded m=3 also deteriorated sharply under universal k1 reduction.

Conclusion:

> the first PHA is not generically bad; the problem is a small extreme-danger subset.

## 14. Dedicated NHA_SHOCK answer sheet

A downside-specific answer sheet was defined:

```text
NHA_SHOCK
=
current PHA is the final PHA of this FAST run
AND
Child final result <= -0.5R
```

Future outcome is label-only.

A dedicated prior-only head produced roughly `0.72` AUC. The useful behavior appeared in the extreme tail rather than as a smooth global ranking.

## 15. Extreme danger tail

Time-ordered diagnostics:

- 2025 H2 trained on 2025 H1;
- 2026 trained on prior 2025.

Top ~5% k1 NHA-shock risk among bounded entries:

```text
18 events
28 units
0 winners
18 losers
18 / 18 severe
17 / 18 H1 structural SL
14 with L=1
2 with L=2
2 with L>=3
weighted PnL -240.67
weighted R -27.33R
```

Top ~10%:

```text
42 events
68 units
36 losers
6 winners
29 structural SL
30 severe loss
L=1 24
L=2 5
L>=3 13
weighted PnL -478.83
weighted R -46.56R
```

This supports a high-confidence veto concept, not a broad risk filter.

## 16. Broad danger filtering failed

2026 diagnostics:

| Removed danger tail | PnL change |
|---:|---:|
| top 25% | **-823** |
| top 20% | **-475** |
| top 15% | **-648** |
| top 12.5% | **-518** |
| top 10% | **+268** |
| top 7.5% | +178 |
| top 5% | +166 |
| top 2.5% | +59 |

The risk score was not monotonically economic over the full range. Some 87.5-90 percentile observations were highly profitable while the most extreme tail was consistently destructive.

Therefore:

> danger evidence is currently useful as an extreme abstention override, not a continuous broad penalty.

The percentile is consumed evidence, not authority.

## 17. Opportunity and danger are distinct heads

Danger events existed even inside high opportunity bins.

Representative diagnostics:

```text
BIN 2 + danger:
29 events
PnL/unit ~-8.38
severe ~72.4%

BIN 2 without danger:
PnL/unit ~+6.79

BIN 3 + danger:
13 events
PnL/unit ~-6.04
severe ~69.2%

BIN 3 without danger:
PnL/unit ~+7.00
```

Conclusion:

```text
Opportunity != Safety
```

A high `P_RUNWAY * P_WIN * P_STD_SUPPORT` score does not make a separate downside veto redundant.

## 18. Stop probability is not economic danger

Observed research heads:

```text
P_STOP              AUC ~0.81
P_SEVERE_LOSS       AUC ~0.74
P_NHA_SHOCK         AUC ~0.72
broad harmful-FP    AUC ~0.59
```

Structural-stop probability can be predicted relatively well, but avoiding all likely stops is not equivalent to improving economics.

`ERA_RISK` showed non-monotonic economic behavior; an ERA_RISK minimum is not justified.

## 19. Lower-tail R modeling

A 10th-percentile Child-R quantile model was reasonably calibrated in 2026:

```text
actual R below predicted Q10
~9-11%
```

Severe-loss discrimination was about `0.74-0.75` AUC.

Again:

```text
broad bottom 10%
-> removes too many winners

extreme bottom ~5%
-> more useful veto behavior
```

One 2026 extreme-tail diagnostic improved PnL by roughly `+180`.

## 20. Multi-head consensus did not beat the simpler danger tail

Compared families:

```text
A. NHA_SHOCK extreme tail
B. P_STOP extreme tail
C. predicted-R lower-tail extreme tail
```

They overlapped heavily.

Representative 2026 selected k1:

```text
0 risk flags 259
1 flag         8
3 flags       13
```

Two-of-three consensus improved about `+180`, while the simpler NHA-shock extreme-tail diagnostic improved about `+268`.

Complexity did not automatically add value.

## 21. Catch-up after k1 abstention failed

Tested idea:

```text
k1 dangerous
-> abstain

k2 survives
-> restore missed exposure
```

Confirmation variants used score / BIN / P_WIN / P_RUNWAY improvement.

The original k1 danger-veto improvement of roughly `+268` often collapsed to only `+20` to `+45` after catch-up.

Interpretation:

> an avoided bad exposure does not need to be mechanically recovered later.

## 22. k1 and k2 should have different jobs

Current evidence:

```text
k1
-> LOSS AVOIDANCE / RUN ADMISSION

k2
-> CONFIRMATION / PERSISTENCE

k3+
-> RUNWAY / CONTINUATION ECONOMICS
```

A k2-specific severe-loss veto was weaker economically, whereas probability of a third same-color H4 was much more predictable.

## 23. Best recorded post-HEAD bounded diagnostic

Session-recorded consumed-data result:

```text
bounded m3
+ extreme NHA-shock veto

PnL         +15,013.69
PF            1.57811
DD          ~2,703.62
structural R +428.23R
```

This result must be preserved with an explicit reproducibility caveat:

- the exact fitted coefficient vector was not persisted;
- the exact veto-row ledger was not persisted;
- therefore it is not the current executable benchmark;
- regenerate it before quoting it as a formal reproduced result or implementing it in an EA.

The exact executable benchmark remains the persisted bounded m3 ledger.

## 24. Right-tail concentration remains material

Run-level concentration:

```text
ALL1
750 runs
run WR ~22.1%
median run PnL -17.08
top 1 run ~28% of total PnL
top 5 ~84%

bounded m3
run WR ~27.2%
median -11.96
top 1 ~17.9%
top 5 ~58.7%

bounded m3 + shock veto
top 1 ~17.7%
top 5 ~58.0%
```

Every later V10 candidate must report right-tail dependence.

### 24A. Run continuation probability is not the same as Child profitability

At `k=2`, score change from the first to second FAST PHA could help predict whether the run continued:

```text
P(final L>=3) AUC ~0.721
```

but had almost no direct power for the new k2 Child's own economics:

```text
k2 positive-R AUC   ~0.506
k2 severe-avoid AUC ~0.502
```

Therefore two questions must remain separate:

```text
Will the FAST run continue?
!=
Is one more Child economically attractive at this price / structural risk?
```

This is a central reason V10 needs a distinct Persistence head and marginal Child-value head instead of one scalar.

### 24B. Continuous downside allocation was informative but not a clean replacement

Continuous safety factors based on `P_STOP` and `P_SHOCK` were also tested.

ALL1 with both-safety modulation:

```text
units ~2,550.7
PnL +12,095.30
PF 1.412
DD ~1,906
R +279.0R
max concurrent ~22
```

A stage `SAFE / CONFIRM` structure plus downside safety produced, before normalization:

```text
units ~2,693
PnL +14,690.61
PF 1.465
DD ~1,925
R +310.7R
max order ~3.60
max concurrent ~23.33
```

After equal-exposure normalization and a diagnostic order cap of 3:

```text
units ~2,486.7
PnL +13,593.29
PF 1.46498
DD ~1,794.21
R +287.01R
max order 3
max concurrent ~21.44
```

Year split remained positive, but direction quality was asymmetric:

```text
2025: PnL +5,033 / PF 1.388 / DD ~1,587
2026: PnL +8,560 / PF 1.526 / DD ~2,089

UP:   PnL +11,826 / PF 1.778
DOWN: PnL +1,767  / PF 1.126 / structural R about -18R
```

Bootstrap versus ALL1 was promising but not decisive:

```text
pooled delta +3,586
95% CI roughly [-594, +8,359]
P(delta>0) ~0.956
```

Interpretation: continuous safety allocation contains useful information, but it raises exposure and direction-concentration concerns. It is not stronger evidence than the simpler extreme-danger veto.

### 24C. Structural-R comparison of major diagnostics

Representative session-recorded risk-normalized metrics:

| Candidate | Structural R | PF_R | DD_R |
|---|---:|---:|---:|
| ALL1 | +253.72R | ~1.269 | ~100.95R |
| bounded m3 | +388.88R | ~1.466 | ~52.98R |
| bounded m3 + shock veto | **+428.23R** | **~1.562** | ~53.59R |
| stage SAFE/CONFIRM | +261.72R | ~1.294 | ~96.95R |
| loss-aware equal exposure | +287.01R | ~1.387 | ~61.93R |
| true V10 early-third Oracle | +733.18R | ~11.68 | ~5.38R |

This is session-recorded evidence and must be regenerated where the underlying post-HEAD model artifacts were not persisted.

## 25. Fixed campaign caps were diagnostics only

Loss-aware continuous sizing examples:

```text
cap 3:
units 1,531
PnL +7,953
PF 1.416
DD ~1,235

cap 5:
units 1,997
PnL +11,087
PF 1.460
DD ~1,708

cap 8:
units 2,312
PnL +13,674
PF 1.507
DD ~1,734
```

No fixed campaign cap is authorized.

## 26. V9 versus V10 context

2025-2026:

```text
V9 BASE
450 Children
PnL +5,307.95
PF ~1.515
DD 1,700.62

V10 bounded m3
1,159 entry events
2,313 units
PnL +14,827.57
PF 1.553
DD 2,638.04

V9 literal exit Oracle
PnL +16,476.18
PF ~3.799
DD ~856.81
```

The post-HEAD shock-veto diagnostic approached ~91% of V9 literal-Oracle raw dollar PnL, but not its path quality. These universes and architectures differ; this is context, not a claim of direct strategy superiority.

### 26A. V10 participation Oracle is a higher ceiling than the V9 exit Oracle

For the same broad 2025-2026 research era:

```text
V9 literal exit Oracle
PnL +16,476.18
PF ~3.799
DD ~856.81

V10 true early-third participation Oracle
PnL +23,344.73
PF ~15.157
DD ~148.81
R +733.18R
```

The V10 answer-sheet PnL is about `+$6,868.55`, or roughly `+41.7%`, above the V9 literal-exit Oracle.

This is the principal reason V10 remains a separate research generation: the larger information gap appears to be **participation selection and exposure placement**, not only better V9 terminal timing.

### 26B. The early-third Oracle is not a perfect economic Oracle

Even true early-third entries can lose. One 2026 diagnostic contained approximately:

```text
218 Oracle entries
45 negative outcomes
15 severe outcomes
9 structural stops
gross loss ~664
```

Therefore the final V10 objective is not:

```text
maximize ORACLE_EARLY recall at any cost
```

but rather:

```text
Participation opportunity
+
Economic safety / marginal Child value
```

A future causal policy can be economically better than a literal early-third imitation while having lower Oracle recall.

## 27. Negative results to preserve

Do not repeat unchanged without a genuinely new hypothesis:

1. universal k1 scout reduction;
2. pure delay to k2/k3;
3. broad LTF trend gates;
4. LTF warning used as early exit of profitable Children;
5. broad trailing morphology history;
6. broad morphology feature soup;
7. adding every LTF coordinate to CORE;
8. complex tree models that did not consistently beat compact heads;
9. continuous loss-magnitude regression as primary approach;
10. broad downside-score multiplication;
11. broad 12.5-25% danger veto;
12. automatic k1-abstention catch-up;
13. k2 harmful-loss veto;
14. ERA_RISK minimum;
15. Oracle recall as sole optimization target;
16. silent fixed Child/campaign caps.

## 28. Working V10 thesis after the post-HEAD research

V10 should not be reduced to:

```text
predict Oracle probability
-> size from one scalar
```

The stronger working interpretation is:

```text
early run
-> protect against rare catastrophic participation

middle run
-> confirm persistence

mature run
-> judge marginal Child economics

first opposite FAST HA
-> exit surviving campaign
```

Semantic heads:

```text
Opportunity
Danger
Persistence
Economic Child value
```

Possible actions:

```text
ABSTAIN
SCOUT / LIMITED PARTICIPATION
ADD
HOLD
STOP-ADDING
EXIT
```

No action threshold or lot map is authority yet.

## 29. Actual-tick gate status

A standalone bounded-m3 replay EA was built because the post-HEAD shock-veto model was not exactly reproducible.

The EA embedded only causal execution payload:

```text
decision timestamp
direction
units
structural SL
```

It did not embed:

```text
final run length
Oracle labels
future PnL
future exit timestamp
```

FAST H4 exit was recomputed from market history.

The first actual-tick run has now been analyzed. See:

`V10_BOUNDED_M3_ACTUAL_TICK_VALIDATION_20260916.md`

That run is a diagnostic, not a validation pass, because market-closed FAST-NHA exits were not latched and retried.

## 30. Evidence classes

### Class A — persisted / reproducible repository evidence

- original V10 comparators;
- bounded m3 entry/run ledgers;
- runway/sizing/formula studies.

### Class B — session-recorded consumed evidence requiring regeneration

- stagewise one-step models;
- exact danger-head coefficients;
- shock-veto row identity;
- continuous safety studies;
- some post-HEAD right-tail decompositions.

### Class C — actual-tick diagnostic evidence now persisted by summary

- event-ledger counts;
- MT5 Tester headline statistics;
- market-closed exit failure;
- exposure overlap / max-concurrent inflation;
- common-fill M1-vs-tick parity decomposition.

Class C is now analyzed, but the corrected execution semantics still require rerun.

## 31. Exact resume instruction

After refreshing GitHub main and reading normal V10 authority:

1. read this checkpoint;
2. read `V10_BOUNDED_M3_ACTUAL_TICK_VALIDATION_20260916.md`;
3. follow `V10_NEXT_RESEARCH_CONTRACT_EXECUTION_FIDELITY_AND_DANGER_REGEN_20260916.md`;
4. repair exit-intent persistence before interpreting another actual-tick headline;
5. regenerate post-HEAD danger / persistence models instead of guessing coefficients;
6. keep bounded m3 as the exact executable control until the new ledgers are reproducible.
