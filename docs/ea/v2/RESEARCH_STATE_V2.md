# V2 Research State

Last updated: 2026-08-22
Phase: `D-150 V2 CONTINUATION-ONLY FORK`
Target build: `2.00R0L0 / V2_CONTINUATION_ONLY_BOOTSTRAP`
Authority: `docs/ea/v2/AGENTS_V2.md`
2021: `UNTOUCHED`

## Objective

```text
realized WR >= 50%
+
average winner meaningfully > 1R
+
positive cost-adjusted expectancy
+
robustness across periods and markets
```

## Permanent V2 scope decision

Active trading research is continuation-only. `EXTERNAL_REVERSAL` is removed from V2 order authority across all symbols.

## Research axis 1 — Runner identification

Status: **PROMISING / CROSS-MARKET SIGNAL EXISTS**

The strongest generalized state so far is M30 structural maturity / remaining external room at first +1R. GOLD and BTC both support the idea that a structurally room-rich +1R state is more likely to reach +2R.

Open problem: separate 1R-only reactions from 2R+ runners with causal state, without a pooled fitted threshold.

## Research axis 2 — Profit preservation

Status: **UNSOLVED**

SP materially reduces giveback losses, but +2R -> cost-BE can surrender nearly the whole move. The next measurement must characterize post-+2R retracement of eventual +3R / structural-TP winners before adding a positive-R lock.

Do not mechanically copy D147 R-step trailing; it previously destroyed expectancy.

## Research axis 3 — Genuine Entry losses / clusters

Status: **UNSOLVED / EM GENERALIZATION WARNING**

GOLD D148 showed that SL-first failures contain multiple causal classes. BTC confirms that poor Entry survival can dominate even when SP works perfectly after +1R.

EM V2 reduced GOLD DD/streak but BTC shadow outcomes indicate it may remove recovery winners. EM therefore remains experimental and should be tested separately from SP.

## Current development priority

```text
1. continuation-only bootstrap
2. SP-only cross-market control runs
3. post-+2R retracement / profit-lock research
4. Entry-survival failure mechanism research
5. EM redesign only after SP and Entry populations are cleanly separated
```

## D-151 target escalation and measurement phase

The previous `>=50%` objective is superseded for active V2 research by:

```text
Primary stretch target:
realized cost-adjusted WR >= 70%
while avg winner > 1R and expectancy > 0

Extreme frontier:
all accepted trades final aggregate net R >= +1R
```

The current GOLD/BTC evidence is far below the extreme frontier and BTC is below the primary target. D-151 therefore prioritizes causal discrimination over additional discretionary filters.

Current stage questions:

```text
ENTRY: what causally-known Fill state separates +1R survival from original-SL-first?
RUNNER: what +1R state separates local reaction from +2R+ continuation?
PRESERVATION: after +2R, how much retracement do eventual 3R/5R/structural winners truly need?
```

D-151 native audit measures all three without changing a trade.
