# V13 HA-6D1 ADX Wilder observation receipt

Date: `2026-09-27`
Status: `OBSERVATION COMPLETE / NO ACTION AUTHORITY / HA-6D STOP CONDITION MET`
Authority base GitHub HEAD: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## Scope

This receipt implements the pre-measurement HA-6D1 contract. It adds only raw-H4
Welles Wilder ADX/DMI period 14 to the unchanged 4,108 Standard-H4 V13 decision
rows. Future outcomes remain in a separate 4,105-row label ledger. Baseline-0
Journey, Child, exit and execution semantics are unchanged.

Formula authority is the MetaQuotes ADX Wilder family. The calculation uses
mutually exclusive +DM/-DM, standard True Range `max(H-L, |H-Cprev|, |L-Cprev|)`,
14-period Wilder/SMMA smoothing, +DI/-DI, DX and ADX. H4 history from 2022 is
used as warm-up; all 2024-2026 decision rows have complete ADX values.

A MetaTrader Help page currently contains a conflicting first True-Range term
using `High(i)-High(i-1)`. The MetaQuotes CodeBase page and its public forum
correction identify the standard `High-Low` term; this audit follows the
CodeBase/Wilder construction. This discrepancy should be remembered for any
later MT5 vector-parity test.

## 1. Directionless ADX strength is only a weak lifecycle separator

Equal-count ADX14 quintiles on all 4,105 labeled decisions:

| ADX14 quintile | Decisions | Next-H4 flip | Flip within 3 H4 |
| --- | ---: | ---: | ---: |
| Q1 lowest | 821 | 26.1% | 57.5% |
| Q2 | 821 | 23.4% | 59.1% |
| Q3 | 821 | 23.6% | 58.2% |
| Q4 | 821 | 22.9% | 54.0% |
| Q5 highest | 821 | 21.3% | 53.5% |

The overall Q1-Q5 next-flip gap is only +4.8 points. It is not stable by
2024/2025/2026 x LONG/SHORT: two of the six slices reverse the sign of the
next-H4 contrast (2024 SHORT and 2026 LONG), while several three-H4 contrasts
also reverse. ADX strength is therefore distinct descriptively, but not a
stable termination coordinate on this consumed GOLD# window.

ADX itself is not merely HA morphology: correlation with H4 body/range is
+0.042, with ATR-normalized |HA Delta| +0.061, and with HASTOC -0.100. The
problem is not obvious redundancy; it is weak and unstable outcome separation.

## 2. DMI direction looks useful raw, but is mostly the HA-6B trend context again

Direction-normalized `side * (+DI - -DI)` gives:

| DMI state | Decisions | Next-H4 flip | Flip within 3 H4 | Median remaining favorable range |
| --- | ---: | ---: | ---: | ---: |
| Journey-aligned | 2,814 | 21.7% | 54.5% | 0.85 |
| Journey-opposed | 1,291 | 27.3% | 60.7% | 0.65 |

The raw difference is real in this sample, and the continuous DI-margin
quintiles decline from 26.9%/26.9% next-H4 flips in the two weakest quintiles
to 16.9% in the strongest quintile.

However, DMI direction is highly redundant with the already consumed MA family:

- `journey_di_margin` correlation with ATR-normalized EMA50 slope: `+0.862`;
- correlation with ATR-normalized EMA20 boundary distance: `+0.908`;
- binary DMI alignment matches EMA50-slope alignment on `84.7%` of decisions;
- it matches the EMA20 beyond-boundary state on `83.2%`.

After H4 geometry, Delta/wick, H1 path, HA-5 swing, HASTOC and MA states are
held in comparable cells, DMI has little supported independent contrast; adding
ATR-normalized geometry leaves only 30 decisions in two eligible full-stack
cells. No full-population incremental DMI claim is justified.

## 3. ADX rising/falling is more consistent raw, but its increment disappears

ADX falling versus rising:

| ADX change state | Decisions | Next-H4 flip | Flip within 3 H4 |
| --- | ---: | ---: | ---: |
| Falling / non-rising | 2,183 | 26.2% | 60.4% |
| Rising | 1,922 | 20.4% | 52.0% |

The falling-minus-rising next-H4 difference has the same sign in all six
2024/2025/2026 x LONG/SHORT slices. This is the strongest descriptive finding
inside HA-6D1.

But staged overlap shows the apparent increment shrinking materially. With H4
geometry + Delta/wick + H1/HA-5 + HASTOC held comparable, the rising-minus-
falling next-flip difference is about -1.9 points. After MA states it is about
-0.4 points over 931 supported decisions. After also adding ATR-normalized
geometry, it is approximately -0.1 point over 593 decisions. The directionless
ADX-change state therefore largely describes state already captured upstream.

## 4. ADX does not solve the H1 false-warning problem

Among the 1,395 decisions where the last completed H1 HA opposes the active H4
Journey:

- DMI aligned: 937 decisions, 46.1% next-H4 flip;
- DMI opposed: 458 decisions, 49.8% next-H4 flip;
- ADX rising: 620 decisions, 43.9% next-H4 flip;
- ADX falling: 775 decisions, 50.1% next-H4 flip.

The ADX falling-minus-rising next-flip difference remains positive in all six
year/side slices (about +1.9 to +8.5 points), so this interaction is not merely
one isolated year. Yet it is still a weak warning refinement, not a safe action:
even `H1 opposed + DMI aligned + ADX rising` retains a 43.0% next-H4 reversal
rate, while other joint states cluster around roughly 49-50%.

A full prior-state overlap inside H1 opposition becomes thin: the complete
stack provides only 164 supported decisions for ADX-rising comparison and only
8 for DMI alignment. These consumed-sample pockets cannot authorize a rule.

## 5. Right-tail counterexamples are decisive

All 88 Journeys lasting at least ten Standard-H4 bars remain in scope.

| Descriptive warning | Long Journeys marked | Decisions | Not next-H4 flip | Median favorable movement still remaining |
| --- | ---: | ---: | ---: | ---: |
| DMI opposed | 42 | 151 | 148 | 3.25 ranges |
| ADX falling | 71 | 355 | 336 | 3.38 ranges |
| DMI opposed + ADX falling | 42 | 131 | 128 | 3.10 ranges |
| Lowest global ADX quintile | 32 | 164 | 161 | 3.71 ranges |
| H1 opposed + DMI opposed | 25 | 40 | 38 | 3.61 ranges |

The putatively weak/troubled ADX/DMI states occur repeatedly inside the very
long Journeys V13 must preserve. Treating them as exit or Child-admission gates
would repeat the HA-4/5/6B tail-loss problem.

## Interpretation

HA-6D1 separates two ideas:

1. **ADX strength** is genuinely different from instantaneous HA morphology,
   but its GOLD# transition relationship is modest and unstable by year/side.
2. **DMI direction** is more strongly ordered with continuation, but it mostly
   re-expresses the raw-price trend context already measured by EMA50/EMA20.
3. **ADX falling** is a consistent raw transition association, including inside
   H1 opposition, but its independent increment nearly disappears after the
   prior state stack is held comparable and it falsely marks long Journeys.

This is enough to meet the V13 stop condition for the HA-6D trend-strength
branch. A SuperTrend experiment is **not performed or judged here**: adding an
ATR-derived directional trailing line after ADX failed to earn distinct action
authority would add another lagged price/volatility transform without a newly
identified mechanism. If SuperTrend is revisited later it requires its own
pre-frozen formula and parameter provenance.

No ADX level, DI direction, ADX slope, threshold, filter, entry, exit, Child
funding rule, SL, TP, sizing change or EA modification is authorized.

## Next roadmap family

The next genuinely distinct HA-6 family is **HA-6E volume / tick-volume
participation**, because HA, raw swings, HASTOC, EMA, ATR and ADX remain derived
from price. Before any volume study, verify exactly what GOLD# `<TICKVOL>` means
in the supplied/broker data and test its stability by year/session/timeframe.
