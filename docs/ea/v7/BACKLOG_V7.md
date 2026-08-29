# V7 Backlog

Status: `ACTIVE`
Current phase: `V7-003A GOLD25/BTC25 DOUBLE-B ANATOMY`

## Immediate — next session

- [ ] Recheck latest GitHub HEAD and V7 handoff.
- [ ] Locate/obtain full-year `GOLD# 2025` M1 data.
- [ ] Locate/obtain full-year `BTCUSD# 2025` M1 data.
- [ ] Record names, SHA256, coverage and timezone/server convention.
- [ ] Run structural data-quality checks.
- [ ] Freeze one H1 resampling convention.
- [ ] Detect all Double-B events.
- [ ] Save/freeze the complete event census before subgroup analysis.
- [ ] Build the V7-003A anatomy ledger.
- [ ] Open outcomes and characterize 1h/4h/12h/24h paths.
- [ ] Discover recurring path families without forcing exactly three archetypes.
- [ ] Write `V7_003A_DOUBLEB_ANATOMY_RESULTS.md`.

## Anatomy fields

Identity:
- event id;
- market;
- H1 time;
- upper/lower/both.

Pre-event:
- 24h/48h displacement;
- trend/range/transition;
- causal S/R;
- MA20 slope/distance;
- BB20 width/change;
- BB4 width/change;
- BB4-vs-BB20;
- session/opening-H1;
- current KTR and causal same-session rank.

Event:
- range/body/wicks/close;
- range/KTR and body/KTR;
- band state;
- S/R relationship;
- session-break state.

Future — discovery only:
- high/low excursion 1h/4h/12h/24h;
- excursion/KTR;
- time to ±0.5/1/2/3KTR;
- structure acceptance/failure/reclaim;
- one-stage/two-stage note;
- descriptive family.

## V7-003B — Context Atlas

- [ ] session opening-candle break/acceptance/failure;
- [ ] support/resistance;
- [ ] Bollinger geometry;
- [ ] candle anatomy;
- [ ] MA/trend maturity;
- [ ] trendline only if a real information gap remains.

For each factor identify whether it helps:
event meaning / archetype / direction / entry / SL / TP room.

## V7-003C — KTR Geometry

- [ ] same-session KTR history;
- [ ] normalized excursion;
- [ ] structural invalidation/KTR;
- [ ] target room/KTR;
- [ ] time-to-KTR barriers;
- [ ] no fixed multiplier tournament.

## V7-003D — Entry Architecture

- [ ] immediate;
- [ ] planned pullback/zone;
- [ ] wait-confirm;
- [ ] skip;
- [ ] separate entry timing error from direction error.

## V7-003E — Staging / Campaign Risk

- [ ] single-entry baseline first;
- [ ] adverse excursion by family;
- [ ] staged entry only where pullback is planned;
- [ ] report legs and total campaign stop-risk.

## V7-003F — Freeze

- [ ] taxonomy;
- [ ] decision card;
- [ ] confirmation logic;
- [ ] KTR use;
- [ ] staging if any;
- [ ] metrics;
- [ ] untouched V7-004 cohort before outcomes.

## Deferred

- V7 EA;
- production sizing;
- live/paper deployment;
- ML classifier;
- automatic trendline;
- portfolio construction.

## Permanently consumed

- V7-002 24-event set and hindsight plans.
- GOLD# 2025 / BTCUSD# 2025 after V7-003 outcome analysis begins.

## Hard restrictions

- no P/L optimization in V7-003A;
- no fixed KTR-table search;
- no staging research before event/single-entry anatomy;
- no deleting ambiguous Double-B events;
- no market expansion based on discovery P/L;
- no same-data validation;
- no V6 filter import.
