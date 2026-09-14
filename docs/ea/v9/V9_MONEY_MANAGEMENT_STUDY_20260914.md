# V9 Money Management Study

Date: `2026-09-14`
Status: `RESEARCH ONLY / NOT LIVE SIZING AUTHORITY`

## 1. Canonical sizing replay

This document supersedes informal chat estimates with a deterministic replay of the uploaded actual-tick event/trade ledgers.

At each `CHILD_ENTRY`:

1. start from current realized balance;
2. mark existing V9 positions to the current Bid/Ask and compute entry-time equity;
3. calculate one-minimum-lot planned structural loss from **actual executable entry to fixed structural SL**;
4. target `risk_pct * entry_equity`;
5. choose the largest integer number of `0.01 lot` units that does not exceed target risk;
6. if one `0.01 lot` already exceeds the target, still use the minimum `0.01 lot` for the experiment;
7. replay the actual tick trade PnL linearly by volume.

This model does not model size-dependent slippage, liquidity impact, changing commissions, broker margin limits, liquidation, or order rejection from insufficient margin. Results are therefore portfolio-sizing research, not executable promises.

## 2. Full-history 1% target, $1,000 start

```text
start balance       $1,000.00
realized end         $5,876.54
marked end equity    $5,893.01
peak realized        $6,230.75
minimum realized       $686.01
max balance DD          36.77%
median lot               0.01
max lot                  0.05
entries where 0.01 lot already exceeded 1% target: 80.66%
```

Year-end realized balances:

```text
2022   $796.57
2023  $1,305.03
2024  $1,654.96
2025  $3,746.83
2026  $5,876.54
```

Conclusion: with a $1,000 GOLD account, a nominal 1% policy is not really a 1% policy because the broker minimum lot is too coarse relative to V9 structural stops.

## 3. 2025-2026 risk grid, $1,000 start

See `MONEY_MANAGEMENT_2025_2026_RISK_GRID.csv` for the exact grid.

Key points:

```text
1%   -> $5,352.10 / max DD 18.59%
2%   -> $4,782.98 / max DD 19.96%
3%   -> $4,840.58 / max DD 31.40%
4%   -> $5,584.32 / max DD 43.00%
5%   -> $7,453.28 / max DD 53.77%
6%   -> $8,740.01 / max DD 63.48%
7%   -> $15,766.84 / max DD 71.09%
8%   -> $14,924.10 / max DD 76.52%
10%  -> $21,172.22 / max DD 85.47%
```

Final balance is not monotonic with target risk because the path contains overlapping positions and severe drawdowns.

## 4. 10% per Child, 2025-2026

```text
start                 $1,000.00
2025 year-end        $11,725.20
realized end         $21,172.22
marked end equity    $21,852.95
peak realized       $106,529.39
minimum realized        $970.36
max balance DD           85.47%
median lot                0.17
max lot                   2.76
```

At entries with two Children open, combined planned structural risk averaged about `17.47%` of entry-time equity, median `17.68%`, with observed maximum about `20.04%`.

Therefore `10% per Child` is not equivalent to a 10% account-risk strategy. The route can carry roughly 20% planned structural exposure before slippage/gap effects.

## 5. Interpretation

The 2025-2026 10% experiment demonstrates compounding sensitivity to V9's rare large Anchor winners, not a recommended risk setting.

The same leverage that turns a large Anchor winner into explosive account growth also creates catastrophic path dependence. A strategy that reaches >$100k and later loses >85% from peak is not stable capital management merely because it ends above the start.

## 6. Current sizing authority

None.

Keep fixed `0.01 lot` as the strategy-validation baseline until forward-demo execution, margin, restart, and broker-friction evidence are stable. Any future live sizing rule must be frozen separately from the V9 market/entry logic.
