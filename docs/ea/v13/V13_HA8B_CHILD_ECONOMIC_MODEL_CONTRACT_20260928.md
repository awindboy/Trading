# V13 HA-8B — Child marginal-economics model contract

Date: `2026-09-28`
Status: `FROZEN BEFORE HA-8B OUTCOME/MODEL RUN / DEVELOPMENT OBSERVATION ONLY`
GitHub main checked: `29e0073e57553d8fe1fd14b843daf09164a7a248`

## Question

At an unchanged Baseline-0 Child opportunity, can causally known HA/H1 and
position-history state distinguish **the marginal Child's** eventual loss
frequency and magnitude from its possible right-tail win? This is deliberately
different from HA-8A's three-H4 color-flip label and X1/X2's one-time
whole-Journey-loss label. The model may not change entry, exit, size, or the EA.

## Frozen population and economics

- GOLD# standard-H4 HA Baseline 0, full canonical 2024-01-01 through
  2026-08-28 available history; 2022 is warm-up only.
- One opportunity at each original Journey bar 1..10; later bars create no
  Child. Entry is the existing idealized next raw-H4 open at `known_at`, exit
  is the next Journey's first executable raw-H4 open. Open terminal Journeys
  have no terminal label and are excluded.
- Target `y = side * (exit - entry) / scale20`, where `scale20` is the median
  raw H4 range of the **previous 20 completed bars** at the signal. This is a
  fixed decision-time coordinate. Retain unnormalized price points for economic
  accounting. No Hard SL, TP, R multiple, or future MFE label is introduced.
- Baseline parity must reproduce 965 closed Journeys, 3,858 Children and
  +8,147.11 idealized GOLD price points (rounding tolerance 0.02); otherwise
  no modeling/economic interpretation.

## Causal feature construction

Run `--build-features` and hash/save its ledger **before** `--evaluate` reads
future outcome labels. Stream the already-validated HA-8A decision-feature
ledger in time order together with raw H4 solely to build the prior-20 range
scale. At a Journey flip, the previous Journey's close price is known at the
same first executable print. Only then update prior-Journey results.

Three predeclared nested information sets:

1. `H4_H1`: Journey side/age, standard-H4 body, raw-close location,
   Delta contraction, opposite wick/reappearance, ordered H1 opposition path
   and trailing opposition count.
2. `+position_history`: above plus current existing Children's mean unrealized
   PnL in current `scale20` units, most recently closed Journey's mean Child
   PnL in current `scale20` units, and log(1+consecutive losing Journeys).
   These use prices known by the current decision. Birth has zero open-Child
   PnL; no previous Journey is marked separately.
3. `+measured_context`: above plus already audited HASTOC10, log same-slot
   relative tick activity and its persistent-H1 interaction, causal raw-swing
   state/distances, and EMA50 slope/position state. No X1/X2 dollar proxy,
   FAST HA, new indicator, time/session feature, or fitted cutoff enters.

Model inputs are an explicit whitelist. `execution_raw_open` is permitted only
to calculate known position state and the separate outcome ledger; absolute
price, `year`, `journey` ID, future labels and terminal Journey length cannot
enter a model. Numeric imputation/standardization and categorical encodings
are fitted in the training fold only.

## Frozen model ladder

The economic model is a three-head hurdle, not a binary profit oracle:

`P(loss)`, `E[positive y | y>0]`, `E[-y | y<0]`.

Its estimated marginal value is `(1-P(loss))*positive_mean -
P(loss)*negative_mean`. Flat outcomes remain zero-valued and are reported.
Compare a stage-aware training-fold historical-mean reference (`Child #1`
versus add-on) with each nested information set under two fixed families:

- regularized linear: logistic loss head (`C=1`), ridge conditional magnitude
  heads (`alpha=20`), nonnegative output clipping;
- shallow nonlinear: histogram gradient boosting, at most 7 leaves, 100
  iterations, learning rate 0.05, minimum 60 rows per leaf, L2 10, no early
  stopping or hyperparameter search, separately for all three heads.

As a **diagnostic guardrail only**, fit a fourth binary head for eventual
`Journey length >=10` with the full feature set in each family. It does not
modify the marginal-value estimate or grant a trading veto.

## Chronological evaluation and interpretation

- Four expanding test blocks: 2024-H2, 2025-H1, 2025-H2, 2026 to cutoff.
  At each block, train only on Journeys whose opposite-color exit was actually
  known **before** the first test decision. No random split or in-sample
  trading score. Group/diagnose by Journey because multiple Child outcomes
  share one exit.
- Report loss Brier/log-loss/AUC, normalized marginal-value MAE/RMSE/bias,
  and stage-aware reference. Show pooled and fold results, 2024/25/26 and
  LONG/SHORT, Child #1 versus add-ons, and repeat-loss Journey diagnostics.
- Predeclare equal-count score quintiles **for description only** at Child #1
  and add-ons separately. For the lowest estimated-value 20%, report losing,
  winning and flat Child counts, gross loss/win/net price points, share of
  total losses captured, and false warnings inside >=10-bar Journeys and the
  largest winning Journeys. This rank bucket uses the whole OOF distribution
  and is **not** a time-causal executable threshold or a variant P/L.
- Do not select the best model/feature set by consumed-sample P/L, tune the
  bucket edge, or call 2024-2026 independent validation. A failure of these
  frozen families does not establish that all ML is useless.
- Exact-window real-tick Baseline-0 receipt, a later frozen **action**
  contract, Python/MQL5 input/output parity and untouched future validation
  are required before any EA or strategy promotion. MQL5 ONNX is an eventual
  deployment mechanism, not evidence of edge.
