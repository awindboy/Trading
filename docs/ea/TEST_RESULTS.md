# EA Test Results

구현 정확성 검증 결과를 아래에 기록한다. 아직 수익성 승인 결과는 없다.

## 2026-08-16 — Authority correction note: Root-primary / optional-child semantics

Status:

```text
AUTHORITY CORRECTION
HISTORICAL TEST COUNTS PRESERVED
AFFECTED PHASES REQUIRE RE-TEST
```

Current required causal order:

```text
pre-existing eligible / unconsumed HTF Root
→ actual HTF Root contact
→ valid Root-reaction liquidity sweep
→ meaningful M1 CHoCH
→ causal M1 FVG
→ widest valid FVG first retest
→ FVG Entry / FVG 20% SL / frozen objective TP
```

Optional side observation:

```text
Root contact
→ post-contact causal child, if any
→ audit/context only
```

D-122 still forbids using a historical pre-contact LTF OB as a post-contact child. D-124 removes child presence, uniqueness, validity, and geometry from trade authorization.

Therefore:

```text
Phase 1.1 structure results
→ remain valid within structure scope

Phase 2 physical liquidity/sweep detector results
→ remain valid within detector scope
→ strategy-authorization ownership/timing still requires Root-based re-audit

Phase 3A HTF Root detection/lifecycle results
→ remain valid within Root-detection scope

Phase 4A H1/M30 map/reversal results
→ remain valid within map scope

Historical Phase 3B child/refinement PASS
→ SUPERSEDED as current strategy-parity evidence

Historical Phase 4B / Phase 4C final-refined-source results
→ old behavior only
→ not current opportunity-frequency evidence
```

All historical records below are intentionally preserved unchanged as test history.

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


## 2026-08-16 — Phase 3B Short Refinement Smoke Test

Status:

```text
PASS — NO_CHILD / fail-closed path
COVERAGE INCOMPLETE — CHILD_CREATED path not exercised
NOT A PROFITABILITY TEST
```

EA:

```text
MentorDeterministicV1EA
repository commit = 72e7e99409a5b12354c1da653308d0e17a9cf471
internal build = 0.40
phase = REFINEMENT_CORE
```

CSV:

```text
event rows = 678
```

Refinement:

```text
REFINEMENT_FROZEN      = 4
REFINEMENT_INVALIDATED = 3
CHILD_CREATED          = 0
CHILD_INVALIDATED      = 0
```

EA stop summary:

```text
roots_created=272
root_price_invalidated=161
root_structure_invalidated=110

children_created=0
children_invalidated=0

refinements_ready=0
refinements_no_child=4
refinements_ambiguous=0
```

Regression:

```text
future available_at                    = 0
same-timestamp MTF order violation     = 0
refinement early-freeze violation      = 0
structure event counts changed         = 0
liquidity event counts changed         = 0
Root runtime event counts changed      = 0
STRUCTURAL_REACTION created            = 0
```

Runtime Root #1:

```text
M15 LONG
root available = 2025-01-06 13:45
root origin = 09:30
parent origin window = 03:30 ~ 09:30
refinement = NO_CHILD
```

Same timestamp contained an M5 bullish BOS,
but its causal source did not satisfy the parent's frozen origin-time relation.

Runtime Root #2:

```text
M15 LONG
root available = 2025-01-07 14:00
root origin = 09:30
parent origin window = 08:15 ~ 09:45
refinement = NO_CHILD
```

Relevant later M5 causal structure did not satisfy the frozen parent origin window.

Conclusion:

```text
The short test supports conservative NO_CHILD behavior.
It does not validate CHILD_CREATED, deepest-child selection,
ambiguity handling, or child invalidation.
```

Required next validation:

```text
extended real-tick run
2025-01-06 ~ 2025-02-01
CHILD_CREATED >= 1 required for final Phase 3B PASS
```

If zero children still occur:

```text
add diagnostic rejection counters first
do not loosen causal rules blindly
```


## 2026-08-16 — Phase 3B Extended Causal Refinement Validation

Status:

```text
PASS — Phase 3B refinement core
NOT A PROFITABILITY TEST
```

EA:

```text
internal build = 0.40
phase = REFINEMENT_CORE
code commit = 72e7e99409a5b12354c1da653308d0e17a9cf471
validation-doc commit = 7c695233eceed2bb69af5e222715657aaa8938f7
```

CSV:

```text
event rows = 6727
```

Refinement:

```text
REFINEMENT_FROZEN = 21
READY = 7
NO_CHILD = 14
AMBIGUOUS = 0

CHILD_CREATED = 7
CHILD_INVALIDATED = 6
```

Child geometry:

```text
M15 = 5
M5 = 2

CONTAINED = 5
EVENT_ADJACENT = 2
```

Automated checks:

```text
missing direct parent = 0
child timeframe not lower than parent = 0
direction mismatch = 0
wrong opposite origin candle = 0
parent/child time causality violation = 0
child origin outside parent window = 0
invalid containment type = 0
CONTAINED geometry mismatch = 0
scenario authority violation = 0
duplicate child ID = 0

invalid PRICE_INVALIDATED geometry = 0
missing parent invalidation propagation = 0

future available_at = 0
same-timestamp MTF order violation = 0
early refinement freeze = 0
```

Lifecycle:

```text
Root:
289 created
167 PRICE_INVALIDATED
120 STRUCTURE_INVALIDATED
2 ACTIVE

Child:
7 created
6 invalidated
1 ACTIVE

active_sources = 3
```

Coverage still not observed:

```text
SHORT child
AMBIGUOUS_FIRST
STOPPED_AMBIGUOUS
multi-level child chain
```

These remain future regression coverage and are not used as a reason
to relax frozen causal rules.

Profitability:

```text
N/A
```

Reason:

```text
No scenario/order layer exists.
```


## 2026-08-16 — Phase 4A H1/M30 Map / Reversal Permission Validation

Status:

```text
PASS — Phase 4A map/reversal core
NOT A PROFITABILITY TEST
```

EA:

```text
repository commit = 400665f8d76e6f4c615a54efa106b5289e59dbf4
internal build = 0.50
phase = MAP_REVERSAL_CORE
```

CSV:

```text
event rows = 8616
execution epoch = 2025-01-06 01:00:05
```

Runtime Phase 4A events:

```text
MAP_STATE = 103
REVERSAL_REFERENCE_SET = 62
REVERSAL_REFERENCE_CLEARED = 3
REVERSAL_REFERENCE_EVENT = 108
REVERSAL_PERMISSION_STATE = 53
```

Runtime map snapshots:

```text
H1 LONG = 86
H1 SHORT = 9
M30 LONG = 3
M30 SHORT = 2
NONE = 3
```

Reference event geometry:

```text
all-history:
CONTINUATION_BODY_BREAK = 289
SWEEP_REJECTION = 240
TOUCH = 1

runtime:
CONTINUATION_BODY_BREAK = 52
SWEEP_REJECTION = 56
```

Permission:

```text
all-history OPEN = 144
all-history CLOSE = 143
tester-end state = OPEN_FOR_SHORT

runtime:
OPEN_FOR_SHORT = 26
OPEN_FOR_LONG = 1
CLOSE continuation = 23
CLOSE owner-change = 3
```

Automated checks:

```text
highest-active-map hierarchy violation = 0
owner set without matching INITIAL_BOS = 0
owner clear without matching PROTECTED_BREAK = 0
direct owner A→B rewrite = 0

reference side / H1 direction mismatch = 0
reference monotonicity violation = 0
same-bar reference self-interaction = 0
reference precedence mismatch = 0
multiple reference events on one H1 bar = 0

permission OPEN direction mismatch = 0
permission OPEN without TOUCH/SWEEP = 0
continuation CLOSE without body-break = 0
permission-origin rewrite while OPEN = 0
permission-origin rewrite on CLOSE = 0

future available_at = 0

Phase 1~3B core event regression = 0
```

Logging-only defect:

```text
Phase 4A bootstrap replay emitted new map/reference events
despite InpLogBootstrapEvents=false.
```

Resolution:

```text
Phase 4B adds map/reference events to bootstrap high-volume suppression.
Final BOOTSTRAP_COMPLETE MAP snapshot remains enabled.
```

Profitability:

```text
N/A
```

Reason:

```text
No order layer exists.
```


## 2026-08-16 — Phase 4B Scenario / Objective Family Validation

Status:

```text
PASS — Phase 4B scenario/objective core
NOT A PROFITABILITY TEST
```

EA:

```text
repository commit = 8e5f0889c0b4e642801fb8718095b37b088c5985
internal build = 0.60
phase = SCENARIO_OBJECTIVE_CORE
```

CSV:

```text
event rows = 7123
```

Scenario:

```text
SCENARIO_PLANNED = 2
SCENARIO_LINEAGE_BOUND = 2
SCENARIO_CANCELED = 2
SCENARIO_REJECTED = 38
PREPLAN_SOURCE_CONTACT = 3
```

Objective family:

```text
OBJECTIVE_CANDIDATE_FROZEN = 9
OBJECTIVE_CANDIDATE_CONSUMED = 9
```

PLAN coverage:

```text
M30-primary EXTERNAL_CONTINUATION LONG = 1
H1-owned EXTERNAL_CONTINUATION LONG = 1

EXTERNAL_REVERSAL = 0
H4_EXTENSION candidate = 0
```

Automated checks:

```text
source outside map = 0
continuation premium/discount violation = 0
owner/direction mismatch = 0
continuation permission violation = 0

future plan-reference M1 close = 0

objective family != EXTERNAL_SWING = 0
wrong side = 0
not direction-ahead = 0
future candidate availability = 0
primary timeframe violation = 0
directional-horizon violation = 0
objective order-index gap = 0
nearest-first order violation = 0
primary horizon mismatch = 0

lineage binding mismatch = 0

PREPLAN-contact lineage later planned = 0

invalid scenario cancellation = 0
```

Ambiguous Root:

```text
SCENARIO_REJECTED reason=AMBIGUOUS_ROOT_LINEAGE = 38
arbitrary candidate fallback = 0
```

Known future regression coverage:

```text
early EXTERNAL_REVERSAL PLAN
H4 objective extension
```

These branches were not relaxed to manufacture coverage.

Logging-only defect:

```text
OBJECTIVE_CANDIDATE_CONSUMED could continue after PLAN cancellation.
```

Resolution:

```text
Phase 4C skips objective-consumption refresh for CANCELED / NO_TRADE PLANs.
```

Profitability:

```text
N/A
```

Reason:

```text
No entry/order layer exists.
```

## 2026-08-16 — D122A Root-Contact / Optional-Child Temporal Validation

Status:

```text
PASS — D122A temporal-causality core within observed child path
REINTERPRETED BY D-124 — child is optional audit/context, not a trade gate
NOT A PROFITABILITY TEST
```

EA:

```text
repository commit = 5693058733b63089ad7e612281ce58a7623c73e3
commit message = EA: D112A version
internal build = 0.80
property version = 1.00
phase = D122A_POST_CONTACT_REFINEMENT_CORE
InpEnableFvgOriginObExperiment = false
```

Uploaded event CSV:

```text
mentor_v1_structure_events(20260816-110812).csv
rows = 7067
observed interval = 2025-01-06 00:00:00 ~ 2025-01-31 23:57:57
execution_epoch_start = 2025-01-06 01:00:05
```

Core counts:

```text
ROOT_WATCH_CREATED = 21
ROOT_CONTACT_OBSERVED = 11
CHILD_CREATED = 1
REFINEMENT READY = 1
CHILD_INVALIDATED = 1

SCENARIO_PLANNED = 0
old Phase4C SOURCE_CONTACT = 0
AUTHORIZED_SWEEP = 0
STRUCTURAL_REACTION strategy authorization = 0
orders/deals = 0
```

Observed child causal sequence:

```text
Root available_at    = 2025-01-14 22:00
Root contact         = 2025-01-15 03:45
child origin         = 2025-01-15 03:55
meaningful M5 low    = 2025-01-15 04:00
wave available       = 2025-01-15 04:15
M5 INITIAL_BOS bar   = 2025-01-15 04:45
child available      = 2025-01-15 04:50
```

Causal checks:

```text
Root contact without prior Root watch = 0
Root contact <= Root.available_at = 0
Root contact before execution epoch = 0
child without Root contact = 0
child origin before Root contact = 0
child available_at <= Root contact = 0
historical pre-contact child authorization = 0
runtime detector/fatal error event in CSV = 0
```

Upstream exact-regression comparison against the preceding
`fvg_origin_ob_experiment=false` control:

```text
WAVE_CONFIRMED               = exact row equality
STRUCTURE_BOS                = exact row equality
STRUCTURE_INITIAL_BOS        = exact row equality
STRUCTURE_PROTECTED_BREAK    = exact row equality
LIQUIDITY_CREATED            = exact row equality
LIQUIDITY_SWEEP              = exact row equality
LIQUIDITY_BODY_DELIVERY      = exact row equality
MAP / REVERSAL events        = exact row equality
ROOT_CREATED/REJECTED/STATE  = exact row equality
```

D-124 interpretation:

```text
11 ROOT_CONTACT_OBSERVED
→ 11 Root-level reaction contexts before later strategy filters

1 CHILD_CREATED
→ one optional post-contact causal observation
→ NOT evidence that only one Root setup survived

10 contacts without a child
→ NOT rejected for missing child
```

The current first-position Entry and SL remain the frozen M1-FVG contract;
child geometry does not alter them.

Profitability:

```text
N/A
```

Reason:

```text
Scenario, strategic sweep, CHoCH, and order authorization were intentionally disabled.
```

## 2026-08-16 — D-124 Root-Primary Consolidation Prepared

Status:

```text
CODE/DOC UPDATE PREPARED
LOCAL COMPILE / STRATEGY TESTER RUN PENDING
```

Target build:

```text
internal build = 0.81
phase = D124_ROOT_PRIMARY_OPTIONAL_CHILD_AUDIT_CORE
```

Acceptance focus:

```text
qualifying Root contact → ROOT_CONTEXT_READY regardless of child
optional child observation may be 0..N
strategy-source child creation = 0
child absence / multiplicity / invalidation cannot veto Root context
scenario/sweep/CHoCH/order remain disabled during isolated smoke
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
