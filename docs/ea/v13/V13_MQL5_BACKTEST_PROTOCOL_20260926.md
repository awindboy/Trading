# V13 MQL5 Backtest Protocol — Baseline 0

Date: `2026-09-26`
Status: `ACTIVE TEST PROTOCOL`
EA: `V13HAOnlyMax10EA.mq5`

## 1. Canonical run

Use MetaTrader 5 Strategy Tester:

```text
Expert: V13HAOnlyMax10EA
Symbol: GOLD#
Chart period: H4
Model: Every tick based on real ticks
Optimization: Off
From: 2024-01-01
To: 2026-08-28
Initial deposit: 10,000 USD
Leverage: 1:100
Visual mode: optional
Account/position mode: HEDGING
```

The chart period is set to H4 for clarity. The EA itself explicitly reads
`PERIOD_H4`.

## 2. Inputs

Frozen baseline strategy input:

```text
InpLotPerChild = 0.01
```

Execution/audit inputs:

```text
InpMagicNumber = 1300260926
InpDeviationPoints = 30
InpVerbose = true
```

Changing lot size rescales money exposure and is not a strategy improvement.
Changing the H4 HA logic or max-10 rule requires a new V13 contract.

## 3. Pre-run checks

The Journal must show successful initialization and must not show:

```text
V13_HALT
non-hedging account rejection
invalid volume rejection
HA initialization failure
pre-existing V13 magic positions
```

If any appears, do not interpret the economic report.

## 4. What to export

Preserve all of the following before changing the EA:

1. Strategy Tester HTML report;
2. tester deal/order history export when convenient;
3. tester Journal covering initialization through completion;
4. EA input settings / `.set` if changed from defaults;
5. broker symbol name, build number, deposit, leverage, commission model, and
   test modeling mode.

Large raw reports should stay outside Git unless explicitly requested. Commit a
compact result receipt under `docs/ea/v13/results/`.

## 5. Required compact metrics

The first official Baseline-0 receipt should at minimum record:

```text
net profit
profit factor
gross profit / gross loss
balance drawdown maximal and relative
equity drawdown maximal and relative
total trades / deals
winning and losing trade counts
average win / average loss
largest win / largest loss
long / short breakdown
2024 / 2025 / 2026 breakdown
maximum simultaneously open V13 positions
```

Also record the tester/broker execution settings because money P/L is broker-
specific.

## 6. Comparison rule

All primary V13 A-vs-B comparisons must rerun both variants on:

`2024-01-01 through 2026-08-28`

Do not promote a variant because it wins on only a few months.

Yearly/monthly/episode slices remain useful for diagnosis after the full result
is known.

## 7. Expected sanity shape, not pass/fail target

The pre-tester idealized H4 reconstruction produced 965 closed Journeys and
3,858 closed Children on the supplied H4 dataset. The MT5 tester need not match
money results because execution is different, but a large unexplained mismatch
in signal/entry counts should trigger a parity audit before strategy research.

Do not tune the EA to force these counts after seeing tester outcomes. First
explain timestamp/history/execution differences causally.
