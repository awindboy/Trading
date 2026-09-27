# V13 HA-6A HASTOC observation receipt

Date: `2026-09-27`
Status: `FIRST FIXED PROBE COMPLETE / DEVELOPMENT EVIDENCE / NO ACTION AUTHORITY`

## Reproducibility and parity

The fixed source-paper formula was audited before using GOLD# outcomes. With
`D = HA_OPEN - HA_CLOSE` and a rolling ten completed-H4-bar min/max including
the current bar, the paper sample reproduces `100.000, 97.725, 86.938`.

The local audit preserves the frozen Baseline-0 structure:

- 4,108 decision-time feature rows;
- 4,105 rows with the existing complete outcome horizon;
- 966 started Journeys, 965 closed before the final open Journey;
- 3,858 successful Children in the 965 closed Journeys.

Its comparison-state parity also matches consumed HA-4C/HA-5 evidence:

- H1 `no_opposition`: 1,637 decisions;
- H1 `repaired`: 1,073;
- ending H1 opposition: 1,395 (`219 persistent + 1,176 unrepaired_mixed`);
- among those 1,395, HA-5 favorable rejection/return: 235 decisions and 138
  next-H4 reversals.

## Primary HASTOC observation

`journey_hastoc10` is HASTOC oriented so that larger values point toward the
active Journey direction. Equal-count quintiles contain 821 decisions each.

| Relative HASTOC quintile | Next-H4 flip | Flip within 3 H4 | Peak already past | Median remaining favorable ranges |
| --- | ---: | ---: | ---: | ---: |
| Q1 weakest | 35.8% | 66.4% | 48.8% | 0.63 |
| Q2 | 27.8% | 60.3% | 40.6% | 0.76 |
| Q3 | 23.8% | 57.2% | 38.5% | 0.77 |
| Q4 | 20.7% | 53.7% | 36.2% | 0.81 |
| Q5 strongest | 9.3% | 44.6% | 27.6% | 0.95 |

The raw Q1-Q5 next-H4 gap is +26.6 percentage points and appears with the same
direction in every 2024/2025/2026 LONG/SHORT slice. That is a strong descriptive
ordering, not proof of an independent signal.

## Redundancy with already-known HA morphology

The HASTOC level has Pearson correlation +0.36 with H4 body/range and +0.29
with absolute H4 HA Delta. More important, the extreme-quintile contrast shrinks
as existing information is held comparable:

- within H4 body/raw-close geometry: +9.1 pp next-H4 flip;
- adding Delta contraction + opposite-wick state: +3.4 pp;
- adding ordered H1 path: +2.7 pp on the globally overlapping extreme cells;
- adding the HA-5 rejection/return state: +4.9 pp on only 811/4,105 rows.

A cell-local rank sensitivity, which re-ranks HASTOC inside each existing-state
cell instead of requiring global Q1/Q5 overlap, leaves about +6.4 pp next-H4
and +8.6 pp three-H4 separation across 3,936/4,105 rows. This suggests some
relative ten-bar context remains after coarse state matching, but its size is
far smaller than the pooled +26.6 pp and varies materially by year/side and
state. It is descriptive consumed-data evidence only.

The one-bar HASTOC change is even more redundant. In its weakest-change
quintile, 99.7% of decisions are already H4 Delta contractions; in its
strongest-change quintile only 2.5% are contractions. Once Delta contraction
is fixed, global extreme-quintile overlap largely disappears. Do not treat
HASTOC change as a separate momentum vote.

## H1 warning interaction and tail protection

Within the 1,395 ending-H1-opposed decisions, HASTOC Q1 versus Q5 has a raw
next-H4 difference of about +21.1 pp (57.7% versus 36.6%). After re-ranking
within Delta-contraction/wick/HA-5 state cells the weighted next-H4 distinction
is about +9.1 pp, while the three-H4 distinction is approximately zero. This
looks more like *near-term transition timing* than an established Journey-end
state.

Most importantly, weak HASTOC is not a safe exit. Among the 88 Journeys lasting
at least ten H4 bars, the full-sample Q1 state occurs in 84 Journeys. Across
337 such tail decisions, 261 do not reverse on the next H4 and median remaining
favorable excursion is still about 1.05 trailing-H4 ranges. Converting Q1 into
an exit would repeat the false-warning/tail-loss problem found in HA-4/HA-5.

## Interpretation

HASTOC10 is useful as a **relative signed-HA-body history coordinate**. Its
pooled ordering is large and stable in direction, but much of that ordering is
already represented by H4 body/Delta/wick and ordered-H1 state. A modest
residual ordering remains after coarse matching, especially for next-H4 timing,
but it is not stable or independent enough to authorize an action rule on the
consumed development period.

HA-6A therefore stops at observation. Retain `journey_hastoc10` as a documented
candidate state variable for later HA-state modelling, but do not promote its
source-paper thresholds, one-bar change, or any HASTOC-based entry/exit. The
next roadmap family may proceed separately under a frozen HA-6B contract.
