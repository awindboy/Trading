# EA Test Results

구현 정확성 검증 결과를 아래에 기록한다. 아직 수익성 승인 결과는 없다.


## 2026-08-16 — Phase 1.1 Structure / Bootstrap Smoke Test

Status:

```text
PASS — structure/bootstrap implementation scope
NOT A PROFITABILITY TEST
```

EA:

```text
MentorDeterministicV1EA
repository commit = 421a92c90b3a0d6c62a950690436125a60c72d3b
internal build = 0.11
property version = 1.00
```

Tester:

```text
symbol = GOLD
broker = XMGlobal-MT5 12
period = M1
model = Every tick based on real ticks
tester period = 2025-01-06 00:00 ~ 2025-01-08 00:00
magic = 26081601
execution delay = 230 ms
```

History / tick coverage observed:

```text
H4  history begins = 2024-01-02 00:00
H1  history begins = 2024-01-02 01:00
M30 history begins = 2024-01-02 01:00
M15 history begins = 2024-01-02 01:00
M5  history begins = 2024-01-02 01:00
M1  history begins = 2024-01-02 01:00

real ticks begin = 2024-02-06 00:00
```

Execution epoch:

```text
2025-01-06 01:00:05
```

Tester result:

```text
476,672 ticks
2,758 M1 bars generated
initial deposit = 10,000 USD
final balance = 10,000 USD
orders = 0
deals = 0
runtime fatal error = 0
tester = passed
```

Structure-event CSV:

```text
rows = 695

runtime:
WAVE_CONFIRMED               = 252
STRUCTURE_BOS                = 120
STRUCTURE_INITIAL_BOS        = 28
STRUCTURE_PROTECTED_BREAK    = 27
STRUCTURE_STATE              = 27
EXECUTION_EPOCH_START        = 1
```

Automated causal checks:

```text
duplicate event/object id                 = 0
duplicate timeframe/bar structure event   = 0
available_at > observed_at                = 0
same-timestamp MTF order violation         = 0
same-side consecutive confirmed wave       = 0
INITIAL_BOS opposite reference missing     = 0
body-close break violation                 = 0
PROTECTED_BREAK without TRANSITION         = 0
ordinary BOS immediately after break       = 0
```

Bootstrap final structure state:

```text
H4  = TRANSITION
H1  = TRANSITION
M30 = TRANSITION
M15 = BEARISH
```

Known defect found:

```text
InpLogBootstrapEvents=false
but bootstrap PROTECTED_BREAK STRUCTURE_STATE rows = 228
```

Classification:

```text
logging-only
strategy calculation impact = none
```

Resolution:

```text
fixed in Phase 2 by suppressing bootstrap PROTECTED_BREAK STRUCTURE_STATE
while keeping BOOTSTRAP_COMPLETE snapshots
```

Compile note:

```text
Phase 1 build 0.10:
0 errors / 1 warning / 482 ms / AVX2 + FMA3

Phase 1.1 executable successfully ran in Strategy Tester.
The exact Phase 1.1 MetaEditor warning line was not archived,
so warning status is not inferred.
```

Profitability metrics:

```text
N/A
```

Reason:

```text
Phase 1.1 intentionally contains no order layer.
```


## 2026-08-16 — Phase 2 Liquidity / Sweep Smoke Test

Status:

```text
PASS — liquidity/sweep implementation scope
NOT A PROFITABILITY TEST
```

EA:

```text
MentorDeterministicV1EA
repository commit = 2a921a43b4e0ea91f611d0428065f618ff667b6d
runtime internal build = 0.21
property version = 1.00
phase = LIQUIDITY_CORE
```

Event CSV:

```text
rows = 644
```

Runtime structure regression:

```text
WAVE_CONFIRMED            = 252
STRUCTURE_BOS             = 120
STRUCTURE_INITIAL_BOS     = 28
STRUCTURE_PROTECTED_BREAK = 27
```

These counts match the verified Phase 1.1 smoke run.

Liquidity:

```text
LIQUIDITY_CREATED       = 93
LIQUIDITY_SWEEP         = 28
LIQUIDITY_BODY_DELIVERY = 48
```

Runtime EXTERNAL_SWING source reasons:

```text
EXTERNAL_EXTREME_PROMOTION = 51
PROTECTED_PROMOTION        = 42
```

Bootstrap active liquidity:

```text
H4  total=12 external=12 defended=0 reaction=0
H1  total=20 external=19 defended=1 reaction=0
M30 total=31 external=30 defended=1 reaction=0
M15 total=49 external=47 defended=2 reaction=0
```

Automated checks:

```text
duplicate LIQUIDITY_CREATED id     = 0
duplicate pool consumption         = 0
same-bar self-consumption          = 0
physical-sweep rule violation      = 0
body-delivery rule violation       = 0
future available_at                = 0
runtime MTF order violation        = 0
within-TF event order violation    = 0
liquidity detector error event     = 0
```

Sweep penetration:

```text
minimum = 2 ticks
```

Body-delivery penetration:

```text
minimum = 4 ticks
```

Phase 1.1 logging regression:

```text
bootstrap PROTECTED_BREAK STRUCTURE_STATE over-logging
→ resolved
```

DEFENDED_RANGE_EDGE coverage note:

```text
No new defended-range creation/consumption occurred in the short runtime window.
Bootstrap restored:
H1=1, M30=1, M15=2 active defended-range pools.
Static source review confirms the four-wave / overlap / body-contained / H4-block guards.
Continue per-object defended-range regression in later longer tests.
```

STRUCTURAL_REACTION:

```text
0
```

Expected because Root/source ownership is not yet attached in Phase 2.

Compile note:

```text
The Phase 2.0 reference-alias compile errors were fixed in internal build 0.21.
A Strategy Tester executable for build 0.21 produced this CSV.
Exact warning count was not supplied, so warning status is not inferred.
```

Profitability:

```text
N/A
```

Reason:

```text
No order layer exists.
```


## 2026-08-16 — Phase 3A HTF Root OB Core Smoke Test

Status:

```text
PASS — Root core within implemented scope
NOT A PROFITABILITY TEST
```

EA:

```text
MentorDeterministicV1EA
latest compile-fix commit = 2b22d828773f8fb59e09e834dd7ff9a125ad784d
internal build = 0.31
phase = ROOT_CORE
```

Event CSV:

```text
rows = 668
```

Runtime regression counts:

```text
WAVE_CONFIRMED               = 252
STRUCTURE_BOS                = 120
STRUCTURE_INITIAL_BOS        = 28
STRUCTURE_PROTECTED_BREAK    = 27

LIQUIDITY_CREATED            = 93
LIQUIDITY_SWEEP              = 28
LIQUIDITY_BODY_DELIVERY      = 48
```

Root runtime:

```text
ROOT_CREATED      = 2
ROOT_INVALIDATED  = 3
ROOT_REJECTED     = 16
ROOT_STATE        = 3
```

Rejections:

```text
NO_CAUSAL_CORRECTION_OR_MEANINGFUL_WAVE = 13
SESSION_GAP_CROSSED                     = 3
```

Bootstrap Root state:

```text
H1  active = 0
M30 active = 0
M15 active = 2 short
```

Full Root lifecycle summary:

```text
roots_created               = 272
root_price_invalidated      = 161
root_structure_invalidated  = 110
active_roots                = 1

161 + 110 + 1 = 272
```

Automated causal checks:

```text
future available_at                              = 0
invalid Root timeframe                           = 0
wrong opposite-candle colour                     = 0
wrong meaningful-wave side                       = 0
origin outside origin window                     = 0
scenario_authority != false                      = 0
scenario_owner_id != UNBOUND                     = 0
same_session_causal_path != true                 = 0
linked structure event mismatch                  = 0
invalid PRICE_INVALIDATED geometry               = 0
STRUCTURE_INVALIDATED without protected break    = 0
same-bar Root self-invalidation                  = 0
unexpected rejection reason                      = 0
rejection without matching structure event       = 0
Phase 1 structure regression                     = 0
Phase 2 liquidity regression                     = 0
STRUCTURAL_REACTION creation                     = 0
```

Known completeness limitation:

```text
Independent enumeration/completeness of every
"structurally meaningful internal swing" Root context
has not yet been implemented/audited as a separate Root path.
```

Therefore:

```text
Phase 3A core = PASS
Full Root-spec completeness = still open
```

Profitability:

```text
N/A
```

Reason:

```text
Scenario and order layers remain disabled.
```


## Required reporting format

For every significant V1 test record:

- EA version / commit
- symbol
- broker
- account mode if relevant
- tester period
- tester model
- trading period
- H4 history first date
- H1 history first date
- M30 history first date
- M15 history first date
- M5 history first date
- M1 history first date
- H4 active long-horizon liquidity count at READY
- bootstrap READY time / `execution_epoch_start`
- startup source context
- magic number
- sizing mode
- submitted volume
- spread / commission assumptions
- number of strategy-valid signals
- number of submitted orders
- number of execution-infeasible signals
- number of rejected orders
- number of filled trades
- win / loss
- profit factor
- expectancy in R
- max drawdown if available
- protocol violations
- execution divergences
- known implementation defects

Profitability results are invalid if known protocol violations remain.