# V13 HA-4B completed-H1 standard-HA observation

Date: `2026-09-27`

Status: `H1 OBSERVATION COMPLETE / NO TRADE RULE / HA-4 COMPLETE`

## Question and source boundary

Does the completed H1 standard-HA sequence inside a completed H4 bar reveal
transition before H4 HA flips, and how often is that only a temporary
interruption? H1 is observed at each existing H4 decision; there is **no
intra-H4 entry or exit** and no modification to Baseline 0.

`research/v13/ha4_mtf_audit.py --stage h1` streamed GOLD# M1 and rebuilt H1
and H4 OHLC. Export parity: 27,518 H1 and 7,198 H4 bars checked through the
canonical cutoff, zero mismatches. The H4 baseline remained 965 closed
Journeys and 3,858 closed Child decisions. Source SHA-256:

```text
M1 fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250
H4 b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf
H1 2898e5b9b6f95a6e8fe27c0c6578f74b7a7bd8adbefe10132ab38e3eef1a426c
```

Like the D1 receipt, HA-4 uses the first actual next-bucket M1 print as
the completion time; HA-2 used nominal H4 bucket labels. The resulting
7.55h versus 7.35h median lag is a clock convention difference, not an H1
effect. Median price giveback is 21.41 under both.

## Full-window H4-decision observation

Of 4,108 completed active-H4 decisions, 4,105 have the specified in-window
future horizon. `Aligned` means the last **completed** H1 HA color equaled the
still-active H4 Journey color at that H4 decision. No forming H1 or future
H4 color entered the feature.

| Last completed H1 vs H4 | Decisions | Next H4 flip | Flip within 3 H4 bars | Final raw favorable extreme already past* |
|---|---:|---:|---:|---:|
| Aligned | 2,710 | 11.2% | 48.7% | 18.2% |
| Opposed | 1,395 | 47.3% | 71.5% | 54.6% |

*The extreme's final timestamp is a **future outcome label**, not something
known at the H4 decision. The association is descriptive, not an oracle.
Journey-cluster bootstrap (1,000 fixed-seed draws) put the observed
opposed-minus-aligned next-H4 flip difference at `+36.1 percentage points`,
with a descriptive 95% interval of `+33.3 to +39.2 points`. This interval
does not make the consumed history independent validation.

This did not depend only on first-bar Journeys: at Journey birth the
aligned/opposed next-flip rates were 13.6%/45.6%, and on continuing H4
Journeys they were 10.2%/47.6%. The direction held in each 2024/2025/2026
and LONG/SHORT diagnostic cut, and in all five H4 body/range quintiles.
At Journey birth the final raw extreme cannot already precede the first
entry by definition. Among **continuing** H4 decisions only, the
extreme-already-past label was 25.7% aligned versus 62.3% opposed; this
remains a retrospective label, not a live turning-point observation.

## The false-warning and redundancy checks

H1 opposition is common, not a precise exit event. It appeared at 1,395 H4
decisions; **735 did not flip on the next H4**, and **397 did not flip within
three H4 bars**. Of the next-H4 flips with this outcome horizon, roughly
68.5% had a preceding opposed-H1 state at the previous H4 decision; the
remaining flips had no such warning. A trigger based on this state alone
would therefore both miss flips and interrupt many continuing Journeys.

Right-tail exposure matters: the 88 Journeys lasting at least ten H4 bars
all had at least one opposed-H1 warning. There were 318 such warning
decisions within those long Journeys, and 254 did **not** precede an
immediate H4 flip. This is retrospective coverage, not simulated profit,
but it cautions against treating H1 opposition as a blanket exit.

H1 opposition remains associated with transition within every H4 body/range
quintile. However, it is **strongly entangled with the already-known H4 raw
close relative to H4 HA Close**: in the most favorable H4 raw-close quintile
there were no opposed-H1 observations. As a post-hoc overlap diagnostic,
among ten H4 body × raw-close cells with at least 20 aligned and 20 opposed
decisions each, the min-group-weighted next-flip difference was only about
`+4.4 points`, versus `+36.1 points` pooled. This check is not a matched
causal estimate and its display-cell cutoff is not a trading threshold.
Only 1,627 decisions fall in these overlapping cells, so the remaining
history has insufficient like-for-like support. The comparison suggests
substantial overlap with H4 price/HA geometry; it does not quantify H1's
unique contribution over the full history.

The number of H1 color flips inside the completed H4 bar was not a clean
monotone transition measure: next-H4 flip rates for 0, 1, 2 and 3 H1 flips
were about 10.1%, 33.3%, 22.9% and 36.8% (the 3-flip group was small).

## Interpretation and boundary

H1 carries an **early descriptive warning** at H4 decision cadence, unlike
the weak D1 next-flip contrast. But HA-4 has **not established that H1 adds
independent actionable information beyond the full H4 raw-price/HA state**,
nor that leaving on H1 opposition preserves large Journeys or improves
actual-tick economics. Those claims require a later frozen action experiment
and unconsumed validation; they are not granted here.

Decision features and future labels are separate local ledgers under
`output/v13_ha4_h1_20260927/`. No raw datasets, generated ledgers or
economic results are promoted to Git. The research order now proceeds to
HA-5 raw-price structure, observation-only.
