# V9 Next Research Contract — Continuous Grammar State-Action Policy

Date: `2026-09-13`  
Status: `ACTIVE NEXT RESEARCH CONTRACT / SUPERSEDES SETUP-CENTRIC NEXT WORK / FUTURE-HIDDEN LOCKED`  
Base GitHub HEAD: `19084062f136474469206eeeee20fadae5943c7f`  
Market: `GOLD# ONLY`  
Production authority: `NONE`  
EA authority: `NONE`  
2024: `CONSUMED POSTMORTEM DATA`  
Future-hidden: `2025-07 LOCKED`  
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. Superseding research question

The active question is no longer primarily:

> Can AI improve the existing COUNTER / WITH_PARENT candidate entries and exits?

That remains a downstream comparison question.

The active question is now:

> Can the continuous V9 Grammar be converted into one causal, compact, reusable state-action policy that knows what to do across the whole market process, not only at two setup branches?

The research chain becomes:

```text
CONTINUOUS GRAMMAR
-> MARKET STATE
-> TRANSITION
-> ROUTE / LANDMARK STAGE
-> POSITION STATE
-> AI ACTION POLICY
-> CAUSAL EXECUTION
```

## 2. Preserve all existing causal infrastructure

Do not rewrite already accepted mechanics merely because the research policy changes.

Retain:

- authoritative M1 source/hash;
- dual-clock `PRICE_REVEALED_CUTOFF` / `INFORMATION_KNOWN_AT`;
- completed-bar causal timing;
- code-owned object geometry/lifecycle;
- exact execution reporting;
- Hard SL fixed before entry and never widened;
- stopped Child is dead;
- Parent/Child separation;
- first-pending-gate safety;
- external-action restart parity;
- exact structural staleness;
- AI outage fail-stop behavior;
- request fingerprinting;
- event batching/coalescing concepts;
- no hindsight rescue/backfill.

The previous causal runtime is a baseline implementation, not discarded work.

## 3. Workstream A — Reproduce branch policy evidence on current main

Before freezing new state or transition counts, reproduce the preliminary branch findings from current authority code/data.

Required consumed inputs only:

```text
2025-01..06
2026-01..02
```

Do not open July or 2021.

Reproduce at minimum:

1. valid H1-hour hierarchical state coverage;
2. state run ledger;
3. transition primitive classification;
4. H1 cycle landmark-event batches;
5. event-batch/day distribution;
6. STRONG versus WEAK interruption-resolution topology;
7. exact unexplained remainder.

The reported `9 states`, `622 transitions`, `615/622`, and `1,828 event batches` are hypotheses to reproduce, not magic constants to force.

If current-main reproduction differs, keep the reproduced result and explain why.

## 4. Workstream B — Build the continuous policy ledger

Create one causal ledger at each meaningful Grammar/route event batch.

Minimum fields:

```text
EVENT_ID
BLOCK
KNOWN_AT
PRICE_REVEALED_CUTOFF

MARKET_STATE
  H4 macro authority / side / agreement
  H4 phase
  H1 auction role
  uncertainty state

TRANSITION
  prior market state
  transition primitive

ROUTE
  active Parent / campaign id if any
  current H1 auction id if any
  active code-owned landmarks
  newly arrived / delivered / retired landmarks
  route-stage research label

POSITION_STATE
  FLAT / ARMED / OPEN_PARENT / OPEN_COUNTER / REMAP_PENDING / other explicit state

CAUSAL_CONTEXT
  selected H4/H1 chart identity
  partial-H1 identity when enabled
  object-ledger hash
  causal-prefix hash

ACTION_RESEARCH
  action
  confidence / unresolved status
  rationale
```

Do not insert later outcome or future price into policy inputs.

## 5. Workstream C — Compress State / Transition / Route vocabulary

Start from the preliminary compact vocabulary, but allow the current-main evidence to correct it.

Candidate market-state axes:

```text
H4 PHASE: MIGRATION / LOCAL_INTERRUPT / NEUTRAL
H4 AUTHORITY: STRONG / WEAK / NEUTRAL-AMBIGUOUS
H1 ROLE: ALIGNED / H1_INTERRUPT / UNRESOLVED
```

Candidate transition primitives:

```text
H1_INTERRUPT_BEGINS
H1_REALIGNS
H4_LOCAL_INTERRUPT_BEGINS
H4_MIGRATION_RESUMES
AUTHORITY_WEAKENS
AUTHORITY_STRENGTHENS
ENTER_NEUTRAL
LEAVE_NEUTRAL
OTHER / UNRESOLVED
```

Candidate route vocabulary:

```text
AUCTION_ORIGIN
IN_TRANSIT
LANDMARK_ARRIVAL
RESPONSE
DELIVERY
RESOLUTION
UNRESOLVED_ROUTE
```

Compression criterion:

> use the smallest vocabulary that preserves decision-relevant distinctions across both consumed blocks and difficult periods.

Do not optimize state definitions for P/L or classification accuracy.

## 6. Workstream D — Unified action vocabulary

Use a small reusable action set rather than one strategy per state.

Initial candidate actions:

```text
WAIT
ARM_PARENT
ARM_COUNTER
ENTER
HOLD
EXIT
REMAP
RESET
```

This action set is research vocabulary, not frozen execution authority.

Important rule:

```text
ALL STATES MUST HAVE AN ACTION MEANING
!=
ALL STATES MUST OPEN A TRADE
```

`WAIT / UNRESOLVED` is a complete action when the market has not supplied enough information.

## 7. Workstream E — Decision-sufficiency study

Run causal sequential review across the consumed policy ledger.

For each event batch, AI receives only information known at that event and returns the research action.

Measure:

- whether action semantics repeat across similar state/route contexts;
- whether the same vocabulary works in 2025H1 and 2026JF;
- where AI repeatedly returns `UNRESOLVED / WAIT`;
- where the same nominal state requires contradictory actions;
- which contradiction can be explained by route stage / position state;
- which contradiction implies a missing causal variable;
- whether a proposed missing variable improves explanation across many consumed cases rather than one example.

Do not use future result to rewrite the original action.

## 8. Workstream F — Grammar events become primary AI wake candidates

The first scheduler candidate for unified-policy research is the market's own meaningful event batch, not trade-P/L milestones.

Candidate wake families:

```text
state transition
H1 interruption / realignment
H4 phase transition
H4 authority strengthening / weakening
neutral entry / exit
meaningful code-owned landmark arrival
liquidity delivery
route-resolution event
Parent authority change
```

Same information batch must produce one AI request with multiple reason codes.

Existing trade-management events such as:

```text
R_MILESTONE
FIRST_FAVORABLE_DELIVERY
POST_DELIVERY_M15_NONSUPPORT
```

remain researchable downstream reasons, especially while a position is open, but they do not define the top-level continuous market policy.

Do not add an arbitrary price-shock threshold.

## 9. Workstream G — Position state is part of policy input

The same market state may imply different actions depending on position state.

Research at minimum:

```text
FLAT
ARMED_PARENT
ARMED_COUNTER
OPEN_PARENT
OPEN_COUNTER
REMAP_PENDING
```

Examples of questions:

```text
FLAT + migration/transit
-> wait for actionable arrival or arm continuation?

OPEN_PARENT + same coherent route
-> hold or review?

OPEN_COUNTER + Parent reacceptance
-> hold, exit, or remap?

Parent side change + old Child alive
-> exit / remap / reset?
```

Do not let Child P/L itself define Parent authority.

## 10. Workstream H — H1-native execution comparison

Only after the unified policy vocabulary is stable enough to generate causal actions should execution scale be compared.

Required variants:

### Variant A — PURE H1 NATIVE

```text
H4/H1 own semantic authority
running H1 may be constructed from revealed M1
M1/tick owns exact event/execution chronology
M15/M5 hidden from AI semantic decision
```

### Variant B — H1 AUTHORITY + LTF EXECUTION AID

```text
H4/H1 own thesis/action authority
M15/M5 visible only after H1 policy arms a trade
LTF may help execution timing/geometry
LTF cannot independently create a new trade thesis
```

### Variant C — CURRENT V9 BASELINE

```text
COUNTER / WITH_PARENT candidate universe
M15 authorization
M5 execution geometry
```

Compare using the same consumed-data causality and risk accounting.

Do not declare Variant A superior merely from the `WITH_PARENT FIRST` proxy.

## 11. Partial-H1 causal contract research

If Variant A/B uses the forming H1 candle, freeze a versioned partial-bar contract before performance comparison.

Required fields include:

```text
PARTIAL_H1_VERSION
PARTIAL_H1_ASOF
SOURCE_LAST_M1_AT
OPEN / RUNNING_HIGH / RUNNING_LOW / LAST_PRICE
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
SOURCE_PREFIX_HASH
```

Rules:

- construct only from actually revealed M1;
- never use final H1 high/low/close before completion;
- no tick-chart discretionary pattern mining by default;
- exact BID/ASK/tick ordering remains execution authority where available;
- any accidental reveal contaminates the interval and forbids hindsight trade insertion.

## 12. Where 2024 belongs

Do not use 2024 to invent the policy vocabulary first.

Preferred order:

```text
2025H1 + 2026JF consumed Atlas
-> policy semantics / decision sufficiency
-> freeze research policy version
-> 2024 consumed tick replay as execution/performance/postmortem comparator
```

2024 is already consumed and can be used for research, but it must never again be described as untouched/OOS validation.

## 13. Existing setup-centric research status

The following remain valuable but are now subordinate/historical research tracks:

```text
COUNTER / WITH_PARENT first strategy extraction
event-driven entry-AI study
R-milestone management scheduler
45 fast-loss blind entry study
21 giveback versus large-winner review
```

Do not delete their ledgers or code.

Use them as:

- causal baseline;
- comparator;
- counterexample source;
- proof that event != action;
- evidence against aggressive winner-cutting rules.

Do not continue optimizing them before the unified-policy study unless required to preserve runtime parity.

## 14. ML status

ML remains retired from the active path.

Do not use ML for:

- direction authority;
- AI-call authority;
- trade action authority.

Only reconsider after the deterministic unified-policy scheduler is measured and a concrete operational deficiency remains.

## 15. Required outputs before any future-hidden gate reconsideration

The project must produce:

1. reproduced current-main state/run/transition/event ledgers;
2. versioned continuous policy-event ledger;
3. compact State / Transition / Route / Position vocabulary;
4. decision-sufficiency report with difficult-period counterexamples;
5. causal AI action ledger across 2025H1 and 2026JF;
6. explicit unresolved-state inventory;
7. frozen partial-H1 contract if used;
8. H1-native A/B/C consumed comparison;
9. 2024 consumed causal replay of the selected policy candidate;
10. implementation/parity tests for any new scheduler or runtime state;
11. frozen packet/chart/prompt/model-role/runtime hashes.

Only then may the future-hidden gate be reconsidered.

## 16. Permanent guardrails

Do not:

- open `2025-07`;
- touch `2021`;
- create state-specific hidden thresholds;
- force `AMBIGUOUS` into a direction;
- turn state base rates into automatic LONG/SHORT rules;
- assume one H1 cycle permits only one Child;
- create a fixed retry/cooldown from `FRESH_REAUTH` evidence;
- delete M15/M5 before controlled comparison;
- turn landmark arrival/delivery into automatic exit;
- use fixed minimum-R / TP / BE / trailing;
- rescue a stopped Child;
- let future outcome rewrite the original policy decision;
- alter authority from one or two examples.

Retain:

- fixed pre-entry Hard SL, never widened;
- Parent/Child separation;
- large-winner participation;
- explicit uncertainty;
- exact code-owned geometry;
- causal replay and fail-closed tooling.

## 17. Future-hidden gate

No status change:

```text
2025-07 = LOCKED
2021    = UNTOUCHED
```

The current future-hidden gate remains `NOT SATISFIED`.
