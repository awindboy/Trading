# V9 Development Handoff

Last updated: `2026-09-14`
Status: `ACTIVE / CONSUMED MECHANICAL POLICY FREEZE CANDIDATE / EXECUTION FREEZE NEXT`
Production authority: `NONE`
EA authority: `NONE`
Base GitHub HEAD before packet: `925368270b8bf91ba70936e8b3a1c1832813091a`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## Current resume point

Do not return to AI direction selection, LTF entry-pattern optimization, fixed-GOLD stop selection, or new feature mining.

The consumed mechanical research has converged on a simple candidate:

```text
PRIMARY_ACTIVE H4-liquidity Arrival
-> immediate entry if flat and H1 structural SL exists
-> H1 structural Hard SL fixed before entry
-> same-side H4 liquidity arrivals: HOLD
-> first opposite H4 liquidity Arrival: CHALLENGED
-> FULL EXIT Child
-> no new Child while CHALLENGED
-> after H4-liquidity resolution returns PRIMARY_ACTIVE,
   a later/current resolving Arrival may authorize a fresh Child
```

`SAME_NEAREST` remains useful continuation-quality context, not a mandatory entry filter.

## Why CHALLENGED full exit currently wins

Holding beyond challenge was period-unstable:

```text
mean incremental R from holding past CHALLENGED
2024     -0.092R
2025H1   +0.876R
2026JF   -1.029R
combined +0.124R
median combined -0.235R
hold better only 18.9% of comparable cases
```

The pooled positive mean was driven by the 2025H1 right tail. Partial-exit fractions merely interpolate between unstable behaviors and add a numeric parameter. A topology resolver at challenge was only about `60.6%` accurate where usable and had no usable two-sided 2026JF cases.

Therefore current consumed freeze candidate:

```text
CHALLENGED -> FULL EXIT
```

This is a Child resolution rule, not proof the Parent Journey permanently reversed.

## Exposure result

Blind full stacking is not acceptable as the core baseline:

```text
max simultaneous Children
2024    11
2025H1  10
2026JF   8
```

The threshold-free `REPLACE_CHILD` comparator stayed positive and increased gross total R, but it cut the right tail back down:

```text
combined +90.66R / PF 2.03
avg winner ~0.59R
payoff ~0.75
```

The user's current problem is improving payoff, so the freeze baseline remains:

```text
ONE ACTIVE CHILD
```

Combined gross:

```text
resolved 115
WR 46.1%
Total +72.21R
Mean +0.628R
PF 2.63
Max DD 4.43R
Avg winner +2.20R
Avg loser -0.71R
Payoff ~3.08
```

## Structural SL status

Exact current selector:

```text
LONG  -> highest active known H1 SSL below entry
SHORT -> lowest active known H1 BSL above entry
```

H1 swing geometry is causal two-left / two-right. The structural scale changed materially across periods, so fixed 15/30/50 GOLD values remain rejected as authority.

## Cost sensitivity

ONE_POSITION result under observed M1-spread proxy:

```text
0x +72.21R / PF 2.63
1x +71.16R / PF 2.59
2x +70.11R / PF 2.54
3x +69.06R / PF 2.50
```

This is encouraging robustness evidence, but exact broker Bid/Ask entry/exit fill, commission and slippage are still unfrozen.

## Runtime result

`scripts/v9_arrival_delivery_runtime.py` now reproduces the policy sequentially from authoritative full-M1 byte ranges with source-hash checking and dual clocks.

Frozen consumed ranges in the packet:

```text
2024   start 43348274  end 65173328
2025H1 start 65173328  end 75912993
2026JF start 86972434  end 90428045
```

The 2025H1 range ends exactly before future-hidden July.

Exact one-position totals reproduced:

```text
2024      +43.8428228413R
2025H1    +20.2899178305R
2026JF     +8.0791431355R
```

Mid-open-position serialize/resume replay produced byte-identical Arrival/Object/Trade ledgers for all consumed blocks. `REPLACE_CHILD` restart parity also passed.

## Immediate next work

The edge-search phase is paused. Next contract is execution freeze only:

1. freeze exact immediate-entry executable-price rule;
2. freeze Hard-SL fill semantics;
3. freeze CHALLENGED exit executable-price rule;
4. freeze gap-cross and same-M1 ambiguity handling;
5. freeze official cost convention;
6. freeze source/runtime/ledger hashes into one manifest;
7. rerun all consumed ranges and require exact parity;
8. only then explicitly review the `2025-07` gate;
9. if hidden data is opened, no retuning after seeing it;
10. `2021` remains untouched.

## Permanent guardrails

No future peek, hindsight rescue, hidden minimum-R, ratio threshold, cooldown, retry cap, no-chase, duration timeout, forced direction balance, or trade quota.
