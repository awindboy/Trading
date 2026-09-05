# V8 Scenario Research — Glass-Ceiling Principles

Date: `2026-09-04`  
Amended: `2026-09-05`  
Status: `PERMANENT RESEARCH GUARDRAIL / ACTIVE`  
Production authority: `NONE`  
Market: `GOLD# ONLY`  
Untouched reserve: `GOLD# 2021`

## 1. Why this document exists

V8 has reached a point where many trading theories can be made to look conceptually compatible with the project:

- Directional Change / intrinsic time;
- Auction Market Theory / acceptance-rejection;
- breakout / failed auction;
- order-flow imbalance;
- volatility clustering / event intensity;
- change-point / regime models;
- session auction logic;
- prior V3 liquidity / delivery / local-acceptance scenarios.

The danger is that all of these can sound correct before testing. The project has already seen many theoretically plausible ideas fail under independent time, exact execution, cost or denominator pressure.

Therefore the active objective is no longer:

> Find a good-looking theory and implement it.

It is:

> Identify the structural glass ceiling that normally defeats that theory, then test whether V8 can avoid that ceiling for a causal reason.

This document is a permanent guardrail for all future V8 scenario research.

## 2. Primary distinction — representation is not new information

Every proposed variable or theory must first be classified into one of two groups.

### A. Information-preserving representation

Examples:

- RSI / stochastic / MACD;
- Bollinger Band state;
- ATR / realized volatility;
- swing / BOS / CHOCH;
- FVG / OB;
- liquidity sweep;
- Directional Change events;
- value area / acceptance derived only from the same price history;
- breakout / retest / persistence;
- candle patterns;
- price-only clustering or HMM state.

These may be useful representations of market state. They do not automatically add directional information because they are transformations of information already present in price/quote history.

A new representation receives no alpha authority merely because its semantics are appealing.

### B. Information-expanding input

Examples:

- scheduled macro release calendar known before the release;
- actual versus consensus macro surprise once legally known;
- COMEX GC trade direction / aggressive flow;
- bid/ask depth and queue imbalance;
- options implied-volatility / skew state;
- causally available positioning or cross-venue price-discovery information.

These can genuinely enlarge the information set.

They still require validation, latency and execution analysis, but they are conceptually different from re-encoding the same OHLC path.

## 3. Permanent lesson — movement and direction have different information ceilings

Current V8 evidence supports:

    movement onset / excursion probability
        more learnable

    broad initial direction
        repeatedly weak / unstable

Therefore do not assume that improving the representation of the same chart history will necessarily solve direction.

The scenario target should normally be conditional and bounded:

    P(direction first-touch at distance d within horizon h | scenario, context)

rather than a universal:

    P(UP) / P(DOWN)

A scenario may contain valid direction information for `0.25S` but not for `0.75S`. That is a real economic property, not a reason to move the threshold until a long runner appears.

## 4. Glass ceiling A — selectivity versus frequency

V3 is the canonical warning.

V3 showed coherent interaction between:

    higher delivery state
    + intermediate liquidity reaction
    + decisive local acceptance

but serially requiring every condition compressed the population severely.

Representative V3 Candidate-A annual counts were approximately:

    2023 40
    2024 29
    2025 27

The project must not solve quality by repeatedly shrinking the denominator.

### Required V8 response

Do not try to make one good scenario trade more often by relaxing its semantics until quality disappears.

Prefer:

    Scenario A 30-50 trades
    + Scenario B 30-50 trades
    + Scenario C 30-50 trades
    + Scenario D ...

where the modules represent different causal/economic mechanisms and have low overlap.

Frequency should come from an `orthogonal scenario portfolio`, not from diluting one edge.

## 5. Glass ceiling B — non-stationarity / meaning reversal

The same apparent pattern can represent a different auction state in a different period.

V3 Candidate B is the permanent negative control:

- discovery looked strong;
- frozen 2022 validation failed materially;
- threshold, session, direction or mirror repair on the validation year was prohibited.

Therefore annual pooled performance is not enough.

A scenario is not strong because one year is profitable. It must preserve its semantic/economic relationship across chronological partitions without changing the rule after outcomes are seen.

## 6. Glass ceiling C — information horizon versus execution cost

Short-horizon information can be statistically real and economically unusable.

V8 has already observed this in:

- micro first-touch;
- micro-grid geometry;
- simple hedge structures;
- short-distance directional edges whose gross margin was too thin after Bid/Ask.

Permanent rule:

> Do not say that spread killed a good strategy when the zero-cost structural edge was already thin.

For every execution-sensitive candidate report:

    gross structural edge
    - actual execution friction
    = surviving edge margin

A candidate should have margin, not merely positive sign before cost.

## 7. Glass ceiling D — backtest search / threshold tournaments

Many theories expose tunable quantities:

- Directional Change threshold;
- acceptance bars;
- breakout window;
- ATR multiplier;
- value-area lookback;
- session window;
- model score boundary;
- runner target.

Do not search these until a profitable point appears.

Natural sensitivity is allowed only to test whether a relationship is broad and stable.

A failed validation is not repaired by threshold movement.

## 8. `Invariant before profitable`

Before P/L promotion, ask whether the relationship is structurally invariant.

### Time invariance

Does direction/economics survive chronological splits and later years?

### Scale invariance

Does the semantic relationship survive natural scale changes, rather than existing at one magical timeframe or one exact threshold?

### Parameter perturbation

Does a small, natural parameter change preserve the relationship?

### Mirror asymmetry

Does the intended direction materially beat the exact mirror or a matched directional control?

### Cost margin

Is the zero-cost edge large enough that actual Bid/Ask does not consume most of it?

Only after these checks should a scenario be described as a trading candidate.

## 9. V3 lesson — use scenario meaning, not V3's serial filter chain

V3's important contribution is architectural:

    auction/delivery state
    x local event
    x acceptance or failure

V8 should reuse that reasoning.

V8 should not automatically reuse:

- the exact V3 swing detector;
- mandatory liquidity sweep;
- exact M15/M30 source;
- mandatory retest;
- exact V3 acceptance threshold;
- the complete serial Entry chain.

V8 testing already showed that copying strict V3 structure onto fresh75 recreates scarcity.

The V3 concept should be used as a scenario classifier/routing language over the broader V8 movement universe.

## 10. Scenario modules must be economically distinct

The following are not four independent modules:

    BB persistence 3 bars
    BB persistence 4 bars
    BB persistence + H1
    BB persistence + M30

They are variants of one mechanism.

Independent modules should represent different causes/processes, for example:

- endogenous initiative expansion;
- exogenous macro information shock;
- failed-auction reversal;
- session auction transition;
- order-flow absorption/exhaustion;
- nested intrinsic-scale reload.

Portfolio frequency receives credit only for genuinely different scenario families.

## 11. Directional Change / Auction Theory usage rule

Directional Change and Auction Market Theory are not approved strategies.

They are candidate languages for describing market processes.

Before using Directional Change as a trading rule, run a `DC glass-ceiling audit`:

1. threshold sensitivity;
2. event-frequency collapse;
3. overshoot-distance decay;
4. chronological stability;
5. execution-cost sensitivity;
6. incremental information versus existing P15 / BB / ignition states;
7. whether multi-scale relations are more stable than one exact threshold.

If DC only renames an existing P15/BB state without incremental conditional information, do not add it to the strategy.

Auction concepts should be treated similarly: acceptance/rejection must beat naive breakout/reversal controls and must remain causal.

## 12. External information is a separate research lane

Price-only research remains valid, but do not assume it must eventually solve every direction problem.

Potential information-expanding lanes include:

### Macro

    scheduled release
    -> pre-event state
    -> actual-consensus surprise when known
    -> first reaction
    -> acceptance / rejection of the reaction

The calendar is primarily movement information. Direction requires separate causal information such as surprise and post-release acceptance.

### COMEX / order flow

The useful question is not:

    OFI > 0 -> LONG

It is closer to:

    same price scenario
    + confirming flow
    versus
    same price scenario
    + absorption/divergent flow

Order flow should be tested as a scenario-meaning resolver, not as a generic ultra-short signal whose edge can be consumed by cost.

Any external source must have explicit timestamp, availability and no-lookahead rules.

## 13. Outcome architecture — survival is separate from continuation

V3's useful lesson carries forward:

    initial Entry survival
    != winner continuation

A scenario that predicts the first `+0.25S before -0.25S` may still be valuable even if direct `+0.75S` continuation fails.

Do not stretch the initial directional forecast beyond its empirical lifetime.

After a scenario reaches a survival checkpoint, continuation should be evaluated as a separate conditional problem with a separate payoff architecture.

Do not increase runner TP merely to force average winner above 1R.

## 14. Current scenario-portfolio philosophy

Active conceptual structure:

    movement/event layer
        P15 / HTF movement / scheduled event / change point

    -> scenario/cause layer
        endogenous expansion / macro / failed auction / session / other independent families

    -> direction-distance-horizon layer
        scenario-specific conditional first-touch / continuation

    -> execution/payoff layer
        checkpoint / protected runner / exact Bid-Ask

No layer should be silently used as another layer's authority.

## 15. Current stop rules

Do not:

- add another indicator vote merely because it is popular;
- convert a chart theory into authority before testing its known ceiling;
- broaden one sparse scenario by outcome-driven threshold relaxation;
- call several parameter variants independent modules;
- optimize 2024 exact-tick outcomes until the portfolio target is met;
- treat 2025 M1 as exact execution validation;
- touch GOLD# 2021;
- claim production authority.

## 16. Immediate research order after documentation

1. reproduce/freeze the current V8 scenario portfolio and definitions in committed replay artifacts;
2. perform Directional Change as a shadow-only glass-ceiling audit, not a strategy optimization;
3. test whether intrinsic multi-scale state adds information conditional on existing scenarios;
4. build a genuinely different failed-auction/reversal scenario only if it has causal semantics and sufficient population;
5. formalize scheduled-macro information as a separate exogenous layer;
6. only after price-only scenario ceilings are quantified, decide whether external COMEX/order-flow acquisition is justified;
7. keep 2021 untouched.

## 17. One-line permanent principle

> Do not ask whether a theory sounds like our strategy. Ask what structural failure normally prevents that theory from becoming a robust strategy, and design the experiment to falsify that failure first.


## 18. Static state is not the same target as state transition

The failure of broad current-state direction does not prove that all price-only information is exhausted.

Treat these as different research targets:

    current state -> next short-horizon sign

versus

    disturbance -> state transition -> persistence

The second target is allowed because it asks whether a new persistent process has actually formed, not whether a static snapshot predicts the next candle.

Do not disguise a next-bar classifier as a regime-transition model.

## 19. Transition before horizon

A longer holding period is not an edge.

Required order:

1. identify a causal transition;
2. demonstrate post-transition persistence;
3. measure its natural distance/time lifetime;
4. only then design payoff.

Do not extend TP or time merely because external research found longer-horizon positive controls.

## 20. External research is supporting evidence only

External evidence may:

- reveal common structural ceilings;
- provide falsification controls;
- suggest a new target variable or research design.

It may not:

- override V8/V3 evidence;
- supply trading thresholds without V8 validation;
- justify copying a strategy from another instrument;
- be described as universal academic consensus when the evidence is narrower.

The Mesfin (2026) MNQ falsification paper is recorded specifically as a useful external example, not project authority.

## 21. State-partition discipline

If clustering/HMM/GMM/Markov-style tools are used:

- state count must not be optimized from P/L;
- labels must be mapped by stable semantic descriptors, not arbitrary cluster numbers;
- state semantics must survive chronological splits and natural perturbations;
- the transition must add information beyond the static state;
- a profitable cluster with unstable meaning is rejected.

The project is not authorized to copy outside GMM or Markov parameters.

## 22. Updated one-line research principle

> When broad direction is weak, do not keep inventing a better static predictor. Test whether a causal market-state transition has occurred, whether that state persists long enough to create economic distance, and whether the relationship survives the same glass ceilings that defeated earlier strategies.
