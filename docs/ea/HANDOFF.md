# EA Development Handoff

Last updated: 2026-08-20
Repository base checked before this update: `418471c7a0c9bc9e45bb075f43e1d726daef4ebf`
Status: D-135A CONTROL PRESERVED / D-142A PARITY PASS / D-143 SIX-SYMBOL FRONT-END AUDIT ANALYZED / D-144 EXACT-TICK BARRIER AUDIT PREPARED
Current phase: **REACTION / ENTRY BARRIER AUDIT** — D-144 `1.92R1L6` exact-tick shadow comparison of ROOT_CONTACT → SWEEP → CHOCH → FVG → ACTUAL_FILL; strategy authority unchanged
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


## D-142A validation and six-symbol result

D-142A passed its GOLD January audit OFF/ON parity gate. The two main ledgers were byte-identical, and stage identity/timing plus forward-label/right-censor accounting matched.

The first 2025 contrast panel used:

```text
BTCUSD
CADJPY
GBPCAD
GOLD
SILVER
USDJPY
```

Key front-end findings now control the next research step:

```text
MAP snapshots = 35,284
PLAN = 7,589
ROOT_CONTACT = 4,809
SWEEP = 3,753
CHOCH = 1,746
FVG = 1,550
ACTUAL_FILL = 519
```

Continuation timing from the same panel:

```text
owner start -> Root causal structure median:
LONG  ~39.5h
SHORT ~48.5h

PLAN -> Root contact median:
LONG  ~6.5h
SHORT ~9.0h

owner age at Root contact median:
LONG  ~59h
SHORT ~73h
```

For 4,809 PLAN/contact pairs, owner ID, active-map TF, H1 state, M30 state, and scenario direction remained unchanged from PLAN to contact. The warning is therefore not a trivial stale-plan-after-map-flip bug.

However, H1 persistent-map direction showed an inverse 24h relationship on all six symbols: the raw 24h return after H1-LONG states was lower than after H1-SHORT states. Across 60 comparable symbol-month blocks, 42 (70%) showed the same inverse ordering. H1 mature direction is therefore a priority causal suspect, not yet a strategy veto.

Root contact itself recovered local directional response: continuation 24h direction correctness moved from approximately 53.3% LONG / 38.7% SHORT at PLAN to 54.5% LONG / 49.5% SHORT at contact, with positive mean signed 24h moves for both directions. This raises the possibility that Root reaction contains local information while the inherited higher-timeframe trend/objective interpretation is wrong or stale.

The user objective for the eventual strategy is **>=50% win rate**. Research must therefore investigate the direction-selection architecture itself, not stop after filtering a subset of losses.


## D-143 six-symbol front-end result — analyzed

D-143 unified ledgers for `BTCUSD / CADJPY / GBPCAD / GOLD / SILVER / USDJPY` were analyzed from structure formation through final fills. Main findings:

```text
PLAN -> Root Contact is intentionally a pullback:
  LONG opposite-direction move before contact = 99.66%
  SHORT opposite-direction move before contact = 99.95%

H1 continuation BOS, 24h same-direction correctness:
  LONG  = 55.2% / mean signed +0.131%
  SHORT = 38.9% / mean signed -0.255%

M30 continuation BOS, 24h same-direction correctness:
  LONG  = 53.5% / mean signed +0.095%
  SHORT = 40.1% / mean signed -0.219%

Root Contact, 24h same-direction correctness:
  LONG  = 54.5% / mean signed +0.139%
  SHORT = 49.5% / mean signed +0.120%
```

The key result is not simply that the map is wrong. Even eventual losing trades often react correctly from the Root first: at 4h after Root Contact, `74.6%` of LONG losses and `70.2%` of SHORT losses were still moving in the scenario direction. By CHoCH, those same losing cohorts were only `37.9%` LONG / `33.7%` SHORT in the scenario direction.

The front end also fans one directional hypothesis into repeated exposure. Among SHORT structure events that produced at least two actual trades, `36` events produced `88` trades with only `2` wins (`2.27%`). Restricting to one trade per event still does not approach the user's `>=50%` win-rate objective, so simple duplicate suppression is not treated as the solution.

A separate lifecycle inconsistency was observed: `49` continuation contacts had a frozen PLAN direction that no longer matched the current highest map direction; `7` reached actual trades and all `7` lost. This remains a specific authority-survival audit item, not the explanation for the whole loss distribution.

Static front-end causal features alone did not reveal a robust `50%` winner subset. The next measurement therefore standardizes the outcome geometry rather than adding a filter.

## D-144 exact-tick measurement contract

D-144 keeps the D-143 unified ledger and adds zero-authority tick-first-hit virtual outcomes at:

```text
ROOT_CONTACT
SWEEP
CHOCH
FVG
ACTUAL_FILL
```

For stage-to-stage comparison, `1R` is frozen once on the first causally actionable tick after Root Contact using the existing baseline `ROOT_OB_DISTAL_20` geometry. The same absolute R distance is reused at Sweep/CHoCH/FVG so information decay is not confused with a changing volatility or stop scale.

Each stage creates SAME_DIRECTION and FLIPPED_DIRECTION shadow entries and records exact tick ordering for:

```text
+1.0R vs -1R
+1.5R vs -1R
+2.0R vs -1R
```

ACTUAL_FILL is measured separately with the actual `fill_price -> normalized_sl` distance as 1R. Exact fill barriers are emitted only when the fill is observed with zero whole-second lag; otherwise the audit records a skip rather than reconstructing missed ticks.

No D-144 result may authorize or reject a trade. `2021` remains untouched.

## D-143 next instrumentation

D-143 does not change strategy authority. It adds shadow evidence for:

```text
H1/M30 INITIAL_BOS
H1/M30 continuation BOS
H1/M30 PROTECTED_BREAK
hourly active MAP state
all created H1/M30/M15 Roots
PLAN
all physical Root contacts, including NO_PREPLAN
preplanned ROOT_CONTACT
existing Sweep / CHoCH / FVG / Fill identities
```

The audit freezes owner age, latest same-direction BOS age, latest protected update/break timing, Root creation/origin timing, H1/M30 context at Root creation, compatible Root ordinal under each owner, PLAN ordinal, and Root-create/PLAN/contact delays. 15m/1h/4h/24h forward return/MFE/MAE remain shadow labels.

Logging is unified: strategy rows and `EDGE_AUDIT_*` rows share **one `InpEventCsvFile`**. There is no separate Edge Audit CSV input. Audit OFF/ON parity compares the unified ledgers after removing `EDGE_AUDIT_*` rows.

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

## D-142A EDGE_AUDIT_V1 prepared

Prepared build:

```text
1.92R1L4
BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW
strategy semantics = D134_EXECUTION_CORE_UNCHANGED
audit authority = NONE
```

D-142A intentionally implements only the first measurement layer:

```text
hourly highest-MAP state
PLAN
ROOT_CONTACT
SWEEP
CHOCH
FVG
ACTUAL_FILL identity snapshot
```

For MAP through FVG it records 15m / 1h / 4h / 24h signed forward return, MFE, and MAE from subsequent closed M1 bars. Exact fill-time virtual 1R/2R/3R barriers are deferred to D-142B until this first instrumentation build proves zero strategy impact.

Full contract: `docs/ea/EDGE_AUDIT_V1.md`.

Validation gate:

```text
MetaEditor compile = 0 errors
audit OFF and audit ON same fixture
main strategy path = identical
only audit ON creates separate audit CSV
```

## EDGE_AUDIT_V1 — full research target after D-142A parity

D-142A is the current prepared implementation and is intentionally narrower. The items below describe the eventual full audit family. D-142B must not be implemented until D-142A compiles and proves audit-OFF/audit-ON strategy parity.

Every audit phase must remain diagnostic/shadow-only and must not authorize or reject trades differently.

### Checkpoints

Record immutable research snapshots at:

```text
MAP hourly state
PLAN
ROOT_CONTACT
SWEEP_ACCEPTED
CHOCH_ACCEPTED
FVG_SELECTED
ACTUAL_FILL
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

### D-142B deferred — standardized virtual barriers

**Not implemented in D-142A.** Only after D-142A OFF/ON parity passes, D-142B may shadow-test at the actual fill:

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

Use Strategy Tester tick ordering so same-bar barrier ambiguity is not reconstructed from OHLC. D-142A does not perform this tick-level virtual test.

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

1. Apply D-143 `1.92R1L5` and compile with 0 errors.
2. Run a short GOLD January fixture with audit OFF and ON, using one unique event filename per run.
3. Compare unified ledgers after excluding `EDGE_AUDIT_*`; any remaining strategy-row difference invalidates D-143.
4. Inspect D-143 structure/Root/PLAN/contact joins and forward-label completeness.
5. If parity passes, re-run the six-symbol 2025 panel with audit ON; only **one CSV per symbol** is required.
6. Analyze direction formation first: INITIAL_BOS → continuation BOS/PB → owner persistence → Root ordinal/age → PLAN → physical contact.
7. Only after the front-end direction/Root relationship is understood should CHoCH-reference or exact-fill barrier variants resume.
8. Keep 2021 untouched.

---

## D-144 GOLD finding -> D-145 runner-context transition

The first exact-tick D-144 run was completed on GOLD 2025 only because the multi-stage virtual barrier fan-out increased tester wall time by roughly 9x. The event file itself grew by only about 15%, so the dominant cost is the per-tick tracker population rather than CSV bytes alone.

GOLD continuation actual fills:

```text
51 fills
current structural-TP winners = 14 / 51 = 27.45%
exact +1R before -1R = 30 / 51 = 58.82%
exact +1.5R before -1R = 25 / 51 = 49.02%
exact +2R before -1R = 20 / 51 = 39.22%
```

Direction split at +1R:

```text
LONG  = 21 / 35 = 60.00%
SHORT =  9 / 16 = 56.25%
```

Of the 37 continuation trades that eventually lost under the current structural objective, 16 had first reached +1R, 11 had reached +1.5R, and 7 had reached +2R. Therefore the next question is not a fixed-R optimization problem. It is why a valid filled trade sometimes exhausts near 1R and sometimes develops into a 2R+ runner.

Current phase is **D-145 RUNNER MARKET-CONTEXT AUDIT**.

D-145 removes the expensive Root/Sweep/CHoCH/FVG mirror barrier population and the already-completed D-143 front-end forward labels. Only:

```text
selected-FVG -> fill pre-fill displacement tracker
actual filled trade runner tracker
```

remain tick-active.

Two causal snapshots are recorded:

```text
A. ACTUAL_FILL market background
B. FIRST +1R market/continuation state
```

Exact outcomes remain observational only:

```text
1R before SL
2R before SL
3R before SL
structural TP before SL
```

The research objective is to identify structural mechanisms whose relationship to runner extension survives direction, month, symbol, and later periods. Do not choose an R threshold from pooled hit-rate optimization.

`2021 = KEEP UNTOUCHED`.
