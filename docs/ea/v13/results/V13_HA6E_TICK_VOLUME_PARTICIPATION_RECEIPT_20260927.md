# V13 HA-6E tick-volume participation receipt

Date: `2026-09-27`
Status: `HA-6E OBSERVATION COMPLETE / ONE HA-7 CANDIDATE MECHANISM IDENTIFIED / NO TRADE AUTHORITY`
Base GitHub main HEAD: `40f97352e47c66cd3b952f74532b1b71969e79fd`
Market/window: `GOLD# / 2024-01-01 through 2026-08-28 available history`

## 1. Platform/source semantics

MetaQuotes `MqlRates` separates `tick_volume` from `real_volume`. The current GOLD# export contains zero `<VOL>` on every H4 bar; only `<TICKVOL>` is populated. Tick volume is therefore treated strictly as broker-feed quote/tick activity, not centralized traded gold quantity.

Useful external references:
- https://www.mql5.com/en/docs/constants/structures/mqlrates
- https://www.mql5.com/en/book/applications/timeseries/timeseries_ohlcvs
- https://www.mql5.com/en/articles/22628
- https://www.mql5.com/en/articles/17065

## 2. Data-quality result

- H4 rows: `7,199`
- duplicate H4 timestamps: `0`
- H4 zero tick-volume rows: `0`
- H4 nonzero real-volume rows: `0`
- M1 -> H4 summed `<TICKVOL>` parity: `7,199 / 7,199 exact`
- M1 aggregated real volume: always zero

Absolute H4 tick-volume medians drift materially:

```text
2024  25,022
2025  37,382
2026  56,328.5
max/min = 2.251x
```

H4-slot raw median max/min is `3.437x`. Absolute tick counts are therefore not a valid cross-year/session coordinate.

The fixed same-slot trailing-20 normalization reduced this strongly:

```text
year relative-volume median max/min = 1.048x
H4-slot relative-volume median max/min = 1.017x
```

## 3. HA-6E1 full-H4 relative participation

Primary coordinate:

`relative_tick_volume20 = current H4 tick_volume / median(previous 20 same-H4-slot tick volumes)`

Equal-count quintiles on the 4,105 labeled decisions:

```text
Q1  n=821  next flip 28.5%  flip<=3 61.3%  remaining favorable 0.61 ranges
Q2  n=821  next flip 25.5%  flip<=3 60.4%  remaining favorable 0.69
Q3  n=821  next flip 23.1%  flip<=3 55.2%  remaining favorable 0.83
Q4  n=821  next flip 20.5%  flip<=3 53.2%  remaining favorable 0.84
Q5  n=821  next flip 19.7%  flip<=3 52.1%  remaining favorable 0.93
```

Raw Q1-vs-Q5 separation is large, but most of it is not independent. Within H4 morphology cells the weighted next-H4 difference shrinks to `+0.65 percentage points`. Adding H1/raw-state controls leaves about `+2.43 points`; adding HASTOC/MA leaves `+4.22 points` but only 535 comparable rows; adding ADX/DMI leaves only 46 comparable rows and no next-H4 difference.

Spearman association of relative tick volume with selected prior fields is moderate rather than independent-zero: `0.276` with ATR-normalized HA Delta and `0.335` with ADX14.

Conclusion: full-H4 relative tick activity mostly describes the intensity of price states already present in V13. It is not a standalone volume gate.

## 4. Important H1-path interaction

The predeclared H1-path breakdown is not uniform.

`persistent_opposition` is the exception: when all available H1 HA bars inside the H4 bar oppose the current H4 Journey, greater participation is associated with *more* transition, not continuation.

Using full-H4 relative-volume display tails:

```text
persistent_opposition Q1: next flip 39.7%
persistent_opposition Q5: next flip 68.8%
```

This prompted one narrower frozen HA-6E2 probe before outcome measurement.

## 5. HA-6E2 H1 opposition-localized participation

H1 standard HA was rebuilt from the H1 export. Reconstructed H1 path state matched the existing HA-4C ledger on all `4,108 / 4,108` decisions.

H1 bars per H4 decision in the source history:

```text
1 bar:   2 decisions
2 bars: 18
3 bars: 683
4 bars: 3,405
```

For each opposed H1 bar, tick volume was normalized against the previous 20 H1 bars of the same start hour. The mean normalized activity of opposed H1 bars was then measured.

### Repaired H1 opposition

```text
Q1 next flip 19.5%
Q5 next flip 13.5%
```

Higher opposed-bar activity does not imply reversal after the opposition has already repaired.

### Unrepaired mixed opposition

```text
Q1 next flip 47.9%
Q5 next flip 45.5%
```

No stable tail separation.

### Persistent opposition

```text
Q1 n=44  next flip 36.4%  flip<=3 56.8%  peak already 47.7%  rem fav 0.85 ranges
Q5 n=44  next flip 65.9%  flip<=3 88.6%  peak already 84.1%  rem fav 0.43 ranges
```

Journey-cluster bootstrap of Q5-Q1 difference:

```text
next-H4 flip: observed +29.5 pp; 95% percentile interval about +7.8 to +50.3 pp
flip<=3:      observed +31.8 pp; 95% percentile interval about +14.1 to +48.9 pp
```

The Q5-Q1 direction remains positive inside body and ATR-normalized Delta tertiles. Year x side is positive in 5/6 slices, with 2025 SHORT the exception; slice counts are small.

However, opposed-H1 activity and full-H4 relative tick volume are almost the same information in persistent opposition (`Spearman rho = 0.973`). The lower-timeframe localization therefore does **not** justify a second volume signal.

## 6. Tail preservation warning

Persistent-opposition high-participation states still generate false warnings inside long Journeys.

Using the globally defined persistent-opposition H1-activity Q5:

```text
44 total events
29 next-H4 flips
39 flips within 3 H4 bars
15 not next-H4 flips
5 not within-3 flips
10 events occurred in >=10-bar Journeys
4/10 flipped next H4
7/10 flipped within 3 H4 bars
```

False next-H4 warnings inside long Journeys can still have materially favorable movement left. This rules out an immediate Journey exit based only on this observation.

## 7. Fixed semantic boundary candidate

A non-optimized, semantically defined diagnostic is `relative_tick_volume20 > 1.0`, meaning activity above its own causal same-slot trailing median.

Inside persistent opposition:

```text
>1.0: 100 decisions, 57.0% next flip, 79.0% flip<=3
<=1.0:119 decisions, 46.2% next flip, 64.7% flip<=3
```

The >1.0 group has higher next-H4 flip in 5/6 year/side comparisons and higher flip<=3 in the broad pooled sample, but it is still not a safe exit. In >=10-bar Journeys, continuation decisions with persistent opposition and >1.0 participation numbered 25; only 24% flipped next H4 and 44% within three H4 bars, with median `2.04` favorable ranges still available.

## 8. HA-6E conclusion

`HA-6E COMPLETE / NO VOLUME EXIT OR FILTER AUTHORITY`

What survives as a mechanism candidate is contextual:

> Persistent H1 opposition carries more transition information when the completed H4 bar's tick activity is above its own recent same-slot baseline. The same volume state is not useful as a universal rule, and localized H1 volume is almost redundant with total H4 relative volume.

Because exiting the Journey would destroy long-tail exposure, the only justified first HA-7 development experiment is narrower: suppress **one new add-on Child** on a continuation bar when persistent H1 opposition coexists with above-baseline relative tick participation, while leaving all existing positions and the Journey itself untouched.

This remains consumed-data development evidence. Untouched future data is required for any strong promotion claim.
