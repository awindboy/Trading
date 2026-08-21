# EA Development Handoff

Last updated: 2026-08-21
Repository base before this handoff package: `f0a9be86d7d8af4e22b21e9b657669aae1245fbd`
Current code/audit build: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`
Current research phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / LOCAL COMPILE + PARITY PENDING**
Strategy semantics: **D134_EXECUTION_CORE_UNCHANGED**
Strategy authority: **UNCHANGED**
2021 status: **KEEP UNTOUCHED**

## 1. Mandatory authority / startup order

On every new session or resumed development:

1. Check the latest GitHub commit first.
2. Read `AGENTS.md` first. It remains the highest V1 strategy authority.
3. Read this `docs/ea/HANDOFF.md`.
4. Read `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`.
5. Read `docs/ea/D146_CONTINUATION_STATE_AUDIT.md`.
6. Read `docs/ea/STRATEGY_RESEARCH_STATE.md` and `docs/ea/BACKLOG.md`.
7. Use `DECISIONS.md`, `TEST_RESULTS.md`, `EA_SPEC.md`, and older research docs only as needed.

If chat memory conflicts with current GitHub, GitHub wins.

Do not redesign already-implemented behavior before inspecting current code and authority docs.

## 2. What is frozen

`AGENTS.md` and `EA_SPEC.md` are not changed by D-145/D-146 research.

Current baseline semantics remain:

```text
objective liquidity
-> H1/M30 map
-> pre-existing eligible H1/M30/M15 Root OB
-> actual Root contact
-> valid liquidity sweep
-> meaningful M1 body CHoCH
-> fresh same causal-leg FVG
-> widest eligible FVG
-> first retest
-> Entry
-> SL
-> frozen structural objective TP
```

Current baseline also preserves:

```text
ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
PD = reference only
same-entry Root merge
same-direction hedging add-ons
opposite-direction coexistence blocked
```

Research findings do not silently change these rules.

## 3. Completed research chain

### D-142A
Stage-forward shadow audit passed GOLD audit-OFF/audit-ON non-interference parity.

### D-143
Six-symbol front-end causal census established:

- PLAN -> Root Contact is intentionally a pullback, not independent direction confirmation.
- mature H1/M30 bearish continuation was weak as an unconditional forward signal.
- Root Contact recovered local directional response.
- static front-end feature/filter mining did not reveal a credible path to the user's final objective.
- one directional structure event can fan out into correlated repeated exposure.

### D-144
GOLD 2025 exact-tick standardized barriers showed that current structural-objective win rate understates local filled-entry edge.

Continuation actual fills:

```text
51 fills
structural objective winners = 14 / 51 = 27.45%
+1R before SL = 30 / 51 = 58.82%
+1.5R before SL = 25 / 51 = 49.02%
+2R before SL = 20 / 51 = 39.22%
```

Many structural-objective losers first made meaningful positive R and then gave it back.

This did NOT authorize a fixed 1R TP. The user's target remains >=50% realized win rate while winners earn meaningfully more than 1R and cost-adjusted expectancy stays positive.

### D-145
D-145 replaced expensive D-144 stage/mirror fan-out with lightweight actual-fill runner tracking.

It records:

```text
Actual Fill causal market snapshot
first +1R causal market snapshot
exact +1R / +2R / +3R / structural-TP outcomes
```

The main D-145 development/generalization panel is:

```text
GOLD 2023
GOLD 2024
GOLD 2025
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

Detailed evidence is frozen in:

`docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`

## 4. Most important D-145 result

Entry survival and winner continuation are now treated as separate research problems.

### A. Entry survival — still unsolved

2025 continuation Fill -> +1R:

```text
GOLD    30 / 51  = 58.8%
BTCUSD  54 / 114 = 47.4%
SILVER  18 / 45  = 40.0%
CADJPY  30 / 111 = 27.0%

total = 132 / 321 = 41.1%
```

Therefore the current Entry architecture is not broadly >=50% to +1R.

### B. Winner continuation — first generalizing structure found

Among trades that already reached +1R, `M30 protected -> current directional external range progress` at the first +1R moment is the strongest surviving relationship.

Definition:

```text
protected swing = 0
current directional external = 1

lower progress = less mature current M30 directional delivery
higher progress = closer to / through current M30 external
```

Median progress, exhaust-before-2R vs +2R runner:

```text
GOLD23   1.061 -> 0.691
GOLD24   0.867 -> 0.644
GOLD25   0.918 -> 0.796
BTC25    0.955 -> 0.788
SILVER25 0.946 -> 0.724
CADJPY25 0.770 -> 0.565
```

Direction of relationship:

```text
market-year aggregate = 6 / 6
comparable market-year x direction cells = 11 / 11
runner had LOWER M30 progress at +1R
```

Coverage caveat:

```text
resolved +1R conditional population = 190
valid comparable M30 scenario-direction range at +1R = 147
```

Missing M30 range state is not imputed.

### Supporting variable

`remaining distance to current M30 external / actual Fill-to-SL risk` was also larger for runners in all 6 aggregate market-year cells, but it contains the trade-risk denominator and has weaker direction-level purity. Treat it as supporting evidence, not the primary state variable.

## 5. What did NOT generalize

Do not promote these into strategy rules from D-145:

```text
M30 net directional advance
FVG -> Fill elapsed time
FVG -> Fill maximum favorable displacement
simple M30 wave progression ratio
simple protected-break count
+1R arrival speed / time-to-1R
M1 same-direction confirmation
M30 leg expansion as a standalone runner rule
```

Relationships weakened or reversed by market/year/direction.

Also, eventual +2R runners often had MORE adverse excursion before first +1R. Do not create a `clean path / low MAE / fast 1R` quality filter.

## 6. Critical interpretation boundary

The current best working interpretation is:

> Root/FVG can generate a valid local reaction. Once +1R is reached, the probability of another full R of delivery is related to how much of the current M30 directional protected-to-external structure has already been consumed.

This is still descriptive evidence.

It does NOT yet prove that the current M30 external is itself the causal waypoint/barrier.

It also does NOT explain Entry -> +1R success.

Therefore:

```text
M30 maturity @ +1R
= runner-continuation research variable

M30 maturity @ +1R
!= Entry authorization filter
```

## 7. Next phase — D-146

Next task is NOT a strategy variant.

D-146 must test whether post-+1R M30 structure evolution explains the D-145 relationship and its exceptions.

Primary question:

> When +1R is reached near an already-mature M30 external, do the trades that still reach +2R first receive a causal outward M30 structure refresh, while the trades that exhaust fail to refresh or suffer protected-structure deterioration?

Secondary question:

> When +1R still has substantial M30 room but the trade nevertheless fails before +2R, is that failure associated with a new protected break, opposite directional event, owner change, or other causal M30 deterioration after +1R?

Detailed measurement contract:

`docs/ea/D146_CONTINUATION_STATE_AUDIT.md`

## 8. D-146 implementation boundary

D-146 must remain shadow-only.

It may observe and log. It may not:

```text
close at +1R
hold based on progress threshold
change structural TP
change SL
change Entry
reject a scenario
add a score
add an M30 maturity gate
add a SHORT/LONG special rule
```

Use one unified CSV per run.

Only +1R-success runner objects need post-+1R tick/state tracking. Do not reintroduce the D-144 all-stage mirror-barrier fan-out.

Required validation order:

```text
1. Re-check current GitHub source.
2. Implement D-146 shadow measurement only.
3. MetaEditor compile = 0 errors.
4. GOLD short smoke audit OFF vs ON => non-audit parity PASS.
5. GOLD 2025 full run to validate event integrity/runtime.
6. Development panel reruns as needed:
   GOLD 2023/2024/2025
   BTCUSD/SILVER/CADJPY 2025
7. Analyze relation direction by market and direction, not pooled threshold.
```

`2021` stays untouched.

## 9. Parallel but separate research problem — Entry survival

After or in parallel with D-146 measurement design, the project still needs a separate causal study of:

```text
Fill -> +1R
```

because 2025 cross-market success is only 41.1%.

Do not try to repair this by reusing D-145 runner maturity as an Entry filter.

The Entry-survival study must search for market background that is known by Fill and generalizes across symbols/periods. It must not use post-Fill outcome-known information.

## 10. Strategy variant promotion rule

Do not implement a dynamic runner exit simply because D-145 looks strong.

Only after D-146 determines a plausible causal state transition should one controlled strategy variant be considered.

A future variant must:

- change one meaningful thing at a time;
- preserve baseline control;
- use causally available information;
- compare against identical conditions;
- evaluate realized WR, average win R, expectancy, drawdown, streaks, annual/directional breadth, and winner dependence;
- avoid threshold tuning to this development panel;
- remain separate from Entry-survival research.

## 11. Execution issues remain separate

Known execution-lifecycle issues are not solved by D-145:

- recoverable pending-cancel rejection (`retcode=10018 / Market closed`) needs deterministic retry;
- pending disappearance without proven fill/cancel still needs reconciliation;
- late-year cohorts need terminalization beyond year-end for final profitability evidence.

Do not mix execution-integrity fixes with strategy-research variants.

## 12. Immediate next-session instruction

The next session should begin by reading GitHub, not by reconstructing this chat.

The D-146 shadow extension is now prepared in `EdgeAuditV1.mqh` as build `1.92R1L8`.

The first concrete validation task is:

> MetaEditor compile with 0 errors, then run the GOLD short-window Audit OFF/ON smoke and require exact non-audit parity before using any D-146 evidence.

After parity, run GOLD 2025 full-year Audit ON and validate D-146 terminal uniqueness, causal M30 event ordering, original-+1R-external tracking, and runtime before broader reruns.
