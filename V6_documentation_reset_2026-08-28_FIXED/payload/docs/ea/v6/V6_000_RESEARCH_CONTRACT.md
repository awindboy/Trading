# V6-000 — Context-Measurement Generalization Research Contract

Status: `FROZEN GENERATION CONTRACT — CORRECTED`  
Date: `2026-08-28`  
Production authority: `NONE`  
Primary market: `GOLD#`

## 1. Research thesis

V6 does not assume V3 failed because one more chart filter was missing.

V6 also does not assume V3 failed because hidden context is definitely the answer.

The scientific problem is:

> A causally meaningful GOLD event can show different outcome meaning across periods. V6 must distinguish selection/multiplicity, covariate shift, omitted context, concept shift, event-formulation insufficiency, and execution effects by using preregistered causal measurements and matched controls.

A richer context may help. That claim must be falsified family by family.

## 2. Initial research object

Use exact V3-003C `BROAD CONTROL` as the initial event anchor, not as strategy authority.

Why:

- broad enough to avoid baking Candidate-A discovery filters into selection;
- causal;
- near-balanced +1R survival across 2023-2025;
- meaningful event semantics unlike generic all-time next-return prediction.

Expected parity:

```text
2023 84
2024 86
2025 67
```

Any mismatch must be resolved before child outcomes are inspected.

## 3. Competing failure hypotheses

V6 begins with no single promoted explanation.

### H1 — selection / multiplicity

V3's final relationship may have been selected from too many development hypotheses.

### H2 — covariate shift

```text
P(X) changes
```

The frequency/distribution of observed market state changes.

### H3 — hidden / omitted context

Relevant state is missing from X.

### H4 — concept shift

```text
P(Y|X) changes
```

Similar observed state has different outcome meaning.

### H5 — event-formulation insufficiency

The current broad event may mix different causal event classes.

### H6 — execution environment

Execution/cost changes may affect realized economics, but this cannot be used as a blanket explanation for V3's 2022 direction/mirror reversal.

Every major V6 interpretation must say which hypothesis it supports, weakens, or leaves unresolved.

## 4. Outcome hierarchy

Do not force all research into one label.

### Stage A — Entry survival

```text
+1R before original structural SL
vs
SL before +1R
```

Use for event/directional survival questions.

### Stage B — symmetric path taxonomy

After the first +/-1R boundary:

```text
W_CONTINUE: +1 -> +2 before 0
W_GIVEBACK: +1 -> 0 before +2
L_RECOVER:  -1 -> 0 before -2
L_CONTINUE: -1 -> -2 before 0
```

Known late-V5 scratch counts:

```text
                 2023  2024  2025  total
W_CONTINUE         22    20    18    60
W_GIVEBACK         21    26    17    64
L_RECOVER          22    18    19    59
L_CONTINUE         19    22    13    54
```

Ambiguous same-M1 ordering must be excluded or separately classified. Right censoring remains censoring.

### Stage C — survival / competing-risk modeling

Only after stable information exists may V6 model time-to-event directly.

### Stage D — strategy economics

Only after stage-specific information is stable may a trading policy be defined and tested.

## 5. Indicator/context family contract

Before an indicator family becomes an active child, preregister:

1. `STATE HYPOTHESIS`
   - what latent market condition is being measured?

2. `V3 FAILURE LINK`
   - direction premise failure?
   - delivery weakness?
   - stop-sensitive recovery?
   - winner exhaustion?
   - execution degradation?

3. `MEASUREMENT`
   - exact source;
   - exact formula/transform;
   - update frequency;
   - causal availability;
   - missing/stale handling.

4. `TARGET STAGE`
   - Entry survival, continuation, execution, etc.

5. `CONTROLS`
   - simple/null baseline;
   - same-capacity control when model dimensionality changes;
   - stale/time-shift/mirror controls when appropriate.

6. `ENVIRONMENTS`
   - chronological folds;
   - year/direction/time-block diagnostics.

7. `UNCERTAINTY`
   - preregistered resampling/interval method appropriate to time clustering.

8. `KILL CONDITION`
   - result that closes the formulation without a threshold rescue.

9. `FOLLOW-UP BUDGET`
   - what is allowed if the primary result passes;
   - what is prohibited if it fails.

## 6. Context families

Parent registry may include:

```text
A. own-market endogenous state
B. cross-market / relative state
C. macro / rates state
D. positioning / fund-flow state
E. execution / liquidity environment
F. scheduled-event / market-environment state
```

This list is a semantic registry, not permission to screen all available variables.

## 7. Representation policy

V6 may use:

- normalized raw OHLC path;
- range/body/wick geometry;
- volatility/trend/activity transforms;
- tick-volume/activity proxy with correct semantics;
- spread/execution state;
- synchronized cross-market state;
- source-qualified macro/positioning/flow state;
- learned representations only after information-stage justification.

V6 must not silently reintroduce V3 selection gates as model channels and claim rediscovery.

## 8. Chronological discipline

Initial chronological research folds:

```text
F1 train 2023       -> evaluate 2024
F2 train 2023-2024  -> evaluate 2025
```

No random CV as claim-grade evidence for stability.

Do not select a best year, timeframe, model, threshold, transformation, or context composition from these outcomes.

## 9. Multiplicity discipline

V3 selection risk is itself a V6 design constraint.

Therefore:

- test hypotheses by semantic family, not by indicator leaderboard;
- freeze a small transformation set before outcomes;
- do not search thresholds after a weak result;
- record consumed hypotheses;
- a new family must be substantively different and preregistered before its outcome is opened.

## 10. Recursive falsification

The V5 recursive falsification discipline is inherited and made permanent.

Before interpretation:

```text
current thesis
opposite thesis
simpler alternative
prior-project recurrence
placebo/control
causal boundary
geometry/economics
kill condition
```

A result cannot be called supported only because pooled AUC/WR improves.

## 11. V6-001A status

Late V5 cross-market scratch:

```text
                         GOLD only   +XAUEUR+USDJPY
2024 extreme AUC           0.486          0.514
2025 extreme AUC           0.645          0.709
2024 ordinal rho          -0.034         +0.030
2025 ordinal rho          +0.084         +0.191
```

This is consumed hypothesis-generation evidence, not claim-grade proof.

`V6-001A` remains a valid preregistered child to distinguish real cross-market information from a same-capacity artifact.

However:

```text
V6-001A pass != V6 strategy pass
V6-001A fail != all context/indicator hypotheses fail
```

Its classification applies only to the stated XAUEUR/USDJPY formulation.

## 12. Adaptation lock

No test-time adaptation, online updating, rolling refit, meta-learning, or regime-conditioned routing may be used to rescue a weak static measurement result.

Adaptation becomes eligible only after a preregistered stage shows:

- useful causal information exists; and
- remaining instability is consistent with concept drift rather than simply no signal.

## 13. Final economic boundary

The eventual strategy target remains:

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2.0R
cost-adjusted expectancy     > 0
```

Information evidence is not strategy authority.
