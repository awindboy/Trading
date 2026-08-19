# Strategy Robustness Research State

Last updated: 2026-08-19
Status: ACTIVE — REGIME FEATURE DISCOVERY
Baseline: Mentor deterministic V1 / build 1.91
Strategy authority: unchanged; `AGENTS.md` remains highest authority

## Current phase

The deterministic execution pipeline is substantially complete. TradingView visual-audit work has been completed for the current research purpose, and the project has moved from broad semantic inspection into **causal regime-feature discovery**.

The current problem is not parameter optimization. The question is:

> Under which causally observable market states does the existing continuation setup retain positive expectancy?

Read the durable feature ledger next:

`docs/ea/REGIME_RESEARCH_2023_2025.md`

## Development / OOS protocol

```text
2023–2025 = Development / Research
2022      = SEALED first OOS
2021      = preferred final untouched confirmation
```

Do not inspect 2022 before the exact regime definition is frozen. If a model is changed after viewing 2022, 2022 loses OOS status.

## Baseline long-run problem

Clean attribution previously established:

```text
2023: +44.94R
2024: -35.56R
2025:  +8.68R
```

The baseline is low-win-rate and tail-dependent. 2024 weakness is broad and is not explained by the known execution divergence or by simply disabling reversal.

Therefore implementation correctness and strategy quality remain separate research questions.

## First strong regime discovery

The first meaningful three-year candidate is:

`M30_CLEAN_PERSISTENT`

```text
scope = EXTERNAL_CONTINUATION
latest 12 confirmed M30 waves
progression >= 2/3
M30 PROTECTED_BREAK inside same 12-wave span <= 1
```

Previously recorded Development-Set result:

```text
36 trades / 15 wins / 41.7%
+55.32R
mean +1.54R/trade
Max DD ≈ -6R
longest losing streak = 6

2023 +46.93R
2024  +2.82R
2025  +5.58R
```

This is **research evidence only**, not a baseline strategy rule.

The complement is deliberately called `UNKNOWN`, not BAD.

## Current strict snapshot contract

All new feature research uses scenario `PLAN` freeze as the snapshot epoch.

Only objects already available by `plan_frozen_at` may enter the feature state. No contact, Sweep, CHoCH, Entry, fill, or later outcome may define the regime snapshot.

A strict 2023–2024 reconstruction of `M30_CLEAN_PERSISTENT` remains positive:

```text
31 trades / +47.90R
2023 +47.22R
2024 +0.69R
```

It is not yet uniformly positive by direction and remains dependent on a small number of large winners, so it is not frozen for OOS yet.

## Feature pass completed

The following axes have now been analyzed from the raw 2023–2024 ledger:

```text
Persistence
Structural churn
Progression magnitude
Expansion / compression
Structure cleanliness / overlap
Trend maturity
H1/M30 agreement
Structural location
```

### Retained

1. **Persistence** — strongest primary axis.
2. **Structural stability** — repeated protected breaks are adverse, especially together with weak progression.
3. **Progression magnitude** — `directional_advance_norm` is highly promising, but strongly correlated with progression and should be studied as an alternative representation rather than stacked.
4. **Impulse vs retracement** — secondary expansion candidate only; needs raw-2025 recheck.

### Not supported as standalone rules

```text
explicit overlap threshold
trend maturity cutoff
H1/M30 agreement veto
structural/PD location veto
generic expansion threshold
multi-factor quality score
```

## Strong BAD-regime candidate

Under the strict PLAN-freeze reconstruction:

```text
M30 progression <= 0.50
44 trades / 6 wins
-27.80R
2023 -4.29R
2024 -23.51R
positive quarters = 0 / 8
```

This is stronger BAD-state evidence than a generic Bull/Bear/Range label. It is still research evidence, not an authorized veto.

## Strong new alternate persistence representation

`directional_advance_norm` measures the median signed same-side M30 advance relative to typical M30 swing-leg size.

A broad threshold sensitivity band remains positive in 2023 and 2024 rather than depending on a single knife-edge cutoff. For example `> 1/3` gives:

```text
27 trades / +35.78R
Max DD = -4.74R
longest losing streak = 4
2023 +31.66R
2024  +4.12R
```

Both LONG and SHORT are positive in each available year at this illustrative split.

However correlation with the original progression score is about `0.84`; it is not an independent new axis.

## Multiple-testing discipline

All tried representations, including failures, are recorded in `REGIME_RESEARCH_2023_2025.md`.

Do not optimize the 2023–2025 equity curve by stacking every favorable subset. Several attractive combinations collapse trade count too far and are explicitly classified as overfit warnings.

## 2025 limitation and next step

The exact raw 2025 ledger used by the prior audit was not available in the current runtime. Therefore the new feature formulas beyond the already-recorded `M30_CLEAN_PERSISTENT` discovery must be re-derived on 2025 before any Regime Research V1 freeze.

Immediate research sequence:

1. re-run the frozen PLAN-time feature formulas on raw 2025;
2. reject features that materially reverse sign;
3. compare `progression` versus `directional_advance_norm` as alternative persistence representations;
4. decide whether `impulse_retrace_ratio` adds genuinely independent information;
5. freeze the smallest defensible regime model;
6. only then open 2022 OOS.

## Parallel execution-safety item

Build 1.91 still has one separate recoverable pending-cancel rejection retry edge case. It must be closed before a multi-year run is called a final profitability baseline, but it does not explain the regime instability and does not block observational regime research.

## Working principle

```text
Direction describes where structure points.
Regime research asks whether that structure is actually progressing and stable enough to trade.
```

Preserve the deterministic baseline as control until OOS evidence justifies a strategy change.
