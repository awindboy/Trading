# V3 Research Authority — Raw-Market-Data Strategy Laboratory

Status: `ACTIVE RESEARCH LINE`
Effective date: `2026-08-24`
V1: `FROZEN HISTORICAL DETERMINISTIC CONTROL`
V2: `PAUSED / PRESERVED RESEARCH CONTROL`
2021: `KEEP UNTOUCHED`

## 1. Purpose

V3 exists because the current deterministic V2 entry chain is too sparse and too
semantically constrained to make fast, reliable strategy discovery practical.

V3 does **not** begin by modifying the MT5 EA.

The V3 workflow is:

```text
raw broker market data
-> offline causal replay laboratory
-> broad event/opportunity universe
-> many explicitly registered strategy hypotheses
-> fast falsification / walk-forward validation
-> small surviving candidate set
-> exact tick replay
-> MT5 Strategy Tester confirmation
-> only then EA implementation
```

GitHub remains the Single Source of Truth.

## 2. Relationship to the mentor method

V3 preserves the mentor method as an important source of causal ideas, but it is
not required to reproduce every discretionary statement literally.

Preserve:

```text
causal ordering
no look-ahead
meaningful liquidity / reaction logic
structure before entry
realistic spread / Bid-Ask / execution
separation of Entry survival and payoff management
```

Open to redesign:

```text
wave detector
structure detector
M1-only trigger
protected-break-only CHOCH
liquidity families
Root definition
continuation-only scope
reversal/internal-rotation scope
FVG selector
entry geometry
SL geometry
objective selection
timeframe routing
session treatment
```

A V3 rule may depart from the mentor's literal discretionary wording if:

1. it is causally available at decision time;
2. it has a coherent market/mechanical interpretation;
3. its discovery and validation are separated;
4. it survives independent market/time validation;
5. it improves the final economic objective rather than only one fitted statistic.

## 3. Primary objective

The strategy objective remains:

```text
cost-adjusted realized WR >= 50%
average winner meaningfully > 1R
positive expectancy after spread/commission/slippage/swap
acceptable drawdown and losing streak
robustness across independent markets and periods
```

The >=70% realized-WR objective remains a stretch target, not a reason to overfit.

V3 adds a first-class research concern:

```text
opportunity frequency / evidence density
```

A strategy that produces only a very small annual sample is not automatically
invalid, but it must be classified as `SPARSE` and cannot be treated as broadly
validated without either:
- much longer independent history; or
- a compatible multi-market universe that raises independent sample density.

Do not add trades merely to hit a quota.

## 4. Data split

Initial V3 research allocation:

```text
2023-2025
    DISCOVERY / DEVELOPMENT LAB

2022
    V3 VALIDATION VAULT
    do not inspect for V3 hypothesis selection

2021
    KEEP UNTOUCHED
```

If later review proves that 2022 was materially used to shape the exact V3
hypothesis being tested, it loses vault status and a different untouched period
must be frozen before validation.

Never move a failed discovery rule's threshold after opening the validation vault.

## 5. Two-level replay architecture

### Level A — fast M1 laboratory

Primary discovery input:

```text
broker-server M1 bars
time
open
high
low
close
tick_volume
real_volume if available
spread
```

All higher timeframes are rebuilt causally from M1.

Use Level A for:
- structure alternatives;
- liquidity definitions;
- Root/context alternatives;
- M1/M5 adaptive trigger logic;
- FVG/OB candidate construction;
- session/regime experiments;
- standardized barrier outcomes;
- opportunity-frequency census;
- broad strategy-family search.

### Level B — exact tick replay

Use tick data only for candidates that survive Level A.

Use it for:
- same-bar ordering;
- Bid/Ask execution;
- exact pending fill;
- SL vs +1R barrier race;
- spread dynamics;
- slippage model sensitivity;
- intrabar Root-contact/sweep ordering.

Do not pay tick-level compute cost for obviously weak hypotheses.

## 6. Research unit

The primary discovery population is **not current EA fills**.

V3 first constructs an outcome-blind event universe containing, as applicable:

```text
structure swings / legs
liquidity pools
zone candidates
Root/context contacts
sweeps
local structure transitions
M1/M5 trigger events
FVG/OB execution candidates
first retests
```

Strategies select from this common universe.

This allows V3 to discover opportunities that V1/V2 never generated.

## 7. Hypothesis governance

Every experiment must record:

```text
experiment_id
data used
strategy family
causal inputs
entry definition
SL definition
outcome definition
parameters searched
selection criterion
validation set
result
decision
```

Prefer natural structural parameterizations over arbitrary dense grids.

For broad search:
- use walk-forward or leave-year-out evaluation;
- report parameter stability, not only the best point;
- report per-year and per-direction results;
- use bootstrap/confidence intervals where useful;
- account for repeated hypothesis search before promotion;
- retain negative results.

Do not hide a failed year inside a pooled aggregate.

## 8. Machine learning boundary

ML is allowed as a **hypothesis discovery instrument**.

Allowed examples:

```text
regularized logistic regression
tree/boosting models
random forests
clustering
survival models
feature interaction discovery
```

The first purpose is to reveal repeatable relationships and interactions.

Default final strategy target remains a transparent deterministic rule or compact
state machine that can be implemented and audited in MT5.

A black-box live model requires a separate future authorization.

## 9. Separation of research stages

Keep separate:

```text
opportunity generation
Entry survival
winner continuation
exit architecture
execution
market suitability
portfolio/exposure
```

A variable discovered in one stage does not automatically receive authority in another.

V2 V3E/SP evidence is preserved as exit-management research, but V3 entry discovery
starts with standardized causal outcome labels before importing a complex exit policy.

## 10. Promotion into MT5

Do not implement every V3 hypothesis in MQL5.

Only a small candidate set that survives offline discovery and independent validation
is promoted to exact MT5 testing.

Required sequence:

```text
offline discovery
-> frozen candidate
-> independent offline validation
-> exact tick replay
-> MT5 Strategy Tester reproduction
-> execution parity
-> controlled EA implementation
```

MT5 remains the final execution authority.

## 11. Current phase

```text
V3-003G CANDIDATE-B 2022 INDEPENDENT VALIDATION — FAIL
NEXT: DEFINE A NEW DISCOVERY ALLOCATION / ARCHITECTURE RESEARCH PROTOCOL
```

Validation result:

```text
V3_DUAL_RELOAD_CANDIDATE_B
24 accepted trades
positive 25.0%
avg positive +1.458R
EV -0.385R/trade
classification FAIL
```

Authority:
- read `V3_003G_CANDIDATE_B_2022_VALIDATION_RESULTS.md`;
- Candidate B is a frozen failed-validation artifact;
- do not retune Candidate B using 2022 or reopen 2023-2025 for threshold rescue;
- H3/BOTH exclusion remains a shadow diagnostic and was not retrofitted into the failed validation;
- 2022 is consumed validation data;
- 2021 remains untouched;
- before new strategy discovery, pre-register a new market/time allocation without outcome peeking;
- no exact-tick, MT5 or EA promotion is authorized.

## V3 research escalation rule ??2026-08-25

V3 must not remain trapped in low-level optimization.

When several natural variants of one component fail to improve cross-period robustness:

```text
L1 component failure
-> question L2 architecture

L2 architecture failure
-> question L3 fundamental assumption
```

Examples:

```text
FVG depth variants all unstable
-> ask whether FVG retracement Entry is needed at all

multiple direction horizons fail
-> ask whether fixed direction classification is the wrong problem

multiple Entry filters fail
-> ask whether the same setup is being traded in different auction states
```

Every complex strategy concept should be compared with a simple causal control.

Negative results are project authority for avoiding repeated dead-end research.

Current V3 market scope is GOLD-first.

