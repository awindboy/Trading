# V8-001B-r2 — Event-Centered Representation Tournament Plan

Status: `FROZEN BEFORE R0-R3 MODEL COMPARISON`
Date: `2026-08-30`
Base representation: `V8-001A-r3`
Production authority: `NONE`

## 1. Primary question

Does a chart-preserving event-centered representation add stable future-path information beyond simpler
same-information numerical/scalar representations?

This remains an information test, not a P/L tournament.

## 2. Frozen anchor population

One row per unique timestamp from the union of:

```text
H1_DOUBLE_B_CONFIRMED
M5_MA20_CENTER_CONTACT_START
M5_BB20_UPPER_CONTACT_START
M5_BB20_LOWER_CONTACT_START
```

Simultaneous facts are merged into a multi-hot event token.

## 3. Shared event-centered input coordinate

For every accepted decision timestamp:

```text
C0 = event/source candle close = last completed M1 close at t
```

Every price-level input across all four timeframes is:

```text
x' = x - C0
```

No per-event ATR division, percentage transformation or visible-window price autoscaling is applied to the
base numerical representation.

Magnitude/meta fields remain native.

## 4. Visual representation

R2/R3 receive the same event-centered geometry at three fixed zoom levels:

```text
tight
medium
wide
```

All zoom spans are frozen globally per timeframe and are identical across events.

The model visual implementation should encode the 12 `(timeframe, scale)` panels as explicit tokens/views,
preferably with a shared compact visual encoder, instead of creating one enormous raster.

Model training panels may use a smaller fixed raster than the human-audit panels as long as:

- the exact size is frozen before model comparison;
- every R2/R3 fold uses the same size;
- chart/event geometry remains deterministic;
- no outcome decides the raster resolution.

## 5. Future-path coordinate

Primary target coordinate is changed to match the event-centered input concept.

For horizon `h`:

```text
MFE_raw_h = max(future HIGH) - C0
MAE_raw_h = min(future LOW)  - C0
RET_raw_h = future final CLOSE - C0
```

The exact M1 open at `t` remains recorded as `future_start_open`, and the opening gap is retained:

```text
gap_from_event_close = future_start_open - C0
```

Causal M5 ATR14-normalized versions are retained only as auxiliary diagnostics. They are not the primary
V8 coordinate and may not silently replace the raw event-centered targets.

## 6. Accepted dataset

The r2 rebuild retains the same population size:

```text
candidate unique anchors: 66,277
accepted full-history + full-240m: 59,438
```

The unchanged population confirms that the coordinate-system change did not outcome-select events.

## 7. Chronological folds

```text
Fold A: train 2022-2023 -> evaluate 2024
Fold B: train 2022-2024 -> evaluate 2025
Fold C: train 2022-2025 -> evaluate 2026 YTD
```

Do not retune model architecture per fold.

## 8. Representation families

### R0 — scalar baseline

Small factual/event-centered scalar summaries only. No TREND/RANGE/BREAKOUT/TURNING labels.

### R1 — numerical sequence

Exact event-centered H1/M15/M5/M1 numerical sequences.

### R2 — visual geometry

Tight/medium/wide fixed-scale causal chart views.

### R3 — fused

R1 + R2 + event/time token.

R3 is the V8 representation hypothesis, but it does not get a larger model-selection budget than controls.

## 9. Training-only optimizer scaling rule

The persisted representation stays in native/event-centered units.

A model may apply a scaler fitted **only on the training fold** for optimizer stability.

Restrictions:

- price-offset channels may be divided by a training-fold scale but must not be shifted away from zero;
- validation/test values never fit the scaler;
- the same fitted scaler is used unchanged on the fold's evaluation year;
- results must still be reported in raw GOLD price units and auxiliary ATR units.

This separates representation semantics from numerical optimizer conditioning.

## 10. Required metrics

For all 9 primary raw path targets report:

- MAE in GOLD price units;
- Huber loss after inverse-transform to raw units;
- Spearman rank correlation;
- Pearson correlation where stable.

Also report the same rank diagnostics for ATR auxiliary targets, event-family/year cuts, retrieval dispersion,
and visual/numerical ablations.

## 11. Hard gate

Visual/fused representation is useful only if it adds information beyond R1 on multiple future-hidden folds.

If R1 matches or beats R3, V8 must accept that the chart raster branch did not add enough information in its
current form. Do not rescue it by arbitrary visual tuning on evaluation outcomes.
