# V8-005 Movement Probability MT5 Shadow Indicator

Date: `2026-08-31`
Status: `SHADOW-DEVELOPMENT CANDIDATE / NOT TRADE AUTHORITY`
Market: `GOLD#`
Chart: `M5` required for exact timeline alignment
Production authority: `NONE`
Direction authority: `NONE`

## 1. Purpose

Display the causal probability that GOLD moves at least `10.0` price units in either direction after each completed M5 decision point, while independently marking factual V8 events on the main chart.

The indicator does **not** estimate LONG/SHORT direction.

## 2. Main-chart event markers

The indicator creates triangle/arrow glyphs on the source candle for:

- `M5 SMA20 CONTACT START`
- `M5 BB20 UPPER CONTACT START`
- `M5 BB20 LOWER CONTACT START`
- `H1 DOUBLE-B CONFIRMED`

Each event family has an independent color input in the indicator Properties window.

Upper-band / upper Double-B events are drawn above the candle. Lower-band / lower Double-B events are drawn below. SMA20-contact marker placement is chosen only to avoid candle overlap (`close < SMA20` => above, otherwise below); it is **not** a directional label.

Hovering a marker shows the 15m/30m/60m movement probabilities known at the event decision time.

## 3. Separate-window probability plots

Three continuous M5 lines are plotted from 0 to 100:

```text
P(|move| >= 10.0 within 15m)
P(|move| >= 10.0 within 30m)
P(|move| >= 10.0 within 60m)
```

The lines are continuous at every completed M5 bar, not only at event timestamps. Therefore the user can scroll backward and inspect how movement probability evolved before, during and after each factual event.

The current forming M5 candle is deliberately blank because its close-time state is not yet causally complete.

## 4. Portable model

The MT5 implementation uses a 53-feature logistic model because it can be embedded exactly in MQL5 and independently parity-tested.

Features are causal M1 range/volatility geometry over active-row windows:

```text
5, 15, 30, 60, 120, 240, 480, 1440 M1 rows
```

Per-window families include:

- squared close-change sum (`RV` proxy);
- high-low range sum;
- rolling max(high)-min(low);
- absolute close-change sum;
- candle-body sum.

Current-state features include:

- current M1 range;
- current true range;
- current absolute close change.

Acceleration/context ratios compare short and long windows, including pairings such as:

- 5 vs 60;
- 15 vs 120;
- 30 vs 240;
- 60 vs 480;
- 120 vs 1440.

The model does not need RSI/MACD/event identity to generate the movement probability. Research ablations found that movement intensity is carried mainly by recent realized range/volatility structure.

## 5. Historical walk-forward model selection

Historical probability display is causal by calendar year:

```text
2024 display -> model trained on eligible 2022-2023 M5 states
2025 display -> model trained on eligible 2022-2024 M5 states
2026 display -> model trained on eligible 2022-2025 M5 states
```

No probability is displayed before 2024.

By default the indicator refuses to extrapolate the 2026 model beyond calendar 2026. Any explicit override has no validation authority.

## 6. Portable-model event-subset validation

Although the logistic model is trained on continuous completed-M5 states, it remains strongly discriminative when evaluated only at the existing V8 factual event timestamps.

### 15-minute 10p movement AUC

```text
2024  0.865
2025  0.873
2026  0.815
```

### 30-minute 10p movement AUC

```text
2024  0.844
2025  0.851
2026  0.796
```

### 60-minute 10p movement AUC

```text
2024  0.807
2025  0.829
2026  0.781
```

30-minute event-family AUC remains informative inside all four event families. Examples:

```text
H1 Double-B       2024 0.864 / 2025 0.812 / 2026 0.832
M5 SMA20 contact  2024 0.840 / 2025 0.844 / 2026 0.791
M5 upper BB       2024 0.803 / 2025 0.850 / 2026 0.777
M5 lower BB       2024 0.849 / 2025 0.867 / 2026 0.808
```

These are development diagnostics, not untouched final validation.

## 7. Research-best model vs portable model

A richer HAR/range research representation achieved slightly different benchmark values and was used to understand the phenomenon.

The MT5 model intentionally uses the portable logistic representation rather than embedding the research-best model because exact reproducibility, inspectable equations and MQL parity are more important at the shadow stage than squeezing out small additional development AUC.

## 8. Python -> MQL formula parity

The MQL feature equations were independently reproduced from the Python training equations on 30 sampled M5 decision times spanning 2024-2026.

Observed maximum differences:

```text
max absolute feature difference      2.22e-12
max absolute probability difference  5.39e-14
```

This validates the formula translation and embedded coefficients to floating-point precision.

It does **not** replace an MT5 compile/runtime parity check on the user's broker history.

Parity reference:

`ledgers/v8/V8MovementProbabilityParityReference.csv`

## 9. Runtime non-interference

The indicator:

- sends no orders;
- modifies no positions;
- modifies no EA state;
- uses only chart/history reads plus its own indicator buffers/chart objects.

It is a shadow decision-support tool only.

## 10. User-facing meaning

A displayed value such as:

```text
10p <= 30m: 82%
```

means:

> Given the current historical M1 range/volatility state, the model estimates an 82% probability that price reaches either `current completed-M5 close + 10.0` or `current completed-M5 close - 10.0` within 30 elapsed minutes.

It does **not** mean LONG 82%, SHORT 82%, liquidity 82%, trade win-rate 82% or automatic permission to enter.

## 11. Required next validation

1. Compile in the user's actual MetaEditor.
2. Load sufficient broker M1/M5/H1 history.
3. Compare several timestamps against `V8MovementProbabilityParityReference.csv` when using the same research feed.
4. Confirm event timing and triangle placement visually.
5. Run prospectively in shadow mode and log every event/probability before discretionary selection.
6. Later test whether human directional/trading performance improves as movement probability increases.

GOLD# 2021 remains unopened.
