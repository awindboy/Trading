# V13 handoff

Last synchronized: `2026-09-26`
Status: `BASELINE 0 FROZEN / EA READY / OFFICIAL MT5 BACKTEST REPORT PENDING`

## Resume point

1. Refresh GitHub `main`.
2. Read `AGENTS_V13.md` and the authority map.
3. Do not modify Baseline 0 before its first official MT5 tester report is
   captured.
4. Compile `mt5/experts/V13HAOnlyMax10EA.mq5`.
5. Run GOLD# on `Every tick based on real ticks` for the full frozen window.
6. Export the raw Strategy Tester report and preserve the Journal.
7. Write a compact V13 Baseline-0 result receipt under `results/`.

## Baseline in one block

```text
standard H4 HA only
same-color run = Journey
one Child after every completed same-color H4 HA
maximum 10 Children
first opposite completed H4 HA = close all
same event then starts opposite Journey
1 fixed unit per Child
no SL / no TP / no filters / no ML
```

## Frozen comparison period

`2024-01-01 through 2026-08-28 available GOLD# history`

No few-month comparison may replace the full-window result.

## Current evidence status

A deterministic H4 next-open Python sanity reconstruction exists and is recorded
in `RESEARCH_STATE_V13.md`. It is not the official economic result because it
does not reproduce Bid/Ask, spread, commission, slippage, or actual-tick order
execution.

The next authoritative evidence is the user's MT5 tester report.
