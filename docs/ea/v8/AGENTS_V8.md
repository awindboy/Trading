# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Active branches:
- `V8-A MOVEMENT PROBABILITY` — FROZEN
- `V8-B INTERNAL-ONLY DIRECTION RESEARCH` — ACTIVE RESEARCH / NO AUTHORITY
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current empirical thesis

V8-A has strong open-development evidence that causal GOLD history contains useful information about near-term movement intensity / +/-10.0 barrier crossing.

Direction remains a separate problem. Repeated strictly causal internal-only direction studies have not yet demonstrated a stable broad LONG/SHORT edge across 2024/2025/2026.

Do not convert V8-A into a direction or trade signal.

## 2. V8-A is frozen

Do not change to rescue V8-B:

```text
C0 = completed M5 decision close
barrier = +/-10.0 GOLD price units
H = 15m / 30m / 60m
portable representation = frozen 53-feature causal M1 model
historical models = walk-forward by year
```

Primary artifact:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

V8-A remains direction-free.

## 3. Direction research is internal-only unless explicitly reopened

The user decided that external/cross-market source-of-move inputs are not the active direction path.

Do not use USDJPY, XAUEUR, BTCUSD, DXY, yields or other external markets as the default V8-B research source.

A future external branch requires an explicit project decision to reopen it.

## 4. Permanent causality boundary

For every resampled timeframe:

```text
completed bar observable iff
bar_start + timeframe_duration <= decision_time
```

A current partial HTF bar may be used only if rebuilt from lower-timeframe observations already available before the decision.

Never infer availability from bar-start timestamp alone.

Training rows whose outcome window crosses a validation/evaluation boundary must be purged.

## 5. Invalidated direction evidence

The high V8-B1 direction AUC committed before the causal-alignment audit is invalid.

Cause:

- M15/H1 `label=left` bars were selected by start timestamp;
- later prices inside the same HTF interval entered the model.

The old `config/v8_b1_direction_models.json` is historical invalidated evidence only and must never be deployed.

## 6. Internal V8-B research lessons

The following have been tested and did not produce a stable broad direction edge after temporal validation:

- price/indicator sequences;
- visual/fused direction models;
- robust normalization and fractional differentiation;
- self-supervised reconstruction;
- TCN / Transformer / LightGBM / logistic variants;
- nearest-neighbor/meta-labeling;
- event-family direction splits;
- V8-A P15/P30/P60 as raw direction features;
- V8-A probability slopes, acceleration and shape;
- event-centered price geometry + V8-A trajectory;
- regime-normalized V8-A probability state;
- directional semivariance/body/wick decomposition;
- signed tick-activity / price-impact proxies;
- low-dimensional score fusion and stacking;
- rolling/recent-year retraining;
- direction-confidence selective tails after exact independent rebuild.

A good 2024 discovery result is not sufficient. If 2025/2026 collapses, do not threshold-tune to save it.

## 7. Selective-direction accounting rule

A high chosen-side hit rate can be manufactured by a strong movement filter even when direction is random.

Always report:

```text
move_rate
conditional_direction_accuracy
chosen_side_hit_rate
directional_excess
```

where:

```text
directional_excess =
chosen_side_hit_rate - 0.5 * move_rate
```

If directional excess is near zero, V8-A is selecting movement but V8-B is not adding meaningful sign information.

## 8. Exact-rebuild requirement

Any promising direction result must be independently reconstructible from:

- the current factual event ledger;
- explicit feature equations;
- explicit model/scaler parameters;
- exact training population;
- exact chronological purge rules;
- exact selection rule.

If an old score artifact cannot be independently regenerated, it is diagnostic history, not authority.

## 9. Current remaining internal hypotheses

Highest-priority remaining work:

1. exact V8-A trajectory × factual event interaction using the frozen continuous M5 probability series;
2. sequential `WAIT -> observe -> recenter -> update` policy;
3. every delayed decision must reset `C0` to the new current decision price before defining +/-10.0;
4. distinguish movement selection from direction contribution with proper scores and directional excess;
5. if retrospective internal direction remains weak, prioritize prospective human-decision labels rather than endless feature mining.

## 10. Sequential decision warning

Do not measure an event at C0, wait 5 minutes, then claim direction skill against the original C0 +/-10 barriers.

If price moved +5 during the wait, the original UP barrier is mechanically closer.

At each delayed decision:

```text
new C0 = current causal decision price
new targets = new C0 +/- 10.0
```

This recentering is mandatory.

## 11. GOLD# 2021

`LOCKED / UNTOUCHED`

Do not consume the reserve until a direction claim-grade candidate exists under a frozen, strictly causal and independently reproducible protocol.
