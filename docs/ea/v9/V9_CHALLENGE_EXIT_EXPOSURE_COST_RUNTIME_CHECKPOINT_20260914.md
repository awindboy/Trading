# V9 CHALLENGED Exit + Exposure + Cost + Runtime Checkpoint

Date: `2026-09-14`
Status: `CONSUMED-DATA RESEARCH CHECKPOINT / MECHANICAL FREEZE CANDIDATE / NOT PRODUCTION AUTHORITY`
Base GitHub HEAD: `925368270b8bf91ba70936e8b3a1c1832813091a`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Purpose

The previous checkpoint established:

```text
relative H4-liquidity topology contains continuation information
+
nearest-target full TP cuts the right tail
+
H1 structural Hard SL + CHALLENGED journey boundary
survives 2024 / 2025H1 / 2026JF
```

This checkpoint resolves the next contract items:

1. exact H1 structural selection;
2. full exit vs partial realization vs hold/review at `CHALLENGED`;
3. repeated/overlapping Child exposure;
4. M1 spread-cost sensitivity;
5. deterministic dual-clock runtime parity and restart parity.

No new LTF trigger, ratio threshold, minimum-R rule, cooldown, retry cap, duration rule, or AI selector was introduced.

---

## 2. Exact H1 structural Hard SL convention

Candidate geometry remains the causal two-left / two-right H1 swing-liquidity engine.

At Child entry time `T`:

```text
ACTIVE_H1_OBJECT
= OBJECT_KNOWN_AT <= T
  and object not raided at or before T
```

LONG:

```text
Hard SL
= highest active H1 SELL_SIDE swing price
  strictly below entry
```

SHORT:

```text
Hard SL
= lowest active H1 BUY_SIDE swing price
  strictly above entry
```

The selected Hard SL is fixed before entry and never widened.
If no valid opposite H1 structural swing exists, no Child is opened.

Coverage:

| Block | Opportunities | Valid H1 SL | Coverage | Median SL | P10 | P90 |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 286 | 284 | 99.3% | 21.62 GOLD | 10.34 | 43.46 |
| 2025H1 | 125 | 125 | 100% | 31.59 GOLD | 17.33 | 61.83 |
| 2026JF | 41 | 41 | 100% | 80.90 GOLD | 42.19 | 251.23 |

The large cross-period scale shift explains why a consumed-optimized fixed numeric stop did not generalize. Structural distance adapts automatically without adding an ATR or fixed-GOLD threshold.

---

## 3. Exact CHALLENGED action study

### 3.1 Full exit candidate

Existing open Child:

```text
PRIMARY_ACTIVE
-> same-side H4 liquidity delivery
   HOLD

PRIMARY_ACTIVE
-> first opposite H4 liquidity delivery
-> CHALLENGED opens
-> FULL EXIT candidate
```

After that exit, the strategy remains flat while `CHALLENGED` is unresolved.
When the next H4-liquidity delivery resolves the Grammar back to `PRIMARY_ACTIVE`, that resolving Arrival is a new eligible mechanical entry event.

Therefore full exit at CHALLENGED does not permanently abandon the larger journey. It removes the Child during semantic uncertainty and permits re-entry after the market earns a new active side.

### 3.2 Hold-through-challenge / FLIP comparator

For Children that actually reached CHALLENGED and for which both full-exit and hold-to-FLIP paths resolved:

| Block | N | Mean incremental R from holding beyond CHALLENGED | Median | Hold better rate |
|---|---:|---:|---:|---:|
| 2024 | 164 | **-0.092R** | -0.227R | 17.1% |
| 2025H1 | 76 | **+0.876R** | -0.219R | 27.6% |
| 2026JF | 19 | **-1.029R** | -0.682R | **0.0%** |
| Combined | 259 | +0.124R | -0.235R | 18.9% |

The pooled mean is positive only because a small 2025H1 right tail dominates. The median is negative and the period sign is unstable.

### 3.3 Partial realization comparator

A common one-position entry cohort was used so the exit policy alone changed.
The study linearly compared:

```text
100% exit at CHALLENGED
75 / 25
50 / 50
25 / 75
0% exit / 100% hold to FLIP
```

No split dominates across periods.

- 2024: increasing hold fraction does not improve the result.
- 2025H1: increasing hold fraction materially helps.
- 2026JF: increasing hold fraction materially hurts.

A partial fraction would therefore be a new optimized parameter without cross-period support.

### 3.4 Mechanical review-resolver audit

Relative H4 topology was also recomputed at the moment CHALLENGED opened, asking whether the nearer old-primary vs challenger destination predicts who resolves the challenge.

```text
2024 usable accuracy:   59.3%
2025H1 usable accuracy: 64.3%
2026JF usable cases:    0
combined:               60.6%
```

2026JF challenge events generally had no usable two-sided active H4 target pair immediately after challenge.

Current-R sign and entry topology also failed to provide a stable cross-period HOLD-vs-EXIT resolver.

### 3.5 Current decision

The simplest surviving consumed-data action is:

```text
OPEN CHILD + CHALLENGED
-> FULL EXIT
```

This is promoted to the current **mechanical research freeze candidate**, not production authority.

---

## 4. Repeated / overlapping Child exposure study

If every eligible `PRIMARY_ACTIVE` Arrival opens a new full-risk Child while existing Children remain open, overlap becomes large:

| Block | Valid entries | Max concurrent Children | Entry while another Child already open |
|---|---:|---:|---:|
| 2024 | 284 | **11** | 69.0% |
| 2025H1 | 125 | **10** | 72.8% |
| 2026JF | 41 | **8** | 73.2% |

Full stacking remains profitable in R accounting, but it permits up to 8-11 simultaneous full-risk Children and therefore does not provide a sane route-level exposure policy.

The count of existing Children at entry also does not earn a retry/stack cap. Later entries remain positive in some periods and deteriorate in others. No fixed `N` is promoted.

---

## 5. Exposure policy comparators

### 5.1 FULL_STACK

Every valid Arrival opens a 1R Child.

Combined consumed result:

```text
resolved 393
Total R  +222.67R
PF         2.50
Max trade-sequence DD 14.66R
max simultaneous Children 11
```

This result is not directly acceptable as a policy because route-level simultaneous risk is not bounded.

### 5.2 ONE_POSITION

```text
one active Child at a time
new same-side eligible Arrivals while open are observed but do not open another Child
Child remains alive until Hard SL or CHALLENGED
```

Combined:

```text
resolved 115
WR        46.1%
Total R  +72.21R
Mean R   +0.628R
PF         2.63
Max DD     4.43R
Avg winner +2.20R
Avg loser  -0.71R
Payoff      3.08
```

Cross-period:

```text
2024    +43.84R / PF 2.41
2025H1  +20.29R / PF 3.20
2026JF   +8.08R / PF 3.08
```

### 5.3 REPLACE_CHILD

Threshold-free comparator:

```text
if one Child is open
and a new eligible same-primary H4 liquidity Arrival occurs:
    close old Child at the new Arrival boundary
    open a new Child immediately
    use the newly causal H1 structural Hard SL
```

This keeps maximum simultaneous Child count at one while participating in every eligible Arrival.

Combined gross:

```text
resolved 414
WR        72.9%
Total R  +90.66R
Mean R   +0.219R
PF         2.03
Max DD     6.96R
Avg winner +0.59R
Avg loser  -0.79R
Payoff      0.75
```

Cross-period gross:

```text
2024    +48.62R / PF 1.85
2025H1  +25.91R / PF 2.10
2026JF  +16.13R / PF 3.19
```

REPLACE_CHILD increases opportunity capture and total R, but fragments the right tail back into small winners and materially reduces payoff ratio.

### 5.4 Current exposure interpretation

Because the current research objective is specifically to preserve the newly recovered large-winner / favorable-payoff structure, the simplest current freeze candidate is:

```text
ONE ACTIVE CHILD PER GOLD# MARKET
```

This is now an explicitly studied exposure convention, not a hidden retry limit or trade quota.

`REPLACE_CHILD` remains a secondary campaign-harvesting comparator. It is not promoted into the core policy at this checkpoint.

---

## 6. Spread / cost sensitivity

The M1 `<SPREAD>` field was used as a **sensitivity proxy**, not exact historical Bid/Ask fill authority.
GOLD# quotes use 0.01 price-point increments in the supplied M1 file, so:

```text
spread_price = SPREAD * 0.01
```

Chart candles are treated as the existing Bid-like price reference used by the research comparator.
Approximate spread cost is charged on the executable side:

```text
LONG  -> entry spread cost
SHORT -> exit spread cost
```

No spread threshold was mined.
Stress scenarios use 0x / 1x / 2x / 3x the observed M1 spread only.

### ONE_POSITION core

| Spread stress | Total R | PF | Max DD | Mean R |
|---|---:|---:|---:|---:|
| 0x | +72.21R | 2.63 | 4.43R | +0.628R |
| 1x | **+71.16R** | **2.59** | 4.56R | +0.619R |
| 2x | +70.11R | 2.54 | 4.68R | +0.610R |
| 3x | **+69.06R** | **2.50** | 4.81R | +0.601R |

At 1x observed spread, all three consumed blocks remain positive.
Across the 20 calendar months represented by the consumed blocks, 16 are positive under this comparator.

### REPLACE_CHILD

| Spread stress | Total R | PF | Max DD |
|---|---:|---:|---:|
| 0x | +90.66R | 2.03 | 6.96R |
| 1x | **+87.33R** | **1.98** | 7.13R |
| 2x | +83.99R | 1.93 | 7.33R |
| 3x | **+80.66R** | **1.88** | 7.57R |

18/20 represented months are positive at 1x observed spread, but payoff remains below 1 because the campaign is repeatedly realized and re-opened.

Commission and broker-specific slippage are not separately modeled because no authoritative commission schedule or exact executable fill stream is frozen here.

---

## 7. Deterministic dual-clock Arrival/Delivery runtime

New research runtime:

```text
scripts/v9_arrival_delivery_runtime.py
runtime version = v9-arrival-delivery-runtime-1
```

Current script SHA256 in this packet:

```text
2fe5246cf867bb119eedf8aaa506776786cbe59cee9d7dbb2b3479aee1b1355a
```

The runtime:

1. validates the authoritative full M1 SHA256;
2. reads only frozen consumed byte ranges;
3. reconstructs H1/H4 sequentially;
4. separates completed-bar information from current-row OHLC reveal;
5. births two-left/two-right H1/H4 liquidity causally;
6. consumes liquidity only on later revealed M1 price;
7. emits Arrival / PRIMARY_ACTIVE / CHALLENGED events deterministically;
8. chooses the H1 structural Hard SL from active known objects;
9. continuously guards Hard SL;
10. applies CHALLENGED full-exit management;
11. supports ONE_POSITION and REPLACE research exposure modes;
12. persists full state and resumes without recomputing future information.

Frozen consumed source ranges:

```text
2024
  start_offset 43348274
  end_offset   65173328

2025H1
  start_offset 65173328
  end_offset   75912993

2026JF
  start_offset 86972434
  end_offset   90428045
```

`2025-07` OHLC is outside the authorized 2025H1 byte range.

---

## 8. Runtime parity

Sequential runtime vs frozen research ledger:

```text
2024
  Arrival core parity PASS
  Trade core parity   PASS
  +43.8428228413R

2025H1
  Arrival core parity PASS
  Trade core parity   PASS
  +20.2899178305R

2026JF
  Arrival core parity PASS
  Trade core parity   PASS
  +8.0791431355R
```

### Restart parity

For each block, replay was stopped while a Child was open, full runtime state was serialized, then replay resumed.

For both `ONE_POSITION` and `REPLACE` modes:

```text
Arrival ledger: byte-identical
Object ledger:  byte-identical
Trade ledger:   byte-identical
```

across 2024 / 2025H1 / 2026JF.

This closes the major consumed-data deterministic runtime-parity gate for the Arrival/Delivery candidate.

---

## 9. Mechanical research freeze candidate

The simplest policy supported by the current consumed evidence is now:

```text
MARKET
  GOLD# only

GRAMMAR
  MOVING / ARRIVAL
  PRIMARY_ACTIVE / CHALLENGED

ENTRY
  eligible H4-liquidity Arrival
  after Grammar resolves to PRIMARY_ACTIVE
  immediate at Arrival boundary reference

TOPOLOGY
  SAME_NEAREST is context / quality evidence only
  not an entry veto
  NOT SAME != FLIP

HARD SL
  nearest causally-known still-active opposite H1 swing liquidity
  two-left / two-right
  fixed before entry
  never widened

EXPOSURE BASELINE
  one active Child at a time

WHILE OPEN
  same-side H4 liquidity Arrival -> HOLD

  opposite H4 liquidity Arrival
  -> CHALLENGED
  -> FULL EXIT

AFTER CHALLENGE
  remain flat while unresolved
  next resolving H4-liquidity Arrival may authorize a fresh Child

AMBIGUITY
  SL and semantic exit in the same M1
  -> INTRAMINUTE_EXECUTION_AMBIGUOUS
  -> never invent favorable ordering
```

No fixed TP is required.
The right tail is preserved until the Grammar itself becomes uncertain.

---

## 10. Hidden-gate review

Despite the strong consumed result and deterministic runtime parity:

```text
2025-07 remains LOCKED.
```

Reason:

The mechanical semantic/runtime policy is now close to frozen, but exact executable-price authority remains a research comparator:

```text
Arrival boundary = chart-price entry/exit reference
M1 spread = sensitivity proxy
exact broker Bid/Ask / slippage / gap-cross fill contract = not yet frozen
```

The next gate should freeze execution assumptions and produce one final mechanical-policy manifest/hash before any hidden replay.

Do not use the strength of the consumed result as permission to open the hidden block early.

---

## 11. Current conclusion

The positive result is no longer coming from one isolated feature.
It now survives as a coherent mechanical chain:

```text
Arrival / Delivery Grammar
+
relative H4-liquidity topology as context
+
causal H1 structural invalidation
+
CHALLENGED full-exit journey management
+
one-Child bounded exposure
+
observed-spread stress
+
deterministic dual-clock restart parity
```

The remaining work is execution/fill freeze and hidden-gate governance, not another round of entry-feature mining.
