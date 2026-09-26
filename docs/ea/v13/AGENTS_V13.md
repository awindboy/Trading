# V13 Research Instructions — Minimal HA Rebuild

Last synchronized: `2026-09-26`
Status: `ACTIVE / BASELINE 0 FROZEN / EA READY FOR USER TESTER RUN / NO PRODUCTION AUTHORITY`
Market authority: `GOLD# ONLY`
Base GitHub HEAD before V13 packet: `b57be8e619254191f3a54da86bec3745edae6ac8`

## 0. Start order

GitHub `awindboy/Trading` latest `main` is the Single Source of Truth.

Read in this order:

1. repository `AGENTS.md`;
2. this file;
3. `V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. `HANDOFF_V13.md`;
5. `RESEARCH_STATE_V13.md`;
6. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
7. `V13_MQL5_BACKTEST_PROTOCOL_20260926.md`;
8. `results/README.md` and the newest V13 result receipt;
9. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` for implementation parity.

## 1. Why V13 exists

V13 intentionally resets the strategy stack after V9-V12 accumulated too many
interacting components to attribute gains and failures cleanly.

The V13 question is deliberately simpler:

> How far can a minimal HA-only participation engine go, exactly where does it
> fail, and what single addition improves those failures without obscuring the
> cause?

Do not reconstruct an old strategy and do not automatically import old rules.
Historical generations may explain prior failures, but V13 rules must be earned
again from the V13 baseline.

## 2. Frozen Baseline 0

Baseline 0 uses only standard H4 Heikin-Ashi.

```text
HA_CLOSE = (O + H + L + C) / 4
HA_OPEN(first warm-up bar) = (O + C) / 2
HA_OPEN(t) = (HA_OPEN(t-1) + HA_CLOSE(t-1)) / 2
```

Color:

```text
BULL if HA_CLOSE > HA_OPEN
BEAR if HA_CLOSE < HA_OPEN
exact equality inherits the previous non-zero color
```

Journey / Child semantics:

```text
one contiguous same-color completed-H4 HA run = one Journey
first qualifying HA flip starts Child #1
next completed same-color HA bar adds Child #2
...
maximum = 10 successful Children
bars after Child #10 add nothing
first completed opposite-color H4 HA closes all Journey Children
same opposite-color event starts the next Journey after close-all succeeds
```

Baseline 0 has:

- no Hard SL;
- no TP;
- no break-even;
- no trailing stop;
- no partial take profit;
- no liquidity rule;
- no CRT;
- no Wave Candle;
- no ML;
- no session/day/hour/news rule;
- no volatility gate;
- no extra indicator;
- no dynamic sizing.

Each Child is one fixed volume unit. The EA default is `0.01` lot per Child.

## 3. Causal timing

Only completed H4 bars may decide.

At the first tick of a newly opened H4 bar:

1. the just-completed H4 OHLC becomes known;
2. its HA value/color is finalized;
3. the Journey decision is made;
4. required market orders are sent at the currently executable Bid/Ask.

No forming H4 bar is used as a completed signal.

Warm-up history before 2024 is permitted only to initialize the recursive HA
state. It cannot create a carried position into the V13 evaluation window.

The evaluation begins flat and waits for the first new HA color flip after the
start boundary.

## 4. Comparison-window authority

Current canonical window:

`2024-01-01 through 2026-08-28 available GOLD# history`

Whenever V13 A and V13 B are compared, both must use this complete window.
Month-only or selected-period comparisons may diagnose behavior but must never
be reported as the primary performance comparison.

## 5. Execution boundary

Official economics come from MT5 Strategy Tester with `Every tick based on real
ticks`.

The EA is a research EA, not a live system. It deliberately fails closed on an
order/close failure. It does not invent a retry schedule. A failure must remain
visible in the Journal and invalidate that run until the execution issue is
understood.

A hedging account/tester mode is required so each Child remains an independent
position and can be inspected in the history.

## 6. Research discipline after Baseline 0

The next V13 experiment must name exactly what it changes from Baseline 0.
Prefer one layer at a time, for example:

```text
Baseline 0
-> Baseline 0 + one risk rule
or
-> Baseline 0 + one participation rule
or
-> Baseline 0 + one exit rule
```

Do not simultaneously alter entry, SL, exit, and sizing and then attribute the
result to one idea.

No new threshold, cooldown, retry, minimum-R, no-chase, forced side balance, or
trade quota exists unless a new V13 contract explicitly defines it.

## 7. Current next action

Compile and run `V13HAOnlyMax10EA.mq5` on GOLD# over the frozen full window,
export the MT5 tester report, and freeze the first official V13 Baseline-0 result
receipt before researching any improvement.
