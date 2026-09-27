# V13 X2 — same-broker EURUSD# H4 observation contract

Date: `2026-09-28`
Status: `FROZEN BEFORE X2 OUTCOME EVALUATION / OBSERVATION ONLY`
GitHub main checked: `be88fa2be516963b2dcd196819f9b2fd026b077a`

## Question

Does the independently traded `EURUSD#` H4 price path on the **same XM MT5
broker feed** add economic-Journey-loss separation at the birth of a standard
HA H4 GOLD# Journey, beyond gold H4 morphology plus ordered gold H1 state?
As in X1, repeated losing Journeys and large winning Journeys must both be
audited. EURUSD# is a bilateral dollar proxy, **not** DXY or a broad dollar
index. No fixed inverse gold/dollar sign rule is assumed.

This is a separate follow-on to X1. X1's negative delayed-daily result neither
preselects nor invalidates this genuine H4 test. Baseline 0 and EA remain
unchanged. No Child veto, exit, size rule, live signal or MT5 trading variant
is authorized.

## Source and as-of contract

- Export 2022-01-01 through 2026-08-28 available H4 bars for `EURUSD#` and
  `GOLD#` using the installed XM MetaTrader 5 terminal's Python
  `copy_rates_range`, with timezone-aware UTC request boundaries.
- Before using FX data, compare **every** returned GOLD# H4 timestamp and
  OHLC against the repository's frozen raw GOLD# H4 file through the cutoff.
  Stop on any mismatch; this proves the API series is clock/price compatible
  with the V13 gold source, not that broker quotes are universal.
- Require an `EURUSD#` H4 bar at the **same opening timestamp** as each GOLD#
  H4 decision signal bar. At the gold `known_at` first executable print after
  the signal bar closes, both completed H4 bars are available. If any exact
  match is absent, stop rather than forward-fill or infer a cross-market bar.
- Save the raw FX export, source SHA-256, parity counts, duplicate/missing
  checks and feature SHA-256. The feature builder streams FX bars in order and
  never uses an FX bar timestamp later than its gold decision signal.
- MetaQuotes timestamp/history semantics:
  https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py

## Frozen features

At each GOLD# HA decision, define `usd_level = -log(EURUSD# close)` for the
same completed H4 signal bar. Exactly three numeric columns represent this
one external family:

1. one-H4 `usd_level` change divided by the median absolute one-H4 change
   from the 20 preceding EURUSD# H4 bars;
2. three-H4 `usd_level` change divided by the median absolute three-H4 change
   from the 20 preceding EURUSD# H4 bars;
3. interaction of feature 2 with the GOLD# Journey side (`+1` LONG, `-1`
   SHORT). This tests incremental *alignment* without hard-coding its sign.

The current bar is excluded from every normalization denominator. No extra
lookback, threshold, directional veto, session feature, event feature, lag
optimization, hidden indicator, or model-family search.

## Target and fixed evaluation

- Primary target: complete Baseline-0 Journey Child-sum `net_points < 0`, at
  Child #1 decision. Previous Journey outcome is used only for the repeated-
  loss diagnostic. Same idealized next-H4-open economic ledger as HA-8A/X1.
- Reuse X1's four chronological OOF blocks, purging every training Journey
  whose exit was unknown at the test block's first decision.
- Compare constant training-fold loss rate, fixed H4 morphology + ordered H1
  regularized logistic model, then `+ FX one-/three-H4 changes`, then `+ FX
  side interaction`. Fixed L2 penalty and train-fold-only preprocessing are
  inherited from HA-8A. No random split or tuning.
- Report Brier, log loss, AUC, calibration by block and pooled; year/side
  diagnostics; same fixed **descriptive only** highest predicted-loss 20%
  Journey group with loss/win counts, repeat-loss capture, gross/net points,
  >=10-bar winners and bucket membership changes versus H4/H1.

## Interpretation

This full 2024-01-01..2026-08-28 period is consumed development evidence.
If the FX additions are small/unstable or damage continuation winners, stop
this family rather than tuning it. Even a positive result needs a later
action contract, untouched future validation, exact-window actual-tick MT5
economics, and Python/MQL5 feature parity before economic promotion.
