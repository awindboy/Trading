# V12 Phase 1T — V10 direct feature-retraining result

Status: **complete deterministic diagnostic / primary failed / control platform parity limited / no action authority**
Date: `2026-09-26`

## What was tested

The frozen V10 R4 quantile score, R5 STOP probability, conditional non-stop R,
and R7G feedback chain were retrained directly with causal weekly clock, weekly
price path, boundary-consumption, and already-released event fields. Raw M1 was
streamed twice through the `2026-08-28 23:57` cutoff. All `6,770` weekly
snapshots end before their decision. The economic comparison covers `1,649`
selected V10 Children from `2024-10-01` through `2026-08-28 12:00`.

This is not a post-hoc veto. The added fields enter the original stage/direction
heads before R4 actions and R5/R7G sizing are recomputed. Model families,
hyperparameters, recency, score source, q50/q75 action mapping, and the 180-H4
feedback rule remain fixed.

## Control parity boundary

The rebuilt R4 score/action is exact: `2,839 / 2,839` actions match the supplied
MT5 event ledger and maximum score error is `5.0e-11`. Conditional-R and all
non-XGBoost STOP heads also match to numeric precision. The three XGBoost STOP
heads differ across the current Windows rebuild and the historical Linux/MT5
artifact: EV sign matches `2,817 / 2,839` and final R7G weight matches
`2,793 / 2,839`.

Therefore the pack is explicitly `CONTROL_PARITY_FAILED`. Augmented variants
are compared with the refit control inside one deterministic runtime, but are
not described as exact MT5 replacement economics. The supplied MT5 anchor
remains `1,649` Children, `3,881` units, `486` stopped units, `741.01R`, and
`285.10R` of >=5R tail.

Two independent 11-file output packs are byte-identical and both pass artifact,
causality, population, ablation, and declared-parity validation.

## Frozen primary result

| Refit policy | Children | Stop Children | Units | Stopped units | Stop/100 | Net R | >=5R tail | Max streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V10 control | 1,649 | 232 | 3,861 | 490 | 12.69 | 722.47 | 283.59 | 5 |
| Week clock, all heads | 1,642 | 219 | 3,786 | 459 | 12.12 | 534.28 | 235.29 | 5 |
| Week price, all heads | 1,561 | 214 | 3,665 | 466 | 12.71 | 421.89 | 163.06 | 5 |
| Week price + event, all heads | 1,553 | 214 | 3,563 | 452 | 12.69 | 349.74 | 163.06 | 5 |

The primary weekly-price model removes `88` Children and `18` stopped Children,
but stopped units fall only `4.90%` and stopped units per 100 slightly worsen.
Net R falls `41.60%`, >=5R tail falls `42.50%`, and equal-stop-budget R retains
only `61.40%` of control. Net R is lower in 2024, 2025, and 2026 and on both
sides. It passes only Child retention and maximum-streak gates among the
economic gates.

At equal one-unit participation, the same R4 selection change lowers stops from
`232` to `214`, but lowers net R from `284.37R` to `178.43R` and >=5R tail from
`126.89R` to `84.20R`. The damage is therefore not created only by R7G sizing.
The augmented R4 ranking replaces `317` baseline selections with `229` others;
the removed set contains `210.22` weighted R and `106.37R` of >=5R tail, while
the added set contributes `-33.34` weighted R and no >=5R tail.

## Head-placement explanation

| Explanatory ablation | Children | Stopped units | Net R | >=5R tail | Interpretation |
|---|---:|---:|---:|---:|---|
| Week price in R4 only | 1,561 | 490 | 399.76 | 175.90 | R4 ranking is the main destructive path |
| Week price in STOP only | 1,649 | 486 | 681.81 | 284.36 | four refit stopped units saved, 40.66R lost |
| Week price in both R5 heads | 1,649 | 492 | 714.36 | 267.10 | net R nearly retained, but stops and DD worsen |
| Week price + event in STOP only | 1,649 | 482 | 679.60 | 284.36 | eight refit stopped units saved, 42.87R lost |

Weekly information is genuinely predictive in the STOP head: mean annual AUC
improves from `0.7747` to `0.7849` and log loss from `0.4744` to `0.4652`.
However, it does not transfer into useful R7G allocation. STOP-only changes
only 172 Children's weights, saves four stopped units, and loses `40.66R`.
Adding event response saves eight stopped units but loses `42.87R`. The lift is
positive in 2024, mixed in 2025, and negative in 2026.

The primary reduces consecutive-stop Children from `64` to `57` and third-and-
later stops from `14` to `9`; repeat stopped units fall `146 -> 129` and deep-
chain units `36 -> 21`. Maximum streak remains five. This is measurable churn
reduction, but it is bought with much larger capital and tail loss.

## Decision

Do not add weekly clock, weekly price, or event blocks wholesale to the frozen
V10 heads. Do not promote the STOP-only ablations merely because their AUC is
better. They reproduce the same boundary seen in earlier V12 work: transition-
risk information is present, but high-risk states also contain the right-tail
capital that pays for V10.

The useful finding is architectural. R4's original HA/path ranking and the new
weekly state are not interchangeable feature dimensions. Weekly state should
remain a subordinate transition-risk coordinate inside a separately created
Parent/Child hypothesis; it should not compete directly with the original V10
features for broad action ranking or be mapped through the old `EV>0` R7G rule.
No Phase-1T score, feature block, or ablation has veto, sizing, trade, EA, or
production authority.
