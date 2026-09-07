# V9 Next Research Contract — Exit/Distance, Sequential Continuation, and Open Route

Date: `2026-09-07`
Status: `PREREGISTERED DEVELOPMENT CONTRACT / NO PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`
Expected base HEAD: `0880cafaac8752e2976ca970244dab6a215955d9`
Raw M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Final untouched reserve: `GOLD# 2021`

## 1. Purpose

The January 2025/2026 replay suggests that V9 entry/location reasoning is more mature than its Exit/Distance architecture.

Do **not** reopen entry design in this phase.

This phase studies three separate problems:

```text
A. routine bridge capture
B. sequential continuation after CP1
C. open-route / price-discovery entry
```

The goal is not to maximize P/L on the consumed January examples. The goal is to stabilize causal language and find counterexamples before any formal exit rule exists.

---

## 2. Frozen controls

### Entry Control

Keep the existing discretionary Decision Corridor entry logic unchanged:

```text
parent context
child route
thesis-dependent falsification
next active memory / route state
structural room
uncertainty
```

### Exit Control A

```text
first natural destination / CP1 reached
-> original trade resolves
-> 100% descriptive exit
```

This is a research control, not final production authority.

### Distance coordinate

```text
S(t) = previous fully completed H4 Wilder ATR14
```

Structure first; S normalization second.

---

## 3. Required pre-entry fields for every new trade

Freeze before future reveal:

```text
decision timestamp
direction
parent context
WHAT parent context changes in the decision
current child route
falsification anchor zone
observable behavior that counts as genuine restoration/invalidation
first intervening memory
why the intervening memory is active or consumed
first natural destination OR OPEN ROUTE state
Risk/S
CP1/S when CP1 exists
execution-continuity uncertainty
remaining ambiguity
```

No later rewrite of these fields.

---

## 4. Track A — Routine bridge control

Use existing V9 behavior.

If CP1 is reached before falsification:

```text
RESOLVED
```

Exit Control A is recorded.

Any later route is not allowed to rescue or extend the original trade retrospectively.

---

## 5. Track B — Sequential continuation re-entry

After CP1 resolution, observe the market without carrying a forced runner.

A continuation idea becomes `ARMED` only if CP1 earns a new role, for example through causal acceptance/consumption.

But:

```text
CP1 consumed != TRADEABLE
```

A new continuation trade requires all of:

1. a **new** causally earned thesis-dependent falsification anchor;
2. a clear statement of what genuine restoration of that anchor means;
3. no skipped intervening active memory;
4. enough S-normalized route room to justify a new decision;
5. a separate trade ID and lifecycle.

This explicitly tests whether large winners are better built as sequential bridges than passive runners.

---

## 6. Track C — Open Route / Price Discovery

Declare `OPEN ROUTE` only when:

1. the last meaningful directional memory has been genuinely consumed/translated through;
2. the causally available higher-timeframe history has been checked far enough back;
3. no meaningful downstream active memory remains visible/relevant.

Then:

```text
OPEN ROUTE != TRADE
```

Trade requirements:

- do not chase the discovery impulse;
- wait for a pullback/repair or another causally earned local structure;
- the proposed anchor must truly negate the open-route thesis if restored;
- do not use a cosmetic micro-low/high merely to reduce Risk/S;
- record Risk/S before entry;
- record whether new endogenous scars/checkpoints form after entry.

There is no fixed TP authority in this track.

Management remains thesis-based and must be documented sequentially.

---

## 7. Exit/continuation observations to collect

For every CP1 or open-route trade record shadow-only:

```text
CP1 role after arrival:
  REACTION / REJECTION / ACCEPTANCE / CONSUMPTION / AMBIGUOUS

max favorable excursion in R and S
max adverse excursion in R and S
when a new falsification anchor first became causally available
how much MFE had already been given back by that recognition time
whether exit-then-re-enter would have produced a valid new corridor
```

The critical variable is **capture latency**, not merely ultimate MFE.

---

## 8. Negative evidence required

Deliberately seek:

- CP1 consumption followed by failed continuation;
- open route followed by immediate restoration;
- a visually good pullback whose proposed anchor is not actually thesis-dependent;
- sequential re-entry that loses;
- correct NO TRADE in price discovery;
- high-R but tiny-S bridge that does not continue;
- large-S route with poor R due wide falsification;
- gap / execution-discontinuity cases.

Do not promote the family until these negatives exist.

---

## 9. Explicit prohibitions

Do not:

- optimize a CP1 partial percentage;
- introduce fixed ATR TP/SL multiples;
- use V8 extension probability as an entry veto;
- make `consumption` a binary mechanical signal;
- define open route from a fixed lookback window only;
- skip an intervening memory to increase R;
- move SL because of unrealized P/L alone;
- rescue a failed thesis with later same-direction movement;
- open GOLD# 2021;
- claim validation economics from 2025/2026 development replay.

---

## 10. Promotion gate

Before formalizing any exit/open-route rule, require:

1. multiple sequential-continuation wins and losses;
2. multiple open-route wins, losses and correct skips;
3. stable behavior-language for restoration/consumption;
4. substantially similar decisions across independent AI/session replays;
5. no frequent post-sample vocabulary edits;
6. later execution-aware testing;
7. only then preregister an economics comparison.

Until then:

```text
Production authority: NONE
EA authority: NONE
```
