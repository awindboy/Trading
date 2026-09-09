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
current entry reference
candidate falsification structures
exact SL boundary for each candidate structure
SL points
S
SL/S
all forward structure price ranges
points/R/S to each forward structure
```

No AI arithmetic and no undocumented price buffer.

---

## 5. Workstream C — event-driven scheduler

Implement continuous local M1 monitoring.

Required mechanical events:

```text
Hard SL touch
fixed Local-Bridge destination touch
```

Required scheduling behaviors:

```text
FLAT -> completed H1 heartbeat
SERIOUS CANDIDATE -> next completed M15 only
OPEN PARENT-JOURNEY -> selected mapped event OR H1 heartbeat
OPEN LOCAL BRIDGE -> M15 heartbeat plus mechanical guards
```

For an intrahour Parent-Journey event, stop at the next authorized completed M15 rather than revealing the full H1.

---

## 6. Workstream D — minimal AI packet

Freeze the request/response schema from the post-June pipeline.

The AI should not be asked to produce discretionary labels that the runtime can neither verify nor use.

Required pre-entry AI fields remain small:

```text
Parent belief
opposite case
trade/no-trade
good-pitch rationale
attempt thesis
SL structure selection
journey scale
fixed destination if Local Bridge
review structures
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
5. mapped review events fire reproducibly;
6. H1 remains a maximum heartbeat rather than blind replay;
7. no candidate-mode full-H1 leakage occurs;
8. AI prompt is materially simpler than the June harness;
9. no new numeric edge rules were fitted to June;
10. untouched reserve remains untouched.

---

## 10. Promotion gate

After all criteria pass:

1. freeze runtime version;
2. freeze active structure registry version;
3. freeze AI packet schema;
4. select a future-hidden development period without inspecting future price;
5. perform contamination preflight;
6. begin a new prospective replay.

Do not call this production validation yet.
