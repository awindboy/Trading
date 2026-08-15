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