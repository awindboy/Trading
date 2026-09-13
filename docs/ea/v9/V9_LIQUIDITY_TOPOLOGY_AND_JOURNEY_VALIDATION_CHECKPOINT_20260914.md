# V9 Liquidity Topology + Journey Validation Checkpoint

Date: `2026-09-14`
Status: `CONSUMED-DATA RESEARCH CHECKPOINT / NOT PRODUCTION AUTHORITY`
Base GitHub HEAD: `753fb412a7e87b2e329ac9462107c1bad07b5e6d`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Future-hidden: `2025-07 LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Purpose

This checkpoint validates the leading mechanical V9 hypothesis on all currently consumed comparison blocks:

```text
2024
2025 Jan-Jun
2026 Jan-Feb
```

It keeps immediate entry fixed and asks two separate questions:

1. Does relative H4-liquidity topology carry stable continuation information?
2. Can the poor payoff of nearest-target harvesting be improved by holding the Child through same-side liquidity consumption and resolving it when the route becomes `CHALLENGED`?

This checkpoint does not unlock `2025-07` and does not touch `2021`.

## 2. Causal conventions

The study preserves current authority:

```text
TOP LEVEL
  MOVING
  ARRIVAL

H4 LIQUIDITY ARRIVAL
  = DELIVERY / PROGRESSION evidence

SLOW STATUS
  PRIMARY_ACTIVE
  CHALLENGED / UNRESOLVED
  PRIMARY_CONTINUES
  CHALLENGER_EARNED
```

H4 and H1 swing-liquidity geometry uses:

```text
2 left bars
2 right bars
```

A swing is available only after the second right bar is complete.

Dual-clock semantics are retained. Missing minutes are not synthesized. `OBJECT_KNOWN_AT` and price reveal remain separate. The 2024 and 2025 blocks use block-internal H4/H1 reconstruction with causal dual-clock completion; 2026JF is reconstructed independently from its consumed block and does not use hidden 2025H2 as warm-up.

## 3. Relative H4-liquidity topology

At every eligible `PRIMARY_ACTIVE` arrival:

```text
D_same
= distance to nearest active H4 liquidity
  in current primary direction

D_opposite
= distance to nearest active H4 liquidity
  in opposite direction
```

Candidate label:

```text
SAME_NEAREST
= both sides exist
  and D_same < D_opposite
```

Interpretation remains asymmetric:

```text
SAME_NEAREST     -> continuation support
NOT SAME_NEAREST -> uncertainty
NOT SAME_NEAREST != automatic flip
```

## 4. Cross-period directional validation

Labeled active-arrival results:

| Block | All active | SAME_NEAREST | NOT SAME_NEAREST |
|---|---:|---:|---:|
| 2024 | 200/285 = 70.2% | 163/216 = 75.5% | 37/69 = 53.6% |
| 2025H1 | 93/124 = 75.0% | 76/90 = 84.4% | 17/34 = 50.0% |
| 2026JF | 30/40 = 75.0% | 18/20 = 90.0% | 12/20 = 60.0% |
| Combined | 323/449 = 71.9% | 257/326 = 78.8% | 66/123 = 53.7% |

Result:

```text
relative H4-liquidity topology survives 2026JF
and remains materially informative.
```

The continuous ratio also remains monotonic.

Define:

```text
RATIO = D_same / D_opposite
```

Across all consumed blocks with both targets present:

| Pooled ratio quartile | Continuation |
|---|---:|
| nearest same-side Q1 | 87/95 = 91.6% |
| Q2 | 77/94 = 81.9% |
| Q3 | 66/94 = 70.2% |
| nearest opposite Q4 | 55/95 = 57.9% |

This is stronger evidence for a continuous geometry relationship than for a single optimized binary threshold.

No numeric ratio threshold is promoted.

## 5. First-target payoff problem

The old simple realization rule was:

```text
entry
-> nearest known same-side H4 liquidity
-> full TP
```

That produces high hit rates but cuts the right tail.

The consumed study showed that one destination being consumed does not imply route completion:

```text
DESTINATION_CONSUMED != ROUTE_COMPLETE
```

Therefore the payoff study held entry and Hard SL fixed and tested semantic journey exits.

## 6. Journey comparator

Primary candidate:

```text
PRIMARY_ACTIVE Child
-> same-side H4 liquidity arrivals do NOT force exit
-> first opposite H4 liquidity arrival
-> route becomes CHALLENGED
-> Child exit / mandatory management boundary
```

Comparator name:

`CHALLENGE_EXIT`

A later `CHALLENGER_EARNED` exit was also examined, but did not dominate consistently enough to replace the simpler first-challenge boundary.

## 7. Cross-period H1-structural + CHALLENGE_EXIT validation

One-position comparator, `CONTROL` = all mechanically eligible `PRIMARY_ACTIVE` arrivals:

| Block | Resolved | WR | Total R | Mean R | PF | Max DD | Avg Win | Avg Loss | Payoff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 75 | 41.3% | +43.84R | +0.585R | 2.41 | 4.43R | +2.42R | -0.71R | 3.42 |
| 2025H1 | 31 | 58.1% | +20.29R | +0.655R | 3.20 | 2.53R | +1.64R | -0.71R | 2.31 |
| 2026JF | 9 | 44.4% | +8.08R | +0.898R | 3.08 | 2.05R | +2.99R | -0.78R | 3.86 |
| Combined | 115 | 46.1% | +72.21R | +0.628R | 2.63 | 4.43R | +2.20R | -0.71R | 3.08 |

The same test restricted to `SAME_NEAREST` also remained positive in every block:

| Block | Resolved | WR | Total R | PF | Max DD |
|---|---:|---:|---:|---:|---:|
| 2024 | 67 | 40.3% | +42.20R | 2.58 | 4.01R |
| 2025H1 | 26 | 61.5% | +17.57R | 3.57 | 1.87R |
| 2026JF | 5 | 40.0% | +2.04R | 1.78 | 2.60R |
| Combined | 98 | 45.9% | +61.81R | 2.71 | 4.01R |

Interpretation:

```text
SAME_NEAREST remains valid continuation information,
but it is not yet justified as a mandatory entry veto.

The broad PRIMARY_ACTIVE universe
+
H1 structural Hard SL
+
CHALLENGED journey boundary
currently produces the strongest broad cross-period mechanical result.
```

## 8. 2026JF falsification of fixed numeric SL selection

The 2026JF block materially weakens the case for selecting a fixed numeric SL from earlier consumed periods.

For `SAME_NEAREST + CHALLENGE_EXIT + one-position`:

```text
FIXED 15 -> -9.84R
FIXED 30 -> -9.92R
FIXED 50 -> +5.75R
H1 structural -> +2.04R
```

Therefore:

```text
do not freeze 15 / 30 / 50 GOLD
from consumed optimization.
```

The structural H1 reference remains the cleaner candidate because it survives all three consumed blocks without adding a fixed price-distance parameter.

## 9. Ambiguity worst-case

For `CONTROL + H1 structural + CHALLENGE_EXIT + one-position`, forcing every same-M1 semantic/SL ambiguity to `-1R` gives:

```text
2024    +31.84R, PF 1.74
2025H1  +18.29R, PF 2.63
2026JF  +7.08R,  PF 2.45
Combined +57.21R, PF 1.97
```

For `SAME_NEAREST`:

```text
Combined +52.81R, PF 2.17
```

Thus the result is not created solely by favorable intraminute ordering assumptions.

## 10. What is now supported

Research evidence now supports:

```text
1. H4 relative-liquidity topology contains stable continuation information.

2. SAME_NEAREST should be treated as positive continuation context,
   not as automatic reversal authority when absent.

3. nearest-known-target full realization is too aggressive
   in cutting the right tail.

4. CHALLENGED is useful not only as semantic uncertainty
   but as a strong open-Child management boundary candidate.

5. causal H1 structural Hard SL is the strongest current
   cross-period structural invalidation candidate.

6. broad PRIMARY_ACTIVE participation should remain alive
   while SAME_NEAREST is treated as quality/probability context.
```

## 11. What is NOT frozen

Not yet authority:

```text
CHALLENGED -> mandatory production exit
one-position-only as final exposure policy
SAME_NEAREST -> mandatory entry filter
any fixed numeric SL
any minimum-R threshold
any ratio threshold
dynamic partial realization rule
portfolio stacking / netting policy
cost/slippage/live-fill assumptions
```

The strong consumed result is a candidate mechanical policy, not hidden-data permission.

## 12. Immediate next work

The next phase should no longer search for another entry trigger.

Priority:

```text
A. freeze exact reproducible implementation of:
   immediate entry
   H1 structural Hard SL
   CHALLENGED management boundary

B. audit whether CHALLENGED should mean:
   full exit
   partial realization
   or mandatory review
   without introducing hidden thresholds

C. study multi-Child / overlapping exposure separately

D. add spread/cost/executable-price sensitivity

E. prove deterministic runtime parity

F. only then review the 2025-07 hidden gate
```

Do not reopen AI or LTF entry optimization before these mechanical/runtime gates are complete.

## 13. Result files

See:

`docs/ea/v9/results/topology_journey_20260914/`

The package includes arrival, topology, H1/H4 object, trade-base, journey, one-position, split, ambiguity, and summary ledgers plus a manifest with hashes.
