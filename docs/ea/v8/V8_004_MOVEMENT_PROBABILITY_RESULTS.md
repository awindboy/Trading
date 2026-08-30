# V8-004 Movement Probability Deep Audit

Date: 2026-08-31  
Status: DEVELOPMENT EVIDENCE / SHADOW-INDICATOR CANDIDATE  
Production authority: NONE  
Direction authority: NONE

## 1. Research question

At an objectively detected GOLD event, can causal historical market information distinguish whether price will move at least 10.0 GOLD price units in either direction within a fixed short horizon?

Primary 30-minute target:

```text
event close = C0

FAST_30 = 1
if, after the event,
high >= C0 + 10.0
OR
low <= C0 - 10.0
within 30 minutes

FAST_30 = 0 otherwise
```

This is **not** a LONG/SHORT forecast. It is a movement-intensity / barrier-crossing probability.

## 2. Important correction made during audit

An earlier interim report mixed results from different movement diagnostics and overstated the 30-minute AUC.

The frozen ±10p event ledger was recomputed from the same labels and the movement model tournament was rerun from the common population.

Authoritative event-year FAST_30 rates are:

| Year | Event N | 10p within 30m |
|---|---:|---:|
| 2022 | 12,740 | 2.14% |
| 2023 | 12,842 | 1.60% |
| 2024 | 12,891 | 3.61% |
| 2025 | 12,525 | 18.40% |
| 2026 YTD | 8,411 | 51.31% |

The increase is economically large and confirms a major movement-intensity regime shift in the later GOLD sample.

## 3. Causal / validation boundary

All model inputs are available before the forecast horizon.

For an evaluation year beginning at `T`:

```text
training decision time < T
AND
training 30m label end < T
```

Internal validation boundaries use the same purge rule.

No future evaluation-year price is permitted to define a training label.

GOLD 2021 remains unopened.

## 4. What actually predicts fast movement?

Ablation results show a very clear structure.

### 2024

| Input | ROC AUC |
|---|---:|
| Event type only | 0.574 |
| Time-of-day only | 0.759 |
| Volatility / activity only | 0.854 |
| Time + volatility / activity | 0.860 |
| Broad indicator snapshot | 0.860 |
| HAR/range multi-horizon + time | **0.868** |

### 2025

| Input | ROC AUC |
|---|---:|
| Event type only | 0.529 |
| Time-of-day only | 0.636 |
| Volatility / activity only | 0.839 |
| Time + volatility / activity | 0.845 |
| Broad indicator snapshot | 0.836 |
| HAR/range multi-horizon + time | **0.844** |

### 2026 YTD

| Input | ROC AUC |
|---|---:|
| Event type only | 0.525 |
| Time-of-day only | 0.648 |
| Volatility / activity only | 0.784 |
| Time + volatility / activity | 0.787 |
| Broad indicator snapshot | 0.778 |
| HAR/range multi-horizon + time | **0.789** |

Interpretation:

1. Event identity by itself explains little.
2. Time-of-day matters, but it is not the main source.
3. Recent volatility, price range and market activity are the dominant information.
4. Adding a large generic indicator set does not improve the movement forecast.
5. Carefully constructed multi-scale realized-volatility/range features give the strongest or joint-strongest result.

## 5. HAR / range representation

The strongest candidate uses causal M1 information aggregated over:

```text
5m
15m
30m
60m
120m
240m
480m
1440m
```

For these horizons it includes volatility/activity quantities such as:

- realized squared price changes;
- realized high-low range;
- total high-low range;
- average absolute price change;
- candle body / wick activity;
- bipower-style continuous variation proxy;
- jump / excess-variation proxy;
- tick-activity statistics;
- spread statistics;
- time-of-day coordinates.

It does not need to know whether a chart is a human-labeled TREND, RANGE, BREAKOUT or TURNING state.

## 6. Multi-horizon movement forecast

The same frozen representation was tested on several time horizons.

### ROC AUC

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | **0.883** | **0.861** | **0.800** |
| 30m | 0.868 | 0.844 | 0.789 |
| 60m | 0.838 | 0.831 | 0.784 |
| 120m | 0.805 | 0.818 | 0.809 |

### Actual probability of a 10p move

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 1.39% | 9.31% | 32.28% |
| 30m | 3.61% | 18.40% | 51.31% |
| 60m | 9.21% | 33.13% | 72.98% |
| 120m | 20.87% | 53.49% | 90.05% |

Shorter horizons provide stronger discrimination, while longer horizons naturally have higher base event rates.

A practical human-facing indicator should therefore show multiple horizons rather than forcing one horizon to do everything.

## 7. 30-minute OOS uncertainty

Week-block bootstrap 95% intervals:

```text
2024: 0.843 – 0.893
2025: 0.819 – 0.865
2026: 0.756 – 0.821
```

The ranking result is therefore not a small-sample fluctuation around AUC 0.5.

## 8. Calibration

The raw 30-minute model already tracked annual event rates surprisingly well:

| Year | Mean predicted P | Actual FAST_30 |
|---|---:|---:|
| 2024 | 3.43% | 3.61% |
| 2025 | 18.08% | 18.40% |
| 2026 YTD | 46.60% | 51.31% |

A naive trailing isotonic / rolling-prior recalibration was tested and **made log-loss and Brier score worse**.

Therefore the current result does not justify automatically bolting a recalibration layer on top.

2026 does show some underprediction of the absolute level, so live shadow use should retain both:

- raw estimated probability;
- historical percentile / activity score.

## 9. Probability-score separation

### 2024

Base FAST_30 rate: **3.61%**

```text
bottom score decile    0.07%
top score decile      20.25%
top 5%                26.51%
top 1%                48.84%
```

### 2025

Base FAST_30 rate: **18.40%**

```text
bottom score decile    1.12%
top score decile      62.65%
top 5%                67.78%
top 1%                73.02%
```

### 2026 YTD

Base FAST_30 rate: **51.31%**

```text
bottom score decile   14.96%
top score decile      93.10%
top 5%                93.35%
top 1%                90.59%
```

This is the strongest evidence for the intended human-filter use case.

The model is not merely producing a statistically significant AUC. It separates event populations with very different realized probabilities of a near-term 10p move.

## 10. Event-family robustness

The same movement score remains informative inside the existing event families.

### 2024 AUC

```text
H1 Double-B             0.832
M5 SMA20 contact        0.866
M5 upper-BB contact     0.853
M5 lower-BB contact     0.866
```

### 2025 AUC

```text
H1 Double-B             0.792
M5 SMA20 contact        0.835
M5 upper-BB contact     0.847
M5 lower-BB contact     0.863
```

### 2026 YTD AUC

```text
H1 Double-B             0.816
M5 SMA20 contact        0.786
M5 upper-BB contact     0.771
M5 lower-BB contact     0.797
```

The signal is therefore not carried by one event type.

## 11. Full sequence neural model falsification

A full multi-timeframe temporal CNN was also trained on the historical OHLC + indicator sequences for the FAST_30 target.

Its first 2024 run produced approximately:

```text
validation AUC 0.527
evaluation AUC 0.521
```

This is dramatically worse than the structured volatility/range model.

Interpretation:

For this task, preserving every technical-indicator sequence and asking a neural network to discover movement intensity from scratch is not currently superior to using economically appropriate realized-volatility/range preprocessing.

This supports the broader lesson that preprocessing / target representation matters more than model complexity here.

## 12. What the model is and is not measuring

A high score means:

> Given current causal range, realized volatility, activity and time structure, a 10-price-unit move in either direction is likely to occur soon.

It does **not** mean:

- LONG probability is high;
- SHORT probability is high;
- market liquidity is necessarily high;
- the event itself has directional edge;
- a trade will be profitable.

The closest interpretation is:

```text
near-term movement intensity
/
range-expansion probability
/
barrier-crossing probability
```

Liquidity may be related, but cannot be inferred directly from this feed alone.

## 13. Recommended shadow indicator

A first MT5 shadow tool should display, at every supported factual event:

```text
V8 MOVEMENT PROBABILITY

10p within 15m    xx%
10p within 30m    xx%
10p within 60m    xx%

Activity percentile
xx / 100

Event
M5 MA20 CONTACT
(or Double-B / BB contact)

Direction
NOT ESTIMATED
```

Suggested visual interpretation should remain descriptive rather than trading-authoritative:

```text
LOW
MEDIUM
HIGH
EXTREME
```

based on historical score percentile, not outcome-tuned trade thresholds.

## 14. Current research decision

### Promote to shadow-development candidate

- 10p movement-probability estimation;
- multi-horizon 15m / 30m / 60m output;
- HAR/range + activity + time representation;
- event-agnostic base score;
- raw probability plus percentile.

### Do not promote

- autonomous direction;
- entry/SL/TP authority;
- hard probability threshold for trading;
- event-specific directional rule;
- claim that this predicts liquidity.

## 15. Next validation before discretionary use

Before treating the value as a real trading filter:

1. implement exact MT5 causal feature parity;
2. run OFF/ON non-interference shadow logging;
3. verify live model input / Python research parity;
4. log every eligible event, including events the human ignores;
5. store 15m/30m/60m predicted probabilities before outcomes occur;
6. measure live calibration and score-decile separation;
7. separately record the human's direction decision and trade outcome.

The key downstream question is:

> Does the human discretionary directional edge improve materially as movement probability rises?

That must be answered from prospectively logged data rather than retrospectively selected examples.
