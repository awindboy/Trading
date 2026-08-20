# D-144 Reaction / Entry Barrier Audit

Date: 2026-08-20
Build: `1.92R1L6`
Phase: `REACTION_ENTRY_BARRIER_AUDIT_V1_EXACT_TICK`
Strategy authority: **NONE**

## Research question

The target is not to remove a few losing trades. The audit asks where a trade-direction hypothesis can first achieve a repeatable standardized hit rate, especially whether any causal stage can support a `>=50%` 1R win rate.

The observed D-143 path suggests:

```text
HTF direction can be late, especially SHORT
-> Root Contact often still reacts correctly
-> Sweep retains some response
-> CHoCH/FVG often arrive after the response has decayed
-> FVG retest / actual Fill may add adverse selection
```

D-144 measures that hypothesis directly.

## Frozen measurement

No threshold is optimized from D-144 output. Before the run the only target levels are frozen as:

```text
TP = +1.0R, +1.5R, +2.0R
SL = -1.0R
```

For stage comparisons, R is the Root Contact risk distance derived from current baseline `ROOT_OB_DISTAL_20`. It is frozen on the first causal tick after contact and reused unchanged at Sweep, CHoCH and FVG.

For actual fills, R is the actual `fill_price -> normalized_sl` distance.

Each stage is measured in the scenario direction and its exact sign-flipped mirror.

## Causality

- ROOT_CONTACT is actionable only after the closed M1 contact bar is known.
- SWEEP / CHOCH / FVG virtual entries activate on the first tick at/after their already-existing scenario event time.
- LONG virtual exits use Bid.
- SHORT virtual exits use Ask.
- No M1 OHLC is used to guess first-hit ordering.
- If actual Fill is discovered after its fill second, exact fill virtual ordering is skipped rather than reconstructed.
- No fixed time expiry is invented; tester-end unresolved paths are right-censored.

## Required analysis

Primary:

```text
stage × direction × target_R
resolved count
TP_FIRST count
SL_FIRST count
win rate
right-censored count
time-to-resolution
MFE_R / MAE_R
```

Secondary:

```text
LONG vs SHORT
H1 vs M30 primary map
H1/M30 agreement/disagreement
symbol
month
structure-event/root lineage
current-direction vs flipped-direction
```

A result is not considered a strategy candidate merely because pooled 2025 win rate exceeds a threshold. It must show breadth and survive later-period validation.

`2021` remains untouched.
