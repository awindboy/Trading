# V12 Phase 1S — V10 weekly-journey direction contract

Status: **frozen before evaluation / consumed-development only**  
Frozen: `2026-09-25`

## Question

Can a continuous, causally known weekly journey state identify V10 Children
whose direction is unnecessary, reduce stopped exposure, and preserve enough
right-tail capital to improve equal-risk economics?

This is not a weekday filter, a named-session rule, or another M30 strategy.
The population is the frozen `1,649`-Child V10 R7G comparator. Every feature is
aligned to the proposed Child direction and is rebuilt from raw M1 strictly
before the V10 decision timestamp.

## Weekly state

The representation combines:

- prior-week direction, settlement, range, and current-week open displacement;
- which prior-week boundary was consumed first, whether price accepted outside
  it or returned inside, and favorable/adverse excursion in normalized units;
- completed-day, previous-day, Monday-range, and completed-H4 settlement inside
  the still-forming week;
- continuous position inside the week and day rather than weekday buckets;
- only already-released USD moderate/high event counts, surprise magnitude, and
  the price path after the latest event.

Normalization uses only prior completed broker weeks and days. Missing Monday or
event state remains missing information and is not backfilled.

## Frozen model and policies

Two fixed L2-logistic heads estimate `P(Hard SL)` and `P(Child R >= 2)`.
Directional badness is their difference. In each expanding walk-forward fold,
only the training population defines the top `20%` operating point.

The primary policy removes a flagged Child entirely. A secondary safety view
keeps one unit for every V10 Child and removes only the extra R7G units above one.
The latter distinguishes genuine directional discrimination from the mechanical
effect of lowering exposure.

The primary result must retain at least `80%` of Children, improve stopped units
per 100 by at least `15%`, retain at least `90%` of net R and >=5R right-tail R,
beat baseline R at equal stopped-unit budget, avoid negative R delta in at least
two of three folds, and improve both LONG and SHORT stop density while retaining
at least `80%` of each side's R.

## Evidence boundary

All observations are consumed development evidence. No model, score, threshold,
veto, or size has action authority. GOLD# 2021 and prices after
`2026-09-18 23:57` remain unread.
