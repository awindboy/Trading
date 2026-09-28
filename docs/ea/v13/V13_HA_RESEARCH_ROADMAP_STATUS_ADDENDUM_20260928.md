# V13 HA research roadmap status addendum

Date: `2026-09-28`
Base GitHub `main`: `6ea22fe914a8a7cc459cb5bd939b8435335b77d6`
Status: `HA-9 CANDIDATE / ACTUAL-TICK CHILD ECONOMICS RECONSTRUCTED / EVENT PARITY PENDING`

| Stage | Status | Current consequence |
| --- | --- | --- |
| HA-0..HA-6 | consumed observation | historical representation/context evidence |
| HA-7 | rejected action | do not revive H1+volume veto |
| HA-8A | consumed model observation | no flip-score action |
| X1/X2 | negative external observations | stop simple EUR/USD rescue attempts |
| HA-8B/8C follow-on | consumed diagnosis | Child-level economic target more useful than Journey-birth target, but model lift modest |
| **HA-9** | **active research candidate** | supplied actual-tick report reconstructed; Journal/event parity still required |
| HA-9 trade-mode follow-on | consumed mechanism diagnosis | timeout, exit-horizon, re-arm and runner variants rejected |

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

The supplied MT5 report provides preliminary actual-tick economics, but not the
Journal events needed to prove proof/timeout/lock timing parity. Obtain and
compare that event stream before changing HA-9. The trade-mode follow-on branch
has been exhausted without a promoted action; see
`V13_HA9_TRADE_MODE_COVERAGE_20260928.md`. Do not add a new model family,
timeout length, cooldown, runner exception or sizing rule to rescue consumed
results.
