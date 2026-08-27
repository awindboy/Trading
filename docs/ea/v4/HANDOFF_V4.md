# V4 Development Handoff

Last updated: `2026-08-27`
Current phase: `PAUSED / PRESERVED — V5 SUCCESS-FIRST ACTIVE`
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

1. apply and commit the Representation Tournament pack;
2. verify CUDA-enabled PyTorch locally;
3. prepare/reproduce the four-market causal store;
4. run R1 and R2 through `tools/run_claim_grade_tournament.ps1`;
5. upload R1/R2 lightweight result bundles plus `V4_001_TOURNAMENT_SUMMARY.json`;
6. keep R3/R4 diagnostic-only;
7. open V4-001B only after a claim-grade PASS and a new freeze decision.

## Hard stop rules

- Do not open XAUJPY/XAUCNH/GAUCNH/GAUUSD because training looks promising.
- Do not inspect GOLD 2021.
- Do not use GOLD 2022 as a pristine V4 validation set.
- Do not start PPO/SAC because the supervised representation is weak.
- Do not add RSI/MACD/ICT labels merely because training stagnates.
- Do not select a model from one lucky seed.
- Do not modify an MT5 EA from V4-001 development results.

## V4-001 Representation Tournament update — 2026-08-27

The first V4 task is no longer a single supervised-Transformer bet.

Claim-grade comparison:

```text
R0 frozen linear
R1 supervised CausalPatchPolicy
R2 self-supervised MarketJEPA -> frozen linear probe
```

Both R1/R2 use the same 2023/2024 temporal and strict future-isolated 2025 LOMO rules. R2 self-supervised pretraining is confined to the training allocation; a held-out LOMO market is excluded from R2 pretraining context as well as labels.

Current external transfer diagnostics:

```text
R3 Kronos-mini zero-shot K-line forecast
R4 MOMENT-1-small frozen embedding probe
```

These are not pristine OOS evidence and cannot promote a candidate by themselves.

Next concrete action:
1. verify CUDA-enabled PyTorch locally;
2. prepare/reproduce the frozen four-market causal store if needed;
3. run R1 and R2 official 3-seed Stage-A through `tools/run_claim_grade_tournament.ps1`;
4. upload both lightweight result bundles plus `V4_001_TOURNAMENT_SUMMARY.json`;
5. run R3/R4 only as optional transfer diagnostics, never as rescue gates.


## V5 routing — 2026-08-27
The R1/R2 CUDA tournament remains frozen and reproducible but is no longer the immediate task.
Active research moved to `docs/ea/v5/` to test whether successful-trader market concepts can produce a better
semantic problem formulation than generic next-return prediction.
