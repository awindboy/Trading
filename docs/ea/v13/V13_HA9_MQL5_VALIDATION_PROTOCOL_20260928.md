# V13 HA-9 MQL5 validation protocol

Date: `2026-09-28`
Status: `NEXT REQUIRED WORK`
EA: `mt5/experts/V13HAProofLockMax10EA.mq5`

## Required tester setup

- Symbol: broker `GOLD#` matching the V13 source feed.
- Model: `Every tick based on real ticks`.
- Canonical comparison window: 2024-01-01 through 2026-08-28 available history.
- Hedging account mode is required because Children are independent positions.
- Fixed lot per Child for structural parity first. Do not add risk sizing until
  action/event parity is established.

## Event parity to verify

1. standard H4 HA colors and Journey births;
2. successful Child numbering up to 10;
3. Child #1 never receives proof/timeout/lock management;
4. add-on proof target equals the immediately preceding signal H4 raw high/low;
5. timeout occurs on the first executable tick after exactly one proof H4;
6. proof on the first tick of a new H4 cannot rescue an expired Child;
7. breakout lock is armed on proof but can close only from the following tick;
8. an individually closed Child is never backfilled;
9. opposite HA close-all supersedes an individual pending timeout/lock close;
10. no duplicate order after ambiguous execution failure.

## Economics to report

The tester receipt must report both traditional economics and the revised V13
quality metrics:

- Child wins/losses/flats and non-flat win rate;
- loss reduction versus Baseline 0;
- PF and net profit;
- max drawdown and max consecutive losses;
- year slices;
- 10/25/50/100-trade chronological block positivity;
- Top-1/3/5/10/20 profitable-Journey removal diagnostic;
- exit reason counts: HA exit / proof timeout / breakout lock.

## Stop conditions

Stop and repair implementation before interpretation if event parity fails.
Do not tune proof duration, proof target or lock formula to compensate for a
compile/execution mismatch.

A materially weaker actual-tick result is evidence about execution realism and
must be explained before any further strategy complexity is added.
