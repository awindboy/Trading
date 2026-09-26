# V13 research state

Last synchronized: `2026-09-27`
Status: `BASELINE 0 FROZEN / ACTUAL-TICK STRUCTURAL PARITY CONFIRMED / HA-0..HA-4 OBSERVATION COMPLETE`
Market: `GOLD# ONLY`

## 1. Generation reset

V13 starts from a fresh minimal strategy rather than extending V12.

The active trading skeleton uses one decision source: completed standard H4
Heikin-Ashi color. V12 CRT, liquidity, Wave, multi-speed HA, ML, session/event
and lower-timeframe feature work remains historical evidence only.

## 2. Frozen strategy skeleton

```text
completed H4 standard HA
-> same-color Journey
-> one Child per completed same-color bar
-> cap at 10 successful Children
-> first opposite completed HA closes all
-> reverse into new Journey
```

No SL or TP exists in Baseline 0.

## 3. Frozen comparison window

`2024-01-01 through 2026-08-28 available GOLD# history`

All strategy-performance comparisons use the full window. Year or month subsets
are diagnostic slices only.

## 4. Deterministic H4 sanity reconstruction

Idealized next-H4-open fills, no transaction costs:

```text
closed Journeys: 965
closed Children: 3,858
gross net points: +8,147.11
Journey PF: 1.2597
Child PF: 1.2000
```

This remains a structural/economic sanity check, not official broker economics.

## 5. Extended MT5 actual-tick diagnostic

The uploaded report `ReportTester-318585216.xlsx` has SHA-256:

`deaf28634e97ebf1cf9805ecb0504d5b7ff1a49e8725439e0c4f752e20926cc3`

Report environment:

```text
terminal: XMGlobal-MT5 7 / Build 6230
symbol: GOLD#
period: H4
test range: 2024-01-01 through 2026-09-26
model: 100% real ticks
deposit: 10,000 USD
leverage: 1:500
```

Whole-report diagnostics:

```text
net profit: +7,180.62 USD
profit factor: 1.167727
balance DD maximal: 3,701.92 USD / 19.12%
equity DD maximal: 5,406.66 USD / 25.82%
equity DD relative: 29.26% / 4,622.08 USD
positions/trades: 3,977
deals: 7,954
LONG: 2,159 / 42.38% winning
SHORT: 1,818 / 29.21% winning
```

This is **not** the official exact-window economic receipt because:

- the run extends beyond the frozen `2026-08-28` end;
- leverage is `1:500`, not the protocol's `1:100`.

Structural prefix verification through the canonical data cutoff found:

```text
Journey IDs started: J000001..J000966
closed Journeys before the final open Journey: 965
Children in closed J000001..J000965: 3,858
J000966: SHORT C01 opened 2026-08-28 20:00 and remained open at source cutoff
closed-Journey Child-count distribution:
1:187, 2:202, 3:139, 4:113, 5:79,
6:59, 7:40, 8:33, 9:25, 10:88
```

That exactly matches the deterministic H4 structural counts. The repaired EA is
therefore suitable as a baseline observation engine.

## 6. Interpretation boundary

The current baseline is deliberately primitive. Do not treat its pooled
statistics as if they were the end product of a mature strategy.

The strongest current lesson is about HA itself:

- HA smooths raw price and suppresses frequent color switching;
- the same recursive smoothing creates reversal lag;
- a same-color late Child can be directionally consistent yet enter after much
  of the move has already occurred;
- opposite-wick/body contraction can emerge before the color flip;
- long persistent runs can be economically important even when many short runs
  are unproductive.

Therefore current diagnostics do **not** authorize:

- SHORT prohibition;
- lowering MaxChildren from ten;
- a fixed late-Child skip;
- a fixed streak cutoff;
- a new SL/TP;
- any external indicator filter.

## 7. External HA research synthesized

The source register now records evidence for the following HA research families:

1. standard recursive HA OHLC and synthetic-price semantics;
2. HA morphology: body, wick, no-wick, strength and Delta;
3. smoothed HA variants and step/noise filters;
4. multi-timeframe HA state;
5. HA + raw-price/fractal structure;
6. HA + moving-average trend context;
7. HA + volatility/trend-strength tools such as ATR, ADX and SuperTrend;
8. HA-derived momentum such as HASTOC;
9. volume/delta participation concepts;
10. HA features combined with ML/ONNX pipelines.

These are research leads only. No source establishes V13 edge without our own
causal full-window test.

## 8. Formula-audit finding

External HA code cannot be trusted by label alone.

MetaQuotes standard authority uses recursive previous **HA** Open/Close for the
next HA Open. One MQL5 deep-learning article's Python example instead calculates
`ha_open` from previous **raw** Open/Close. That article remains useful as an
ML-integration example but is not a standard-HA formula authority.

Every imported implementation must therefore pass formula parity before use.

## 9. HA-0..HA-3 research update

The completed observation receipts are under `results/`. HA-1 confirms that
body strength and opposite-wick geometry describe related persistence state;
their apparent signals must not be counted as independent. HA-2 finds a
standard-HA median 7.35-hour raw extreme to opposite-color exit and median
21.41 GOLD-price giveback. The year medians rise with Gold's price movement;
fixed-price cutoffs are not authorized.

HA-3 changes *representation only*. On the full window, FAST-R25 has 1,240
closed Journeys versus STD's 965, with median lag/giveback 6.40h/18.03 versus
7.35h/21.41. PRE-EMA2 has 757 closed Journeys and 8.83h/24.10. POST-EMA2 has
exactly the same color chronology as PRE-EMA2 under these formulas. These are
different episode partitions, not matched-trade improvement or MT5 economics.

All findings use already-consumed 2024-2026 development data. No variant has
been promoted into the baseline EA, and the official exact-window real-tick
economic receipt is still pending.

## 10. HA-4 D1 and H1 completed-HA update

HA-4 reconstructed completed D1 and H1 standard HA from chronological raw
M1, with zero OHLC mismatches against the exported H4/D1/H1 bars and the same
965-Journey/3,858-Child baseline structure. The stages were analyzed
separately; neither timeframe changed Baseline-0 decisions.

- Last completed D1 color opposed versus aligned to the H4 Journey showed
  next-H4 flip rates 24.3% versus 22.8%. H4-morphology and year/side cuts did
  not support a robust next-flip distinction. Its three-H4-bar difference
  remains exploratory development evidence, not a D1 veto.
- Last completed H1 opposed versus aligned showed 47.3% versus 11.2% next-H4
  flips and 54.6% versus 18.2% final raw-extreme-already-past labels. But
  735 of 1,395 opposed-H1 decisions did not flip next H4, and all 88 long
  Journeys had at least one opposed-H1 warning. The pooled contrast shares
  much information with H4 raw-close versus HA geometry; H1's distinct
  actionable contribution is not established.

The raw-extreme-already-past variable is a future label. No H1 exit, D1
alignment filter, changed funding, or MTF score has trading authority.

## 11. Active research question

The next question is no longer “which simple filter immediately improves P/L?”

It is:

> Can causally confirmed raw-price swing structure distinguish actual
> continuation/failed breaks from temporary H1 opposition and clarify the
> H4 HA lifecycle without relying on hindsight pivots?

Roadmap Stage HA-5 studies this without changing trades.

## 12. Promotion boundary

Observation may begin now. Strategy modification may not.

Before any candidate rule becomes V13 action authority it must:

1. have a stated mechanism;
2. be frozen before economic comparison;
3. alter one component where practical;
4. use causal decision inputs only;
5. compare against Baseline 0 over the full canonical window;
6. preserve tail/giveback accounting rather than report only win rate;
7. survive year/side/Journey diagnostics without hidden exceptions.

The exact-window actual-tick baseline rerun remains required before final
economic promotion of any new strategy variant.
