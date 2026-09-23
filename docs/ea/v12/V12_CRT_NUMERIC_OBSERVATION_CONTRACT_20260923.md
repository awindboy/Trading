# V12 CRT causal numeric observation contract

Date: `2026-09-23`

Status: `PHASE-0 OBSERVATION CONTRACT / NO ENTRY AUTHORITY`

## 1. Purpose

This contract turns the CRT source grammar into an auditable numeric event
universe without pretending that unresolved discretionary terms are already
rules. It defines what must be recorded before a V12 entry contract can exist.

## 2. Input and clocks

- Source: verified GOLD# raw M1, monotonically revealed.
- Official lanes:
  - `W1_TO_H4`: parent W1, execution H4;
  - `D1_TO_H1`: parent D1, execution H1.
- Shadow lane: `H4_TO_M15_M5_SHADOW`, excluded from official scorecards.
- Bar boundaries use one frozen broker timezone/session specification. Weekend,
  holiday, and partial-session bars are flagged rather than silently deleted.
- Higher bars are assembled only from M1 rows revealed by the event timestamp.

## 3. Exhaustive parent universe

Every eligible completed parent bar is registered as a provisional C1. The next
completed parent bar is its C2. This prevents hindsight selection of only visually
meaningful ranges.

For each C1 record raw O/H/L/C, midpoint, range, body, wick proportions, duration,
ATR-normalized range, and causal location coordinates. Location may later rank a
candidate; it does not delete the Phase-0 event.

## 4. C2 range-interaction state

At C2 close, classify the interaction with the frozen C1 high/low:

- `NO_EXTREME_TRADE`;
- `HIGH_SWEEP_RETURN`: C2 high exceeds C1 high and C2 closes at or below C1 high;
- `LOW_SWEEP_RETURN`: C2 low falls below C1 low and C2 closes at or above C1 low;
- `HIGH_OUTSIDE_ACCEPTANCE`: C2 closes above C1 high;
- `LOW_OUTSIDE_ACCEPTANCE`: C2 closes below C1 low;
- `DUAL_SWEEP_INSIDE`: both extremes traded and C2 closes inside C1;
- `DUAL_OR_CONFLICTED`: both extremes traded with an outside/edge close that
  cannot be assigned to one clean branch.

Equality policy is explicit and symbol-point aware. Raw values and point-rounded
comparisons are both retained. Dual sweeps are never silently forced into the
last-looking direction.

Record sweep depth in price, C1-range units, and causal ATR units; C2 close
location within/around C1; elapsed time to first extreme; and whether each
extreme touch is known only to M1 or to exact tick order.

## 5. Branch intent

Phase 0 records a structural direction hypothesis, not a trade:

- high sweep and return -> rejection hypothesis SHORT;
- low sweep and return -> rejection hypothesis LONG;
- high outside acceptance -> continuation hypothesis LONG;
- low outside acceptance -> continuation hypothesis SHORT;
- dual/conflicted -> no directional authorization.

This mapping can be falsified later. It must not be altered after outcomes are
known.

## 6. Trigger primitives

The supplied source describes Model #1 and true MSS, but the current secondary
guide is not precise enough to grant automated entry authority. The Phase-0
ledger therefore records primitives separately:

- causal level swept;
- trigger candle O/H/L/C and direction;
- body/range ratio and normalized range;
- later completed close that invalidates the trigger candle's opposite side;
- displacement and optional FVG coordinates;
- close-through strength, return/repair, and time from C2 close;
- whether a true-MSS candidate breaks a causal swing rather than a visual zigzag.

`MODEL1_CONFIRMED` and `TRUE_MSS_CONFIRMED` may be assigned only after a separate
labeling guide and blind inter-rater audit are frozen. Until then they are
nullable annotations with no trade authority.

## 7. State machine

The canonical parent states are:

```text
C1_REGISTERED
-> C2_FORMING
-> C2_CLOSED_NO_TRADE
   or C2_REJECTION_OBSERVED
   or C2_OUTSIDE_ACCEPTANCE_OBSERVED
   or C2_CONFLICTED
-> TRIGGER_PRIMITIVES_OBSERVED
-> CHILD_CONFIRMATION_PENDING
-> CHILD_AUTHORIZED        (future contract only)
-> C3_ACTIVE               (future contract only)
-> TARGET1_50_HIT / INVALIDATED / EXPIRED / AMBIGUOUS
-> TARGET2_OPPOSITE_HIT / TERMINATED
```

Phase 0 ends at `CHILD_CONFIRMATION_PENDING`. Later states exist in the schema so
outcomes can be logged without retroactively authorizing a trade.

## 8. Parent and Child identifiers

- `parent_id` hashes symbol, lane, C1 open, C2 open, broker-clock spec, and source
  dataset hash.
- `child_id` adds trigger timestamp, direction, trigger family, and definition
  version.
- one Parent may own multiple Children only when each has a new completed trigger
  and its own frozen risk. Retrying after a stop without new information is not a
  new Child.

## 9. Risk and destinations

No Hard-SL variant has action authority yet. Phase 0 records two preregistered
structural variants for later comparison:

- `C2_EXTREME`: beyond the C2 sweep extreme plus symbol-point policy;
- `TRIGGER_STRUCTURE`: beyond the independently confirmed trigger structure.

They are calculated before outcome reveal and never widened. Variant comparison
must keep candidate coverage fixed and report ambiguous same-M1 cases.

Destinations are recorded independently:

- `TARGET_1`: C1 midpoint;
- `TARGET_2`: opposite C1 extreme;
- `TARGET_3`: older causal liquidity, if it existed at the decision time.

Touching 50% may permit a later partial-management study, but no exit rule is
authorized in Phase 0.

## 10. Subordinate observations

At C1 close, C2 close, trigger, and decision, record where available:

- raw OHLC geometry and causal ATR normalization;
- FAST/STD/SLOW HA O/H/L/C, color, run age, agreement, and separation;
- Wave settlement-density, path-efficiency, directional-settlement, and selected
  shell coordinates for H4 events;
- causal prior day/week highs/lows and swing objects;
- KOD-like location relative to a target as a numeric coordinate, not a label;
- SMT primitives only when both instruments share verified synchronized data.

None of these fields may delete a Phase-0 event.

## 11. Decision/outcome separation

The decision record contains only information available at `decision_time`. The
outcome record is a separate object keyed by `child_id` and may contain first
touch, R, MFE/MAE, duration, and execution states.

Feature builders must never join outcome fields before a split is frozen. Future
run length, eventual target, realized R, and time-to-stop are forbidden inputs.

## 12. Ambiguity and compliance

- Same-M1 target and SL touches without exact ticks -> `AMBIGUOUS_ORDER`.
- A future-loaded bar, post-outcome label edit, missing source hash, or changed
  timezone spec -> contamination incident.
- A manual exclusion requires a coded reason from a frozen list.
- Missing data is a state, not silently imputed evidence.
- Market-closed order failure is `EXECUTION_MARKET_CLOSED`, not a loss and not a
  backfilled trade.
