# V8 Research Instructions

Status: `ACTIVE / GOLD P15 + ATR GRID DIRECTION-ERROR ABSORBER`
Generation: `V8`
Last synchronized: `2026-09-04`
Production authority: `NONE`
Market: `GOLD# ONLY`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Source Git HEAD verified before this synchronization: `bbe30f7d23d13def712ad53117df9e8bc42a5e2e`

## 1. Authority

GitHub is the permanent project authority.

On resume:

1. refresh Git HEAD;
2. read `HANDOFF_V8.md`;
3. read `RESEARCH_STATE_V8.md`;
4. read the research/decision files named by HANDOFF;
5. do not rely on conversation memory over newer GitHub state.

## 2. Hard scope

Until the user explicitly reopens scope:

- GOLD# only;
- no other markets;
- no market-universe screening;
- no GOLD# 2021;
- no production authority.

P0 and P2 are alternate deterministic training de-overlap realizations.

Never merge them as independent trades.

## 3. Stable semantic separation

Never silently merge these concepts:

- movement onset;
- initial direction viability;
- structural survival;
- normal adverse rotation;
- opposite one-way continuation;
- winner continuation;
- entry;
- staged exposure;
- rescue;
- exit;
- execution;
- cost;
- capital allocation.

Permanent reminders:

    P15 movement opportunity != direction edge
    retention != movement
    high AUC != profitable action
    BE recovery != direction continuation
    MFE != capturable P/L
    structural damage != automatic stop
    campaign RR != first-entry TP/SL distance

## 4. P15 time-scale guardrail

P15 is a near-term movement/excursion probability model.

Do not silently transform it into a multi-hour trend predictor.

ATR-grid research is allowed to use staged positions to absorb initial direction error, but it must remain conceptually connected to the V8 movement event unless a separate longer-horizon hypothesis is preregistered and validated.

Do not repeat the research drift from micro-grid candle slicing to 3-24h unrelated mean-reversion without explicitly declaring a new strategy.

## 5. Current working architecture

The current research architecture is:

    P15 fresh75
    -> weak initial direction hypothesis
    -> ATR-scaled staged exposure
    -> normal rotation may rescue at weighted BE
    -> directional progress milestone protects winner
    -> genuine opposite continuation should trigger reduction / exit / flip
    -> validated continuation may justify a separate runner/add tranche

This is a research scaffold, not a frozen strategy.

## 6. P15 / ACCEPTANCE / High-Q authority

P15 remains movement opportunity, not direction.

ACCEPTANCE remains a structural state transition, not direct direction permission.

micro3 remains a structural-retention quality prior.

PRISTINE / DAMAGED / CLOSE_BROKEN remain structural/hazard states.

High-Q remains sparse positive continuation evidence.

Do not repurpose a model from one semantic layer into another merely because it has a high score.

## 7. Direction-research status

The following direct direction families have already failed or remained unstable:

- fresh75 direct LONG/SHORT action EV;
- reveal FOLLOW / FADE;
- every-M1 EV;
- rolling EV;
- direct P(win) x payoff;
- probability sizing;
- micro first-touch;
- stop-and-reverse;
- synthetic straddle;
- continuous M1 trend following.

Do not rescue them by fine threshold search.

A genuinely new directional mechanism may reopen the question.

## 8. Trade-frequency guardrail

Do not solve poor economics by repeatedly narrowing the population.

For every candidate report:

- original denominator;
- selected N;
- excluded N;
- unique campaigns;
- tickets/tranches;
- campaign coverage;
- year split.

A profitable 5-10% subset is a state/component, not automatically the final strategy.

## 9. M1 versus exact tick

Grid and multi-fill strategies are intrabar-order sensitive.

M1 is appropriate for:

- broad family screening;
- geometry;
- state characterization;
- descriptive hazard research.

Exact tick is mandatory for:

- execution P/L;
- fill chronology;
- weighted-average chronology;
- BE chronology;
- Bid/Ask;
- same-minute conflict resolution.

Never infer add-before-exit or exit-before-add from M1 OHLC without explicit conservative/favorable sensitivity.

## 10. Tick coverage

For every exact-tick dataset:

- verify period;
- timezone;
- timestamp precision;
- Bid/Ask;
- duplicates;
- month/file boundaries;
- missing intervals.

Campaigns crossing missing coverage are right-censored/incomplete.

Never force them into win/loss.

## 11. Causal timing

Every feature must have an explicit `known_at`.

For a decision stamped `15:35` whose origin is 15:34 close:

    legal feature cutoff = 15:34 close
    earliest execution = 15:35

Do not allow the 15:35 M1 into the feature vector.

A 1-minute look-ahead occurred once in this research and all affected results were invalidated.

This error must never recur.

## 12. Spread analysis

Do not say "spread killed the edge" without decomposition.

Required when spread is material:

- exact actual-spread replay;
- same tick path with zero spread;
- difference in direct cost;
- difference in outcome classification;
- actual-dollar effect.

A strategy that is only breakeven at zero spread does not have a strong edge destroyed by the broker.

## 13. Actual-dollar reporting

R remains useful for normalization, but the user requires actual economic scale.

Every grid report must include actual dollars for the chosen reference lot.

Minimum categories:

- direct/protected TP;
- grid-before-winner if present;
- BE rescue;
- early cut;
- flip winner;
- hard loss;
- timeout/censored if any.

For each category report:

- N;
- rate;
- average dollars;
- total dollars.

Also report:

- total campaigns;
- completed / censored;
- mean dollars per campaign;
- total dollars;
- PF;
- max campaign loss;
- tail contribution;
- lot schedule.

## 14. Direction accuracy reporting

If direction accuracy is reported, define the target exactly.

If the "correct direction" uses future first-touch or future +1.5S outcome, label it:

`DIAGNOSTIC / NONCAUSAL`

Do not present it as a tradable classifier.

If a causal direction model is used, report:

- training window;
- validation window;
- known_at;
- N;
- accuracy/AUC;
- actual trade economics.

## 15. ATR-grid scale

Do not repeat the `0.08S` micro-grid drift unless deliberately testing execution-noise behavior.

The active grid should represent meaningful ATR-scaled adverse movement, not M1 candle slicing.

But do not jump to multi-hour spacing/horizons merely to raise BE recovery.

The grid must solve the original V8 problem, not create a different strategy.

## 16. BE semantics

Weighted BE is primarily a rescue level.

BE touch does not prove the original direction has restarted.

Default behavior after rescue must not assume continuation.

If continuation is traded after BE, require independent causal evidence and evaluate it as a separate action/tranche.

## 17. Progress / TP semantics

`+1S` is currently treated as meaningful directional progress, not automatically the final TP.

The active protected-runner reference is around `+1.5S`, because that is roughly one H4 ATR-scale move and is economically more meaningful.

Do not increase TP merely to improve backtest payoff.

Any runner extension must be supported by continuation evidence.

## 18. Campaign RR

Always calculate risk over all filled tranches.

Example current equal-size scaffold:

    entry 1 = 0
    entry 2 = -0.4S
    entry 3 = -0.8S
    hard boundary = -1.2S

Equal `1:1:1` basket loss:

    1.2 + 0.8 + 0.4 = 2.4S

A +1.5S single initial-unit winner therefore has gross campaign reward/risk 0.625.

Never report RR from first-entry price distance alone.

## 19. Sizing research

The immediate mandatory sizing controls are:

Fixed:

    1 : 1 : 1

Decreasing:

    1 : 0.5 : 0.25
    1 : 0.5 : 0.5
    1 : 0.25 : 0.25

Martingale:

    1 : 2 : 4

Do not label martingale "better" based on BE-recovery rate.

For martingale, maximum basket loss, exposure and margin are first-class metrics.

## 20. Deep-adverse state

The current key state is after the third tranche / about `-0.8S`.

At this point the current exact-tick development population is approximately split between:

- normal recovery to BE;
- continued adverse move to hard loss.

The research question is not another generic classifier.

It is:

    What is the action EV of HOLD?
    What is the action EV of REDUCE?
    What is the action EV of EXIT?
    What is the action EV of FLIP?

Report actual dollars for each.

## 21. Wrong-direction / flip research

Among eventual hard-loss campaigns, a large majority later produce a substantial move in the opposite direction.

This is diagnostic evidence that many hard losses are true initial-direction mistakes.

The future opposite move is never a causal input.

Research may use only information available after the deep-adverse state to decide whether an opposite-direction flip has positive action EV.

## 22. Sequential training

For model-based decisions:

2025 test:

    train <= 2024

2026 test:

    retrain <= 2025
    i.e. use 2024 + 2025

Do not keep a 2024-only model through 2026 merely because the feature was normalized.

Do not leak validation outcomes.

## 23. Threshold discipline

Discovery and validation are separate.

Do not rescue a failed validation by moving the threshold.

Do not freeze a threshold from one year, one P0/P2 realization or one small cell.

Prefer broad economic plateaus over single-point peaks.

## 24. Existing probability models

Use existing V8 models when their semantics fit the action.

Potential valid uses:

- structural models as hazard context;
- High-Q as continuation context;
- P15 as campaign authorization / movement scale context.

Invalid default uses:

- micro3 as direct direction permission;
- CLOSE_BROKEN as automatic exit;
- High-Q as justification to move every existing TP farther;
- P15 as multi-hour directional trend probability.

## 25. Final strategy requirements

The final strategy still needs:

- realized WR >=50% as the baseline condition;
- average winner/payoff meaningfully >1R under the final campaign-risk definition;
- spread, commission and slippage-adjusted positive expectancy;
- acceptable drawdown and loss streak;
- robustness across independent GOLD periods;
- adequate trade frequency;
- no reliance on right-censored assumptions;
- 2021 untouched until preregistered final validation.

## 26. Reading order

1. `HANDOFF_V8.md`
2. `RESEARCH_STATE_V8.md`
3. `V8_ATR_GRID_DIRECTION_ERROR_ABSORBER_RESEARCH_20260904.md`
4. `DECISIONS_V8_ATR_GRID_ADDENDUM_20260904.md`
5. `V8_NEXT_GRID_SIZING_AND_WRONG_DIRECTION_CONTRACT_20260904.md`
6. `V8_EXECUTABLE_MAPPING_REVALIDATION_20260903.md`
7. `DECISIONS_V8_RESEARCH_INFERENCE_GUARDRAILS_ADDENDUM_20260903.md`
8. `V8_SEQUENTIAL_CAPITAL_ALLOCATION_RESEARCH_20260903.md`
9. older V8 history only as needed

Always refresh GitHub HEAD before continuing.
