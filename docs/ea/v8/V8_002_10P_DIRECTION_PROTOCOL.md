# V8-002 — 10P First-Hit Numerical Context Protocol

Date: `2026-08-31`
Status: `DEVELOPMENT / FROZEN PILOT CONTRACT`
Production authority: `NONE`

## 1. Base target

For every causal decision anchor:

```text
C0 = event/source candle close known at decision time
UP target   = C0 + 10.0 GOLD price units
DOWN target = C0 - 10.0 GOLD price units
```

Starting with the first M1 bar after the decision timestamp, scan forward until one target is reached.

Label:

```text
UP_FIRST
DOWN_FIRST
AMBIGUOUS_SAME_M1
```

If both targets are inside the same M1 bar, the intrabar order is unknowable and the event is excluded from
binary training.

No arbitrary 15m/60m/240m terminal-return direction label is used.

`10p` in this protocol means GOLD price-axis `10.0`, e.g. `3000 -> 3010`, not `10 MT5 points = 0.10`.

## 2. Coordinate system

All price-level input series share the event reference:

```text
x_centered = x - C0
```

Therefore the event close is zero.

This applies to:

- OHLC;
- moving-average levels;
- Bollinger levels;
- other price-level series.

Magnitude/oscillator variables are not shifted by C0.

A +1234.5 synthetic translation audit reproduced the centered numerical input to floating-point tolerance
(max observed error < 8e-10).

## 3. Visual input

Visual/raster input is not part of the V8-002 base path.

The default model receives exact numerical multi-timeframe sequences.

Visual models remain historical diagnostics only unless later evidence justifies reopening them.

## 4. Historical input windows

```text
H1   96 completed bars
M15 128 completed bars
M5  144 completed bars
M1  180 completed bars
```

Every value is a historical sequence, not only the latest indicator snapshot.

## 5. Raw chart channels

At minimum:

```text
open
high
low
close
```

## 6. Indicator-history channels

Current first panel:

```text
tick volume
spread last / median
SMA20
BB20 upper / lower
EMA9
EMA20
EMA50
RSI14
Stochastic K14 / D3
MACD 12/26
MACD signal9
MACD histogram
ATR14
True Range
BB20 width
close - SMA20
close - EMA20
causal log tick-volume
causal EWM tick-volume z-score
```

H1 additionally preserves the V7 Double-B representation:

```text
SMA4 of OPEN
BB4/4 upper
BB4/4 lower
```

These are representations only. No rule such as `RSI > 70 => SHORT` is supplied.

## 7. Indicator changes

The `IND_DELTA` variant adds causal 1-bar changes for:

```text
SMA20
BB20 upper/lower
EMA9/20/50
RSI14
Stochastic K/D
MACD histogram
ATR14
BB20 width
close-SMA20
close-EMA20
H1 SMA4 / BB4 levels
```

The full historical raw indicator series remains present; the delta channels are additional representation.

## 8. Event facts

The model is also told which factual anchor fired:

```text
H1 Double-B
M5 SMA20 contact-start
M5 upper BB20 contact-start
M5 lower BB20 contact-start
```

Event facts do not carry BASIC/BREAKOUT/TURNING labels.

## 9. Chronological diagnostics

```text
train 2022-2023      -> evaluate 2024
train 2022-2024      -> evaluate 2025
train 2022-2025      -> evaluate 2026 YTD
```

2022-2026 remain open development evidence. GOLD 2021 remains untouched.

## 10. Metrics

AUC is an information-ranking diagnostic, not the trading objective.

Always report at least:

```text
ROC AUC
accuracy
balanced accuracy
Brier score
log loss
true UP rate
```

Final trading promotion still requires campaign P/L, WR, expectancy, costs, drawdown and exposure accounting.
