# V8 Decisions Addendum — Persistence / Structural Retention — 2026-09-02

This file continues the V8 decision history after `D-V8-148` in `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`.

## D-V8-149 — Reclassify current Slow-N P15 as excursion/ONSET probability
The active `0.25 * previous-completed H4 ATR14 / P15` output is barrier-touch / excursion probability, not terminal net-displacement or persistence.

## D-V8-150 — Separate persistence from fresh-time ONSET features
Do not assume a second classifier on the same fresh-time 86-feature vector will solve persistence inside fresh75. Update after new causal price action appears.

## D-V8-151 — Reject simple reveal distance as a universal continuation law
Do not promote fixed-H4 or local-M1/M5 ATR reveal, nor extra M1-close dwell, as standalone momentum evidence. Equal-distance controls remain near chance.

## D-V8-152 — Reject blind pullback entry as acceptance evidence
25/40/50% pullback alone does not distinguish healthy retracement from reversal.

## D-V8-153 — Retain reveal -> pullback -> reclaim as the first causal ACCEPTANCE state
Primary family: 0.25 H4-ATR M1-close reveal <=15m, >=25% pullback with origin retained, then M1-close reclaim. 30m and 40/50% are robustness families. No exact pullback fraction is production-frozen.

## D-V8-154 — Downgrade the original PERSIST-A target-vs-failure result because of geometry
Distance-to-target and distance-to-failure explain much of the initial AUC. Do not claim it as pure persistence.

## D-V8-155 — Retain Structural Retention as the primary persistence question
After acceptance estimate `P(pullback extreme remains unbroken for 15/30/60m)`. Equality touch counts as break.

## D-V8-156 — Retain `micro3` as compact Structural Retention challenger
Use `prog1 + run + prog3` with regularized logistic regression. It is research-only.

## D-V8-157 — Structural Retention is structure-validity probability, not generic momentum
Never describe the score as `P(price keeps moving in this direction)`. Equal-distance continuation remains near chance.

## D-V8-158 — Downgrade later-rung PERSIST-B/C and reject universal rung-law claims
Later-rung path-only performance weakens after geometry control; pooled normalized rungs do not rescue 2025 late-rung behavior.

## D-V8-159 — Realized Structural Retention is a directional-extension state fact, not a frozen predictor
Actual retention materially enriches same-direction 0.75-ATR extension, but the current retention score alone does not predict same-side extension strongly.

## D-V8-160 — Do not freeze RETENTION-Q75 + EXT-Q75
Both-high cells are typically only ~3-10 events and unstable.

## D-V8-161 — Do not wait for full 15m retention confirmation as default entry
Roughly one third of confirmed-retention events have already reached the same-direction 0.75-ATR target before the full 15m label resolves.

## D-V8-162 — Reframe the candidate lifecycle
Every ONSET fresh opens a deterministic lifecycle:
`ONSET -> reveal -> pullback -> reclaim/ACCEPTANCE -> dynamic retention update -> later entry/holding`.
Immediate fresh-close position is no longer required. Hindsight abstention remains forbidden; timeout/no-reveal/no-acceptance/failure states must be causal.

## D-V8-163 — Next research is dynamic retention hazard + competing risk
Before exit optimization:
1. model 1/3/5/10/15m structural-retention hazard;
2. update after each completed M1;
3. model competing outcomes: structural break, same-side delivery, opposite-side delivery, unresolved;
4. keep equal-distance controls;
5. test V4-aligned raw tick incremental retention with shifted placebo;
6. study direction/regime interaction;
7. test BB-B only as acceptance/retention context;
8. freeze timing before payoff research.

## D-V8-164 — Keep EXT directionless until new evidence proves otherwise
Continue `0.75 H4 ATR P60/P120/P240` as movement-magnitude/horizon context. Simple micro3+EXT bridge is only modest/inconsistent for same-side delivery.

## D-V8-165 — Keep 2021 locked and all retention evidence developmental
All persistence/retention findings use consumed 2022-2026 development evidence. `GOLD# 2021` remains untouched.

## D-V8-166 — Treat reconstructed P0/P2 population as exact downstream authority
Per explicit project direction on 2026-09-03, the reconstructed current Slow-N 4-class P0/P2 population is the exact downstream authority. Small historical parity differences are not a blocker and must not be reopened unless a direct contradiction appears.

## D-V8-167 — Keep micro3 as acceptance-time prior, not repeated dynamic updater
Exact-population static retention remains positive, but after strong geometry/process control acceptance-time and current-time micro3 add approximately zero robust incremental break-hazard AUC. Do not build a repeated micro3 voter.

## D-V8-168 — Freeze dynamic hazard semantics as structural geometry/process state
Dynamic 0->1 / 1->3 / 3->5 / 5->10 / 10->15m hazard is mainly a function of current distance to the pullback extreme, nearest approach, path progress/MFE, acceptance geometry and lifecycle timing. High hazard AUC is structural-state discrimination, not directional alpha.

## D-V8-169 — Replace flat competing risk with hierarchical State A
Use `ACCEPTANCE alive -> BREAK / SAME75 / unresolved`, with `PRE_SAME75` separate. Opposite-side delivery is a post-break question because it is structurally nested behind failure.

## D-V8-170 — Add staged structural integrity states
Keep wick equality as the sensitive primary break label, but distinguish:
`PRISTINE = wick intact`,
`DAMAGED = wick breached but close integrity retained`,
`CLOSE_BROKEN = M1 close breaches the structural extreme`.
Do not treat a wick touch as automatic terminal invalidation.

## D-V8-171 — Do not interpret post-break as reversal
The break bar often closes back inside the structure, close-through repair vs further adverse move is approximately balanced, and equal-distance post-break direction is near chance. Break means structural damage, not automatic opposite-direction permission.

## D-V8-172 — Retain direction/regime interaction without permission rules
SHORT retention ranking remains materially stronger than LONG and quarter variation is real. Preserve these as interaction variables only; do not create SHORT-only or quarter-specific rules from consumed years.

## D-V8-173 — Keep raw tick fail-closed and BB-B secondary
Current raw-tick coverage fails predeclared gates (`83.853% aligned / 69.660% joint`). No tick evidence may be promoted. BB-B remains secondary context only, with no acceptance/retention gate frozen.

## D-V8-174 — Structural phase complete; open practical movement characterization, not economics optimization
The structural lifecycle is frozen enough to characterize MFE, current displacement, giveback, target-distance and hit-time distributions, large-winner continuation and structural-state conditioning. Explicit entry/SL/TP economics remain closed until that descriptive/causal mapping is complete and preregistered.

## D-V8-175 — Keep 2021 locked
The new dynamic structural-state evidence still uses only consumed 2022-2026 development evidence. `GOLD# 2021` remains untouched.

## D-V8-166 — Treat practical movement in S units as primary research scale
Use S-normalized movement for cross-regime research. Fixed GOLD points remain implementation/economic views because the same +10 points changes from roughly 0.84S in 2024 to roughly 0.23S in 2026.

## D-V8-167 — Separate available MFE from retained displacement
Large MFE is common while fixed-horizon terminal displacement is near zero. Do not use passive time holding as the default exit concept.

## D-V8-168 — Do not equate structural break with the final trading stop
A substantial fraction of eventual 0.50/0.75S winners experience wick and sometimes close damage before target. Structural invalidation and trade-stop economics must be tested separately.

## D-V8-169 — Retain close-intact + realized early MFE as the primary runner candidate
At 15m, within close-intact events, MFE15/S predicts future +0.50S with AUC roughly .657-.716 and future +0.75S roughly .745-.820 across P0/P2 2025/26.

## D-V8-170 — Freeze validation method, not the MFE threshold
2024-derived top-quartile MFE15 (~0.55S) materially enriches future large continuation in 2025/26, but Q75/~0.55S is not a production threshold. Future economics must not threshold-rescue it on consumed outcomes.

## D-V8-171 — Downgrade giveback ratio as standalone runner evidence
Current displacement/giveback is less stable than realized MFE for future large continuation. Do not create a giveback gate from current evidence.

## D-V8-172 — Open economics only through preregistration
Practical movement characterization is complete enough to open entry/risk/partial-profit/runner economics. Candidate architecture families and parameter ranges must be frozen before examining P/L. 2021 remains locked.

