# V13 Heikin-Ashi research roadmap

Date: `2026-09-26`
Status: `ACTIVE ORDER / ONE LAYER AT A TIME / NO NEW TRADE RULES YET`

## 1. Objective

The V13 baseline is intentionally simple enough to act as a laboratory for HA.
The research goal is not to rush toward a more complicated strategy. It is to
understand what standard HA contains, what information it loses through
smoothing, and which single complementary information source is worth adding.

The order below is authoritative unless a later V13 decision document replaces
it after evidence is consumed.

## 2. Common protocol for every stage

Every stage must:

- use causal completed-bar inputs only;
- preserve the Baseline-0 trade ledger unless the stage explicitly becomes an
  action experiment;
- use the full `2024-01-01 .. 2026-08-28` window for primary comparisons;
- show 2024/2025/2026 and LONG/SHORT slices only as diagnostics;
- preserve Journey grain and Child grain separately;
- keep large right-tail Journeys visible;
- separate decision features from future outcome labels;
- avoid converting exploratory quantiles or visually attractive thresholds into
  rules without a new frozen contract;
- document source provenance and exact formulas.

## Stage HA-0 — Standard-HA measurement ledger

### Change from Baseline 0

`NONE` to trading behavior.

### Build

For every completed H4 bar and every Child decision, record:

```text
raw OHLC
standard HA OHLC
HA color
HA Delta and absolute Delta
HA body / range / body-to-range
upper and lower wick length / ratio
directional wick / opposite wick
no-opposite-wick flag
same-color streak
Delta change / body change
raw body/range
raw close displacement from HA close/open
Journey ID / Child number
```

Future outcomes live in separate columns/table:

```text
bars and hours to next opposite HA color
final Journey length
future MFE / MAE until Journey end
raw-price favorable extreme and timestamp
giveback from favorable extreme to HA exit
Child terminal PnL
Journey terminal PnL
```

### Questions

- What does a typical HA Journey look like from birth to death?
- Which HA measurements evolve smoothly with Journey age and which do not?
- How large is raw-price turning-point -> HA-color-flip lag?
- How much profit is commonly given back between raw favorable extreme and HA
  exit?

### Output

A descriptive receipt only. No strategy change.

---

## Stage HA-1 — HA morphology and persistence

### Inputs

Only fields produced in HA-0.

### Study

- Delta magnitude and sign;
- body/range strength;
- no-opposite-wick continuation state;
- first reappearance of opposite wick;
- small-body/two-sided-wick state;
- same-color streak;
- body and Delta expansion/contraction.

### Methods

Prefer continuous curves, empirical distributions, transition matrices and
rank/quantile diagnostics over arbitrary hard thresholds.

Quantiles are descriptive bins, not trade gates.

### Questions

- Does no-opposite-wick state actually correspond to longer persistence on GOLD#?
- Does opposite-wick emergence precede color change often enough to matter?
- Does Delta/body contraction contain transition information before color flips?
- Are the relationships stable across years and sides?

### Gate

Do not create an entry/exit rule yet.

---

## Stage HA-2 — Lifecycle, lag and giveback anatomy

### Goal

Map HA's smoothing benefit and lag cost directly.

### Study

For each Journey:

1. HA color-flip start;
2. expansion phase;
3. maximum raw favorable excursion;
4. contraction / opposite-wick emergence;
5. raw-price turn;
6. eventual opposite HA color;
7. realized giveback to HA exit.

Estimate descriptive transition/survival quantities such as:

- probability same color survives another 1/2/3 bars conditioned on current HA
  morphology;
- empirical time-to-flip curves;
- distribution of remaining favorable excursion;
- distribution of giveback conditional on HA state.

These are research outcomes, not probabilities authorized for trading.

### Gate

At the end of HA-2, decide whether the first action problem is primarily:

- participation timing;
- late-Journey funding;
- exit timing;
- or none of the above.

Do not decide this before the lifecycle audit.

---

## Stage HA-3 — Standard versus smoothed HA representations

### Source family

MQL5 smoothed HA / ExMachina / iHeikenAshiSm.

### Order

1. standard HA control;
2. one clearly specified pre-smoothed-price HA implementation;
3. one clearly specified post-HA smoothing implementation;
4. only later consider DEMA/SMMA/LWMA/step variants if the first comparison shows
   a mechanism worth pursuing.

### Do not

- launch a large period/method optimization grid;
- choose the best period after seeing P/L;
- mix smoothing with a new entry/exit rule in the same experiment.

### Measure first

- color-change frequency;
- lag from raw favorable extreme to color transition;
- short-run/chop frequency;
- Journey-length distribution;
- retained/given-back excursion;
- how much distinct information the variant adds versus merely increasing lag.

---

## Stage HA-4 — Multi-timeframe standard HA

### Why

MTF uses the same standard representation on another time scale rather than
changing HA mathematics.

### Sequence

1. `D1 standard HA` as broader state alongside H4 baseline;
2. `H1 standard HA` as faster transition observation around H4 Journey changes.

Each is observation-only first and is tested separately.

### Questions

- Does H4 morphology mean something different when D1 HA is persistent versus
  transitional?
- Does H1 HA reveal a raw transition before H4 color changes without becoming
  pure lower-timeframe noise?

No forced alignment rule is pre-authorized.

---

## Stage HA-5 — Raw-price structure complement

### First candidate

Fractal / causal swing structure, inspired by the 2025 MQL5 HA + Fractal system.

### Rationale

HA is synthetic. Raw price structure may contribute information that HA cannot:
actual swing highs/lows, breakout/failed-break geometry and location relative to
real traded prices.

### Research order

1. observation-only relation between HA state and confirmed raw swings;
2. measure whether structure adds incremental information to HA-2 lifecycle
   diagnostics;
3. only then consider a one-rule action contract.

Fractals must respect their confirmation delay. No future-centered swing may be
used before it is causally confirmed.

---

## Stage HA-6 — Single complementary indicator families

Test **one family at a time**, only if it adds information not already captured
by HA morphology and raw structure.

### HA-6A — HASTOC / HA-derived momentum

Reason: it is explicitly designed to combine HA trend and momentum and has
published empirical research. Reproduce the formula before judging it.

### HA-6B — Moving-average context

Reason: MA level/slope may provide a raw-price directional reference distinct
from HA morphology. Start with one named implementation/contract, not a period
optimizer.

### HA-6C — ATR as normalization, not signal

Reason: compare body, wick, displacement and excursion across changing Gold
volatility regimes. ATR initially normalizes measurements and has no entry veto.

### HA-6D — ADX / SuperTrend

Reason: test whether an independent trend-strength/volatility construction adds
anything after HA + ATR normalization. Be alert to redundant trend lag.

### HA-6E — volume / tick-volume participation

Reason: HA is price-derived and contains no participation dimension. Verify
broker GOLD# tick-volume semantics before using it.

### Rule

Do not bundle these families. `HA + EMA + ADX + ATR + RSI` is not one experiment.

---

## Stage HA-7 — First action experiment

Only after HA-0..HA-6 identify a repeatable mechanism may V13 change trading
behavior.

A valid first action contract changes **one** of:

- Child admission;
- additional-Child funding;
- Journey exit;
- risk/SL;
- sizing.

Do not change two categories at once.

The experiment must specify:

```text
mechanism
causal trigger
what Baseline-0 action changes
what stays identical
full-window comparator
right-tail preservation checks
execution requirements
```

A visually obvious example or an in-sample optimum is insufficient.

---

## Stage HA-8 — Machine learning as a HA-state model

ML is allowed only after the representation work above is complete enough to
state a meaningful target.

### 8.1 Baselines first

Start with:

1. constant/base-rate predictor;
2. logistic or other regularized linear model;
3. shallow tree / Random Forest;
4. XGBoost or CatBoost only if warranted.

Only after tabular baselines are understood consider LSTM, TCN, RNN or
Transformer-style sequence models.

### 8.2 Preferred targets

Avoid “predict LONG/SHORT next bar” as the default objective.

Prefer lifecycle targets such as:

```text
P(same HA color survives next k bars)
P(opposite HA color within k bars)
remaining favorable excursion before flip
giveback risk after current state
time to opposite-color confirmation
conditional future MFE/MAE
```

These future quantities are labels only. Decision features must be frozen first.

### 8.3 Validation

Because 2024-2026 is consumed V13 development history:

- use chronological walk-forward/out-of-fold predictions for development
  diagnostics;
- never report in-sample model predictions as strategy performance;
- preserve year/side/Journey/tail diagnostics;
- future untouched data is still required for strong promotion claims.

### 8.4 MT5 deployment

If a model ever affects MT5 action:

- freeze preprocessing exactly;
- export via ONNX when appropriate;
- reproduce normalization/transforms/features in MQL5;
- pass Python/MQL5 feature-vector and output parity;
- then run actual-tick tester economics.

---

## 3. Stop conditions

A research branch should stop when:

- it adds no stable information beyond prior stages;
- its apparent benefit is concentrated in a tiny number of already-known tail
  Journeys with no causal selector;
- it requires post-hoc thresholds to look useful;
- its formula cannot be reproduced consistently;
- its improvement disappears under the full comparison window;
- complexity grows faster than explanatory value.

Stopping a branch is a successful V13 result.

## 4. Current next step

`HA-5 Causally confirmed raw-price structure complement`

HA-0..HA-4 descriptive receipts and the HA-3/HA-4 observation contracts are
under `results/` and the V13 root respectively. No EA strategy modification is
authorized by any of them. HA-5 begins observation-only.
