# V13 HA-6D1 ADX Wilder observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE MEASUREMENT / OBSERVATION ONLY`
Authority base GitHub HEAD: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## Question

Does raw-price directional-movement strength from Welles Wilder ADX add Journey
continuation/transition information beyond Standard-H4 HA morphology, ordered H1
path, HA-5 causal raw swings, HA-6A HASTOC, HA-6B MA context and HA-6C
volatility-aware coordinates?

This is not a threshold-filter study and it does not add SuperTrend.

## Fixed representation

Use H4 raw OHLC and Wilder period 14. Follow the MetaQuotes ADX Wilder family:

- positive and negative directional movement from consecutive raw highs/lows; when both are positive, retain only the larger directional move (a tie zeros both), matching the standard Wilder DMI construction;
- True Range from current high/low and previous close;
- Wilder/SMMA smoothing over 14 bars;
- `+DI = 100 * smoothed(+DM) / smoothed(TR)`;
- `-DI = 100 * smoothed(-DM) / smoothed(TR)`;
- `DX = 100 * abs(+DI - -DI) / (+DI + -DI)`;
- `ADX14 = Wilder/SMMA(DX, 14)`.

Warm up from the supplied 2022 H4 history. By the 2024 evaluation boundary the
long warm-up makes initialization effects negligible, but the implementation
still uses the conventional Wilder seed (first 14 valid values averaged, then
recursive `(prev*(n-1)+x)/n`).

## Decision-time fields

At each frozen Standard-H4 decision, using only the just-completed H4 bar:

1. `adx14_wilder` — directionless trend-strength coordinate.
2. `journey_di_margin = side * (+DI14 - -DI14)` — direction-normalized DMI
   margin. Positive means DMI agrees with the active HA Journey.
3. `di_aligned = journey_di_margin > 0` (exact zero is neutral and retained
   separately if it occurs).
4. `adx_rising = ADX14_t > ADX14_(t-1)` when the prior H4 value exists.
5. `adx_change = ADX14_t - ADX14_(t-1)` as a continuous descriptive coordinate.

No `ADX > 20`, `ADX > 25`, DI spread cutoff, crossover delay, cooldown, score,
or selected numerical threshold is authorized.

## Predeclared comparisons

1. ADX14 equal-count quintiles: next-H4 flip, flip within 3 H4 bars,
   future-peak-already-past label, remaining favorable excursion and giveback.
2. DI alignment and ADX rising/falling separately; then their four joint states.
3. Check redundancy/increment against the existing state stack:
   - H4 body/range and raw-close geometry;
   - H4 Delta contraction and opposite-wick state;
   - ordered H1 path;
   - HA-5 favorable rejection/return;
   - HA-6A journey HASTOC;
   - HA-6B EMA50 slope/position and EMA20 envelope state;
   - HA-6C ATR-normalized H4 Delta/raw-close displacement.
4. Use only descriptive overlap cells with adequate support; report coverage.
   Do not extrapolate an incremental effect to non-overlap rows.
5. Report 2024/2025/2026 x LONG/SHORT diagnostics, Journey birth/continuation,
   and all >=10-bar Journeys. False warnings and remaining favorable movement
   are mandatory.
6. Because the whole 2024-2026 period is consumed development data, resampling
   or intervals describe this sample only; they are not OOS validation.

## Stop / advance rule

Stop HA-6D1 if ADX/DMI mostly repackages existing HA/MA/ATR state or if apparent
transition separation has unacceptable long-Journey false-warning cost.

Only a separately frozen later stage may study SuperTrend. No entry, Child
admission, exit, SL, TP, sizing, EA or MT5 economic rule is created here.
