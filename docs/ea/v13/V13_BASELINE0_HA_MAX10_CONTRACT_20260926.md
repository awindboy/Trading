# V13 Baseline 0 Contract — Standard H4 HA / Max-10 Journey

Date: `2026-09-26`
Status: `FROZEN BASELINE CONTRACT / RESEARCH ONLY`
Market: `GOLD# ONLY`
Production authority: `NONE`

## 1. Purpose

This contract defines the smallest V13 trading system. It is the reference from
which future V13 additions are measured.

It is intentionally not an old-version restoration.

## 2. Input information

Only raw completed H4 OHLC is used to calculate standard Heikin-Ashi.

No other timeframe or indicator may influence a Baseline-0 trade.

## 3. Standard HA formula

For each H4 source bar:

```text
HA_CLOSE = (O + H + L + C) / 4
```

Initialization at the earliest warm-up bar:

```text
HA_OPEN_0 = (O_0 + C_0) / 2
```

Then:

```text
HA_OPEN_t = (HA_OPEN_(t-1) + HA_CLOSE_(t-1)) / 2
```

Color:

```text
BULL: HA_CLOSE > HA_OPEN
BEAR: HA_CLOSE < HA_OPEN
EQUAL: inherit previous non-zero color
```

Warm-up starts from available pre-evaluation history at or after
`2022-01-03 00:00` broker time. Warm-up creates state only, never a position.

## 4. Evaluation boundary

The evaluation starts flat.

No Journey that began before `2024-01-01` is carried into the result.

The EA waits for the first completed post-boundary HA color flip before starting
Journey 1.

The current frozen end of the comparison history is `2026-08-28`.

## 5. Journey definition

A Journey is one contiguous run of completed H4 HA candles with the same color.

Journey direction is the HA color:

- BULL -> LONG Journey;
- BEAR -> SHORT Journey.

## 6. Child entry

At the first tick of a new H4 bar, the previous H4 bar becomes the completed
signal bar.

If that completed bar starts a new Journey, submit Child #1 in the new direction.

For each later completed H4 bar with the same Journey color, submit one
additional Child.

Each Child uses the same fixed requested volume.

Default EA volume:

`0.01 lot per Child`

## 7. Maximum participation

Maximum successful Children in one Journey:

`10`

After Child #10, further same-color completed H4 bars create no order.

The cap is a user-authorized V13 baseline rule, not a fitted threshold.

## 8. Exit and reversal

The first completed H4 HA bar of the opposite color ends the active Journey.

At the first executable tick of the new H4 bar:

1. close every open Baseline-0 position for the current symbol/magic;
2. verify close-all success;
3. start the opposite Journey;
4. submit Child #1 in the opposite direction.

There is no delayed confirmation.

## 9. Risk / take profit

Baseline 0 deliberately has:

```text
Hard SL = none
TP = none
break-even = none
trailing = none
partial close = none
```

Loss is controlled only by the next opposite completed H4 HA exit and by the
10-Child participation cap.

## 10. Forbidden hidden rules

Baseline 0 may not use:

- CRT or liquidity;
- FAST/STD/SLOW transformed HA;
- Wave Candle;
- ML or probability scores;
- ATR/range/volatility filters;
- session/day/hour/news filters;
- minimum-R or target-distance gates;
- cooldown or retry rules;
- fixed no-chase distance;
- forced LONG/SHORT balance;
- additional Child spacing beyond one completed H4 HA bar;
- discretionary overrides.

Any addition creates a new named V13 experiment.

## 11. Execution-failure policy

Trade execution failure is not a market signal.

The baseline EA does not invent retries. If an intended market open/close does
not receive a successful trade-server result, the EA logs a `V13_HALT` record
and stops generating further trades for that run.

That run is execution-invalid until the failure is understood.

## 12. Official evaluation

Primary economic evidence must come from MT5 Strategy Tester on the full frozen
window using `Every tick based on real ticks`.

A partial-period result cannot establish superiority over Baseline 0.
