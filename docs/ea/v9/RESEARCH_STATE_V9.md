# V9 Research State

Date: `2026-09-14`
Status: `ACTIVE / CONSUMED MECHANICAL POLICY FREEZE CANDIDATE / DETERMINISTIC RUNTIME PARITY PASSED`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`

## Current thesis

The strongest V9 mechanical candidate is now carried by:

```text
Arrival / Delivery Grammar
+
causal H1 structural invalidation
+
semantic journey harvesting to CHALLENGED
+
one-active-Child exposure baseline
```

Relative H4-liquidity topology remains useful context but does not need to be a mandatory trade gate.

## Directional topology evidence

```text
2024      SAME_NEAREST 163/216 = 75.5%
2025H1    SAME_NEAREST  76/90  = 84.4%
2026JF    SAME_NEAREST  18/20  = 90.0%
combined  SAME_NEAREST 257/326 = 78.8%
combined  NOT SAME      66/123 = 53.7%
```

No ratio threshold is authority. Absence of SAME_NEAREST is not reversal proof.

## Current mechanical policy candidate

```text
if Grammar after H4-liquidity Arrival is PRIMARY_ACTIVE
and no Child is open
and causal H1 structural SL exists:
    enter immediately in primary direction

while open:
    same-side H4 liquidity -> HOLD
    Hard SL -> Child dead
    opposite H4 liquidity -> CHALLENGED -> FULL EXIT

while CHALLENGED:
    no new directional Child

next H4-liquidity resolution:
    Grammar may return PRIMARY_ACTIVE
    and a mechanically eligible Arrival may authorize a fresh Child
```

## CHALLENGED decision evidence

Full exit is the simplest surviving action.

Holding past challenge to `CHALLENGER_EARNED` / resolution was unstable: combined median incremental R was negative and 2026JF mean incremental R was about `-1.03R`.

Partial exits did not dominate each consumed period and introduce an arbitrary fraction parameter.

A direct challenge-time topology resolver was insufficient (`~60.6%` where usable; no usable two-sided 2026JF cases).

Therefore current freeze candidate:

```text
OPEN CHILD + CHALLENGED -> FULL EXIT
```

## Exposure evidence

Full independent stacking can reach 11 simultaneous Children and is not the frozen baseline.

`REPLACE_CHILD` remained positive:

```text
combined +90.66R / PF 2.03 / DD 6.96R
```

but fragmented winner payoff:

```text
avg winner ~0.59R
avg loser  ~-0.79R
payoff     ~0.75
```

Current one-active-Child baseline preserves the desired right tail:

```text
2024      +43.84R / PF 2.41
2025H1    +20.29R / PF 3.20
2026JF     +8.08R / PF 3.08
combined  +72.21R / PF 2.63 / DD 4.43R

combined avg winner ~+2.20R
combined avg loser  ~-0.71R
payoff ~3.08
```

`ONE_POSITION` is an exposure convention, not a retry cap.

## Exact H1 structural SL

Current selector:

```text
LONG  -> nearest/highest active causally-known H1 SSL below entry
SHORT -> nearest/lowest active causally-known H1 BSL above entry
```

H1 swing geometry: two-left / two-right; object must already be known and active at entry.

Median SL distance by block:

```text
2024      ~21.6 GOLD
2025H1    ~31.6 GOLD
2026JF    ~80.9 GOLD
```

This scale shift is strong evidence against consumed-optimized fixed-GOLD SL authority.

## Cost sensitivity

Observed M1 spread proxy, ONE_POSITION:

```text
0x  +72.21R / PF 2.63
1x  +71.16R / PF 2.59
2x  +70.11R / PF 2.54
3x  +69.06R / PF 2.50
```

No spread threshold is introduced. Commission, slippage and exact executable Bid/Ask convention remain unresolved execution details.

## Runtime parity

New `v9_arrival_delivery_runtime.py`:

- verifies the authoritative source SHA256;
- consumes exact frozen byte ranges rather than scanning future-hidden data for strategy input;
- reconstructs H1/H4 causally with dual clocks;
- creates two-left/two-right H1/H4 liquidity objects;
- reproduces Grammar transitions, topology, H1 structural SL, one-position management and CHALLENGED full exit;
- persists resumable state.

Consumed full-source range replay exactly reproduced the frozen research totals.

Mid-open-position restart tests produced byte-identical Arrival/Object/Trade ledgers for 2024, 2025H1 and 2026JF. REPLACE comparator restart parity also passed.

## What is frozen only as a candidate

Supported for the next execution-freeze gate:

```text
Immediate PRIMARY_ACTIVE entry
H1 structural fixed Hard SL
same-side arrival HOLD
first CHALLENGED FULL EXIT
one active Child baseline
SAME_NEAREST as context only
```

Still not production authority:

- exact broker executable entry fill;
- exact CHALLENGED exit fill;
- gap-cross handling;
- same-M1 ambiguous ordering policy for official performance;
- commission/slippage;
- live position sizing/account-risk policy;
- future-hidden permission.

## Immediate next contract

Use:

`V9_NEXT_RESEARCH_CONTRACT_EXECUTION_FREEZE_AND_HIDDEN_GATE_20260914.md`

No further edge mining before that contract is completed.

## Data classification

```text
2024         consumed
2025 Jan-Jun consumed
2026 Jan-Feb consumed
2025-07      future-hidden LOCKED
2021         untouched reserve
```

Future-hidden gate remains `NOT SATISFIED` until the execution contract and freeze manifest explicitly pass.
