# V12 Phase 1L — H1 main-timeframe feasibility

Status: **complete, reproducible, failed viability gate**  
Evidence: consumed development history through `2026-09-18 23:57`  
Authority: diagnostic only; no trade or sizing authority

## Result

Moving the repeated HA Child clock from H4 to H1 does not improve funded quality.

| lane | Children | stops / 100 | win rate | R / unit | PF | equal-total-stop-budget R / H4 unit |
|---|---:|---:|---:|---:|---:|---:|
| H4 core | 6,857 | 26.28 | 32.27% | 0.0557 | 1.139 | 0.0557 |
| H1 core | 26,881 | 26.20 | 32.53% | 0.0243 | 1.060 | 0.0244 |
| H1 + H4 FAST | 15,184 | 24.70 | 32.64% | 0.0269 | 1.069 | 0.0286 |
| H1 + H4 FAST/STD | 13,267 | 24.33 | 32.88% | 0.0363 | 1.094 | 0.0392 |

H1 core creates `3.92x` as many Children and `3.91x` as many stopped units,
while stop density and win rate are nearly unchanged. Once total stopped units
are matched, it retains only `43.8%` of H4 R per baseline unit. It is negative
in 2024 and 2026, so the frozen `4 / 5` positive-year requirement also fails.

Completed-H4 FAST/STD alignment is the cleanest predeclared comparator. It
reduces stop density by `7.4%` and is positive in four years, but retains only
`70.4%` of H4 equal-total-stop-budget R. It does not justify replacing H4.

## New dimensions

Three threshold-free univariate screens pass:

- M15 directional net / H1 ATR versus Hard SL: oriented AUC `0.605`;
- M15 HA body efficiency versus Hard SL: oriented AUC `0.601`;
- M15 directional net / H1 ATR versus `>=5R`: oriented AUC `0.619`.

The directional-net relation points in the same raw direction for both targets:
stronger already-completed movement is associated with fewer immediate stops
but also fewer later `>=5R` outcomes. It is a competing-outcome coordinate, not
a free stop filter. No threshold, veto, score, or model was fitted.

## Integrity

- The rebuilt H4 engine matches all `6,770` historical V10 rows: entry max
  difference `0`, stop difference below `1e-9`, R difference below `1e-12`, and
  zero stop-label mismatches.
- Two independent eight-file packs are byte-identical.
- All V12 tests pass (`62`); complete-pack validation passes.
- No post-cutoff price row was parsed; GOLD# 2021 remains sealed.

## Decision

Reject a whole-base H1 HA substitution. Retain H1/M15 only as subordinate Child
and path clocks under a separately defined Parent. Do not tune M15 thresholds
to rescue this consumed result.
