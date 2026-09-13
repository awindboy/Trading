# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-14`
Status: `ACTIVE / ARRIVAL-DELIVERY / CONSUMED MECHANICAL POLICY FREEZE CANDIDATE / EXECUTION FREEZE NEXT`
Production authority: `NONE`
EA authority: `NONE`
Market authority: `GOLD# ONLY`
Consumed research blocks: `2024`, `2025-01..06`, `2026-01..02`
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Base GitHub HEAD before this update packet: `925368270b8bf91ba70936e8b3a1c1832813091a`

## 0. First rule on every resume

GitHub `awindboy/Trading` latest `main` HEAD is the Single Source of Truth.

After this packet is merged, read in this exact order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_ARRIVAL_DELIVERY_GRAMMAR_CORE_AUTHORITY_20260913.md`
7. `docs/ea/v9/V9_MECHANICAL_EDGE_AND_IMMEDIATE_ENTRY_AUTHORITY_20260913.md`
8. `docs/ea/v9/V9_LIQUIDITY_TOPOLOGY_AND_JOURNEY_VALIDATION_CHECKPOINT_20260914.md`
9. `docs/ea/v9/V9_CHALLENGE_EXIT_EXPOSURE_COST_RUNTIME_CHECKPOINT_20260914.md`
10. `docs/ea/v9/V9_MECHANICAL_POLICY_FREEZE_CANDIDATE_20260914.md`
11. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_EXECUTION_FREEZE_AND_HIDDEN_GATE_20260914.md`
12. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
13. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
14. current code/tool parity state.

Older FLOW_ROUTE, H1-state-action, COUNTER/WITH_PARENT, scheduler, AI-direction, LTF-trigger and superseded next-contract documents remain history unless explicitly retained by the authority map.

## 1. Current Grammar

```text
MOVING
ARRIVAL
```

Arrival attributes:

```text
SIDE
  UP / DOWN / OVERLAP-UNRESOLVED

ROLE
  H4 LIQUIDITY -> DELIVERY / PROGRESSION
  H4 FVG / OB  -> RESPONSE / INTERACTION
```

Slow resolver:

```text
PRIMARY_ACTIVE(A)
  opposite H4 LIQ B
  -> CHALLENGED(A,B)

CHALLENGED(A,B)
  next H4 LIQ A -> PRIMARY_CONTINUES(A)
  next H4 LIQ B -> CHALLENGER_EARNED(B)
```

No count, timeout, ATR, R, cooldown, retry, no-chase, side-balance, or trade-quota threshold is attached.

## 2. Immediate entry remains fixed

```text
causal meaningful H4-liquidity Arrival
-> update Grammar
-> if PRIMARY_ACTIVE and mechanically eligible
-> immediate Child entry
```

No M1/M5/M15 pattern is required. LTF is chronology/execution evidence, not the active edge-discovery layer.

## 3. Relative H4-liquidity topology remains factual quality information

```text
D_same
D_opposite
SAME_NEAREST := D_same < D_opposite
```

Consumed directional result:

```text
2024      SAME_NEAREST 163/216 = 75.5%
2025H1    SAME_NEAREST  76/90  = 84.4%
2026JF    SAME_NEAREST  18/20  = 90.0%
combined  SAME_NEAREST 257/326 = 78.8%
combined  NOT SAME      66/123 = 53.7%
```

Interpretation:

```text
SAME_NEAREST = positive continuation-quality information
NOT SAME != FLIP
SAME_NEAREST != mandatory entry gate
```

No numeric ratio threshold is authority.

## 4. Current consumed mechanical policy freeze candidate

The strongest simple cross-period candidate is now:

```text
PRIMARY_ACTIVE Arrival
-> if no Child is open, immediate Child entry
-> Hard SL = nearest causally-known still-active opposite H1 swing liquidity
-> hold through same-side H4 liquidity arrivals
-> first opposite H4 liquidity Arrival opens CHALLENGED
-> FULL EXIT the open Child
-> while CHALLENGED, no new directional Child
-> next H4-liquidity resolution may return PRIMARY_ACTIVE and authorize a fresh Child
```

One-active-Child consumed result:

```text
2024      +43.84R / PF 2.41 / DD 4.43R
2025H1    +20.29R / PF 3.20 / DD 2.53R
2026JF     +8.08R / PF 3.08 / DD 2.05R
combined  +72.21R / PF 2.63 / DD 4.43R
```

This is **research freeze candidate**, not production authority and not hidden-data permission.

## 5. Exact H1 structural Hard SL candidate

H1 swing/liquidity geometry remains two-left / two-right.

At Child entry time `T`:

```text
LONG
  -> highest active causally-known H1 SSL strictly below entry

SHORT
  -> lowest active causally-known H1 BSL strictly above entry
```

The object must be known before entry and unconsumed at entry. Hard SL is fixed before entry and never widened. No valid H1 structural SL means no Child.

Observed median structural-SL distance changes strongly by block (`~21.6`, `~31.6`, `~80.9 GOLD` for 2024/2025H1/2026JF), which is why fixed 15/30 GOLD selections are not current authority.

## 6. CHALLENGED action is now resolved for the consumed freeze candidate

For new entries:

```text
CHALLENGED = UNRESOLVED / NO NEW DIRECTIONAL EDGE
```

For an already-open Child, the consumed freeze candidate is:

```text
first opposite H4-liquidity Arrival
-> CHALLENGED
-> FULL EXIT
```

Reasons:

- holding until `CHALLENGER_EARNED` did not improve robustly across periods;
- post-challenge hold increment median was negative and 2026JF had no positive hold increment;
- partial-exit fractions did not dominate across periods and would add a numeric parameter;
- a topology-based challenge resolver was only about `60.6%` accurate where usable and had zero usable two-sided cases in 2026JF.

Do not convert CHALLENGED into a new direction oracle. Full exit resolves the Child, not necessarily the Parent Journey.

## 7. Exposure baseline

Full 1R stacking is not frozen: it reached up to `11` simultaneous Children and creates uncontrolled route-level risk.

`REPLACE_CHILD` is retained as a secondary comparator, but it fragments the right tail and reduced combined average winner to about `0.59R` with payoff ratio about `0.75`.

Current freeze baseline:

```text
ONE ACTIVE CHILD
```

This is an exposure convention, not a retry cap. While a Child is open, later eligible Arrivals do not open another Child. After the Child is resolved, a later mechanically eligible PRIMARY_ACTIVE Arrival may open a fresh Child.

## 8. Cost sensitivity

Observed M1 `<SPREAD>` is used only as a descriptive execution-cost proxy; no spread threshold is mined.

ONE_POSITION combined sensitivity:

```text
0x observed spread  +72.21R / PF 2.63
1x observed spread  +71.16R / PF 2.59
2x observed spread  +70.11R / PF 2.54
3x observed spread  +69.06R / PF 2.50
```

Exact broker Bid/Ask fill, commission and slippage remain execution-freeze work.

## 9. Deterministic runtime status

A new sequential dual-clock Arrival/Delivery runtime reproduces the consumed candidate directly from authoritative full-M1 byte ranges.

It verifies the source SHA, reads only frozen consumed ranges, emits completed H1/H4 information before same-time current-row OHLC reveal, creates two-left/two-right objects causally, guards Hard SL continuously, applies CHALLENGED full exit, and persists state for restart.

Exact one-position totals reproduced:

```text
2024      +43.8428228413R
2025H1    +20.2899178305R
2026JF     +8.0791431355R
```

Mid-position save/restart produced byte-identical Arrival/Object/Trade ledgers in every consumed block. Future-hidden `2025-07` OHLC was not used.

## 10. Active next work

Use:

`V9_NEXT_RESEARCH_CONTRACT_EXECUTION_FREEZE_AND_HIDDEN_GATE_20260914.md`

The active work is **not new feature mining**.

Order:

```text
1. freeze exact executable entry / Hard-SL / CHALLENGED-exit fill semantics
2. freeze gap-cross and same-M1 ambiguity handling
3. freeze official cost convention without threshold mining
4. freeze authoritative source ranges, runtime/script hashes and ledger hashes
5. rerun consumed blocks and require exact parity
6. create a single mechanical-policy freeze manifest
7. only then review whether the 2025-07 hidden gate is satisfied
8. no retuning after hidden reveal
9. 2021 remains untouched regardless
10. AI and optional LTF-entry refinement remain deferred
```

## 11. Permanent guardrails

- no future peek;
- no hindsight backfill;
- stopped Child is dead;
- Parent and Child remain separate;
- Hard SL fixed before entry and never widened;
- code/runtime owns clocks, geometry, fills, and R arithmetic;
- `PRICE_REVEALED_CUTOFF <= INFORMATION_KNOWN_AT`;
- explicit uncertainty is valid;
- no hidden minimum-R, ratio threshold, cooldown, retry cap, no-chase, duration limit, forced side balance, or trade quota;
- `2025-07` remains locked until the explicit execution/runtime gate review;
- `2021` remains untouched.
