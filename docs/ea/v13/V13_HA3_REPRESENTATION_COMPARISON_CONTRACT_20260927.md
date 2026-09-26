# V13 HA-3 representation comparison contract

Date: `2026-09-27`

Status: `OBSERVATION ONLY / NO EA OR TRADE RULE CHANGE`

## Question

How does changing HA responsiveness trade color persistence against raw-price
turning-point lag and giveback? This is a representation study, not a P/L
optimization or a replacement for Baseline 0.

## Frozen comparison

All variants consume the same completed GOLD# H4 OHLC, warm up from the
`2022-01-03` source start, start flat at `2024-01-01`, and use the entire
available comparison window through the `2026-08-28 20:00` execution open.
An H4 bar is revealed only at the next H4 open. M1 is used only after the
decision sequence is fixed, for retrospective raw-extreme outcome labels and
source parity. The existing Baseline-0 EA and its MT5 execution authority are
unchanged.

The four predefined variants are:

```text
STD:       C=(O+H+L+C_raw)/4; O=(previous HA O+previous HA C)/2
FAST-R25:  same HA C; O=0.25*previous FAST O+0.75*previous FAST C
PRE-EMA2:  EMA2 each raw O/H/L/C independently, then standard HA
POST-EMA2: standard HA, then EMA2 its O and C independently for color
```

Every recursive series is initialized at its first warm-up source bar. EMA2
uses `alpha=2/3`. Exact ties inherit the previous nonzero color. FAST-R25 and
EMA2 are single sensitivity probes, not optimized parameters. No parameter
grid, fitted threshold, trade-rule change, or P/L winner is permitted here.

## Measurements and caveats

- color flips, closed/open Journeys, 1-bar and >=10-bar Journeys, Journey length;
- color disagreement with STD and same-bar flip overlap;
- new-color persistence after another 1/2/3 H4 bars;
- M1 favorable extreme after a Journey's first hypothetical execution open,
  until the opposite-color exit open, and its timestamp;
- time from that extreme to the exit open, and direction-adjusted giveback
  from extreme to the next-H4-open raw price;
- year and side slices as diagnostics, never as a parameter selector.

Different representations partition the same history into different Journeys.
Their median giveback values therefore describe **different episode sets**;
they are not matched-trade improvements. A lower giveback may simply be caused
by earlier fragmentation. The next causal test, if one is later authorized,
must compare matched underlying price episodes and the entire participation
path, not only exit distances.

Decision fields and future labels are kept in separate CSV ledgers. The source
code is `research/v13/ha_representation_audit.py`. The primary summary is a
compact receipt under `results/`; generated ledgers and raw source files stay
outside Git.
