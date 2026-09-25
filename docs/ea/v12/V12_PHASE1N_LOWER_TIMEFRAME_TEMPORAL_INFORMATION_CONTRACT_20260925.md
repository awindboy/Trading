# V12 Phase 1N — lower-timeframe temporal-information contract

Status: **frozen before evaluation; consumed-development diagnostic only**  
Frozen: `2026-09-25`

## Why this phase exists

The reason to lower the timeframe is not to run V10 more often. H4 compresses
Asia, London, New York, economic releases, session-box breaks, re-entry, and
settlement into only six bars per day. Phase 1N tests whether those information
dimensions become useful when observed at the H1 and M15 Child clocks.

## Populations and outcomes

The two independent-attempt populations are H1 FAST `k=1` and M15 FAST `k=1`.
Each enters at the first following M1 open, uses the previous completed same-
timeframe STD HA extreme as a frozen Hard SL, and exits at the first opposite
completed FAST HA decision. Conservative same-M1 ordering remains primary.

The three separately modeled outcomes are Hard SL, `>=3R`, and `>=5R`. One
stop-only score is insufficient because information that removes stops may also
remove the right tail.

## Complete information matrix

Every decision receives only causally available observations:

1. same- and higher-timeframe FAST/STD/SLOW HA state;
2. static session/weekday/hour labels as negative controls;
3. continuous Tokyo, London, New York, broker-day, and broker-week phase;
4. exact distance to/from USD moderate/high events and released surprise only;
5. Asia, London-to-New-York, London-complete, and New-York-complete source-box
   break, extension, dwell, re-entry, settlement, and cross-box handoff paths;
6. latest completed D1 CRT Parent for H1 and H4 shadow Parent for M15;
7. internal M15 path for H1 and M5 path for M15;
8. lower-bar price-time distribution, median settlement, entropy, dispersion,
   directional mass, close density, and settlement location as Wave features.

## Comparisons

Ten frozen ablations run independently for H1 and M15: HA only; HA plus static
time, continuous clock, events, session path, CRT Parent, micro path, or Wave;
all time information; and the full assembly. Models use expanding walk-forward
folds, train-only encoding, and train-only regularization selection.

An information family passes only if mean test log loss improves versus HA-only
for both Hard SL and `>=5R`, with each outcome improving in at least two of
three folds. Capital views are diagnostic and must report stop density, net R,
right tail, total-stop-budget normalization, year, side, concentration, and
liquidity stability.

No result can create a session/news veto, long-only rule, threshold, sizing map,
EA, or trade authority. All data through `2026-09-18 23:57` are consumed;
GOLD# 2021 and later chronology remain sealed.
