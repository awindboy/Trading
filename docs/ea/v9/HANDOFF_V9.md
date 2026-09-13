# V9 Development Handoff

Last updated: `2026-09-14`
Status: `ACTIVE / TOPOLOGY EDGE VALIDATED / JOURNEY PAYOFF CANDIDATE VALIDATED`
Production authority: `NONE`
EA authority: `NONE`
Base GitHub HEAD before packet: `753fb412a7e87b2e329ac9462107c1bad07b5e6d`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## Current resume point

Do not return to AI direction selection or LTF entry-pattern optimization.

The latest consumed research has now established two important mechanical facts.

### 1. Relative H4 liquidity topology carries direction information

```text
combined SAME_NEAREST
257 / 326 = 78.8% continuation

combined NOT SAME_NEAREST
66 / 123 = 53.7%
```

2026JF independently reproduced the separation:

```text
SAME_NEAREST 18 / 20 = 90.0%
NOT SAME     12 / 20 = 60.0%
```

Treat SAME_NEAREST as positive quality information, not a mandatory trade gate and not a reversal rule when absent.

### 2. First-target full TP was the main payoff bottleneck

The broad candidate that currently survives 2024, 2025H1 and 2026JF is:

```text
PRIMARY_ACTIVE
-> immediate entry
-> H1 structural Hard SL
-> hold through same-side H4 liquidity consumption
-> first opposite H4 liquidity Arrival
-> CHALLENGED
-> Child management boundary
```

One-position comparator:

```text
2024      +43.84R / PF 2.41
2025H1    +20.29R / PF 3.20
2026JF     +8.08R / PF 3.08
combined  +72.21R / PF 2.63
```

Worst-case treatment of all same-minute SL/semantic ambiguities as `-1R` remains positive:

```text
combined +57.21R
PF 1.97
```

## Important correction

Do not freeze fixed 15/30/50 GOLD stops from consumed optimization.

In 2026JF, SAME_NEAREST + CHALLENGE_EXIT:

```text
15 GOLD -> -9.84R
30 GOLD -> -9.92R
50 GOLD -> +5.75R
H1 structural -> +2.04R
```

The stable finding is structural invalidation, not a selected fixed number.

## Immediate next work

1. Freeze the exact reproduction implementation and ledger hashes.
2. Decide exact open-Child action at `CHALLENGED`: full exit, partial realization, or mandatory review.
3. Preserve the H1 structural Hard SL convention.
4. Study overlapping/repeated Children separately; do not turn one-position into hidden authority.
5. Add spread/cost sensitivity.
6. Port the candidate to the deterministic dual-clock runtime and prove parity.
7. Keep 2025-07 locked until the full mechanical/runtime packet is frozen.

## Permanent guardrails

No future peek, no hindsight rescue, no hidden minimum-R, ratio threshold, cooldown, retry cap, no-chase, duration timeout, trade quota, or forced direction balance.
