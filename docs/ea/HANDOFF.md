# EA Development Handoff

> **V2 ACTIVE ROUTING — 2026-08-24 / D-154O**  
> Current V2 phase is `D-154O BROAD-MARKET GOLD-LIKE EXECUTION-SUITABILITY SCREEN`; D154N is deferred. Read `docs/ea/v2/HANDOFF_V2.md`, `RESEARCH_SYNTHESIS_D154A_D154UL.md`, and `D154O_BROAD_MARKET_GOLD_LIKE_SCREEN.md` first.  
> Ultra Low confirmed lower friction but did not solve high-friction markets. The next priority is outcome-blind screening of a broad Ultra Low symbol universe for GOLD-like execution scale. Baseline strategy semantics remain unchanged.

Last updated: 2026-08-22
Repository base before this documentation update: `7cb26133235c45a3756492af951900f15213f8cb`
Current code/research build: `2.02R0L2 / V2_SP_ARCHITECTURE_RESEARCH_V3`
Current research phase: **D-152 SP V3 MATRIX COMPLETE / V3E PROVISIONAL SP REFERENCE / ENTRY SURVIVAL NEXT**
Strategy semantics: **V1 FROZEN / V2 CONTINUATION-ONLY / D151 SHADOW + D152 SP RESEARCH MODES**
Strategy authority: **V2 -> docs/ea/v2/AGENTS_V2.md; V1 preserved as historical control**
2021 status: **KEEP UNTOUCHED**

## 1. Mandatory authority / startup order

On every new session or resumed development:

1. Check the latest GitHub commit first.
2. Read `AGENTS.md` first. It remains the highest V1 strategy authority.
3. Read this `docs/ea/HANDOFF.md`.
4. Read `docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md` for the current solution-research evidence and V2 contract.
5. Read `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md` and `docs/ea/D146_CONTINUATION_STATE_AUDIT.md` for the runner-state evidence behind SP.
6. Read `docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md` for the Entry-failure classes constraining EM.
7. Read `docs/ea/STRATEGY_RESEARCH_STATE.md` and `docs/ea/BACKLOG.md`.
8. Use `DECISIONS.md`, `TEST_RESULTS.md`, `EA_SPEC.md`, and older research docs only as needed.

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

## D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / LOCAL COMPILE + BASELINE PARITY PENDING

D-147 is a controlled post-fill research variant. It does not change PLAN, Root/Sweep/CHoCH/FVG authorization, Entry, initial normalized SL, position sizing, structural objective selection, or initial structural TP.

Modes:

```text
V1_EXIT_ORIGINAL
  exact baseline post-fill server SL/TP behavior

V1_EXIT_R_STEP_TRAILING
  R0 = |actual fill - original normalized SL|, frozen forever
  +1R -> SL 0R
  +2R -> SL +1R
  +3R -> SL +2R
  ...
  structural TP retained

V1_EXIT_R_STEP_PARTIAL
  each newly reached integer R closes 50% of CURRENT remaining volume
  original SL retained
  structural TP retained
  if broker min/step volume makes a true partial impossible, do not substitute a full close
```

The 50% fraction is frozen and not exposed as an optimizer input. D-145/D-146 M30 maturity is not used as a threshold or gate in this first exit experiment.

Required validation order:

```text
1. MetaEditor compile = 0 errors
2. D-147 ORIGINAL vs D-146 baseline canonical event parity = PASS
3. GOLD 2025 ORIGINAL / TRAILING / PARTIAL under identical settings
4. compare realized net WR, average winner/loser R, cost-adjusted expectancy, DD, loss streak, direction split, large-winner dependence
5. only then expand to the development panel
```

Use `InpEnableEdgeAudit=false` for the D-147 performance comparison so the D-146 counterfactual tracker does not complicate the exit-variant ledger. 2021 remains untouched.

## D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / LOCAL COMPILE + AUDIT PARITY PENDING

D-147 established that post-+1R profit giveback and pre-+1R Entry survival are different problems. GOLD 2025 mechanical partial exits improved realized win-rate / drawdown behavior but did not change the 21 continuation trades that hit the original SL before +1R.

D-148 now studies only:

```text
actual filled EXTERNAL_CONTINUATION
+
normalized SL reached before first +1R
```

D-148 is shadow-only. It does not change Entry, SL, TP, exit mode, order lifecycle, sizing, map authority, or scenario authorization.

For each failure it freezes exact SL-first time, then keeps a private shadow tracker after the real position is closed until the first of:

```text
original +1R price recovered
current H1/M30 map no longer supports the trade direction
Strategy Tester end (right censor)
```

`frozen owner invalidated` and `Root invalidated` are recorded separately. A frozen M30 owner break is not automatically treated as a directional premise failure because a same-direction H1/M30 successor authority may exist.

Required test configuration:

```text
InpExitManagementMode = V1_EXIT_ORIGINAL
InpEnableEdgeAudit = true for the audit run
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
Every tick based on real ticks
```

Validation order:

```text
1. MetaEditor compile = 0 errors
2. short GOLD audit OFF/ON non-audit parity PASS
3. GOLD 2025 full Audit ON
4. summarize_d148_entry_survival_failure_taxonomy.py => EVENT INTEGRITY PASS
5. classify early-entry/stop-sensitivity vs map-premise failure before designing any Entry filter
```

No pooled threshold optimization. 2021 remains untouched.

## D-149 SP + EM RESEARCH V1 — IMPLEMENTED / LOCAL VALIDATION PENDING

Build: `1.95R1L11 / SP_EM_RESEARCH_V1`.

Independent research toggles:

```text
Exit: ORIGINAL / R_STEP_TRAILING / R_STEP_PARTIAL / SMART_PARTIAL
EM:   OFF / CAUSAL_EPISODE_V1
```

Primary four-run matrix:

```text
A ORIGINAL + EM_OFF        baseline control
B SMART_PARTIAL + EM_OFF   SP isolated
C ORIGINAL + EM_ACTIVE     EM isolated
D SMART_PARTIAL + EM_ACTIVE combined
```

SP V1:
- first +1R freezes causally available M30 protected/external state;
- if current M30 external is at/beyond original +2R, close 25% only (`STRONG_RUNNER`);
- otherwise/missing M30 range, close 50% (`DEFAULT`);
- no repeated integer-R partials;
- first +2R moves remaining SL to actual Fill;
- structural TP remains unchanged.

EM V1, continuation only:
- episode identity = frozen active H1/M30 owner + direction;
- one pending/filled exposure per same episode;
- after first net loss, a fresh same-direction map delivery is required before one retry;
- H1-led episode accepts same-owner H1 BOS or new same-direction M30 INITIAL_BOS/BOS as refresh;
- M30-led episode requires same-owner M30 BOS;
- second consecutive net loss hard-locks that owner until a new owner creates a new episode;
- a positive realized-net trade resets the episode consecutive-loss count.

D148 audit remains available only for `ORIGINAL + EM_OFF`. Do not enable D148 audit on SP/EM performance runs.

2021 remains untouched.

## D-149 V1 result -> V2 revision — 2026-08-21

The GOLD 2025 A/B/C/D research ledgers are now locally validated for the three supplied research variants. Detailed evidence and the pre-registered V2 fix are frozen in:

`docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md`

Key continuation results:

```text
ORIGINAL control: 51 trades / WR 27.45% / avg winner 3.827R / expectancy +0.254R / DD 19.53R / streak 11
SP V1:            51 trades / WR 43.14% / avg winner 1.880R / expectancy +0.315R / DD 11.05R / streak 6
EM V1:            29 trades / WR 27.59% / avg winner 4.842R / expectancy +0.563R / DD 15.13R / streak 14
SP+EM V1:         30 trades / WR 43.33% / avg winner 2.256R / expectancy +0.538R / DD 8.29R / streak 7
```

Interpretation:

- SP V1 is **PROMISING**. The pre-registered strong state separated +2R continuation on GOLD 2025: continuation `STRONG_RUNNER 9/11 = 81.8%` vs `DEFAULT 4/19 = 21.1%`.
- EM V1 is **DEMOTED**. Same-episode concurrency blocking removed many trades without shortening the longest loss streak; EM-only streak worsened to 14.
- The useful EM V1 component is the post-failure fresh-delivery requirement. Concurrent exposure blocking is removed from V2.
- D-148 clean GOLD 2023-2025 remains the Entry-side causal basis: 167 continuation fills, 78 SL-first, 27/78 recovered +1R before map-support loss, including 18 local-source-failure recoveries and 9 same-Root recoveries.

Current build after this package: `1.96R1L12 / SP_EM_RESEARCH_V2`.

V2 adds controls without deleting V1:

```text
V1_EXIT_SMART_PARTIAL_V2
V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

SP V2:
- only EXTERNAL_CONTINUATION is managed;
- strong state remains the same D145/D146 structural rule and keeps the 25% partial;
- DEFAULT chooses the minimum broker-valid +1R close volume whose modeled original-SL fallback retains a small positive gross/cost buffer;
- if a true DEFAULT partial is impossible because of volume granularity, a logged +1R full-close fallback is allowed;
- after +2R the remainder receives a forward-only, current-known-cost-adjusted BE floor, recalculated as carry accumulates;
- structural TP remains frozen.

EM V2:
- no same-episode concurrency block;
- a same episode still needs fresh same-direction map delivery after a genuine Entry failure;
- only `SL before +1R` counts as an EM failure; +1R-then-giveback is an exit problem and does not count;
- two consecutive genuine Entry failures enter global quarantine;
- during quarantine real submissions are blocked and one eligible setup at a time is shadowed with its frozen Entry/SL geometry;
- quarantine ends only after a shadow +1R success or an already-open real trade reaches +1R;
- the successful shadow setup itself remains untraded; the next setup is the first eligible real trade.

V2 is research only. ORIGINAL + EM_OFF remains baseline authority. 2021 remains untouched.

## D-150 active routing — V2

The active development line is now V2. Read `docs/ea/v2/HANDOFF_V2.md` after root `AGENTS.md`. V1/D149 documents remain historical evidence and controls; do not add new reversal strategy work to V1.

## D-151 V2 routing note

Active work now resumes from `docs/ea/v2/HANDOFF_V2.md` and `docs/ea/v2/D151_V2_CAUSAL_RESEARCH_PLATFORM.md`. V1/D149 documents remain historical evidence.

## D-152 V2 routing note

Active V2 work is D-152 SP architecture research. Read `docs/ea/v2/HANDOFF_V2.md` then `docs/ea/v2/D152_SP_ARCHITECTURE_RESEARCH.md`.

## D-152 completed SP V3 matrix — current routing

The D-153 automated GOLD25/BTCUSD25 real-tick batch is complete and clean.

Primary research result:

```text
V3E BANK_2R_LOCK_ONE
= provisional post-+1R SP reference
= NOT baseline authority
```

Read immediately:

`docs/ea/v2/D152_SP_V3_RESULTS.md`

Key interpretation:

```text
GOLD25 Fill -> +1R = 56.6%
BTC25 Fill -> +1R  = 47.2%

post-+1R management is no longer the primary bottleneck
next primary research = Entry survival
```

Do not perform additional same-sample SP threshold tuning before the Entry-survival causal study.

D-153 batch automation is validated end-to-end and should be reused for subsequent GOLD25/BTC25 research matrices.
