# V12 research state

Last synchronized: `2026-09-23`

## Status

`ACTIVE RESEARCH / ARCHITECTURE FROZEN FOR PHASE 0 / NO RESULT`

## Established inputs

- The supplied 28-page Korean CRT guide is a secondary synthesis of public Romeo
  material. Its SHA-256 is
  `16426b4f1ac3bac12c444d54c103b38760e1e1eb854dff1306467b906b1b6384`.
- The source grammar is broader than a three-candle picture: context, location,
  timing, trigger, target, and reevaluation matter.
- Every candle can be treated as a range. C1 defines a range, C2 tests/sweeps an
  extreme, and C3 is potential distribution/delivery only after causal evidence.
- A sweep followed by a close back inside and an accepted close outside are
  distinct branches.
- Beginner execution belongs after C2 closes. Predicting C2 while it forms is not
  the Phase-0 V12 task.
- The guide explicitly retains Monthly->Daily, Weekly->H4, and Daily->H1 examples.
  V12 initially uses W1->H4 and D1->H1 because they connect to the existing H4
  research without inventing a source claim.
- C1 50% is the first structural destination; the opposite extreme or older
  liquidity is a later destination. Target logic is separate from entry and risk.
- SMT is context/confirmation, not a standalone entry.

## Inherited evidence

- V10 proved that low-noise H4 HA participation can produce a large right tail,
  but broad stop classifiers, next-HA prediction, generic regime labels, fixed
  MA bands, and binary selective funding failed economic conversion.
- FAST/STD/SLOW HA remain useful phase sensors; none is market truth. Whole-base
  STD substitution reduced color churn but increased actual Hard-SL burden.
- Wave Candle compresses completed M5 settlement inside H4 and remains a valid
  observation instrument, but static Wave geometry did not establish a trading
  gate on consumed evidence.
- V11 Stage 0-5 were principally capital diagnostics bound to the V10 R7G ledger.
  They did not constitute a new strategy skeleton.
- A genuinely ledger-independent V11 STD/SLOW-memory skeleton reduced descriptive
  stop rate but failed side/year robustness. Its progress ladder reduced full-size
  stop clusters by staging size, not by recognizing stop candidates.

## Current V12 decisions

- CRT creates candidates; HA/Wave/ML do not.
- The first baseline is mechanical and has no ML.
- All continuous geometry is recorded both in raw price and causal volatility-
  normalized units to compare liquidity eras.
- Decision and outcome records are separated.
- Python raw-M1 replay is the numeric oracle. MQL5 must reproduce the event ledger
  before Strategy Tester P/L is accepted.
- Real ticks are required for economic evidence whenever intrabar ordering can
  change SL/target outcomes. Faster tester modes are smoke tests only.
- Market-closed order failures are execution states, not strategy losses; their
  lifecycle repair remains deferred to the EA implementation phase.

## Phase-0 hypotheses

These are questions, not rules:

1. Does a completed C2 rejection/acceptance state form a cleaner candidate
   population than HA-color transitions alone?
2. Conditional on the same CRT state, do FAST/STD/SLOW disagreement and Wave
   settlement add information beyond C1/C2 price geometry?
3. Can separate competing-risk heads rank stop-before-50%, 50%-before-stop, and
   continuation-after-50% without deleting the persistent right tail?
4. Does the answer remain stable across W1->H4 versus D1->H1, LONG versus SHORT,
   year, and normalized liquidity era?

## Evidence boundary

- All GOLD# observations through `2026-09-18 23:57` are consumed.
- GOLD# 2021 remains sealed.
- No V12 backtest, scorecard, EA, or independent validation exists yet.
- Phase 0 is complete only when the event definition can be independently
  reproduced and ambiguity rates are reported.
