# D-135A Long-Run Validation and 2023-2025 Research Evidence

Date recorded: 2026-08-19
Repository base checked: `4798a0607f11946b7914ed7f804b193f03785711`

This is a focused supplement to `docs/ea/TEST_RESULTS.md`.
It supersedes the earlier "D-135A prepared / validation pending" status for the specific long-run results recorded below.

## 1. D-135A 2025 full-year regression

EA identity:

```text
build = 1.91
phase = D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX
SL model = ROOT_OB_DISTAL_20
model = Every tick based on real ticks
period = 2025-01-01 ~ 2025-12-31
```

Uploaded D-135A event CSV:

```text
rows = 234,277
SHA-256 = 1bd119c4d3aea9ab759a24541de71be01d0379fa948927bede2a1dae5b9d7b65
user-reported runtime ≈ 7 minutes 10 seconds
```

D-134 lifecycle parity target:

```text
execution geometry ready = 74
pending accepted = 73
pending canceled = 15
filled = 58
closed = 58
opposite-direction conflict = 1
execution divergence = 0
```

D-135A result:

```text
execution geometry ready = 74
pending accepted = 73
pending canceled = 15
filled = 58
closed = 58
opposite-direction conflict = 1
execution divergence = 0
```

Primary June regression fixture passed:
- the LONG pending around Entry `3388.90` was canceled after Root invalidation;
- the later SHORT around Entry `3397.25` was no longer falsely blocked by the orphan LONG pending.

Secondary November canceled-pending fixture around Entry `4138.03` also received normal broker cancellation.

Canonical Entry/FVG/SL/TP/fill/close economics matched the D-134 baseline. Simultaneous same-direction order ticket numbering could differ because working-set traversal order is not strategy priority.

Classification:

```text
D-135 performance optimization = PASS
D-135A canceled-pending lifecycle hotfix = PASS
2025 D-134 execution lifecycle parity = PASS
2025 execution divergence = 0
```

Performance:

```text
D-134 ≈ 9 hours
D-135A ≈ 7m10s
speedup ≈ 75x
```

## 2. D-135A 2023-2024 two-year run

Uploaded event ledger:

```text
period = 2023-01-01 ~ 2024-12-31
build = 1.91
phase = D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX
rows = 442,722
SHA-256 = 16be6cc44e57dadd9e32250d3e8df9cd1de4e14575a55c0732bc3427a237744e
```

Execution funnel:

```text
execution geometry = 159
pending accepted = 148
filled = 130
closed = 126
normal pending cancel = 17
pending cancel reject = 1
tester-end open positions = 4
tester-end live pending = 1
```

Because the run contains one execution divergence and unfinished tester-end exposure, it is **not a clean final profitability baseline**.

## 3. 2023 versus 2024 preliminary strategy result

Closed-trade research summary:

```text
2023
closed trades = 70
wins = 23
losses = 47
win rate ≈ 32.9%
realized ≈ +44.94R

2024
closed trades = 56
wins = 5
losses = 51
win rate ≈ 8.9%
realized ≈ -36.56R
```

The 2024 figure includes the contaminated run context described above and therefore must not be treated as final broker-clean performance.

However, the broad weakness remains after excluding the single known divergence trade and cannot be explained by that execution bug alone.

By scenario scope:

```text
2023 EXTERNAL_CONTINUATION ≈ +48.31R
2023 EXTERNAL_REVERSAL     ≈  -3.37R

2024 EXTERNAL_CONTINUATION ≈ -29.46R
2024 EXTERNAL_REVERSAL     ≈  -7.10R
```

Research implication:

```text
reversal weakness is real evidence,
but reversal removal alone cannot explain or repair 2024.
```

## 4. Remaining execution edge case discovered

Observed scenario:

```text
2023-12-20
LONG pending accepted
Entry = 2029.55
SL = 2026.35
TP = 2047.77

2023-12-22
strategy cancellation required
broker cancellation rejected
retcode = 10018
comment = Market closed

build 1.91 did not retry the pending cancellation

2024-01-05
the strategy-canceled pending later filled
→ FILLED_AFTER_STRATEGY_CANCELLATION
→ EXECUTION_DIVERGENCE
```

The unresolved pending also activated execution protection and blocked later opportunities while broker state remained unsafe.

Required implementation behavior:

```text
strategy cancellation remains required
+ exact pending still live
+ cancellation rejected for recoverable broker condition

→ remain in managed execution working set
→ keep exposure/divergence lock
→ retry exact-ticket cancellation later
→ terminalize only after cancel or fill proof
```

This is an execution-safety problem, not a strategy-regime explanation.

## 5. Cross-year strategy evidence

Combining the clean portions of 2023-2025 analysis showed approximately:

```text
clean closed trades ≈ 183
aggregate ≈ +18.1R
positive months = 13 / 36
monthly R median ≈ -1.65R
longest losing streak = 22 trades
top 10 winners ≈ 54% of positive R
```

This describes a low-win-rate, tail-dependent equity curve with substantial regime instability.

The desired research objective is therefore not simply higher total R.

Future comparisons should emphasize:

```text
annual consistency
rolling 3/6-month expectancy
max R drawdown
losing streak
trade frequency
direction/scope consistency
large-winner concentration
```

## 6. Current interpretation

Implementation correctness and strategy quality must remain separate.

The pipeline can be causal and execution-correct while still receiving poor semantic inputs.

Current strategic research questions:

```text
Does structure identify meaningful market structure?
Does liquidity identify meaningful unresolved liquidity?
Does Root OB identify a meaningful causal source?
Does H1/M30 directional authorization represent an actual tradable regime?
Do Sweep and CHoCH confirm real order-flow change or merely satisfy mechanical definitions?
```

The next research phase is a visual semantic audit followed by cross-year causal measurement.

See:
`docs/ea/STRATEGY_RESEARCH_STATE.md`
