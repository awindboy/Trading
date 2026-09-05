# V8 Scenario Layer Phase-0 — V3 Bridge, Portfolio and Payoff Result

Date: `2026-09-04`  
Status: `DEVELOPMENT SYNTHESIS / PROMISING MECHANISM / NOT VALIDATED`  
Production authority: `NONE`  
Market: `GOLD# ONLY`  
2024 exact tick: `development execution evidence`  
2025 exact tick: `UNAVAILABLE`  
2025/2026 M1: `screening / descriptive robustness only`  
GOLD# 2021: `UNTOUCHED`

## 1. Purpose

This phase began after the grid sizing/deep-action branch failed to solve initial direction/payoff economics.

The active question changed from:

> Can a generic direction model or grid absorb direction error?

into:

> Does P15 identify a broad movement-event universe that can be routed into several semantically different scenario modules, each with its own direction, valid distance and payoff lifetime?

The research explicitly revisited V3 because V3 had strong scenario semantics but suffered severe frequency compression and later validation failure.

## 2. V3 lesson carried forward

V3's useful idea was the interaction:

    higher delivery / auction state
    x local reaction
    x acceptance / failure

V3's failure mode was to serially require too many conditions before Entry.

Representative strict V3 reload Candidate-A counts were approximately:

    2023 40
    2024 29
    2025 27

V8 therefore does not copy the strict V3 Entry chain.

Instead P15 supplies a broader movement opportunity population and scenario modules are allowed to be parallel.

## 3. P0 development population

Current execution-development control uses the reproducible old P0 2024 fresh75 population:

    N = 648

The earlier synchronized `653` population is not silently merged with 648.

2025 exact tick is treated as absent. 2021 remains locked.

## 4. Scenario association finding

Fresh75 is strongly enriched in already-expanding states rather than quiet compression.

Representative 2024 fresh75 versus ordinary M5 enrichment found:

- BB outside: ~45.4% versus ~11.7%;
- 1h breakout: ~50.6% versus ~14.8%;
- 3h breakout: ~39.7% versus ~7.9%;
- M5 body >= 0.15S: ~70.1% versus ~9.4%;
- prior 1h range >= 0.50S: ~86.7% versus ~35.0%.

Simple event-side direction remained near chance.

Interpretation:

> P15 often detects the onset/continuation of a non-ordinary movement state, but event existence alone does not solve direction.

## 5. V3 bridge — strict copy recreates scarcity

Direct overlap between strict/broad V3 reload triggers and fresh75 is very small.

Copying the V3 serial chain into V8 therefore recreates the same denominator problem.

A broader V8 test of local M5 ownership transition at fresh75 appeared directionally positive in M1 but failed 2024 exact tick when entered immediately.

Conclusion:

> local transition alone is not an executable edge; state and persistence matter, but adding them as serial gates can recreate V3 scarcity.

## 6. Current independent scenario modules

Three distinct mechanisms currently survive as development modules.

### A. BB persistent expansion + HTF alignment

Semantic process:

    price outside BB
    -> distance from SMA expands over successive M5 bars
    -> next M5 remains outside and expands further
    -> M30/H1 structural ownership aligns with expansion direction

M1 screening with the V3-L-style payoff:

| Year | N | Mean R | PF |
| --- | ---: | ---: | ---: |
| 2024 | 37 | +0.135 | 1.39 |
| 2025 | 31 | +0.256 | 1.70 |
| 2026 | 30 | +0.078 | 1.21 |

2024 exact tick:

- candidates 37;
- completed 32;
- positive 15 / negative 17;
- WR 46.88%;
- mean +0.0435R;
- total +1.393R;
- PF 1.098;
- average positive +1.040R;
- checkpoint 13;
- residual +2R 8.

Interpretation:

- low/medium frequency;
- WR below project target standalone;
- positive expectancy and average positive >1R in 2024 exact development;
- runner continuation after checkpoint is materially present;
- not validated.

### B. Endogenous late ignition

Semantic process:

    relatively quiet/flat earlier pre-path
    -> sharp late displacement/activity burst before fresh75
    -> exclude the identified scheduled-major-macro 15:30 population
    -> follow the ignition direction only over its short empirical lifetime

M1 screening:

| Year | N | Mean R | PF |
| --- | ---: | ---: | ---: |
| 2024 | 28 | +0.220 | 1.67 |
| 2025 | 26 | +0.105 | 1.26 |
| 2026 | 19 | +0.319 | 2.31 |

2024 exact tick:

- candidates/completed 28;
- positive 17 / negative 11;
- WR 60.71%;
- mean +0.1340R;
- total +3.753R;
- PF 1.357;
- average positive +0.839R;
- checkpoint 16;
- residual +2R 5.

Interpretation:

- standalone WR is promising;
- average positive remains below 1R;
- direction edge is short-lived and must not be stretched into a large fixed TP;
- not validated.

### C. Scheduled major macro reaction

2024 major release population includes scheduled 08:30 ET NFP/CPI/PPI/PCE dates mapped to the broker-time reaction window.

The chart-only H1 movement model substantially underpredicts major-release movement because it does not know the release calendar.

This is evidence that scheduled calendar information is genuinely information-expanding for movement probability.

2024 M1 screening under the V3-L-style payoff:

- N 35;
- mean about +0.266R;
- PF about 1.87.

2024 exact tick:

- candidates 35;
- completed 33;
- positive 19 / negative 14;
- WR 57.58%;
- mean +0.1198R;
- total +3.955R;
- PF 1.307;
- average positive +0.887R;
- checkpoint 19;
- residual +2R 7.

Interpretation:

- scheduled macro is a strong movement event;
- simple first-reaction follow has limited directional lifetime;
- future macro research should separate calendar, surprise and post-release acceptance;
- not validated.

## 7. Common payoff — V3-L survival / continuation separation

The useful V3 idea was reused without changing scenario thresholds to optimize P/L.

Reference payoff:

    initial risk = 0.25S
    +0.25S favorable = +1R survival checkpoint
    -> realize 50%
    -> move residual to BE
    -> residual target +2R

Economic meaning:

- the scenario only needs to forecast the initial short-distance direction;
- continuation beyond the checkpoint is a separate conditional process;
- do not force the initial scenario to predict a +0.75S direct runner.

## 8. 2024 scenario portfolio

The three modules have low overlap.

Deduplication rule:

- one unique P15 campaign;
- if multiple scenario labels occur, use the earliest causally confirmed eligible module rather than count multiple independent trades from the same campaign.

2024 union:

- raw module observations about 100;
- unique scenario campaigns 96;
- completed 89;
- censored 7;
- positive 49;
- negative 40;
- realized positive WR 55.06%;
- mean +0.1049R per completed campaign;
- total +9.339R;
- PF 1.262;
- average positive +0.9168R;
- average negative -0.8896R;
- +1R checkpoint 47;
- residual +2R 19.

Comparison to V3 scarcity:

    2024 strict V3 Candidate-A ~29
    current V8 scenario union 96

The union is approximately 3.3x the V3 2024 strict candidate count.

This is the first material evidence that scenario precision and usable frequency may coexist through an orthogonal module portfolio rather than through one relaxed scenario.

## 9. Current project-target scorecard

| Requirement | Current 2024 exact-tick development |
| --- | --- |
| realized WR >= 50% | PASS — ~55.1% |
| positive expectancy | PASS — +0.105R |
| PF > 1 | PASS — ~1.26 |
| average positive meaningfully >1R | FAIL — ~+0.917R |
| adequate frequency | IMPROVED — 96 candidates, not yet final |
| independent exact-tick validation | FAIL / unavailable |
| full production cost authority | FAIL |

Therefore the portfolio is not production-worthy.

## 10. Runner lifetime result

Among the 47 checkpoint events, exact-tick maximum favorable continuation after the initial risk scale was:

| Level | Reached | Conditional rate |
| --- | ---: | ---: |
| +1.5R | 25 | 53.19% |
| +2R | 19 | 40.43% |
| +2.5R | 11 | 23.40% |
| +3R | 10 | 21.28% |
| +4R | 6 | 12.77% |
| +5R | 3 | 6.38% |

Longer runner targets do not automatically improve economics.

The current information lifetime decays materially beyond ~+2R.

Do not move TP to +3R/+5R merely to raise average winner.

## 11. Full-position +0.5R floor variant

A non-filter payoff variant was tested:

    +1R checkpoint
    -> protect the whole position at +0.5R
    -> target +2R

2024 exact tick union:

- completed 89;
- WR unchanged ~55.1%;
- mean +0.0865R;
- total +7.697R;
- PF 1.216;
- average positive +0.883R.

This underperformed the current partial-realization / residual-BE control and is not promoted.

## 12. Negative V3-style extensions that must not be reopened casually

The following broad extensions did not solve the problem:

- immediate M5 ownership-transition entry;
- strict P15-after-V3 reload overlap;
- broad breakout acceptance with HTF alignment after exact tick;
- mandatory exact breakout-boundary retest;
- retest + reacceptance chain;
- strict post-P15 V3 reload-state-machine confirmation.

Common failure:

> every extra serial confirmation either diluted the execution edge or compressed the population back toward V3 scarcity.

## 13. What is actually promising

Not one final scenario.

The promising mechanism is:

    broad P15 movement universe
    -> independent scenario families with distinct causal semantics
    -> scenario-specific short-distance direction
    -> separate continuation/payoff layer
    -> portfolio union for frequency

This architecture is the current research candidate.

## 14. Validation warning from V3

V3 Candidate B looked strong in discovery and failed frozen 2022 validation.

Therefore the current 2024 portfolio must be treated as something to falsify, not something to defend.

Do not tune 2024 until average winner exceeds 1R.

Do not use 2025 M1 as if it were exact-tick validation.

Do not touch 2021.

## 15. Immediate next research

Before more P/L optimization:

1. commit/reproduce exact scenario definitions and replay artifacts;
2. adopt `V8_SCENARIO_GLASS_CEILING_RESEARCH_PRINCIPLES_20260904.md` as a permanent guardrail;
3. run Directional Change / intrinsic-time only as a shadow glass-ceiling audit first;
4. determine whether multi-scale intrinsic events add incremental conditional information beyond existing P15/scenario states;
5. seek new orthogonal modules, not variants of the current three;
6. preserve separate information-expanding lanes for macro surprise and potential COMEX/order-flow data;
7. no 2021 use.

## 16. Production status

`NONE`
