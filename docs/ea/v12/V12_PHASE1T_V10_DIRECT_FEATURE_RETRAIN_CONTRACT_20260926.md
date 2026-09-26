# V12 Phase 1T — V10 direct feature-retraining contract

Status: **frozen before Phase-1T model evaluation / consumed-development only**
Frozen: `2026-09-26`

## Question

Can the continuous weekly clock, weekly price path, boundary-consumption state,
and already-released USD event response improve V10 when they are learned
inside the original R4/R5 heads rather than applied afterward as a veto?

This is a V10 component-interaction diagnostic inside the active V12 research
repository. It does not turn V10 entries into V12 CRT candidates, does not
replace the V12 assembly, and grants no action or sizing authority.

## Fixed comparison

The causal V10 universe is rebuilt from raw M1 through
`2026-08-28 23:57`. Every higher timeframe and weekly state is constructed
strictly before each decision. The fixed economic window is
`2024-10-01 00:00` through the last resolved V10 decision at
`2026-08-28 12:00`.

Four nested feature views are evaluated:

1. `V10_CONTROL`: the frozen head-specific V10 features;
2. `V10_WEEK_CLOCK`: continuous week/day phase only;
3. `V10_WEEK_PRICE`: clock plus weekly/day/H4 settlement and prior-week
   boundary-consumption path;
4. `V10_WEEK_PRICE_EVENT`: weekly price plus already-released USD
   moderate/high event response.

The primary comparison is `V10_WEEK_PRICE` versus `V10_CONTROL`. Event fields
are an incremental ablation because Phase 1S did not establish robust event
increment beyond weekly price.

## Frozen model assembly

- Each `k1/k2/k3+ x LONG/SHORT` R4 and R5 head retains its frozen model family,
  hyperparameters, recency weighting, original feature list, and random seed.
- Added fields are appended to that list. There is no new feature selection,
  model-family search, penalty scan, or operating-threshold scan.
- R4 retains its frozen quantile source. Previous-quarter, same-stage/direction
  q50 and q75 map the score to `0/1/3` units.
- R5 retains the hurdle form
  `EV = -P(STOP) + (1-P(STOP))*E[R|non-stop]`.
- R7G is rebuilt chronologically from each variant's changed R4/R5 eligibility;
  frozen historical weights are not reused.

Before any augmented economic claim, the refit control must match the pinned MT5
event ledger exactly on R4 actions, R5 EV sign, and R7G weights. Failure is
reported as a parity failure rather than hidden with a tolerance or threshold
change.

## Success gate

The primary weekly-price variant must retain at least `90%` of Children, net R,
and `>=5R` right-tail R; lower stopped units per 100 by at least `10%`; match or
beat baseline R at equal stopped-unit budget; not worsen maximum stop streak;
not worsen stop density on either side; and avoid a negative R delta in at least
two of the three calendar-year slices touched by the economic window.

All price observations are consumed development evidence. GOLD# 2021 remains
sealed, prices after the cutoff remain unread, and no score, feature block,
weight, or policy receives trade authority.

## Post-primary explanatory ablations

After the frozen all-head primary failed, four head-placement ablations were
added only to explain that failure: weekly price in R4 only, R5 STOP only, both
R5 heads, and weekly price/event in R5 STOP only. They cannot redefine the
primary gate, select a successor, or claim prospective validation.

The current Windows rebuild reproduces R4 exactly, but three historical
XGBoost STOP heads do not reproduce the Linux/MT5 reference exactly. This is a
declared platform parity limitation. Relative augmented-versus-control results
remain deterministic diagnostics inside one runtime; they are not exact MT5
replacement economics.
