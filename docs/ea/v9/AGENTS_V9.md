# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-14`
Status: `ACTIVE / ARRIVAL-DELIVERY GRAMMAR / TOPOLOGY + JOURNEY MECHANICAL CANDIDATE VALIDATED ON CONSUMED BLOCKS`
Production authority: `NONE`
EA authority: `NONE`
Market authority: `GOLD# ONLY`
Consumed research blocks: `2024`, `2025-01..06`, `2026-01..02`
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Base GitHub HEAD before this update packet: `753fb412a7e87b2e329ac9462107c1bad07b5e6d`

## 0. First rule on every resume

GitHub `awindboy/Trading` latest `main` HEAD is the Single Source of Truth.

After this packet is merged, read in this order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_ARRIVAL_DELIVERY_GRAMMAR_CORE_AUTHORITY_20260913.md`
7. `docs/ea/v9/V9_ARRIVAL_DELIVERY_GRAMMAR_AND_SIMPLE_BASELINE_CHECKPOINT_20260913.md`
8. `docs/ea/v9/V9_MECHANICAL_EDGE_AND_IMMEDIATE_ENTRY_AUTHORITY_20260913.md`
9. `docs/ea/v9/V9_IMMEDIATE_ENTRY_AND_LTF_NOISE_RESEARCH_CHECKPOINT_20260913.md`
10. `docs/ea/v9/V9_LIQUIDITY_TOPOLOGY_AND_JOURNEY_VALIDATION_CHECKPOINT_20260914.md`
11. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_POST_TOPOLOGY_JOURNEY_VALIDATION_20260914.md`
12. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
13. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
14. current code/tool parity state.

Older FLOW_ROUTE, H1-state-action, COUNTER/WITH_PARENT, scheduler, AI-direction, and LTF-trigger documents remain history unless explicitly retained by the authority map.

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

No count, timeout, ATR, R, cooldown, retry, or trade-quota threshold is attached.

## 2. Immediate entry remains fixed for research

```text
causal meaningful H4-liquidity Arrival
-> update Grammar
-> if mechanically authorized
-> immediate Child entry
```

No separate M1/M5/M15 pattern is required.

LTF remains chronology/execution evidence, not the active edge-discovery layer.

## 3. Latest mechanical evidence

Relative active H4-liquidity geometry is the strongest current factual edge.

```text
D_same
D_opposite
SAME_NEAREST := D_same < D_opposite
```

Consumed directional validation:

```text
2024      SAME_NEAREST 163/216 = 75.5%
2025H1    SAME_NEAREST  76/90  = 84.4%
2026JF    SAME_NEAREST  18/20  = 90.0%

combined  SAME_NEAREST 257/326 = 78.8%
combined  NOT SAME      66/123 = 53.7%
```

Absence of SAME_NEAREST is not reversal authority.

## 4. Latest journey evidence

Nearest-known same-side full TP cuts the right tail.

Strongest current broad consumed candidate:

```text
PRIMARY_ACTIVE
-> immediate entry
-> causal H1 structural Hard SL
-> hold through same-side H4 liquidity consumption
-> first opposite H4 liquidity Arrival opens CHALLENGED
-> CHALLENGED = mandatory Child-management boundary candidate
```

One-position comparator, all eligible `PRIMARY_ACTIVE` arrivals:

```text
2024      +43.84R  PF 2.41  DD 4.43R
2025H1    +20.29R  PF 3.20  DD 2.53R
2026JF     +8.08R  PF 3.08  DD 2.05R
combined  +72.21R  PF 2.63  DD 4.43R
```

This is research evidence, not production authority.

## 5. Current interpretation of SAME_NEAREST

Do not silently promote:

```text
SAME_NEAREST -> only trades allowed
```

Current evidence supports:

```text
SAME_NEAREST
= positive continuation-quality information
```

The broad `PRIMARY_ACTIVE` universe remains valid for current mechanical research because the journey-management candidate retained stronger total participation and robust cross-period expectancy.

## 6. Hard SL status

Fixed numeric SL values are not authority.

2026JF falsified the idea of selecting a consumed-optimized fixed 15/30 GOLD stop for the SAME_NEAREST journey candidate.

Current structural candidate:

```text
causally known active H1 swing liquidity
opposite the Child
known before entry
Hard SL fixed before entry
never widened
```

## 7. CHALLENGED status

For new entries:

```text
CHALLENGED = UNRESOLVED / NO NEW DIRECTIONAL EDGE
```

For an already-open Child:

```text
CHALLENGED
= strongest current management-boundary candidate
```

Whether final policy is full exit, partial realization, or mandatory review is the immediate unresolved question.

## 8. Active next work

Use:

`V9_NEXT_RESEARCH_CONTRACT_POST_TOPOLOGY_JOURNEY_VALIDATION_20260914.md`

Order:

```text
1. freeze standalone reproduction + hashes
2. freeze exact H1 structural selection
3. freeze exact CHALLENGED management action
4. study multi-Child/exposure separately
5. cost/spread sensitivity
6. deterministic dual-clock runtime parity
7. hidden-gate review only after all gates pass
8. AI later
9. optional LTF-entry refinement later still
```

## 9. Permanent guardrails

- no future peek;
- no hindsight backfill;
- stopped Child is dead;
- Parent and Child remain separate;
- Hard SL fixed before entry and never widened;
- code/runtime owns clocks, geometry, fills, and R arithmetic;
- `PRICE_REVEALED_CUTOFF <= INFORMATION_KNOWN_AT`;
- explicit uncertainty is valid;
- no hidden minimum-R, ratio threshold, cooldown, retry cap, no-chase, duration limit, forced side balance, or trade quota;
- `2025-07` remains locked;
- `2021` remains untouched.
