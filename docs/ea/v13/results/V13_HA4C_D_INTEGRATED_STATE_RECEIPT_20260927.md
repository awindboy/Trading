# V13 HA-4C/D integrated HA-state observation

Date: `2026-09-27`
Status: `DESCRIPTIVE DEVELOPMENT EVIDENCE / NO ACTION AUTHORITY`

Contracts: `../V13_HA4C_INTEGRATED_STATE_CONTRACT_20260927.md` and
`../V13_HA4D_EMA_MORPHOLOGY_CONTRACT_20260927.md`.
Source: `research/v13/ha4_mtf_audit.py` and
`research/v13/ha_integrated_state_audit.py`. Local separated ledgers and full
summary: `output/v13_ha4c_integrated_20260927/` (not in Git).

## Why this was necessary

HA-1 found useful body/Delta/wick information, yet HA-2 condensed lifecycle
mainly to final aggregate lag/giveback; HA-3 and HA-4 then emphasized colors,
representation-defined Journeys and D1/H1 color alignment. Those were valid
*narrow* observations, not a complete test of HA's state information. HA-4C/D
join all representations to the **same** Standard-H4 Journey and completed-H4
decision timestamp. They do not relabel hindsight entries or alter Baseline 0.

## Source and grain checks

The H1 and D1 context was regenerated from chronological raw M1, not from a
future-loaded higher-timeframe dataframe. The source hashes matched the prior
HA-0/HA-4 receipts. M1 reconstruction checked 7,198 H4, 27,518 H1 and
1,201 D1 bars against exports, with zero OHLC mismatches. The baseline retained
965 closed Journeys and 3,858 closed-Child decisions. Of 4,108 active H4
decisions, 4,105 have the predefined in-window future horizon (964 distinct
closed Journeys in that outcome subset). Each representation was joined by
signal time, Standard Journey, side and H4 morphology; future labels were
kept in a separate file.

For remaining favorable excursion, use the future raw H4 high/low between the
decision's next-H4-open and the Standard Journey's opposite-color exit, divided
by the median range of the last 20 *completed* raw H4 bars, including the
current signal bar. The first 19 evaluation decisions lack that local
normalizer. This is a retrospective measurement, not an entry/exit distance.

## Ordered H1 states: color alone discarded information

At each completed H4 decision, classify the completed H1 states *inside that
H4*, relative to the active Standard-H4 Journey:

| H1 path | H4 decisions | Next H4 flip | Flip within 3 H4 | Final raw peak already past* | Median remaining favorable excursion (H4 ranges) |
|---|---:|---:|---:|---:|---:|
| Never opposed | 1,637 | 7.9% | 45.1% | 14.7% | 1.03 |
| Opposed, then repaired by final H1 | 1,073 | 16.1% | 54.1% | 23.5% | 0.86 |
| Opposed at end, mixed path | 1,176 | 46.6% | 71.6% | 53.1% | 0.49 |
| Opposed throughout observed H1 sequence | 219 | 51.1% | 71.2% | 63.0% | 0.58 |

*Final-peak-already-past is defined using future M1 observations and was not
known at the decision. A H1 path's apparent risk contrast is an association,
not an exit rule. Most H1-opposed states still have another H4 bar without a
color flip: 735 of 1,395; 397 have no flip within three H4 bars.

Among continuing (non-birth) Standard Journeys, the four next-flip rates are
6.1%, 15.8%, 46.7%, and 51.6% in the same order. Across 2024/2025/2026 and
both sides, last-H1 opposition retains a pooled next-flip association. Yet
the H1-repaired versus never-opposed next-flip difference shrinks from +8.2
percentage points pooled to about +2.9 points in comparable Standard-H4
body/range and raw-close tertile cells. That is a descriptive overlap check,
not an independent effect estimate.

The last-H1 opposed/agree difference is +36.1 points pooled. Within H4
body/range and raw-close **tertile** overlap cells it is +13.1 points over
2,737/4,105 decisions. With finer **quintile** overlap cells (at least 20 per
group) it is +4.4 points over only 1,627/4,105 decisions. Adding H4 Delta
contraction and opposite-wick state to the coarse cells gives +12.4 points
over 2,720/4,105. The difference depends on coarsening and limited overlap;
neither "H1 adds no information" nor "H1 adds an independent 36-point
signal" is established.

## Same-Journey FAST, D1 and EMA morphology

- FAST-R25 opposed Standard H4 on 386 decisions, with 52.3% next-H4 flip
  versus 20.5% otherwise. But **375 of those 386** also had Standard-H4 Delta
  contraction: FAST opposition is largely coupled to already visible H4
  weakening. Its within-H4-body/raw-close-tertile next-flip contrast was
  +5.2 points over 2,631/4,105 comparable decisions, not the pooled +31.9.
- D1 opposition remained weak for the next-H4 outcome: 24.3% versus 22.8%;
  within the H4 geometry tertiles, about -0.1 points over all 4,105 decisions.
  D1 Delta contraction alone was 24.2% versus 22.7%. A three-bar D1
  association is still descriptive and does not grant a direction veto.
- PRE-EMA2 and POST-EMA2 Open, Close, color and Delta-contraction chronology
  matched under the defined formulas, but opposite-wick **presence differed
  on 518 of 4,105 decisions**. This confirms that color equivalence does not
  imply morphology equivalence: PRE smooths raw highs/lows before HA, while
  POST retains raw highs/lows around smoothed HA Open/Close.
- POST-EMA2 opposite-wick *reappearance* occurred on 413 continuing-Journey
  decisions. Next-H4 flip was 46.0% versus 21.5% on the 2,728 continuing
  decisions without it. Within comparable H4 body/raw-close tertile cells,
  however, the difference was only +3.3 points with overlap on 1,454 of
  3,141 continuation decisions. PRE reappearance occurred on 339 decisions;
  its next-flip rate was 44.5%. These are plausible morphology descriptions,
  not evidence that one EMA representation warrants an exit.

## The large-Journey cost remains decisive

All 88 Standard Journeys lasting >=10 H4 bars had at least one last-H1
opposition. Their 318 opposed-H1 decisions included **254 without a next-H4
flip**, and the median *remaining* favorable raw-price excursion after such
decisions was 2.17 trailing-H4 ranges. Blanket H1 opposition exit would
therefore cut many still-productive Journeys. FAST opposition occurred in 65
of the 88 long Journeys; POST-EMA2 wick reappearance in 79, with 111 of 139
tail warnings lacking a next-H4 flip. These counts are not simulated P/L.

## Interpretation and next gate

The useful observation is **temporal state**, especially H1 opposition that
repairs before H4 completion versus opposition that persists. However much
of the pooled association is entangled with the known Standard-H4 body,
Delta, wick and raw-close geometry, and the apparent residual varies with
which comparable cells are retained. PRE/POST EMA wick shapes are not
interchangeable despite identical colors. D1 showed little distinct next-H4
separation here.

This fills the specific HA-1-to-HA-4 continuity gap, not the whole action
question. It changes no trade, filter, ML model, sizing, SL or EA. The entire
window is consumed development history, and overlapping H4 decisions are
dependent. Future work may now proceed to HA-5 observation, but no H1/FAST/
EMA warning is promoted until a separate, frozen action contract accounts
for false warnings, Journey-level returns and tail preservation in MT5 actual
ticks and later untouched validation.
