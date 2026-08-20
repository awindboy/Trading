# Strategy Robustness Research State

Last updated: 2026-08-20
Repository base: `260d14e714bbd635448d466d12d848b9ef80ba39`
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

## D-142A audit harness prepared

```text
build = 1.92R1L4
phase = BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW
default = audit OFF
strategy authority = NONE
```

Exact contract: `docs/ea/EDGE_AUDIT_V1.md`.

D-142A records hourly MAP state and PLAN / Root Contact / Sweep / CHoCH / FVG forward labels. ACTUAL_FILL is identity-only in this first build; exact tick virtual barriers are deferred until D-142A parity passes.

Status: **PREPARED / COMPILE + OFF/ON PARITY PENDING**.

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

D-142B deferred, only after D-142A parity:

```text
actual-fill same-direction fixed exits: 1R / 2R / 3R
actual-fill direction-flipped mirror:    1R / 2R / 3R
```

These tick-order virtual barriers are **not implemented in D-142A**. No shadow result may ever affect same-run strategy authorization.


## Six-symbol D-142A front-end evidence

The first contrast panel is no longer only a downstream-trigger audit. It exposed a more upstream question.

```text
H1 active-map LONG vs SHORT future raw 24h return ordering:
BTCUSD  -0.143%p
CADJPY  -0.066%p
GBPCAD  -0.012%p
GOLD    -0.115%p
SILVER  -0.192%p
USDJPY  -0.042%p
```

All six are inverse to the ordering expected from a useful directional classifier. 42/60 comparable symbol-month blocks show the same inverse ordering. This is a warning, not proof of an anti-signal, because hourly snapshots are serially dependent.

The current owner can persist for days while many new Root/PLAN opportunities inherit it. Median owner age at physical preplanned contact is about 59h LONG and 73h SHORT. The owner/trend state nevertheless remained exactly unchanged from PLAN to contact in all 4,809 paired scenarios, so the issue is not a simple map-flip bookkeeping defect.

At Root contact, local 24h signed response becomes positive on average in both directions and direction correctness improves materially for SHORT. This makes the core research question:

```text
Does the H1/M30 owner classify an already-completed move too late,
while a Root contact still produces a local reaction that is incorrectly
interpreted as continuation toward a distant external objective?
```

## D-143 FRONT-END CAUSAL AUDIT

Priority order is now:

```text
INITIAL_BOS / direction formation
→ owner persistence and continuation refresh
→ Root creation and Root ordinal under owner
→ PLAN selection
→ physical Root contact
→ only then downstream Sweep / CHoCH / FVG / Entry
```

D-143 logs all research rows into the normal `InpEventCsvFile` with an `EDGE_AUDIT_*` event prefix. No separate audit file is used.

The eventual strategy target is `>=50%` realized trade win rate. A variant that merely removes some losses without demonstrating a credible path to that target is not sufficient.

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


## D-143 conclusion / D-144 transition

The six-symbol D-143 panel does not support a simple explanation that all losses begin with a wrong direction. Bearish H1/M30 continuation classification is weak, but Root contact frequently produces the intended local reaction before the current trigger chain loses it. Repeated Root/PLAN fan-out amplifies bad directional hypotheses but suppressing duplicates alone remains far below the `>=50%` win-rate objective.

Therefore the next evidence gate is D-144 exact tick barrier measurement. The decisive table will be:

| Stage | Same-dir 1R WR | Same-dir 1.5R WR | Same-dir 2R WR | Flipped 1R WR |
|---|---:|---:|---:|---:|
| ROOT_CONTACT | ? | ? | ? | ? |
| SWEEP | ? | ? | ? | ? |
| CHOCH | ? | ? | ? | ? |
| FVG | ? | ? | ? | ? |
| ACTUAL_FILL | ? | ? | ? | ? |

No strategy redesign occurs until this table is measured across the same six-symbol panel and checked by symbol/month/direction.

---

## Current runner-extension research state — D-145

GOLD 2025 D-144 established that current actual Fill is not equivalent to a 27% directional signal when standardized to a 1R objective. The same 51 continuation fills produced a 58.82% exact +1R-before-SL hit rate, while +2R fell to 39.22%.

This is **not** authority for a 1R TP. The project objective remains a strategy with `>=50%` win rate while preserving meaningful reward greater than 1R. The current research question is therefore the conditional continuation mechanism:

> after the same filled entry has proven itself by reaching +1R, which causally-known market background and newly formed structure distinguish 2R+ delivery from 1R exhaustion?

Pre-registered descriptive axes for D-145:

```text
HTF directional maturity / remaining structural room
current M30 net directional advance
current M30 same-side progression
current M30 leg expansion / contraction
protected-break churn
selected-FVG -> Fill maximum pre-fill displacement
selected-FVG -> Fill adverse retrace
Fill -> first +1R time and pre-1R MAE
new H1/M30/M1 same-direction vs opposite structure events after Fill
current M1 state at +1R
```

No axis has a frozen trading threshold. Generalization requires the qualitative relationship to survive multiple independent cuts.
