# V9 Discretionary Trading Pipeline — Post-June Minimal AI Contract

Date: `2026-09-10`
Status: `ACTIVE PIPELINE DESIGN / USE AFTER RUNTIME PARITY GATE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Purpose

This pipeline preserves the V9 discretionary core while preventing the AI from spending most of its capacity satisfying a large conceptual checklist.

The pipeline asks only the decisions that an EA cannot honestly make yet.

---

## 2. Flat H1 review

Runtime supplies deterministic H4/H1 structure and geometry.

AI answers:

```text
PARENT_WORKING_BELIEF: one line
STRONGEST_OPPOSITE_CASE: one line
SERIOUS_CANDIDATE: NONE / LONG / SHORT
```

A Parent belief is not a direction veto.

If no serious candidate: remain FLAT and wait for next H1 heartbeat.

If serious candidate: switch to M15.

---

## 3. Serious candidate M15 review

Each completed M15, AI answers:

```text
PITCH: TRADE / NO TRADE / STILL FORMING
SIDE
WHY_GOOD_PITCH: one or two sentences
```

If a prior same-side Child stopped recently, also answer:

```text
WHAT_IS_NEW: one objective factual change
```

`STILL FORMING` means remain in candidate mode and reveal only the next M15.

Do not reveal the rest of the H1.

---

## 4. Pre-entry decision

If `TRADE`, AI selects:

```text
ATTEMPT_THESIS: one sentence
SL_STRUCTURE_ID
SCALE: LOCAL_BRIDGE / PARENT_JOURNEY
FIXED_DESTINATION_ID: required only for Local Bridge
REVIEW_STRUCTURE_IDS: optional subset of forward mapped structures
```

Runtime automatically writes:

```text
Entry
Hard SL
SL points
1R
S
SL/S
all forward structure distances points/R/S
exact timestamps and provenance
```

### Required SL sanity statement

If `SCALE = PARENT_JOURNEY` and the selected anchor is local relative to the broader packet, AI adds one sentence:

> Why does losing this exact structure end the current Child even though the Parent may survive?

No numeric local/global threshold is authorized.

---

## 5. Open Parent-Journey

Runtime continuously guards Hard SL and mapped structural events.

AI is called at:

```text
earliest selected structure event
or next completed H1 heartbeat
```

Intrahour structure events are reviewed on the next completed M15.

At each call AI answers only:

```text
DECISION: HOLD / EXIT / REMAP
EVIDENCE: 1-3 exact price/settlement facts
```

### HOLD

Use when larger progression remains capable, including normal counterflow.

### EXIT

Use when factual progression has materially deteriorated. Do not require Parent metaphysical death.

Do not exit solely because:

- profit is +5p or +10p;
- a nearby structure was touched;
- one opposing candle appeared;
- a fixed R was reached;
- indicator changed.

### REMAP

Use when a forward structure has been consumed/invalidated and the trade remains alive. Runtime supplies the next deterministic structure map.

---

## 6. Open Local Bridge

Runtime guards Hard SL and fixed destination M1-by-M1.

If neither resolves first, AI receives M15 lifecycle heartbeats and may HOLD or EXIT on structural invalidation.

Do not relabel a profitable Local Bridge into Parent-Journey after outcome reveal. A scale change requires a new explicit decision.

---

## 7. Hard SL

Hard SL is final for the current Child.

```text
touch = Child finished
never widen
later same-side move cannot rescue it
```

Parent is reassessed separately.

---

## 8. Baseball / payoff audit

At session end, ask:

```text
Did we swing at too many marginal pitches?
Did repeated stops come from genuinely different opportunities or the same auction?
Did any good winner get managed like a scalp?
Did we refuse a strong Parent-Journey because the nearest structure looked close?
Did we hold a trade after actual progression had failed?
```

This is qualitative research audit only.

Do not convert answers into:

- N-loss limits;
- retry caps;
- minimum R;
- minimum SL;
- fixed take-profit/trailing rules.

---

## 9. Directional bias audit

At session end record:

```text
LONG serious candidates / trades
SHORT serious candidates / trades
strong imbalance + market reason
whether opposite-side evidence was held to the same standard
```

No forced side balance.

---

## 10. Required journal output

For every trade, runtime produces the factual ledger automatically.

AI-specific fields stored are only:

```text
Parent belief
opposite case
good-pitch rationale
attempt thesis
selected SL structure
scale
WHAT_IS_NEW if retry
review decisions/evidence
```

This should keep the process auditable without turning trading into form completion.
