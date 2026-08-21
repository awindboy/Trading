# D-148 ENTRY SURVIVAL FAILURE TAXONOMY

Date: 2026-08-21  
Status: **IMPLEMENTED SHADOW MEASUREMENT / LOCAL COMPILE + AUDIT PARITY PENDING**  
Implementation identity: `1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW`  
Strategy authority: **NONE**  
Baseline control for this study: `V1_EXIT_ORIGINAL`  
2021: **KEEP UNTOUCHED**

## 1. Why this phase exists

D-147 separated two different problems on GOLD 2025:

```text
A. +1R reached, then profit was given back
   -> exit / winner-management problem

B. +1R was never reached before the original normalized SL
   -> Entry-survival problem
```

Mechanical PARTIAL improved the first problem but did not change the second. The D-147 GOLD 2025 continuation population was:

```text
actual continuation fills = 51
+1R before original normalized SL = 30
original normalized SL before +1R = 21
```

D-148 studies only the 21-style primary failure population. It does not reuse the D-145 +1R M30 maturity relationship as an Entry filter.

## 2. Primary research question

For a valid EXTERNAL_CONTINUATION fill that reaches the original normalized SL before +1R:

> Was the trade direction already losing H1/M30 causal support, or did the stop occur while the same higher-timeframe direction remained supported and price later recovered?

The purpose is to distinguish, before proposing any fix:

```text
directional-premise failure
vs
entry/correction-completion timing failure
vs
possible SL-geometry sensitivity
```

D-148A is a taxonomy phase, not a filter-mining phase.

## 3. Primary population

```text
actual filled EXTERNAL_CONTINUATION
+
exact normalized-SL barrier reached before exact +1R barrier
```

Exact executable-side prices are retained:

```text
LONG  -> Bid
SHORT -> Ask
```

R remains permanently defined from:

```text
risk_distance = abs(actual_fill - original_normalized_SL)
```

No later SL modification or broker exit price redefines R.

## 4. Why the original frozen owner is not the terminal by itself

At Fill, D-148 freezes:

```text
PLAN active_map_tf
PLAN owner_id
Root id
current highest H1/M30 map direction
current highest map owner
```

A later protected break of the frozen PLAN owner is important, but it is **not automatically total directional-premise failure**.

Example:

```text
M30 frozen owner breaks
-> H1 or a new M30 owner can still provide same-direction authority
```

Therefore D-148 records three distinct facts:

```text
1. frozen PLAN owner invalidated
2. Root invalidated
3. current highest H1/M30 direction no longer supports trade direction
```

Only the third is used as the competing directional-support terminal after SL.

## 5. Causal observation window

### T0 — actual Fill

Freeze the existing causal Fill snapshot and D-148 identity.

### TSL — first exact normalized-SL touch before +1R

For the primary failure population freeze:

```text
SL timestamp
exact exit-side price
pre-SL MFE / MAE in original R
current highest H1/M30 map direction / owner / timeframe
whether current map still supports trade direction
whether frozen PLAN owner already broke
whether Root already invalidated
structure-event counters at SL
```

This is the taxonomy anchor. The real strategy position can close normally; D-148 keeps only a private shadow tracker afterward.

### After TSL

Continue observing price and causally available map state. No broker or strategy object is modified.

Track:

```text
original Entry recovery
original +1R-price recovery
worst adverse excursion from original Fill
extra adverse excursion beyond the original -1R stop
H1/M30/M1 structure-event deltas
frozen-owner invalidation
Root invalidation
current H1/M30 direction-support loss
```

There is **no arbitrary time cutoff**.

## 6. Post-SL terminal taxonomy

The primary failure tracker ends at the first applicable causal outcome.

### A. `MAP_SUPPORT_NOT_SAME_AT_SL`

At the exact SL-first anchor, current highest H1/M30 map direction already does not equal the trade direction.

Interpretation candidate:

```text
directional premise became stale before or by the stop
```

This does not by itself identify the pre-Fill cause; D-148B would compare the causal sequence before Fill/SL.

### B. `MAP_SUPPORT_LOST_AFTER_SL`

At SL, H1/M30 still supports the trade direction, but before original +1R recovery that support is later lost at a completed causal timestamp group.

Interpretation candidate:

```text
directional premise survived Entry and SL temporarily,
but ultimately failed before counterfactual recovery
```

### C. `ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS`

After the original stop, price later reaches the original Fill-based +1R price while current H1/M30 direction support has not yet been lost.

Interpretation candidate:

```text
higher-timeframe direction remained viable;
entry/correction completion or stop geometry deserves deeper study
```

This is counterfactual research only. It is **not** permission to widen/remove the SL.

### D. `RIGHT_CENSORED_AFTER_SL`

Tester ends before either +1R recovery or map-support loss.

Do not impute a class.

### Pre-SL censor

If a filled continuation trade reaches neither +1R nor normalized SL before tester end:

```text
RIGHT_CENSORED_BEFORE_1R_OR_SL
```

It is not part of the resolved primary failure population.

## 7. Intermediate fact — Entry recovery

After SL, D-148 also records the first return to the original Entry price.

This is not terminal because:

```text
SL -> Entry recovery
```

may still be followed by either:

```text
+1R recovery
or
map-support loss
```

It helps quantify how much of the failed trade was a shallow stop-out versus a full directional failure.

## 8. Event ordering and no-lookahead

D-148 follows existing runtime ordering:

```text
closed-bar structure processing
-> map refresh
-> completed timestamp-group audit sample
-> broker/execution management
-> exact-tick audit processing
```

A map-support loss becoming available at a completed timestamp group is therefore observed before later tick-only counterfactual recovery at the same runtime timestamp.

For `PROTECTED_BREAK`, the existing audit callback occurs before core `EnterTransition`. D-148 does **not** label callback fields as post-transition state. It uses only the PB event itself as causal proof that the frozen owner was invalidated and logs:

```text
callback_state_is_pre_transition=true
```

Current map support is evaluated separately after the completed timestamp group.

No future owner/external state is backfilled.

## 9. Shadow-only non-interference boundary

D-148 may:

```text
read strategy/map/source state
read Bid/Ask
maintain private audit trackers
write EDGE_AUDIT_D148_* rows
```

D-148 may not:

```text
submit/cancel/modify orders
close positions
change Entry
change SL or TP
change exit mode
change position size
change scenario authorization
change map/structure/source state
add a gate, score, threshold, or timeout
```

`AGENTS.md` and `EA_SPEC.md` remain unchanged.

## 10. D-148 rows

```text
EDGE_AUDIT_D148_FILL_STATE
EDGE_AUDIT_D148_1R_CONTROL
EDGE_AUDIT_D148_SL_FAILURE
EDGE_AUDIT_D148_FROZEN_OWNER_INVALIDATED
EDGE_AUDIT_D148_ROOT_INVALIDATED
EDGE_AUDIT_D148_MAP_SUPPORT_LOST
EDGE_AUDIT_D148_ENTRY_RECOVERED
EDGE_AUDIT_D148_TERMINAL
EDGE_AUDIT_D148_CENSORED
EDGE_AUDIT_D148_PRE_SL_CENSORED
```

Existing `EDGE_AUDIT_RUNNER_OUTCOME target=1R` remains the independent exact-barrier cross-check.

## 11. Required validation

Use `V1_EXIT_ORIGINAL`. D-148 is an Entry-survival study and must not be contaminated by D-147 post-fill variants.

Recommended fixture:

```text
Symbol: GOLD
Model: Every tick based on real ticks
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
InpExitManagementMode = V1_EXIT_ORIGINAL
```

Validation order:

1. MetaEditor compile `MentorDeterministicV1EA.mq5` with 0 errors.
2. Short GOLD Audit OFF / Audit ON under otherwise identical settings.
3. Strip `EDGE_AUDIT_*`; all remaining rows must match exactly.
4. Run GOLD 2025 full-year Audit ON.
5. Run:

```powershell
python tools\summarize_d148_entry_survival_failure_taxonomy.py <GOLD_2025_D148_LEDGER.csv>
```

Required before interpretation:

```text
D148 EVENT INTEGRITY: PASS
```

The analyzer verifies, among other things:

```text
one D148 Fill state per eligible continuation fill
1R control vs SL-first population exclusivity
agreement with existing exact 1R runner outcomes
one terminal/right-censor per primary SL failure
causal terminal timestamps
post-SL map-loss timestamp consistency
row-count / EDGE_AUDIT_STOP counter consistency
```

## 12. Analysis plan after integrity

First classify the resolved GOLD failures by terminal type.

Then compare failure classes and +1R controls using only causally available pre-Fill / Fill information. Initial research families, not pre-authorized filters:

```text
M1 correction-completion sequence
M30 owner turnover sequence (not simple PB count)
H1-transition / M30-temporary-authority lineage
local reaction strength relative to trade risk
CHoCH body-break / sweep-to-CHoCH displacement geometry
FVG width relative to risk / Root width
Root contact depth and reaction geometry
signal-to-Fill authority changes
```

Do not fit pooled cutoffs from GOLD 2025.

If D-148A shows a large recover-after-stop class, D-148B should instrument the causal M1 reaction/correction sequence before changing Entry or SL. If most failures lose map support before counterfactual recovery, research should shift toward directional authority/regime reliability.

Any discovered relationship must later be checked on other GOLD periods before strategy authority and eventually across markets.

## 13. Future idea recorded but not active — smart partial

D-147 showed that mechanical 50%-of-remaining PARTIAL materially improved GOLD 2025 realized win rate / drawdown behavior while reducing large-winner payoff.

Future research may test:

```text
SMART_PARTIAL_WITH_CONTINUATION_STATE
```

Concept:

```text
+1R reached
-> use causally available continuation state
-> decide how much to realize versus retain as runner
```

This future study must retain a mechanical PARTIAL control and must not optimize a pooled M30-progress cutoff or partial fraction from GOLD 2025.

It is intentionally not implemented in D-148.

## GOLD 2023-2025 D-148 generalization result — 2026-08-21

Clean continuation population after excluding the known 2024 stale-fill execution-divergence fixture:

```text
2023: 64 fills / 35 immediate +1R / 29 SL-first / 11 post-SL +1R recoveries
2024: 52 clean fills / 24 immediate +1R / 28 SL-first / 9 post-SL +1R recoveries
2025: 51 fills / 30 immediate +1R / 21 SL-first / 7 post-SL +1R recoveries

total: 167 fills / 89 immediate +1R / 78 SL-first
SL-first -> +1R before map-support loss = 27 / 78 = 34.6%
SL-first -> map-support failure first = 51 / 78 = 65.4%
```

Among the 27 post-SL +1R recoveries, the original Root had already invalidated in 18. Only 9 retained the original Root through recovery. Therefore most recoveries are not evidence for globally widening the SL; they are evidence that a local source can fail while the higher-timeframe directional premise survives.

Root-timeframe relationship survived all three years: M15-Root SL failures recovered later in the same HTF direction materially more often than H1/M30-Root failures. M30-led vs H1-led immediate-entry success did not generalize consistently and is not an Entry veto.

Known contaminated fixture excluded from 2024 clean inference:
`2023-12-22 cancel rejection retcode=10018 -> 2024-01-05 stale fill`.
