# V13 HA-8A combination model contract

Date: `2026-09-28`
Status: `FROZEN BEFORE THIS RUN'S MODEL/ECONOMIC MEASUREMENT / OBSERVATION ONLY`
GitHub main checked: `53457bf5a38b0da0b77da094b6ea0223bc238fab`
Market/window: GOLD#, 2024-01-01 through 2026-08-28 available history.

## Question and boundary

Can measured standard-H4 HA state, ordered H1 opposition, broker tick
participation, causal raw-price swing response, and slower EMA50 context jointly
distinguish an actual Journey transition from temporary weakness? In
particular, does H1 opposition with unusual same-slot activity still warn when
raw price fails to establish favorable progress? This is **not** a Child veto,
exit, size, SL, strategy backtest, or production model. Baseline 0 and its EA
remain unchanged. The entire sample is already consumed V13 development data.

## Inputs and timing

- Use existing HA-4C and HA-5 decision-feature ledgers, keyed one-to-one by
  `(signal, journey)`. Their future labels are loaded only after the new
  feature ledger has been built and saved.
- Stream raw H4 in chronological order from pre-2024 warm-up through the frozen
  cutoff. For each completed bar construct standard HA, journey-oriented
  HASTOC10, raw-close EMA50, and relative tick volume using only the *previous*
  20 completed H4 bars in the same start-hour slot. The current completed
  H4 tick count is the numerator. Full future history is not loaded into the
  feature builder. `known_at` is the first executable print in the following
  H4 bar, which may be later than that bar's nominal timestamp. The next raw
  H4 open supplies the idealized execution price; no unfinished H4 is used.
- HASTOC10 follows the previously verified HA-6A formula. EMA50 uses the
  raw-close SMA50 seed and EMA recurrence from HA-6B1. Tick activity is
  feed-specific and follows HA-6E; it is not exchange volume.
- Source/file hashes, coverage, missingness and structural Baseline-0 Child
  parity must be recorded. If parity fails, economic interpretation stops.

## Fixed target and model ladder

The sole fit target is `flip_within_3`: an opposite standard-H4 HA color among
the next three completed H4 bars. Other future labels are descriptive only.

1. `constant`: training-fold event rate.
2. `H1_only`: ordered H1 path and trailing opposition count.
3. `HASTOC_only`: journey-oriented HASTOC10.
4. `H4_H1`: side, Journey age, H4 body ratio, raw-close position, Delta
   contraction, opposite wick/reappearance, ordered H1 path/count.
5. `plus_HASTOC`: model 4 plus HASTOC10.
6. `plus_activity`: model 5 plus log same-slot relative H4 tick volume and its
   interaction with persistent H1 opposition. Whole-H4 and H1-local activity
   are not counted as independent votes.
7. `plus_raw_swing`: model 6 plus the existing HA-5 favorable/adverse swing
   states and their close-to-level distances in trailing-H4-range units.
   This is the effort-versus-result combination under examination.
8. `plus_EMA50`: model 7 plus Journey-aligned/opposed EMA50 slope and position
   states. EMA is slower context, not a direction veto.

Every nonconstant model is an L2-regularized logistic regression with fixed
penalty 1.0 in summed-log-likelihood units; no hyperparameter search. Numeric
imputation and standardization use training rows only. Categorical vocabularies
are predefined from feature semantics. No random split, tree, boost, sequence
model, automated threshold search, or feature selection follows this run.

## Chronological evaluation

Expanding training windows: initial 2024-H1, then four test blocks beginning
2024-07-01, 2025-01-01, 2025-07-01 and 2026-01-01. Train rows whose three-H4
future label would not have been known before the first test decision are
purged (H4 signal index + 4). The final test block ends at the frozen cutoff.
2024-H1 has no prior training block and is **not** out-of-fold evidence.

Report per-block and pooled Brier score, log loss, ROC AUC and calibration,
alongside event base rates. Decompose by year, side and Journey age. Compare
the predeclared model ladder without choosing an in-sample winner. Full-window
Baseline-0 structural P/L is reconstructed as a parity check only, not an
official MT5 economic receipt.

For payoff/tail diagnosis, describe the highest predicted-risk 20% of OOF
eligible add-on Children (`journey_bar` 2..10) for each relevant model:
losses, winners, gross winning/losing points, net points and >=10-bar Journey
representation. This is a descriptive rank bucket, **never** a trading
threshold or simulated veto. An apparent flip prediction gain is not useful
if the group still contains outsized continuation winners. Also inspect
flip-within-3 false alarms inside >=10-bar Journeys.

## Interpretation

No component receives action authority from a model score or from this
consumed-period OOF result. If incremental calibration/discrimination is small,
unstable across blocks, or accompanied by tail damage, stop this combination
without adding complexity. A later action proposal requires a separately
frozen contract, untouched future validation, and the exact-window real-tick
MT5 economic receipt required by V13 authority.
