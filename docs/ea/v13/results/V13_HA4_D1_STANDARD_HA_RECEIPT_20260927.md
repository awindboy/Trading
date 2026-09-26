# V13 HA-4A completed-D1 standard-HA observation

Date: `2026-09-27`

Status: `D1 OBSERVATION COMPLETE / NO TRADE RULE / H1 NEXT`

## Question and causal boundary

Does the last **completed** D1 standard-HA state distinguish H4 Journey
continuation or transition beyond what the completed H4 HA candle already
shows? The forming D1 bar was never a decision feature. This study follows
`../V13_HA4_MTF_OBSERVATION_CONTRACT_20260927.md` and does not change the
Baseline-0 EA, Child admission, or exit.

The script `research/v13/ha4_mtf_audit.py --stage d1` streamed the raw GOLD#
M1 source through the full frozen window. It reconstructed H4 and D1 directly
from M1, then checked their OHLC against the exports. H4: 7,198 bars checked,
zero mismatches; D1: 1,201 bars checked, zero mismatches. The Baseline-0
structural prefix remained 965 closed Journeys and 3,858 closed Children.

Source SHA-256:

```text
M1 fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250
H4 b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf
D1 3180a978f7790c568fecd0349a9e3e04c0748ed565b4ea2c47b50e109ef47a4e
```

HA-4 timestamps completion at the **first actual M1 print** of the next
bucket. HA-2 used the exported next-H4 nominal bar time. Thus HA-4's
raw-extreme-to-exit median is 7.55h versus HA-2's 7.35h; the price giveback
median remains 21.41. This is a clock convention difference, not an MTF
strategy result.

## Full-window observation

There were 4,108 completed active-H4 decisions; 4,105 have the specified
future-outcome horizon in-window. Alignment means the last completed D1 HA
color equaled the active H4 Journey color at the H4 decision.

| D1 vs H4 | H4 decisions | Next H4 flip | Flip within 3 H4 bars | Journey's raw favorable extreme already past |
|---|---:|---:|---:|---:|
| Aligned | 2,270 | 22.8% | 54.2% | 30.3% |
| Opposed | 1,835 | 24.3% | 59.2% | 30.9% |

The raw-extreme column is a **future label**, not information available at
the decision. D1 opposition had only a 1.4 percentage-point higher next-H4
flip rate. Its 3-bar difference was about five points, but this is not an
independent validation or an entry/exit rule.

Resampling whole Journeys (1,000 fixed-seed draws) rather than pretending
successive H4 decisions are independent gave opposed-minus-aligned
next-flip difference `+1.43 pp` with a descriptive 95% interval of
`-1.18 to +4.03 pp`; the three-bar difference was `+5.05 pp` with
`+0.55 to +9.69 pp`. This quantifies uncertainty in the observed period,
not out-of-sample reliability.

After grouping H4 decisions by H4 body/range quintile, the next-flip
aligned/opposed comparison changed sign or became negligible. The respective
next-flip rates in the five H4 body bins were approximately:

```text
H4 body bin     aligned    opposed
weakest          41.4%      42.1%
Q2               30.8%      25.9%
Q3               23.5%      22.3%
Q4               15.6%      15.6%
strongest          8.6%       8.7%
```

D1 body/range quintiles themselves had next-H4-flip rates 24.4%, 21.3%,
23.1%, 23.3%, and 25.2% from weakest to strongest: no ordered relation.
No-opposite-wick D1 versus opposite-wick D1 also showed little separation
(23.8% versus 23.2%). Year/side cuts did not show a uniform alignment effect;
2026 LONG and SHORT cuts reversed the pooled next-flip direction. The
rank association of completed-D1 same-color streak with next-H4 flip was
approximately `+0.006`, likewise offering no clear monotone distinction.

## Interpretation

Completed D1 standard HA is a valid broader-state observation, but this first
full-window audit has not found a stable, distinct **next-H4-transition**
signal on top of H4 morphology. The 3-bar separation merits description,
not a veto: it varies by year/side and repeated H4 decisions within each
Journey are dependent. No D1 action authority follows.

The generated decision-feature and future-label CSVs are separate and stay
under `output/v13_ha4_d1_20260927/`, outside Git. The next HA-4 step studies
H1 standard HA independently, including all false early warnings.
