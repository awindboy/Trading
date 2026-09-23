# V12 origin and CRT hybrid thesis

Date: `2026-09-23`

## Why V12 exists

V10 became profitable after moving its participation clock from ordinary candles
to H4 Heikin-Ashi. That was valuable because it reduced observational noise and
kept participation in persistent journeys. Its structural weakness remained:
many HA transitions were treated as opportunities without a separate reason for
why price had stopped, swept, accepted, or departed at that location.

V11 tried to reveal more of the H4 formation process through Wave Candle and then
reassembled V10 capital. It produced a better representation and useful exposure
diagnostics, but it did not discover a robust new candidate skeleton. Most Stage
0-5 experiments still inherited V10's selected event ledger. The independent
STD/SLOW-memory skeleton was cleaner descriptively but unstable by side and year.

V12 therefore changes the order of construction.

## New order of construction

```text
old order
HA event -> candidate -> try to filter likely stops

V12 order
HTF range journey and location
-> sweep versus outside acceptance
-> completed confirmation on the execution timeframe
-> one independently falsifiable Child
-> HA/Wave/liquidity observations
-> conditional ML estimates
```

CRT is not expected to predict the market perfectly. Its value is that it may
create a more meaningful event population: a Child exists because a defined
range interaction and confirmation occurred, not merely because an indicator
changed color.

## What CRT contributes

- a higher-timeframe range object rather than a permanent direction label;
- a distinction between liquidity taken and liquidity accepted beyond;
- a temporal grammar: C1 range, completed C2 interaction, possible C3 delivery;
- explicit first and later destinations: C1 midpoint, opposite extreme, older
  liquidity;
- a location-before-trigger discipline;
- failure and reevaluation states instead of retrospective pattern rescue.

The supplied guide also describes Model #1, true MSS, KOD, and SMT. V12 treats
these as hypotheses requiring numeric definitions. A name or chart annotation
does not authorize an entry.

## What HA and Wave contribute

FAST/STD/SLOW HA are retained as different phase and smoothing coordinates:

- FAST: early participation and transition sensitivity;
- STD: intermediate phase compression;
- SLOW: persistent journey memory.

They are recorded at C1 close, C2 close, trigger, and Child decision. Agreement,
disagreement, run age, body geometry, and normalized separation are observations.
They do not veto a CRT candidate in Phase 0.

Wave Candle contributes compressed settlement-density, path-efficiency, and
directional-settlement observations inside H4. It is most naturally paired with
the W1->H4 lane. It remains observation-only because its prior static and forming
coordinates did not demonstrate stable stop selectivity.

## What ML contributes

Prior research repeatedly failed when ML was asked a broad question such as
"will this trade stop?" or "what is the next HA color?" V12 narrows the task to
conditional questions inside one already-defined structural event:

- which competing event occurs first: Hard SL or C1 50%;
- after C1 50%, does delivery continue to the opposite extreme;
- how long until each event;
- what is conditional R after the first destination;
- how calibrated and stable are those estimates by lane, side, year, and era.

ML cannot create candidates and cannot turn a weak CRT definition into a good
one. The complete preprocessing chain must be exported and parity-tested before
MQL5 can consume an ONNX model.

## Falsifiable V12 claim

V12 is worth continuing only if a reproducible CRT-created event population can
reduce avoidable stopped Children or stopped risk-units while preserving enough
trade count and persistent-run right-tail capital to improve scalable risk-adjusted
performance. Lower exposure alone is not success.

Every experiment must report at least:

- candidates, traded Children, and explicit `NO TRADE` counts;
- stopped Children and stopped risk-units;
- first/repeat/alternating-direction stop chains;
- win rate, gross and net R, and R per exposed unit;
- right-tail retention by outcome bucket;
- concurrent exposure and drawdown;
- LONG/SHORT, year, lane, and normalized-era stability;
- ambiguity, market-closed, and other execution-state counts.

## Non-goals

- proving that CRT, HA, or any named theory explains every movement;
- finding a chart-perfect oracle;
- optimizing a visual pattern on consumed history;
- importing a community EA and treating its backtest as V12 evidence;
- disguising V10 entries with CRT labels after outcomes are known.
