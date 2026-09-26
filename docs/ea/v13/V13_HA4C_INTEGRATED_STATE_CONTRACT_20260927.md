# V13 HA-4C integrated HA-state observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE MEASUREMENT / OBSERVATION ONLY`

## Why this supplement exists

HA-1 found meaningful standard-H4 body/wick morphology. HA-2 measured aggregate
lag/giveback. HA-3 and HA-4 then emphasized color chronology and alignment,
without adequately testing how their additional representations interact with
the *same* H4 Journey's evolving morphology. HA-4C fills that descriptive gap
before HA-5. It does not revise HA-0..HA-4 receipts or Baseline-0 orders.

## Population, timing and source

- One row per completed Standard-H4-HA decision in the canonical GOLD# window.
- Preserve the 965 closed Baseline-0 Journeys and match HA-3/HA-4 by signal time,
  active Journey ID, side and H4 OHLC; do not compare variant-defined Journeys
  as if they were the same market episodes.
- Rebuild H1/D1 from chronological raw M1 using the existing HA-4 tool. At an
  H4 decision use only completed H1/D1 bars available at that timestamp.
- Keep decision features in a separate file from future labels. No baseline EA,
  child admission, exit, risk or sizing change is permitted.
- Existing 2024-2026 data are consumed development evidence; no independent
  validation or strategy-performance claim is possible from this study.

## Predeclared decision-time observations

1. Standard H4: body/range, absolute Delta contraction versus the preceding
   same-Journey bar, opposite-wick present and first reappearance, raw close
   versus HA close normalized by the just-completed raw H4 range, and Journey
   birth/continuation. These are *separate* descriptors; body and wick are not
   independent votes.
2. FAST-R25: color opposed to the active Standard-H4 Journey, body/range and
   absolute-Delta contraction across the same H4 decision timestamps. This is
   a secondary observation, never a replacement Journey in this comparison.
3. Last completed D1: color opposition, body/range and absolute-Delta
   contraction versus the preceding completed D1.
4. Ordered completed H1 states inside the just-completed H4: no opposition,
   temporary opposition repaired by the final H1, opposition still present at
   the final H1, plus trailing consecutive opposed-H1 count. Retain last-H1
   body/wick morphology and its Delta contraction. Preserve the order; a flip
   count alone is insufficient.

## Predeclared retrospective outcomes

- Baseline Standard-H4 color flip on the next H4 and within three H4 bars;
- whether the Journey's final favorable raw M1 extreme was already past (a
  *future-defined* label, not a live observable);
- remaining favorable raw-price H4 high/low excursion from the current next-
  H4-open until the Baseline Journey exit, and ensuing giveback, each divided
  by the median raw H4 range of the preceding 20 completed bars. The H4 extrema
  must match the source M1 parity already established. This normalization is
  a measurement coordinate only, not a trading threshold.

## Comparisons and limits

- First describe Standard-H4 morphology and the ordered H1 path jointly:
  next-flip, three-bar flip, false warning, remaining favorable excursion,
  and >=10-bar Journey warning coverage.
- For FAST, H1 and D1, contrast states only within comparable Standard-H4
  body/range and raw-close geometry display bins; report overlap coverage and
  do not extrapolate to non-overlap. A simple pooled rate is not incremental
  information.
- Show year, side and Journey-birth/continuation diagnostics. H4 decisions
  within a Journey are dependent; preserve denominators and tail Journeys.
- The categorical H1 paths and rank bins are descriptive, not fitted trade
  gates. No cutoff, score, veto, exit, ML model or P/L optimum may be promoted.
- If overlap or sample size is inadequate, state that the distinct
  contribution is unresolved rather than declaring the component useless.

Output: reproducible source code, separated local ledgers, compact receipt.
