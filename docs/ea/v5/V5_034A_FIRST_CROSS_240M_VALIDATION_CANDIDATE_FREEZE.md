# V5-034A — First Cross 240m Validation Candidate Freeze

Status: `FROZEN VALIDATION CANDIDATE`
Date: `2026-08-27`
Parent result: `V5-030A DEVELOPMENT PASS`
Production authority: `NONE`

## Candidate identity

```text
V5_FIRST_CROSS_240M_HALF_EMA_RUNNER
```

This document freezes the exact strategy before any V5 external-market validation data are opened.

## Signal timeframe

```text
240 minutes
```

Bars are broker-server-time bars resampled causally:

```text
closed = left
label = right
```

A bar labeled `T` contains observations in `[T-240m, T)` and becomes available at `T`.

## 3/10 oscillator

```text
fast = SMA3(close) - SMA10(close)
slow = SMA16(fast)
```

LONG regime starts when slow crosses from `<=0` to `>0`.
SHORT regime is mirrored.

The setup is only the **first** fast-line pullback through zero after the slow regime change while slow remains on the trend side.

## Price confirmation

The oscillator is an initial condition, not the Entry.

After the first oscillator pullback:

LONG:
- take the first causal 3-bar pivot low;
- pivot low must remain above the frozen reversal-regime low.

SHORT mirrored:
- first causal 3-bar pivot high;
- pivot high must remain below the frozen reversal-regime high.

The pivot at bar `k` is known only after completion of `k+1`.

Entry stop:

```text
LONG  = high(k+1) + one symbol point
SHORT = low(k+1)  - one symbol point
```

Initial stop:

```text
LONG  = pivot low  - one point
SHORT = pivot high + one point
```

The candidate also preserves the frozen prior-impulse structural objective only as a setup-validity constraint:
it must lie beyond the actual Entry. The candidate management does not exit at that objective.

## Pending-order lifecycle

Order expires when the 3/10 slow line crosses zero against the regime.

Before fill, invalidation of the frozen reversal-regime extreme cancels the setup.

If Entry and structural invalidation/stop cannot be ordered inside the same M1 bar, exclude conservatively.

Gap-through Entry uses the worse M1 open when applicable.

## Management

Let initial structural risk be `1R`.

Before +1R:
- full position uses the original structural stop.

If stop first:
- gross `-1R`.

If +1R first:
- realize exactly 50% at `+1R`;
- runner stop moves to original Entry;
- no fixed runner profit target.

Runner exits at the first:
1. completed 240m close through EMA20 against the position; or
2. 3/10 slow line zero-cross against the position;

executed at the next available M1 open at the completed signal-bar timestamp.

The BE runner stop remains active intrabar.

Same-M1 `+1R then back to Entry` ordering is ambiguous and excluded.

## Cost model for Level-A validation

Subtract once:

```text
2 * entry_bar_spread_points * symbol_point / initial_risk
```

This is a recorded-spread proxy only.

Do not alter the setup because a market has high cost.

## Explicitly absent

No:
- session veto;
- market veto;
- direction veto;
- ADX threshold;
- ATR adequacy filter;
- daily alignment;
- target-room threshold;
- alternate timeframe;
- commission/slippage fudge chosen from development results.

## Development evidence

Read `V5_030A_FIRST_CROSS_240M_DEVELOPMENT_RESULTS.md`.

The rule above is now immutable for external validation.

Any change creates a new discovery candidate and cannot use the same external validation set as pristine evidence.
