# V6 — Event-Conditioned Generalization Research Authority

Status: `ACTIVE RESEARCH AUTHORITY`
Date: `2026-08-28`
Production authority: `NONE`
Primary market: `GOLD#`

Parent generations:
- V1 `FROZEN deterministic control`
- V2 `PAUSED / preserved`
- V3 `PAUSED / negative strategy authority + important mechanism/event evidence`
- V4 `PAUSED / preserved AI research; practical failure = no useful learned signal`
- V5 `CLOSED / historical success-first + payoff-first evidence`

## 1. Mission

V6 exists to solve the central limitation exposed by V3 and not solved by V4:

```text
the same apparently meaningful GOLD event/state
can have different outcome meaning across periods/regimes/markets
```

V3 tried to solve this with hand-authored state variables and filters.
V4 tried to replace the ontology with generic raw-sequence prediction but did not obtain meaningful learning.

V6 therefore uses a middle abstraction:

```text
causally meaningful event anchor
+ raw multi-resolution market state
+ optional synchronized cross-market context
-> learned / statistical representation
-> stability and information tests
-> only later policy
```

V6 is NOT defined by a specific AI architecture.
Its novelty is the research formulation and generalization discipline.

## 2. Mandatory startup order

Every V6 session must:

1. check latest GitHub HEAD;
2. read root `AGENTS.md`;
3. read root `docs/ea/HANDOFF.md`;
4. read this file;
5. read `HANDOFF_V6.md`;
6. read `RESEARCH_STATE_V6.md`;
7. read `V6_000_RESEARCH_CONTRACT.md`;
8. read `V6_FAILURE_MAP_V3_V4_V5.md`;
9. read `V6_001A_CONTEXT_INFORMATION_AUDIT.md`;
10. read `BACKLOG_V6.md`;
11. read `../v5/V5_FINAL_SYNTHESIS.md`;
12. read V3 D145/D146/D148 and V3-003G validation documents when working on event semantics or labels;
13. read V4 model/spec/literature documents when reusing representation code;
14. inspect exact current code and data before implementation.

GitHub wins over chat memory.

## 3. Non-negotiable problem facts

### 3.1 V3 failure must be treated as real

V3 produced encouraging GOLD 2023-2025 discovery relationships and a promising Candidate B, but GOLD 2022 validation and other-market checks broke the apparent edge.

Therefore V6 must assume:

```text
period-specific relationship is the default risk
```

A model or feature that works in 2023-2025 does not earn authority by pooled performance.
Chronological sign stability is mandatory.

### 3.2 V4 no-learning must be treated as real

The practical V4 stopping reason was that multiple attempts did not produce useful learning.

Therefore V6 may NOT respond to failure by automatically trying:
- a bigger Transformer;
- another pretrained foundation model;
- JEPA because it is newer;
- RL/agent policy learning;
- broad hyperparameter search.

A simpler information/learnability test must pass first.

### 3.3 V5 narrowed the problem

V5 showed:
- payoff architecture cannot always be repaired after Entry;
- strong-looking state relationships may fail cross-architecture transfer;
- point-in-time external macro state is not automatically useful;
- late event-conditioned GOLD-only raw-path probes still showed chronological instability;
- synchronized XAUEUR/USDJPY context produced the first small same-direction improvement across 2024 and 2025, but a same-capacity placebo was not completed.

V6 begins exactly there.

## 4. Final economic target

Any eventual strategy must still target:

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2.0R
cost-adjusted expectancy     > 0
```

Additionally:
- multiple independent periods;
- more than one structurally compatible market before final promotion;
- acceptable drawdown/loss streak;
- no unacceptable winner concentration;
- execution parity including spread/commission/slippage.

Do not force every winner to 2R merely to satisfy the metric.

## 5. Separation of research stages

V6 separates at least these questions:

```text
A. event meaning / Entry survival
B. winner continuation
C. payoff capture / exit lifecycle
D. execution
E. market suitability
F. portfolio / exposure
```

A feature/model discovered for A does not automatically become a rule for B or C.

## 6. Event anchor policy

The initial V6 event anchor is the exact V3-003C `BROAD CONTROL`, because it provides meaningful causal event semantics without applying the later hand-authored V3 selection gates.

Expected parity:

```text
2023 84 events
2024 86 events
2025 67 events
total 237
```

The initial anchor includes:

```text
persistent M15 intermediate liquidity
-> atomic same-M1 sweep/recovery
-> pre-sweep M5 owner opposite reaction
-> sweep extreme intact
-> first completed M5 owner transition back with reaction
-> trigger-close Entry
-> sweep-extreme structural SL
```

Do NOT filter the V6 learning population by:
- DELIVERY_ACTIVE;
- STRONG_ACCEPTANCE;
- Candidate A;
- Module H/L;
- Candidate B.

Those are consumed V3 discoveries and may be reported only as descriptive references.

V6 is allowed to later define a new event family, but only through a separate preregistered phase. Do not silently mutate the anchor after seeing model outcomes.

## 7. Causal input rules

At event time `t`, every input must be available by `t`.

Initial causal histories may reuse the V4 multi-resolution horizon:

```text
M1   256 completed bars
M5   192 completed bars
M30   96 completed bars
H4    42 completed bars
```

No still-open higher-timeframe bar may be used.

Cross-market context must use only bars available no later than the GOLD anchor time. Alignment staleness must be explicitly represented or audited.

No future-normalized feature.
No outcome-derived normalization.

## 8. Model progression rule

Models exist to test information, not to create authority by complexity.

Use this order:

```text
simple linear / ridge / raw-convolution probe
-> stable chronological information?
    no  -> stop or reformulate the information question
    yes -> self-supervised representation may be justified
-> stable representation across environments?
    no  -> study hidden context / concept drift
    yes -> survival / continuation model
-> policy only after information is stable
```

Do not run a model tournament and select the winner from the same consumed outcomes.

## 9. Non-stationarity rule

V6 explicitly treats these as different hypotheses:

```text
covariate shift: P(X) changes
concept shift:   P(Y|X) changes
hidden context:  relevant state is omitted from X
```

Do not call every failure `regime change` without testing which class is plausible.

Online/test-time adaptation is NOT the first response.
It becomes eligible only after static hidden-context tests fail or remain insufficient, and it must use strictly past information/labels.

## 10. Validation rules

Primary chronology for the initial event population:

```text
train 2023       -> evaluate 2024
train 2023-2024  -> evaluate 2025
```

Do not pool years first and cross-validate randomly.

GOLD 2022 is already consumed by V3.
It may later be used only as a harsh falsification/stress test after the V6 pipeline is frozen; it cannot promote the method.

GOLD# 2021 remains closed.

Any final strategy must later use a genuinely independent period/market allocation.

## 11. Controls are first-class research objects

A model improvement is not accepted without a control capable of explaining it away.

Examples:
- same-capacity GOLDx3 context placebo;
- stale cross-market context;
- time-block/domain controls;
- exact mirror stress where meaningful;
- class-prior baseline;
- consumed V3 hand-state reference, clearly labeled non-OOS.

If a control explains the improvement, close the claim.

## 12. Documentation

Material negative findings must be documented.
Do not document every trivial failed hyperparameter.

Update:
- `RESEARCH_STATE_V6.md` when phase classification changes;
- `HANDOFF_V6.md` when the next-session task changes;
- `BACKLOG_V6.md` when stages close/open;
- a phase result document for any material pass/fail;
- decisions for any rule that constrains future research.

No production EA change is authorized by V6 startup.
