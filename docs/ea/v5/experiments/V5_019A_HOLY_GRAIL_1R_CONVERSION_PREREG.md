# V5-019A — Holy Grail +1R Risk-Conversion Runner Pre-registration

Status: `PRE-REGISTERED BEFORE V5-019A OUTCOME ANALYSIS`
Date: `2026-08-27`
Parent: `V5-012A Holy Grail Risk-Unit Survival Geometry`
Strategy authority: `NONE`

## Why this study

V5-012A found that the unchanged Holy Grail entry/initial-stop population reaches +1R before -1R slightly more than
50% of the time at every 15/30/60/120m signal scale. The published prior-swing objective often lies below 1R, creating
a direct conflict between the project's >=50% realized win-rate requirement and its requirement that average winners
meaningfully exceed 1R.

Successful trend traders commonly separate loss truncation from winner continuation. Street Smarts also explicitly
permits taking part of a Holy Grail position and tightening the remainder when continuation is expected.

V5-019A therefore tests a single risk-conversion lifecycle without changing entry selection.

## Population

Exactly the V5-012A / resolved V5-006B first-entry population.

No setup, ADX, EMA, market, direction, timeframe, target_R, session, or stop-width filter is added.

## Frozen +1R event

Initial risk is the unchanged V5-012A structural risk.

If -1R initial stop is reached before +1R:
- full trade exits at -1R.

If +1R is reached first:
- exit exactly 50% at +1R;
- starting with the NEXT M1 bar, move the remaining 50% stop to the original entry price;
- then ratchet that runner stop one-way using completed signal-timeframe EMA20 values.

The 50/50 split is frozen before outcomes and matches the previously used literal interpretation of Street Smarts'
"exit part ... tighten stops on the balance" language. It is not optimized here.

## Runner ratchet

LONG:
`runner_stop = max(previous runner stop, completed signal-bar EMA20)`

SHORT:
`runner_stop = min(previous runner stop, completed signal-bar EMA20)`

The updated stop becomes active only after the signal bar has completed.

If the completed-bar EMA update crosses through the market, exit the runner at that completed bar close rather than
creating an impossible stop.

Adverse gaps through an already-active stop fill at the worse M1 open.

No fixed runner target and no maximum holding horizon. Right-censoring remains explicit.

## Costs

One recorded entry spread in R is subtracted once from the whole composite trade.
No additional spread is invented for the partial because the current Level-A project convention uses one round-trip
spread proxy; this remains a fast research approximation, not exact-tick authority.

## Composite gross R

- pre-1R stop: `-1R`
- +1R reached: `0.5*(+1R) + 0.5*runner_R`

## Promotion gate

A timeframe is a `SUCCESSFUL DEVELOPMENT CANDIDATE` only if all hold:
- net-positive trade rate >=50% pooled;
- net-positive trade rate >=50% in >=18/24 adequate market-year-direction groups;
- average realized gross winner >1.0R pooled;
- median market-year-direction average gross winner >1.0R;
- pooled net expectancy >0;
- median market-year-direction net expectancy >0;
- net expectancy >0 in >=18/24 adequate groups;
- no one market/year is necessary for the result;
- neighboring timeframe does not show material expectancy sign reversal.

If it fails, do not tune partial fraction, +1R threshold, EMA length, or timeframe.
