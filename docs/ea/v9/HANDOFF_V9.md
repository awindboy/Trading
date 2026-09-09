# V9 Development Handoff

Last updated: `2026-09-10`
Status: `ACTIVE V9 / JUNE CONSUMED / POST-JUNE EXECUTION-RUNTIME BUILD`
Current phase: `SIMPLIFY AI DUTIES -> BUILD DETERMINISTIC STRUCTURE + PRECOMMITTED ORDER RUNTIME -> CONSUMED-DATA PARITY TEST`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Resume order

Start from latest GitHub HEAD, then read:

1. `AGENTS_V9.md`
2. this file
3. `RESEARCH_STATE_V9.md`
4. stable mindset authority
5. `DECISIONS_V9_POSTJUNE_SIMPLIFICATION_AND_RUNTIME_ADDENDUM_20260910.md`
6. June execution-environment postmortem
7. causal numeric tooling protocol dated 2026-09-10
8. deterministic execution-runtime protocol dated 2026-09-10
9. precommitted-order / AI-call scheduler protocol dated 2026-09-10
10. post-June discretionary pipeline dated 2026-09-10
11. active post-June research contract
12. implementation/parity state.

Do not resume future-hidden trading until the active contract's runtime gate is satisfied.

---

## 2. Why the phase changed

June showed two things simultaneously.

First, May's one-sided directional drift improved: both LONG and SHORT opportunities were considered.

Second, the execution process became too dependent on AI interpretation and compliance prose. The system could describe many `Child`, `repair`, `memory`, and `campaign` states while still lacking a reproducible objective route map and event-driven review environment.

This created a bad failure mode:

```text
more documentation
-> more AI interpretation work
-> not necessarily better pitch selection
```

The correction is **not** to make the AI more sophisticated.

The correction is:

```text
code handles what code can handle exactly
AI handles only what genuinely requires discretionary judgment
```

---

## 3. Permanent philosophy retained

```text
market understanding != direction prediction != good trade
```

V9 is allowed to lose repeatedly.

Two or three ordinary stops are not a problem if they came from genuinely worthwhile pitches with bounded risk.

But six or ten stops in a cluster must trigger research scrutiny. V9's baseball principle does not mean every causally new move is a pitch worth swinging at.

The intended payoff architecture remains:

```text
several -1R attempts can be acceptable
provided a genuine winner is allowed to become materially larger
```

Do not redesign V9 into a high-win-rate scalp system.

---

## 4. Parent/Child retained, taxonomy reduced

Parent remains the larger working belief.

Child remains one current paid attempt.

Retain:

- Child stop != Parent death;
- Parent survival != immediate re-entry permission;
- later same-direction movement cannot rescue a stopped Child;
- same-side retry asks `WHAT IS NEW?`.

Remove from mandatory execution:

- elaborate Child type labels;
- mandatory memory-role naming;
- mandatory repair/reclaim taxonomy;
- long-form per-trade prose proving every conceptual label.

These may remain descriptive commentary only.

---

## 5. June failure transfer

Three main mechanisms were observed:

1. **same-auction churn** — local events inside broad rotation were repeatedly promoted into paid attempts;
2. **falsification scale mismatch** — very local M15/M1 structures sometimes carried full Parent-Journey stop authority without enough justification;
3. **small-winner / late-review behavior** — Parent-Journey positions lacked an objective forward structure map and event-driven re-analysis, contributing to both misleading tiny `CP1` reporting and large MFE giveback.

These findings do not authorize minimum stop distance, N-loss cooldown, or fixed take-profit rules.

---

## 6. Active implementation target

Build a deterministic runtime that supplies the same packet to any AI:

```text
raw causal price facts
objective structure IDs and price ranges
structure provenance
Entry/SL geometry
R
S
forward structure distances
structure-touch/cross events
next authorized review time
```

AI then answers only:

```text
Parent working belief + opposite case
Good pitch or no trade?
Which mapped structure falsifies this attempt?
Local Bridge or Parent-Journey?
At review: HOLD / EXIT / REMAP?
```

---

## 7. Prepared-pitch API environment

No continuous large-model observation.

The target lifecycle is:

```text
planning call
-> prepared conditional setup
-> pending entry/trigger ARMED
-> local M1 monitoring
-> entry / cancel / expiry / invalidation
-> if filled: precommitted SL + destination/review events
```

Important operational transfer:

- a good pitch is preferably prepared before price reaches it;
- the large model should not be called after every new candle to discover another possible trade;
- fast live entry cannot depend on waiting for model latency after the price event;
- replay should skip directly between precommitted relevant events without exposing intermediate candles to AI.

Local Bridge normally uses precommitted entry + SL + fixed destination.

Parent-Journey uses precommitted entry + SL + objective future review/remap events; fixed TP may remain NONE.

Maximum-staleness heartbeat is a fail-safe only, not a periodic trade-search instruction.

Read `V9_PRECOMMITTED_ORDER_AND_AI_CALL_SCHEDULER_PROTOCOL_20260910.md`.

---

## 8. Immediate next task

Do **not** trade a new hidden period yet.

First:

1. define/version the objective structure registry;
2. implement deterministic geometry packet;
3. implement deterministic pending-entry trigger types and order state machine;
4. implement cancellation/expiry/OCO/bracket semantics;
5. implement event-driven AI scheduler and maximum-staleness fail-safe;
6. implement minimal planning/review AI schema;
7. replay consumed June episodes in setup-armed mode for parity only;
8. measure AI-call reasons/counts and confirm intermediate candles are not unnecessarily exposed;
9. confirm identical structure/geometry/order/event outputs across repeated runs;
10. only then freeze the runtime and choose the next future-hidden development period.

`GOLD# 2021` remains untouched.
