# V13 handoff

Last synchronized: `2026-09-28`
Status: `HA-9 BREAKTHROUGH CANDIDATE / RESEARCH EA READY / ACTUAL-TICK VALIDATION NEXT`
Base GitHub `main`: `29e0073e57553d8fe1fd14b843daf09164a7a248`

## Resume point

V13 Baseline 0 remains the frozen comparator. HA-7 was rejected; HA-8A and X1/X2
were useful negative observations but did not solve the economic loss problem.
The research objective has since been clarified: prioritize reduction of ordinary
losing Children and improvement of the typical equity path; do not automatically
reject a candidate because it cuts large continuation winners.

Read `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md` before interpreting old
right-tail language.

## Current breakthrough candidate — HA-9

Child #1 remains Baseline 0. For add-ons only:

```text
enter normally after same-color signal H4
  -> one-H4 proof window
  -> LONG must break signal-H4 raw HIGH
     SHORT must break signal-H4 raw LOW

if proof:
  lock = max(entry, signal high) LONG
       or min(entry, signal low) SHORT
  lock active only after proof observation

if no proof by next H4 boundary:
  close that add-on Child
```

Early closure does not end the Journey and does not backfill the Child number.

## Verified consumed-data result

```text
structural comparator:
  965 closed Journeys
  3,858 closed Children
  Baseline +8,147.11 points

HA-9:
  losses 2,427 -> 1,685 (-742 / -30.6%)
  wins   1,430 -> 2,151
  non-flat win rate 37.08% -> 56.07%
  trade-sequence DD 3,756.99 -> 1,283.65
  max consecutive losses 25 -> 14
  net +3,946.06 / PF 1.17634
```

Year net:

```text
2024 +37.15
2025 +1,867.48
2026 +2,041.43
```

Top profitable Journey removal:

```text
remove top 5:  Baseline -1,504.63 / HA-9 +1,426.97
remove top 10: Baseline -5,785.30 / HA-9    +74.26
```

This is the first V13 candidate that materially improves the ordinary Child
stream instead of merely predicting HA reversal better.

## What changed about right-tail interpretation

Old HA-7/HA-8 evidence that some warnings hit huge winners remains true. It no
longer controls the research objective. Current rule:

> report tail cost, but judge the candidate first on loss reduction, win rate,
> loss streaks, ordinary block quality, drawdown and trimmed robustness.

Do not delete or rewrite frozen historical contracts to pretend this objective
always existed.

## Immediate next work

1. MetaEditor compile `mt5/experts/V13HAProofLockMax10EA.mq5`.
2. Run `Every tick based on real ticks`, canonical 2024-01-01..2026-08-28.
3. Verify proof/timeout/lock event timing against
   `research/v13/ha9_addon_proof_lock_audit.py`.
4. Produce actual-tick receipt with the revised quality metrics.
5. If actual-tick parity holds, decompose the remaining 1,685 losing Children;
   do not return immediately to broad indicator or ML feature stacking.

## Do not resume with

- optimizing proof duration or an ATR offset on this consumed sample;
- adding HASTOC/EMA/ADX/volume/XGBoost to HA-9 before execution parity;
- treating total net reduction alone as failure;
- treating any touched large Journey as automatic failure;
- adding side/year exceptions from the current sample;
- changing Child #1 before the add-on mechanism is validated in actual ticks.
