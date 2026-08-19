# EA Development Handoff

Last updated: 2026-08-19
Repository base checked before this research update: `02781412d125e4990c8f4ad6e45d15bbce48f7c4`
Status: D-135A BUILD 1.91 EXECUTION BASELINE VALIDATED / VISUAL AUDIT COMPLETED / REGIME FEATURE DISCOVERY ACTIVE
Current phase: strategy robustness research — persistence / structural stability / regime representation
Remaining execution issue: recoverable broker pending-cancel rejection retry

## Authority

- `AGENTS.md` is the highest strategy authority.
- `docs/ea/EA_SPEC.md` defines the deterministic implementation contract.
- `docs/ea/DECISIONS.md` preserves design decisions.
- `docs/ea/REGIME_RESEARCH_2023_2025.md` is the current regime-discovery evidence ledger.
- `docs/ea/STRATEGY_RESEARCH_STATE.md` is the current research-state summary.
- Research attribution does **not** modify strategy authority.

## Current baseline

Preserve build 1.91 as the control:

```text
H1/M30 map
→ eligible HTF Root OB
→ Root contact
→ direction-compatible M1 liquidity Sweep
→ later M1 protected-break CHoCH
→ causal fresh M1 FVG
→ widest eligible FVG
→ first retest Entry
→ contributor-merged SL/objective geometry
→ hedging same-direction execution
→ pending/fill/cancel/close reconciliation
```

Current baseline properties:

- primary validation SL = `ROOT_OB_DISTAL_20`
- FVG-origin OB + last-opposite OB are both baseline Root recognizers
- PD Array = context/reference only
- same-direction independent positions allowed on hedging accounts
- opposite-direction coexistence blocked

Do not alter this chain from development-set regime attribution alone.

## Long-run execution status

2025 D-135A full-year real-tick lifecycle parity passed with zero execution divergence:

```text
execution geometry = 74
pending accepted = 73
pending canceled = 15
filled = 58
closed = 58
execution divergence = 0
runtime ≈ 7m10s
```

A separate 2023–2024 run exposed one recoverable cancel-reject edge case (`retcode 10018 / Market closed`) that can leave a strategy-canceled pending order live. Retry-by-exact-ticket remains required before final multi-year profitability validation.

## Research protocol now frozen

```text
2023–2025 = Development / Research set
2022      = SEALED first OOS
2021      = preferred final untouched confirmation
```

Do not open 2022 until an exact regime definition has been frozen. If 2022 causes a model change, it is no longer OOS.

## TradingView visual-audit status

The TradingView visual-audit work has been completed for the current research purpose. It remains an audit aid, not strategy authority or MT5 parity proof.

The main conceptual problem observed and now supported statistically is:

```text
H1/M30 BULLISH or BEARISH
!=
automatically tradable continuation regime
```

## Primary regime discovery

Current strongest three-year development candidate:

`M30_CLEAN_PERSISTENT`

```text
EXTERNAL_CONTINUATION
latest 12 confirmed M30 waves
same-side directional progression >= 2/3
M30 PROTECTED_BREAK in same 12-wave span <= 1
```

Previously recorded 2023–2025 attribution:

```text
36 trades / 15 wins / 41.7%
+55.32R
Max DD ≈ -6R
longest losing streak = 6

2023 +46.93R
2024  +2.82R
2025  +5.58R
```

Research status: **PROMISING / NOT STRATEGY AUTHORITY / NOT OOS-VALIDATED**.

## New full feature pass

The current 2023–2024 raw ledger was revalidated by SHA and the baseline clean outcomes were exactly reproduced. New features were snapshotted at scenario `PLAN` freeze with no look-ahead.

Completed axes:

```text
Persistence
Protected-break churn
Progression magnitude
Expansion/compression
Structure cleanliness/overlap
Trend maturity
H1/M30 agreement
Structural location
```

### Strongest new observations

1. **Very weak progression is strongly adverse**

```text
progression <= 0.50
44 trades / -27.80R
2023 -4.29R
2024 -23.51R
0 positive quarters / 8
```

2. **Progression magnitude is highly promising**

`directional_advance_norm` = median same-side advance in trade direction / median M30 swing-leg size.

Illustrative `> 1/3` split:

```text
27 trades / +35.78R
Max DD -4.74R
longest losing streak 4
2023 +31.66R
2024 +4.12R
```

Both LONG and SHORT are positive in each available year, but this feature is strongly correlated with progression (`rho ≈ 0.84`). Treat it as a possible persistence replacement/refinement, not a new stacked filter.

3. **Expansion adds only conditional evidence**

`M30_CLEAN_PERSISTENT + median directional impulse > median retracement`:

```text
26 trades / +38.94R
2023 +36.25R
2024 +2.69R
Max DD -6.17R
```

Promising but not yet 2025-validated.

### Axes not supported as standalone filters

```text
explicit overlap/cleanliness threshold
trend maturity cutoff
H1/M30 agreement veto
structural/PD location veto
generic expansion threshold
```

Do not construct a quality score from these.

## Important remaining limitation

The raw 2025 ledger used in the previous audit was not available during this new feature pass. Therefore R-004 through R-009 are currently re-derived only on raw 2023–2024 data.

The already-recorded three-year `M30_CLEAN_PERSISTENT` result remains valid as prior discovery evidence, but the new `directional_advance_norm` and expansion representations must be re-run on raw 2025 before freezing Regime Research V1.

## Immediate next actions

1. Obtain/re-run the exact raw 2025 build-1.91 ledger.
2. Apply the already-frozen PLAN-time feature formulas without changing thresholds from the 2023–2024 result.
3. Reject any new feature whose relationship materially reverses in 2025.
4. Compare binary progression and magnitude-aware `directional_advance_norm` as alternative persistence representations.
5. Keep only genuinely non-redundant information; target 2–4 axes maximum.
6. Freeze Regime Research V1 completely.
7. Only then open 2022 OOS.
8. Separately fix the recoverable pending-cancel retry edge case before final profitability validation.

## Do not do

- Do not tune 2023–2025 until the curve looks pretty.
- Do not stack every favorable subset.
- Do not add EMA/ADX/RSI or a generic quality score.
- Do not treat `UNKNOWN` as automatically BAD.
- Do not open 2022 early.
- Do not modify baseline EA semantics from observational attribution alone.

## Working principle

> The current question is no longer whether the EA can label direction. It is whether the labeled structure is progressing strongly and stably enough for the existing continuation setup to have repeatable expectancy.
