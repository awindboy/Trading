# V10 Research Instructions — HA-Primary Participation and Oracle Replication

Last synchronized: `2026-09-16`
Status: `ACTIVE / HA-PRIMARY SHADOW RESEARCH / PARTICIPATION-ORACLE REPLICATION`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`
Market authority: `GOLD# ONLY`
Base GitHub HEAD: `bebdfd73567e4bc5e311f739dbb359c388a8ac40`

## 0. Resume order

GitHub `awindboy/Trading` latest `main` HEAD is the Single Source of Truth.

Read in this order:

1. `AGENTS.md`
2. `docs/ea/v10/AGENTS_V10.md`
3. `docs/ea/v10/V10_DOCUMENT_AUTHORITY_MAP_20260916.md`
4. `docs/ea/v9/V9_RESEARCH_CLOSURE_AND_V10_TRANSITION_20260916.md`
5. `docs/ea/v10/HANDOFF_V10.md`
6. `docs/ea/v10/RESEARCH_STATE_V10.md`
7. `docs/ea/v10/V10_RESEARCH_GUARDRAILS_20260916.md`
8. `docs/ea/v10/V10_HA_PRIMARY_RESEARCH_CHECKPOINT_20260916.md`
9. `docs/ea/v10/V10_NEXT_RESEARCH_CONTRACT_ORACLE_PARTICIPATION_20260916.md`
10. current V10 result ledgers under `docs/ea/v10/results/`
11. current runtime / research code when it exists.

V9 remains historical evidence and the principal predecessor comparator. Where V10 research documents conflict with older V9 research routing about the **active research question**, V10 controls. V10 does not retroactively rewrite V9 results.

<!-- V10_POST_HEAD_20260916_START -->
## 0A. Post-HEAD current resume addendum — 2026-09-16

After completing the base Resume order above, the current V10 continuation order is:

1. `V10_POST_HEAD_RESEARCH_CHECKPOINT_20260916.md`
2. `V10_BOUNDED_M3_ACTUAL_TICK_VALIDATION_20260916.md`
3. `V10_NEXT_RESEARCH_CONTRACT_EXECUTION_FIDELITY_AND_DANGER_REGEN_20260916.md`
4. `results/V10_BOUNDED_M3_ACTUAL_TICK_SUMMARY_20260916.csv`
5. `results/V10_BOUNDED_M3_ACTUAL_TICK_EVENT_COUNTS_20260916.csv`
6. `scripts/v10_actual_tick_execution_audit.py`

Current exact executable control remains the persisted bounded `m=3` ledger:

```text
1,159 selected entry events
2,313 units
PnL +14,827.57
PF 1.553395
DD 2,638.04
+388.88R
max order 3
max concurrent 12
```

Post-HEAD research supports a stage-aware hypothesis:

```text
k1  -> extreme Danger / run admission
k2  -> Persistence confirmation
k3+ -> marginal Child economics
FAST opposite HA -> campaign exit comparator
```

The recorded `bounded m3 + extreme NHA-shock veto` result (`+15,013.69`, PF `1.57811`, `+428.23R`) is **session-recorded consumed evidence**, not an executable benchmark, because its exact fitted coefficients and veto-row ledger were not persisted.

The first bounded-m3 actual-tick run is also **not a validation pass**. It found that a market-closed `FAST_NHA_EXIT` rejection erased exit intent instead of keeping an immutable pending close. This produced stale-position holding, opposite-direction overlap, and max concurrent exposure `16` instead of the research geometry `12`.

Immediate priority:

```text
repair EXIT_PENDING persistence
-> rerun exact bounded-m3 control unchanged
-> regenerate post-HEAD Danger/Persistence artifacts
-> only then test state-machine policy changes
```
<!-- V10_POST_HEAD_20260916_END -->

## 1. V10 research question

V10 asks:

> Can an HA-primary participation engine causally approximate the future early-run participation Oracle closely enough to improve entry price, exposure placement, structural-R capture, and trend participation without relying on future run length?

The primary problem is no longer “how do we improve V9 terminal exit while keeping Grammar as the entry clock?”

It is:

```text
Which HA run is worth participating in?
How much exposure should be accumulated now?
When should new exposure stop being added?
When should the FAST HA campaign exit?
```

## 2. Current research architecture — not strategy authority

Current shadow baseline:

```text
FAST H4 transformed HA
  HC = (O + H + L + 2*C) / 5
  HO_t = 0.25*HO_(t-1) + 0.75*HC_(t-1)

STD H4 HA
  standard Heikin-Ashi representation

SLOW H4 transformed HA
  same close weight w=2
  alpha=0.75 recursive open

H1 structural invalidation
  nearest active causal opposite H1 swing liquidity

ERA_SCALE
  previous completed H4 Wilder ATR180

Eligibility screening
  ERA_RISK <= 4
```

These are **current research baselines**, not promoted production rules.

Current FAST campaign comparator:

```text
same-color FAST HA -> participation opportunities
first completed opposite-color FAST HA -> default campaign exit comparator
each Child keeps its own structural H1 SL
```

## 3. Oracle labels

Future information is allowed only in the answer sheet / training label.

### Early-third participation Oracle

```text
k = current FAST HA index in the same-color run
L = final FAST run length

ORACLE_EARLY = 1 iff 3*k <= L
```

`L` is never a live feature.

### Relative runway labels

Research may ask:

```text
L >= m*k
```

for diagnostic `m` families.

No scanned `m` value becomes authority merely because it performed best on consumed data.

### Economic quality label

A separate answer sheet asks whether a hypothetical Child produces positive outcome under:

```text
own H1 structural SL
vs
first opposite FAST HA campaign exit
```

Future Child outcome is a label only, never a live feature.

## 4. Current semantic roles

### FAST H4 HA
- execution / participation clock;
- primary run segmentation;
- current default exit comparator.

### STD H4 HA
- broader PHA-location / maturity representation;
- directional support for FAST;
- currently more predictable early-run representation than FAST itself.

### SLOW H4 HA
- broader regime / maturity context;
- useful as participation context;
- not supported as delayed exit authority by current evidence.

### H1 standard HA / M30 FAST HA / M15 FAST HA
- multi-timeframe delivery context;
- M15 FAST body flow is the strongest current single LTF HA coordinate;
- feature soup is not authority.

### Grammar
- structural / campaign context;
- no longer assumed to be the primary V10 entry clock.

### H1 liquidity
- structural invalidation;
- risk geometry;
- current `ERA_RISK <= 4` screening baseline.

## 5. Current strongest findings

The current 2025-2026 M1-first-touch / H1-eligible FAST universe:

```text
2,489 eligible FAST participation opportunities
ALL1 PnL +10,007.27
PF 1.368
DD 2,034.28
+253.72R
```

True early-third Oracle:

```text
567 Oracle entries
PnL +23,344.73
PF 15.157
DD 148.81
+733.18R
```

Formula-level early-zone predictability:

```text
STD w1/a0.50      mean AUC 0.850
Smooth STD a0.75  mean AUC 0.849
SLOW w2/a0.75     mean AUC 0.847
FAST w2/a0.25     mean AUC 0.822
Close4 FAST       mean AUC 0.808
```

A bounded prior-only quartile research map using:

```text
P_RUNWAY(3x)
* P_WIN
* P_STD_SUPPORT
```

and diagnostic exposure map:

```text
bottom 50% -> 0
50-75%    -> 1 unit
top 25%   -> 3 units
```

produced:

```text
PnL +14,827.57
PF 1.553
DD 2,638.04
+388.88R
2,313 total lot-units
max order 3 units
```

This map is a consumed-data research diagnostic. The quartiles and `0/1/3` units are **not authority**.

## 6. Non-negotiable leakage rules

Never use as live state:

- final HA run length;
- true early-third label;
- future Child count;
- future challenge;
- later HA / later LTF bar that has not completed;
- eventual Child or campaign PnL;
- future structural-liquidity consumption;
- future Oracle timestamp;
- post-stop Child resurrection.

A stopped Child stays dead.

## 7. No hidden rules

Do not invent:

- fixed minimum-R unless explicitly researched and authorized;
- cooldown;
- retry limit;
- fixed no-chase distance;
- fixed Child count cap;
- fixed “three bars then add” ladder;
- forced LONG/SHORT balance;
- session/day/hour exclusion;
- fixed duration timeout.

Any such idea must be an explicit research hypothesis with a ledger.

## 8. Promotion status

No V10 production strategy exists.

No current V10 probability model, HA formula, runway multiple, score threshold, quartile cut, or lot map has production authority.

Promotion requires at minimum:

- fixed causal semantics;
- selection-stability controls;
- route-level regret and concentration audit;
- actual-tick executable replay;
- structural-R and concurrent-risk accounting;
- forward-demo evidence.

<!-- V10_REPRO_LEDGER_20260916_START -->
## 0B. Reproducibility-ledger addendum — 2026-09-16

After the post-HEAD / actual-tick addendum, also read:

1. `V10_REPRODUCIBILITY_LEDGER_AND_MODEL_REGEN_CHECKPOINT_20260916.md`
2. `V10_DATA_AND_LEDGER_MANIFEST_20260916.md`
3. `V10_REGENERATION_RESULTS_20260916.md`
4. row-level execution, parity, feature, coefficient and score ledgers under `results/`

The research-artifact requirement is now explicit:

```text
summary statistic alone
!= reproducible research evidence

serious model/policy claim
-> source population
-> causal feature definition
-> train/test window
-> preprocessing
-> coefficients/model artifact
-> per-event score
-> prior-only decision reference
-> action ledger
-> outcome/regret ledger
-> validation receipt
```

The newly regenerated `_REGEN` heads are **selection-conditioned on the 1,159 bounded-m3 selected signals**. They are new reproducible research candidates. They are not asserted to recover the missing full-universe coefficients of the earlier session-recorded shock-veto experiment.

Current work order remains:

```text
EXIT_PENDING execution repair
-> unchanged bounded-m3 actual-tick rerun
-> row-level parity audit
-> reproducible Danger/Persistence evaluation
-> only then policy/state-machine changes
```
<!-- V10_REPRO_LEDGER_20260916_END -->

<!-- V10_DECISION_CLOCK_HOTFIX_20260916_START -->
## 0C. Signal decision-clock hotfix — 2026-09-16

Also read:

`V10_SIGNAL_DECISION_CLOCK_HOTFIX_20260916.md`

Canonical timestamp semantics:

```text
decision_ts / decision_time
= research signal clock
= EA effective_ts when present

entry_event_time / entry_time_actual
= execution chronology
```

`signal_id + effective_ts` is the exact parity key. Do not treat a one- or two-second MT5 fill/event lag as a signal mismatch, and do not solve it with an arbitrary tolerance.
<!-- V10_DECISION_CLOCK_HOTFIX_20260916_END -->
