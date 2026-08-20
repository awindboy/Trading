# Strategy Robustness Research State

Last updated: 2026-08-20
Repository base: `2ce911297ea2f5b8d26f0ba78d2ac132445ac0a8`
Status: **BASELINE EDGE NOT DEMONSTRATED / BASE EDGE AUDIT ACTIVE / FROZEN REGIME V1 PRESERVED / 2021 UNTOUCHED**
Baseline control: Mentor deterministic V1 / build 1.91 semantics
Cross-symbol harness: `1.92R1L3`
Strategy authority: unchanged; `AGENTS.md` remains highest authority

## Current phase

The project is no longer treating Regime Research V1 promotion as the immediate next decision.

The new 18-symbol 2025 NO-GATE result challenges the more basic assumption that the underlying continuation signal has generally positive predictive edge.

Current priority:

`BASE EDGE AUDIT`

The project must determine where, if anywhere, predictive information exists in:

```text
Map
-> Root
-> Contact
-> Sweep
-> CHoCH
-> FVG
-> Entry
-> SL/TP geometry
```

before adding more regime filters or consuming the final untouched period.

Detailed current evidence:

`docs/ea/BASE_EDGE_AUDIT_2025.md`

## What remains frozen and valid

Regime Research V1 remains exactly:

`M30_CLEAN_PERSISTENT_EXPANDING`

```text
EXTERNAL_CONTINUATION
latest 12 confirmed M30 waves at PLAN freeze
progression >= 2/3
protected-break count <= 1
leg_expansion_ratio > 1.0
```

Historical evidence remains:

```text
2023–2025 direct:
24 trades / 13 wins
+49.797314R
mean +2.074888R
DD -5.173397R

2022 first sealed OOS:
6 trades / 1 win
+0.994756R
mean +0.165793R
DD -3.012334R
PASS under pre-registered contract
```

This evidence still supports the bounded statement that the frozen gate selected a favorable subset in its Gold development lineage and passed the first sealed 2022 contract.

It does **not** prove that the underlying baseline has broad cross-symbol edge.

## New 2025 cross-symbol evidence

Common setup:

```text
18 symbols
BASELINE_NO_REGIME_GATE
build 1.92R1L3
FIXED_RISK_MONEY = $100
ROOT_OB_DISTAL_20
Every-tick Strategy Tester evidence
```

Raw closed trades:

```text
1,463 trades
246 wins
16.81%
-418.221912R
mean -0.285866R
PF ≈ 0.6686
```

Five symbol-years contain execution divergence and are not final strategy evidence:

```text
EURCAD
EURGBP
GBPJPY
GBPUSD
USDCHF
```

Divergence-free 13-symbol continuation panel:

```text
901 trades
165 wins
18.31%
-179.573032R
mean -0.199304R
PF ≈ 0.7637
```

Strategy-planned-barrier rescore:

```text
TP -> +planned R
SL -> -1R

total = -166.492129R
mean = -0.184786R/trade
```

Therefore broker slippage/swap/execution realism is not the primary explanation for the negative expectancy.

## Weak null diagnostic

Trade-specific stylized barrier null:

```text
P(TP first) = 1 / (1 + planned_R)
```

Divergence-free continuation:

```text
expected wins = 205.73
actual wins = 165

expected rate = 22.83%
actual rate = 18.31%
```

This is a diagnostic only, not a final statistical market model.

## Direction asymmetry

LONG:

```text
460 trades
101 wins
actual TP rate 21.96%
null TP rate 23.08%
planned-barrier -4.18R
canonical -13.36R
```

SHORT:

```text
441 trades
64 wins
actual TP rate 14.51%
null TP rate 22.57%
planned-barrier -162.31R
canonical -166.21R
```

Current interpretation:

```text
LONG = edge not demonstrated; approximately null-like in 2025
SHORT = strong negative-edge warning in 2025
```

This does not authorize a permanent SHORT veto.

## H1 continuation split

```text
H1 BULLISH:
355 trades / 80 wins
planned-barrier -1.45R

H1 BEARISH:
329 trades / 46 wins
planned-barrier -139.86R

H1 TRANSITION:
217 trades / 39 wins
planned-barrier -25.18R
```

The mature bearish continuation path is the dominant failure cluster.

## Breadth

Positive divergence-free continuation symbols:

```text
BTCUSD
GBPCAD
GOLD
```

Negative:

```text
CADCHF
CADJPY
CHFJPY
EURCHF
EURJPY
EURUSD
GBPCHF
SILVER
USDCAD
USDJPY
```

The negative pooled result is not explained by one outlier symbol.

## Current trigger-design concern

D-127 is intentionally `SEQUENCE_ONLY`.

After Root contact, the scenario accepts the first direction-compatible detected M1 Sweep, then a later same-direction generic M1 protected-break CHoCH.

The current strategy deliberately does not require:

```text
Root reintersection at Sweep
Root-owned liquidity family
sweep-time opposite M1 trend
sweep-time protected-reference freeze
additional CHoCH strength score
mandatory child
```

This design was previously adopted to remove nested filtering.

The 2025 evidence now requires a new question:

```text
Did the simplification remove redundant filters,
or did it remove the causal ownership that gave the human setup meaning?
```

Do not answer by stacking old filters back into the baseline.

## Code-level symmetry checkpoint

A targeted source audit found no simple directional inversion in:

```text
structure break
FVG geometry
Entry side
Root-distal SL
objective reward sign
BUY_LIMIT / SELL_LIMIT request
```

So the SHORT result cannot currently be dismissed as an obvious sign bug.

A deeper directional audit remains part of the next phase.

## Current research order

```text
1. BASE EDGE AUDIT
2. identify where information appears/disappears
3. separate direction / Entry / SL / TP
4. compare simple frozen benchmarks
5. only then test one controlled strategy change
6. only then revisit regime gating
7. final untouched confirmation
```

## EDGE_AUDIT_V1 target

The next harness must be strategy-neutral.

Required checkpoints:

```text
PLAN
ROOT_CONTACT
SWEEP
CHOCH
FVG
ENTRY/FILL
```

Required research-only labels after the fact:

```text
15m / 1h / 4h / 24h signed forward returns
MFE / MAE
```

At Entry, also shadow:

```text
same-direction fixed exits:
1R / 2R / 3R

direction-flipped mirror:
1R / 2R / 3R
```

No shadow result may affect same-run strategy authorization.

## Simple benchmarks

After the audit harness:

```text
time-matched/random control
EMA trend-follow
RSI mean-reversion
MACD crossover
```

Use frozen/simple definitions. The purpose is benchmark comparison, not optimization.

## 2021

2021 remains the preferred untouched final confirmation dataset.

**Do not open it now.**

The base strategy is under re-evaluation, so consuming 2021 for the old Regime V1 promotion would reduce the value of the final untouched set.

## Parallel execution-safety work

Separate P0 items:

```text
recoverable cancel-reject exact-ticket retry
pending-disappeared broker-state reconciliation
terminalize late-2025 entry cohort
re-run contaminated symbol-years
```

Execution integrity and predictive edge remain separate research questions.

## Explicit non-actions

Do not:

```text
tune Regime V1
promote Regime V1
add SHORT veto
add planned-R cap
add PD veto
add generic quality score
restore D-126 wholesale
open 2021
```

until the base-edge audit identifies a specific causal failure or surviving edge.
