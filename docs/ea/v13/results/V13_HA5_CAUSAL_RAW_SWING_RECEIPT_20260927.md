# V13 HA-5 causal raw-swing observation receipt

Date: `2026-09-27`
Status: `FIRST FIXED PROBE COMPLETE / DEVELOPMENT EVIDENCE / NO ACTION AUTHORITY`

## Scope and reproducibility

This is the first observation-only probe specified in
`../V13_HA5_CAUSAL_RAW_SWING_CONTRACT_20260927.md`. It does not change the
Standard-H4 Baseline-0 Journey, Child, exit or execution semantics. The sole
new information family is confirmed *actual traded-price* H4 swing levels,
not another HA representation or an imported strategy.

- Full canonical GOLD# decision window: `2024-01-01` through the last
  completed H4 decision before `2026-08-28 20:00` execution-open.
- Raw M1 streamed in time order from 2022 warm-up; 1,648,308 rows through
  cutoff reconstructed 7,198 H4 bars. Exported H4 OHLC parity: 0 mismatches.
- M1 SHA256: `fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250`.
  H4 SHA256: `b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf`.
- 4,108 matched decision-time rows; 4,105 with available future outcome labels
  across 964 Journeys. The final three decisions lack a complete label horizon.
  These counts are **not** Child-trade counts or MT5 P/L.
- Strict two-left/two-right H4 pivots become known only after their two right
  H4 bars complete. A bar is classified against pivots known *before that bar
  began*, then may confirm a new pivot for later bars. No level was missing in
  the 4,105 labeled decisions. Median confirmation age: favorable level 5 H4
  bars; adverse level 4 H4 bars.
- Decision features and future labels are separate local files under
  `output/v13_ha5_raw_swing_20260927/`. Reproduce with
  `research/v13/ha5_causal_raw_swing_audit.py` and the frozen HA-4C/D ledger.
  Generated ledgers are not Git authority.
- Four narrow state-classification regression tests passed; they check
  LONG/SHORT symmetry, strict touch handling and active-level changes. They
  are not evidence of trading edge or tick-level execution parity.

The latest confirmed high and low are independent levels, **not necessarily
one enclosing range**. The high was at/below the low in 43/4,105 decisions;
both boundaries were exceeded within 31 H4 bars. Do not invent intrabar order
from H4 OHLC or interpret this pair as a clean box. The M1 stream establishes
the H4 observations, not exact tick execution or spread.

## What raw structure added descriptively

`Progress` means beyond the last confirmed raw high for a LONG Journey and
beyond the last confirmed raw low for SHORT, mirrored exactly. The table uses
the current completed H4 bar and shows **future** outcomes only as labels.
Remaining favorable movement is measured from the next H4 open until the
Standard opposite-color exit, in units of the trailing 20-H4 median range.

| Favorable boundary state | Decisions | Next H4 opposite HA | Median remaining favorable range |
| --- | ---: | ---: | ---: |
| First close beyond confirmed level | 399 | 4.0% | 1.18 |
| Continued close beyond same level | 1,128 | 17.4% | 0.94 |
| No break | 2,125 | 27.3% | 0.68 |
| Intrabar probe, close rejected | 351 | 29.9% | 0.74 |
| Previous close beyond, current close returned inside | 102 | 64.7% | 0.41 |

Fresh raw-price progress usually accompanies HA persistence. A return inside
a previously crossed level often occurs late in a Journey, but is uncommon and
not a self-sufficient exit. Across the six year/side slices, fresh progress had
only 2.5%-5.9% next-H4 reversal, while return-inside had 50%-80%; some latter
cells contain only 5-27 decisions. These are consumed-sample descriptions,
not an independently validated forecasting rule.

## Does it clarify the H1 opposition warning?

At 1,395 decisions where the last completed H1 HA opposed the continuing H4
Journey, 660 actually reversed on the next H4, while 735 did not. The
predeclared favorable `probe_rejected OR return_inside` event occurred in 235
of those decisions:

| Last-H1-opposed subset | Decisions | Next H4 reversal | Reversal within 3 H4 | Median remaining favorable range |
| --- | ---: | ---: | ---: | ---: |
| Favorable rejection/return | 235 | 58.7% | 80.9% | 0.43 |
| Neither | 1,160 | 45.0% | 69.7% | 0.53 |

The pooled next-H4 difference is +13.7 percentage points. A Journey-cluster
resampling interval is +7.0 to +20.9 points; this interval describes sampling
dependence in *this same consumed period*, not out-of-sample validity. The
event catches only 138/660 actual next-H4 reversals (~21%). It also has
97/235 false next-H4 warnings. Within H4 body/raw-close tertile overlap,
the descriptive difference contracts to +9.8 points (1,395/1,395 rows);
adding H4 Delta contraction and wick state leaves +6.0 points on just
812/1,395 overlapping rows. With finer quintile cells and at least 20 on
each side there is **zero** overlap. The apparent increment beyond HA
morphology is therefore not established robustly.

Separately, `return_inside` within last-H1 opposition appears in 90 decisions
and precedes 60 next-H4 reversals, but 30 do not reverse; it is narrower than
the compound event and does not solve the false-warning problem. Closing
beyond the adverse swing appeared in only 43 last-H1-opposed decisions and
barely separated next-H4 reversals (48.8% versus 47.3%); there were no
comparable H4-geometry cells for that contrast.

## Counterexamples and tail protection

All 88 Journeys lasting at least ten Standard-H4 bars remain in scope. The
favorable rejection/return event occurred in 56 of them, across 95 decisions;
74 of those decisions did **not** reverse on the next H4. Of the 43 event
decisions also showing last-H1 opposition, 26 did not reverse on the next H4
and still had a median 1.05 trailing-H4 ranges of favorable movement left.
Treating this as an exit would repeat the HA-4 false-warning/tail-loss problem.

A different-looking pocket exists without any H1 opposition: adverse-level
closes appeared 75 times, with 18.7% next-H4 reversals against 7.4% for the
1,562 other decisions. A Journey-cluster descriptive interval for the +11.2
point gap is +2.8 to +20.1 points; H4 body/raw-close matching covers only
720/1,637 such decisions. **61/75 did not reverse next H4**, and only 5/75
had already passed their eventual Journey peak. This could reflect normal
intrajourney noise, not a discovered termination signal. No promotion.

## Interpretation and boundary

This fixed probe demonstrates a useful *description*: actual price can newly
clear, reject, or return inside a **causally known** swing while HA color
remains unchanged. Yet much of the reversal association shares information
with the completed H4 candle/HA morphology, and remaining overlap becomes
thin under tighter comparison. The study has not shown a reliable way to cut
repeated losses without sacrificing long Journey participation. Do not
back-fill a favorable threshold or convert any state, age, year or side into
an entry, exit, stop, sizing or ML label authority.

HA-5's first fixed observation probe is complete. The raw-structure branch
stops at description until a separately frozen, causally testable incremental
hypothesis has credible overlap and tail accounting. Roadmap HA-6 may be
considered as a *new, one-family-at-a-time* observation; it does not inherit
any HA-5 trading permission. The exact-window MT5 actual-tick economic
Baseline-0 receipt remains pending and is distinct from this study.
