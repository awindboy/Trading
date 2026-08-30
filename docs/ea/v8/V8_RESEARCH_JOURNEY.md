# V8 Research Journey — From Chart Representation to Movement Probability

Date: `2026-08-31`
Status: `CURRENT V8 RESEARCH NARRATIVE / SSOT COMPANION`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Why V8 was opened

V8 began after repeated strategy research showed a recurring failure mode: ambiguous human chart concepts were being converted too early into exact labels or thresholds.

Examples included:

```text
TREND
RANGE
BREAKOUT
TURNING
HEALTHY_PULLBACK
TERMINAL_EXPANSION
```

The problem was not that these ideas are meaningless to a trader. The problem was that an exact numerical rule could be perfectly deterministic while still being the wrong proxy for the human concept.

The V8 reset therefore started from a representation-first thesis:

```text
observable event
+ causal chart/history representation
+ exact numerical context
+ campaign state
        ↓
learn context without forcing a semantic state label
        ↓
reason about future path / actions
```

Double-B, MA contact, Bollinger contact, session interaction and later campaign events were treated as factual attention anchors rather than directional labels.

## 2. First representation foundation

The first V8 implementation built causal M1/M5/M15/H1 streams from the unified GOLD# M1 source.

Source used in open development:

```text
GOLD#_M1_202201030100_202608282357.csv
SHA256: 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
rows: 1,648,545
coverage: 2022-01-03 01:00 through 2026-08-28 23:57
```

Initial factual event families included:

- H1 Double-B confirmation;
- M5 SMA20 contact episode start;
- M5 BB20 upper contact episode start;
- M5 BB20 lower contact episode start.

The implementation enforced completed-bar visibility, prefix invariance and no-future checks before any economic claim.

## 3. Important representation correction: event-close-centered coordinates

A major user insight changed the scaling contract.

For each decision/event anchor:

```text
C0 = event/source candle close
price_level_centered = price_level - C0
```

Therefore the event close becomes zero.

The same `C0` is shared across all price-level channels and timeframes. This applies to:

- OHLC;
- moving averages;
- Bollinger levels;
- later price-level structure variables.

Magnitude or bounded variables are not shifted by `C0`:

- ATR;
- spread;
- range;
- RSI;
- Stochastic;
- volume/activity measures.

A synthetic constant-price translation audit (`+1234.5`) showed the centered input remained invariant to floating-point tolerance.

This removed absolute GOLD price era as a nuisance coordinate while preserving actual relative chart geometry.

## 4. Visual representation was tested, then de-scoped

V8 initially treated rasterized charts as a first-class representation hypothesis.

The first renderer used fixed multi-scale views after rejecting per-window autoscaling, because autoscaling could make a $5 range and a $50 range look geometrically identical.

The visual branch was then compared against exact numerical sequence geometry.

Key result:

- exact event-centered numerical geometry retained useful information;
- the first low-resolution raster representation lost information;
- larger neural/Transformer architectures did not solve the bottleneck.

The conclusion was not that charts are meaningless. It was that rasterization was not adding demonstrated incremental information over exact numerical sequences for the active task.

Visual input was therefore de-scoped from the active V8 base path. It can only be reopened by a controlled incremental-value test.

## 5. First future-path representation tournament

The initial V8 future-path dataset used 59,438 eligible event contexts from the open 2022-2026 development sample.

Early targets included MFE, MAE and terminal returns over 15m/60m/240m horizons. These were diagnostic, not trading policy authority.

The broad pattern was important:

- future excursion magnitude was learnable to a meaningful degree;
- future sign / terminal-return direction remained weak and unstable.

This was the first clue that GOLD historical context might contain much more information about `how much / how fast` than `which direction`.

## 6. Direction target redesigned to +/-10p first passage

The user proposed a more trading-like label:

```text
reference = event close C0
UP target   = C0 + 10.0
DOWN target = C0 - 10.0
```

The outcome asks which barrier is reached first.

Initial pilot census:

```text
UP_FIRST                 30,320
DOWN_FIRST               29,089
AMBIGUOUS_SAME_M1            29
```

If both barriers are reached inside the same M1 candle, order is unknowable and the case is excluded from binary direction training.

This was better than an arbitrary statement such as `60-minute close is above current close`, because a large favorable excursion followed by a late reversal should not be treated as if no directional opportunity existed.

## 7. Input contract expanded to full historical indicator sequences

A second major user correction was that a trader does not see only OHLC. The model should also receive the historical path of indicators during the same context window.

The V8 numerical sequence therefore included historical series such as:

- OHLC;
- SMA / EMA families used for diagnostics;
- Bollinger levels;
- RSI;
- Stochastic;
- MACD and histogram;
- ATR / true range;
- Bollinger width;
- tick activity / spread;
- selected level distances;
- indicator changes.

Indicators were representations only. No rule such as `RSI > 70 => SHORT` was supplied.

Adding historical indicator information improved the first 2024 direction diagnostic relative to OHLC-only, but the improvement did not remain strong enough in 2025/2026.

## 8. Preprocessing tournament: the problem was attacked directly

Because direction AUC remained near chance, V8 stopped adding isolated features and ran a preprocessing/learning tournament.

Key ablations included:

- barrier-unit scaling;
- level + multi-lag dynamics (`d1/d3/d6`);
- causal robust / instance normalization;
- fractional differentiation;
- overlap / sample-uniqueness weighting;
- self-supervised masked reconstruction;
- linear, LightGBM, temporal CNN and patch/Transformer families;
- competing-risk direction + time modeling.

Important methodological correction:

Training examples were purged not only by decision timestamp but also by label resolution timestamp. A late-December training event whose +/-10p outcome is resolved in January cannot be used to train a model evaluated on January data.

This removed a subtle future-boundary leakage mode.

## 9. What preprocessing did and did not solve

Multi-lag dynamics were more useful than simple level scaling alone.

However:

- robust/RevIN-style normalization did not create a strong direction edge;
- fractional differentiation did not help the GOLD 10p direction task;
- masked self-supervised reconstruction did not create the missing directional signal;
- larger neural/Transformer models were not materially better than simpler models;
- nearest-neighbor chart similarity did not produce stable direction;
- event-family-specific direction models did not remain stable;
- rolling retraining and online updates did not rescue direction;
- one-active/non-overlap populations did not rescue direction;
- simple meta-labeling of hand-specified primary sides did not rescue direction.

A representative competing-risk direction result after the 2024 selection step was approximately:

```text
2024 direction AUC  ~0.523
2025 direction AUC  ~0.510
2026 direction AUC  ~0.475
```

The model could improve hit-time estimates while direction still collapsed or inverted.

This was a critical falsification: `direction + time joint modeling` did not solve the direction problem.

## 10. Double-B follow-up chains were also falsified

V8 explicitly tested a more discretionary-looking causal chain:

```text
H1 Double-B
→ subsequent progress
→ adverse excursion
→ pullback from peak
→ elapsed time
→ first M5 MA/BB follow-up event
→ next +/-10p path
```

This did not produce stable directional predictability.

The result matters because it blocks a tempting rescue story: simply expressing `Double-B then pullback to MA` in more scalars was not enough to recover the human discretionary concept.

## 11. The decisive decomposition: movement intensity vs direction

The research then separated two questions:

```text
A. Will price move far enough soon?
B. Which direction will it move?
```

The contrast was large.

Direction remained near chance in many tests.

Near-term 10p barrier-crossing probability, however, was strongly learnable.

This led to a new active V8 branch:

> predict movement intensity / range expansion, not direction.

## 12. Important numerical correction during the movement audit

An interim conversational report overstated a movement AUC because results from different diagnostics were mixed.

That number was explicitly rejected as authority.

The movement study was recomputed from the frozen +/-10p event ledger using common definitions and chronological boundaries.

Authoritative FAST_30 event rates in the open-development event population were:

```text
2022   2.14%
2023   1.60%
2024   3.61%
2025  18.40%
2026  51.31%
```

This itself revealed a large movement-intensity regime shift across the development sample.

## 13. What actually predicts movement intensity

Ablation showed a much cleaner mechanism than the direction work.

Event identity alone was weak. Time-of-day helped, but it was not the main source.

The dominant information was:

- recent realized price variation;
- multi-horizon high-low ranges;
- absolute price-change activity;
- candle body / wick activity;
- tick activity / spread context;
- acceleration or compression between short and long horizons;
- time-of-day as supplementary context.

A structured HAR/range-style representation over M1 windows of roughly:

```text
5 / 15 / 30 / 60 / 120 / 240 / 480 / 1440 minutes
```

was much stronger than a broad generic indicator snapshot and much stronger than a full-sequence neural model trained to discover the same concept from scratch.

## 14. Best research movement-probability evidence

For the structured multi-horizon movement model, open-development ROC AUC was approximately:

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 0.883 | 0.861 | 0.800 |
| 30m | 0.868 | 0.844 | 0.789 |
| 60m | 0.838 | 0.831 | 0.784 |
| 120m | 0.805 | 0.818 | 0.809 |

For the 30m model, week-block bootstrap 95% AUC intervals were approximately:

```text
2024  0.843-0.893
2025  0.819-0.865
2026  0.756-0.821
```

The ranking evidence is therefore far from a marginal 0.5 result.

## 15. Human-filter relevance: score separation

The most important evidence for discretionary use was not AUC by itself but the realized movement rate inside score tails.

For 30m / 10p movement:

### 2024

```text
base rate              3.61%
bottom score decile    0.07%
top score decile      20.25%
top 5%                26.51%
top 1%                48.84%
```

### 2025

```text
base rate             18.40%
bottom score decile    1.12%
top score decile      62.65%
top 5%                67.78%
top 1%                73.02%
```

### 2026 YTD

```text
base rate             51.31%
bottom score decile   14.96%
top score decile      93.10%
top 5%                93.35%
top 1%                90.59%
```

This supports the intended human-assistance use case: filter factual chart events by whether the market is currently in a high or low near-term movement state, while leaving direction to the trader.

## 16. Why the active model is portable logistic rather than the research-best model

For MT5 deployment, V8 intentionally did not embed the most complex research model.

A 53-feature continuous-M5 logistic representation was trained using causal M1 range/volatility state and retained strong discrimination at the factual event timestamps.

Event-subset AUC for the portable model:

| Horizon | 2024 | 2025 | 2026 YTD |
|---|---:|---:|---:|
| 15m | 0.865 | 0.873 | 0.815 |
| 30m | 0.844 | 0.851 | 0.796 |
| 60m | 0.807 | 0.829 | 0.781 |

This was chosen because:

- it remains strongly discriminative;
- feature equations are explicit;
- coefficients can be embedded directly in MQL5;
- Python-to-MQL parity can be checked numerically;
- it needs no external Python inference server.

## 17. MT5 shadow indicator design

Current implementation artifact:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

Required chart:

`GOLD# M5`

The separate indicator window shows continuous completed-M5 probability lines:

```text
P(10p move within 15m)
P(10p move within 30m)
P(10p move within 60m)
```

The main chart marks factual events with configurable triangle colors:

- M5 SMA20 contact-start;
- M5 BB20 upper contact-start;
- M5 BB20 lower contact-start;
- H1 Double-B confirmation.

The probability lines are continuous rather than event-only, so a human can scroll backward and inspect whether movement probability was building or falling before an event.

The current forming M5 bar is deliberately blank to preserve completed-bar causality.

## 18. Historical display must remain walk-forward

Historical MT5 probabilities cannot use one final 2026 model across old history.

Current policy:

```text
2024 display <- model trained on 2022-2023
2025 display <- model trained on 2022-2024
2026 display <- model trained on 2022-2025
```

No pre-2024 probability is displayed by the current model pack.

Extrapolating beyond 2026 has no validation authority until the model is retrained and checked.

## 19. Python-to-MQL parity

Thirty sampled M5 decision timestamps spanning 2024-2026 were recomputed independently using the Python research equations and the embedded MQL equations.

Maximum observed differences:

```text
feature difference      2.22e-12
probability difference  5.39e-14
```

This validates the formula/coefficients translation to floating-point precision.

It does not replace actual MetaEditor compilation and broker-history runtime parity on the user's Windows/MT5 environment.

## 20. Current conceptual model

V8 now separates roles deliberately:

```text
OBJECTIVE EVENT
Double-B / MA / BB interaction
        ↓
MOVEMENT MODEL
How likely is a 10p move soon?
        ↓
HUMAN CHART ANALYSIS
LONG / SHORT / WAIT / SKIP
```

A movement probability is not:

- LONG probability;
- SHORT probability;
- liquidity probability;
- win-rate probability;
- automatic trade permission.

It is best interpreted as near-term movement-intensity / range-expansion / barrier-crossing probability.

## 21. Current strongest hypothesis

The current V8 evidence supports:

> GOLD endogenous historical data contains strong information about near-term movement intensity, but much weaker and unstable information about direction.

This is why further RSI/EMA/threshold mining is no longer the active research priority.

A future autonomous direction branch would require a materially new information source or a genuinely different formulation, not another round of indicator accumulation.

## 22. Immediate next study

After the user compiles and confirms runtime parity, begin prospective shadow logging.

For every supported event, record before outcome:

- event type and timestamp;
- 15m/30m/60m movement probabilities;
- movement-score percentile if added;
- human discretionary LONG/SHORT/WAIT/SKIP decision;
- actual trade entry if any;
- SL/TP and realized result if traded.

Primary downstream question:

> Does human directional/trade performance improve materially as movement probability increases?

This must be answered prospectively. Do not retrospectively choose only attractive chart examples or tune a probability threshold from the trader's remembered winners.

## 23. Untouched reserve

`GOLD# 2021` remains untouched.

Do not open it for movement-probability validation until the shadow indicator, preprocessing, model policy and evaluation claim are frozen at a claim-grade stage.
