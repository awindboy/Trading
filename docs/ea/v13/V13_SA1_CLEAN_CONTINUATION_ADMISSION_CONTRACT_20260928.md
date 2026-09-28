# V13 SA-1 Clean Continuation Admission action contract

Date: `2026-09-28`
Status: `CONSUMED-DEVELOPMENT ACTION CANDIDATE / ACTUAL-TICK STRATEGY TESTER VALIDATION PENDING`
Base GitHub `main`: `652dcd070206f04a51eb5a7451a253393b60ee03`
Market: `GOLD# ONLY`

## 1. Purpose

SA-1 is an **admission overlay** on the current HA-9 add-on mechanism. It was derived after State-Anatomy showed that the dominant difference between quick winners and no-proof timeout losers is not holding time itself but whether the signal H4 and its internal H1 path already show clean directional acceptance.

SA-1 is not a new exit-horizon, runner, re-arm, cooldown, ML score or risk-sizing branch.

## 2. Frozen parts

The following remain unchanged:

- Standard H4 Heikin-Ashi Journey definition.
- Child #1 timing and management.
- Opposite completed H4 HA closes the remaining Journey and starts the opposite Journey.
- Fixed unit size during research.
- Maximum 10 **successful** Child entries.
- HA-9 management after an add-on is admitted: one-H4 favorable-extreme proof, proof timeout, and post-proof breakout lock.
- No initial Hard SL, TP, ATR offset, HASTOC threshold, ADX/volume gate, session gate, side exception or calendar exception.

## 3. Admission population

SA-1 applies only to same-color H4 add-on opportunities while a Journey is active and successful Child count is below 10.

Child #1 bypasses SA-1 and remains Baseline-0/HA-9 unchanged.

## 4. Exact admission conditions

For the just-completed same-color signal H4 with Journey direction `d`:

### A. Raw-close acceptance

Use the completed raw H4 close and that same H4's standard HA close.

```text
LONG:  raw Close > HA Close
SHORT: raw Close < HA Close
```

Strict comparison. Equality is not accepted.

### B. No opposite H4 HA wick

Using standard H4 HA geometry:

```text
LONG:  lower opposite wick == 0 within price epsilon
SHORT: upper opposite wick == 0 within price epsilon
```

The research EA uses `_Point * 0.1` as floating-price epsilon for equality handling, not as an optimized trading threshold.

### C. No H1 opposition inside the signal H4

Reconstruct standard H1 HA causally from the same broker history. Consider the observed completed H1 bars whose open timestamps fall inside `[signal_H4_open, signal_H4_open + 4h)`.

```text
LONG signal: every observed H1 HA color must be LONG
SHORT signal: every observed H1 HA color must be SHORT
```

At least one observed completed H1 is required. Missing market-closure hours are not invented and do not automatically fail the gate; only observed H1 bars are evaluated.

### Admission

```text
ADMIT = raw_close_accept
        AND no_opposite_H4_wick
        AND signal_H4_H1_no_opposition
```

No fitted numeric score or weighted threshold is allowed.

## 5. Entry and Child numbering

If admitted, enter at the same first executable timing used by HA-9 after the completed signal H4.

If rejected:

- do not enter;
- do not increment successful Child count;
- do not backfill that rejected signal later using future price;
- a later same-color completed H4 may independently be evaluated as the next opportunity while the Journey remains active;
- stop once 10 successful Child entries have occurred.

This preserves the Baseline-0 definition of maximum 10 **successful entries**, rather than consuming a Child ordinal for a skipped signal.

## 6. Post-entry management

Once an add-on is admitted, SA-1 ends and HA-9 controls management exactly:

1. signal-H4 raw HIGH is proof target for LONG; raw LOW for SHORT;
2. proof must occur during the immediately following H4;
3. if proven, lock is `max(actual entry, signal high)` LONG or `min(actual entry, signal low)` SHORT;
4. lock cannot trigger on the same proof observation;
5. if not proven, close at first executable print after one H4 proof window;
6. opposite H4 HA close-all has Journey priority;
7. a closed Child is not resurrected.

## 7. Causal constraints

- All admission inputs are known when the signal H4 completes.
- H1 colors used by the admission gate are completed before the H4 decision timestamp.
- Future T1/T2/T3 State-Anatomy features after the new entry are **not** admission inputs.
- No hindsight recovery, no side/year exception, no fitted Child-ordinal exception.

## 8. Current authority level

This contract defines a **research candidate**, not production authority. The consumed-data evidence is strong enough to justify a fresh actual-tick test, but not to authorize capital sizing or replace HA-9 until compilation, event parity and Strategy Tester economics are verified.
