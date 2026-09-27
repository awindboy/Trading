# V13 HA research roadmap status addendum

Date: `2026-09-27`
Base roadmap: `V13_HA_RESEARCH_ROADMAP_20260926.md`
GitHub base HEAD: `40f97352e47c66cd3b952f74532b1b71969e79fd`
Status: `HA-0..HA-6 CONSUMED / HA-7 FIRST ACTION REJECTED / HA-8A NEXT`

This addendum updates **stage status and resume order only**. The original
roadmap's stage definitions, stop conditions and research discipline remain in
force unless explicitly superseded below.

## Stage status

| Stage | Status | Authority consequence |
| --- | --- | --- |
| HA-0 | complete | standard-HA causal ledger established |
| HA-1 | complete | morphology informative; no action rule |
| HA-2 | complete | lag/giveback lifecycle mapped; no exit rule |
| HA-3 | complete | alternate representations descriptive only |
| HA-4 | complete | D1 weak; H1 informative but false-warning heavy |
| HA-5 | first fixed probe complete | raw swing adds context; no safe rule |
| HA-6A | complete | HASTOC retained as model feature candidate only |
| HA-6B | complete | MA regime/extension context only |
| HA-6C | complete | ATR useful as normalization only |
| HA-6D1 | complete / branch stop | ADX/DMI no action authority; SuperTrend not tested |
| HA-6E | complete | normalized tick participation contextual only |
| HA-7 | first action complete / rejected | no EA change; no threshold tuning |
| HA-8A | **next** | causal state-model baseline, observation only |

## Why HA-7 did not authorize further threshold search

The first frozen action removed 89 add-on Children and worsened both total net
points and realized-Journey drawdown. More importantly, 15 removed long-Journey
Children contributed +341.09 points. The failure is not solved by searching a
better volume threshold or Child index on the same consumed period.

## HA-8A objective

Test whether conditional combination of already-measured causal state can
separate true transition from temporary weakness better than the individual
warning families.

Preferred first target:

`P(opposite standard-H4 HA within next 3 completed H4 bars)`

The model stage does **not** alter trading behavior.

### Required baseline ladder

1. constant/base-rate;
2. simple single-family references (e.g. ordered H1 path, HASTOC alone);
3. regularized logistic regression;
4. shallow tree / small Random Forest only if justified;
5. boosted trees only after simple baselines;
6. no sequence/deep model until tabular behavior is understood.

### Validation

- chronological walk-forward/out-of-fold only on 2024-2026 consumed history;
- no random split as primary evidence;
- no in-sample score as strategy evidence;
- report calibration plus discrimination, not accuracy alone;
- preserve year/side/Journey-age and >=10-bar tail diagnostics;
- compare false-positive states specifically inside long Journeys;
- untouched future data is required before strong promotion;
- action mapping is a later, separately frozen experiment.

## Stop condition for HA-8A

Stop before action if the model:

- gains little over simple H1/HASTOC/state baselines;
- is poorly calibrated or unstable across chronological folds;
- improves aggregate metrics only by misclassifying long-Journey continuation;
- requires opaque complexity to recover tiny consumed-data gains;
- depends on post-hoc threshold selection.
