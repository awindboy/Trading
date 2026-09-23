# V12 Phase-1D temporal and economic-event state contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT MECHANISM STUDY / NO TRADE OR SIZING AUTHORITY`

Contract version: `v12-phase1d-temporal-event-state-v1`

## 1. Question

Phase 1D asks whether time is a missing state dimension in V12 rather than a
weekday/hour admission filter. It tests three nested clocks:

1. the recurring MT5 broker-clock liquidity profile;
2. scheduled macroeconomic release clusters and the realized release shock;
3. the age and transition clock of the frozen V10 Child and Phase-1B journey.

The purpose is to determine whether repeated stopped exposure is concentrated
in reproducible temporal/event states while useful right-tail capital remains
concentrated elsewhere. A lower trade count alone is not success.

## 2. Source and clock authority

- Market input remains verified raw `GOLD#` M1 streamed only through
  `2026-09-18 23:57`.
- Economic events come from the MetaTrader 5 Economic Calendar terminal API:
  `CalendarValueHistory`, `CalendarEventById`, and `CalendarCountryById`.
- MQL5 documents calendar timestamps and query bounds as trade-server time.
  This makes a direct numeric join to broker-label M1 possible when the same
  connected terminal produced the price exports.
- The exported event snapshot must record terminal build, broker/server,
  extraction time, requested range, row count, and SHA-256.
- Exact duplicate value IDs are deduplicated. If copies of one value ID disagree
  on timestamp or any other field, all copies of that ID are excluded; the
  analysis must not choose the more convenient timestamp.
- Before joining outcomes, offsets `-1, 0, +1, +2, +3, +4` hours are audited
  against 15-minute USD-high activity. This is a source-clock integrity check,
  not an optimized feature or named-session conversion.
- TradingView may be used only as a spot-check for selected rows or missing
  fields. It cannot silently replace the terminal snapshot or change timestamps.
- No broker timestamp is called London or New York time until an independent
  timezone/DST check passes. Results remain in broker-clock labels.

## 3. Event record and clustering

Each calendar value retains:

- value/event IDs and release/period timestamps;
- country, currency, event name/code, source URL;
- event type, sector, frequency, time mode, importance, unit, multiplier,
  digits, and impact type;
- actual, forecast, previous, and revised-previous values with explicit missing
  flags.

Multiple releases at the same server minute form one event cluster. The cluster
retains its member count, maximum importance, currencies/sectors, and each
member's values. It is not counted as several independent market shocks.

## 4. Causal availability

The analysis keeps two physically distinct feature times:

- `SCHEDULED_STATE`: release time, country/currency, metadata, importance,
  forecast, and previous value. These may describe time before release.
- `REALIZED_STATE`: actual value, revised previous value, impact type, and
  surprise. These become available only at or after the release timestamp.

No actual or surprise value may explain a decision made before the release.
Historical calendar revisions are treated as snapshot risk and disclosed; they
are not assumed to reproduce the exact pre-release database state.

## 5. Normalization

- Event surprise is `actual - forecast` in the event's native decoded units.
- Cross-event comparison uses a causal expanding median/MAD of prior releases
  of the same `event_id`; fewer than six prior releases produces no normalized
  surprise rather than an imputed value.
- M1 tick volume and range are interpreted relative to a causal rolling
  60-trading-day median/MAD for the same broker minute of day.
- Raw values remain present. Normalization is a coordinate, not an entry rule.

## 6. Frozen observation windows

For each event cluster, report symmetric market windows of `15`, `30`, `60`,
`120`, and `240` minutes. For each V10 Child and Phase-1B FAST flip, report
minutes since the latest and until the next event cluster at those same bounds.

The windows are an observation grid. No best window is selected from consumed
outcomes and no window receives veto or sizing authority.

## 7. Required analyses

1. Broker weekday/hour/minute tick-volume and true-range profiles by year.
2. Stability of the user's observed broker `16:00` concentration.
3. Event-cluster volume/range lift versus matched same-weekday and same-minute
   non-event controls.
4. V10 selected-Child stop burden, stopped units per 100 funded, net R, PF,
   and `>=5R` right tail by scheduled and realized event state.
5. Phase-1B FAST-flip explanation state, immediate k1 stop, later repair, and
   Parent termination by event proximity.
6. Concentration and stability by year, side, weekday, hour, importance,
   currency, and sector.

Any proposed interpretation must state which stopped units disappear, which
right-tail units disappear, and whether the distinction holds outside one year
or one event family.

## 8. Evidence boundary

All price chronology through the cutoff is consumed development evidence.
`GOLD# 2021` remains sealed. The calendar snapshot can establish temporal and
event associations, not causation, future performance, trade authority, or a
news-direction oracle. A later action proposal requires a frozen future shadow
and Python/MQL5 parity.
