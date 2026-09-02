# V8-A-N-SLOW Persistence / Structural Retention Research — 2026-09-02

Status: `DEVELOPMENT EVIDENCE / STRUCTURAL RETENTION RETAINED / NO PRODUCTION AUTHORITY`
Market: `GOLD#`
Base Git HEAD: `cde7cfec1a6e07b872c72cdfaa62562c5e545735`
Raw M1 source SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`

## 1. Why this research was opened

The current Slow-N ONSET model predicts:

```text
T_onset = 0.25 * previous-completed H4 Wilder ATR14
P15 = P(price touches C0 +/- T_onset within 15m)
fresh75 = previous P15 < 75%, current P15 >= 75%
```

This is an excursion / first-barrier-touch question. It is **not** a terminal net-displacement question and it is **not** a persistence question.

The user challenged the prior interpretation: if ONSET only says that price is likely to touch a barrier, a directional strategy also needs to know whether the move is accepted / retained rather than immediately reversed.

This research therefore separates:

```text
ONSET      = is a volatility episode beginning?
REVEAL     = which direction did price actually attempt?
ACCEPTANCE = did price pull back and reclaim the revealed territory?
RETENTION  = will the accepted LTF structure remain intact?
EXTENSION  = is a materially larger movement episode likely?
```

The goal is to discover whether HTF movement probability and LTF structural persistence can be connected causally without pretending that excursion probability already contains direction.

## 2. Important semantic correction: P15 is excursion, not persistence

Current Phase-0 Slow-N fresh75 remains:

```text
2024 N653 / touch15 78.10%
2025 N535 / touch15 78.50%
2026 N321 / touch15 76.01%
```

However, among touched events, only roughly `46-49%` still finish the 15-minute window at a full `0.25 H4 ATR` displacement in the touched direction.

Touch followed by later origin loss is common, roughly `34-42%` depending on year/model realization.

Therefore:

```text
P15 high
!=
high probability that the directional move persists
```

The current P15 authority should be described as an **ONSET / excursion detector**.

## 3. Net-displacement labels were tested separately

Additional labels were built:

```text
NET-HALF:
abs(C15 - C0) >= 0.125 H4 ATR

NET-FULL:
abs(C15 - C0) >= 0.25 H4 ATR

ACCEPT-HALF:
0.25 ATR barrier is touched and
C15 remains at least 0.125 ATR in the touched direction
```

Inside current Phase-0 fresh75, representative factual rates were approximately:

```text
NET-HALF    ~66-69%
NET-FULL    ~40-42%
ACCEPT-HALF ~51-56%
```

The original 86-feature Slow-N representation can model these labels over the full M5 population with moderate AUC, but **inside the already-selected fresh75 population** additional discrimination falls to roughly chance (`~0.47-0.56`).

Interpretation: pre-fresh information used by ONSET is largely exhausted by the fresh75 selection itself. This argues against simply attaching another static `PERSIST` head to the same fresh-time feature vector.

## 4. Direction reveal alone does not create momentum

A family of causal reveal tests was run.

Representative reveal distances:

```text
0.10 / 0.15 / 0.20 / 0.25 H4 ATR
and later
0.30 / 0.40 / 0.50 H4 ATR
```

Both fixed H4-scaled and local M1/M5-ATR-scaled reveal definitions were checked.

An early result appeared very strong when asking whether the reveal direction later reached a larger origin-anchored target first. That result was rejected as a **distance-geometry artifact**: after price has already moved +0.25 ATR, the next upside origin-anchored target is much closer than the symmetric downside origin-anchored target.

When the test was corrected to equal-distance barriers from the **current reveal / acceptance price**, continuation returned to approximately chance.

Representative equal-distance continuation after a 0.25-ATR reveal:

```text
roughly 48-55% depending on year / distance
```

Waiting for 2/3/5 additional M1 closes above the reveal territory did not produce a robust universal continuation law.

Conclusion:

```text
direction reveal
!=
reliable immediate momentum edge
```

## 5. Blind pullback entry also failed

After reveal, 25/40/50% retracement entries were tested.

Blind limit entry cannot distinguish:

```text
healthy retracement
from
true reversal
```

because both winner and loser paths pass through the same retracement levels.

The useful state appeared only after requiring:

```text
direction reveal
-> pullback
-> reclaim
```

which is referred to below as **ACCEPTANCE**.

## 6. Acceptance state definition

Primary research state:

```text
Slow-N fresh75
-> price produces +/-0.25 H4 ATR M1-close reveal
-> reveal occurs within 15m of the fresh decision
-> price pulls back at least 25% of the reveal leg
-> origin is not lost before acceptance
-> M1 close reclaims the +/-0.25 ATR reveal level
```

Robustness families also used:

```text
reveal horizon: 15m / 30m
pullback fraction: 25% / 40% / 50%
```

No pullback fraction is production-frozen.

## 7. A key false-positive was found in the first PERSIST-A formulation

The first persistence outcome was:

```text
same direction 0.50 ATR target
vs
pullback extreme failure
```

and initially showed AUC around `0.66-0.74`.

Regression analysis showed that much of this came from simple first-passage geometry:

```text
distance to target
distance to failure
```

A two-feature geometry-only model itself reached roughly `0.69-0.72` AUC.

Therefore the initial PERSIST-A result was **downgraded**.

Equal-distance continuation tests from the current price again returned near chance.

This is an important anti-overfit finding: target/failure geometry must not be confused with a directional persistence law.

## 8. Structural Retention is the strongest surviving persistence concept

The persistence question was reframed.

After acceptance, define the pullback extreme:

```text
LONG  -> pullback low
SHORT -> pullback high
```

Structural Retention asks:

> after the reclaim is confirmed, does this pullback extreme remain unbroken for the next H minutes?

Primary horizons:

```text
15m / 30m / 60m
```

Equality with the pullback extreme counts as a break in the retained ledger.

This is not "will price keep trending immediately?" It is:

```text
P(accepted LTF structure remains valid)
```

## 9. Compact `micro3` retention model

The most stable compact causal feature set is:

```text
prog1 = directional progress of the reclaim-confirming final M1 bar
run   = same-direction consecutive M1 run at acceptance
prog3 = directional progress over the recent 3m path
```

All are known at acceptance time.

Regularized logistic model:

```text
StandardScaler
L2 logistic regression
C = 0.5
chronological future-year evaluation
```

The coefficients are unusually stable across phase/year training fits:

```text
prog1 always positive: ~0.56 to 0.67
run   always positive: ~0.24 to 0.45 for 15/30m; weaker at 60m
prog3 always negative after controlling prog1/run
coefficient-vector cosine similarity:
~0.976-0.987 for 15m
~0.979-0.990 for 30m
~0.922-0.957 for 60m
```

Interpretation is intentionally narrow: the strongest retained acceptance states tend to show a sharp final reclaim impulse / run after a less one-directional recent 3-minute path.

Do not convert this into a generic "strong last candle = trend" rule outside the defined acceptance population.

## 10. Primary Structural Retention result

Primary family:

```text
reveal <= 15m
pullback >= 25%
acceptance = 0.25 H4 ATR reclaim
```

### 15-minute pullback-extreme retention

| Phase | Test year | N | Base retention | AUC |
|---:|---:|---:|---:|---:|
| 0 | 2025 | 236 | 36.86% | 0.7290 |
| 0 | 2026 | 153 | 34.64% | 0.7353 |
| 2 | 2025 | 235 | 36.60% | 0.7540 |
| 2 | 2026 | 144 | 34.72% | 0.7270 |

### 30-minute retention

| Phase | Test year | N | Base | AUC |
|---:|---:|---:|---:|---:|
| 0 | 2025 | 236 | 28.39% | 0.7222 |
| 0 | 2026 | 153 | 27.45% | 0.7124 |
| 2 | 2025 | 235 | 27.66% | 0.7252 |
| 2 | 2026 | 144 | 27.78% | 0.6933 |

### 60-minute retention

| Phase | Test year | N | Base | AUC |
|---:|---:|---:|---:|---:|
| 0 | 2025 | 236 | 22.46% | 0.7256 |
| 0 | 2026 | 153 | 22.22% | 0.7128 |
| 2 | 2025 | 235 | 21.28% | 0.7211 |
| 2 | 2026 | 144 | 21.53% | 0.6840 |

The signal therefore survives two probability-model realizations, two future years and three retention horizons.

## 11. Statistical stress

Week-block bootstrap and within-quarter permutation were run for the primary family.

Representative 15m results:

```text
P0 2025 AUC .729
95% week-block bootstrap ~.650-.805
quarter-preserving permutation p=.0005

P0 2026 AUC .735
bootstrap ~.681-.795
p=.0005

P2 2025 AUC .754
bootstrap ~.670-.827
p=.0005

P2 2026 AUC .727
bootstrap ~.660-.803
p=.0005
```

30m and 60m remained positive; the weakest reported cell was P2-2026 60m AUC `.684`, with bootstrap lower bound about `.609` and permutation `p=.001`.

These are **development-data diagnostics**, not untouched validation p-values.

## 12. Overlap / event clustering stress

To reduce the possibility that clustered fresh events inflate AUC, acceptance events were collapsed so that a retained event must be separated by at least 60m or 120m.

For the primary 15m retention label, AUC remained approximately:

```text
P0 2025 .742 / .740
P0 2026 .752 / .753
P2 2025 .748 / .738
P2 2026 .738 / .731
```

for 60m / 120m collapse respectively.

Therefore the signal is not explained by repeated near-identical overlapping events.

## 13. Direction stress

Primary 15m retention:

```text
2025:
P0 SHORT .808 / LONG .622
P2 SHORT .800 / LONG .696

2026:
P0 SHORT .790 / LONG .688
P2 SHORT .794 / LONG .669
```

Both directions remain above chance, but SHORT is materially stronger.

Do not create a "SHORT-only" rule from consumed years. The correct conclusion is that the retention mechanism is direction-asymmetric and future research must explicitly test regime/direction interaction.

## 14. Quarter stress

Primary 15m quarter AUCs remain mostly positive.

Representative Phase-0:

```text
2025Q1 .810
2025Q2 .793
2025Q3 .631
2025Q4 .684
2026Q1 .746
2026Q2 .693
2026Q3 .833 on small N
```

Phase-2 is similar, with the weakest substantial cell around `2025Q3 ~.598`.

No single quarter explains the full annual signal, but quarter/regime variation is material.

## 15. Pullback / reveal family robustness

The effect is not limited to one exact semantic cell.

### 25% pullback

Across reveal horizon 15m/30m, phase0/2, years 2025/26:

```text
15m-retention AUC ~.727-.754
30m-retention AUC ~.689-.725
60m-retention AUC ~.681-.726
```

### 40% pullback

Still positive but somewhat weaker:

```text
15m-retention AUC ~.666-.740
30m-retention AUC ~.643-.728
60m-retention AUC ~.612-.702
```

### 50% pullback

Materially weaker and less stable, especially in 2025.

Interpretation: the strongest retained signal is associated with relatively shallow-to-moderate accepted pullbacks. Deep 50% pullbacks are a different / weaker state.

Do not optimize an exact pullback percent from these consumed results.

## 16. Score ordering and calibration

Training-derived score quantiles were carried into future years.

For 15m retention, Q75 coverage is roughly `21-26%` of the acceptance population.

Observed retention in the future Q75 bucket:

```text
P0 2025 52.0% vs base 36.9%
P0 2026 57.5% vs base 34.6%
P2 2025 60.0% vs base 36.6%
P2 2026 61.8% vs base 34.7%
```

Q90 has only ~12-24 events per cell and is unstable; it must not become an operating threshold.

The model ranks retention meaningfully, but calibration is not yet production-grade.

No retention trigger is frozen.

## 17. Equal-distance directional continuation remains negative

Even after acceptance, the model does **not** robustly predict which equal-distance side from the current price will be reached first.

Equal-distance continuation models across:

```text
+/-0.10
+/-0.15
+/-0.25 H4 ATR
```

remain approximately chance.

Therefore:

```text
Structural Retention
!=
generic direction continuation probability
```

This distinction is mandatory in future interpretation.

## 18. Later rung persistence weakened after geometry control

Earlier exploratory PERSIST-B/C results (`0.50->0.75`, `0.75->1.00`) looked positive before strict geometry decomposition.

After the same correction:

```text
0.50 -> 0.75 path-only:
unstable / roughly .36-.58

0.75 -> 1.00:
small sample / year reversal
```

Pooling all 0.25-ATR rungs into a universal scale-normalized survival model did not rescue 2025 late-rung performance.

Conclusion: a universal Markov law at every 0.25-H4-ATR rung is not supported.

The strongest persistence information is currently concentrated around the first accepted LTF structure after ONSET.

## 19. Relationship to directionless EXTENSION

Current EXT remains:

```text
T_ext = 0.75 * previous-completed H4 ATR14
P60 / P120 / P240
```

### Realized retention is strongly associated with same-direction extension

Among accepted events, actual 15m pullback-extreme retention is associated with materially higher same-direction `0.75 ATR` realization.

Representative Phase-0:

```text
2025
same-side hit within 120m:
retention failed 40.4%
retention survived 67.9%

same-side hit within 240m:
44.1% vs 74.4%

2026
120m:
40.2% vs 58.8%

240m:
49.4% vs 66.7%
```

Phase-2 is materially similar.

So actual structural retention contains directional meaning.

### But the predicted retention score does not directly solve extension direction

The retention score alone has near-chance AUC for same-direction 0.75-ATR hit when used directly.

Fresh-time EXT alone is also weak for same-direction delivery.

Simple models using `micro3 + EXT` improve some future cells:

```text
same-direction 0.75ATR / 60m:
P0 2025 .616
P0 2026 .667
P2 2025 .566
P2 2026 .652

120m:
P0 2025 .573
P0 2026 .628
P2 2025 .528
P2 2026 .590

240m:
P0 2025 .567
P0 2026 .619
P2 2025 .531
P2 2026 .574
```

This is not yet robust enough for authority.

The `retention score * EXT score` product predicts the **joint event** "retention survives and same-direction extension occurs" with AUC roughly `.62-.74`, but does not materially predict same-direction extension alone (`~.46-.51`).

Interpretation: current EXT remains mostly a directionless movement-magnitude signal. Retention is a directional structural-validity signal. Their simple static combination is not yet the full bridge.

## 20. Q75 x Q75 combination is too sparse

Applying training-derived Q75 thresholds to both retention and EXT creates very small intersections, typically `N ~3-10`.

Some percentages look high, others reverse.

Therefore:

```text
do not freeze RETENTION-Q75 + EXT-Q75
```

as a trading gate.

## 21. Why waiting for full 15m retention is too late

If one waits until the 15-minute structural-retention outcome is fully known, many of the desired 0.75-ATR moves have already happened.

Among confirmed-retention cases, roughly `34-38%` had already reached the same-direction 0.75-ATR target before the 15m confirmation time.

After excluding those already-completed cases, same-direction post-confirmation realization remains meaningful but smaller.

Representative post-confirmation same-direction 0.75 hit:

```text
2025:
~50.6% within 60m
~60-62% within 120m
~72-74% within 240m

2026:
~40-41% within 60m
~57-58% within 120m
~62-64% within 240m
```

Therefore the strategy should **predict retention early**, not wait for the full 15m label to resolve.

## 22. Final research interpretation

The strongest current causal architecture is:

```text
Slow-N ONSET
0.25 H4 ATR / P15 fresh75
        |
        v
directional M1-close reveal
        |
        v
pullback
        |
        v
reclaim = ACCEPTANCE
        |
        v
dynamic STRUCTURAL RETENTION probability
"will the pullback extreme remain intact?"
        |
        +----> directionless EXT context
        |
        v
later entry / holding research
```

This is materially different from:

```text
P(move) + static direction classifier
```

The new working hypothesis is:

> direction is not necessarily forecast at fresh time. Price first reveals a side; the useful prediction problem is whether that accepted side retains its structure long enough for a larger HTF-scale move to be delivered.

## 23. What is closed / downgraded

Do not rescue or re-open without genuinely new information:

- immediate reveal = momentum;
- equal-distance continuation after reveal;
- blind pullback limit entry;
- extra M1-close dwell confirmation;
- generic M1 technical-indicator majority;
- initial PERSIST-A target-vs-pullback-extreme AUC as a pure persistence claim;
- PERSIST-B/C as universal rung laws;
- simple EXT threshold as directional permission;
- Q75 x Q75 retention/EXT gating;
- exact retracement-percent optimization.

## 24. What remains active

### Retained primary research candidate

`Structural Retention / micro3`

Primary semantic family:

```text
fresh75
-> <=15m 0.25ATR M1-close reveal
-> >=25% pullback, origin retained
-> 0.25ATR M1-close reclaim
-> predict pullback-extreme survival over 15/30/60m
```

Status:

`STRONG DEVELOPMENT CANDIDATE / NOT PRODUCTION / NOT A COMPLETE ENTRY RULE`

### Secondary context

- directionless EXT `0.75 H4 ATR / P60-P120-P240`;
- BB-B accepted upside expansion context;
- raw-tick/M1 temporal re-synchronization, still incomplete on full Slow-N coverage.

## 25. Next research — predeclared direction

The next stage should not tune retracement percentages or score thresholds from P/L.

### A. Dynamic retention hazard

Instead of predicting one fixed 15m label only at acceptance, update:

```text
P(structure survives next 1m)
P(survives next 3m)
P(survives next 5m)
P(survives next 10m)
P(survives next 15m)
```

after each completed M1 bar.

This directly addresses the problem that waiting 15m is too late.

### B. Competing-risk bridge

At each accepted state, model mutually competing outcomes:

```text
1. pullback extreme breaks
2. same-direction 0.50 / 0.75 ATR delivery
3. opposite-direction 0.75 ATR delivery
4. unresolved by horizon
```

Do not use asymmetric target/failure geometry without an explicit control.

### C. Raw tick incremental retention test

Use V4 wall-clock alignment around:

```text
reveal
pullback extreme
reclaim / acceptance
```

Predeclare aligned and shifted-placebo windows.

The question is no longer generic tick direction:

> do final quote/tick transitions add incremental information about early structural retention beyond micro3?

### D. Direction/regime interaction

SHORT retention is consistently easier to rank than LONG in 2025/26 consumed evidence.

Research the causal regime/context interaction without creating a direction-specific rule from 2026.

### E. BB-B interaction

Test BB-B as a context for:

```text
accepted upside structure
+
structural retention
```

not as a generic upper-band breakout vote.

### F. Calibration / threshold work only after architecture freeze

No Q75/Q90 trigger authority.

After the dynamic-hazard architecture is frozen:

- calibration;
- score-decile monotonicity;
- monthly/quarterly stability;
- phase-realization robustness;
- MT5/Python parity.

### G. Entry / economics remain closed

Do not optimize SL/TP yet.

First freeze:

```text
candidate lifecycle
reveal
acceptance
retention score timing
entry timing
failure state
```

Then preregister payoff/economics.

### H. Mandatory-fresh objective is reframed, not abandoned

Every ONSET fresh should open a deterministic candidate lifecycle.

It is no longer necessary to force an immediate position at the fresh close if the research architecture requires later causal reveal/acceptance.

However, events may not be silently deleted because a hindsight outcome is bad.

Any lifecycle timeout / no-acceptance / structural failure must be defined before economics.

### I. 2021 remains locked

`GOLD# 2021` is not opened by this research.

## 26. QA notes

- latest base repository commit for this package: `cde7cfec1a6e07b872c72cdfaa62562c5e545735`;
- raw M1 SHA matched current Slow-N authority;
- Phase-0 fresh census reproduced exactly (`653/535/321`);
- causal H4 decision-block target alignment was preserved;
- equal-distance controls were used to expose geometry artifacts;
- event-overlap collapse was run;
- week-block bootstrap and quarter-preserving permutation were run;
- Phase-0 and Phase-2 probability-model realizations were both used;
- direction and quarter stresses were run;
- no 2021 evidence was used;
- no production threshold or P/L optimization was authorized.
