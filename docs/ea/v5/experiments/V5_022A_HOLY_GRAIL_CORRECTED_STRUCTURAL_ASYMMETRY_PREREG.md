# V5-022A — Holy Grail Source-Corrected Structural Asymmetry Pre-registration

Status: `PRE-REGISTERED BEFORE V5-022A SUBSET OUTCOME ANALYSIS`
Date: `2026-08-27`
Parents: `V5-011A structural asymmetry rule`, `V5-020A previous-bar trigger source correction`
Strategy authority: `NONE`

## Rationale

V5-011A pre-registered exactly one economic eligibility condition on the old trigger population:

`target_R > 1.0`

The threshold was derived from the project's required >=50% win rate and requirement that winners meaningfully exceed
1R; it was not selected from discovery performance.

V5-020A corrected the Holy Grail source entry to the previous signal bar high/low. This materially changes both fill
selection and target_R, so the already-frozen economic condition must be re-evaluated on the corrected source
population rather than inferred from the old-trigger result.

## Base setup

Exactly V5-020A source-corrected first attempts:
- unchanged arm/touch population;
- previous-bar trigger;
- dynamic structural stop;
- frozen prior-swing target;
- frozen fresh-arm expiry.

## Eligibility

At actual fill, using only already-known trigger, frozen target, and causal structural stop:

`target_R > 1.0` exactly.

No second R threshold, no market/session/timeframe filter, and no post-fill information.

## Exit A — published structural objective

- stop first: -1R;
- target first: +target_R;
- one recorded-spread Level-A cost once.

## Exit B — already-frozen +1R conversion diagnostic

Without changing eligibility, also report V5-019A lifecycle unchanged:
- 50% at +1R;
- remaining 50% to breakeven from next M1;
- completed signal-timeframe EMA20 ratchet.

Neither exit may be routed based on outcome.

## Promotion gate

At one timeframe and for one frozen exit architecture:
- net-positive WR >=50% pooled and in >=18/24 adequate groups;
- average gross winner >1R pooled and median group;
- pooled and median-group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no one market/year necessary;
- neighboring timeframe no material expectancy sign reversal.

If the subset fails, do not inspect target_R 1.2/1.5/2.0 or any other rescue threshold.
