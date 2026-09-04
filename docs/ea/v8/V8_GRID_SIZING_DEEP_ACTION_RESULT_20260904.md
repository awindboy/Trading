# V8 Grid Sizing and Deep-Action Exact-Tick Result

Date: `2026-09-04`  
Status: `2024 DEVELOPMENT EVIDENCE / STATIC SIZING AND SIMPLE DEEP-ACTION STAGE COMPLETE / NO PRODUCTION AUTHORITY`  
Market: `GOLD# ONLY`  
Source Git HEAD before this study: `ba28a16be6751178549eab5a623f14b5ded38778`  
Untouched reserve: `GOLD# 2021`

## 1. Purpose

Execute the preregistered sizing/deep-action stage:

1. compare fixed, decreasing and martingale tranche sizing under identical grid geometry;
2. compare causal `HOLD / REDUCE / EXIT / FLIP` after the third-fill deep-adverse state;
3. use exact 2024 Bid/Ask ticks for execution-sensitive results;
4. do not rescue failed branches by denominator shrinkage or threshold tuning.

## 2. P0 reproducibility correction

The prior synchronized documents listed P0 2024 fresh75 as `653`.

This study rebuilt the original Slow-N Phase-0 pipeline from the authoritative M1 source and reproduced:

- M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- 2024 model-evaluation population: exactly `67,956`;
- P15 AUC: approximately `0.81398` versus documented `0.813936`;
- reproducible old P0 2024 fresh75: `648`.

The user clarified that `653` had been promoted in the previous session after the old P0 could not be reproduced then. Since old P0 is now reproducible, the user explicitly authorized this execution study to proceed with `P0 2024 N=648`.

Therefore this study uses `648` as its exact-execution development population.

Do not silently merge `648` and `653`. This mismatch is now an explicit project fact. It does not automatically rewrite 2025/2026 historical counts.

## 3. 2025 exact-tick correction

The uploaded 2025 tick package is incomplete/sparse and cannot support full-year exact-tick validation.

Per user instruction, treat 2025 exact tick as unavailable.

Therefore:

- 2024 exact tick = development/replay authority for this stage;
- 2025 M1 = descriptive screening only if needed;
- no independent 2025 execution-validation claim is permitted;
- GOLD# 2021 remains untouched.

The older contract sentence saying 2025 exact tick is mandatory is superseded by this data-availability correction.

## 4. 2024 tick quality and coverage rule

2024 tick files contain approximately `51,063,932` rows.

Audit found:

- timestamp reversals: `0`;
- parsing failures: `0`;
- reconstructed `Ask < Bid`: `0`;
- very few exact duplicates;
- Bid-only / Ask-only records are incremental quote updates and were forward-filled from the prior quote state.

Known missing tick intervals exist, especially at some month boundaries. The user confirmed these gaps are known and instructed research to proceed.

Coverage rule used here:

- normal market closures are not missing coverage when M1 is also absent;
- when tick data are missing while authoritative M1 shows the market traded, a campaign crossing that interval is `CENSORED`;
- censored campaigns are excluded from completed-campaign P/L.

## 5. Execution semantics

Direction control:

- fixed causal 30-minute momentum hypothesis;
- no direction re-optimization during sizing.

Scale:

- `S = previous-completed H4 Wilder ATR14`.

Grid:

- entry 1: `0`;
- entry 2: `-0.4S`;
- entry 3: `-0.8S`;
- primary adverse boundary: `-1.2S`.

Execution:

- LONG entry/add: Ask;
- SHORT entry/add: Bid;
- LONG exit: Bid;
- SHORT exit: Ask;
- actual executable quote used as fill price;
- features end at the last completed M1 before decision time;
- execution starts at the decision timestamp.

To isolate sizing without inventing a missing historical runner-stop detail, the primary sizing comparison uses the unambiguous `+1.0S` immediate-exit control. This is an execution control only, not a final strategy payoff endorsement.

A minimal `+1S -> protect at entry -> +1.5S` variant was checked as robustness only. It is not promoted because the exact historical protection-stop semantics were not preserved in authority artifacts.

## 6. Analytic sizing geometry

| Schedule | Max units | Weighted BE after 3 fills | Rebound from -0.8S to BE | Loss at -1.2S | Gross RR vs +1.5S |
|---|---:|---:|---:|---:|---:|
| `1:1:1` | 3.00 | -0.400S | +0.400S | 2.40S | 0.625 |
| `1:0.5:0.25` | 1.75 | -0.229S | +0.571S | 1.70S | 0.882 |
| `1:0.5:0.5` | 2.00 | -0.300S | +0.500S | 1.80S | 0.833 |
| `1:0.25:0.25` | 1.50 | -0.200S | +0.600S | 1.50S | 1.000 |
| `1:2:4` | 7.00 | -0.571S | +0.229S | 4.40S | 0.341 |

Static trade-off:

- decreasing size cuts tail size but moves BE farther away;
- martingale moves BE closer but greatly increases tail exposure.

## 7. Same-boundary exact-tick sizing result

All schedules use the same `-1.2S` boundary and `+1S` execution control.

| Schedule | Completed | Censored | Direct TP | BE rescue | Hard loss | Mean $/campaign | Total $ | PF | Worst $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1:1:1` | 542 | 106 | 148 | 331 | 63 | **+0.053** | **+28.92** | **1.015** | -51.71 |
| `1:0.5:0.25` | 530 | 118 | 148 | 286 | 96 | -0.307 | -162.78 | 0.920 | -36.78 |
| `1:0.5:0.5` | 532 | 116 | 148 | 294 | 90 | -0.237 | -126.12 | 0.937 | -38.89 |
| `1:0.25:0.25` | 524 | 124 | 148 | 262 | 114 | -0.515 | -269.67 | 0.874 | -33.00 |
| `1:2:4` | 555 | 93 | 148 | 367 | 40 | -0.331 | -183.54 | 0.914 | -94.23 |

Pairwise complete-event deltas versus fixed:

| Variant | Pair N | Variant - Fixed mean $ | Total delta $ |
|---|---:|---:|---:|
| `1:0.5:0.25` | 530 | -0.360 | -190.86 |
| `1:0.5:0.5` | 532 | -0.290 | -154.40 |
| `1:0.25:0.25` | 524 | -0.568 | -297.44 |
| `1:2:4` | 542 | -0.397 | -215.02 |

On a same-complete 524-event diagnostic subset:

- fixed direct TP average: about `+$12.52`;
- fixed hard-loss average: about `-$29.63`;
- fixed hard-loss total: about `-$1,866.53`;
- fixed worst: `-$51.71`.

`1:0.25:0.25` reduces hard-loss average to about `-$18.80` and worst to `-$33.00`, but hard-loss count rises materially because weighted BE is farther away.

`1:2:4` increases BE rescues and reduces hard-loss count, but average hard loss is about `-$53.56`, worst is `-$94.23`, and one average hard loss erases roughly four normal +1S direct winners.

Conclusion:

> Static size alone does not solve the campaign payoff problem. Decreasing schedules lose too many rescues; martingale buys rescue probability with unacceptable tail size.

## 8. Equal-risk-boundary extension

After the required same-geometry comparison, an outcome-blind extension equalized gross basket risk to the fixed control's `2.4S`.

Analytic boundaries:

- `1:1:1 -> -1.2S`;
- `1:0.5:0.25 -> -1.6S`;
- `1:0.5:0.5 -> -1.5S`;
- `1:0.25:0.25 -> -1.8S`;
- `1:2:4 -> about -0.914S`.

Raw per-schedule completed means became superficially positive for several decreasing variants, but completion/censor rates changed materially. Pairwise complete-event comparison still favored fixed:

| Variant | Pair N | Fixed mean $ | Variant mean $ | Variant - Fixed mean $ |
|---|---:|---:|---:|---:|
| `1:0.5:0.25 @ -1.6S` | 506 | +1.016 | +0.198 | -0.818 |
| `1:0.5:0.5 @ -1.5S` | 515 | +0.884 | +0.143 | -0.741 |
| `1:0.25:0.25 @ -1.8S` | 483 | +1.472 | +0.365 | -1.107 |
| `1:2:4 @ -0.914S` | 542 | +0.053 | -0.640 | -0.693 |

Interpretation:

> Raw positive decreasing results were materially influenced by schedule-dependent censoring. Do not promote them.

Wider `-1.5S` to `-1.8S` boundaries also risk reopening the rejected multi-hour mean-reversion drift.

## 9. Deep-state action definitions

Fixed `1:1:1` produced 143 campaigns that reached the third-fill deep state before any gap censor. 133 had completed HOLD outcomes. The fully common subset across the first action definitions was 103.

Actions were fixed before replay:

- `HOLD`: keep full basket to weighted BE or -1.2S hard boundary;
- `REDUCE_LATEST`: close third unit, retain first two, no further adds;
- `REDUCE_HALF_ALL`: close 50% of all three units proportionally;
- `EXIT`: close full basket immediately;
- `FLIP`: close basket and open one opposite unit, TP +1.5S, SL -0.4S, protect at flip entry after +1S, no re-entry.

## 10. Unconditional deep-state action result

Common action-complete `N=103`:

| Action | Mean final campaign $ | Mean Q from deep state $ | Increment vs HOLD $/event |
|---|---:|---:|---:|
| HOLD | **-10.295** | **+5.023** | 0 |
| REDUCE_LATEST | -14.035 | +1.282 | -3.740 |
| REDUCE_HALF_ALL | -12.806 | +2.511 | -2.511 |
| EXIT | -15.317 | 0.000 | -5.023 |
| FLIP | -16.704 | -1.387 | -6.410 |

Key result:

> Reaching -0.8S does not mean the original direction should be abandoned. HOLD still recovers substantial expected value from the current mark-to-market state.

## 11. Five-minute causal action study

For campaigns still unresolved 5 minutes after the third fill, causal features included:

- elapsed time from fresh75 to deep state;
- second-to-third fill time;
- signed progress at 1m / 3m / 5m;
- minimum/maximum signed progress observed only through the first 5 minutes.

### Invalidated intermediate run

The first implementation accidentally continued updating `xmin/xmax` after the 5-minute decision time. This leaked future path and produced false AUC around 0.98. The result was immediately invalidated.

After fixing the boundary:

- compact hard-loss AUC on H1->H2: about `0.69`;
- an encouraging single H1->H2 EXIT result appeared;
- expanding-quarter walk-forward reversed in Q4.

Expanding-quarter aggregate action deltas:

- EXIT: about `-$15.96`;
- proportional half reduction: about `-$7.98`;
- latest-tranche reduction: about `-$79.58`;
- FLIP: about `-$15.68`.

No 5-minute model is promoted.

## 12. Price-triggered adverse continuation actions

To remove arbitrary clock timing, action was also tested at first causal reach of `-0.9S`, `-1.0S`, and `-1.1S` after the third fill.

EXIT incremental value versus HOLD:

| Trigger | Pair N | EXIT - HOLD mean $ |
|---|---:|---:|
| -0.9S | 114 | -2.241 |
| -1.0S | 99 | -3.682 |
| -1.1S | 88 | -5.200 |

REDUCE and FLIP were negative at all three levels.

At `-1.1S`, EXIT improved the individual outcome in roughly 72% of cases, yet average dollar value was still worse than HOLD.

Therefore:

> Hard-loss probability is not the action target. Remaining BE-recovery upside versus remaining hard-boundary downside determines action EV.

## 13. Conditional temporary hedge experiment

A new mechanism then preserved the original basket instead of abandoning it:

1. retain full `1:1:1` basket;
2. after third fill, on first reach of `-1.0S`, open one opposite unit;
3. close hedge for profit at original `-1.2S` hard boundary;
4. close hedge for loss on rebound to `-0.8S`;
5. single use; no re-entry;
6. original basket continues unchanged.

Exact tick on completed fixed-control campaigns:

- completed: 542;
- hedge triggered: 88;
- hedge profit cases: 49;
- hedge loss cases: 39;
- actual hedge total: `-$9.82`;
- base mean: `+$0.053/campaign`;
- hedged mean: `+$0.035/campaign`.

Same-path ideal zero-spread diagnostic:

- theoretical hedge total: `+$21.94`;
- actual Bid/Ask total: `-$9.82`;
- friction difference: about `-$31.76`.

Interpretation:

> The conditional hedge has a small gross structural edge, but the margin is too thin to survive actual Bid/Ask friction. This is not a strong edge destroyed by spread.

## 14. Main conclusions

### Static sizing

No tested static schedule improves fixed robustly.

- decreasing size reduces individual hard-loss magnitude but loses too many BE rescues;
- martingale increases rescue frequency but creates an unacceptable tail;
- equal-risk wider boundaries fail pairwise comparison and risk horizon drift.

### Deep-state action

The deep state contains more information than fresh75 direction, but current causal information is not sufficient for a robust action policy.

- unconditional REDUCE / EXIT / FLIP fail;
- 5-minute compact models are not walk-forward stable;
- direct adverse-threshold actions fail in dollar EV;
- single-use temporary hedge is slightly negative after actual execution.

### Current control

Fixed `1:1:1` remains the best tested static economic control for this stage, but its strict-gap +1S control edge is extremely thin:

- mean about `+$0.053/campaign`;
- PF about `1.015`.

This is not sufficient for production and does not satisfy the final payoff objective.

## 15. Research decision

Do not continue threshold rescue inside this static-grid family.

Downgrade/reject for the tested geometry:

- static decreasing sizing as a standalone fix;
- martingale `1:2:4`;
- unconditional deep-state REDUCE / EXIT / FLIP;
- fixed 5-minute compact action model;
- simple `-0.9/-1.0/-1.1S` intervention thresholds;
- single-use `-1.0S` one-unit temporary hedge.

Preserve:

- fixed `1:1:1` only as the current development control;
- deep-state path information as a diagnostic state;
- action-EV framing;
- the lesson that recovery payoff asymmetry dominates raw hard-loss probability.

## 16. Next research direction

The next mechanism must change the payoff shape more fundamentally rather than run another threshold tournament on HOLD/EXIT.

Research question:

> Can a state-contingent exposure transformation preserve most normal-rotation recovery value while creating materially stronger convex payoff against genuine opposite continuation than the failed one-unit hedge?

Any new branch must be preregistered before opening P/L and must report both same-path zero-cost and actual Bid/Ask economics.

Do not touch GOLD# 2021.

## 17. Production status

`NONE`
