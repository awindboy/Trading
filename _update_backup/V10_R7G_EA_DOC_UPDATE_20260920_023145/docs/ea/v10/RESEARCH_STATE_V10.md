# V10 Research State

Date: `2026-09-16`
Status: `ACTIVE HA-PRIMARY SHADOW RESEARCH / NO PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`

<!-- V10_POST_HEAD_STATE_20260916_START -->
## Latest state addendum — 2026-09-16

The initial V10 state below is preserved. The latest research refinement is:

```text
single Oracle-likeness scalar
-> insufficient description

current working state:
Opportunity
+ Danger
+ Persistence
+ marginal Child value
```

Strong post-HEAD observations:

- destructive false positives, especially very short FAST runs, explain a large part of the Oracle gap;
- one-step FAST survival is easier to model than final run length from k1;
- compact M15/M30/H1 body-flow + persistence is more useful than feature soup;
- k1 and k2 have different jobs;
- broad downside filters delete large winners;
- only an extreme danger tail showed promising abstention behavior;
- automatic exposure catch-up after a k1 veto was weak;
- late non-Oracle Children in long runs can remain economically useful.

Best recorded but not yet reproducible post-HEAD bounded diagnostic:

```text
bounded m3 + extreme NHA-shock veto
PnL +15,013.69
PF 1.57811
DD ~2,703.62
R +428.23R
```

Actual-tick gate:

```text
984 fills
174 market-closed entry rejects
1 SL-already-touched reject

raw tester:
PnL +16,220.67
PF 1.686554
Balance DD 8.52%
Equity DD 15.27%

critical defect:
market-closed FAST_NHA_EXIT was not latched/retried
-> unintended holding
-> ~311h opposite-direction overlap
-> max concurrent 16 vs intended 12
```

Where exit semantics stayed comparable, the 853-position normal subset showed close M1-vs-tick parity (`+$11,618.07` M1 reference versus `+$11,478.19` actual tick).

Therefore the immediate next objective is execution fidelity first, then model regeneration.
<!-- V10_POST_HEAD_STATE_20260916_END -->

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

<!-- V10_REPRO_LEDGER_STATE_20260916_START -->
## Reproducibility state — 2026-09-16

The following evidence is now persisted rather than summarized only in prose:

```text
raw Strategy Tester event CSV + report XLSX
1,159 signal-execution rows
175 selected entry rejects
134 rejected NHA-close requests
84 distinct exit-reject incidents
131 contaminated filled positions
131 intended-vs-actual pending-exit delay rows
1,968 normalized deals
1,968 normalized orders
1,968 deal-by-deal exposure states
33 opposite-direction overlap episodes
252 structural-SL execution rows
1,159 causal selected-signal MTF feature rows
```

The selected-signal feature ledger is bound to exact M15/M30/H1/H4 source SHA256 values. Its future answer-sheet columns are explicitly named and prohibited as live features.

New deterministic regeneration artifacts persist preprocessing, coefficients, scores and prior-percentile references. Their population is `BOUNDED_M3_SELECTED`; they are not the lost original full-universe Danger model.

This improves reproducibility but does not change the promotion status: V10 remains shadow research with no production authority.
<!-- V10_REPRO_LEDGER_STATE_20260916_END -->

<!-- V10_REGIME_RISK_STATE_20260917_START -->
## Current research state — 2026-09-17

The active problem has advanced again.

### Main clock

```text
H4 FAST remains the campaign clock.
H1-main was tested and rejected as the current direction because turnover/churn exploded and PF approached 1.
```

### Participation state

The working topology is now:

```text
LONG
-> FAST NHA -> EXIT
-> either opposite campaign admission OR NEUTRAL

NEUTRAL
-> wait for causal regime/direction organization
-> LONG or SHORT when admission is justified
```

Current evidence distinguishes:

```text
REGIME
ADX + H4 path efficiency + flip context

DIRECTION
EMA + DI + compact M15/M30/H1 HA delivery + STD/SLOW phase
```

Post-hoc conditional-NEUTRAL scans produced roughly `+17.4k` to `+17.9k` on the consumed bounded-m3 sample while preserving October trend profits much better than universal hard gates. These values are research diagnostics, not authority.

### Risk state

The V9-derived nearest-active H1 liquidity stop is now a comparator rather than the preferred design direction.

Leading clean HA-native Hard-SL candidate:

```text
LONG  -> previous completed H4 STD HA low
SHORT -> previous completed H4 STD HA high
```

Local fixed-lot reconstruction:

```text
+14,357.83
PF 1.538
DD 2,552.97
1,158 / 1,159 valid stop rows
median stop distance 28.85
```

Money-risk interpretation under this stop:

```text
Equal Child risk:
+170.80R / PF_R 1.382 / DD 28.67R

W1=1, W3=3 risk units:
+401.88R / PF_R 1.467 / DD 60.21R
max committed 12 risk units
```

Campaign-risk scans show substantial R can survive lower maximum committed risk, but no cap value is promoted.

### Current integrated architecture hypothesis

```text
H4 FAST campaign clock
+ regime-aware reverse admission / NEUTRAL
+ compact direction confirmation
+ previous-STD H4 HA Child Hard SL
+ Child money-risk sizing
+ campaign aggregate risk ceiling
+ FAST opposite HA campaign exit
```

No production V10 strategy exists.
<!-- V10_REGIME_RISK_STATE_20260917_END -->

<!-- V10_R3_CAUSAL_ML_STATE_20260917_START -->
## Current causal-ML state — 2026-09-17

The ML research question is now narrower and more reproducible.

### Input state

```text
official raw GOLD M1 SHA guarded
single chronological M1 pass
M15/M30/H1/H4 completed-bar reconstruction
6,770 Child rows / 2,139 resolved FAST runs
label_available_at purge
3,962-row exact R2 decision parity for 2024-2026
```

### Model state

Rejected:

- broad `trendable3` REGIME admission model;
- generic negative-R danger target;
- treating generic log-loss winner as automatic action-model winner;
- HistGB/union as action authority despite attractive realized DD.

Primary future shadow hypothesis:

```text
R2-selected k1 population
21 purpose-specific causal features
RobustScaler(10,90)
LogisticRegression C=0.5
Platt calibration from chronological OOF predictions
q97.5 prior-OOF extreme tail
```

Consumed result:

```text
1,573 -> 1,556 selected positions
17 vetoes: 16 losses / 1 win
R +532.16 -> +553.83
PF_R 1.4525 -> 1.4813
DD_R 52.41 -> 45.41
pooled bootstrap delta-R 95% [6.03, 38.74]
```

### Compliance state

The R2 committed ledger and current EA differ on six actions because the ledger applies conditional-NEUTRAL per Child while the EA latches run admission. R3 has not been integrated into MQL.

### Authority state

```text
shadow hypothesis only
no threshold promotion
no EA authority
no independent validation
no 2021 reserve use
```

Next contract: `V10_NEXT_RESEARCH_CONTRACT_K1_SHADOW_FORWARD_20260917.md`.
<!-- V10_R3_CAUSAL_ML_STATE_20260917_END -->

<!-- V10_R7_SIZING_STATE_20260917_START -->
## Current sizing research state — 2026-09-17

R6 showed that direct realized-R meta, standalone right-tail classification, simple relative-rank normalization, specialist stacking, and generic exposure downgrade did not produce a stable improvement over R4 across fixed Gold quarter samples.

The research role of ML is therefore narrowed:

```text
HA / R4
-> participation clock and base action

ML
-> opportunity / downside evidence
-> exposure sizing assistance

recent realized causal feedback
-> whether the current environment is still paying for extra exposure
```

Direct next-HA prediction is not current authority. Earlier flow remains useful context, but next-step / survival predictability did not translate stably into economics across regimes.

Current frozen R7G shadow:

```text
R4 weight 1
+ R5 EV positive
+ prior-exited eligible Child mean R positive over last 180 completed H4 bars
-> upgrade 1 to 3 units
```

Consumed full-quarter diagnostic through partial 2026 Q3:

```text
R4   +485.07R
R7G  +741.01R
delta +255.94R
PF_R 1.583 -> 1.682
DD_R 50.32 -> 59.71
```

Raw-M1 price-path audit passed for 2,182 non-stop and 658 stop Children.
The raw `pnl` unit is GOLD price movement, not account-currency PnL.

R7G's incremental economics remain right-tail dependent: short FAST runs lose additional R while L6+ runs pay for the extra exposure.

Authority status:

```text
R7G = promising consumed-data sizing shadow
!= strategy authority
!= EA authority
!= independent validation

no-k3p-SHORT = post-hoc diagnostic only
180 H4 = research horizon only
```

Next: exact reproducibility -> Python/MQL sizing parity -> actual-tick/cost semantics -> Child account-risk lots -> campaign committed-risk ledger -> future-only shadow evidence.
<!-- V10_R7_SIZING_STATE_20260917_END -->
