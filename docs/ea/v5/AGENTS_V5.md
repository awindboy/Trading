# V5 — Success-First Market Mechanism Research Authority

Status: `ACTIVE RESEARCH AUTHORITY`
Date: `2026-08-27`
Production authority: `NONE`
Parent lines:
- V1 `FROZEN deterministic control`
- V2 `PAUSED / preserved`
- V3 `PAUSED / negative + mechanism evidence`
- V4 `PAUSED / preserved AI-native representation research`

## 1. Purpose

V5 changes the research question.

The project no longer begins with:

```text
indicator / pattern / model
-> threshold
-> trade rule
-> backtest
```

It begins with:

```text
verified successful trader
-> repeated observation
-> pattern as visible expression
-> market concept
-> proposed mechanism
-> causal observable / falsifier
-> statistics for validation
-> only then strategy construction
```

V5 is called **success-first** because the research corpus starts from traders and systematic programs with meaningful evidence of long-term survival or real performance, then reverse-engineers what their methods were actually exploiting.

V5 is called **mechanism-first** because a chart shape receives no authority merely because it has a familiar name. A setup must be translated into a hypothesis about market state, participant behavior, order/liquidity constraints, volatility, price impact, or payoff geometry that can be contradicted by data.

## 2. Startup order

On every V5 session:

1. check latest GitHub commit;
2. read root `AGENTS.md`;
3. read root `docs/ea/HANDOFF.md`;
4. read this file;
5. read `HANDOFF_V5.md`;
6. read `RESEARCH_STATE_V5.md`;
7. read `DECISIONS_V5_APPEND_D180_D182.md`;
8. read `DECISIONS_V5_APPEND_D183_D184.md`;
9. read `V5_036A_CROSS_ARCH_CONTINUATION_PORTABILITY_RESULTS.md`;
10. read `V5_037A_SOURCE_REVIEW_AND_LINEAGE_SCREEN.md`;
11. read `V5_037A_GOLD_REAL_YIELD_DIRECTIONAL_DELIVERY_CONTRACT.md`;
12. read `V5_000_SUCCESS_FIRST_RESEARCH_CONTRACT.md`;
13. read `V5_SUCCESS_FIRST_TRADER_CORPUS_V1.md`;
14. read `V5_MARKET_MECHANISM_ONTOLOGY_V1.md`;
15. read `V5_SOURCE_LEDGER.md`;
16. read `BACKLOG_V5.md`;
17. inspect older V5/V1-V4 evidence only after the current question is clear.

GitHub wins over chat memory.

## 3. Core research rules

### 3.1 Success evidence before mythology

A trader is not included because they are famous, sell a course, or have a compelling story.

Record:
- evidence of longevity/performance;
- whether evidence is institutional/third-party, self-reported, or secondary;
- markets and horizons;
- what is actually public about the method;
- what is inference rather than direct statement.

Weakly evidenced traders may still supply hypotheses, but they cannot establish a mechanism by reputation.

### 3.2 Pattern names are observations, not explanations

Examples:

```text
H&S
rectangle
NR7
inside day
liquidity sweep
failed breakout
pullback
```

are not V5 mechanisms by themselves.

The required question is:

```text
What broader condition could this visible pattern be expressing?
```

Possible answers include:
- balance / equilibrium;
- directional expansion;
- stop activation;
- failed price discovery;
- liquidity absorption;
- exhaustion;
- inventory adjustment;
- volatility-state transition;
- trend persistence;
- payoff convexity.

Each remains a hypothesis until observable and validated.

### 3.3 Observation -> concept -> principle -> statistics

V5 adopts the research ordering independently articulated by Toby Crabel in 2026:

```text
Observation
-> Pattern
-> Concept
-> Principle
-> Statistics
-> Strategy
```

Statistics validate concepts; they do not automatically supply a meaningful concept.

This does not ban data-driven discovery. It prevents the project from promoting a relationship that has no coherent interpretation or survives only through threshold search.

### 3.4 Context before signal

The same visible event may imply different things in:
- trend;
- balance;
- volatility contraction;
- volatility expansion;
- mature move;
- early move;
- high-friction execution;
- thin liquidity;
- event/news shock.

A signal without state/context is incomplete.

### 3.5 Interaction is more important than the level name

A level is not automatically support/resistance.

V5 asks how price interacts with a pre-existing boundary:
- approach character;
- first penetration;
- dwell/acceptance beyond;
- re-entry;
- retest;
- follow-through;
- opposite response.

### 3.6 Effort/result terminology is evidence-tiered

With true trade/order-book data:

```text
effort = signed flow / OFI / depth consumption
result = price impact
```

With MT5 CFD M1 data, tick volume is only an activity proxy.

Therefore V5 may calculate:

```text
EFFORT_RESULT_PROXY
```

but must not label it `ABSORPTION` or real order-flow imbalance without appropriate data.

### 3.7 Full-path ledger before discrete labels

The first instrumentation should record continuous causal and post-event quantities before inventing PASS/FAIL thresholds.

Do not prematurely turn a concept into a Boolean gate.

### 3.8 Old V3 variables become observations, not privileged truth

V3 ideas such as:
- wave progression;
- acceptance;
- protected break;
- direct transfer;
- H/L;
- failed auction;

may be reused only as candidate descriptive observations.

They are not inherited V5 gates and do not receive authority because they existed previously.

### 3.9 Discovery / validation remains strict

The project still forbids:
- validation rescue;
- single-year rule patching;
- look-ahead;
- post-outcome market selection;
- threshold proliferation;
- small-N promotion.

### 3.10 Final strategy objective — D-180

Any eventual production candidate must target:
- realized positive-trade rate >= 50%;
- average positive NET R >= 2.0R;
- positive full-cost expectancy;
- acceptable drawdown / loss streak;
- robustness across independent periods and markets;
- execution parity.

`2R` is an evaluation criterion, not authorization to force every trade to a fixed 2R TP.

However, V5 corpus/mechanism discovery is **not allowed to exclude successful traders merely because their own win rate is below 50%**. Discovery evidence and final project requirements are separate.


### 3.11 Mandatory recursive falsification

Before promoting any V5 interpretation, read `V5_RECURSIVE_FALSIFICATION_PROTOCOL.md`.

Every major result must explicitly test:
- the opposite thesis;
- a simpler confounder explanation;
- a placebo/negative control;
- recurrence of prior V1-V4 failures;
- whether confirmation consumed payoff geometry.

A result that fails a frozen adversarial control is recorded and downgraded; it is not rescued with another threshold.

## 4. V4 disposition

V4 is not declared false.

The frozen R0/R1/R2 Representation Tournament and its data/code remain preserved.

V4 is paused because V5 is testing whether a better semantic problem formulation should exist **before** asking a model to learn arbitrary next-return direction.

If V5 produces useful causal semantic states, V4 methods may later be used as:
- representation learners over mechanism primitives;
- state-transition models;
- conditional-policy models.

## 5. Current active question

```text
Does a causally available change in US 10-year TIPS real yield
condition the next complete GOLD broker-day directional delivery
in the inverse economic direction?
```

Current authority:
- V5-030A = historical old-gate PASS / new-gate FINAL ECONOMICS FAIL;
- V5-036A = portable M30 observable / cross-architecture transfer FAIL;
- First Cross payoff-rescue = CLOSED;
- V5-037A = preregistered external-state mechanism audit;
- GOLD# 2021 remains untouched;
- production authority remains NONE.

Read `V5_037A_GOLD_REAL_YIELD_DIRECTIONAL_DELIVERY_CONTRACT.md` before new empirical work. Point-in-time DFII10 release history must be qualified before Stage 1.
