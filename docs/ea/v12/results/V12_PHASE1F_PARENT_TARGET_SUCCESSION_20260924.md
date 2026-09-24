# V12 Phase-1F Parent target-succession result

Date: `2026-09-24`

Status: `REPRODUCIBLE CONSUMED-DEVELOPMENT DIAGNOSTIC / TARGET-COMPLETENESS GATE REJECTED / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1f-parent-target-succession-v1`

## Scope and integrity

Phase 1F replaced Phase 1C's single immutable C1-opposite-edge test with a
causal rolling objective ledger. C1 midpoint and opposite edge came first;
later objectives were the nearest still-active same-direction price in the
existing one-use H4/day/week/month inventory. Replacements occurred only on a
later completed H4, and the directional progress frontier could not retreat.

The study changed no V10 entry, exit, Hard SL, or unit. It joined the frozen
Phase-1B, Phase-1C, and corrected Phase-1E packs and read no new price row. Two
independent builds produced all 13 files byte-identically. Complete-pack
validation and 41 regression tests pass.

The inventory contains `4,675` selected targets across `2,649` Parents;
`3,089` completed before Parent end. There were zero reframes without an
available target.

## Representation audit

| target kind | selected | completion rate | median completion time |
|---|---:|---:|---:|
| origin C1 midpoint | 1,493 | 57.27% | 0.60 h |
| origin C1 opposite edge | 402 | 45.52% | 1.88 h |
| external one-use cluster | 2,780 | 73.78% | 0.48 h |

The external inventory is too dense for the intended completeness question.
`2,551 / 2,780` external targets are previous-H4-only clusters, and every
external cluster contains a previous-H4 object. Median external distance at
selection is only `0.224 H4 ATR`; 1,311 of the 2,051 completed external targets
finish within one hour and 300 finish in the selection M1.

Consequently `TARGET_UNFINISHED` covers 1,422 of 1,499 V10 Children that have an
active Parent. All 118 Phase-1C carry-eligible Children, all 60 bridge episodes,
all 31 repairs, and all 35 H20 aligned pre-event Children are unfinished. The
rolling target therefore broadens the old 12-Child subset to the entire broad-
carry population instead of recognizing which bridge should be trusted.

The 77 `TARGET_COMPLETE_REFRAME_PENDING` Children are not a clean low-risk
state. All occur at broker hour 00; 66 are `ORDER_FAIL`, ten are
`EXIT_PENDING_BLOCK`, and only one is an ordinary `ENTRY`. Their apparent
`5.13` stopped units per 100 is mainly an execution-state mixture and cannot be
treated as strategy selectivity.

## V10 capital at the query time

| state | Children | funded units | stopped units / 100 | net R | >=5R right tail |
|---|---:|---:|---:|---:|---:|
| target unfinished | 1,422 | 3,356 | 12.84 | +683.69 | 892.35 |
| complete / reframe pending | 77 | 195 | 5.13 | +10.43 | 27.15 |
| no active Parent | 150 | 330 | 13.64 | +46.89 | 91.90 |

The state does not isolate the known bad H20 event interaction: every one of
its 35 Children remains unfinished, preserving `24.73` stopped units per 100,
`-13.85R`, and only `5.78R` of right tail.

At FAST flips, the rolling target is also saturated. All 490 flips for which
the old Parent remains active are unfinished, including the old-journey
counterflow population with a `46.94%` linked-k1 stop rate. Actual Parent
invalidation remains meaningfully distinct, but that distinction already came
from Phase 1B rather than target succession.

## Target kind is lifecycle context, not a solved gate

External-target Children look cleaner in the pooled ledger:

| current target kind | Children | stopped units / 100 | net R | >=5R right tail |
|---|---:|---:|---:|---:|
| external one-use cluster | 1,005 | 9.73 | +394.94 | 498.88 |
| origin C1 midpoint | 392 | 18.15 | +167.22 | 278.56 |
| origin C1 opposite edge | 102 | 18.98 | +131.96 | 142.07 |

This is not an external-liquidity veto. Relation and Child ordinal explain much
of the separation:

- aligned external-target Children have `9.01` stopped units per 100, while
  opposed external-target Children have `27.66` and still retain `+28.76R`;
- later aligned Children have only `4.42`–`7.41` stopped units per 100 across
  all three target kinds;
- among first aligned Children, external target is still lower at `12.67`
  versus `20.47` for midpoint and `22.14` for opposite edge, but it is not
  stable enough to act.

For first aligned external-target Children, journey-start external objectives
are almost entirely outside-acceptance Parents. High-outside-acceptance LONGs
produce `+113.24R` at `9.77` stopped units per 100, whereas low-outside-
acceptance SHORTs produce `-7.23R` at `14.46`. The attractive pooled result is
therefore partly the already-known CRT branch/side asymmetry, not evidence that
the nearest external price itself predicts success.

External succession after a completed target is also unstable: first aligned
Children stop at `23.64`, `10.84`, and `17.42` units per 100 in 2024, 2025, and
2026 respectively; 2024 net R is negative.

## Carry and repair consequence

Because all 118 carry Children remain `TARGET_UNFINISHED`, the new definition
reproduces broad Parent-active carry exactly: `+23.19R` delta but 26 added Hard
SLs and 66 added stopped units, with 2026 losing `40.18R` versus baseline.
It does not rescue the rejected Phase-1C holding rule.

Target kind does not supply a robust repair either. The 100 external-target
carry Children add only `+4.75R` while creating 19 Hard SLs; the ten opposite-
edge Children supply most of the remaining gain and are too sparse. All 31
repair k1s are still unfinished, so repair economics remain the unchanged
`+0.42R` over the ordinary exit clock.

## Decision

The Phase-1F target-completeness gate is rejected. A deterministic nearest
one-use target is reproducible, but previous-H4 levels make it nearly always
possible to tell an active Parent that it still has somewhere to go. That is a
description of market topology, not conviction.

Retained observations are narrower:

1. actual Parent invalidation remains different from counterflow;
2. origin-target versus external-target phase is a useful lifecycle coordinate;
3. the first aligned external-target population warrants conditional study,
   but only after controlling branch, side, first/later status, time, and event
   state;
4. the 35-Child H20 pre-event interaction survives unchanged and is not
   explained by target completeness.

No target state, target kind, family, carry, repair, session, weekday, or event
interaction receives action authority.

## Next boundary

Do not tune a minimum target distance or remove one family from this consumed
result. The next frozen study should treat `origin phase / external phase` as a
descriptive Parent lifecycle coordinate and ask whether FAST/STD/SLOW
disagreement plus Wave settlement adds incremental information inside the
already-frozen CRT flip meanings. It must control branch, side, first/later
Child, session, weekday, and the retained H20 event cell, and must report stop
capital and right tail together.
