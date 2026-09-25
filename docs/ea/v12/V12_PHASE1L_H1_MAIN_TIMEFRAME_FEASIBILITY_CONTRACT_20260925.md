# V12 Phase 1L — H1 main-timeframe feasibility contract

Status: **frozen before evaluation; consumed-development diagnostic only**  
Frozen: `2026-09-25`

## Decision

Decide whether H1 deserves a new V12 Child architecture. More signals or more
R are not sufficient. H1 must retain acceptable stop density, equal-stop-budget
economics, right-tail production, and year/side stability.

## Frozen lanes

All lanes are rebuilt from the same chronological raw-M1 prefix.

- `H4_CORE`: the V10 FAST/STD/SLOW HA Child semantics with one unit and without
  historical R4/R5/R7G selection.
- `H1_CORE`: the exact same semantics moved to H1.
- `H1_H4_FAST_ALIGNED`: H1 rows aligned to the latest completed H4 FAST HA.
- `H1_H4_FAST_STD_ALIGNED`: H1 rows aligned to completed H4 FAST and STD HA.

The H4-aligned lanes are transparent architecture comparators, not optimized
filters. The common analysis window begins only after both timeframes have the
same 180-bar warmup requirement satisfied.

## Child semantics

- Enter at the first causal M1 open after the completed main-timeframe bar.
- Set the Hard SL to the previous completed main-timeframe STD HA low for LONG
  or high for SHORT.
- Exit at the first opposite completed FAST HA decision open.
- A same-M1 stop/FAST-exit collision uses the conservative stop as primary and
  records the alternative.
- Every Child is one unit. Stops are never widened.

## New information dimensions

At every H1 decision, record without action authority:

- latest completed H4 FAST/STD/SLOW alignment and H4 run age;
- the four completed M15 FAST HA bars inside the H1 bar: aligned fraction,
  directional net/ATR, path efficiency, transitions, and body efficiency;
- continuous broker-day and broker-week sine/cosine coordinates.

This phase measures univariate stop/tail discrimination only. It does not fit a
threshold, score, model, session veto, or position map.

## Success and guardrails

Primary KPIs are stopped units per 100 funded, net R per unit, and equal-stop-
budget net R versus H4. Guardrails include win rate, R-profit factor, maximum
stop streak, concurrent exposure, `>=5R` tail production, tail concentration,
year/side stability, and same-M1 ambiguity.

H1 is only viable for deeper work if it is positive in at least four of five
years, stop density is no more than `1.50x` H4, equal-stop-budget R/unit is at
least `0.80x` H4, PF is at least `0.90x` H4, and maximum stop streak is no more
than `2x` H4.

All observations through `2026-09-18 23:57` are consumed. GOLD# 2021 and later
chronology remain sealed. No result has trade or sizing authority.
