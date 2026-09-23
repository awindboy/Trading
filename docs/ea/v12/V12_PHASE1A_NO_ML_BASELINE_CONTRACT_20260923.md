# V12 Phase-1A no-ML baseline contract

Date frozen: `2026-09-23`

Status: `DEVELOPMENT CONTRACT / CONSUMED EVIDENCE ONLY / NO TRADE AUTHORITY`

Contract version: `v12-phase1a-model1-v2`

Revision note: v1 was executed once and then failed a source-compliance audit:
it guarded midpoint consumption only after C3 opened. V2 was frozen before its
outcomes were generated and begins the midpoint guard at the first relevant C1
extreme breach inside C2. This is a compliance correction, not a fitted rule.

## 1. Purpose

Phase 1A asks a narrow question before HA, Wave, or ML is added:

> Does a mechanically confirmed CRT rejection Child improve the stop population
> and risk-unit distribution relative to entering every completed C2 rejection at
> C3 open?

This contract is frozen before Phase-1A outcomes are generated. It is not claimed
to be the only valid interpretation of Romeo's Model #1.

## 2. Frozen input

- Phase-0 parent IDs and bar ledgers from the pack whose decision JSONL SHA-256
  is `4b5fe2b76d8ba6faca26b062b8caac0aa8d56bcf5e08066b8d11c7375550a33a`.
- Verified chronological GOLD# raw M1 through `2026-09-18 23:57` only.
- Official mappings remain W1->H4 and D1->H1.
- Every completed next W1/D1 bar after C2 is the finite C3 window. If it is not
  complete, no Phase-1A outcome is created.

## 3. Branch coverage

Phase 1A authorizes research Children only for:

- `HIGH_SWEEP_RETURN` -> SHORT;
- `LOW_SWEEP_RETURN` -> LONG.

`NO_EXTREME_TRADE`, both dual states, and both outside-acceptance states remain
in the parent disposition ledger with explicit non-execution codes. A
continuation destination beyond C1 is not defined well enough to trade the
outside branch without inventing a rule.

## 4. Mechanical Model #1 relaxation

The source requires a specific thick execution candle that attacks old
liquidity, followed by a completed close beyond that candle in the opposite
direction. It gives no numeric `thick` threshold.

For each completed rejection C2:

1. inspect only completed mapped execution bars inside C2;
2. bearish: eligible bars strictly exceed C1 high and close above their open;
3. bullish: eligible bars strictly fall below C1 low and close below their open;
4. rank eligible bars by absolute body / causal execution-timeframe ATR14, then
   body/range ratio, sweep depth, and latest open time;
5. select the single highest-ranked bar as the Model #1 trigger candle;
6. bearish confirmation is the first later completed execution bar closing
   strictly below trigger low; bullish is the symmetric close above trigger
   high; and
7. entry cannot occur before C2 close. A confirmation completed inside C2 waits
   for C3; a later confirmation enters after that completed bar.

This is named `MODEL1_RELATIVE_THICK_V1`. It uses no fitted threshold. Body and
sweep coordinates remain continuous audit fields. True MSS is not implemented
because a causal swing definition is not yet frozen.

## 5. Families and risk variants

The fixed research families are:

1. `C3_OPEN_CONTROL` + `C2_EXTREME`;
2. `MODEL1_RELATIVE_THICK_V1` + `C2_EXTREME`;
3. `MODEL1_RELATIVE_THICK_V1` + `TRIGGER_STRUCTURE`.

Entry is the first observed M1 open at or after the decision timestamp. One
point is placed beyond the structural stop:

- LONG C2 stop = C2 low - 0.01;
- SHORT C2 stop = C2 high + 0.01;
- LONG trigger stop = trigger low - 0.01;
- SHORT trigger stop = trigger high + 0.01.

Stops are never widened. There is one Child per Parent/family/risk combination
and no retry in Phase 1A.

## 6. Pre-entry invalidation

Chronological M1 guards C1 midpoint from the first relevant C1-extreme breach
inside C2. The C2-extreme stop is guardable after completed C2 close; the trigger
stop is guardable after the selected trigger candle closes. If a guarded stop or
midpoint is touched before entry, the Child is not filled and receives a coded
no-execution state. If parent sweep and midpoint occur in the same M1, the order
is ambiguous and no trade is backfilled. If the first executable M1 opens at or
beyond stop or midpoint, it is also not filled. These states are not losses.

No minimum-R, no-chase, body threshold, session veto, or discretionary quality
filter is allowed.

## 7. Outcomes

Two separate full-exit surfaces are recorded on fixed coverage:

- `T1_MIDPOINT`: C1 50%;
- `T2_OPPOSITE_EXTREME`: opposite C1 edge.

The primary Phase-1A strategy score is `T1_MIDPOINT`. T2 is a journey diagnostic,
not a claim that midpoint management is solved. If neither stop nor destination
is touched by C3 close, exit at the last observed M1 close before C3 close.

The first M1 containing both stop and destination is `AMBIGUOUS`; no tick order
is invented. Adverse gap through stop fills at the first observed M1 open. An
entry opening at/beyond a destination is not executed because that destination
has already been consumed.

Primary scores are spreadless structural R, matching the frozen V10 structural
R comparator. Actual-tick costs and order lifecycle remain Phase 4 work.
Drawdown in this prototype is realized R aggregated by terminal timestamp; it is
not mark-to-market portfolio drawdown and must not be substituted for V10's
retained overlapping-exposure drawdown statistic.

## 8. Reporting and V10 comparison

Report each family/risk separately across:

- lane, direction, year, and interaction;
- decisions, fills, no-executions, ambiguities, stops, targets, and expiries;
- net/gross R, PF, mean/median R, R per 100 filled units, maximum drawdown,
  maximum stop streak, and right-tail counts;
- rejection-parent coverage and time-to-confirmation.

The matched V10 comparison window is the actual frozen selected-R7G interval
present in the Stage-3 ledger, bounded by its first entry and `2026-08-28 23:57`.
Report both V10 selected Children at one unit each and historical R7G funded
units. Lower total R under fewer fills is never sufficient by itself to reject
V12; compare stopped units, PF, R per funded unit, drawdown, and right-tail loss.

## 9. Interpretation boundary

Phase 1A is a mechanical source relaxation, not a certified exact Romeo model.
The same consumed chronology may diagnose mechanisms but cannot provide
independent validation. No result from this phase may set live size or read the
post-`2026-09-18 23:57` holdout.
