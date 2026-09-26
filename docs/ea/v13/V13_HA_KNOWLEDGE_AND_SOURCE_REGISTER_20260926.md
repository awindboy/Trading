# V13 Heikin-Ashi knowledge and source register

Date: `2026-09-26`
Status: `ACTIVE RESEARCH SOURCE MAP / NO TRADE AUTHORITY`

## 1. Purpose

V13 intentionally starts with a minimal standard-Heikin-Ashi strategy. This
register prevents the research from reducing HA to a single color bit and also
prevents external examples from silently becoming strategy rules.

It records:

- what standard HA mathematically contains;
- recurring ways practitioners analyze HA beyond color;
- common HA combinations;
- ML/ONNX usage examples;
- source reliability and implementation caveats;
- which ideas are allowed to enter the V13 research queue.

A source appearing here means **study it**, not **trade it**.

## 2. Source authority classes

### A — platform / reference authority

MetaQuotes documentation or official MetaQuotes CodeBase/reference material.
Controls platform semantics and the V13 definition of standard HA where clear.

### B — MQL5 implementation / research lead

MQL5 Articles, user CodeBase implementations or established forum work. Useful
for concrete formulas, features and testable ideas. Does not prove edge.

### C — academic / published empirical research

Peer-reviewed or research-repository work. Stronger evidence that an idea has
been systematically studied, but market/timeframe transfer still requires V13
reproduction.

### D — community / Market practice lead

Forum practice, commercial Market products and trading-system examples. Useful
to see what combinations exist; never proof of profitability.

### E — external educational material

Broker/educational material useful for standard interpretation and terminology.
Not strategy evidence.

## 3. Standard HA authority

### S01 — MetaQuotes Heiken-Ashi CodeBase

- class: `A`
- URL: https://www.mql5.com/en/code/33
- role: V13 standard formula authority.
- key semantics:
  - `HA Close = (raw O + H + L + C) / 4`;
  - `HA Open = (previous HA Open + previous HA Close) / 2`;
  - `HA High = max(raw High, HA Open, HA Close)`;
  - `HA Low = min(raw Low, HA Open, HA Close)`;
  - HA candles are synthetic, not executable market prices.
- V13 use: mandatory parity reference.

### S02 — Building a Professional Trading System with Heikin Ashi, Part 1

- class: `B`
- URL: https://www.mql5.com/en/articles/19260
- published: `2025-09-08`
- role: recent MQL5 implementation walkthrough for custom HA construction.
- V13 use: implementation cross-check only; S01 remains formula authority.

## 4. HA information beyond color

The Baseline-0 EA currently reduces each completed HA bar to one bit: BULL/BEAR.
Standard HA itself exposes more information.

### 4.1 HA Delta

```text
HA_DELTA = HA_CLOSE - HA_OPEN
```

Color uses only its sign. Magnitude contains HA-body information. Delta change
and Delta contraction/expansion can describe persistence or weakening while the
color remains unchanged.

### 4.2 Body / range / strength

```text
BODY = abs(HA_CLOSE - HA_OPEN)
RANGE = HA_HIGH - HA_LOW
BODY_STRENGTH = BODY / RANGE
```

The ratio measures how much of the synthetic candle is body versus wick. It is
not yet a V13 threshold.

### 4.3 Wick geometry

For a bullish HA candle, absence of a lower/opposite wick is commonly treated as
strong continuation; for bearish HA, absence of an upper/opposite wick is the
mirror case. Reappearance of the opposite wick plus body contraction is commonly
used as an indecision/transition cue.

### S03 — Professional HA System, Part 2: HA + Fractals

- class: `B`
- URL: https://www.mql5.com/en/articles/18810
- published: `2025-10-02`
- observed idea: defines a strong bullish HA candle as bullish with no lower
  wick, strong bearish as bearish with no upper wick, then requires a raw-price
  fractal breakout.
- V13 lesson: wick state and raw-price structure carry distinct information.
- caveat: article strategy results do not establish V13 edge.

### S04 — ExMachina Heikin Ashi Enhanced v3.0

- class: `B`
- URL: https://www.mql5.com/en/code/70827
- published: `2026-03-20`
- features relevant to V13:
  - proper recursive standard HA OHLC;
  - HA Delta;
  - same-color consecutive-bar counter;
  - body-to-range strength percentage;
  - MTF mapping;
  - SMA/EMA/DEMA/SMMA/LWMA smoothing;
  - optional step filter.
- V13 lesson: current community implementations explicitly expose the same
  morphology/persistence variables V13 should measure before adding indicators.
- caveat: feature availability is not evidence of predictive value.

### S05 — Charles Schwab Heikin-Ashi education

- class: `E`
- URL: https://www.schwab.com/learn/story/heikin-ashi-candles-reversals-and-strategies
- updated/published: `2026-01-06`
- observed interpretation:
  - long same-color runs describe trend persistence;
  - transition from long-body/no-opposite-wick bars to short bodies with wicks
    on both sides can mark uncertainty;
  - HA signals can appear later than raw-candle signals;
  - HA tends to work more naturally in strong trends than volatile/choppy
    conditions;
  - HA is often used with moving averages.
- caveat: educational interpretation, not V13 proof.

## 5. Smoothed HA and alternative HA representations

### S06 — Heiken Ashi Smoothed community implementation

- class: `B/D`
- URL: https://www.mql5.com/en/forum/266733
- idea: smooth/filter/average raw price before/within HA to suppress additional
  noise; common methods include SMA, EMA, SMMA and LWMA; optional step filters
  also exist.

### S07 — iHeikenAshiSm CodeBase

- class: `B`
- URL: https://www.mql5.com/en/code/142
- idea: HA with configurable moving-average and result-smoothing periods/methods.

### Research distinction that must be preserved

“Smoothed HA” is not one unique formula. External implementations may:

1. smooth raw OHLC before HA;
2. smooth HA outputs after calculation;
3. do both;
4. apply a step/no-change filter;
5. replace standard recursion with another formula.

Every V13 smoothed-HA experiment must name the exact transformation. It may not
silently be called standard HA.

## 6. HA Delta / oscillator-style use

### S08 — MQL5 community haDelta discussion

- class: `D`
- URL: https://www.mql5.com/en/forum/174562/page29
- origin discussed in thread: Dan Valcu haDelta concept.
- idea: treat `HA Close - HA Open` as a continuous value, optionally compare it
  with a smoothed signal line and zero.
- V13 lesson: color is a lossy sign transform of a richer continuous HA state.
- caveat: historical community discussion; research hypothesis only.

## 7. HA + raw-price structure

### S03 again — HA + Fractals

The 2025 MQL5 system uses HA to describe smoothed momentum and Fractals to
represent actual swing structure.

This is conceptually attractive for V13 because HA prices are synthetic. A raw
swing high/low or breakout answers a different question from HA persistence.

Allowed V13 role: observation after internal HA stages, then a one-component
comparison if warranted.

## 8. HA + moving averages / trend context

### S09 — Price Action Toolkit Part 54: EMA and Smoothed Price Action

- class: `B`
- URL: https://www.mql5.com/en/articles/20851
- published: `2026-01-16`
- implementation:
  - HA for smoothed candle direction;
  - EMA20 high/low as local boundaries;
  - EMA50 close/slope as broad trend context;
  - only accepts HA signals aligned with the EMA structure.
- V13 lesson: an MA can contribute a raw-price trend/reference scale distinct
  from HA morphology.
- caveat: the article's claims and backtests are research leads, not authority.

### S05 external corroboration

The 2026 Schwab education example overlays 8/21 EMAs with HA as a possible
trend/reversal confirmation tool.

## 9. HA + volatility / trend-strength tools

### S10 — HASuperTrendADX Market example

- class: `D`
- URL: https://www.mql5.com/en/market/product/183342
- published: `2026-06-27`
- example combination:
  - HA alignment;
  - SuperTrend calculated on HA OHLC;
  - ADX with optional DI confirmation;
  - ATR stop/trailing components.
- V13 lesson: current practice commonly separates smoothed direction, trend
  strength and volatility.
- caveat: commercial product description. It is evidence that the combination
  exists, not evidence that it is profitable or robust.

V13 must also recognize redundancy: HA, MA and SuperTrend are all trend-oriented
transformations and may merely stack lag. Any such experiment must state what
new information is expected.

## 10. HA-derived momentum — HASTOC

### S11 — Heiken Ashi Stochastic (HASTOC)

- class: `C`
- published paper: https://onlinelibrary.wiley.com/doi/10.1002/ijfe.2245
- open research record: https://mpra.ub.uni-muenchen.de/90439/
- published research objective: combine HA trend-generation information and
  momentum in one numerical indicator.
- reported testing: multiple currencies, an index/equity and several timeframes;
  positive results are reported for selected markets/timeframes.
- V13 lesson: a HA-derived momentum representation deserves study before
  assuming that generic RSI/MACD is the only way to add momentum.
- caveat: external markets and selected timeframes are not GOLD# V13 evidence.

## 11. Volume / participation concepts

MQL5 Market and community tools also combine HA with volume, delta or VSA-style
participation measures. These are retained as a later research family because
HA itself is price-derived and contains no independent participation variable.

V13 rule: before using tick volume on GOLD#, verify what the broker field means
and whether it is stable enough for the intended comparison. No volume gate is
currently authorized.

## 12. Multi-timeframe HA

### S04 — ExMachina MTF support

The 2026 CodeBase implementation maps higher-timeframe HA onto the active chart.
MTF HA is conceptually different from changing the HA formula: it observes the
same standard representation on different time scales.

V13 later-stage candidates:

- D1 standard HA as broader context for H4;
- H1 standard HA as faster transition information around H4 lifecycle changes.

They must be tested separately; no forced alignment rule exists today.

## 13. HA + machine learning / ONNX

### S12 — PSAR, Heiken Ashi and Deep Learning

- class: `B`
- URL: https://www.mql5.com/en/articles/15868
- published: `2024-09-18`
- example stack: HA + PSAR + SMA + RSI + ATR + deep-learning/ONNX prediction.
- reported quick-test result is modest and explicitly exploratory.
- useful lesson: HA can be a model feature/context rather than the whole trading
  system.

### Critical formula audit on S12

The article's Python example calculates `ha_open` from prior **raw** open/close,
not prior **HA** open/close. It therefore does not implement V13 standard HA as
specified by S01. The source remains useful for ML integration ideas but cannot
be copied as HA formula authority.

### S13 — MetaQuotes: ML pipeline to ONNX in MQL5

- class: `A/B` (MetaQuotes-authored engineering article)
- URL: https://www.mql5.com/en/articles/22474
- published: `2026-05-14`
- key engineering lesson:
  - feature generation, scaling and dimensional transforms must be reproduced
    consistently between training and terminal inference;
  - Python trains the model;
  - ONNX transports the fixed computation;
  - MQL5 must reproduce the same preprocessing/input space.
- V13 role: engineering authority if ML is eventually promoted toward MT5.

### S14 — 2026 conference multi-model HA example

- class: `C-low / exploratory proceedings`
- URL: https://cdn.iferp.in/conf-proceedings/2026/15th_ICRCET_2026.pdf
- described system: 5-minute HA with MTF validation and an ensemble of SVM,
  Random Forest, XGBoost, CatBoost, MLP, LSTM and RNN with adaptive retraining.
- V13 lesson: advanced HA+ML assemblies exist.
- caveat: conference proceeding description is insufficient evidence for edge,
  leakage control, execution realism or reproducibility.

## 14. What V13 should measure before adding anything

The highest-priority fields are all available from standard HA + raw H4:

```text
ha_open
ha_high
ha_low
ha_close
ha_color
ha_delta
abs_ha_delta
ha_body
ha_range
ha_body_to_range
ha_upper_wick
ha_lower_wick
ha_directional_wick
ha_opposite_wick
ha_no_opposite_wick
same_color_streak
delta_change
abs_delta_change
body_change
body_expansion_ratio
raw_body
raw_range
raw_close_minus_ha_close
raw_close_minus_ha_open
raw_extreme_distance_to_ha_body
```

No field above is an entry/exit rule by itself.

## 15. Source-to-roadmap mapping

```text
S01/S02 -> formula parity and standard-HA ledger
S03/S04/S05/S08 -> morphology, Delta, wick, streak, lifecycle
S06/S07/S04 -> smoothed HA variants
S04 -> MTF standard HA
S03 -> raw-price/fractal structure
S09/S05 -> MA context
S11 -> HA-derived momentum / HASTOC
S10 -> ATR/ADX/SuperTrend research family
volume/VSA leads -> participation family
S12/S13/S14 -> ML architecture only after representation work
```

## 16. Non-negotiable source rule

No source may be imported by reputation, popularity or claimed profitability.
For every candidate:

1. reproduce exact semantics;
2. identify what information is genuinely new relative to standard HA;
3. define causal decision-time fields;
4. test observationally before granting action;
5. if action is later proposed, freeze one change and compare it over the full
   V13 canonical window.
