# V9 Next Research Contract — Post-June Execution Runtime

Date: `2026-09-10`
Status: `ACTIVE NEXT V9 CONTRACT / IMPLEMENTATION + PARITY PHASE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Untouched reserve: `GOLD# 2021`

## 1. Purpose

Do not ask the AI for more discretionary intelligence before fixing the execution environment.

The next phase asks:

> Can V9 present the same objective price geometry and trigger the same review moments across sessions, while leaving only a small set of genuinely discretionary decisions to AI?

Positive retrospective P/L is irrelevant to this phase.

---

## 2. Future-hidden gate

No new future-hidden trading period may be opened until all workstreams below pass on already-consumed data.

Do not use `GOLD# 2021` to design or tune the runtime.

---

## 3. Workstream A — structure registry

Define each active objective structure family mathematically/algorithmically.

For every family document:

```text
name/version
required input timeframe
exact construction rule
price-range rule
status rule
provenance rule
invalidation-boundary rule if usable for SL
```

Do not promote a family because it seems visually sensible.

At minimum, trivial objective facts such as exact prior session/day/week extremes can be implemented without AI. More complex pivot/range structures require explicit frozen definitions first.

No `major/minor` importance label is required unless it also has a deterministic definition.

---

## 4. Workstream B — geometry packet

Given a fixed cutoff and selected side, code must reproduce exactly:

```text
candidate pending-entry condition(s)
planned trigger/order price for each condition
candidate falsification structures
exact SL boundary for each candidate structure
planned SL points / 1R
PLAN_S and planned SL/S
all forward structure price ranges
planned points/R/S to each forward structure
FILL_S recorded if/when order fills
```

No AI arithmetic and no undocumented price buffer.

---

## 5. Workstream C — prepared orders and event-driven scheduler

Implement continuous local M1 monitoring without continuous AI calls.

The required primary state flow is:

```text
PLANNING
-> SETUP PLANNED
-> ORDER/CONDITION ARMED
-> FILLED / CANCELLED / EXPIRED / INVALIDATED-BEFORE-FILL
-> if filled: SL / destination / selected review events
```

Required entry-condition support must include deterministic, parity-tested forms for at least:

```text
retracement-style pending entry
break-style pending entry
```

Do not authorize vague executable conditions such as `meaningful reclaim` until their exact rule is frozen.

Required mechanical post-fill events:

```text
Hard SL touch
fixed Local-Bridge destination touch
```

Required scheduling principle:

```text
ordinary candle completion != automatic AI call
precommitted price/order event -> local handling or scheduled AI review
heartbeat -> maximum-staleness fail-safe only
```

Replay must advance directly from one precommitted relevant event to the next without showing the AI every intermediate candle.

---

## 6. Workstream D — minimal AI packet

Freeze the request/response schema from the post-June pipeline.

The AI should not be asked to produce discretionary labels that the runtime can neither verify nor use.

Required planning/setup AI fields remain small:

```text
Parent belief
opposite case
NO SETUP or prepared setup(s)
good-pitch rationale
attempt thesis
entry condition / objective entry structure
SL structure selection
journey scale
fixed destination if Local Bridge
review structures if Parent-Journey
setup invalidation / expiry condition
WHAT_IS_NEW only on retry
```

Required open-position field:

```text
HOLD / EXIT / REMAP + concise factual evidence
```

---

## 7. Workstream E — consumed-June parity dry run

Use already-consumed June only for runtime/parity testing.

Important audit windows include:

```text
2025-06-17 06:00 -> 2025-06-18 06:59
2025-06-26 10:00 -> 16:59
2025-06-30 07:00 -> 15:59
```

These windows contain:

- broad rotational churn;
- directional movement with repeated local stop-outs;
- repeated short-lived inversion attempts.

Do **not** alter structure definitions to make historical trades profitable.

The purpose is exact reproducibility and event timing.

---

## 8. Parity test

At identical consumed cutoffs, repeated independent runs must match exactly on:

```text
structure IDs
price ranges
provenance
SL boundary for the same selected structure
S
points/R/S geometry
event timestamp
next authorized review time
```

The following may differ and should be labeled `AI DISCRETIONARY DIVERGENCE`, not tooling failure:

```text
Parent belief
pitch quality
trade/no-trade
which objective SL structure is selected
Local Bridge vs Parent-Journey
hold/exit/remap decision
```

---

## 9. Success criteria

This phase passes only if:

1. objective packet is reproducible;
2. no AI-invented price structure has execution authority;
3. SL derivation is deterministic after structure selection;
4. p/R/S arithmetic is automatic;
5. pending entry conditions and their cancel/expiry logic fire reproducibly;
6. mapped post-fill review events fire reproducibly;
7. ordinary candle completion does not cause unnecessary large-model calls;
8. heartbeat is a maximum-staleness fail-safe rather than blind periodic analysis;
9. replay can move from armed setup to first relevant event without exposing intermediate candles to AI;
10. AI prompt is materially simpler than the June harness;
11. no new numeric edge rules were fitted to June;
12. untouched reserve remains untouched.

---

## 10. Promotion gate

After all criteria pass:

1. freeze runtime version;
2. freeze active structure registry version;
3. freeze AI packet schema;
4. freeze precommitted-order / cancellation / expiry / bracket semantics;
5. select a future-hidden development period without inspecting future price;
6. perform contamination preflight;
7. begin a new prospective replay.

Do not call this production validation yet.
