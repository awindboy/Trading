# V9 Development Handoff

<!-- V10_TRANSITION_NOTICE_START -->
> **V9 HANDOFF CLOSED — 2026-09-16**
> This file preserves the final V9 handoff state. Active research resumes from `../v10/HANDOFF_V10.md`.
> Transition rationale and the exact V9 stopping point are recorded in `V9_RESEARCH_CLOSURE_AND_V10_TRANSITION_20260916.md`.
<!-- V10_TRANSITION_NOTICE_END -->


Last updated: `2026-09-16`
Status: `FINAL V9 HANDOFF / FROZEN HISTORICAL CONTROL / V10 SUCCESSOR ACTIVE`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`

## 1. Resume point

Read `AGENTS_V9.md` and follow its exact resume order.

Do not return to broad entry-feature mining.
Do not alter the frozen prototype from consumed-data terminal research.

Two lanes remain separate:

```text
A. execution lane
frozen BASE prototype -> EA R1 -> forward demo

B. strategy-research lane
terminal literal-oracle ledger -> causal state-table replication -> actual-tick validation if earned
```

## 2. Frozen prototype authority

Unchanged:

- H1/H4 causal 2-left / 2-right liquidity;
- tick-native H4 Arrival chronology;
- PRIMARY_ACTIVE / CHALLENGED Grammar;
- nearest active opposite H1 structural Hard SL;
- previous-completed H4 Wilder ATR180;
- `ERA_RISK <= 4`;
- ANCHOR / CONTINUATION role semantics;
- no fixed TP, SHORT ban, Child-count cap, session/day/hour filter, or duration timeout.

The user-requested `ALL_TO_CHALLENGE` ledger below is a terminal-research comparator only.

## 3. Current actual-tick terminal research ledger

Uploaded tester:

```text
management=ALL_TO_CHALLENGE
700 closed Children
PnL +6,973.87
PF 1.533
DD 1,700.62
```

Common H4-covered research cohort:

```text
693 Children
191 routes
BASE +7,210.31
PF 1.5655
DD 1,700.62
```

Literal oracle:

```text
TRUE LAST ACCEPTED CHILD
-> first completed opposite-color H4 HA after that Child
-> close all surviving Children at H4_FINALIZED Bid/Ask
```

Correct current denominator:

```text
157 Oracle routes
ORACLE +19,827.81
PF 3.6176
DD 856.81
BASE -> ORACLE opportunity +12,617.50
```

The prior `156` transition-HA1 oracle missed one route whose final Child occurred inside an already-opposite NHA episode.

## 4. Main research discoveries

### Cycle / recovery

`CycleMin` survives the actual-tick ledger change.
Post-HA recovery confirmation improves classification but waiting +1/+2 completed H4 loses exit economics.

### Position damage

Loss depth is more useful than losing-Child count.
A deeply underwater surviving Child makes an opposite HA more economically meaningful.
Observed thresholds are consumed-data diagnostics only.

### PHA / NHA

PHA = contiguous primary-color HA run immediately before HA1.
NHA = contiguous opposite-color run beginning at HA1.

Useful PHA/NHA state is primarily:

```text
NHA close penetration into prior PHA progress
NHA opposite body accumulation relative to PHA
```

Raw NHA high-low range is weaker.

### Historical state-family rebuild

The strongest robust raw route-relative coordinate is same-side H4 participation loss between opposite-HA opportunities.

Current strongest conceptual decomposition:

```text
same-side participation deteriorates
+ opposite structural pressure gains
+ survived-reversal cycle matures
+ current opposite delivery becomes strong
```

## 5. Current repeat-state benchmarks

Best discrimination pair:

```text
SAME_PARTICIPATION_LOSS + RESILIENT_PRESSURE

AUC 2025 0.768
AUC 2026 0.730
mean 0.749
```

Observed consumed-data economic best:

```text
SAME_PARTICIPATION_LOSS
+ OPP_PRESSURE_GAIN
+ CYCLE_MIN
+ RESILIENT_PRESSURE

2025-2026:
BASE +5,307.95
CANDIDATE +9,528.95
ORACLE +16,476.18
BASE delta +4,221.00
Oracle recovery 37.79%
PF 2.103
DD 1,529.50

EXACT 23 / 99
EARLY 8
LATE 5
MISS 63
FALSE 1
```

There are `43` 2025-2026 Oracle routes where repeat-cycle state is available; the observed best matches `23 / 43` exactly.

## 6. Critical caution

The observed best combination was selected after screening consumed data.

Nested prior-only combination selection:

```text
2025 choose combination from 2024
2026 choose combination from 2024-2025
```

produced only:

```text
PnL +6,064.84
BASE delta +756.89
Oracle recovery 6.78%
PF 1.642
DD 2,344.84
```

Therefore do **not** promote the `+4,221` combination as a live rule.

The main open question is whether the four-state structure is a stable representation even though operating/combination selection is unstable.

## 7. Next exact research goal

Follow:

`V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STATE_TABLE_STABILITY_20260916.md`

Required work:

1. route-level oracle-regret table for the observed repeat-state best;
2. causal reconstruction of every repeat-state EARLY route;
3. explain remaining repeat-cycle Oracle misses;
4. stabilize representation / operating point without test-year combination selection;
5. separately solve FIRST-HA1 routes where no CycleMin exists;
6. preserve exact actual-tick Bid/Ask chronology;
7. only after stability, evaluate promotion through actual-tick EA and forward demo.

## 8. Result package

Current result folder:

`docs/ea/v9/results/terminal_state_table_20260916/`

Primary files:

- `ORACLE_LITERAL_ROUTE_ANSWER_SHEET_157.csv`
- `ORACLE_LITERAL_COMMON_693_TRADES.csv`
- `HA1_STATE_EVENTS.csv`
- `NHA_CAUSAL_STATE_EVENTS.csv`
- `REPEAT_STATE_COMBINATION_SUMMARY.csv`
- `REPEAT_STATE_COMBINATION_AUC_SCREEN.csv`
- `TOP_REPEAT_STATE_COMBO_CHILD_LEDGER_2025_2026.csv`
- `TOP_REPEAT_STATE_COMBO_ROUTE_DECISIONS_2025_2026.csv`
- `NESTED_PRIOR_ONLY_COMBO_SELECTION_BY_YEAR.csv`
- `SUMMARY_METRICS_20260916.csv`

All historical periods are consumed.
