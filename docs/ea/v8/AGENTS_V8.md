> **V8 ACTIVE RESEARCH SUPERSEDED BY V9 — 2026-09-07**  
> This document remains authoritative for preserved V8 research contracts, evidence, negative controls, and historical decisions.  
> It is no longer the active strategy-research routing document.  
> Current active research resumes from `docs/ea/v9/AGENTS_V9.md` and `docs/ea/v9/HANDOFF_V9.md`.  
> V9 does not invalidate V8 findings; it changes the primary research objective after separating market understanding, directional prediction, and trade quality.  
> Do not resume new V8 threshold/model research unless V9 explicitly reopens a V8 question.

# V8 Research Instructions

Status: `ACTIVE / GOLD P15 SCENARIO PORTFOLIO + STATE-TRANSITION / GLASS-CEILING RESEARCH`  
Generation: `V8`  
Last synchronized: `2026-09-05`  
Production authority: `NONE`  
Market: `GOLD# ONLY`  
Untouched reserve: `GOLD# 2021`  
Source Git HEAD before this synchronization: `eb0daed45f8c2784d28599b954faba3ce2cd246c`

## 1. Authority and resume order

GitHub is the permanent project authority.

On every session:

1. refresh Git HEAD;
2. read `HANDOFF_V8.md`;
3. read `RESEARCH_STATE_V8.md`;
4. read `V8_SCENARIO_GLASS_CEILING_RESEARCH_PRINCIPLES_20260904.md`;
5. read the current result/decision files named by HANDOFF;
6. use older V8/V3 files only when needed for preserved history or comparison;
7. never let conversation memory override newer GitHub state.

## 2. Hard scope

Until the user explicitly reopens scope:

- GOLD# only;
- no other-market search;
- no market-universe pivot;
- no GOLD# 2021;
- no production authority.

P0/P2 or any rebuilt population versions are deterministic research realizations, not independent trades to merge.

## 3. Permanent semantic separation

Never silently merge:

- movement onset;
- scenario/cause;
- direction;
- direction-valid distance/horizon;
- structural survival;
- winner continuation;
- entry;
- exit/payoff;
- execution;
- cost;
- capital allocation.

Permanent reminders:

    P15 movement opportunity != direction edge
    event existence != event direction
    acceptance != automatic Entry
    high AUC != profitable action
    first-touch accuracy != economic edge
    MFE != capturable P/L
    structural damage != automatic stop
    gross edge != surviving edge after execution
    campaign RR != first-entry TP/SL distance

## 4. Current architectural thesis

Active research architecture:

    movement/event layer
        P15 / HTF movement / scheduled event / change-point descriptors

    -> scenario/cause layer
        independent market processes

    -> scenario-specific direction-distance-horizon

    -> survival checkpoint

    -> separate winner continuation / payoff

    -> exact Bid/Ask execution

    -> orthogonal scenario portfolio for frequency

This is a research scaffold, not a frozen strategy.

## 5. P15 authority

P15 remains a near-term movement/excursion probability model.

Do not turn it into:

- a universal direction model;
- a multi-hour trend model;
- direct permission to stretch TP.

Fresh75 often occurs after expansion/displacement has already begun. Research must inspect the process that caused P15 to become high, not only the snapshot at fresh75.

## 6. V3 permanent lesson

V3 is a major scenario-design reference.

Preserve the principle:

    higher auction/delivery state
    x local event/reaction
    x acceptance/failure

Do not automatically preserve V3's exact swing, liquidity, FVG, retest, timeframe or serial Entry chain.

V3's permanent warning:

    added selectivity can improve discovery numbers
    while collapsing trade count
    and still fail frozen validation

The V3 Candidate-B 2022 failure is a permanent negative control against rescuing discovery results.

## 7. Trade-frequency guardrail

Do not solve economics by shrinking the denominator.

For every candidate report:

- original population;
- selected N;
- excluded N;
- unique campaigns;
- overlap with existing modules;
- year/time split;
- exact completed/censored counts where applicable.

Frequency should come from genuinely different scenario modules, not from weakening one scenario or counting parameter variants as diversification.

## 8. Glass-ceiling-first rule

Before implementing a theory as a strategy, identify the structural ceiling that normally defeats it.

Mandatory ceiling categories:

- selectivity vs frequency;
- non-stationarity / meaning reversal;
- information horizon vs execution cost;
- threshold/backtest search;
- overlap with information already contained in price history.

The first experiment should attack the ceiling, not optimize P/L.

## 9. Representation versus new information

Classify every proposed input first.

### Information-preserving representation

Price/quote-history transformations, including:

- indicators;
- swing/BOS/FVG/liquidity labels;
- Directional Change / intrinsic-time labels;
- auction/value labels derived from the same price path;
- breakout/persistence;
- price-only clustering/regime models.

Useful as representations; not automatically new directional information.

### Information-expanding input

Causally new information, e.g.:

- scheduled macro calendar;
- actual-consensus macro surprise once known;
- COMEX GC flow/depth;
- options state;
- other causally available external price-discovery data.

External inputs require explicit known-at, latency and execution assumptions.

## 10. `Invariant before profitable`

Before strategy promotion test:

- chronological stability;
- natural scale stability;
- small parameter perturbation stability;
- exact mirror / naive-control asymmetry;
- execution-cost margin.

Prefer broad semantic/economic plateaus over one exact profitable point.

Never rescue a failed validation by moving thresholds.

## 11. Direction target discipline

Do not default to universal `UP/DOWN`.

Define direction with explicit distance and horizon, e.g.:

    P(+0.25S before -0.25S within h | scenario)

A scenario may have direction edge at 0.25S but no edge at 0.75S.

That is a valid finding. Do not stretch the forecast lifetime to manufacture a runner.

## 12. Survival versus continuation

Initial survival and winner continuation are separate research stages.

Current scenario payoff control:

    risk = 0.25S
    +1R survival checkpoint
    -> realize 50%
    -> residual BE
    -> residual +2R

This is a control, not final authority.

Do not move the runner to +3R/+5R simply to force average winner >1R.

## 13. M1 versus exact tick

M1 is appropriate for:

- broad screening;
- scenario/state description;
- trajectory analysis;
- natural sensitivity;
- candidate generation.

Exact Bid/Ask tick is mandatory for:

- execution P/L;
- first-touch ordering when economically relevant;
- stop/TP chronology;
- spread/slippage-sensitive results;
- multi-fill/grid logic;
- same-minute conflicts.

Do not claim exact execution authority from M1.

## 14. Tick coverage and censoring

For every exact-tick dataset verify:

- period;
- timezone/server-time assumptions;
- Bid/Ask;
- timestamp precision;
- duplicates;
- month/file boundaries;
- missing intervals.

Campaigns crossing active missing coverage are right-censored/incomplete.

Do not force censored events into win/loss.

## 15. Causal timing

Every feature/state/event must have explicit `known_at`.

For a decision at `15:35` based on the completed 15:34 M1:

    legal feature cutoff = 15:34 close
    earliest execution = 15:35

No current-bar look-ahead.

A previous one-minute look-ahead error was invalidated and must not recur.

External macro/order-flow data must obey the same rule.

## 16. Cost and edge-margin rule

When execution cost matters, report both:

- same-path structural/gross result where meaningful;
- actual Bid/Ask result.

Interpret:

    gross structural edge
    - execution friction
    = surviving edge margin

Do not say "spread killed the edge" when the gross edge was already thin.

## 17. Directional Change / Auction Theory status

Neither is adopted as a strategy.

Directional Change broad-direction shadow audit is now complete and negative. Its state representation is stable, but single/multi-scale direction is near chance or chronologically unstable and does not add a broad orthogonal module outside the existing scenario set.

Do not optimize DC thresholds. DC is shadow context only unless a new causal interaction is preregistered.

The completed audit checked:

1. threshold sensitivity;
2. event-frequency collapse;
3. overshoot-distance decay;
4. chronological stability;
5. execution-cost sensitivity;
6. incremental information conditional on current P15/scenario states;
7. multi-scale semantic invariance.

Do not optimize DC thresholds for P/L.

Auction/acceptance concepts may define scenario semantics only if they beat naive breakout/reversal controls and remain causal.

## 18. External-information lane

Potential future research:

### Macro

    scheduled calendar
    -> pre-event state
    -> actual-consensus surprise once known
    -> first reaction
    -> acceptance/rejection

Calendar primarily informs movement opportunity. Direction requires separate causal information.

### COMEX / order flow

If acquired, use order flow primarily to resolve scenario meaning:

    confirming flow
    versus
    absorption/divergence

Do not default to `OFI sign -> trade`.

## 19. Completed grid branch

The ATR-grid static-sizing/deep-action branch is preserved but no longer primary.

Rejected/downgraded controls include:

- decreasing sizing;
- martingale;
- equal-risk wider-boundary rescue;
- unconditional REDUCE/EXIT/FLIP;
- simple adverse thresholds;
- corrected five-minute action model;
- single-use hedge.

Do not reopen these by threshold tweaking without a genuinely new mechanism.

## 20. Current scenario-development status

Current Phase-0 modules:

- BB persistent expansion + HTF alignment;
- endogenous late ignition;
- scheduled major macro reaction.

2024 exact-tick union currently shows development evidence around:

- unique candidates 96;
- completed 89;
- WR ~55.1%;
- mean ~+0.105R;
- PF ~1.26;
- average positive ~+0.917R.

This is promising but not validated and does not yet satisfy the average-winner objective.

Do not tune 2024 to force the missing metric.

## 21. Data authority

Current execution-development population:

- reproducible P0 2024 fresh75 = 648;
- prior 653 remains documented historical mismatch;
- 2024 exact tick = development evidence;
- 2025 exact tick = unavailable;
- 2025/2026 M1 = screening/descriptive only for current scenario research;
- GOLD# 2021 = untouched reserve.

## 22. Final strategy requirements

The final strategy still requires:

- realized WR >=50%;
- average winner/payoff meaningfully >1R under the final campaign-risk definition;
- spread, commission and slippage-adjusted positive expectancy;
- acceptable drawdown/loss streak;
- robustness across independent GOLD periods;
- adequate frequency;
- no dependence on censoring assumptions;
- no validation repair by retuning;
- 2021 used only after a preregistered final-validation decision.

## 23. External research handling

External papers are supporting evidence and falsification references only. They never override GitHub project evidence.

Current supporting synthesis: `V8_EXTERNAL_DIRECTION_RESEARCH_SYNTHESIS_20260905.md`.

Permanent interpretation:

    short-horizon current-state direction may have a thin gross-edge ceiling
    !=
    all price-only information is exhausted

A distinct remaining target is:

    movement disturbance
    -> causal state transition
    -> persistent directional state
    -> economically meaningful continuation horizon

Do not copy outside GMM, Markov, threshold, session, or holding-period parameters. Import the research question, not the rule.

## 24. Current next primary research

The next primary contract is:

`V8_NEXT_P15_STATE_TRANSITION_PERSISTENCE_CONTRACT_20260905.md`

It is shadow-first.

The research object is transition/persistence, not the static state label and not next-bar sign.

Required first-stage questions:

- does P15 mark a disturbance followed by a reproducible state transition?
- is the post-transition state persistent over natural 15/30/60m horizons?
- is that information incremental beyond Late Ignition / BB Persistence / Macro?
- are semantics stable across 2024 H1/H2 and 2025/2026 M1 descriptive periods?
- does any eventual executable relationship have enough gross edge margin to justify exact-tick escalation?

Do not turn the first state partition into an Entry gate.

## 25. Immediate reading order

1. `HANDOFF_V8.md`
2. `RESEARCH_STATE_V8.md`
3. `V8_SCENARIO_GLASS_CEILING_RESEARCH_PRINCIPLES_20260904.md`
4. `V8_EXTERNAL_DIRECTION_RESEARCH_SYNTHESIS_20260905.md`
5. `V8_NEXT_P15_STATE_TRANSITION_PERSISTENCE_CONTRACT_20260905.md`
6. `V8_SCENARIO_LAYER_PHASE0_RESULT_20260904.md`
7. `V8_DIRECTIONAL_CHANGE_GLASS_CEILING_AUDIT_20260904.md`
8. `DECISIONS_V8_SCENARIO_GLASS_CEILING_ADDENDUM_20260904.md`
9. `V8_GRID_SIZING_DEEP_ACTION_RESULT_20260904.md`
10. older V8/V3 history only as needed.

Always refresh GitHub HEAD before continuing.
