# V12 Phase-1G continuous intraday path result

Date: `2026-09-24`

Status: `COMPLETE AND REPRODUCIBLE / PROMISING STOP-RISK REPRESENTATION / SUCCESS GATE NOT MET / NO ACTION AUTHORITY`

## Question

Can the continuous path from Asia through London and New York explain V10
stops better than named session, weekday, and event buckets, without discarding
the right tail? This phase is a correction to the discrete-cell framing in
Phases 1D/1E and the over-dense target inventory in Phase 1F.

## Causal universe

- Raw M1 rows revealed through cutoff: `1,669,073`.
- Post-cutoff price rows parsed: `0`.
- DST-aware completed source boxes: `4,868`.
- V10 context rows: `1,649`; actual `ENTRY` model rows: `1,409`.
- FAST flips: `2,234`; flips with linked k1 outcome: `2,101`.
- Unique bridge starts: `60`; confirmed repairs: `31`.
- Two independent 14-file packs are byte-identical and both pass full-pack
  validation.

At every query, the latest completed Asia range, London range frozen at New
York open, completed London range, and completed New York range are followed
minute by minute. The ledger records strict edge breaks, order ambiguity,
extension, close dwell, transitions, outside-to-inside repair, settlement,
cross-box handoff, and exact USD event distance. Raw prices are retained for
audit, but models receive only prior-60-day normalized or scale-free,
direction-symmetric coordinates.

## Primary out-of-time result

Metrics below are the unweighted mean of three frozen expanding-window test
folds. Lower Brier/log loss and higher AUC are better.

| Population / outcome | Model | Brier | Log loss | AUC |
|---|---:|---:|---:|---:|
| V10 Child stop | structure only | 0.1110 | 0.3747 | 0.6629 |
| V10 Child stop | static session/weekday/event | 0.1150 | 0.3840 | 0.6827 |
| V10 Child stop | continuous clock/event time | 0.1184 | 0.3947 | 0.6634 |
| V10 Child stop | full continuous path | **0.1067** | **0.3577** | **0.7320** |
| V10 `>=5R` presence | structure only | 0.0643 | 0.2534 | 0.5983 |
| V10 `>=5R` presence | continuous clock/event time | **0.0637** | **0.2484** | **0.6249** |
| V10 `>=5R` presence | full continuous path | 0.0648 | 0.2532 | 0.6150 |
| FAST-linked k1 stop | structure only | 0.1854 | 0.5573 | 0.6413 |
| FAST-linked k1 stop | full continuous path | **0.1835** | **0.5507** | **0.6660** |

The full path improved V10 stop Brier, log loss, and AUC on average. It also
improved all three stop metrics in folds 1 and 3, but fold 2 log loss worsened
from `0.3987` to `0.4126`. The right-tail head did not beat the continuous-time
control and its fold behavior is mixed. The frozen success boundary therefore
is **not met**.

## What carries the information

Mechanism-group ablation points to path state, not the session name:

- `settlement/repair` is the strongest compact stop group on average: V10 stop
  AUC `0.7235`; linked-k1 stop AUC `0.6738`.
- `boundary consumption` is next for V10 stops at AUC `0.7148`.
- cross-box handoff adds less (`0.6775`).
- exact event sequence is weak alone (`0.6223`) and does not support a generic
  news explanation or veto.
- no group is stable enough across all three folds to become a rule. Fold 2 is
  the recurring failure period.

The useful object is therefore not “New York is risky.” It is whether prior
ranges were breached on the favorable or opposed side, how far price extended,
how long closes remained outside, whether the boundary was repeatedly repaired,
and where settlement stands when the Child appears.

## Stop risk is not the same as bad capital

The highest predicted stop-risk quintile contains `128 / 322` stopped units,
but also `+135.99R` and `225.08R` of the `>=5R` right tail. A stop-only veto
would repeat the old failure: it would remove many losses and a disproportionate
share of the campaign payoff together.

As an exploratory, post-contract diagnostic, subtracting predicted stop risk
from predicted `>=5R` presence creates a relative conviction coordinate. Its
highest quintile is positive in every test fold:

| Conviction quintile | Funded units | Stopped units | Stop rate | Net R/unit |
|---|---:|---:|---:|---:|
| Q1 lowest | 462 | 108 | 23.38% | 0.285 |
| Q2 | 414 | 62 | 14.98% | 0.148 |
| Q3 | 486 | 84 | 17.28% | 0.078 |
| Q4 | 506 | 38 | 7.51% | 0.120 |
| Q5 highest | 570 | 30 | **5.26%** | **0.271** |

Q5 stop rates are `5.05%`, `5.86%`, and `4.67%` in the three folds. This is
the first consumed-data result aligned with the desired concept of confidence:
a frequent population with much lower stop burden that still earns positive
R in every test period. It is not a sizing result. The composite was inspected
after primary results, continuous-time alone creates much of the separation,
and Q1 still contains large right-tail episodes. No capital may be moved on this
evidence.

## What the representation cannot do

Predicting `log(1 + FAST run H4 bars)` fails. Mean out-of-time R2 is `0.0158`
for structure only and `-0.0155` for the full path. The path can describe
immediate whipsaw/stop vulnerability; it cannot tell how long the next journey
will run. Economic releases also do not become directional causes merely by
being close to a break.

## Decision

Retain Phase-1G as the first promising continuous-time stop-risk representation,
but do not convert it into a V10 veto, retry rule, or sizing map. The next phase
must freeze a compact conviction head before opening any further chronology:

1. use settlement/repair and boundary-consumption primitives, with continuous
   clock as a control;
2. jointly estimate stop burden and right-tail presence rather than optimizing
   either alone;
3. predeclare calibration, side/year/liquidity-era stability, and capital-
   retention gates;
4. test the frozen head on untouched chronology before any EA or MQL5 promotion.

All observations through `2026-09-18 23:57` remain consumed development
evidence. GOLD# 2021 remains sealed. Phase-1G has no trade, veto, exit, retry,
or sizing authority.
