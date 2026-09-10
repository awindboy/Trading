# V9 Discretionary Trading Pipeline — Sequential Map + Trigger

Date: `2026-09-10`
Status: `ACTIVE RESEARCH PIPELINE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Start causally

Start from a preselected replay cutoff and FLAT state.

Use `v9_causal_m1.py`.
Build only the revealed chronological prefix.

Do not preload or inspect future OHLC for active decisions.

## 2. Build exact ICT candidate universe

Run `v9_ict_object_engine.py` on the revealed prefix.

Generate H4/H1 candidates:

```text
FVG
OB
SWING / LIQUIDITY
```

Candidate object output includes exact geometry, provenance, and lifecycle facts.

Code does not decide importance.

## 3. Render MAP

Use H1 as the main AI-facing map.
Overlay selected H4/H1 objects.

Map should show only what matters:

- major leg(s);
- selected POI(s);
- selected liquidity;
- large route;
- Entry/SL/review levels when relevant.

Keep annotations short.

## 4. AI updates the market-map ledger

AI outputs:

```text
MAP_VERSION
SELECTED_OBJECT_IDS + ROLES
LONG_SCENARIO
SHORT_SCENARIO
PREFERRED_PITCH / WAIT
ACTIVE_WAIT_EVENT
MAP_CHANGES
```

Do not rebuild the story from scratch.
Explain any strategic object-role change.

## 5. WAIT

Default to WAIT.

Freeze the event that is allowed to wake AI again.
Examples:

```text
selected POI touch
selected liquidity raid
selected POI geometric end
frozen completed-bar condition
explicit remap event
```

Use `v9_replay_event_runner.py` to advance to the first frozen event.

No AI inspection of ordinary intermediate candles.

## 6. Update objects at event

Rebuild the candidate ledger from the newly revealed prefix.

Code updates exact lifecycle:

- FVG touch/full fill;
- liquidity raid;
- OB mitigation/invalidation.

AI updates strategic roles.

## 7. Open TRIGGER chart only when authorized

If an HTF event creates an actionable pitch, open M5 trigger chart.
Use M15 instead when the active structure is M15-scale.

Show:

- active HTF POI;
- selected local liquidity;
- sweep/raid when relevant;
- selected structural reference;
- trigger state.

Do not search the whole LTF chart for unrelated trades.

## 8. Freeze the LTF trigger

Before advancing again record one objective trigger condition.

Examples can include a selected M5/M15 close across a frozen structural reference.
The exact trigger is discretionary and research-stage.

Do not add a mandatory trigger chain.

If the POI is consumed/invalidated before trigger, cancel the Child candidate.
Do not backfill.

## 9. Freeze Child before entry

Record:

```text
SIDE
ATTEMPT_THESIS
ENTRY / ENTRY_TRIGGER
HARD_SL
WHY_SL_INVALIDATES_THIS_CHILD
PARENT_ROUTE
DESTINATION / REVIEW_OBJECT_IDS
```

Set Hard SL before entry.
Never widen.

## 10. Manage open position at HTF scale

Runtime scans M1 for:

- Hard SL;
- fixed destination when used;
- selected HTF review object/event.

Do not manage a multi-hour journey from every M5/M15 fluctuation.

At authorized review show updated MAP + TRIGGER/resolution chart and answer:

```text
HOLD
EXIT
REMAP
```

## 11. Child resolution and retry

Child ends at Hard SL or authorized exit/destination.

Do not rescue it later.

If Parent survives, a new Child requires:

```text
WHAT OBJECTIVE FACT CHANGED?
IS THIS A GOOD PITCH?
```

No retry count or cooldown.

## 12. Journal

Record every AI call and runtime event:

- cutoff/as-of;
- call reason;
- MAP image;
- TRIGGER image/state;
- candidate-engine version;
- selected object IDs and roles;
- geometric object state changes;
- LONG/SHORT scenarios;
- frozen wait/trigger event;
- Entry / Hard SL;
- review/destination;
- HOLD/EXIT/REMAP;
- R/S/MFE/MAE/hold time;
- process-quality review.

Outcome is secondary to execution/process quality during current research.
