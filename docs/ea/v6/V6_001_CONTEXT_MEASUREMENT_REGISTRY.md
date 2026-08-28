# V6-001 — Context-Measurement Hypothesis Registry

Status: `ACTIVE / PRE-OUTCOME DESIGN`  
Date: `2026-08-28`  
Production authority: `NONE`

## 1. Purpose

V6-001 defines the parent research map before child indicator/context experiments are activated.

The goal is not to collect as many indicators as possible.

The goal is to identify a small number of causally meaningful measurements that could explain specific V3 failure modes, freeze their research order without outcome shopping, and test them one family at a time.

## 2. Target V3 failure modes

Every child must name at least one target.

### F1 — direction-premise failure

The original event direction itself is wrong.

Historical clue:
- weak V3 cells and GOLD 2022 showed exact mirrors sometimes beating the intended direction.

### F2 — weak delivery / temporary reaction

The event produces local reaction but not durable directional delivery.

### F3 — stop-sensitive recovery

The event is directionally plausible but adverse path/stop geometry causes failure before later recovery.

### F4 — winner exhaustion / giveback

The trade reaches favorable excursion but does not continue.

### F5 — execution/liquidity degradation

The market idea may be valid but spread/feed/session/execution conditions destroy realized economics.

Do not use one label to mix these failure modes if the measurement hypothesis is stage-specific.

## 3. Family A — own-market endogenous state

Possible latent dimensions:

- trend/structure persistence;
- directional maturity/progress;
- compression vs expansion;
- realized volatility/range state;
- path efficiency/choppiness;
- tick-volume/activity state;
- higher-timeframe relative location;
- recent directional asymmetry.

Governance:

- consumed V3 variables are references, not free features to retune;
- D-145/V5-036 proves a measurement can be portable while its predictive meaning is not;
- standard indicators are allowed only when their transform has a named state interpretation;
- no oscillator/window tournament.

Primary relevance:

```text
F1 / F2 / F3 / F4
```

## 4. Family B — cross-market / relative state

Purpose:

Measure whether the GOLD event occurs inside a broader currency/gold-relative state not visible in GOLD alone.

Prepared child:

```text
V6-001A
GOLD + XAUEUR + USDJPY
vs
same-capacity GOLDx3
```

Important:

- V5-041 is consumed scratch evidence;
- V6-001A is a capacity-confound cleanup, not pristine discovery;
- failure closes the exact XAUEUR/USDJPY formulation only;
- no replacement-market shopping inside V6-001A.

Potential later cross-market hypotheses require a separate parent-registry update before outcomes.

Primary relevance:

```text
F1 / F2 / F4
```

## 5. Family C — macro / rates state

Purpose:

Measure slow economic state that may alter the meaning of a GOLD event.

Eligible examples only when source-qualified and causally available:

- real/nominal yield state;
- inflation-expectation state;
- broad USD state;
- monetary/liquidity environment.

Historical boundary:

V5-037 falsified one specific 2023 next-day inverse real-yield directional-delivery hypothesis.

That result means:

```text
do not rerun that same direct predictor
```

It does NOT mean:

```text
real yield can never be a conditioning variable
macro context is useless
```

Any V6 reuse must pose a different preregistered event-conditioning question and must explicitly separate it from the consumed V5 direct-day hypothesis.

Primary relevance:

```text
F1 / F2 / F4
```

## 6. Family D — positioning / fund-flow state

Purpose:

Measure slow participant positioning/capital-flow context.

Eligible examples:

- source-faithful COT state;
- ETF/fund holdings or flow;
- other source-qualified positioning measures.

Historical boundary:

- V5 source-faithful COT 2023 population was too sparse; price outcome was not opened.
- V5 GLD flow was prepared but not run.

Therefore these are not classified as predictive failures.

But sample density and update frequency must be qualified before any price outcome is opened.

Primary relevance:

```text
F1 / F2 / F4
```

## 7. Family E — execution / liquidity environment

Purpose:

Distinguish semantic strategy failure from environment-specific execution degradation.

Possible measurements:

- spread relative to structural risk;
- quote/activity state;
- session availability;
- broker/feed regime;
- symbol execution scale.

Historical boundary:

V3 2022 Candidate-A survival did not recover under zero-spread replay, so execution alone cannot explain V3's main generalization collapse.

Execution remains mandatory for final economics.

Primary relevance:

```text
F3 / F5
```

## 8. Family F — scheduled-event / market-environment state

Purpose:

Measure whether the event occurs in a structurally different information/liquidity environment.

Examples may include scheduled macro-event proximity or other causally known calendar state only if a physical/economic mechanism is stated first.

Prohibited:

- generic session/day/month filters selected because they improve outcomes;
- calendar mining without a preregistered mechanism.

Primary relevance:

```text
F1 / F2 / F3 / F5
```

## 9. Outcome-blind prioritization criteria

Before activating a child, score qualitatively — without opening new price outcomes — on:

1. `DIRECT LINK TO KNOWN V3 FAILURE`
2. `CAUSAL AVAILABILITY`
3. `COVERAGE / SAMPLE DENSITY`
4. `MEASUREMENT INDEPENDENCE`
5. `UPDATE FREQUENCY COMPATIBLE WITH EVENT`
6. `CONTROL QUALITY`
7. `CONSUMED-EVIDENCE STATUS`
8. `IMPLEMENTATION AUDITABILITY`

Do not use prior favorable AUC/WR as the sole ranking criterion.

Consumed evidence may motivate a falsification/cleanup test, but it cannot be treated as pristine discovery.

## 10. Child activation template

Before any child runs, create/freeze:

```text
child id
family
target failure mode
state hypothesis
source/data identity
causal availability rule
measurement/transform
population
target outcome stage
chronological folds
controls/placebos
uncertainty method
coverage/min-N rule
primary kill condition
allowed secondary diagnostics
forbidden rescues
```

## 11. Current registry state

Already prepared:

```text
V6-001A
family B — cross-market / relative state
status = QUEUED / PREREGISTERED CHILD
```

Not yet frozen:

- the outcome-blind order of subsequent families;
- whether V6-001A remains the first empirical child after the registry review;
- exact child contracts for families A/C/D/E/F.

The next task is to finish this parent registry and freeze the first child based on the criteria above before opening any new outcome.
