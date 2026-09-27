# V13 HA-7 first action experiment — one add-on Child admission veto

Date: `2026-09-27`
Status: `FROZEN BEFORE ECONOMIC MEASUREMENT / DEVELOPMENT ONLY`
Parent observation: `V13_HA6E_TICK_VOLUME_PARTICIPATION_RECEIPT_20260927.md`
Base GitHub main HEAD: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## Mechanism

HA-4 established that `persistent_opposition` is a later H1 transition state than repaired/no-opposition paths. HA-6E shows that above-normal tick participation strengthens that transition interpretation, but false warnings remain common in long Journeys. Therefore an early Journey exit is too destructive.

The least invasive action is to stop adding one new unit when the current continuation bar is already showing persistent lower-timeframe opposition with above-normal participation. Existing exposure remains untouched.

## Frozen causal trigger

At the first executable tick after a completed H4 bar:

```text
Journey already exists and current journey_bar is 2..10
AND h1_path_state == persistent_opposition
AND relative_tick_volume20 > 1.0
```

where:

`relative_tick_volume20 = completed H4 tick_volume / median(previous 20 completed H4 bars with the same H4 start hour)`.

`1.0` is not optimized from P/L. It is the semantic boundary “above its own causal trailing same-slot median.” No alternative threshold is searched in this experiment.

## One action change

Baseline scheduled add-on Child for that H4 decision is **not opened**.

Everything else stays unchanged:

- Child #1 at Journey birth is never vetoed by this experiment;
- existing Children remain open;
- no Journey exit is added;
- opposite completed H4 HA still closes all existing Children;
- no SL, TP, trailing, partial close, sizing, cooldown or retry rule is added;
- no skipped child is backfilled later;
- later original H4 child slots remain eligible through original Journey bars 2..10;
- original ten-H4-slot admission horizon is preserved so the experiment measures only removal of identified add-on entries.

## Comparator

First run deterministic structural economics on the canonical full window using the same next-H4-open idealized prices as the frozen Baseline-0 sanity ledger. Baseline parity must reproduce:

```text
closed Journeys = 965
closed Children = 3,858
gross net points = +8,147.11
Journey PF ~= 1.2597
Child PF ~= 1.2000
```

If parity fails, stop.

## Predeclared measurements

- admitted/skipped Child count;
- skipped winners vs losers and their gross point contribution;
- variant net points, gross profit/loss and Child PF;
- Journey-level PF and realized-point drawdown diagnostic;
- 2024/2025/2026 x LONG/SHORT contribution;
- Journey-length and original child-slot distribution of skipped entries;
- effect inside >=10-bar Journeys;
- whether gains depend on one year, side, or a handful of Journeys.

## Promotion boundary

This is consumed 2024-2026 development history and idealized structural economics. Even a positive result does not alter the V13 EA or Baseline 0. A promising result must next receive:

1. exact implementation contract;
2. MT5 actual-tick comparison on the frozen window;
3. untouched future validation before strong authority.

No threshold sweep or alternative action is allowed in this experiment.
