# V8-003 — Preprocessing / Label-Learning Tournament Contract

Date: 2026-08-31
Status: FROZEN BEFORE V8-003 RESULTS
Production authority: NONE

## Fixed prediction target

For each existing factual anchor, `C0 = event/source candle close`.
The realized direction label is whichever price is hit first after the decision:

- UP: `C0 + 10.0` GOLD price units
- DOWN: `C0 - 10.0` GOLD price units

If both are first reachable inside the same M1 bar, exclude the sample as intrabar-order ambiguous.
The barrier size is not tuned in this tournament.

## Strict chronological splits and purging

- A: train <= 2023, evaluate 2024
- B: train <= 2024, evaluate 2025
- C: train <= 2025, evaluate 2026 YTD

A training event is removed if its label end time is at/after the evaluation start. Internal validation uses the
same purge rule at the validation start. Thus no training label may consume price action from the next fold.

## Base representation

Exact numerical histories only; visual/raster input is de-scoped.

- H1: 96 completed bars
- M15: 128
- M5: 144
- M1: 180

Raw OHLC plus the previously cached indicator histories are supplied. Human semantic labels such as
TREND/RANGE/BREAKOUT/TURNING are forbidden.

## P1 — barrier-unit semantic scaling

All price levels: `(x - C0) / 10`.
Price magnitudes (ATR, TR, BB width, MACD price units, price distances, price-level changes): `/10`.
Spread: convert MT5 points to price with point=0.01, then `/10`.
RSI/Stochastic: center 50 and divide 50. Tick volume uses log/activity representations.

## P2 — levels + dynamics

P1 plus causal multi-lag changes at lags 3 and 6 for a frozen subset of price, indicator, volatility and activity
channels. Existing 1-bar changes remain present.

## P3 — dual raw + causal robust instance representation

P2 plus a second copy of selected channels normalized *inside each historical input window* using median and
MAD. Raw barrier-centered geometry remains present. This is causal and does not use future/global statistics.

## P4 — memory-preserving fractional-difference channel

P3 plus fixed-width fractional-difference channels for selected price-level series.
The order is chosen outcome-blind on 2022-2023 M5 close by the smallest grid value satisfying ADF p<0.05 and
correlation with level >0.95 using a finite-width threshold 1e-3. The resulting preregistered order is `d=0.2`.
No P/L/label metric enters this choice.

## P5 — overlap-aware training

Use the best preprocessing from A, unchanged, but weight training samples by average label uniqueness over
`[decision_time, first_hit_time]`. This prevents one long move from receiving repeated full weight through many
overlapping anchors.

## P6 — self-supervised pretraining

Use the best P1-P5 representation. Pretrain the temporal encoders on unlabeled historical windows from the
training allocation only with masked-sequence reconstruction. Set each unlabeled window's own final completed
close as its origin. Then fine-tune on the same 10p labels.

No evaluation-year unlabeled data enters pretraining.

## Discrete competing-risk head

After the best preprocessing is selected, compare ordinary binary direction BCE against a discrete
first-hit-time competing-risk head. Time bins are frozen outcome-blind:

`<=30, <=60, <=120, <=240, <=480, <=960, <=1920, >1920 minutes`.

The head predicts 16 classes = 2 directions x 8 time bins. Direction probability is the sum of its 8
cause-specific probabilities.

## Model-family diagnostic

On the selected preprocessing, compare:

1. logistic regression on causal sequence summaries;
2. LightGBM on the same summaries;
3. compact full-sequence temporal CNN;
4. compact time-patch Transformer (PatchTST-inspired diagnostic).

Only 2024 is used for model/preprocessing selection. 2025/2026 are sequential diagnostics of the frozen choice.

## Metrics

Information:
- ROC AUC
- balanced accuracy
- Brier score / log loss
- weekly block-bootstrap AUC interval

Decision-tail diagnostics:
- accuracy among top 1%, 5%, 10%, 20% absolute-confidence events
- events per active market day
- first-hit time distribution in selected tails

These are not final strategy metrics. No P/L/SL/TP/campaign promotion occurs in V8-003.
