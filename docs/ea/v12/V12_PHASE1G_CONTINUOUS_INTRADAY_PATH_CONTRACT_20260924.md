# V12 Phase-1G continuous intraday path contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT REPRESENTATION STUDY / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1g-continuous-intraday-path-v1`

## Correction of direction

Phase 1D and 1E mostly treated hour, session, weekday, and event proximity as
cells. Phase 1F then returned to a liquidity-target inventory already known to
be too broad. Neither construction represents the user's actual time thesis:
the market carries unfinished business and damage from Asia through London and
New York, while scheduled and realized events alter that same path.

Phase 1G therefore does not ask whether one named session is good or bad. It
asks what path was already built by the query timestamp.

## Time is a path, not a label

Asia, London, and New York names identify only the clocks that generate source
ranges. They are not primary classifier buckets. At every V10 Child, FAST flip,
bridge, and repair timestamp, the raw-M1 causal prefix reconstructs:

- the latest completed Asia range;
- the London range frozen exactly at the New York open;
- the latest completed London range;
- the latest completed New York range.

For each available source box, retain its OHLC, range, net move, path
efficiency, exact age, and the entire later path through the query:

- first strict high and low break times and their order;
- maximum extension beyond each edge;
- M1-close dwell above, inside, and below the range;
- boundary transitions and outside-to-inside repairs;
- exact time since the last transition;
- current settlement location;
- post-box net displacement and path efficiency.

Cross-box overlap, center separation, range ratio, and directional alignment
describe how one clock handed the market to the next. These are continuous
coordinates. A hard label such as `NEW_YORK_SESSION` cannot replace them.

## Causal box and break rules

- A box or handoff snapshot exists only after its frozen end timestamp.
- `LONDON_AT_NEW_YORK_OPEN` uses only London prices revealed before the exact
  DST-aware New York open; it never uses the later London close.
- Edge equality is a touch. A break requires a strict point-rounded M1 breach.
- Same-M1 high/low break order remains ambiguous without ticks.
- All range and displacement fields retain raw price and prior-60-completed-
  broker-date median-range normalization.

## Event sequence

The corrected MQL5 calendar is joined as an event stream, not `PRE_30_60` or
`POST_0_60` cells.

- Before release, only schedule, importance, codes, sectors, and exact minutes
  until release exist.
- After release, exact minutes since release, causal surprise, and realized
  price path may exist.
- Every source-box edge break records the nearest prior and following USD
  moderate/high event and the signed minute distance.
- The query also records the count and realized surprise of events encountered
  since each source box ended.

No event may be credited with causing a break merely because it was nearby.
The ledger records temporal order and distance; causal attribution remains a
hypothesis.

## Incremental-information test

Four deterministic weighted ridge-logistic shadow models are compared on
expanding chronological folds:

1. CRT/V10 structure only;
2. structure plus the old static session/weekday/event buckets as a negative
   control;
3. structure plus continuous clock and exact event timing;
4. structure plus the full continuous intraday path.

Train-only standardization, one-hot vocabularies, and an inner time split choose
regularization from the frozen grid. Test periods are never used to choose a
feature, coefficient, lambda, or threshold.

Stop and `>=5R` right-tail presence are modeled separately. Weighted Brier,
log loss, AUC, and test-only prediction quintiles must expose both avoided
stopped units and displaced right-tail capital. A better stop score that merely
rejects the right tail is not success.

The primary Child model includes only frozen rows whose execution event is
`ENTRY`. `ORDER_FAIL` and `EXIT_PENDING_BLOCK` remain in the context ledger but
cannot teach a strategy stop model; their lifecycle belongs to later EA work.

## Authority boundary

This phase tests whether the continuous temporal representation contains
incremental information. It cannot create, veto, delay, exit, or resize a
Child. It does not revive a session rule, event rule, liquidity target, Wave
gate, or black-box oracle. All observations through `2026-09-18 23:57` are
consumed development evidence; `GOLD# 2021` remains sealed.
