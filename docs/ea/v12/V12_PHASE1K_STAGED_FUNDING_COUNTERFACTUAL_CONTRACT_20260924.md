# V12 Phase 1K — Staged-funding counterfactual contract

Status: **frozen before evaluation; consumed-development capital audit only**  
Frozen: `2026-09-24`

Phase 1J found stable early post-entry progression/damage separation. Phase 1K
does not tune its values. It asks whether three literal event policies improve
the existing V10 Child portfolio.

## Population

Use all `679` Phase 1I funded FAST runs and their `1,409` actual-entry Children.
Entry, Hard SL, exit, and realized outcome remain unchanged. The first Child of
every run is always funded.

For every later Child, only an M15 event whose bar completed no later than that
Child's actual entry time is known. A skipped Child is never backfilled.

## Policies

- `BASELINE`: retain all original Children.
- `PROGRESSION_RELEASE`: release later Children only after two consecutive
  favorable M15 closes.
- `DAMAGE_STOP`: release later Children until two consecutive opposed M15 closes
  have occurred, then stop adding.
- `PROGRESSION_OR_REPAIRED_DEPARTURE`: release later Children after either
  favorable persistence or repaired departure.
- `FIRST_CHILD_ONLY`: broad exposure-reduction comparator.

There is no numeric threshold search. `PROGRESSION_RELEASE` is primary because
it implements demonstrated favorable business before extra exposure.

## Required judgment

Stopped units, repeat stopped units, funded exposure, Child win rate, tail
units, tail-journey participation, raw R, and equal-stop-budget R are evaluated
together by test fold. A policy that removes stops and tail in roughly the same
proportion is not an improvement.

All evidence remains consumed development history. No result grants entry,
funding, sizing, exit, or production authority. GOLD# 2021 and post-cutoff
chronology remain sealed.
