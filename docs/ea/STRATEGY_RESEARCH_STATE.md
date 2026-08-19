# Strategy Robustness Research State

Last updated: 2026-08-20
Status: REGIME RESEARCH V1 FROZEN / DIRECT DEVELOPMENT VALIDATED / 2022 FIRST OOS PASS / NOT YET BASELINE AUTHORITY
Baseline control: Mentor deterministic V1 / build 1.91
Research harness: Regime Research V1 family `1.92R1`, current logging/baseline-toggle revision `1.92R1L2`
Strategy authority: unchanged; `AGENTS.md` remains highest authority

## Current phase

The broad 2023–2025 regime-feature search is complete for V1.

The frozen research model has now passed:

```text
1. 2025 same-formula transfer check
2. direct MT5 Development Set execution comparison
3. first sealed 2022 OOS contract
```

The next research step is **final untouched confirmation**, preferably 2021, followed by an explicit promotion/no-promotion decision. Do not tune V1 on the already-opened 2022 result.

Read the full evidence ledger:

`docs/ea/REGIME_RESEARCH_2023_2025.md`

## Dataset protocol

```text
2023–2025 = Development / Research
2022      = first sealed OOS — now opened and completed
2021      = preferred final untouched confirmation
```

The frozen V1 definition was fixed before 2022 was opened and was not changed afterward.

## Baseline problem that motivated regime research

Clean build-1.91 attribution:

```text
2023: +44.94R
2024: -35.56R
2025:  +8.68R
```

Continuation-only:

```text
2023: +48.31R
2024: -28.45R
2025: +15.94R
```

The baseline is low-win-rate, tail-dependent, and regime-unstable. The large 2024 deterioration could not be explained by the known execution divergence or by simply removing reversal.

## Frozen parent state

`M30_CLEAN_PERSISTENT`

```text
scope = EXTERNAL_CONTINUATION
snapshot = scenario PLAN freeze
latest 12 confirmed M30 waves
progression >= 2/3
M30 PROTECTED_BREAK inside the same 12-wave span <= 1
```

Canonical offline PLAN-freeze Development result:

```text
39 trades / 15 wins
+52.489559R
mean +1.345886R/trade
Max DD -8.1724R
longest losing streak 8
```

This state represents:

```text
DIRECTION
+ PERSISTENCE
+ STRUCTURAL STABILITY
```

## Frozen Regime Research V1

`M30_CLEAN_PERSISTENT_EXPANDING`

Adds exactly one axis to the Parent:

```text
leg_expansion_ratio > 1.0

leg_expansion_ratio =
mean(abs(last 4 M30 wave-to-wave legs))
/
mean(abs(previous 4 M30 wave-to-wave legs))
```

Full conceptual model:

```text
DIRECTION
+ PERSISTENCE
+ STRUCTURAL STABILITY
+ EXPANSION
```

Canonical offline Development result:

```text
20 trades / 13 wins / 65.0%
+53.847843R
mean +2.692392R/trade
Max DD -3.012821R
longest losing streak 3
```

The `>1.0` boundary is frozen because it means the recent four M30 legs are larger on average than the immediately preceding four. It was not selected as an arbitrary decimal optimum.

## Feature search outcome

### Retained in V1

```text
progression >= 2/3
PB <= 1 inside the same 12-wave span
leg_expansion_ratio > 1.0
```

### Rejected / downgraded after 2025 recheck

Weak progression as a standalone BAD veto failed transfer:

```text
progression <= 0.50
2025: 12 trades / +11.316R
```

Magnitude-aware persistence failed as a V1 replacement:

```text
directional_advance_norm > 1/3
2025: 16 trades / -7.889R
```

### Not included

```text
impulse_retrace threshold
retracement-depth threshold
explicit overlap/cleanliness threshold
trend maturity / owner BOS-count band
H1/M30 agreement veto
PD/range-location veto
EMA / ADX / ATR / RSI
multi-factor quality score
```

Protected-break churn remains adverse across all three Development years, but its information is already represented by the Parent's `PB <= 1` requirement.

## Direct Development Set execution

Post-filtering was not accepted as final evidence because removing scenarios can alter contributor merge, hedging exposure, opposite-direction conflicts, pending lifecycle, and later opportunity availability.

The direct research EA therefore ran the Parent and Expansion modes independently.

### Formula implementation parity

The full-audit Expansion run contained 2,338 `EXTERNAL_CONTINUATION` regime decisions. Independent reconstruction from logged M30 waves/PB events produced:

```text
progression mismatch = 0
PB-count mismatch = 0
leg-expansion mismatch = 0
PASS/REJECT mismatch = 0
```

### Parent direct — 2023–2025

```text
46 trades / 15 wins / 32.6%
+45.436530R
mean +0.987751R/trade
Max DD -11.204262R
longest losing streak 11

2023 +45.219207R
2024  -3.364869R
2025  +3.582192R
```

### Expansion direct — 2023–2025

```text
24 trades / 13 wins / 54.2%
+49.797314R
mean +2.074888R/trade
Max DD -5.173397R
longest losing streak 5

2023 +43.879687R
2024  -1.687467R
2025  +7.605095R
```

All 24 Expansion trades are exact members of the Parent run with identical R.

Expansion removes:

```text
22 Parent trades
2 wins / 20 losses
-4.360784R
mean -0.198217R/trade
```

So the additional Expansion axis improved expectancy and drawdown in direct execution, not only in offline classification.

## Why offline and direct results differ

The original offline frozen V1 attribution was:

```text
20 trades / +53.847843R
```

The direct V1 run was:

```text
24 trades / +49.797314R
```

The original 20 trades were all reproduced exactly. Four additional direct trades explain the difference.

Two were genuine causal portfolio-state effects:

```text
1. a baseline FAIL master Root was removed, allowing PASS contributors at the same Entry to merge and execute;
2. a FAIL opposite-direction position was removed, releasing a later PASS trade from exposure conflict.
```

Two were late-December 2024 positions already present in the baseline path but excluded from the old calendar-bounded closed-trade attribution because they closed in early 2025.

Conclusion:

> Offline post-filtering is useful for discovery and PLAN classification; direct Strategy Tester execution is the authority for final strategy-variant performance.

## 2022 first OOS result

The pre-registered contract required V1:

```text
trades >= 5
Total R > 0
mean R/trade > 0
Max DD less severe than baseline continuation
longest losing streak no worse than baseline continuation
```

Direct results:

| Mode | Trades | Wins | Total R | Mean R/trade | Max DD | Longest loss streak |
|---|---:|---:|---:|---:|---:|---:|
| Baseline continuation | 72 | 15 | -14.476581R | -0.201064R | -20.764118R | 18 |
| Parent | 16 | 3 | -3.825354R | -0.239085R | -5.741120R | 5 |
| Frozen Expansion V1 | 6 | 1 | +0.994756R | +0.165793R | -3.012334R | 3 |

Classification:

```text
2022 FIRST OOS = PASS
```

The expansion component also satisfies its separate requirement because it improves both Parent expectancy and Parent drawdown.

The six Expansion trades are exact Parent members with identical R. The ten Parent-only trades sum to:

```text
-4.820111R
mean -0.482011R/trade
```

## OOS caveat

The 2022 V1 sample is small and tail-dependent:

```text
6 trades
1 winner ≈ +6.023R
5 losses ≈ -5.028R
net ≈ +0.995R
```

This is enough to satisfy the frozen OOS contract, but not enough to call robustness proven.

## Current research harness

Current ResearchMode options:

```text
V1_REGIME_PARENT_CLEAN_PERSISTENT
V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING
V1_REGIME_BASELINE_NO_GATE
```

`BASELINE_NO_GATE` disables regime authorization only; the execution core remains unchanged.

Long-run event logging defaults to:

```text
RESEARCH_COMPACT
```

with `FULL_AUDIT` retained for diagnostic reruns. The logging change has no strategy authority.

## Next decision gate

Run the preferred untouched 2021 confirmation with the frozen model unchanged.

Recommended comparison:

```text
A. BASELINE_NO_GATE
B. PARENT_CLEAN_PERSISTENT
C. CLEAN_PERSISTENT_EXPANDING
```

Evaluate:

```text
Total/mean R
Max R drawdown
longest losing streak
year/direction behavior
trade count
large-winner concentration
execution divergence
```

If 2021 is supportive, make a separate explicit promotion decision before touching `AGENTS.md` or `EA_SPEC.md`.

If any formula/threshold is changed after the 2022 result, the changed model is V2 and 2022 cannot be reused as its OOS proof.

## Parallel execution-safety item

The recoverable pending-cancel rejection retry remains separate:

```text
strategy cancellation required
+ exact pending still live
+ broker cancel rejected for recoverable condition
-> retry exact ticket when permitted
```

Do not mix this lifecycle fix into the interpretation of Regime Research V1 results.
