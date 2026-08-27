# V5-002 — Balance-Generated Boundary Research Contract

Status: `PRE-REGISTERED / OUTCOMES UNOPENED UNDER THIS DESIGN`
Date: `2026-08-27`
Trading authority: `NONE`

## 1. Why V5-002 exists

V5-001A rejected a convenient shortcut:

```text
previous-day high/low == meaningful technical boundary
```

That proxy did not retain a robust directional effect after causal pre-state matching.

The Success-First corpus points to a different object:

```text
a range / balance is formed by prior two-sided price behavior;
its own boundary is then resolved.
```

Brandt's rectangle and Crabel's contraction/expansion cycle are examples.

V5-002 tests that object without first selecting a profitable `box` threshold.

## 2. Research question

For a causally defined trailing price range:

> Does the **continuous character of the pre-break range** condition the later breakout path?

Do not ask:

```text
Which range length makes the most money?
```

## 3. Pre-registered scales

All must be built and reported:

```text
60 minutes
240 minutes
1440 minutes
```

These are measurement scales, not candidates selected by P/L:
- 1h;
- 4h;
- 1 broker day.

No scale may be silently discarded because its discovery result is weak.

## 4. Causal range definition

At M1 event bar `t`, for scale `W`:

```text
window = observed bars in [t-W, t)
high_W = max(high) in window
low_W  = min(low) in window
```

Current M1 bar is excluded.

Up breakout event:

```text
current high > high_W
```

Down breakout event:

```text
current low < low_W
```

The frozen pre-break range `[low_W, high_W]` becomes the event's reference.

## 5. Episode de-duplication

A same-scale/same-direction breakout becomes `ACTIVE`.

Do not create another same-direction event at that scale while price remains outside that event's frozen boundary.

Re-arm only after a completed M1 close returns inside the frozen pre-break range.

This lifecycle is causal and uses no P/L cooldown.

If one bar breaks both sides, record the event(s) with `dual_break = true`; do not silently choose a direction.

## 6. Balance is continuous first

Do **not** define:

```text
efficiency < x = balance
range ratio < y = contraction
```

in V5-002A.

Record the following pre-event axes continuously.

### B1 directional efficiency

```text
abs(net log return in W)
/
sum(abs(M1 log returns in W))
```

Low values are *consistent with* two-sided balance, but receive no threshold authority.

### B2 non-overlapping contraction ratio

```text
range([t-W,t))
/
range([t-2W,t-W))
```

### B3 realized-volatility ratio

```text
RV([t-W,t))
/
RV([t-2W,t-W))
```

### B4 midpoint crossing density

Count completed-close crossings of the frozen window midpoint inside W, normalized by observed transitions.

### B5 boundary age

Minutes since the relevant high_W / low_W was last established within the pre-event window.

### B6 activity ratio

Tick-volume sum in current W divided by tick-volume sum in the preceding non-overlapping W.

Tick volume remains an activity proxy, not true order flow.

### B7 spread state

Recorded spread/price and spread relative to causal short-horizon volatility where possible.

## 7. Full-path outcomes

Reuse continuous V5-001 path fields at:

```text
5 / 15 / 30 / 60 / 240 minutes
```

including:
- signed boundary displacement;
- maximum extension;
- inside excursion;
- fraction of closes beyond;
- first re-entry;
- directional efficiency;
- realized volatility;
- data coverage/censoring.

No P/L or Entry rule is created.

## 8. Primary falsification tests

Before interpreting a balance descriptor:

1. **Market/year sign stability** — not pooled only.
2. **Direction split** — upward and downward separately.
3. **Scale report** — all 60/240/1440m.
4. **Permutation control** — shuffle the descriptor within symbol/year/direction/time-of-day block; real relation must
   exceed the shuffled relationship.
5. **Volatility confounder** — a descriptor that only predicts absolute movement after conditioning on realized
   volatility is not directional mechanism evidence.
6. **Confirmation geometry** — if post-break evidence becomes informative only after most displacement is consumed,
   record it as state description, not Entry edge.

## 9. Primary questions, in order

### Q1
Do balance descriptors explain **resolution direction**?

### Q2
If not, do they explain only **interaction intensity / volatility**?

### Q3
Does early post-break behavior add incremental information about the path that remains after that observation?

### Q4
Are any relationships stable across independent market-years?

Do not skip from Q2 to a trading strategy.

## 10. Data

Discovery only:

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

Still closed:
- XAUJPY# / XAUCNH# / GAUCNH# / GAUUSD# V4 vault;
- GOLD# 2021.

GOLD# 2022 remains consumed.

## 11. Allowed conclusions

Only:

```text
BALANCE CHARACTER SUPPORTS A PREREGISTERED SEMANTIC CANDIDATE
OBSERVABLE PROXY INSUFFICIENT
MECHANISM NOT SUPPORTED
CONFOUNDED / DESIGN INSUFFICIENT
```

No strategy authority.
