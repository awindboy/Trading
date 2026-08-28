# V5 Final Synthesis — Success-First / Payoff-First Research

Status: `CLOSED / HISTORICAL RESEARCH AUTHORITY`
Date closed: `2026-08-28`
Production authority: `NONE`
Final promoted strategy: `NONE`
Successor: `V6 — EVENT-CONDITIONED GENERALIZATION RESEARCH`

## 1. Why V5 existed

V5 was created after V3 and V4 failed in different ways.

- V3 found apparently meaningful GOLD structure/event relationships, especially in GOLD 2023-2025, but those relationships weakened or reversed in independent periods and markets.
- V4 deliberately moved from hand-authored state to raw-sequence learning, but in actual project work meaningful learning did not emerge despite multiple attempts. The practical V4 stop reason is therefore `NO USEFUL LEARNED SIGNAL`, not merely `CUDA RUN PENDING`.

V5 initially tried to recover progress by starting from successful traders and observable market mechanisms rather than by continuing to add V3 filters or by blindly increasing V4 model complexity.

The final project economics were raised during V5 to:

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2.0R
cost-adjusted expectancy     > 0
```

`2R` is an outcome criterion, not a fixed-TP instruction.

## 2. V5-001 to V5-025 — success-first mechanism falsification cycle

V5 first reverse-engineered public methods from successful discretionary/systematic traders, translated visible setups into causal hypotheses, then tested them mechanically.

Major families included:

- generic balance / breakout / cross-scale trendability;
- generic breakout-retest and failed price-discovery states;
- Raschke Holy Grail family;
- Turtle Soup / failure-fade families;
- Anti;
- Momentum Pinball;
- 80-20;
- related continuation / exhaustion / pullback variants.

The dominant recurring result was a structural trade-off:

```text
higher Entry survival -> winners too small
large multi-R winners -> realized hit rate too low
```

Representative historical examples:

- Holy-Grail-like variants could reach roughly 50-60% hit rates but average positive R remained too small and/or EV failed.
- Momentum Pinball produced very large average winners but hit rate was around the high teens.
- 80-20 generated large-R tails but hit rate was around the low teens and execution was fragile.

No V5-001..025 family satisfied the project's final economic target with adequate robustness.

Primary synthesis authority remains:
`V5_002_TO_V5_025_SUCCESS_FIRST_SYNTHESIS.md`.

## 3. V5-026 to V5-033 — First Cross research

### 3.1 Source interpretation

First Cross was interpreted as:

```text
slow 3/10 state crosses zero
-> first fast pullback through zero while slow regime remains
-> price confirms first higher-low / lower-high
-> causal price trigger
```

The oscillator was treated as an initial condition; Entry came from causal price confirmation.

### 3.2 Main progression

V5-026A broad reproduction:

```text
pooled N      10,480
WR            45.29%
avg positive   1.052R
EV            -0.231R
```

120-minute state was the strongest common intraday scale but still insufficient.

V5-027A/B introduced causal pivot confirmation and froze the 240-minute bridge scale before later exact replay.

V5-028A exact M1 replay:

```text
N              398
WR             46.73%
avg positive    1.354R
EV             +0.048R
```

V5-029A realized 50% at +1R and left a structural runner. It raised WR but manufactured small winners:

```text
N              390
WR             55.90%
avg positive    0.796R
EV             -0.030R
```

V5-030A changed management to:

```text
50% at +1R
runner SL -> Entry
runner exit = first completed 240m adverse EMA20 close OR slow-zero reversal
```

Corrected development result:

```text
N                   406
WR                  53.9409%
avg positive NET R   1.1968R
EV                  +0.1482R/trade
total               +60.154R
avg recorded cost     0.0955R/trade
```

Year results:

```text
2023 N138 WR55.07% avg+ 1.379R EV +0.271R
2024 N131 WR56.49% avg+ 1.048R EV +0.116R
2025 N137 WR50.36% avg+ 1.155R EV +0.055R
```

Market results:

```text
BTCUSD# N136 WR54.41% avg+1.276R EV+0.174R
GOLD#   N93  WR61.29% avg+0.951R EV+0.183R
XAUEUR# N86  WR51.16% avg+1.616R EV+0.307R
USDJPY# N91  WR48.35% avg+0.962R EV-0.077R
```

Under the old gate this was a development PASS.
Under D-180 it became a `FINAL ECONOMICS FAIL` because average positive NET R was only about 1.20R.

V5-031 daily alignment, V5-032 ATR adequacy, and V5-033 HG branch did not rescue the architecture.

Primary synthesis authority remains:
`V5_026_TO_V5_033_FIRST_CROSS_SYNTHESIS.md`.

## 4. V5-034 — external validation did not become strategy evidence

The frozen external panel was:

```text
XAUJPY#
XAUCNH#
GAUCNH#
GAUUSD#
2023-2025
```

The supplied Ultra Low broker histories began only around September 2025, so the preregistered 2023-2025 window did not exist for those exact symbols.

Therefore:

```text
V5-034A = UNEXECUTABLE AS PREREGISTERED
NOT strategy FAIL
NOT validation PASS
```

A short-window inception diagnostic was exploratory only and was not promoted because it was underpowered and point values were inferred rather than fully execution-authoritative.

After D-180, V5-030A no longer qualified for promotion anyway, so validation budget was not spent finding substitute markets merely to rescue it.

## 5. V5-035 — payoff-capacity and rescue audits

### 5.1 V5-035A payoff-capacity audit

Current V5-030A positive outcomes:

```text
resolved              406
positive               219 = 53.94%
mean positive NET R    1.1968R
median positive         0.580R
Q90 positive            2.092R
Q95 positive            3.498R
max positive           17.711R
```

Winner concentration was material:

```text
top 1%  of positives -> 14.94% of positive R
top 5%               -> 33.70%
top 10%              -> 45.63%
top 20%              -> 59.22%
```

Raw structural-regime MFE, N409:

```text
median MFE       0.864R
mean MFE         2.342R
>=1R            46.45%
>=2R            28.85%
>=3R            18.09%
>=4R            12.96%
```

The 2R excursion rate was broad across markets and years, but not sufficient by itself to satisfy the new final economics.

Among clear +1R activations (N223), post-1R MFE showed substantial continuation potential:

```text
median          1.845R
>=2R            45.29%
>=3R            27.80%
>=4R            18.83%
```

A key finding was that 28 of 100 eventual partial-BE trades had reached >=2R before returning to BE. The management architecture was giving back substantial favorable excursion.

### 5.2 Partial-fraction feasibility

The entire family

```text
realize fraction f at +1R
remaining 1-f uses same BE + EMA/slow runner
```

was evaluated algebraically without inventing a new exit signal.

Results included:

```text
f=0   WR 29.56% avg positive 2.755R EV +0.293R
f=.5  WR 53.94% avg positive 1.197R EV +0.148R
f=1   WR ~54.68% avg positive ~0.913R EV ~0.003R
```

Across all f in [0,1]:

```text
max avg positive while WR>=50%  ~1.515R
max WR while avg positive>=2R   ~39.66%
```

Therefore partial sizing alone was structurally incapable of the new joint target.

### 5.3 V5-035B structural-lock availability

A same-240m causal pivot trailing idea was audited only as shadow state.

Among N223 clear +1R trades:

```text
positive structural lock available 96 = 43.05%
median first lock                 ~0.794R
median max lock                   ~1.616R
median time to first lock         ~19.9h
```

Crucially:

```text
EMA/slow runners N123: lock available 57.7%, median max lock 2.621R
partial-BE N100:       lock available 25.0%, median max lock 0.765R
```

The structure mostly appeared on trades already becoming runners. It did not rescue the population that needed rescue.

Classification: `NEGATIVE AS SIMPLE RESCUE`.

### 5.4 V5-035C post-1R continuation-state falsification

Three source-native binary states at +1R were frozen without thresholds:

- H1: slow regime still alive;
- H2: fast line aligned;
- H3: price on favorable EMA20 side.

H1 was strongest pooled:

```text
slow alive true  continuation >=2R 50.0%
slow alive false continuation >=2R 18.2%
```

but direction instability was severe:

```text
SHORT difference  +3.1pp
LONG difference  +54.4pp
```

H2/H3 were weak and reversed in some market/year cells.

No rule was promoted.

## 6. V5-036 — V3 D-145 continuation-state portability

V3 had one unusually strong winner-continuation observation:

> among +1R survivors, lower M30 protected->external progress tended to be associated with later +2R continuation.

V5 did not auto-transfer the variable. It first inspected the exact V1 implementation.

### Stage 0 — measurement portability

The D-146 metric used global causal M30 `V1StructureState`:

```text
trend
protected boundary
external boundary
trade direction
observation price
```

It did not depend on Root/FVG/scenario identity.

An exact M30 state replay was reconstructed, including wave confirmation, INITIAL_BOS, protected break, continuation BOS, correction promotion, and processing order.

State-only delayed-start QA at +7/+14/+30/+60 days produced exact agreement whenever both runs had valid state.

Classification: `MEASUREMENT PORTABLE`.

### Stage 1 — relationship transfer

Inherited frozen prediction:

```text
median progress(+2R runner) < median progress(exhaust)
```

Observed First Cross transfer:

```text
valid N                122
runner median          1.0074
exhaust median         0.9649
```

The pooled sign reversed.

Breadth:

```text
markets supporting inherited sign    2 / 4
years supporting                     1 / 3
LONG supporting                      no
SHORT supporting                     no
comparable cells supporting          3 / 9
```

Final classification:

```text
PORTABLE OBSERVABLE
NON-TRANSFERRED RELATIONSHIP
FIRST CROSS PAYOFF-RESCUE CLOSED
```

This was important evidence that an apparently strong V3 relationship was not a universal Entry-independent market law.

## 7. V5-037 / V5-038 external-state experiments

These were late V5 scratch studies and are documented here to prevent repetition.
They are not production or strategy authority.

### 7.1 V5-037A US real-yield directional-delivery audit

Research question:

```text
Does causally available US 10y TIPS real-yield change
condition the next complete GOLD broker-day
in the inverse economic direction?
```

Causality work explicitly separated H.15 observation date from publication availability.

2023 discovery result was a clear falsification. Approximate final scratch summary:

```text
pooled mean signed close R        ~ -0.059R
pooled median signed close R      ~ -0.065R
median excursion advantage        ~ -0.051R
H1                                negative
H2                                negative
LONG                              negative
SHORT                             negative
fresh state                       worse than stale-state control
```

2024/2025 were not opened.
No magnitude/session/month/direction rescue was attempted.

Classification: `FATAL FALSIFICATION / CLOSED`.

### 7.2 V5-038 COT research

An initial exploratory Commercial-price-divergence scratch produced `FAIL_CLOSE`; however later source audit found that this was not the exact Larry Williams COT Index definition, so it is not retained as Williams-strategy evidence.

The source-faithful Williams branch was then redefined as:

```text
Commercial Net = Commercial Long - Commercial Short
COT Index = position of current Commercial Net in prior 156 weekly reports
>=80 bullish commercial extreme
<=20 bearish commercial extreme
```

Using Gold Legacy Futures Only, contract code 088691, the 2023 source-defined population contained only two qualifying reports and both were LONG extremes.

```text
qualifying 2023 reports = 2
minimum preregistered N = 12
```

Price outcomes were intentionally not opened.

Classification: `SOURCE-DEFINED POPULATION INSUFFICIENT / CLOSED BEFORE PRICE OUTCOME`.

No 80->75 threshold relaxation, window change, or extra years were used to rescue the branch.

### 7.3 V5-039 GLD physical-flow idea

A causal SPDR GLD holdings-flow runner was prepared, with next-day activation and stale/prior-GOLD controls.
The user then reset V5 away from external-variable hunting before this became a completed empirical branch.

Classification:

```text
PREPARED / NOT COMPLETED
NO RESULT
NO AUTHORITY
```

Do not treat it as failed or passed.

## 8. V5-040 / V5-041 — transition back toward modern learning

Late in V5 the user clarified the intended direction:

> use modern technology/research to solve V3's generalization limitation more intelligently; do not keep replacing the strategy with unrelated external variables.

This changed the research question again.

### 8.1 Broad event-conditioned population

Instead of learning final Candidate A/B, the exact V3-003C broad control was reconstructed before `DELIVERY_ACTIVE` and `STRONG_ACCEPTANCE`:

```text
2023  84 events / +1R 51.19%
2024  86 events / +1R 53.49%
2025  67 events / +1R 52.24%
total 237
```

Candidate-A parity was also reproduced:

```text
2023 40 / +1R 60.00%
2024 29 / +1R 65.52%
2025 27 / +1R 62.96%
```

This established that raw-data reconstruction was correct.

### 8.2 Event-conditioned GOLD-only raw-path learnability scratch

A fixed multi-timeframe raw-convolution diagnostic was run on causal pre-event sequences rather than on generic all-time next-return prediction.

Chronological primary-style results:

```text
train 2023 -> eval 2024     AUC ~0.456
train 2023-24 -> eval 2025  AUC ~0.572
pooled OOF                   AUC ~0.504
month-cluster 95% CI         ~0.424 to 0.579
exact-mirror pooled          AUC ~0.476
```

Individual timeframe behavior changed materially by year:

```text
         2024     2025
M1       .555     .514
M5       .494     .578
M30      .465     .609
H4       .434     .495
```

No best-timeframe selection was allowed.

Interpretation:

```text
NO STABLE GOLD-ONLY EVENT-CONDITIONED LEARNABILITY
```

This was highly consistent with the central V3 problem: the meaning of apparently similar event state changed across time.

### 8.3 Path taxonomy / label-noise audit

The binary `+1R before SL` label was decomposed using only symmetric price-path outcomes:

```text
+1 -> +2   W_CONTINUE
+1 ->  0   W_GIVEBACK
-1 ->  0   L_RECOVER
-1 -> -2   L_CONTINUE
```

Counts:

```text
                 2023  2024  2025  total
W_CONTINUE         22    20    18    60
W_GIVEBACK         21    26    17    64
L_RECOVER          22    18    19    59
L_CONTINUE         19    22    13    54
```

This proved the binary label mixed materially different outcomes.

However changing the target did not remove chronological instability.

Ordinal path-strength scratch:

```text
2024 Spearman  ~ -0.090
2025 Spearman  ~ +0.214
```

Robust extreme endpoints only (`W_CONTINUE` vs `L_CONTINUE`):

```text
2024 AUC ~0.425
2025 AUC ~0.714
```

Therefore simple label engineering was not enough. The evidence pointed toward concept drift / hidden context rather than merely noisy labels.

### 8.4 Domain-shift diagnostic

A scratch domain-classification audit found 2024 and 2025 pre-event raw distributions were distinguishable at approximately:

```text
domain AUC ~0.82
```

Yet outcome prediction was better in 2025, so simple covariate shift alone did not explain failure.

The 2023<->2024 relationship was less clean as a stable input-domain shift while the outcome mapping itself failed.

Interpretation: `concept drift / omitted latent context` became the stronger working hypothesis.

### 8.5 Cross-market hidden-context scratch

Causal synchronized context from the project's existing same-broker markets was then added:

```text
GOLD#
XAUEUR#
USDJPY#
```

The purpose was not a hand-made USDJPY filter. It was to let the model distinguish gold-specific repricing from currency-related state around the same anchored event.

Recovered scratch results for robust path endpoints:

```text
                         GOLD only   +XAUEUR+USDJPY
2024 extreme AUC           0.486          0.514
2025 extreme AUC           0.645          0.709

2024 ordinal rho          -0.034         +0.030
2025 ordinal rho          +0.084         +0.191
```

This was the first late-V5 result where adding context improved both chronological evaluation years in the same direction.

However it was NOT sufficient for promotion because:

```text
GOLD-only input     ~10 channels
cross-market input  ~30 channels
```

The improvement could therefore be a dimensionality/model-capacity artifact rather than real external information.

The preregistered next falsifier was a same-capacity `GOLD x3` 30-channel placebo.
That placebo was not completed before the V5/V6 phase boundary.

Classification:

```text
INTERESTING TRANSITIONAL SCRATCH
NOT CLAIM-GRADE
MIGRATED TO V6
```

## 9. What V5 actually taught the project

V5 did not produce a final strategy, but it materially narrowed the problem.

### Lesson A — payoff cannot be repaired casually after Entry

First Cross demonstrated that a setup can have:

```text
WR > 50%
positive EV
real 2R+ excursions
```

and still be structurally incapable of `WR>=50% + avg positive>=2R` under a nearby management family.

### Lesson B — an observable that generalizes inside one architecture may not transfer across Entry architectures

D-145 M30 progress was measurable outside V3 but its continuation relationship did not transfer to First Cross.

### Lesson C — external economic variables are not automatically useful trading state

Real yields failed even with careful point-in-time causality.
Source-faithful Williams COT extremes were too sparse in 2023 for the preregistered test.

### Lesson D — V3's central failure survives naive AI replacement

Event-conditioned raw GOLD paths also showed chronological sign/quality instability.

### Lesson E — V4's central failure must not be forgotten

The project has already tried generic raw-sequence learning without obtaining meaningful learning. V6 must therefore not equate `modern model` with `better research`.

### Lesson F — the most promising unresolved question is hidden context / concept drift

Cross-market context improved both 2024 and 2025 scratch results, but same-capacity placebo testing remained unfinished.
This is the clean handoff point to V6.

## 10. V5 final classification

```text
V5 STATUS                  CLOSED
FINAL STRATEGY             NONE
PRODUCTION AUTHORITY       NONE
GOLD PRIMARY MARKET        PRESERVED
FIRST CROSS                CLOSED / ECONOMIC FAIL
EXTERNAL-STATE BRANCH      CLOSED / NOT THE USER'S INTENDED DIRECTION
LATE AI/CONTEXT SCRATCH    MIGRATED TO V6
GOLD# 2021                 UNTOUCHED
```

V5 must not be reopened to rescue old branches.
Its results remain historical and mechanism evidence only.

Active research continues in `docs/ea/v6/`.
