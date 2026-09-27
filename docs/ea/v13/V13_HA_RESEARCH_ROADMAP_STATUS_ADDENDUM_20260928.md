# V13 HA research roadmap status addendum

Date: `2026-09-28`
Base GitHub `main`: `29e0073e57553d8fe1fd14b843daf09164a7a248`
Status: `HA-9 BREAKTHROUGH CANDIDATE / RESEARCH EA IMPLEMENTED / ACTUAL-TICK TEST PENDING`

| Stage | Status | Current consequence |
| --- | --- | --- |
| HA-0..HA-6 | consumed observation | historical representation/context evidence |
| HA-7 | rejected action | do not revive H1+volume veto |
| HA-8A | consumed model observation | no flip-score action |
| X1/X2 | negative external observations | stop simple EUR/USD rescue attempts |
| HA-8B/8C follow-on | consumed diagnosis | Child-level economic target more useful than Journey-birth target, but model lift modest |
| **HA-9** | **active breakthrough candidate** | add-on proof/lock/timeout EA ready for actual-tick validation |

## Objective change

Current research does not require preserving every large continuation Journey.
The first priority is loss-frequency reduction and ordinary trade-stream quality.
Tail loss remains disclosed through trimmed-P/L diagnostics.

## HA-9 development result

```text
Baseline losses: 2,427
HA-9 losses:     1,685   (-742 / -30.6%)

Baseline non-flat win rate: 37.08%
HA-9 non-flat win rate:     56.07%

trade-sequence DD: 3,756.99 -> 1,283.65
max consecutive losses: 25 -> 14
```

HA-9 total net is lower (`+3,946.06` vs Baseline `+8,147.11`), but this no
longer dominates the evaluation because much of the Baseline total depends on a
small extreme-winner set. Removing the top 10 profitable Journeys leaves HA-9
slightly positive while Baseline is deeply negative.

## Immediate next step

No new data and no additional model family are required before execution work.
Run the new research EA on canonical actual ticks and produce event/economic
parity. If execution parity fails, fix semantics before changing strategy.
