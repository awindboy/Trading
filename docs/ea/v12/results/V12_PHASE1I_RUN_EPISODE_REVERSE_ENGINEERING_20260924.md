# V12 Phase-1I run-episode reverse-engineering result

Date: `2026-09-24`

Status: `COMPLETE AND REPRODUCIBLE / TRUE RUN-EPISODE REVERSE ENGINEERING / PRIMARY GATE FAILED / NO ACTION AUTHORITY`

Frozen contract commit: `f8e15f5`

## Question

Can the information already available at the first funded decision of a FAST
run distinguish another repeated-loss run from a tail-producing journey well
enough to remove a material amount of stopped exposure without destroying the
reason V10 earns money?

Unlike Phase 1H, the outcome unit is not a Child. Completed funded FAST runs are
first assigned retrospective economic roles, then the analysis returns to the
run's first actual-entry decision and uses only information known then.

## Reconstructed outcome universe

- Actual V10 entry Children: `1,409`.
- Funded FAST runs: `679`.
- Tail-journey runs: `57`.
- Stop-only runs: `181`.
- Neutral runs: `441`.
- Runs immediately following a prior funded stop-only run: `180`.
- Repeat stop-only runs in that state: `46`, carrying `115` stopped units.
- Strict adjacent-FAST repeats: `34`, carrying `86` stopped units.

All prior funded runs were resolved before the next run decision. Two independent
ten-file packs are byte-identical, all 51 V12 regression tests pass, and zero
post-cutoff price rows were parsed.

## Frozen policy result

Only runs following a known stop-only funded run could be changed. Every other
run remained identical to V10. Fold thresholds came only from training-run
predictions and were applied unchanged out of time.

| Pooled policy | Children | Stopped units | Stop/100 | Child win rate | Net R | Tail units |
|---|---:|---:|---:|---:|---:|---:|
| V10 baseline | 1,044 | 322 | 13.21 | 40.23% | 446.37 | 609.17 |
| Asymmetric Path+HA policy | 906 | 271 | 12.88 | 40.51% | 409.69 | 535.04 |
| Skip every run after a stop | 772 | 233 | 13.13 | 40.67% | 368.16 | 487.51 |
| Perfect repeat-stop oracle | 995 | 235 | **10.14** | **41.81%** | **534.52** | **609.17** |

The primary policy removes `58.6%` of repeated stopped units and `15.8%` of all
stopped units. But it also removes `13.2%` of Children, so normalized stopped
exposure barely changes: `13.21 -> 12.88` per 100 funded units. Child win rate
rises only `0.28` percentage points.

Tail-unit retention is `87.8%` pooled, but only `65.3%` in fold 1. That fold
loses one LONG tail run beginning `2025-04-09 08:00`, which alone contains
`60.97` tail units and `+74.26R`. The model correctly removes many repeated
losses but cannot recognize this rare, decisive journey.

At an equal stopped-unit budget, the primary policy produces `0.172R` per
baseline funded unit versus `0.183R` for V10. Increasing size therefore does
not repair the policy. The frozen tail-retention, win-rate, and equal-stop-budget
gates fail.

## Why this is not merely a threshold failure

The out-of-time heads are unstable:

| Head | F1 AUC | F2 AUC | F3 AUC |
|---|---:|---:|---:|
| Stop-only run, Path+HA | 0.776 | 0.583 | 0.658 |
| Tail-journey run, Path | 0.563 | 0.693 | 0.502 |

The stop side contains useful information, but the tail head is nearly random
in two folds. The after-stop reverse-engineering cohort contains only 11 tail
runs: one in F1, five in F2, and two in F3. Several coordinates have the same
descriptive sign across folds—London transition age, London/New-York settlement
and efficiency, elapsed time since the prior run, and STD alignment—but those
signs rest on too few tail examples and do not protect the large F1 journey.

Broad skip-after-stop is worse. It removes all repeat stops but retains only
`73.9%` of Children and `80.0%` of tail units; equal-stop-budget R falls to
`0.152`. This reproduces the prohibited cooldown failure directly.

## What the oracle establishes

The perfect oracle is not a strategy, but it bounds the opportunity. Removing
only repeat stop-only runs would:

- reduce stopped exposure from `13.21` to `10.14` per 100;
- preserve every tail journey and every tail unit;
- retain `95.3%` of Children;
- raise net R from `446.37` to `534.52`;
- raise child win rate by only `1.58` percentage points.

Therefore repeated-stop removal is economically valuable, but even perfect
removal of this narrow target cannot create a dramatic win-rate increase by
itself. Materially higher win rate would also require distinguishing some first
stop-only runs, without deleting the first entry into a journey.

## Decision and next reverse-engineering step

Reject the first-decision admission policy. Existing static Path, clock, prior-
run, and completed-H4 HA state does not reproduce the oracle.

Do not add another start-of-run indicator or tune a new score. The next useful
object is the causal formation timeline inside each run. For the fixed tail and
stop-only cohorts, reconstruct sequential M15/H1/H4 evidence from the first
entry until the first stop or tail-development milestone and ask:

1. when, if ever, the two cohorts first become distinguishable;
2. whether that separation occurs before meaningful stopped exposure;
3. whether a small initial probe followed by evidence-based risk release can
   preserve journey frequency while preventing second and third stopped units;
4. whether no usable separation exists before the outcome, in which case this
   objective is not identifiable from available price-derived information.

This is not permission to revive fixed k2 funding, arbitrary cooldown, or the
closed complete-feature-stack sequential model. The timeline must identify a
causal event, not merely a later bar number.

All chronology through `2026-09-18 23:57` remains consumed. GOLD# 2021 and
post-cutoff chronology remain sealed. Phase 1I grants no trade, veto, cooldown,
retry, capital, EA, or production authority.
