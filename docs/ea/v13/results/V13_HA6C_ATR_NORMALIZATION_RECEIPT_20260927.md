# V13 HA-6C ATR normalization observation receipt

Date: `2026-09-27`
Status: `OBSERVATION COMPLETE / NORMALIZATION COORDINATE ONLY / NO ACTION AUTHORITY`
Authority base checked before work: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## Scope and source parity

HA-6C follows roadmap HA-6C exactly: ATR is used to normalize measurements, not
as a signal. The frozen coordinate is completed-H4 MetaQuotes-style ATR14,
computed from 14 raw H4 True Ranges. There was no ATR period search.

The currently mounted source files are byte-different from the hashes recorded
in the HA-5 receipt because the current exports include the trailing 2026-08-28
20:00 H4 bar and M1 prints through 23:57. This does not alter the frozen decision
window. A fresh chronological M1 -> H4 parity audit consumed 1,648,545 current
M1 rows and matched all 7,199 current exported H4 OHLC bars with zero mismatches
and zero missing bars. The frozen Baseline population also reproduced:

```text
4,108 decision rows
4,105 rows with future labels
966 Journey IDs begun
965 closed Journeys
3,858 Children in the 965 closed Journeys
1,395 ending-H1-opposed decisions
235 ending-H1-opposed + HA-5 favorable rejection/return decisions
138 next-H4 flips inside those 235
```

Thus the active decision prefix is structurally consistent with HA-4C/5/6A/6B.

## 1. GOLD# price-unit scale drift is large

Median H4 ATR14 by year:

| Year | ATR14 price | ATR14 / raw Close | Raw H4 range |
| --- | ---: | ---: | ---: |
| 2024 | 11.99 | 0.486% | 10.26 |
| 2025 | 20.27 | 0.593% | 18.98 |
| 2026 | 41.01 | 0.902% | 38.78 |

ATR14 itself rose 3.42x from the lowest to highest yearly median. Raw H4 range
rose 3.78x. Volatility therefore changed materially even after considering the
higher Gold price; ATR/Close rose about 1.86x.

ATR14 is not a useful standalone transition selector in this consumed sample.
Across ATR14 quintiles, next-H4 flip rates were 24.36%, 24.00%, 22.66%, 23.39%
and 22.90%. This is recorded only to prevent later reinterpretation of HA-6C as
an ATR volatility gate.

## 2. ATR normalization removes most price-unit drift from HA measurements

Yearly median magnitude drift before and after dividing by ATR14:

| Measurement | Raw max/min yearly median | ATR-normalized max/min |
| --- | ---: | ---: |
| |HA Delta| | 3.91x | **1.10x** |
| opposite-wick magnitude | 2.84x | **1.38x** |
| |raw Close - HA Close| | 3.86x | **1.03x** |
| |HA Close - EMA50| | 3.89x | **1.23x** |
| |EMA50 one-bar slope| | 3.82x | **1.23x** |
| |HA Close - EMA20 directional boundary| | 3.65x | **1.20x** |

Examples make the effect clear. Median absolute HA Delta was 4.50 / 8.79 /
17.60 price units in 2024/2025/2026, but 0.396 / 0.434 / 0.409 ATR14. Median
absolute raw-Close-minus-HA-Close was 2.17 / 3.97 / 8.40 price units, but
0.189 / 0.195 / 0.192 ATR14.

This confirms that fixed GOLD price-unit thresholds would be era-dependent and
should not be inferred from the consumed V13 sample.

## 3. Morphology relationships become more cross-year stable, but not new

For |HA Delta|, the pooled next-H4 flip gradient is strongly monotone in both raw
and ATR coordinates:

```text
raw Delta quintiles: 41.5%, 30.5%, 21.8%, 14.9%, 8.7%
Delta / ATR14:       42.9%, 31.8%, 23.9%, 15.2%, 3.5%
```

More important than the stronger pooled extreme is stability. Using frozen
full-window cut points, the six 2024/2025/2026 x LONG/SHORT Q1-minus-Q5
next-flip contrasts ranged over 20.1 percentage points in raw Delta space but
only 10.8 points after ATR normalization.

The Journey-signed raw-Close-minus-HA displacement similarly reduced the spread
of the six year/side Q1-Q5 contrasts from 25.0 to 17.8 percentage points after
ATR normalization.

However, these are not independent signals. In the same 4,105 decisions:

```text
corr(|HA Delta| / ATR14, H4 body/range) = +0.754
corr(Journey rawClose-HAclose / ATR14, existing rawClose/H4-range) = +0.883
corr(|HA Delta| / ATR14, Journey HASTOC10) = +0.449
```

ATR normalization therefore improves the coordinate for existing morphology;
it does not create a new vote.

## 4. EMA context is rescaled, not repaired

The MA-family price magnitudes also become far more comparable across years,
but ATR normalization does not make EMA50/EMA20 a robust immediate transition
selector.

Correlation between the previous HA-6B percent-of-price coordinate and the new
ATR coordinate is still high:

```text
HA Close to EMA50:  +0.897
EMA50 one-bar slope: +0.896
HA Close to EMA20 directional boundary: +0.884
```

The year/side transition gradients did **not** consistently become more stable:
EMA50-distance, EMA50-slope and EMA20-distance Q1-Q5 gradient dispersion was
similar or sometimes larger after ATR normalization. This supports the HA-6B
interpretation: the MA family carries slower trend/regime context, and its main
problem is not merely a bad price scale.

## 5. Existing trailing-range outcome normalization was already strong

Raw remaining-favorable median by year rose:

```text
2024  7.52 price
2025 16.33
2026 30.38
max/min = 4.04x
```

Re-expressing it in decision ATR14 units gives:

```text
2024 0.620 ATR
2025 0.777 ATR
2026 0.654 ATR
max/min = 1.25x
```

But the existing trailing-20-H4 median-range coordinate used in HA-4C/5/6A was
already at 0.742 / 0.835 / 0.774, only 1.13x max/min.

The same is true for giveback:

```text
raw price max/min:             3.45x
trailing-20-H4-range max/min:  1.06x
ATR14 max/min:                 1.08x
```

Therefore HA-6C does **not** justify replacing the existing trailing-range
outcome coordinate with ATR14. Both remove most era scale; the existing
coordinate is at least as stable for these lifecycle outcomes.

## 6. Current-bar versus one-bar-lagged ATR sensitivity is small

Using the completed signal bar's ATR14 is the frozen primary convention. As a
non-selective numerical sensitivity check, substituting the preceding H4 ATR14
changed the median normalized |HA Delta| by only 0.011 ATR units and normalized
raw H4 range by 0.027 units. No alternate denominator is selected.

## 7. Tail preservation remains visible

All 88 Journeys with at least ten completed Standard-H4 bars remain in scope
(1,129 decisions). Their median remaining favorable excursion is 2.07 ATR14
versus 2.36 trailing-H4 ranges. Normalization changes units, not the existence
of the long right tail. No earlier false-warning evidence is erased.

## Interpretation

HA-6C succeeds as a measurement stage:

1. raw GOLD price-unit features are strongly era-dependent;
2. ATR14 removes most of that scale drift for HA morphology and displacement;
3. the resulting variables largely remain alternate coordinates of already
   measured HA morphology/HASTOC/raw-close state;
4. MA-context weakness is not solved by changing its denominator;
5. V13's existing trailing-20-H4 median-range outcome normalization is already
   as stable as, or slightly more stable than, ATR14 for the lifecycle labels;
6. ATR level itself showed little monotone next-H4 transition separation and
   gains no signal authority.

No ATR threshold, volatility regime, entry filter, Child veto, exit, Hard SL,
TP, trailing rule, sizing change or EA change is authorized.

Roadmap HA-6C is complete. The next distinct family is HA-6D, but ADX and
SuperTrend must not be bundled: a next contract should first isolate one named
trend-strength construction and state what information it can add beyond HA
morphology, raw structure, HASTOC, MA context and normalized scale.
