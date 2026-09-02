# V8 Research Instructions

Status: `ACTIVE / V8-A-N-SLOW ONSET + ACCEPTANCE + STRUCTURAL RETENTION`
Generation: `V8`
Last synchronized: `2026-09-02`
Production authority: `NONE`
Market: `GOLD#`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Base Git HEAD for this update: `cde7cfec1a6e07b872c72cdfaa62562c5e545735`

## 1. Current architecture
`ONSET (0.25 H4ATR P15 touch) -> actual reveal -> pullback -> reclaim/ACCEPTANCE -> dynamic STRUCTURAL RETENTION -> later entry/holding`.
EXT remains directionless `0.75 H4ATR P60/P120/P240`.

P15 is excursion probability, not terminal displacement/persistence.

## 2. Structural Retention authority
Primary family:
`fresh75 -> <=15m 0.25ATR M1-close reveal -> >=25% pullback with origin retained -> 0.25ATR M1-close reclaim`.

Label: pullback extreme remains unbroken for 15/30/60m.
`micro3 = prog1 + run + prog3`.

Future-year/phase AUC:
`15m .727-.754 / 30m .693-.725 / 60m .684-.726`.

Robust to bootstrap, permutation, overlap collapse, LONG/SHORT, quarters, 15/30m reveal and 25/40% pullback. 50% is weaker.

No threshold/model production authority.

## 3. Geometry control is mandatory
Any target-vs-failure claim must control `distance_to_target` and `distance_to_failure`.
Any directional persistence claim must include equal-distance barriers from the current state price.

Do not call origin-anchored ordering momentum without these controls.

## 4. Negative evidence
Do not rescue by threshold search:
- generic chart/MTF/M1 voters;
- static higher-horizon direction;
- simple ATR reveal momentum;
- blind pullback;
- extra dwell closes;
- equal-distance continuation after acceptance;
- initial PERSIST-A as pure persistence;
- PERSIST-B/C universal rung law;
- EXT as directional permission;
- Q75xQ75 retention/EXT gate.

## 5. Lifecycle objective
Every ONSET fresh opens a deterministic lifecycle.
Immediate fresh-close position is no longer required.
No hindsight abstention. Timeout/no-reveal/no-acceptance/failure must be causal.

## 6. Next order
1. dynamic 1/3/5/10/15m retention hazard;
2. competing-risk break/same-side/opposite-side/unresolved;
3. equal-distance controls;
4. full V4 raw ticks around reveal/retest/reclaim;
5. shifted placebo incremental tick test over micro3;
6. direction/regime interaction;
7. BB-B only as acceptance/retention context;
8. freeze lifecycle/entry timing before economics;
9. keep 2021 locked.

## 7. Legacy secondary hypotheses
BB-B: Phase0 N64 65.63%, Phase2 N63 65.08%.
relative0001: old/new overlap N45 66.67%, -10m placebo 45%. Full Slow-N tick coverage missing.

## 8. Indicator authority
Legacy and Slow-N P15 indicators remain research/shadow artifacts. Do not add retention trading behavior before dynamic-hazard semantics freeze. Future implementation must start shadow-only with non-interference and Python/MQL parity.

## 9. Reading order
1. `HANDOFF_V8.md`
2. `V8_A_N_SLOW_PERSISTENCE_RETENTION_RESEARCH_20260902.md`
3. `DECISIONS_V8_PERSISTENCE_RETENTION_ADDENDUM_20260902.md`
4. `V8_A_N_SLOW_HIGHER_HORIZON_EXTENSION_RESEARCH_20260902.md`
5. `V8_A_N_SLOW_DOWNSTREAM_REVALIDATION_RESULT_20260902.md`
6. `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`
7. `RESEARCH_STATE_V8.md`
8. `BACKLOG_V8.md`

Always refresh GitHub HEAD before continuing.
