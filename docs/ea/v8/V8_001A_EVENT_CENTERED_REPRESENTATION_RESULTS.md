# V8-001A-r3 — Event-Centered Causal Representation Results

Status: `PASS / SUPERSEDES V8-001A-r1 VISUAL SCALING`
Date: `2026-08-30`
GitHub base used for implementation: `25c4f912cb3c83aa96ef640088702cc0e33d7f49`
Production authority: `NONE`
EA authority: `NONE`
Economic outcomes opened for this representation decision: `NO`

## 1. Why r3 exists

The first V8 renderer used an independent visible-window y-scale. That preserved local visual detail, but it
meant two events with very different absolute displacement could be stretched into a similar-looking image.

The user proposed a simpler invariant coordinate:

```text
C0 = event/decision anchor candle close
price_level' = price_level - C0
```

The event close therefore becomes exactly zero.

This solves absolute-price translation without requiring a hard trend/range label or ATR-normalizing the
entire chart.

## 2. Frozen coordinate rule

At each decision timestamp use one shared causally-known reference close:

```text
reference_close = last completed M1 close at decision_time
```

For every current factual anchor in V8-001A this equals the close of the source event candle.

The same reference is shared by H1/M15/M5/M1.

Price-level fields are transformed by subtraction only:

```text
open, high, low, close
SMA20 close
H1 SMA4 open
BB20 upper/lower
H1 BB4 upper/lower
future visible S/R price levels when later added
campaign average-entry price when supplied to the model

x' = x - reference_close
```

Magnitude/meta fields are **not** shifted or divided by the reference close:

```text
ATR
standard deviations / band width magnitudes
spread
volume / tick activity
source-row count
time/event flags
risk in R
```

They stay in native units at the representation layer.

## 3. Full-ledger origin parity

The rule was checked against the complete factual V8-001A event ledger:

```text
416,136 events checked
reference_close != source_event_candle_close: 0
maximum absolute difference: 0.0
PASS
```

Thus the shared origin is not an approximate M1 proxy for the event close in the current data. It is exactly
the same close.

## 4. Translation invariance test

A synthetic market path was duplicated with every OHLC price shifted upward by a constant `+1234.5`.
Indicators were recomputed from the shifted source.

After event-close centering:

- all numerical observation tensors matched;
- rendered image hashes matched;
- price magnitude/meta fields retained their native values.

This is the direct acceptance test for the intended invariance:

> the representation should not care whether the same geometry occurs around GOLD 1800 or GOLD 3300.

## 5. Important visual correction: one fixed wide scale is not enough

A single fixed visual range derived from ~99.5% coverage made low-volatility historical events too flat to
read visually.

Using per-event autoscaling would restore readability but violate the new invariant representation goal.

V8-001A-r3 therefore uses a **fixed multi-scale visual pyramid**. The underlying coordinates do not change;
only the raster zoom differs.

Frozen half-spans in GOLD price units:

| TF | tight | medium | wide |
|---|---:|---:|---:|
| H1 | +/-100 | +/-325 | +/-750 |
| M15 | +/-40 | +/-160 | +/-375 |
| M5 | +/-25 | +/-90 | +/-225 |
| M1 | +/-10 | +/-40 | +/-100 |

Every event uses exactly these same scales.

The scale identities are explicit model tokens/configuration; the model is never allowed to infer an unknown
auto-zoom factor.

## 6. Outcome-blind scale derivation

The fixed scale pyramid was derived without future-path or P/L labels from the frozen first V8-001B anchor
population (`66,277` decision times).

For each timeframe the maximum absolute visible price-level distance from event close was measured.

Representative distribution:

| TF | median | p95 | p99.5 | wide frozen |
|---|---:|---:|---:|---:|
| H1 | 73.42 | 300.60 | 701.75 | 750 |
| M15 | 32.70 | 149.34 | 352.43 | 375 |
| M5 | 18.47 | 82.71 | 216.23 | 225 |
| M1 | 7.60 | 37.39 | 99.33 | 100 |

Wide-scale clipping is below `0.5%` on every timeframe in the calibration population.

Tight-scale clipping is intentional: it is a fixed close-up view, while medium and wide preserve the broader
geometry.

## 7. Numerical observation changes

The previous ATR/window normalization was removed from the base representation.

The model-ready numerical stream now keeps:

- event-centered price levels in raw GOLD price units;
- exact native ATR;
- exact recorded spread values;
- exact tick activity / volume;
- exact standard-deviation magnitudes;
- exact source-row counts.

A later neural model may use **training-fold-only optimizer scaling** internally, but that is a model adapter,
not representation authority. Price offsets must keep zero as zero.

## 8. Causal audit after the change

`V8-001A-r3-event-close-multiscale` reran the full representation audit.

Result:

```text
Overall PASS
28 outcome-blind sample events
three fixed visual scales per sample
no event-close origin mismatch
no completed-bar/future visibility failure
no indicator-prefix failure
no raw-resample-prefix failure
no deterministic render hash mismatch
no visual/numerical timestamp parity failure
```

Unit tests:

```text
8 tests
8 PASS
```

The new tests specifically cover:

- event close = numerical zero origin;
- magnitude fields remain native;
- constant-price translation invariance for numerical and visual representation.

## 9. Decision

`V8-001A-r3` supersedes the previous r1/r2 visual scaling as the first V8 representation authority.

The representation is now ready for V8-001B model comparison under one common coordinate system.

No trading-policy claim is implied.
