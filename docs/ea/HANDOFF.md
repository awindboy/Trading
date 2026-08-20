# EA Development Handoff

Last updated: 2026-08-20
Repository base checked before this update: `2ce911297ea2f5b8d26f0ba78d2ac132445ac0a8`
Status: D-135A / BUILD 1.91 CONTROL PRESERVED / REGIME RESEARCH V1 FROZEN BUT DEPRIORITIZED / 2025 18-SYMBOL NO-GATE BASE-EDGE WARNING
Current phase: **BASE EDGE AUDIT** — prove whether the baseline signal has predictive edge before any further regime promotion or threshold research
2021 status: **KEEP UNTOUCHED**
Strategy authority: **UNCHANGED**

## Authority

- `AGENTS.md` remains the highest current baseline strategy authority.
- `docs/ea/EA_SPEC.md` remains the deterministic baseline implementation contract.
- `docs/ea/REGIME_RESEARCH_2023_2025.md` remains the historical record of Frozen Regime Research V1 discovery, direct validation, and 2022 OOS.
- `docs/ea/BASE_EDGE_AUDIT_2025.md` is the current cross-symbol base-edge evidence and the research plan that now controls the next analytical phase.
- `docs/ea/STRATEGY_RESEARCH_STATE.md` is the compact current research-state summary.
- `docs/ea/TEST_RESULTS.md` is the execution/backtest evidence ledger.
- `docs/ea/BACKLOG.md` is the active work queue.

No finding in the 2025 cross-symbol study changes `AGENTS.md` or `EA_SPEC.md` by itself.

## Current deterministic control

The baseline chain remains:

```text
H1/M30 map
-> eligible HTF Root OB
-> Root contact
-> direction-compatible M1 liquidity Sweep
-> later M1 protected-break CHoCH
-> causal fresh M1 FVG
-> widest eligible FVG
-> first retest Entry
-> contributor-merged SL/objective geometry
-> hedging same-direction execution
-> pending/fill/cancel/close reconciliation
```

Current control properties remain:

```text
SL = ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB = baseline Root recognizers
PD Array = context/reference only
same-direction independent add-ons = allowed on hedging accounts
opposite-direction coexistence = blocked
```

## Frozen Regime Research V1 remains preserved

The frozen research state is still:

`M30_CLEAN_PERSISTENT_EXPANDING`

```text
scope = EXTERNAL_CONTINUATION
snapshot = baseline-equivalent scenario PLAN freeze
latest 12 confirmed M30 waves with available_at <= PLAN freeze

progression >= 2/3
protected-break count in the same 12-wave span <= 1

leg_expansion_ratio > 1.0

leg_expansion_ratio =
mean(abs(last 4 M30 wave-to-wave legs))
/
mean(abs(previous 4 M30 wave-to-wave legs))
```

Historical direct evidence remains valid:

```text
2023–2025 Expansion direct:
24 trades / 13 wins
+49.797314R
mean +2.074888R/trade
Max DD -5.173397R
longest losing streak 5

2022 first sealed OOS:
6 trades / 1 win
+0.994756R
mean +0.165793R/trade
Max DD -3.012334R
longest losing streak 3
PASS under the pre-registered contract
```

This evidence is not deleted or reinterpreted.

However, **Regime V1 promotion is paused** because the new cross-symbol NO-GATE evidence challenges the prior implicit assumption that the underlying baseline continuation signal already has a generally positive edge.

Do not change the frozen V1 formula or thresholds.

## 2025 18-symbol NO-GATE cross-symbol run

Source bundle analyzed directly:

```text
ALL.zip
SHA-256 = 9408fd91c70a2a75e55888f43fa915652cd5b3b24b10415b536b49d74a9ea6eb

18 symbols:
BTCUSD
CADCHF
CADJPY
CHFJPY
EURCAD
EURCHF
EURGBP
EURJPY
EURUSD
GBPCAD
GBPCHF
GBPJPY
GBPUSD
GOLD
SILVER
USDCAD
USDCHF
USDJPY
```

Common tester identity:

```text
build = 1.92R1L3
phase = REGIME_RESEARCH_V1_MULTI_SYMBOL_RISK_SIZING
regime_mode = BASELINE_NO_REGIME_GATE
position_sizing_mode = FIXED_RISK_MONEY
fixed_risk_money = 100 USD
SL model = ROOT_OB_DISTAL_20
strategy semantics = D134_EXECUTION_CORE_UNCHANGED
```

Aggregate execution funnel:

```text
PLANs = 22,272
execution geometry ready = 1,957
orders accepted = 1,681
positions filled = 1,477
positions closed = 1,463
pending cancellations = 199
cancel rejected = 3
execution divergences = 8
tester-end active execution = 17
tester-end open filled positions = 14
```

Raw 18-symbol closed-trade result:

```text
1,463 trades
246 TP
16.81% win rate
-418.221912R
mean -0.285866R/trade
R PF ≈ 0.6686
```

This raw panel is **not final strategy evidence** because five symbol-years contain execution divergence.

## Execution-divergence split

Five symbol-years are contaminated:

```text
EURCAD
EURGBP
GBPJPY
GBPUSD
USDCHF
```

The eight divergences split into two defect classes.

### A. Recoverable pending cancel rejected; stale order later filled — 3

```text
EURGBP
2025-02-03 cancel rejected
retcode 10018 / Market closed
stale pending filled 2025-03-06

GBPUSD
2025-02-03 cancel rejected
retcode 10018 / Market closed
stale pending filled 2025-02-04

USDCHF
2025-07-28 cancel rejected
retcode 10018 / Market closed
stale pending filled later the same day
```

Required future behavior remains:

```text
strategy cancellation remains required
+ exact broker pending still live
+ recoverable cancel rejection

-> keep exact ticket in managed working set
-> keep exposure lock
-> retry cancellation later
-> terminalize only after cancel/fill proof
```

### B. Pending disappeared without fill/cancel proof — 5

Observed:

```text
EURCAD order 42   — 2025-04-07
GBPJPY order 144  — 2025-07-29
GBPUSD order 130  — 2025-08-14
GBPJPY order 224  — 2025-11-11
GBPUSD order 213  — 2025-12-22
```

Do not guess the root cause.

Required investigation:

```text
current order set
vs order history
vs deal history
vs position state
using exact order/position identity
```

A contaminated symbol-year must be re-run after the lifecycle fix. Do not repair it by deleting one divergent trade offline because divergence can change later exposure authorization.

## Divergence-free 13-symbol base-edge panel

The divergence-free symbols are:

```text
BTCUSD
CADCHF
CADJPY
CHFJPY
EURCHF
EURJPY
EURUSD
GBPCAD
GBPCHF
GOLD
SILVER
USDCAD
USDJPY
```

All-scope closed result:

```text
1,023 trades
187 wins
18.28%
-193.184127R
mean -0.188841R/trade
R PF ≈ 0.7768
```

Continuation only:

```text
901 trades
165 wins
18.31%
-179.573032R
mean -0.199304R/trade
R PF ≈ 0.7637
```

Reversal only:

```text
122 trades
22 wins
18.03%
-13.611095R
mean -0.111566R/trade
R PF ≈ 0.8714
```

The continuation weakness survives complete removal of all five execution-divergent symbol-years.

## Execution is not the main explanation

To separate strategy signal from broker realism, the 901 divergence-free continuation trades were rescored using only the strategy-planned barriers:

```text
TP first -> +planned R
SL first -> -1R
```

This removes the economic effect of:

```text
fill slippage
SL/TP overshoot
swap
money sizing granularity
```

Result:

```text
901 trades
planned-barrier total = -166.492129R
mean = -0.184786R/trade
```

Therefore the large negative result already exists at the strategy-planned TP/SL level.

Fixing broker lifecycle defects is required for execution integrity, but **will not by itself repair baseline expectancy**.

## Stylized barrier-null diagnostic

For a zero-drift continuous barrier process with 1R stop distance and a `planned_R` target:

```text
P(TP first) = 1 / (1 + planned_R)
```

This is only a diagnostic null. It is not a full market model because real markets have drift, volatility clustering, serial dependence, sessions, and cross-symbol correlation.

Applied trade-by-trade to the 901 divergence-free continuation trades:

```text
expected TP count under stylized null = 205.7306
actual TP count = 165

expected TP rate = 22.8336%
actual TP rate = 18.3130%
```

Under an independence-only Poisson-binomial calculation:

```text
P(X <= 165) ≈ 0.0003157
```

Do not treat that p-value as final proof because trade independence is false. The important result is that the baseline does not even clear this first weak null diagnostic.

## Direction split — main warning

Divergence-free continuation:

### LONG

```text
460 trades
101 wins
actual TP rate = 21.9565%
stylized-null TP rate = 23.0821%

planned-barrier total = -4.181063R
planned-barrier mean = -0.009089R/trade

canonical realized-price R = -13.361419R
```

Interpretation:

```text
LONG edge is not demonstrated.
The observed result is close to the weak null benchmark.
```

### SHORT

```text
441 trades
64 wins
actual TP rate = 14.5125%
stylized-null TP rate = 22.5744%

planned-barrier total = -162.311067R
planned-barrier mean = -0.368052R/trade

canonical realized-price R = -166.211613R
```

Independence-only Poisson-binomial diagnostic:

```text
expected TP count = 99.5530
actual TP count = 64
P(X <= 64) ≈ 0.00000603
```

Interpretation:

> The strongest current base-edge warning is bearish continuation.  
> In 2025 cross-symbol data it is not merely weak; it materially underperforms the first stylized barrier null.

This is a research finding, not a permanent `NO SHORT` rule.

## H1 map split

Continuation trades by H1 state at PLAN freeze:

| H1 state | Trades | Wins | Actual TP rate | Null TP rate | Planned-barrier R | Canonical R |
|---|---:|---:|---:|---:|---:|---:|
| BULLISH | 355 | 80 | 22.54% | 23.65% | -1.4545R | -8.6640R |
| BEARISH | 329 | 46 | 13.98% | 22.78% | -139.8579R | -141.9049R |
| TRANSITION | 217 | 39 | 17.97% | 21.58% | -25.1797R | -29.0041R |

The mature H1 bearish continuation path is the dominant failure cluster.

Again, do not create a permanent bearish veto from one year. First determine whether this is:

```text
market-regime dependence
direction/map implementation problem
trigger-timing problem
or a genuinely non-predictive market-structure assumption
```

## Planned-R bins

Divergence-free continuation:

| Planned R | Trades | Wins | Actual TP rate | Null TP rate | Planned-barrier R |
|---|---:|---:|---:|---:|---:|
| 1–2R | 217 | 68 | 31.34% | 40.89% | -47.9764R |
| 2–4R | 251 | 53 | 21.12% | 26.16% | -44.6526R |
| 4–8R | 247 | 31 | 12.55% | 15.12% | -41.7568R |
| 8–16R | 137 | 13 | 9.49% | 8.68% | +16.8937R |
| 16R+ | 49 | 0 | 0.00% | 4.30% | -49.0000R |

The problem is not only extreme RR. Ordinary 1–8R setups also underperform the stylized null.

The 16R+ result remains a structural research warning, not an authorized threshold:

```text
49 divergence-free continuation trades
0 TP
canonical result ≈ -51.58R
```

Do not add `planned_R < 16` to the baseline from this 2025 observation.

## Per-symbol divergence-free continuation

| Symbol | Trades | Wins | Actual TP rate | Null TP rate | Canonical R |
|---|---:|---:|---:|---:|---:|
| BTCUSD | 112 | 28 | 25.00% | 22.37% | +15.6835R |
| CADCHF | 32 | 4 | 12.50% | 22.39% | -12.8645R |
| CADJPY | 111 | 9 | 8.11% | 21.00% | -61.1590R |
| CHFJPY | 66 | 15 | 22.73% | 23.17% | -9.5899R |
| EURCHF | 42 | 8 | 19.05% | 27.47% | -20.9184R |
| EURJPY | 76 | 15 | 19.74% | 21.66% | -10.5871R |
| EURUSD | 82 | 16 | 19.51% | 21.48% | -9.7424R |
| GBPCAD | 68 | 15 | 22.06% | 23.03% | +16.9811R |
| GBPCHF | 56 | 7 | 12.50% | 23.47% | -32.0104R |
| GOLD | 51 | 14 | 27.45% | 21.10% | +15.9365R |
| SILVER | 45 | 4 | 8.89% | 20.86% | -30.4628R |
| USDCAD | 79 | 14 | 17.72% | 25.31% | -24.4038R |
| USDJPY | 81 | 16 | 19.75% | 25.11% | -16.4358R |

Breadth:

```text
positive continuation canonical R = 3 / 13 symbols
negative continuation canonical R = 10 / 13 symbols
```

No single bad symbol explains the pooled failure.

## Trigger-chain timing warning

For the 901 divergence-free continuation trades that eventually closed:

| Stage interval | Median | 90th percentile | Maximum |
|---|---:|---:|---:|
| PLAN -> Root contact | 10.73h | 88.97h | 683.50h |
| Root contact -> Sweep | 2.33h | 11.65h | 81.45h |
| Sweep -> CHoCH | 2.03h | 13.07h | 100.02h |
| FVG selection -> Fill | 0.85h | 15.63h | 142.66h |

This does not justify an arbitrary time cutoff.

It does show that the current deterministic chain can connect events that are many hours or days apart.

## Code-level directional audit

A targeted audit of the current EA found no simple LONG/SHORT sign inversion in the main path.

The main branches are mirror-defined:

```text
structure protected break
bullish/bearish FVG geometry
LONG FVG-top / SHORT FVG-bottom Entry
Root-distal outward SL
LONG/SHORT objective reward
BUY_LIMIT / SELL_LIMIT request
```

Therefore the current SHORT failure should not be dismissed as an obvious one-line sign bug.

Further code audit remains warranted because a large directional asymmetry exists empirically.

## D-127 causal-looseness concern

The current D-127 baseline intentionally simplified the trigger layer.

The M1 Sweep detector snapshots already-known active liquidity and has no:

```text
Root filter
scenario filter
distance filter
family quality/ranking filter
child filter
```

The scenario then accepts the first direction-compatible post-contact Sweep.

Current audit rows explicitly record:

```text
rule=SEQUENCE_ONLY
root_reintersection=false
family_whitelist=false
child_required=false
choch_reference_freeze=false
```

CHoCH acceptance is also sequence-only after Sweep and does not require:

```text
opposite M1 trend at Sweep
frozen protected reference at Sweep
additional CHoCH strength/quality
Root reintersection
```

This was an intentional simplification, not an implementation accident.

The new cross-symbol result creates a legitimate research question:

> Did the deterministic simplification remove nuisance filters, or did it remove the causal ownership that made a human-recognized Root reaction meaningful?

Do not answer by re-adding all old filters at once.

## Current research decision

The project now pauses:

```text
Regime threshold expansion
Regime V1 promotion
2021 final confirmation
strategy-quality score work
symbol-specific tuning
```

and moves to:

`BASE EDGE AUDIT`

Frozen Regime Research V1 is preserved unchanged as historical research evidence.

The priority is to determine:

```text
1. whether map direction itself predicts future price;
2. whether Root contact adds information;
3. whether Sweep adds information;
4. whether CHoCH adds or destroys information;
5. whether FVG/retest Entry improves or degrades timing;
6. whether the main defect is direction, Entry, SL, or structural TP;
7. whether simple benchmark strategies beat the Mentor signal under equal risk rules.
```

## EDGE_AUDIT_V1 — required next harness

The next code change should be a diagnostic/shadow harness, not a strategy change.

It must not authorize or reject trades differently.

### Checkpoints

Record immutable research snapshots at:

```text
PLAN
ROOT_CONTACT
SWEEP_ACCEPTED
CHOCH_ACCEPTED
FVG_SELECTED
ENTRY/FILL
```

For each checkpoint retain:

```text
symbol
timestamp
scenario_id
scope
direction
active map TF
H1/M30 trend and owner IDs
Root ID/TF/bounds
relevant Sweep identity
CHoCH broken swing identity
selected FVG identity/bounds
strategy Entry/SL/TP when available
```

### Forward labels

After the future horizon has actually elapsed, research-only labeling may record:

```text
15m signed return
1h signed return
4h signed return
24h signed return

MFE
MAE
```

These labels are hindsight research outputs only and must never feed same-run order authorization.

### Standardized virtual barriers

At the real strategy Entry, shadow-test:

```text
same direction:
1R TP / 1R SL
2R TP / 1R SL
3R TP / 1R SL

direction-flipped mirror:
same timestamp
same absolute risk distance
opposite direction
1R / 2R / 3R virtual TP
```

Use tester tick ordering so same-bar barrier ambiguity is not reconstructed from OHLC.

This separates:

```text
direction edge
from
structural objective edge
from
SL geometry
```

### Stage-ablation interpretation

Desired output:

```text
                 LONG        SHORT
MAP                 ?            ?
ROOT CONTACT        ?            ?
SWEEP               ?            ?
CHOCH               ?            ?
FVG                 ?            ?
ENTRY               ?            ?
```

Decision logic:

```text
Map already has no edge
-> fundamental structure/direction hypothesis is unsupported.

Map has edge, later stages lose it
-> trigger/entry timing is degrading the signal.

Entry has edge under standardized exits, structural TP/SL loses
-> geometry/objective design is the main problem.

Only a stable pre-registered regime subset has edge
-> regime research becomes relevant again.
```

## Benchmark requirement

After EDGE_AUDIT_V1 is working, compare against deliberately simple frozen controls on the same symbols/period/risk protocol.

Candidate controls:

```text
deterministic random/time-matched null
simple EMA trend-follow
simple RSI mean-reversion
simple MACD crossover
```

Do not optimize these controls aggressively. Their purpose is to answer:

```text
Does the Mentor pipeline add information beyond cheap/simple baselines?
```

## 2021 policy

2021 remains untouched.

Do not consume it for the old Regime V1 promotion while the base strategy itself is under audit.

If a materially changed strategy emerges from the base-edge study, 2021 is more valuable as a final untouched confirmation for that surviving structure.

## Parallel execution work

Execution integrity still requires:

```text
1. recoverable exact-ticket cancel retry
2. pending-disappeared order/history/deal/position reconciliation
3. terminalize the 2025 entry cohort beyond year-end
4. re-run contaminated symbol-years after the fix
```

Keep these changes isolated from strategy research.

## Do not do

- Do not add a SHORT veto from the 2025 result alone.
- Do not add `planned_R < 16`.
- Do not add MACD/RSI/EMA as Mentor filters merely because they are benchmarked.
- Do not tune D-127 time gaps after looking at winners and losers.
- Do not restore all historical D-126 filters simultaneously.
- Do not modify Frozen Regime V1 thresholds.
- Do not open 2021 yet.
- Do not call an execution-divergent symbol-year final profitability evidence.
- Do not assume complexity implies edge.

## Immediate next actions

1. Preserve current baseline and Frozen Regime V1.
2. Design and implement `EDGE_AUDIT_V1` as logging/shadow-only instrumentation.
3. Validate that the audit harness has zero effect on existing trade identities and economics.
4. Re-run enough 2025 symbols to produce stage-by-stage forward labels and virtual-barrier outcomes.
5. Diagnose LONG and SHORT separately.
6. Only after the base edge location is known, choose a single controlled strategy hypothesis to test.
7. Keep 2021 untouched until that research branch reaches a genuine final-confirmation gate.
