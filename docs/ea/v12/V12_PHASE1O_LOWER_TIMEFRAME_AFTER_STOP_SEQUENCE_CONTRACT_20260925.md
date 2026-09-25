# V12 Phase 1O — lower-timeframe after-stop sequence contract

Status: **frozen before evaluation / consumed-development only**  
Frozen: `2026-09-25`

## Why this phase exists

Phase 1N shows that H1 internal M15 formation and static time can separate many
stops from non-stops, but their low-risk bands are broad low-opportunity states:
they remove about 80% of candidates and nearly all right-tail capital. They do
not distinguish recurrent stops from isolated stops strongly enough.

Phase 1O therefore changes the question. It leaves every candidate outside the
after-stop cohort unchanged and asks only whether the next opposite H1/M15
`k=1` transition will repeat the causally completed prior stop.

## Frozen cohort and information

The conditional cohort contains a current `k=1` candidate only when the
immediate prior `k=1` outcome was available by the current decision and ended
at Hard SL. Causal history includes the previous one to three outcomes, prior
R, run length, holding time, stop streak, and flip cadence. These are combined
separately with HA, static time, continuous clocks, events, complete session
paths, internal M15/M5 path, and Wave coordinates.

Ridge history is the linear control. Fixed-parameter histogram gradient
boosting tests nonlinear interactions; no test outcome selects model depth,
learning rate, leaf count, or regularization.

## Evaluation and policy boundary

The two outcomes are current repeat Hard SL and current `>=5R` right tail.
Training rows require both their decision and current outcome label to be known
before the fold boundary. The only policy audit excludes the train-defined top
repeat-risk quintile inside the after-stop cohort. All other H1/M15 candidates
remain funded.

Success requires better repeat-stop log loss, at least 30% pooled and 20% per-
fold repeat-stop removal, at least 75% total participation, at least 90% pooled
and 80% per-fold right-tail-R retention, and at least 95% pooled equal-stop-
budget R with positive R in every fold.

This is not permission for cooldown, session/news veto, long-only selection,
combined-score tuning, or sizing. All chronology through `2026-09-18 23:57`
is consumed; GOLD# 2021 and later prices remain sealed.
