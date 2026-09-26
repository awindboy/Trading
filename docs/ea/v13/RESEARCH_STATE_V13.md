# V13 research state

Last synchronized: `2026-09-26`
Status: `BASELINE 0 FROZEN / PRE-TESTER SANITY LEDGER COMPLETE / OFFICIAL TESTER RESULT PENDING`
Market: `GOLD# ONLY`

## 1. Generation reset

V13 starts from a fresh minimal strategy rather than extending V12.

The active strategy has exactly one information source: completed standard H4
Heikin-Ashi color.

V12 CRT, liquidity, Wave, multi-speed HA, ML, session/event, and lower-timeframe
feature work remains historical evidence. None is present in Baseline 0.

## 2. Frozen strategy skeleton

```text
completed H4 standard HA
-> same-color Journey
-> one Child per completed same-color bar
-> cap at 10 successful Children
-> first opposite completed HA closes all
-> reverse into new Journey
```

No SL or TP exists in Baseline 0.

## 3. Frozen comparison window

Current full-window comparison authority:

`2024-01-01 through 2026-08-28 available data`

All strategy-performance comparisons must use the full window. Year or month
subsets are diagnostic slices only.

## 4. Preliminary H4 next-open sanity reconstruction

Before the EA was written, a deterministic standard-H4 reconstruction was run
with idealized next-H4-open fills, no transaction costs, and the same max-10
Journey rules.

Closed full-window counts / gross price-point diagnostics:

```text
closed Journeys: 965
closed Children: 3,858
gross net points: +8,147.11
Journey PF: 1.2597
Child PF: 1.2000
Journey realized DD (sequential gross points): 3,659.45
Child realized DD (sequential gross points): 3,756.99
```

Year diagnostics from that approximation:

```text
2024 Child gross points:  -378.64 / PF 0.9558
2025 Child gross points: +4,583.83 / PF 1.3540
2026 Child gross points: +3,941.92 / PF 1.2051
```

These are **sanity numbers only**. They are not official V13 economics and must
not be used as the final baseline because they omit broker execution effects.

## 5. What remains unknown

Until the MT5 tester report exists, V13 does not yet know:

- actual net profit after spread/commission;
- actual Strategy Tester PF and drawdown;
- whether every intended H4 boundary order fills cleanly;
- actual long/short deal statistics under Bid/Ask execution;
- exact tester position/deal counts;
- whether broker H4 history/timestamps produce material parity differences from
  the supplied H4 CSV sanity reconstruction.

## 6. Next evidence gate

No new strategy layer should be researched before the baseline EA is compiled
and the full-window actual-tick report is frozen.

After that receipt, the first research question remains:

> Where does pure HA participation lose money, and which single intervention can
> remove a meaningful part of that damage without destroying the right tail?
