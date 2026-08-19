# D-135A Long-Run Validation, Regime Research, and 2022 OOS Evidence

Date recorded: 2026-08-20
Repository base checked before this update: `0d9ca2cc72dceb6e982df4700ee83f42a11135af`

This ledger preserves the execution-validation evidence for build 1.91 and the later Regime Research V1 direct-development / first-OOS results. Historical results are retained even when a later test gives a cleaner comparison.

Research calculation convention for the direct runs:

```text
trade R denominator = actual fill to frozen strategy SL
LONG R  = (actual exit - actual fill) / (actual fill - strategy SL)
SHORT R = (actual fill - actual exit) / (strategy SL - actual fill)

year attribution = entry/fill year
trade-sequence Max DD / losing streak = chronological fill-order R sequence
execution-divergent trades = excluded from strategy-performance evidence
```

Late-year positions are allowed to reach their actual terminal exit even if the exit occurs in the next calendar year.

## 1. D-135A 2025 full-year regression

EA identity:

```text
build = 1.91
phase = D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX
SL model = ROOT_OB_DISTAL_20
model = Every tick based on real ticks
period = 2025-01-01 ~ 2025-12-31
```

Uploaded D-135A event CSV:

```text
rows = 234,277
SHA-256 = 1bd119c4d3aea9ab759a24541de71be01d0379fa948927bede2a1dae5b9d7b65
user-reported runtime ≈ 7 minutes 10 seconds
```

D-134 lifecycle parity target and D-135A result:

```text
execution geometry ready = 74
pending accepted = 73
pending canceled = 15
filled = 58
closed = 58
opposite-direction conflict = 1
execution divergence = 0
```

Primary June regression fixture passed:
- the LONG pending around Entry `3388.90` was canceled after Root invalidation;
- the later SHORT around Entry `3397.25` was no longer falsely blocked by the orphan LONG pending.

Secondary November canceled-pending fixture around Entry `4138.03` also received normal broker cancellation.

Canonical Entry/FVG/SL/TP/fill/close economics matched the D-134 baseline. Simultaneous same-direction order ticket numbering could differ because working-set traversal order is not strategy priority.

Classification:

```text
D-135 performance optimization = PASS
D-135A canceled-pending lifecycle hotfix = PASS
2025 D-134 execution lifecycle parity = PASS
2025 execution divergence = 0
```

Performance:

```text
D-134 ≈ 9 hours
D-135A ≈ 7m10s
speedup ≈ 75x
```

## 2. D-135A 2023–2024 two-year run

Uploaded event ledger:

```text
period = 2023-01-01 ~ 2024-12-31
build = 1.91
phase = D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX
rows = 442,722
SHA-256 = 16be6cc44e57dadd9e32250d3e8df9cd1de4e14575a55c0732bc3427a237744e
```

Execution funnel:

```text
execution geometry = 159
pending accepted = 148
filled = 130
closed = 126
normal pending cancel = 17
pending cancel reject = 1
tester-end open positions = 4
tester-end live pending = 1
```

Because the run contains one execution divergence and unfinished tester-end exposure, it is **not a clean final profitability baseline**.

## 3. 2023 versus 2024 preliminary strategy result

Closed-trade research summary:

```text
2023
closed trades = 70
wins = 23
losses = 47
win rate ≈ 32.9%
realized ≈ +44.94R

2024
clean closed trades = 55 after excluding the known divergence trade
wins = 5
realized ≈ -35.56R
```

Continuation-only clean attribution:

```text
2023 EXTERNAL_CONTINUATION ≈ +48.31R
2024 EXTERNAL_CONTINUATION ≈ -28.45R
```

The broad 2024 weakness remains after excluding the single known divergence and cannot be explained by reversal alone.

## 4. Remaining execution edge case discovered in the historical baseline run

Observed scenario:

```text
2023-12-20
LONG pending accepted
Entry = 2029.55
SL = 2026.35
TP = 2047.77

2023-12-22
strategy cancellation required
broker cancellation rejected
retcode = 10018
comment = Market closed

build 1.91 did not retry the pending cancellation

2024-01-05
the strategy-canceled pending later filled
-> FILLED_AFTER_STRATEGY_CANCELLATION
-> EXECUTION_DIVERGENCE
```

Required future execution behavior remains:

```text
strategy cancellation remains required
+ exact pending still live
+ cancellation rejected for recoverable broker condition

-> remain in managed execution working set
-> keep exposure/divergence lock
-> retry exact-ticket cancellation later
-> terminalize only after cancel or fill proof
```

This is an execution-safety problem, not a regime explanation, and was not mixed into Regime Research V1.

## 5. Development-set baseline evidence that motivated regime research

Clean build-1.91 outcomes used as the Development control:

| Year | Clean closed trades | Wins | Total R | Mean R/trade |
|---|---:|---:|---:|---:|
| 2023 | 70 | 23 | +44.937806R | +0.641969R |
| 2024 | 55 | 5 | -35.555410R | -0.646462R |
| 2025 | 58 | 14 | +8.680565R | +0.149665R |

Continuation-only:

```text
2023: 64 trades / +48.308745R
2024: 48 trades / -28.452965R
2025: 51 trades / +15.936463R
```

This baseline is low-win-rate, tail-dependent, and regime-unstable. The research objective therefore became annual consistency, expectancy, drawdown, streak behavior, and large-winner dependence rather than total R alone.

## 6. Frozen Regime Research V1 before 2022

Parent:

`M30_CLEAN_PERSISTENT`

```text
scope = EXTERNAL_CONTINUATION
latest 12 confirmed M30 waves available by PLAN freeze
progression >= 2/3
M30 PROTECTED_BREAK inside the same 12-wave span <= 1
```

Frozen V1:

`M30_CLEAN_PERSISTENT_EXPANDING`

adds exactly:

```text
leg_expansion_ratio > 1.0

leg_expansion_ratio =
mean(abs(last 4 M30 wave-to-wave legs))
/
mean(abs(previous 4 immediately preceding legs))
```

Canonical offline PLAN-freeze Development attribution before direct execution:

| Variant | Trades | Wins | Total R | Mean R | Max DD | Longest loss streak |
|---|---:|---:|---:|---:|---:|---:|
| Parent | 39 | 15 | +52.489559R | +1.345886R | -8.1724R | 8 |
| Frozen V1 | 20 | 13 | +53.847843R | +2.692392R | -3.012821R | 3 |

Frozen V1 by year:

```text
2023: 12 trades / 8 wins / +43.879687R
2024:  3 trades / 1 win  /  +2.363062R
2025:  5 trades / 4 wins /  +7.605095R
```

The exact freeze and failed/retained feature history are preserved in `docs/ea/REGIME_RESEARCH_2023_2025.md`.

## 7. Direct MT5 Development validation — Parent

Source:

```text
file = 25(1).csv
period = 2023-01-01 ~ 2025-12-31
mode = M30_CLEAN_PERSISTENT
rows = 9,710
bytes = 5,477,452
SHA-256 = aeba85cc7fe396d21db4e93d2967f8dd27513d7e61c66faba174a04b096257c2
log mode = RESEARCH_COMPACT
execution divergence = 0
```

Result:

```text
46 trades / 15 wins / 32.61%
Total = +45.436530R
Mean = +0.987751R/trade
R Profit Factor ≈ 2.4518
Max DD = -11.204262R
Longest losing streak = 11
```

By entry year:

```text
2023: 23 trades / 9 wins / +45.219207R
2024: 14 trades / 2 wins /  -3.364869R
2025:  9 trades / 4 wins /  +3.582192R
```

Execution funnel:

```text
pending accepted = 59
filled = 46
closed = 46
canceled before fill = 13
execution divergence = 0
```

## 8. Direct MT5 Development validation — Frozen Expansion V1

Source:

```text
file = 25.csv
period = 2023-01-01 ~ 2025-12-31
mode = M30_CLEAN_PERSISTENT_EXPANDING
rows = 608,893
bytes = 236,873,208
SHA-256 = e43cd7e12e672d21afc63ed2bbcb5837ea5ca0dd8f1270401979ac203a2f7ca3
log mode = pre-compact full audit
execution divergence = 0
```

Independent formula-reconstruction QA across all `2,338` EXTERNAL_CONTINUATION regime decisions:

```text
progression mismatch = 0
protected-break-count mismatch = 0
leg-expansion mismatch = 0
final PASS/REJECT mismatch = 0
```

Execution result:

```text
24 trades / 13 wins / 54.17%
Total = +49.797314R
Mean = +2.074888R/trade
R Profit Factor ≈ 5.4352
Max DD = -5.173397R
Longest losing streak = 5
```

By entry year:

```text
2023: 12 trades / 8 wins / +43.879687R
2024:  7 trades / 1 win  /  -1.687467R
2025:  5 trades / 4 wins /  +7.605095R
```

Execution funnel:

```text
Regime accepted PLANs = 428
Root contact = 274
Sweep = 191
CHoCH = 109
FVG selected = 84
execution geometry = 34
pending accepted = 34
filled = 24
closed = 24
canceled before fill = 10
execution divergence = 0
```

## 9. Direct Development A/B — Expansion increment

Every one of the 24 Expansion trades is an exact Parent trade with identical scenario/economic R. Common-trade R difference is `0`.

Expansion removes exactly 22 Parent trades:

```text
22 trades / 2 wins / 20 losses
Total = -4.360784R
Mean = -0.198217R/trade
```

By entry year:

```text
2023: 11 removed / +1.339520R
2024:  7 removed / -1.677402R
2025:  4 removed / -4.022903R
```

Therefore the direct Development comparison supports the expansion axis as incremental:

```text
Parent    = +45.436530R / mean +0.987751R / DD -11.204262R / streak 11
Expansion = +49.797314R / mean +2.074888R / DD  -5.173397R / streak 5
```

The result is not explained by a changed downstream Entry/SL/TP on common trades.

## 10. Why offline post-filter counts differ from direct MT5 execution

The frozen offline V1 had 20 trades; direct V1 produced 24. All original 20 were reproduced with identical R. Four additional direct trades were explained by causal execution state:

1. **2024-04-30 LONG ≈ -1R** — an H1 same-entry contributor failed the regime gate while M15 same-entry contributors passed; after the H1 branch disappeared, the surviving M15 contributors could merge and execute.
2. **2024-12-13 LONG ≈ -1.001592R** — the baseline opportunity had been blocked by an opposite SHORT exposure whose Root failed the regime gate; removing that exposure released the LONG.
3. **2024-12-17 SHORT ≈ -1.030270R** — already filled in the old baseline but excluded from calendar-2024 closed-trade attribution because it closed on 2025-01-02.
4. **2024-12-18 SHORT ≈ -1.018667R** — same year-end right-censoring issue.

Research rule:

```text
offline post-filter = discovery / PLAN classification aid
direct Strategy Tester = final implemented-variant execution authority
```

Year statistics should cohort by **entry year** and allow late-year positions to reach terminal outcome rather than truncating open trades at December 31.

## 11. Compact logging validation

The original 3-year Expansion full audit generated:

```text
608,893 rows
≈ 226 MiB
```

The largest single source was global `M1_FVG_DETECTED`, with about 272,603 rows and roughly half the text volume.

The research harness therefore introduced a logging-only selector:

```text
RESEARCH_COMPACT
FULL_AUDIT
```

`RESEARCH_COMPACT` retains:

```text
M30 WAVE_CONFIRMED
M30 STRUCTURE_PROTECTED_BREAK
regime ACCEPT/REJECT snapshot
scenario PLAN / Root contact / Sweep / CHoCH / selected FVG
Entry/SL/TP geometry
merge/add-on/exposure decision
pending/fill/cancel/close
execution error/divergence
```

and suppresses high-volume detector/audit noise not required for ordinary long-run research.

The 3-year Parent compact run was approximately:

```text
9,710 rows
5.2 MiB
```

with zero execution divergence. This logging change has no strategy authority.

## 12. 2022 first sealed OOS — data provenance

The Parent and Expansion runs were accidentally appended into one CSV and were split by their separate `EA_START` boundaries before analysis.

Combined research-mode file:

```text
file = 25(2).csv
rows = 6,766
bytes = 3,279,300
SHA-256 = 7a9df6350eed1f93938b485ae3eecde8ddf42464a734d5b29e7e2b4a56e26bd1
run 0 = Parent
run 1 = Frozen Expansion V1
```

Baseline no-gate file:

```text
file = no_gate.csv
rows = 6,857
bytes = 4,383,745
SHA-256 = 40c0bf0f744504f9d12ff7a777fc85a8366ab2b3bd168a23f6a35599f944b42a
mode = BASELINE_NO_REGIME_GATE
execution divergence = 0
```

## 13. 2022 baseline direct result

All baseline scopes:

```text
85 trades / 17 wins / 20.0%
Total = -19.209190R
Mean = -0.225990R/trade
Max DD = -24.339604R
Longest losing streak = 13
R Profit Factor ≈ 0.7187
```

Pre-registered OOS comparator — baseline `EXTERNAL_CONTINUATION` only:

```text
72 trades / 15 wins / 20.83%
Total = -14.476581R
Mean = -0.201064R/trade
Max DD = -20.764118R
Longest losing streak = 18
```

Baseline reversal:

```text
13 trades / 2 wins
Total = -4.732610R
```

## 14. 2022 Parent direct result

```text
16 trades / 3 wins / 18.75%
Total = -3.825354R
Mean = -0.239085R/trade
Max DD = -5.741120R
Longest losing streak = 5
R Profit Factor ≈ 0.7083
execution divergence = 0
```

The Parent alone therefore did **not** turn 2022 expectancy positive.

## 15. 2022 frozen Expansion V1 direct result

```text
6 trades / 1 win / 16.67%
Total = +0.994756R
Mean = +0.165793R/trade
Max DD = -3.012334R
Longest losing streak = 3
R Profit Factor ≈ 1.1979
execution divergence = 0
```

Approximate trade-R sequence:

```text
-1.008R
-1.003R
-1.002R
+6.023R
-1.011R
-1.004R
----------------
+0.995R
```

Important caveat: the 2022 V1 result is a very small six-trade sample and is strongly dependent on one approximately +6R winner. It is a PASS under the pre-registered contract, but not evidence of a smooth or high-confidence yearly return distribution by itself.

## 16. 2022 Parent versus Expansion increment

All six Expansion trades are exact members of the Parent run and have identical R.

Expansion removes ten Parent-only trades:

```text
10 trades / 2 wins / 8 losses
Total = -4.820111R
Mean = -0.482011R/trade
R Profit Factor ≈ 0.4039
```

Thus in the untouched 2022 OOS:

```text
Parent    = -3.825354R / mean -0.239085R / DD -5.741120R
Expansion = +0.994756R / mean +0.165793R / DD -3.012334R
```

The expansion axis improved both expectancy and drawdown, satisfying the separately frozen incremental-support condition.

## 17. Pre-registered 2022 OOS classification

Frozen before opening 2022:

```text
INCONCLUSIVE if V1 clean closed trades < 5

PASS candidate if:
trades >= 5
AND Total R > 0
AND mean R/trade > 0
AND Max DD less severe than 2022 continuation baseline
AND longest losing streak no worse than 2022 continuation baseline

FAIL otherwise
```

Observed:

| Condition | Required | Observed | Result |
|---|---:|---:|---|
| Clean V1 trades | >= 5 | 6 | PASS |
| Total R | > 0 | +0.994756R | PASS |
| Mean R/trade | > 0 | +0.165793R | PASS |
| Max DD | better than -20.764118R | -3.012334R | PASS |
| Longest loss streak | <= 18 | 3 | PASS |
| Expansion vs Parent expectancy+DD | not worse on both | better on both | PASS |

Final classification:

```text
2022 FIRST SEALED OOS = PASS
FROZEN EXPANSION AXIS OOS SUPPORT = PASS
```

No V1 formula or threshold was changed after viewing 2022.

## 18. Current interpretation and next validation

The evidence now supports the following bounded statement:

```text
The frozen M30_CLEAN_PERSISTENT_EXPANDING research gate
survived direct Development execution and the pre-registered 2022 OOS contract.
```

It does **not** yet imply automatic baseline strategy promotion.

Current authority remains:

```text
AGENTS.md = unchanged
EA_SPEC.md = unchanged
build 1.91 baseline = preserved control
```

Next preferred validation:

```text
2021 untouched direct A/B/C confirmation
-> explicit promotion / no-promotion decision
```

If the formula or threshold changes after the already-opened 2022 result, the changed model is Regime Research V2 and 2022 is no longer untouched OOS evidence for it.

The recoverable pending-cancel retry remains a separate execution-safety item and must not be mixed into the regime hypothesis without a controlled regression.
