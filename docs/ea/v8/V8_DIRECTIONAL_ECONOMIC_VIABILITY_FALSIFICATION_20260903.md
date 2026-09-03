# V8 Directional Economic Viability Falsification Result — 2026-09-03

Status: `DEVELOPMENT EVIDENCE / GOLD-INTERNAL DIRECTIONAL FILTER MINING CLOSED`
Production authority: `NONE`
Market: `GOLD#`
Reserve: `GOLD# 2021 UNTOUCHED`
Git HEAD inspected: `0b7dab2b0b61be3deadd2908060e6e8ebb718b28`

## 1. Purpose

The practical movement/economics work showed that the current frequent base architecture can approach the desired
WR/payoff frontier, but economic sign varies materially by year/direction. This phase asked one narrow question:

> Can causal GOLD-internal state tell us whether an already-formed Slow-N ACCEPTANCE direction is economically viable?

Exit parameters were not optimized in this phase.

A broad causal acceptance population was used only as a mechanism-discovery control. Its reconstruction returned
exactly 35,724 ACCEPTANCE events, matching the previously established broad lifecycle parity. This broad population
is not the Slow-N trading population.

Primary economic direction diagnostic:
- entry: next M1 open after acceptance;
- symmetric target/stop: +/-0.25 S;
- stop-first on same-bar ambiguity;
- right-censored events excluded;
- S = previous existing completed H4 Wilder ATR14.

Broad resolved win rate is approximately 50% by year, confirming that ACCEPTANCE direction alone is not a generic
direction edge.

## 2. GOLD-internal formulations tested and falsified

### A. Auction / local-liquidity context

Causal inputs included:
- 15/30/60/240m range, net path, path efficiency and oriented range position;
- recent same-side/opposite-side boundary consumption;
- reveal/acceptance relation to older range boundaries;
- acceptance/reveal geometry and timing.

Train 2022-2024 -> evaluate 2025/2026.

Representative AUC:
- auction logistic: 2025 ~0.501 / 2026 ~0.506;
- auction HGB: ~0.497 / ~0.508;
- geometry logistic: ~0.494 / ~0.504;
- geometry HGB: ~0.504 / ~0.516.

Disposition: `FAIL`.

### B. Slow persistence / mean-reversion regime

Only prior observations were used:
- M5 1/3/5-day efficiency, volatility, volatility-of-volatility, sign persistence, return autocorrelation, variance ratio;
- H4 efficiency, sign persistence, ATR regime.

Future AUC remained approximately 0.49-0.51.

Disposition: `FAIL`.

### C. Reveal purity / commitment

Measured before or at causal reveal:
- maximum adverse close excursion;
- origin-cross count;
- ordering through 0.05/0.10/0.15/0.20 S intermediate rungs;
- clean-rung count;
- reveal path efficiency.

Train 2022-2024 -> 2025/2026:
- logistic ~0.503 / ~0.493;
- HGB ~0.503 / ~0.503.

Disposition: `FAIL`.

### D. Six-hour auction/session state

Used current and prior 6h session move/range/position/elapsed state without future information.

Representative:
- logistic ~0.500 / ~0.526;
- HGB ~0.499 / ~0.515.

The small 2026 uplift is absent in 2025 and is not promotable.

Disposition: `FAIL / NO SESSION RULE`.

### E. Transfer of the older N2-M1 synchronization findings

The older N2 study had real development evidence that M1 confirmed structure could improve the quality of an existing
N2 directional state and that a very local M5/M1/tick re-synchronization sequence could reach ~65-72% directional
accuracy. Those findings were not treated as generic M1 direction.

They were transferred without lookback scanning to the current ACCEPTANCE direction.

Broad +/-0.25S result:
- M1 structure aligned: 2024 49.6%, 2025 49.3%, 2026 50.7%;
- M5 stochastic aligned: 50.2%, 49.3%, 51.6%;
- both aligned: 50.1%, 49.0%, 51.5%;
- pullback-ending re-synchronization: N=57/62/40, WR=43.9%/54.8%/50.0%.

Disposition: `FAIL TRANSFER`.

Interpretation: the old result belonged to the old N2 directional state plus local sequencing; it is not a universal
filter for Slow-N ACCEPTANCE direction.

### F. Transfer of B34 recent-15m signed direction efficiency

Historical B34 was strictly local and had a weak-but-positive exclusive-direction clue:
recent-15m signed efficiency AUC roughly 0.639 / 0.577 / 0.531 in 2024/2025/2026.

Transferred to current acceptance direction:
- at acceptance: 2024 0.505 / 2025 0.500 / 2026 0.498;
- at the original M5 decision: 2024 ~0.500 / 2025 ~0.488 / 2026 ~0.500.

Disposition: `FAIL TRANSFER`.

## 3. Consolidated verdict

The following statement is now strongly supported by repeated independent falsification:

```text
near-term movement intensity / excursion opportunity = learnable
structural survival / damage state                = learnable
large-winner continuation after realized progress = learnable

but

static GOLD-internal ACCEPTANCE direction economic viability
= not robustly learnable from the tested causal price/state families
```

Do not add another endogenous indicator/voter family merely to rescue direction.

The prior good research remains valid because those modules answer different questions:
- Slow-N ONSET: movement episode probability;
- ACCEPTANCE: reveal/pullback/reclaim lifecycle state;
- micro3: initial structural-quality prior;
- dynamic geometry: structural hazard;
- early realized MFE: runner continuation.

None of those should be silently converted into a direction permission score.

## 4. Research decision

Close the current GOLD-internal directional-filter branch.

Next legitimate research is split into two non-overlapping branches:

1. `SOURCE-OF-MOVE`: use the pre-existing broker external panel (USDJPY#, XAUEUR#, BTCUSD#) to test whether
   external causal state adds incremental information about GOLD ACCEPTANCE economic direction.
2. `MARKET-UNIVERSE TRANSFER`: apply the same frozen Slow-N -> ACCEPTANCE -> base/runner lifecycle independently
   to the entire predeclared non-GOLD panel, so frequency/robustness is sought by compatible markets rather than
   by loosening GOLD filters.

Do not use old V5/V6/V7 P/L to select which of the three markets to test.

`GOLD# 2021` remains locked.
