# V12 Phase-1C CRT-protected carry and repair result

Date: `2026-09-24`

Status: `REPRODUCIBLE CONSUMED-DEVELOPMENT MECHANISM RESULT / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1c-crt-protected-carry-repair-v1`

## Scope and integrity

Phase 1C changed the holding clock, not the selected V10 entry set or R7G units.
It tested whether an aligned Child that reached its ordinary FAST-NHA exit could
remain alive when the same Phase-1B CRT Parent was still active and no opposite
Parent had been authorized. The Child retained its original Hard SL and exited
at the first Hard-SL touch or causal Parent termination.

The primary target-led view additionally required the origin C1 opposite edge
to remain unresolved at the NHA decision. A separate one-unit `REPAIR` Child
used the frozen V10 k1 entry/SL only when FAST returned to the same still-active
Parent direction.

Verified raw M1 was streamed only through `2026-09-18 23:57`. Zero later price
rows were parsed. Two independent builds passed complete validation and all
seven files were byte-identical.

The unchanged baseline reproduced `1,649` Children, `3,881` funded units,
`486` stopped units, and `+741.010865R`.

## Event population

- `118` selected Children across `60` unique old-journey bridge episodes were
  eligible for broad Parent-active carry.
- `31` episodes returned to the original FAST direction under the same Parent
  and had a valid causal k1; `29` Parents ended before such a repair.
- only `10` bridge episodes (`12` selected Children) still had the origin C1
  opposite edge unresolved at NHA;
- only `2` episodes still had that target unresolved when repair occurred.

The last two counts expose a representation gap: Phase 1B often leaves a
journey active after its original C1 targets have already been consumed.

## Selected-portfolio result

| Policy | Changed Children | Stops | Stopped units | Net R | PF_R | >=5R right tail | Grouped realized DD_R | Funded unit-hours |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V10 baseline | 0 | 232 | 486 | +741.01 | 1.682 | +1011.41 | 57.00 | 81,540.8 |
| all active-Parent carry | 118 | 258 | 552 | +764.20 | 1.674 | +1062.79 | 62.49 | 86,090.3 |
| unfinished-target carry | 12 | 237 | 499 | +758.02 | 1.695 | +1032.07 | 56.91 | 82,281.1 |

Broad carry gained `+23.19R`, but added `26` stopped Children, `66` stopped
units, `5,549.5` funded unit-hours, and `5.49R` of grouped realized drawdown.
Its median changed-Child delta was negative. The best bridge contributed
`+36.94R`; removing that one bridge changes the total carry delta to
`-13.75R`. The 2026 portfolio lost `40.18R` versus baseline. Therefore
`Parent active` alone is not a valid holding rule.

The unfinished-target view gained `+17.01R`, added five stopped Children and
13 stopped units, preserved the five-stop maximum chain, and left maximum
concurrent units unchanged at 48. Its grouped realized drawdown was slightly
lower. However, it changed only 12 Children, was negative versus baseline in
2025, and its best episode supplied `+14.59R` or `85.8%` of the total gain.
Excluding that episode leaves only `+2.42R`. This is insufficiently broad and
stable for promotion.

## Repair result

The 31 one-unit repair Children earned `+5.12R`, PF `1.55`, with four Hard SLs.
The same k1 population under the ordinary V10 first-NHA exit earned `+4.70R`, so
changing its exit clock added only `+0.42R`.

`26` of the 31 repair k1s were already selected by R7G. On those already-funded
Children the Parent clock lost `1.96R` versus the ordinary exit. Only five
repair k1s were incremental to the selected portfolio; they earned `+3.08R`
with two stops, far too few for an admission conclusion.

Adding one repair unit improved direction-adjusted basket average entry in only
`5 / 31` cases (`16.1%`). It improved none of the two still-unfinished-target
cases. A later PHA return is usually a less favorable price, so “averaging the
entry” is not the mechanism. Any value would have to come from renewed delivery,
not a reliably better average price.

## Decision

The user's distinction is valid: an NHA can be Child interruption without being
the end of the Parent Journey. Phase 1C also proves that changing the exit clock
can recover additional right-tail R. But the current Phase-1B state is not yet
specific enough to decide when to carry:

- active-Parent carry is too broad, increases stop burden and drawdown, and is
  dominated by a few episodes;
- the target-led subset is directionally cleaner but too sparse because only
  one immutable C1 opposite-edge target is represented;
- PHA repair largely duplicates Children V10 already admits and does not usually
  improve average entry.

No carry, repair entry, capital addition, or sizing rule is promoted.

## Next research boundary

The next structural task is not a carry threshold. It is a causal rolling target
inventory for the Parent:

1. retain C1 midpoint and opposite edge as the first two objectives;
2. pre-register the next unresolved same-direction external liquidity object
   from the existing one-use H4/day/week/month inventory;
3. consume targets chronologically and require an explicit reframe before a
   finished target can be replaced;
4. classify NHA as counterflow, Parent termination, or target-complete reframe;
5. only then retest Child carry and one repair Child inside a genuinely
   unfinished Journey.

This must remain target-first and deterministic. It must not rank level families
from these outcomes, invent a weighted key-level score, or tune a carry duration.
The frozen post-cutoff shadow semantics remain unchanged, and `GOLD# 2021`
remains sealed.
