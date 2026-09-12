# V9 Continuous Grammar -> Unified State-Action Policy Pivot Checkpoint

Date: `2026-09-13`  
Status: `ACTIVE RESEARCH PIVOT / PRELIMINARY CONSUMED EVIDENCE / NO NEW TRADE RULE AUTHORITY`  
Base GitHub HEAD: `19084062f136474469206eeeee20fadae5943c7f`  
Market: `GOLD# ONLY`  
Production authority: `NONE`  
EA authority: `NONE`  
2024: `CONSUMED POSTMORTEM DATA`  
2025H1 + 2026JF: `CONSUMED ANSWER-SHEET DATA`  
Future-hidden: `2025-07 LOCKED`  
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. Why this pivot exists

The current V9 Grammar explains the market as a continuous hierarchical process:

```text
H4 MACRO AUTHORITY
-> H4 PHASE
-> H1 AUCTION
-> LANDMARK / ROUTE
-> RESOLUTION
-> NEXT STATE
```

The first strategy extraction did not convert the whole process into a trading policy. It selected two narrow candidate paths:

```text
COUNTER
WITH_PARENT
```

then delegated much of the decision authority to M15/M5 authorization/execution logic.

The 2024 tick-AI postmortem and subsequent blind entry/management studies showed that improving only those candidate decisions is not enough. The larger research question is now:

> Did V9 build a useful continuous market model but then discard too much of it by extracting a small setup universe instead of a continuous action policy?

Current decision: this question has higher research priority than further optimization of the existing candidate universe.

## 2. Preliminary branch evidence

A separate consumed-data research branch supplied three related findings. They are important enough to motivate the pivot, but they are **preliminary evidence** until reproduced from the current `main` code/data path.

### 2.1 H1-native proxy inside the 2024 strategy ledger

The existing 2024 strategy result was decomposed as:

```text
all resolved trades           305   +20.51R   PF 1.12   max DD -30.73R
COUNTER                       256   +12.26R   PF 1.09
WITH_PARENT                    49    +8.25R   PF 1.26
WITH_PARENT FIRST              34   +17.05R   PF 1.81   max DD  -6.21R
WITH_PARENT FRESH_REAUTH       15    -8.80R   PF 0.219
```

Interpretation allowed:

> repeated lower-timeframe reauthorization may have fragmented one larger H1 thesis into multiple paid Child attempts.

Interpretation **not** allowed:

```text
one H1 cycle = one trade
H1-native strategy already earns +17.05R
M15/M5 must be removed
fresh reauth is always bad
```

The `WITH_PARENT FIRST` result remains concentrated in large winners and is a proxy, not a native-H1 backtest.

### 2.2 Compact market-state coverage

The branch research reported that `3,401` valid consumed H1 hours were covered by nine hierarchical state combinations built from:

```text
H4 PHASE
H4 AUTHORITY STRENGTH
H1 ROLE
```

Candidate compact state set:

```text
MIGRATION       | STRONG | ALIGNED
MIGRATION       | STRONG | H1_INTERRUPT
LOCAL_INTERRUPT | STRONG | ALIGNED
LOCAL_INTERRUPT | STRONG | H1_INTERRUPT
MIGRATION       | WEAK   | ALIGNED
MIGRATION       | WEAK   | H1_INTERRUPT
LOCAL_INTERRUPT | WEAK   | ALIGNED
LOCAL_INTERRUPT | WEAK   | H1_INTERRUPT
NEUTRAL
```

This is not a frozen nine-state trading model. It is evidence that a continuous policy may remain compact rather than exploding into dozens of independent setups.

### 2.3 Compact transition primitives

The branch research reported `622` state-run transitions, of which `615` (`98.9%`) were represented by eight transition primitives:

```text
H1_INTERRUPT_BEGINS
H1_REALIGNS
H4_LOCAL_INTERRUPT_BEGINS
H4_MIGRATION_RESUMES
AUTHORITY_WEAKENS
AUTHORITY_STRENGTHENS
ENTER_NEUTRAL
LEAVE_NEUTRAL
```

Reported counts:

```text
H1 interruption begins        192
H1 realigns                   159
H4 migration resumes           65
H4 local interrupt begins      63
enter neutral                  48
leave neutral                  48
authority strengthens          29
authority weakens              11
other                           7
```

Again, these counts are preliminary branch evidence. The next research step must reproduce them from the current authority path before they are treated as frozen factual ledgers.

## 3. Why State alone is not enough

A market state such as:

```text
H4 strong UP
H4 migration
H1 aligned
```

can persist for hours. The correct action cannot remain `LONG` throughout that entire run.

The missing policy context is route stage and position state.

Research representation becomes:

```text
MARKET STATE
+
TRANSITION
+
ROUTE / LANDMARK STAGE
+
POSITION STATE
+
CAUSAL CHART / OBJECT CONTEXT
```

A compact conceptual form is:

```text
A_t = policy(G_t, T_t, R_t, P_t, C_t)
```

where:

```text
G = Grammar market state
T = transition primitive
R = route / landmark stage
P = position state
C = causal chart / code-owned object context
```

This is a research model, not yet a frozen runtime schema.

## 4. Route stage becomes a first-class policy variable

Preliminary branch research reported `186` consumed H1 interruption cycles with:

```text
cycles with >=1 landmark event    163
median landmark batches             2
mean landmark batches             2.86
max landmark batches                18
```

Reported route density differed by resolution:

```text
same-Parent realign cycles: mean landmark batches 2.35
Parent side-change cycles: mean landmark batches 4.56
```

This supports treating an H1 auction as a route rather than a single setup.

Candidate route vocabulary for research:

```text
AUCTION_ORIGIN
IN_TRANSIT
LANDMARK_ARRIVAL
RESPONSE
DELIVERY
RESOLUTION
```

Do not turn the labels into deterministic reversal/continuation rules. A POI touch or liquidity delivery is an event that may change route interpretation; it is not automatic trade authority.

## 5. Unified action policy replaces setup-per-state thinking

The objective is not:

```text
state 1 -> strategy A
state 2 -> strategy B
state 3 -> strategy C
```

The objective is one compact action vocabulary reused across the whole Grammar.

Candidate research actions:

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

Every market state should have a coherent action meaning, but **not every state should create new risk**.

Examples:

```text
AMBIGUOUS / NEUTRAL
-> WAIT / information acquisition may be the correct complete policy

strong migration + aligned + position already open
-> HOLD may be the candidate action

side-change earned + old Child alive
-> EXIT / REMAP / RESET becomes the relevant policy family
```

## 6. Decision sufficiency becomes a Grammar test

A stronger Grammar test is now possible.

Old question:

> Can the Grammar describe the historical market continuously?

New question:

> Given only causal information, is the Grammar rich enough to support a repeatable action decision?

If the same state/route context repeatedly requires contradictory actions that cannot be explained causally, then one of two conclusions should follow:

1. the correct action is genuinely `WAIT / UNRESOLVED`; or
2. the Grammar is missing a decision-relevant causal variable.

Do not patch this with hidden thresholds or case-specific setup names.

## 7. Role of H1-native execution

H1-native trading is now a **high-priority execution hypothesis**, not strategy authority.

Candidate hierarchy:

```text
H4 = campaign / context
H1 = auction / route / primary semantic trading scale
M1/tick = running H1 formation + exact execution chronology
```

However, current evidence does not justify deleting M15/M5 information.

The research must separate:

```text
Variant A — PURE H1 NATIVE
H4/H1 semantic input; M1/tick only for partial-H1 construction and execution

Variant B — H1 AUTHORITY + LTF EXECUTION AID
H4/H1 own trade thesis; M15/M5 may assist timing/geometry after policy ARM

Variant C — CURRENT V9 BASELINE
M15 authorization + M5 execution geometry
```

The research question is therefore:

> Is LTF information itself harmful, or was too much strategy authority assigned to it?

No answer is frozen yet.

## 8. Running H1 candle is a research candidate

A native-H1 policy may need to inspect the currently forming H1 auction rather than wait for the completed H1 close.

If researched, partial H1 must be constructed only from revealed M1 and versioned with:

```text
PARTIAL_H1_ASOF
SOURCE_LAST_M1_AT
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
```

No future M1 or later H1 completion may leak into the decision.

`tick/M1` may update running H1 facts and exact execution, but this does not authorize discretionary tick-chart pattern analysis.

## 9. Meaning of prior event-scheduler research

The event-driven AI scheduler work remains useful infrastructure and evidence, but it is no longer the top-level strategy research question.

Retain:

- causal event batching;
- one request per same causal batch;
- stale/supersede/rebuild safety;
- Hard-SL independence;
- chart packet fingerprinting;
- exact execution chronology;
- evidence that event != automatic action.

Reclassify:

```text
R_MILESTONE
FIRST_FAVORABLE_DELIVERY
POST_DELIVERY_M15_NONSUPPORT
```

as downstream review candidates, not the primary definition of when the market itself has produced a meaningful policy event.

The upstream scheduler candidate should first be the continuous Grammar / route event batch.

## 10. Existing strategy extraction remains a baseline

`COUNTER` and `WITH_PARENT` are not deleted.

They remain:

- historical strategy-extraction evidence;
- a fully implemented causal baseline;
- a comparator for future policy variants;
- a source of 2024 postmortem evidence.

They are no longer assumed to define the complete candidate universe for current research.

## 11. What is accepted by this checkpoint

Accepted as **research direction**:

```text
continuous Grammar -> unified state-action policy
route stage is a first-class policy variable
position state is a first-class policy variable
setup extraction is no longer the active top-level research frame
H1-native execution is a priority comparison hypothesis
existing event scheduler becomes downstream infrastructure
ML remains retired
```

Not accepted:

```text
nine states as final production states
eight transitions as final runtime contract
one H1 cycle = one trade
M15/M5 deletion
H1-native performance claim
fixed policy action for any one state
partial-H1 trade authority
new production/live authority
future-hidden unlock
```

## 12. Data boundary

No future-hidden status changes.

```text
2024       = CONSUMED POSTMORTEM DATA
2025H1     = CONSUMED ANSWER-SHEET DATA
2026JF     = CONSUMED ANSWER-SHEET DATA
2025-07    = LOCKED
GOLD# 2021 = UNTOUCHED FINAL RESERVE
```

The preliminary branch evidence must be reproduced on the current `main` consumed path before being frozen as authoritative factual ledgers.
