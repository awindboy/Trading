# V13 HA-6C ATR normalization observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE MEASUREMENT / OBSERVATION ONLY`
GitHub authority base: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## Question

Does volatility normalization materially change or stabilize the descriptive
relationships already observed in V13 HA morphology and MA context across the
2024-2026 GOLD# volatility/price regimes?

ATR is a **coordinate only** in HA-6C. It is not an entry filter, volatility
regime gate, stop distance, take-profit distance, sizing rule or score.

## Fixed ATR representation

Use raw H4 OHLC and the standard MetaQuotes ATR period `14` convention:

```text
TR_t = max(H_t, C_(t-1)) - min(L_t, C_(t-1))
ATR14_t = mean(TR_(t-13) ... TR_t)
```

Warm-up starts from the supplied 2022 H4 source. At an H4 decision the signal
bar is completed, so its ATR14 is causally known. No future bar contributes to
the denominator.

Period 14 is frozen from the standard MetaQuotes ATR implementation/default;
there is no period search. A one-bar-lagged ATR is retained only as a numerical
sensitivity diagnostic and may not be selected post hoc.

## Existing population and parity

- GOLD# only.
- Frozen V13 window: 2024-01-01 through the last completed H4 decision before
  the 2026-08-28 20:00 execution open.
- Preserve 4,108 decision rows, 4,105 rows with future labels, 965 closed
  Journeys and 3,858 closed-Journey Children.
- Reuse the unchanged Standard-H4 Journey, ordered H1 state, HA-5 raw-swing
  state, HA-6A HASTOC and HA-6B EMA50/EMA20 semantics.
- Decision features and future labels remain physically separate.

## Primary normalized coordinates

For each completed H4 decision compute, without thresholds:

```text
abs HA Delta / ATR14
opposite HA wick / ATR14
raw H4 range / ATR14
Journey-signed (raw Close - HA Close) / ATR14
Journey-signed EMA50 one-bar slope / ATR14
Journey-signed (HA Close - EMA50) / ATR14
Journey-signed (HA Close - directional EMA20 High/Low boundary) / ATR14
```

HASTOC remains unchanged because it is already dimensionless. Existing
body/range and raw-close/H4-range ratios remain controls rather than being
replaced.

## Outcome normalization

Re-express the already-frozen future quantities in ATR14 units using only the
ATR14 known at the decision:

```text
remaining favorable raw-price excursion / decision ATR14
giveback from final favorable extreme to Baseline HA exit / decision ATR14
```

The future numerator is a label; ATR14 is the frozen decision-time denominator.
This does not make the future quantity a live signal.

## Predeclared comparisons

1. Compare raw price-unit feature medians across 2024/2025/2026 with their
   ATR14-normalized medians. Report whether year-to-year scale drift contracts.
2. For HA Delta, opposite wick and raw-vs-HA displacement, use full-window
   equal-count quintiles and compare next-H4 / 3-H4 transition gradients by
   year and side. Quintiles are display bins only.
3. Compare EMA50/EMA20 coordinates in percent-of-price form from HA-6B versus
   ATR14 form. Do not choose a representation based on the better-looking P/L;
   assess stability and incremental descriptive information only.
4. Compare raw future favorable/giveback price medians, trailing-20-H4-range
   units already used by HA-4C/5/6A, and ATR14 units by year and side.
5. Report ATR14 magnitude/price diagnostics separately only to show regime
   scaling. Do not interpret low/high ATR as a trading state.
6. Preserve >=10-bar Journey tail accounting. ATR normalization cannot be used
   to erase or downweight long-Journey false warnings.

## Promotion boundary

No threshold, ATR regime, entry veto, Child admission rule, exit, Hard SL, TP,
trailing rule, sizing change, EA change or MT5 economic claim is authorized.

HA-6C succeeds if it supplies a more stable measurement coordinate, even if it
adds no predictive information. It should stop if it only rescales variables
without changing their interpretation.
