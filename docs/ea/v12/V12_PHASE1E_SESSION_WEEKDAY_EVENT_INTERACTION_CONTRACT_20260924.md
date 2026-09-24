# V12 Phase-1E session, weekday, and event interaction contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT MECHANISM STUDY / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1e-session-weekday-event-interaction-v1.1`

## Question

Phase 1E tests whether the Phase-1D clock result becomes more explanatory when
the broker hour is mapped into real DST-aware market clocks and crossed with
weekday, scheduled events, and the already frozen CRT/FAST transition state.
It does not search for the best session or weekday filter.

The required question for every cell is two-sided: which stopped units are
concentrated there, and how much `>=5R` right-tail capital is carried there?

## Corrected calendar authority

The Phase-1D monthly exporter exposed a startup time-namespace defect: the
first January 2022 query was three hours behind later queries and eight value
IDs were duplicated at the January/February boundary. Excluding those eight
IDs did not repair the first-month timestamps.

The corrected exporter waits for terminal/server synchronization, requires two
complete reads of a sentinel interval to agree on every ID and timestamp, and
then performs one full-range query. The new snapshot has one row per value ID.
Its fixed `UTC+3` broker-label mapping must pass two independent schedule
sentinels before any named-session result is accepted:

- US nonfarm payrolls: `08:30 America/New_York`;
- Federal Reserve rate decision: `14:00 America/New_York`.

One source anomaly is frozen explicitly rather than hidden: the ten-member US
Employment Situation cluster on `2025-11-20` is stored by MQL5 at server 15:30,
while the official BLS schedule and release record say 08:30 ET. Under the
verified fixed UTC+3 mapping that is server 16:30. The exact ten value IDs and
the official source are locked in `v12_calendar_time_overrides.json`; an
override applies only when both ID and original timestamp match.

Phase 1D must be rerun with this snapshot. Any changed conclusion is corrected,
not silently carried forward.

## Frozen session coordinates

Broker labels are converted to UTC by subtracting three hours and then mapped
with IANA DST rules. The windows are market landmarks, not claims that OTC gold
has a single centralized session:

- `ASIA_PRECIOUS_CORE`: JPX precious-metals day session, 08:45–15:45 Tokyo;
- `LONDON_CORE`: 08:00–16:30 London;
- `NEW_YORK_RISK_CORE`: 08:30–16:00 New York, beginning with the common US
  macro-release clock and covering the US cash-risk session.

Each minute receives exactly one phase: `OFF_CORE`, `ASIA_ONLY`,
`LONDON_PRE_NY`, `LONDON_NY_OVERLAP`, or `NY_AFTER_LONDON`. LBMA 10:30/15:00
London auctions and the 13:29–13:30 New York COMEX settlement are separate
landmark coordinates, not new sessions.

## Weekday and units

Both broker weekday and New York local weekday are retained. V10 Children are
classified at decision, entry, and exit; the primary capital scorecard uses
entry session because it is the first period actually exposed. FAST flips use
their causal `known_at` timestamp.

Required tables cover M1 activity, V10 capital, and FAST-flip outcomes by the
predeclared session/weekday/CRT/event interactions in the JSON contract. The
existing `H20 + aligned + pre-USD-moderate/high 30–60m` cell is decomposed by
session, New York weekday, year, and event family to test whether it is merely
a Friday/Baker-Hughes or US-afternoon proxy.

Generic stability tables also cross session and weekday with year, side, and
the original broker H4 slot. These are required parity checks, not extra cells
selected because of an attractive consumed-history result.

## Uncertainty and promotion boundary

Cells with at least 20 Children receive a deterministic 2,000-draw ISO-week
block-bootstrap interval for stopped units per 100 funded and net R. All
predeclared cells are reported; no best cell is promoted from consumed data.
No session, weekday, landmark, event, CRT state, or interaction may veto,
delay, resize, reverse, or exit a trade in this phase.
