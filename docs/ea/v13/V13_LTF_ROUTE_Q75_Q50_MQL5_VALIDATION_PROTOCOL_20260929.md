# V13 LTF route q75/q50 MQL5 validation protocol

Date: `2026-09-29`
Status: `COMPLETED FOR RECONSTRUCTION A / NOT LIVE AUTHORITY`

## Required artifacts

1. regenerated final q75-entry/q50-repair policy ledger;
2. ledger SHA-256 and row-count receipt;
3. fold/threshold manifest proving strict-prior OOF construction;
4. `mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5` and compiled EX5;
5. Strategy Tester report and complete Journal.

Reconstruction A completed these checks through the complete Journal and
EA-emitted balance/equity telemetry. The terminal did not emit the requested
HTML report in the portable run, so the immutable Journal, per-event balance
deltas, final tester balance and exact-tick equity telemetry are the economic
source. See the actual-tick receipt and parity JSON.

## Ledger checks

- exact header required by the action contract;
- one ENTRY and one EXIT per `event_id`;
- ascending `action_time`, then `action_order`;
- `EXIT` before `ENTRY` at equal timestamps;
- all entries exactly `0.01` lot;
- no entry action after its frozen exit time;
- no duplicate ids, unresolved positions or actions beyond the canonical cutoff;
- policy counts and year slices reconcile to the regenerated research ledger.

## Tester settings

```text
symbol: GOLD#
account mode: hedging
model: Every tick based on real ticks
lot: 0.01 fixed
date: cover the complete frozen ledger
spread/commission: broker tester values
optimization: off
```

Copy the ledger to `Terminal Common\Files\V13\` unless the EA input selects the
terminal-local Files area. Ledger timestamps are MT5 server time.

## Required Journal parity

Parse every `V13Q75_EVENT|` line and reconcile:

- INIT_OK and ledger event count;
- every ENTRY/EXIT event id and timestamp order;
- retryable ORDER_FAIL events and eventual resolution;
- zero permanent HALT;
- zero unexpected `EXIT_NO_POSITION` except documented expired-entry pairs;
- zero position-count mismatch;
- REPLAY_COMPLETE with zero own positions.

The first actual tick after a frozen action timestamp is the executable print.
Slippage and spread may change economics but may not change policy membership.

## Acceptance boundary

Only after event parity may actual tester evidence control execution economics.
Compare at minimum trades, wins/losses/flats, net, PF, average
winner/loss, payoff, expectancy, realized and floating DD, streaks,
10/25/50/100-trade blocks, year slices and concurrency.

A successful compile proves only MQL5 syntax. A completed tester run without
Journal parity does not prove q75/q50 policy parity. Embedded-model EA work
begins only after both policy replay parity and action-candidate promotion; it
must reproduce the frozen ledger before it can replace it. Reconstruction A
passed parity but was not promoted under the ordinary-equity objective, so an
embedded production implementation is not authorized.
