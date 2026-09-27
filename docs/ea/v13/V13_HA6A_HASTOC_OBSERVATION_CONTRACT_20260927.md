# V13 HA-6A HASTOC observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE MEASUREMENT / OBSERVATION ONLY`

## Question

Does the relative position of the current signed Standard-H4 Heikin-Ashi body
inside its own recent signed-body history add Journey lifecycle information
beyond Standard-H4 morphology, the ordered H1 path, and the HA-5 causal
raw-price swing interaction?

This is not an oscillator-entry study and does not import the source paper's
trading thresholds.

## Source and fixed formula

Primary research source: Smita Roy Trivedi, *Technical analysis using Heiken
Ashi Stochastic: To catch a trend, use a HASTOC*, International Journal of
Finance & Economics 27(2), 1836-1847; first published 2020. The open MPRA
working-paper record provides the formula and sample table.

The paper defines HASTOC from the difference between HA Open and HA Close and
normalizes it to 0-100 over ten periods. The published sample table is exactly
reproduced by the following orientation and rolling convention:

```text
D_t = HA_OPEN_t - HA_CLOSE_t
HASTOC10_t = 100 * (D_t - min(D[t-9:t])) /
                   (max(D[t-9:t]) - min(D[t-9:t]))
```

The current completed H4 bar is included in the ten-bar window. Warm-up bars
before 2024 initialize the window. If the denominator is zero, record missing.
The published sample's first available values are reproduced as
`100.000, 97.725, 86.938` before GOLD# outcomes are inspected.

For side-comparable display only:

```text
LONG  journey_hastoc10 = 100 - HASTOC10
SHORT journey_hastoc10 = HASTOC10
```

Larger values therefore mean the current signed HA body lies nearer the recent
ten-bar extreme in the current Journey direction. This is a coordinate, not a
strength threshold.

## Population and causal timing

- GOLD# only.
- Standard H4 HA warmed from the 2022 source start.
- Frozen V13 Baseline-0 Journey sequence and canonical 2024-01-01 through
  2026-08-28 decision window.
- One feature row per completed H4 decision; no forming H4 data.
- Future outcomes remain physically separate.
- Existing HA-4C H1 path and HA-5 causal raw-swing states are comparison
  context only; they do not change trades.

## Predeclared fields and comparisons

Record raw `HASTOC10`, side-normalized `journey_hastoc10`, same-Journey one-bar
change, and ten-bar D range. Describe level/change continuously and by
retrospective equal-count quintiles. Compare next-H4 flip, flip within three H4
bars, future peak-already-past, remaining favorable excursion and giveback.

Then test whether apparent separation survives comparison with:

1. H4 body/range and raw-close-versus-HA geometry;
2. H4 Delta contraction and opposite-wick state;
3. ordered H1 path state;
4. HA-5 favorable raw-swing rejection/return state.

Report year/side, Journey birth/continuation and >=10-bar Journey diagnostics.
Quintiles are display bins, never trading thresholds.

## Explicit non-imports

The paper discusses levels such as 5%, 30%, 50% and 70%. None is imported.
HASTOC(W), generic Stochastic/RSI, MA, ATR, ADX, SuperTrend and volume are
separate measurements/families and are not bundled into this first probe.

No threshold, veto, Child admission rule, exit, SL, TP, sizing, score, EA
change or MT5 economic claim is authorized.
