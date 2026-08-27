# V5-007A — Raschke/Connors Turtle Soup Core Geometry Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Strategy authority: NONE

Primary published source: Street Smarts Turtle Soup rules.

## Daily setup

Use broker-calendar trading sessions reconstructed from M1.

For LONG:
1. Current day trades below the previous completed 20-trading-session low.
2. The most recent occurrence of that previous 20-session low is at least 4 completed trading sessions old.
3. After the break, place a same-day-only buy stop at previous 20-session low + N ticks.
4. If filled, stop = one tick below the current day's low observed up to fill.

SHORT mirrors the rules at the previous 20-session high.

Published entry offset is 5-10 ticks. Report both frozen endpoints:
N=5 and N=10.
Neither may be selected after outcome inspection.

Tick = broker point recorded for the symbol.

## Causality

- previous-day statistics use completed broker days only;
- current-day high/low evolves M1 by M1;
- entry becomes possible only after the old 20-day boundary has first been breached;
- order expires at broker-day end if not filled;
- stop uses only the current-day extreme observed through the completed M1 immediately before/at fill;
- same-minute entry/stop ambiguity is pessimistic.

## Mechanism diagnostic

Original exit language is discretionary trailing.
Before inventing an exit, measure the structural opportunity in R units.

For every fill record whether price reaches, before the initial stop:
+1R
+2R
+3R

and maximum favorable excursion in R before stop/censoring.

The position may continue beyond the entry day; only the ENTRY order is day-only.

Also record one-spread Level-A cost in R.

## Success criterion for mechanism

Strong support requires BOTH 5-tick and 10-tick variants to show:
- P(+1R before -1R) > 50% in at least 18/24 market-year-direction groups with adequate N;
- P(+2R before -1R) > 50% in at least 16/24 adequate groups OR median MFE before stop >2R with stable market-year signs;
- median one-spread cost small enough that +1R/+2R geometry is not consumed;
- no one market/year dominates.

If supported, then and only then freeze a trailing/partial exit based on published Turtle Soup management.
No age-rule, 20-day length, or tick-offset tuning.
