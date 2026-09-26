# V13 HA-0 measurement receipt

Date: `2026-09-27`

Status: `DESCRIPTIVE DEVELOPMENT EVIDENCE / NO TRADE RULE CHANGE`

## Reproduction

`research/v13/ha_representation_audit.py` consumed H4 bars chronologically,
using each bar only at the next H4 open. The raw GOLD# M1 file was streamed
separately for source parity and retrospective labels. Evaluation began flat
at `2024-01-01`; the last in-window decision/execution open was
`2026-08-28 20:00`. Earlier H4 data warmed the recursive HA state.

Source SHA-256:

```text
H4 b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf
M1 fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250
```

The M1 reconstruction matched all 4,108 in-window H4 OHLC bars within 0.01
GOLD price. All 4,108 completed H4 decisions belong to a started Journey;
the first post-boundary completed H4 bar itself changed color relative to the
warm-up state. HA-1's next-bar outcome sample is 4,107 because the final H4
decision has no in-window next completed bar.

## Standard-HA structural result

```text
closed Journeys                    965
closed-Journey Child decisions  3,858
one-bar Journeys                  187
Journeys >=10 bars                 88
open Journey at cutoff             1
```

These reproduce the Baseline-0 structural counts. Child result labels in the
generated ledger use hypothetical next-H4-open gross price differences without
costs. They are not MT5 actual-tick P/L.

The decision ledger records raw/HA OHLC, HA body, Delta, range, wick geometry,
streak and Child index. Separate future-label ledgers contain Journey exit,
M1 favorable/adverse extrema and time, giveback, and gross Child outcomes.
Large CSV ledgers remain local under `output/v13_ha3_20260927/`, not in Git.

No threshold, filter, exit, or Baseline-0 EA change follows from HA-0.
