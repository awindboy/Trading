# V4 Development Handoff

Last updated: `2026-08-27`
Current phase: `V4-001A CAUSAL PATCH REPRESENTATION BASELINE`
V1: `FROZEN CONTROL`
V2: `PAUSED / PRESERVED`
V3: `PAUSED / NEGATIVE + MECHANISM AUTHORITY`
V4 production authority: `NONE`

## Why V4 exists

V3 reached an L3 research conclusion rather than a missing-threshold conclusion.
The frozen Candidate B passed its 2023-2025 discovery target but failed GOLD# 2022 independent validation:

```text
24 accepted
positive 25.0%
avg positive +1.458R
EV -0.385R/trade
```

Subsequent development-only cross-market diagnostics on the V2 outcome-blind GOLD-like primary panel also
showed that Candidate-A polarity and H/L rules do not transfer cleanly to BTCUSD#, XAUEUR# and USDJPY#.
Simple additional chart-state rules, delayed-confirmation routing and generic compression/trend controls did
not establish a stable direction edge.

V4 therefore changes the abstraction level:

```text
human-defined state -> rule
```

to:

```text
causal sequence -> learned latent state -> falsifiable information test -> policy
```

This does not declare technical analysis impossible. It stops assuming that the human labels used in V1-V3
are the optimal representation for machine decision making.

## Active development allocation

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

Current uploaded-development identity is recorded in `V4_001_DATA_MANIFEST.json`.

Validation vault remains unopened for V4:

```text
XAUJPY#
XAUCNH#
GAUCNH#
GAUUSD#
2023-2025
```

Final temporal confirmation remains:

```text
GOLD# 2021 — untouched
```

## First base model

Name:

```text
V4_001_CausalPatchPolicy
```

Architecture:

```text
completed causal bars
    M1 / M5 / M30 / H4
    across target + available context markets
-> shared per-market patch encoders
-> cross-market/timeframe fusion Transformer
-> latent state z_t
-> 15m / 60m / 240m distributional return heads
-> Stage-A OOS skill diagnostics
```

Only after Stage A passes:

```text
predicted 15m expected return
+ current position
+ recorded spread cost
-> LONG / FLAT / SHORT one-step predictive controller
```

The initial controller is deliberately not RL. At our research scale, the historical price path is exogenous,
so full-information action rewards are available and a simple predictive controller is a cleaner baseline.

## Immediate task order

1. apply the V4 bootstrap pack and commit the authority change;
2. create a local V4 Python environment with PyTorch;
3. build the prepared causal dataset from the four development markets;
4. run data-parity/smoke tests;
5. train simple linear/raw baselines;
6. train `V4_001_CausalPatchPolicy` Stage A with fixed config;
7. run walk-forward and leave-one-market-out diagnostics;
8. decide PASS / FAIL / REDESIGN-IN-DEVELOPMENT under the frozen contract;
9. do **not** open the external-market validation vault yet.

## Hard stop rules

- Do not open XAUJPY/XAUCNH/GAUCNH/GAUUSD because training looks promising.
- Do not inspect GOLD 2021.
- Do not use GOLD 2022 as a pristine V4 validation set.
- Do not start PPO/SAC because the supervised representation is weak.
- Do not add RSI/MACD/ICT labels merely because training stagnates.
- Do not select a model from one lucky seed.
- Do not modify an MT5 EA from V4-001 development results.
