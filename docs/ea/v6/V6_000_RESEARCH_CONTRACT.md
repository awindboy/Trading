# V6-000 — Event-Conditioned Generalization Research Contract

Status: `FROZEN STARTUP CONTRACT`
Date: `2026-08-28`
Production authority: `NONE`
Primary market: `GOLD#`

## 1. Research thesis

V6 does not assume that V3 failed because one more chart filter was missing.
It also does not assume that V4 failed because the neural network was not large enough.

The working thesis is:

> A meaningful GOLD event may require a richer latent market context to determine whether it represents true directional delivery, temporary reaction, giveback, or stop-sensitive recovery. The relevant context may be distributed across timescales and related markets, and its meaning may drift over time.

This thesis is falsifiable.

If no stable information can be extracted under strict chronology and controls, V6 must accept that the chosen event formulation may not contain enough predictive information.

## 2. Initial research object

Use exact V3-003C BROAD CONTROL as an event anchor, not as a strategy authority.

Why:
- it is broad enough to avoid baking Candidate-A discovery filters into sample selection;
- it is causal;
- it has near-balanced +1R survival across 2023-2025;
- it provides a meaningful event-conditioned population, unlike V4 generic all-time return prediction.

Expected pre-context parity:

```text
2023 84
2024 86
2025 67
```

Any mismatch must be resolved before model outcomes are inspected.

## 3. Outcome hierarchy

Do not force all research into one binary label.

### Stage-A Entry survival

```text
+1R before original structural SL
vs
SL before +1R
```

This remains useful as a diagnostic but late-V5 evidence showed it mixes different path types.

### Stage-B symmetric path taxonomy

After the first +/-1R boundary:

```text
W_CONTINUE: +1 -> +2 before 0
W_GIVEBACK: +1 -> 0 before +2
L_RECOVER:  -1 -> 0 before -2
L_CONTINUE: -1 -> -2 before 0
```

Known V5 scratch counts:

```text
                 2023  2024  2025  total
W_CONTINUE         22    20    18    60
W_GIVEBACK         21    26    17    64
L_RECOVER          22    18    19    59
L_CONTINUE         19    22    13    54
```

Ambiguous same-M1 ordering must be excluded or separately classified, never guessed.
Right censoring must remain censoring.

### Stage-C survival / competing-risk modeling

Only after stable information is established may V6 model time-to-first-hit / competing events directly.
Do not start here merely because the method is modern.

## 4. Representation policy

V6 may use:
- normalized raw OHLC path;
- range/body/wick geometry;
- tick-volume/activity proxy with correct semantics;
- spread / execution state;
- cross-market synchronized raw state;
- learned self-supervised embeddings, if Stage-0 information supports escalation.

V6 must not silently reintroduce V3 filters as model channels and then claim the model rediscovered them.

## 5. Environment policy

Environment stability is part of the objective, not a post-hoc chart.

Minimum environments:

```text
2024 evaluation
2025 evaluation
LONG / SHORT diagnostics
calendar-time blocks
```

Later:
- GOLD 2022 consumed falsifier;
- independent structurally compatible markets;
- execution environment changes separately.

## 6. What counts as progress

Progress is NOT:
- higher pooled AUC after selecting a timeframe;
- one strong year;
- one lucky seed;
- a more complex network;
- a visually separated embedding;
- post-hoc threshold discovery.

Progress is:

```text
same formulation
-> same direction of information gain
-> across chronological environments
-> beyond strong matched controls
-> with uncertainty compatible with real signal
```

## 7. Current unresolved hypothesis

Late V5 cross-market scratch suggested synchronized `XAUEUR# + USDJPY#` context improved robust path-endpoint discrimination in both chronological evaluation years.

Recovered scratch values:

```text
                         GOLD only   +XAUEUR+USDJPY
2024 extreme AUC           0.486          0.514
2025 extreme AUC           0.645          0.709
2024 ordinal rho          -0.034         +0.030
2025 ordinal rho          +0.084         +0.191
```

However actual context had ~30 channels versus ~10 for GOLD-only.

Therefore this is NOT yet evidence of cross-market information.
The first V6 task is a same-capacity falsifier.

## 8. Adaptation lock

No test-time adaptation, online updating, rolling refit, meta-learning, or regime-conditioned routing may be introduced before V6-001A is classified.

If V6-001A supports genuine context information but 2024 remains weak, a later preregistered stage may test whether context is insufficient or whether causal adaptation is necessary.
