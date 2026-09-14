# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-15`
Status: `ACTIVE / PROTOTYPE FROZEN / ACTUAL-TICK VALIDATED / TERMINAL-ORACLE REPLICATION SHADOW RESEARCH NEXT`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`
Market authority: `GOLD# ONLY`
Base GitHub HEAD before this update packet: `d123ea1e9e40ad388cf107b3d3a4d08386877b6b`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Actual-tick event ledger SHA256: `c6e4a1117c1c0b8b073b09caaa433d940eae858dea1d9f9bc8c63fc95ab1c37c`
Actual-tick trade ledger SHA256: `bb4167b9c53ba3c73320f7dc032acc83f9d97bc6898aa04818947e167dc16bce`

## 0. Resume order

GitHub `awindboy/Trading` latest `main` HEAD remains the Single Source of Truth.
Read in this order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_PROTOTYPE_AUTHORITY_20260914.md`
7. `docs/ea/v9/V9_MT5_ACTUAL_TICK_VALIDATION_20260914.md`
8. `docs/ea/v9/V9_MONEY_MANAGEMENT_STUDY_20260914.md`
9. `docs/ea/v9/V9_ACTUAL_TICK_EXECUTION_AND_ERA_SCALE_ADDENDUM_20260914.md`
10. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
11. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
12. `docs/ea/v9/V9_TERMINAL_STAGE_HEIKIN_ASHI_RESEARCH_CHECKPOINT_20260915.md`
13. `docs/ea/v9/V9_TERMINAL_STAGE_CAUSAL_COMBINATION_RESEARCH_CHECKPOINT_20260915.md`
14. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_ORACLE_LEDGER_REPLICATION_20260915.md`
15. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STAGE_CAUSAL_DETECTION_20260915.md` — supporting predecessor contract; where evaluation objectives conflict, item 14 controls.
16. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md`
17. current EA/runtime/code state.

Older one-active-Child, hidden-gate, fixed-GOLD-SL, M1-only ambiguity, and pre-ERA4 documents remain historical evidence only when they conflict with current prototype authority.

## 1. Current prototype authority remains unchanged

```text
H1/H4 swing liquidity: causal 2-left / 2-right
H4 liquidity raid: tick-native Bid chronology
Grammar: PRIMARY_ACTIVE / CHALLENGED
Entry: immediate eligible PRIMARY_ACTIVE Arrival
Hard SL: nearest active causal opposite H1 swing liquidity
ERA_SCALE: previous completed H4 Wilder ATR180
ERA_RISK: abs(entry - structural SL) / ERA_SCALE
Eligibility: ERA_RISK <= 4

First accepted Child in active route = ANCHOR_CHILD
  -> own structural SL
  -> hold same-side H4-liquidity Arrivals
  -> exit at CHALLENGE_OPENS

Later accepted Child in same route = CONTINUATION_CHILD
  -> own structural SL
  -> exit at first subsequent H4-liquidity Arrival

No fixed TP.
No SHORT ban.
No Child-count cap.
No day/session/hour filter.
No duration timeout.
```

The terminal-stage / Heikin-Ashi work is **shadow research only** and does not replace current prototype exits.

## 2. Research answer sheet / oracle

For terminal-stage research only, the answer-sheet ledger is:

```text
TRUE LAST ACCEPTED CHILD of route
-> first completed opposite-color H4 Heikin-Ashi (HA1) after that Child
-> close every still-open Child in the route at that HA1 research close
```

This is deliberately non-causal because `TRUE LAST ACCEPTED CHILD` is future information. It is an **ORACLE / UPPER BOUND / ANSWER SHEET**, never a live rule or input feature.

Full deterministic M1 research population:

```text
BASE role policy
1,139 resolved Children
PnL +8,530.74 / PF 2.023 / WR 65.58% / DD 440.35

ORACLE last-Child -> HA1 -> close all still-open Children
1,139 resolved Children
PnL +13,863.22 / PF 3.475 / WR 70.41% / DD 288.75

Oracle improvement over BASE = +5,332.48
```

## 3. Primary evaluation rule from this checkpoint forward

Do not call a terminal detector successful merely because it beats BASE.
The primary research objective is **causal replication of the oracle ledger**.

For any candidate evaluated on period `P`, compare BASE, candidate, and ORACLE on exactly the same `P`.

```text
ORACLE_IMPROVEMENT_RECOVERY(P)
= (PnL_candidate(P) - PnL_BASE(P))
  / (PnL_ORACLE(P) - PnL_BASE(P))
```

BASE is the `0% recovery` reference; ORACLE is the `100% answer-sheet` reference.

Also report:

- oracle PnL gap;
- exact / same-HA exit matches;
- EARLY exits relative to oracle terminal HA1;
- LATE exits / giveback relative to oracle;
- MISSED oracle terminal HA1 opportunities;
- route-level and Child-level oracle regret;
- PF/DD gap to oracle;
- right-tail preservation.

Checkpoint AUC and BASE delta are secondary diagnostics only.

## 4. Latest causal-combination result

A broad consumed-data screen combined H4 HA information with H4 liquidity geometry, range/location indicators, H1 indicators, Ichimoku, and simple ML.

The current most interesting **research candidate**, not authority, is a high-precision mechanical rank using the same causal event timestamp:

```text
first opposite H4 HA event
+
Child-relative opposite-H4-liquidity pressure
+
H4 Donchian primary-direction location loss
+
opposite HA body strength / ATR180
```

On the 2024-2026 evaluation slice:

```text
BASE      +7,428.37
ORACLE    +11,625.62
CANDIDATE +7,869.42

candidate improvement over BASE = +441.05
available oracle improvement    = +4,197.25
oracle improvement recovery     = 10.51%
remaining oracle PnL gap        = 3,756.20
```

The candidate emitted `12` selected route events in that slice, with `0` events before the route's true last Child in the answer-sheet diagnostic; route delta was positive on `9` and unchanged on `3`.

This is promising only as a precision-first proof of concept. **10.5% recovery is still far from the oracle.**

Using the same three-variable information, fixed Logistic / shallow Tree / HGB variants did not beat the mechanical combination economically and produced more false-early interventions in the tested slice.

## 5. Important new timing evidence

The exact last Child does not appear to require instantaneous identification.
In the oracle diagnostic, delaying HA1 activation after the true last Child retained substantial economics:

```text
BASE                 +8,530.74 / PF 2.023
last Child + 0 H4    +13,863.22 / PF 3.475
last Child + 1 H4    +13,839.03 / PF 3.464
last Child + 2 H4    +13,715.95 / PF 3.407
last Child + 3 H4    +13,471.13 / PF 3.272
last Child + 4 H4    +12,608.38 / PF 2.927
```

Therefore research may use causal information that arrives during the H4 bars after the final accepted Child, as long as it is available before the terminal HA exit event. Do not require a classifier to identify the last Child at its entry timestamp.

## 6. Active research objective

> Using only causally known information, reproduce as much of the oracle terminal-HA1 ledger as possible while minimizing early exits that destroy normal multi-Child right-tail journeys.

The next session should prioritize explaining and recovering the **remaining oracle gap**, not broad indicator mining for its own sake.

## 7. Data governance and guardrails

All supplied V9 GOLD# periods are research-consumable by explicit user override. No supplied period remains hidden/OOS.

This does **not** permit hindsight repair.

- `TRUE LAST CHILD` is label/answer-sheet information only;
- never use future route count, later price, final PnL, eventual challenge, or oracle exit as causal inputs;
- stopped Child stays dead;
- Parent/route and Child remain separate;
- Hard SL remains fixed before entry and never widens;
- do not create fitted `Nth Child`, duration, fixed-MFE, direction-specific, cooldown, retry, or trade-quota rules;
- do not interpret opposite HA as objective trend end;
- use actual-tick chronology as higher authority for execution questions;
- no terminal-stage candidate changes strategy authority until separate causal, actual-tick, and forward evidence earns it.
