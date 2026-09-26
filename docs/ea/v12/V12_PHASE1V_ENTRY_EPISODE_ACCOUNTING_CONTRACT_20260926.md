# V12 Phase 1V — entry-episode and journey-count accounting contract

Status: **frozen before Phase-1V outcome evaluation / consumed-development only**

## Question

Phase 1U mixed journey-start admission, later participation, and late-run losses
inside one Child population. Phase 1V asks the narrower question:

> If FAST/STD/SLOW ownership is evaluated only at the first actual entry of a
> funded FAST run, can it prevent repeated bad starts while preserving distinct
> profitable and tail-producing run episodes?

This is an entry diagnostic. It does not change how an admitted journey is
managed after entry and does not treat later Child losses as entry failures.

## Unit boundary

The primary unit is one funded FAST-run entry episode at its first actual-entry
Child. Existing `run_id` is a causal V10 FAST-run identifier, not proof of the
market's complete larger Journey. Phase 1V therefore uses `entry episode` in
formal fields and reports `journey-count proxy` only as an economic accounting
view.

For every episode record:

- first Child outcome and Hard-SL status;
- all later-Child outcomes separately;
- total episode net R and stopped units;
- one binary positive-episode count, regardless of Child count or weight;
- one tail-journey count when the episode contains any existing >=5R tail unit;
- prior episode's first-Child stop, known only after that episode has resolved.

## Fixed sources and common window

- Phase-1I funded-run episode ledger;
- Phase-1K baseline Child ledger for first/later Child decomposition;
- Phase-1U causal multi-speed state ledger;
- common decision window ending `2026-08-28 12:00`, where all three sources
  overlap exactly.

No raw outcome, Child, or state is relabeled. No future state may enter the
first-entry decision row. GOLD# 2021 remains sealed.

## Frozen primary policy

`ENTRY_OWNERSHIP_AUTHORIZED` evaluates only the first actual-entry Child. It
admits the complete existing episode when that first Child is either:

- `FAST_WITH_MEMORY`; or
- `TRANSFER_CONFIRMED`.

If admitted, every original later Child, weight, Hard SL, exit, and outcome is
preserved. If rejected, the whole episode is absent. This isolates admission
quality from post-entry journey management. No other state combination or
threshold is selected from outcomes.

## Count-first metrics

Primary metrics are episode counts, not weighted tail R:

- admitted entry episodes;
- first-Child Hard-SL episodes;
- consecutive first-Child Hard-SL episodes;
- alternating-direction repeated first-Child stops;
- positive and negative episode counts from total episode net R;
- tail-journey episode count, counted once per episode;
- positive/negative count curve where each episode contributes `+1`, `-1`, or
  `0`, independent of Child count, weight, or R magnitude;
- non-tail positive/negative count curve and non-tail net R per episode;
- year and side stability.

Secondary diagnostics report first-Child versus later-Child stopped units and
R, actual weighted R, and inter-tail block drift. They cannot rescue a failed
count gate.

## Frozen success gates

The primary must satisfy all of:

- at least `20%` fewer first-Child Hard-SL episodes;
- at least `30%` fewer repeated first-Child Hard-SL episodes;
- at least `90%` retention of positive episodes;
- at least `90%` retention of tail-journey episodes;
- at least `1.5` avoided first-Child stops per lost positive episode;
- higher episode win rate and no worse maximum first-stop streak;
- positive pooled non-tail count-curve slope after admission;
- no side with a higher first-Child stop rate;
- at most one represented year with a higher first-Child stop rate.

Passing consumed-history gates would still grant no entry, veto, sizing, trade,
EA, or production authority.

## Explicit non-questions

Phase 1V does not optimize add-on funding, change exits, ignore NHA, redefine a
larger market Journey from hindsight, or judge performance by a few oversized
tail Children. It only corrects the population and accounting grain for the
entry question.
