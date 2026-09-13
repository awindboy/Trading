# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-13`
Status: `ACTIVE / FLOW-ROUTE MARKET GRAMMAR RECONSTRUCTION`
Production authority: `NONE`
EA authority: `NONE`
Market authority: `GOLD# ONLY`
Consumed answer-sheet data: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Consumed postmortem data: `2024-01 through 2024-12`
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 0. First rule on every resume

GitHub `awindboy/Trading` latest `main` HEAD is the Single Source of Truth.

Before any V9 research, read the current documents in this exact order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_FLOW_ROUTE_GRAMMAR_CORE_AUTHORITY_20260913.md`
7. `docs/ea/v9/V9_FLOW_ROUTE_RESEARCH_RECOVERY_CHECKPOINT_20260913.md`
8. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_FLOW_ROUTE_RECONSTRUCTION_20260913.md`
9. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
10. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
11. current code/tool parity state.

Read older strategy, scheduler, state-action, H1-native, COUNTER/WITH_PARENT, or postmortem documents only when historical evidence is specifically needed. They do **not** define current research direction.

## 1. What V9 Grammar means now

The core Grammar is a **continuous price-flow process**, not an H4/H1 alignment classifier.

Canonical semantic sequence:

```text
ORIGIN
-> ACTIVE MOVEMENT / DELIVERY
-> LANDMARK ARRIVAL
-> RESPONSE
-> ACCEPTANCE / REJECTION / FAILURE / RESOLUTION
-> NEXT DELIVERY or ROUTE COMPLETE / RESET
-> NEXT ROUTE
```

The primary semantic unit is:

```text
FLOW_ROUTE / FLOW_LEG
```

not:

```text
one H1 candle
one H4 bar
one alignment label
one H1 interrupt
one H1 realign
one setup
```

The research goal is to explain long contiguous price paths as a small number of meaningful routes that persist through local candle noise.

## 2. H4/H1 labels are context observations, not the Grammar itself

Retain these observations because they are useful context:

```text
H4 authority: STRONG / WEAK / NEUTRAL-AMBIGUOUS
H4 phase: MIGRATION / LOCAL_INTERRUPT / NEUTRAL
H1 local relation: ALIGNED / H1_INTERRUPT / UNRESOLVED
```

But treat them as **observations about an active route**, not as standalone route identities or trade signals.

Critical interpretation:

```text
H1_REALIGN
= price has already moved enough for the H1 classification to align again
!= forecast that the next movement must continue
!= proof a new FLOW_ROUTE began
!= automatic entry authorization
```

Likewise:

```text
H1_INTERRUPT
= local counterflow / balance observation inside the current context
!= automatic counter route
!= automatic exit
```

A route may remain the same while H1 alignment changes several times.
A new route must be earned by route/landmark resolution, not by a candle-state flip alone.

## 3. Landmarks and destinations are first-class Grammar semantics

Code owns exact object geometry and lifecycle for available candidate families.
AI/research assigns strategic meaning.

Keep separate:

```text
GEOMETRIC FACT
vs
FLOW / ROUTE ROLE
```

Candidate flow roles include:

```text
ORIGIN
TRANSIT LANDMARK
ACTIVE DESTINATION
ARRIVAL
RESPONSE AREA
DELIVERY / CONSUMED DESTINATION
ROUTE-COMPLETE / CAMPAIGN-CHANGING LANDMARK
UNRESOLVED ROLE
```

Object existence never equals strategic importance.

## 4. Recovered research that remains usable

The 2026-09-13 research recovery audit found that the useful pre-drift Atlas direction was already present before H4/H1 labels became the semantic center.

Keep these historical ideas/assets:

```text
Stage 1: FLOW LEG / DELIVERY PATH / ARRIVAL / NEXT STATE as the research unit
Stage 2: exact code-owned POI / FVG / OB / swing-liquidity geometry and lifecycle
Stage 3: arrival -> response -> next delivery as the right structural question
Later hierarchy work: H4/H1 topology, uncertainty and neutralization as route context only
```

Use existing strict consumed evidence as raw material:

```text
docs/ea/v9/results/market_flow_atlas/MARKET_FLOW_EVENT_LEDGER.csv
docs/ea/v9/results/market_flow_atlas/POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
```

Do **not** resurrect:

- the early 80-90% response/acceptance figures as forward edge;
- `last accepted probe before next state` or any future-selected last-event logic;
- H1/H4 state flips as FLOW_ROUTE boundaries;
- `H1_REALIGN -> continuation` as Grammar authority.

Read `V9_FLOW_ROUTE_RESEARCH_RECOVERY_CHECKPOINT_20260913.md` for the exact carry-forward boundary.

## 5. Current research question

Do **not** ask first:

```text
Should H1 realign be bought/sold?
Which state has the best R?
Should AI filter this candidate?
Should M15/M5 be removed?
```

Ask:

```text
Where did the current flow originate?
What is the active delivery side?
What meaningful destination is price moving toward?
What did price arrive at?
What response occurred there?
Was the destination accepted, rejected, consumed, or unresolved?
Did the old route continue, complete, or remap?
What is the next route?
```

Only after this route language is compact and causal should trading policy be extracted again.

## 6. Immediate next work — do this before any trading study

Start from the chronological strict arrival stream, not from a trade and not from an H1 realign.

```text
1. build FLOW_ROUTE_EVENT_STREAM from strict POI/liquidity events + authoritative price
2. build ANSWER_SHEET_FLOW_ROUTE_LEDGER over 2025H1 + 2026JF
3. use same-side liquidity deliveries as candidate evidence of an ongoing delivery path, not as a fixed route rule
4. study opposite-side raids/POI responses inside an active path and distinguish local response from genuine route completion
5. attach H4/H1 observations only after route identity has been reconstructed
6. audit H1/H4 observation flips that occur inside one persistent route
7. test the same vocabulary on difficult/transition-heavy periods
8. only then freeze a causal prefix-only FLOW_ROUTE contract
```

No new quantitative route-count authority was established in the recovery session. The next session must create the first actual FLOW_ROUTE ledger rather than inventing counts from the old state ledgers.

## 7. Active research order

Current order:

```text
1. answer-sheet FLOW_ROUTE reconstruction on consumed periods
2. route/origin/destination/arrival/response vocabulary compression
3. difficult-period and counterexample review
4. distinguish route persistence from local H4/H1 observation changes
5. freeze causal FLOW_ROUTE reconstruction contract
6. replay causal prefix-only flow maps
7. freeze AI semantic packet for route interpretation if needed
8. only then extract trading policy / compare mechanical vs AI vs human-discretion research
9. consumed execution/performance replay
10. implementation/parity freeze
11. only then reconsider future-hidden 2025-07
```

## 8. Explicitly retired as current research directions

The following are historical evidence or infrastructure only and must not be resumed as the active research program:

- `COUNTER / WITH_PARENT` as the assumed complete candidate universe;
- direct `H1_REALIGN -> ENTER` research;
- `PURE H1 NATIVE` as a presumed solution;
- the `9-state / 8-transition -> unified state-action policy` pivot as the top-level semantic model;
- entry-AI filtering of existing setup candidates as the main problem;
- R-milestone / first-delivery scheduler as the top-level market model;
- ML direction or AI-call sentinel research;
- state-by-state LONG/SHORT policy tables.

These may be used as comparators after FLOW_ROUTE semantics are stable.

## 9. Permanent causal and trading guardrails

Retain:

- no future peek;
- no hindsight backfill;
- stopped Child is dead and never rescued by later price;
- Parent and Child remain separate;
- Hard SL fixed before entry and never widened;
- exact executable prices/objects come from code/runtime;
- no hidden minimum-R, cooldown, retry cap, fixed no-chase, fixed TP, forced LONG/SHORT balance, or trade/day quota;
- do not turn one/two examples into authority;
- explicit uncertainty is valid information;
- chart semantics and numeric execution authority remain separate;
- `PRICE_REVEALED_CUTOFF <= INFORMATION_KNOWN_AT` and dual-clock rules remain binding.

## 10. Data boundary

```text
2024        = CONSUMED POSTMORTEM / RESEARCH DATA
2025-01..06 = CONSUMED ANSWER-SHEET DATA
2026-01..02 = CONSUMED ANSWER-SHEET DATA
2025-07     = FUTURE-HIDDEN LOCKED
2021        = UNTOUCHED FINAL RESERVE
```

Do not open July or 2021.

## 11. What counts as progress now

Progress is **not** a new profitable H1 rule.

Progress is:

- a route ledger that explains long contiguous periods without bar-by-bar route flipping;
- exact origin/destination/arrival links to code-owned facts;
- compact response/resolution semantics that survive difficult periods;
- a causal version that can preserve route identity from revealed data only;
- explicit unresolved cases rather than invented certainty.

If a future session starts optimizing H1 realign trades or state-action tables before these gates, it is off-contract.
