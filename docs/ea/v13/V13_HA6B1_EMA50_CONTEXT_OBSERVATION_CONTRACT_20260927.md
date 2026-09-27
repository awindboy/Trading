# V13 HA-6B1 EMA50 raw-close context observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE MEASUREMENT / OBSERVATION ONLY`

## Question

Does a fixed, slower raw-price EMA context add Journey lifecycle information
beyond Standard-H4 HA morphology, ordered H1 path, HA-5 causal raw swings and
the HA-6A HASTOC relative-momentum coordinate?

## External source and fixed implementation

Research lead: MQL5 Article 20851, *Price Action Analysis Toolkit Development
(Part 54): Filtering Trends with EMA and Smoothed Price Action* (2026-01-16).
The article creates `iMA(..., 50, 0, MODE_EMA, PRICE_CLOSE)` as a broad trend
filter and compares the current EMA50 with the previous EMA50 to define slope.
It also uses EMA20 High/Low boundaries, but those are deliberately excluded
from HA-6B1 so the long-horizon EMA context can be attributed separately.

Use raw H4 CLOSE, not HA CLOSE, as the EMA input:

```text
alpha = 2 / (50 + 1)
EMA50_t = alpha * raw_close_t + (1-alpha) * EMA50_(t-1)
```

Initialize with the SMA of the first 50 available H4 raw closes. Because V13
warms from January 2022 and evaluation begins in January 2024, also report a
seed-sensitivity check against first-close initialization over the evaluation
window. This check is implementation robustness only, never a fitted choice.

## Causal clock and population

- GOLD# only; unchanged Standard-H4 Baseline-0 Journey population.
- Full frozen V13 comparison window.
- At the first executable tick after an H4 bar closes, EMA50 through that
  completed raw H4 close and its previous completed value are available.
- Future labels remain separate from decision features.
- Baseline-0 trades and EA remain unchanged.

## Predeclared EMA50 observations

For each Standard-H4 decision record:

1. `journey_ema50_slope_pct = side * (EMA50_t-EMA50_(t-1))/EMA50_(t-1)`.
   Positive means EMA slope agrees with the active Journey.
2. `journey_ha_close_to_ema50_pct = side * (HA_CLOSE_t-EMA50_t)/EMA50_t`.
   Positive means the completed HA close is on the Journey-favorable side of
   the raw-close EMA50.
3. `ema50_slope_aligned`: sign of observation 1.
4. `ema50_position_aligned`: sign of observation 2.
5. Four-state context: both aligned / slope only / position only / neither.

Exact zero remains a separate neutral case if it occurs; do not force it to a
side. Percent coordinates provide dimensionless display scale and are not ATR
normalization or trading thresholds.

## Predeclared comparisons

- Describe continuous slope and position coordinates in equal-count
  retrospective quintiles; quintiles are display bins only.
- Compare next-H4 flip, flip within 3 H4 bars, future peak-already-past,
  remaining favorable excursion and giveback.
- Compare slope/position alignment within existing H4 body/raw-close geometry,
  then H4 Delta contraction/wick state, ordered H1 path, HA-5 favorable
  rejection/return, and HA-6A HASTOC quintile where support remains.
- Specifically inspect last-H1-opposed decisions: does EMA50 distinguish a
  durable transition from a temporary H1 warning?
- Preserve year/side, Journey birth/continuation and >=10-bar Journey warning
  coverage / false-warning / remaining-tail accounting.

## Explicit exclusions

No EMA period optimization. No EMA20 High/Low channel. No EMA crossover entry.
No HA+EMA trade gate. No ADX, ATR, SuperTrend, RSI, volume, ML, SL, TP, sizing,
Child-admission or exit change. The source article's combined strategy is not
imported as V13 authority.

## Stop / advance rule

Stop HA-6B1 if EMA50 context is mostly redundant with existing HA/H1/raw-swing/
HASTOC state, or if warning states damage long-Journey participation. Only a
separately frozen follow-up may test EMA20 boundaries or an action rule.
