# V9 Terminal-Stage Causal Combination Research Checkpoint

Date: `2026-09-15`
Status: `CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY`
Market: `GOLD# ONLY`
Base GitHub HEAD: `d123ea1e9e40ad388cf107b3d3a4d08386877b6b`

## 1. Purpose

After establishing the non-causal `true last Child -> HA1 -> close all open Children` oracle, this study asked whether Heikin-Ashi information combined with causally available indicators/structure could mechanically identify terminal HA events.

The study deliberately explored multiple information families, but the current prototype remained frozen.

## 2. Answer sheet

Research oracle:

```text
TRUE LAST ACCEPTED CHILD
-> first completed opposite-color H4 HA1
-> close every still-open Child in that route
```

Full-history deterministic result:

```text
BASE   +8,530.74 / PF 2.023 / WR 65.58% / DD 440.35
ORACLE +13,863.22 / PF 3.475 / WR 70.41% / DD 288.75
```

`TRUE LAST CHILD` is future information and was used only for labels/evaluation.

## 3. Delayed-oracle test

The oracle was deliberately activated later than the true last Child to measure how much detection latency can be tolerated.

| Delay | PnL | PF | WR | DD |
|---|---:|---:|---:|---:|
| BASE | +8,530.74 | 2.023 | 65.58% | 440.35 |
| 0 H4 | +13,863.22 | 3.475 | 70.41% | 288.75 |
| 1 H4 | +13,839.03 | 3.464 | 70.41% | 288.75 |
| 2 H4 | +13,715.95 | 3.407 | 70.24% | 288.75 |
| 3 H4 | +13,471.13 | 3.272 | 70.06% | 260.86 |
| 4 H4 | +12,608.38 | 2.927 | 69.36% | 371.34 |

Interpretation: terminal-stage recognition does not have to be instantaneous at Child entry. Several completed H4 bars may remain available to gather causal evidence before much of the oracle value disappears.

## 4. Information families explored

At causal H4 / opposite-HA event timestamps the study examined:

### Heikin-Ashi

- opposite HA body / ATR180;
- body/range fraction;
- wick asymmetry and no-wick states;
- current body versus recent HA bodies;
- opposite streak / prior primary streak;
- H1 HA majority/persistence context.

### H4 liquidity

- nearest same/opposite H4 liquidity distance / ATR180;
- distance ratio;
- active counts and ages;
- Child-relative change in same/opposite distance;
- missing same-side target / topology;
- replenishment/depletion context.

### Price/structure/location

- H4/H1 Donchian location;
- Bollinger location/bandwidth;
- RSI;
- EMA location;
- MACD histogram;
- DMI/ADX;
- H1/H4 Kijun / cloud location;
- H1 range/volatility/efficiency context.

### Journey context

- Anchor MFE/giveback;
- route progress;
- open Child state;
- movement-capacity context.

## 5. Univariate observations

No single indicator solved the terminal problem.
Representative event-time average AUCs in 2024-2026 included approximately:

```text
H4 liquidity distance ratio      ~0.69
H1 primary-aligned RSI           ~0.66
Child-relative liquidity change  ~0.65
H1 cloud location                ~0.65
H4 Donchian primary location     ~0.65
H4 Bollinger location            ~0.64
H4 MACD histogram                ~0.63
HA opposite body strength        ~0.58
```

HA morphology itself was therefore not sufficient. Its strongest role remains the actual H4 reversal event.

## 6. Common indicator rules were not enough

Direct rules such as opposite HA plus RSI, MACD, EMA, Kijun, cloud, DMI, Donchian, or H1-HA agreement generally generated too many interventions and underperformed BASE on the all-history consumed screen.

This is evidence against simply adding a familiar trend indicator to HA and calling it terminal authority.

## 7. Three-part mechanical decomposition

The most coherent recurring combination was:

```text
A. LIQUIDITY PRESSURE
   opposite H4 liquidity becomes more threatening relative to the Child state

B. LOCATION LOSS
   price loses favorable primary-direction H4 range location

C. HA REVERSAL STRENGTH
   a meaningful opposite H4 HA body is now confirmed
```

A natural semantic example:

```text
HA1
+ opposite liquidity closer than at Child entry
+ H4 Donchian primary location weak
+ current HA body stronger than recent HA bodies
```

produced a positive `+268.90` BASE delta over 2024-2026 with `17` selected route events and `0` answer-sheet early events in that slice.

This exact rule is not frozen authority.

## 8. High-precision mechanical rank candidate

A continuous mechanical rank using:

```text
Child-relative opposite-H4-liquidity pressure
+
H4 Donchian primary-direction location
+
opposite HA body strength / ATR180
```

was screened at a fixed high-precision operating point.

### 2024-2026 economics

```text
BASE      +7,428.37
CANDIDATE +7,869.42
ORACLE    +11,625.62
```

Hence:

```text
candidate BASE delta             +441.05
same-period oracle opportunity  +4,197.25
oracle improvement recovery       10.51%
remaining oracle gap            +3,756.20
```

Selected route events: `12`.
Answer-sheet early events: `0`.
Route deltas: `9` positive, `3` unchanged, `0` negative.

The candidate is therefore a clean **proof of concept**, but it still recovers only a small fraction of the oracle opportunity.

## 9. Same-feature mechanical vs ML comparison

Using the same three causal variables and comparable high-precision screening:

| Method | 2024-26 BASE delta | Worst year delta | selected events | answer-sheet early |
|---|---:|---:|---:|---:|
| **Mechanical rank** | **+441.05** | **+21.70** | 12 | **0** |
| Logistic | +234.60 | -122.41 | 17 | 4 |
| Tree depth 2 | +110.20 | -169.12 | 42 | 12 |
| Tree depth 3 | +182.90 | -163.45 | 28 | 4 |
| HGB | +140.64 | -46.24 | 12 | 3 |

Their AUCs were broadly similar around the mid-0.60s. The economic difference came from false-early intervention cost, not from a large AUC gap.

## 10. Correct evaluation interpretation

The current candidate must **not** be described simply as a successful `+441` improvement.

The answer-sheet comparison on the same period is:

```text
0% reference = BASE +7,428.37
100% reference = ORACLE +11,625.62
current candidate = +7,869.42
recovered oracle improvement = 10.51%
```

The current problem is therefore the unrecovered `89.49%` of the same-period oracle improvement, not proving that BASE can be beaten.

## 11. Research conclusion

Current evidence supports a two/three-stage concept:

```text
route participation / liquidity geometry
-> primary location/depletion state
-> opposite H4 HA reversal event
-> possible route-level profit protection
```

No exact threshold or model has earned authority.
The next research step is to explain the oracle gap route-by-route and build a causal terminal state that reproduces more of the answer-sheet ledger without sacrificing large winners.
