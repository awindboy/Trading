# V13 objective and evaluation update — loss-frequency first

Date: `2026-09-28`
Status: `ACTIVE RESEARCH DOCTRINE / SUPERSEDES RIGHT-TAIL-FIRST INTERPRETATION`
Base GitHub `main` checked before this update: `29e0073e57553d8fe1fd14b843daf09164a7a248`
Market: `GOLD# ONLY`

## 1. Why this update exists

Earlier V13 work correctly discovered that many apparent reversal warnings occur
inside very profitable long Journeys. That evidence prevented weak filters from
being promoted. However, the research objective was subsequently clarified:

> The primary problem is not to preserve every large continuation winner. The
> primary problem is to reduce the many ordinary losing Children and persistent
> downward stretches so that the base stream of trades becomes more consistently
> upward. If this materially improves loss frequency and win rate, sacrificing
> part of the extreme right tail is an acceptable cost to measure rather than an
> automatic rejection reason.

This document changes **evaluation priority**, not historical facts. Old HA-6,
HA-7, HA-8, X1 and X2 contracts/receipts remain immutable evidence of what was
measured at that time.

## 2. Current primary evaluation order

For a V13 action experiment, inspect these first:

1. number and share of losing Children removed or converted to non-losses;
2. non-flat Child win rate;
3. consecutive-loss length;
4. chronological trade-stream drawdown and rolling/block P/L quality;
5. whether typical 10/25/50/100-trade blocks become more often positive;
6. year-level stability across the full consumed 2024-01-01..2026-08-28 window;
7. robustness after removing the largest profitable Journeys.

Net points and Profit Factor remain mandatory diagnostics, but a lower total
net caused by cutting a small number of very large winners does **not** by
itself reject a candidate when the ordinary trade stream improves materially.

## 3. Right-tail rule after this update

Right-tail accounting remains visible, but its role changes:

- **Historical role:** used as a major rejection argument when V13 was seeking a
  transition filter that would preserve Baseline-0 payoff shape.
- **Current role:** a cost/robustness diagnostic. Report how much large winners
  are reduced, then separately ask whether loss count, win rate, drawdown and
  trimmed equity improve.
- Do not use `a profitable long Journey was touched` as an automatic veto.
- Do not hide tail damage either. Keep Top-N profitable-Journey removal and
  long-Journey decomposition visible so the trade-off is explicit.

## 4. What does not change

- No hindsight trades.
- No future price before a decision/action timestamp.
- No post-hoc recovery of a closed Child.
- No side/year exception mined from consumed history.
- No hidden minimum-R, cooldown, retry, fixed no-chase or forced side balance.
- Baseline 0 remains the frozen comparator.
- 2024-2026 remains consumed development history; current results are not
  untouched validation.
- Actual-tick MT5 execution is required before any production authority.

## 5. Consequence for HA-9

The new add-on proof/lock candidate is evaluated primarily because it changes
loss frequency and the ordinary equity path, not because it maximizes Baseline-0
net points. Its tail sacrifice must be reported, but is not an automatic failure.
