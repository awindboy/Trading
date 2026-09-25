# V12 Phase 1Q — third-and-later stop-chain result

Status: **complete and reproducible / M15 deep-churn layer passes / no action authority**  
Date: `2026-09-25`

## Question and population

After two causally completed consecutive stopped `k=1` candidates, can the
third or later stopped candidate be identified without using a cooldown?

All four lower clocks were tested: H2 (`357` chain-state candidates), H1
(`686`), M30 (`1,249`), and M15 (`2,285`). Two independent six-file packs are
byte-identical.

## Result

Only M15 static-time history and M15 session-path history pass every frozen
gate. H2/H1/M30 often improve repeat-stop log loss, but fail maximum-streak,
tail-preservation, or equal-stop-budget requirements. Their deeper-chain test
cells are also much smaller.

| M15 chain layer | Third-plus stops removed | Child retention | Tail-R retention | Max streak | Net R | Equal-stop-budget R |
|---|---:|---:|---:|---:|---:|---:|
| Session path | 31.65% | 99.10% | 97.36% | `5 -> 4` | 436.97 | 443.56 |
| Static time | 36.69% | 98.96% | 96.98% | `5 -> 4` | 429.94 | 437.48 |
| Baseline | — | 100% | 100% | 5 | 459.52 | 459.52 |

Both models preserve at least 94.9% of tail R in every fold and remain positive
in every fold. Session path retains more raw and equal-stop-budget R, so it is
the less destructive of the two. LONG and SHORT remain positive, as do 2025
and 2026.

## Interpretation

M15 has two different roles:

- as a general after-one-stop admission clock, it is too noisy and removes too
  much right-tail capital (Phase 1O);
- after two already-known consecutive failures, its local session-path state
  contains useful information about whether churn will continue.

That is a state-conditional observation role, not a universal M15 strategy.
The passing layer changes only about 1% of all M15 candidates. It reduces the
rare maximum chain by one, but does not meet the user's aspirational `1–2`
maximum and does not improve win rate materially (`33.746% -> 33.759%` for
session path). It is defensive: raw R falls by `22.56R`, although loss-budget
retention remains within the frozen tolerance.

No cooldown, every-third-trade skip, score threshold, session veto, sizing map,
EA, or trade authority is created. This result is consumed development evidence
and requires independent validation before it can influence exposure.
