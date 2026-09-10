# V9 Discretionary Trading Pipeline — HTF Market Map

Date: `2026-09-10`
Status: `ACTIVE RESEARCH PIPELINE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Build the chart packet

Show:

```text
H4 broader context
H1 multi-day chart
numeric scale facts
```

Show enough history to contain the active major legs.

Do not begin with LTF.

## 2. Build the market map

AI marks:

- major legs;
- major highs/lows;
- major POIs;
- external liquidity candidates;
- range/compression boundaries;
- consumed structure;
- large directional routes.

State both LONG and SHORT scenarios.

## 3. Decide WAIT or PITCH

Default to WAIT.

A pitch exists when a meaningful HTF scenario has become actionable near a selected POI or structural transition.

Do not trade because a local pattern appeared.

## 4. Open LTF only when needed

After the HTF scenario is clear, inspect H1/M15/M5 for execution.

Use LTF for:

- better entry location;
- trigger timing;
- reduced execution risk.

Do not let LTF redefine the Parent map.

## 5. Freeze the Child

Before entry record:

```text
SIDE
ATTEMPT_THESIS
ENTRY
HARD_SL
WHY_SL_INVALIDATES_THIS_CHILD
PARENT_ROUTE
MAJOR_DESTINATION / REVIEW_STRUCTURE
```

Set Hard SL before entry.
Never widen it.

## 6. Hold at the intended scale

Do not manage a multi-hour Parent-Journey from every M5/M15 fluctuation.

Review when:

- Hard SL is touched;
- a major mapped HTF structure is reached;
- progression is materially damaged;
- a predeclared remap event occurs.

At review answer:

```text
HOLD
EXIT
REMAP
```

## 7. Destination

Use major HTF structure and external-liquidity candidates.

Do not use the nearest local high/low as automatic TP.

Parent-Journey may use `FIXED TP = NONE`.

## 8. Retry

After a stopped Child ask:

```text
WHAT OBJECTIVE FACT CHANGED?
IS THE NEW PITCH WORTH PAYING RISK FOR?
```

Do not use retry counts or cooldown.

## 9. Journal

Record:

- chart cutoff;
- market map image;
- selected POIs;
- selected liquidity/route;
- LONG/SHORT scenarios;
- entry;
- Hard SL;
- exit/review;
- points;
- R;
- S;
- MFE/MAE;
- hold time;
- execution-quality review.

Judge process before outcome.
