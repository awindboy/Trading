# V12 Phase 1M — H1 transition-Child contract

Status: **frozen before evaluation; consumed-development diagnostic only**  
Frozen: `2026-09-25`

## Question

Phase 1L showed that moving the whole repeated-HA architecture from H4 to H1
multiplies both opportunities and total stopped exposure without improving
quality enough. Phase 1M asks a narrower structural question: can an H1 FAST HA
transition be the Child event while H4 remains the Parent clock?

## Frozen lanes

- `H4_CORE`: Phase-1L H4 baseline.
- `H1_K1`: only the first positive HA after each opposite H1 FAST run.
- `H1_K1_H4_FAST_ALIGNED`: the same transition aligned with completed H4 FAST.
- `H1_K1_H4_FAST_STD_ALIGNED`: the same transition aligned with completed H4
  FAST and STD.

`k=1` is known at the decision timestamp. It is not a cooldown, retry limit, or
post-result selection. Entry, structural H1 STD stop, FAST exit, conservative
same-M1 handling, one-unit funding, common window, and source cutoff remain
identical to Phase 1L.

## Decision rule

The best H1 lane must be positive in at least four of five years, use no more
total stopped units than H4, retain at least `0.80x` H4 return after matching
the **total** stopped-unit budget, retain at least `0.90x` H4 profit factor and
`0.70x` H4 right-tail R per 100, and keep maximum stop streak within `1.50x` H4.

All observations through `2026-09-18 23:57` are consumed. This phase grants no
trade, sizing, or production authority.
