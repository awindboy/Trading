# V9 Discretionary Trading Pipeline — Post-June Prepared-Pitch AI Contract

Date: `2026-09-10`
Status: `ACTIVE PIPELINE DESIGN / USE AFTER RUNTIME PARITY GATE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Purpose

V9 is a baseball-style discretionary strategy:

```text
predicting direction != good trading
```

A few bounded Child losses are acceptable when the trader avoids marginal pitches and participates materially when a strong Parent-scale journey works.

The AI should therefore not inspect every candle looking for new trades.

Its primary job is to **prepare a worthwhile conditional pitch in advance**, then let the runtime wait for price.

Read together with:

- `V9_DETERMINISTIC_EXECUTION_RUNTIME_AND_STRUCTURE_PACKET_PROTOCOL_20260910.md`
- `V9_PRECOMMITTED_ORDER_AND_AI_CALL_SCHEDULER_PROTOCOL_20260910.md`
- `V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`

---

## 2. Planning state — default while flat

The default flat state is not continuous trade search.

At an authorized planning call, runtime supplies deterministic H4/H1 context and the objective structure/geometry packet.

AI answers:

```text
PARENT_WORKING_BELIEF: one line
STRONGEST_OPPOSITE_CASE: one line
SETUPS: NONE or one/more PRECOMMITTED SETUP records
```

`NONE` is a valid result.

The question is:

> What future price condition, if reached, would be worth one bounded swing?

not:

> Is there something to trade right now?

---

## 3. Prepared setup

For each worthwhile pitch the AI freezes:

```text
SETUP_ID
SIDE
ATTEMPT_THESIS
SCALE: LOCAL_BRIDGE / PARENT_JOURNEY
ENTRY_CONDITION_TYPE
ENTRY_STRUCTURE_ID
ENTRY_TRIGGER_RULE
SL_STRUCTURE_ID
FIXED_DESTINATION_ID if Local Bridge
REVIEW_STRUCTURE_IDS if Parent-Journey
SETUP_INVALIDATION_CONDITION
SETUP_EXPIRY_CONDITION
```

If this is a same-side retry after a stopped Child:

```text
WHAT_IS_NEW: one objective factual change
```

The runtime calculates all exact order prices, risk points, R, S, and forward-structure distances.

---

## 4. Armed state

Once a setup is `ARMED`, stop asking the AI to reinterpret ordinary candles.

Runtime advances/monitors price until the first relevant precommitted event:

```text
ENTRY FILLED
SETUP CANCELLED
SETUP EXPIRED
SETUP INVALIDATED BEFORE FILL
```

There is no M15-by-M15 `STILL FORMING` loop by default.

That loop is allowed only when the setup itself explicitly requires a deterministic completed-bar confirmation that cannot be expressed as an immediately executable pending order.

---

## 5. Entry and Hard SL

When the entry condition is filled, Hard SL becomes active immediately.

```text
touch = Child finished
never widen
later same-side movement cannot rescue it
```

A Child remains simply:

> the current attempt on which money is at risk.

Do not require the AI to generate an elaborate Child subtype taxonomy.

---

## 6. Local Bridge

A Local Bridge must have a precommitted deterministic destination.

After fill, runtime can normally monitor:

```text
Hard SL vs fixed destination
```

without AI calls.

Whichever resolves first ends the local trade, subject to M1 execution-order ambiguity rules.

An earlier AI exit is permitted only at a precommitted review event that shows the local thesis itself has failed.

---

## 7. Parent-Journey

A Parent-Journey always has a Hard SL but may have no fixed TP.

Before entry the AI selects objective forward structures that justify future discretionary review.

After fill, the default is **HOLD WITHOUT RE-ANALYSIS** until:

```text
Hard SL
or
selected objective review event
or
coarse maximum-staleness heartbeat requiring genuine remap/reassessment
```

At a discretionary review the AI answers only:

```text
HOLD / EXIT / REMAP
EVIDENCE: 1-3 exact price/settlement facts
```

Do not exit solely because:

- profit is +5p or +10p;
- one opposing candle appears;
- the nearest structure was touched;
- a fixed R was reached;
- Stochastic/EMA changed.

The intended payoff architecture accepts giveback when necessary to remain available for a large winner.

---

## 8. Good-pitch and retry discipline

The existence of a new candle, break, reclaim, or local event is not automatically a new pitch.

A good pitch should normally be describable before its entry condition occurs.

After a stop, Parent may survive. But another same-side swing requires a genuinely new prepared setup and concise `WHAT_IS_NEW`.

Do not introduce:

- N-loss limits;
- retry caps;
- minimum R;
- minimum SL;
- generic no-trade range rule.

Repeated losses are audited as possible evidence that the system kept preparing marginal pitches inside the same auction.

---

## 9. Opposite-side fairness

The planning call must preserve:

```text
PARENT_WORKING_BELIEF
STRONGEST_OPPOSITE_CASE
```

The AI may prepare a conditional opposite-side setup if it is genuinely worthwhile and independently executable.

Parent belief is never a direction veto.

No forced LONG/SHORT balance.

---

## 10. AI-call discipline

Large-model calls exist only for genuinely discretionary decisions.

Preferred categories:

```text
PLANNING / REPLANNING
PRECOMMITTED REVIEW EVENT
PARENT-JOURNEY REMAP / HOLD-EXIT DECISION
```

Do not call merely because an M1, M5, M15, or H1 candle completed unless that completion is itself a frozen planning/review condition.

The runtime may continuously process M1 locally without exposing every intermediate candle to the AI.

---

## 11. Session audit

At session end ask only:

```text
Did we prepare too many marginal pitches?
Were repeated stops genuinely different opportunities or repeated attempts inside one auction?
Did we convert ordinary candle noise into new setups?
Did any good winner get managed like a scalp?
Did we ignore real progression damage because we were afraid to exit?
Was opposite-side evidence judged fairly?
```

These are audit questions, not mechanical rules.

---

## 12. Journal

Runtime records factual fields automatically:

```text
setup creation time
entry/cancel/expiry/invalidation condition
entry fill reference
Hard SL
fixed destination if any
p/R/S geometry
MFE/MAE
all order/review event timestamps
AI-call count and reason
```

AI-specific journal fields remain small:

```text
Parent belief
opposite case
why this conditional setup is a good pitch
attempt thesis
selected SL structure
scale
WHAT_IS_NEW if retry
HOLD/EXIT/REMAP decisions
```

This preserves auditability without turning the AI into a form-filling market classifier.
