# V5-021A — Holy Grail Source-Corrected Published Re-entry Pre-registration

Status: `PRE-REGISTERED BEFORE V5-021A OUTCOME ANALYSIS`
Date: `2026-08-27`
Parent: `V5-020A previous-bar trigger source reproduction`
Strategy authority: `NONE`

## Why

Street Smarts explicitly instructs that if a Holy Grail first attempt is stopped out, the trader should place a new
stop-entry at the original entry price. V5-013A tested this on the earlier touch-bar-trigger implementation. V5-020A
corrected the source trigger to the previous signal bar high/low, materially changing the first-attempt population and
therefore requires a fresh source-correct re-entry test rather than borrowing the old negative result.

## Base first attempt

Exactly V5-020A:
- same arm/touch population;
- previous-bar trigger;
- dynamic newly formed pullback stop through first fill;
- same frozen fresh-arm expiry.

## Re-entry eligibility

Only first attempts actually stopped before +1R are eligible.

Re-entry order:
- original V5-020A trigger price;
- active beginning with the first M1 bar AFTER the first stop bar;
- expires at the unchanged V5-006B/V5-020A fresh-arm expiry;
- no same-minute stop/re-entry assumption.

## Re-entry structural stop

LONG: lowest completed M1 low from the first stop bar through the minute before re-entry fill.
SHORT: highest completed M1 high over the same interval.

No stop-width filter.

## Re-entry lifecycle

Use the already-frozen V5-019A +1R risk-conversion lifecycle unchanged:
- if -1R before +1R: full -1R;
- if +1R first: 50% at +1R;
- remaining 50% stop to entry from next M1;
- then one-way completed signal-timeframe EMA20 ratchet;
- one recorded-spread Level-A cost once per executed attempt.

The first attempt is also evaluated with the same V5-019A lifecycle.

## Accounting

Report both, without choosing after outcomes:
1. `ATTEMPT LEVEL`: first attempts and executed re-entry attempts are individual trades.
2. `SETUP CYCLE`: sum the net R of first attempt plus any executed re-entry from the same setup.

The project's realized-win-rate gate applies primarily to attempt-level executed trades.

## Promotion gate

At one timeframe:
- attempt-level net-positive WR >=50% pooled and in >=18/24 adequate market-year-direction groups;
- average attempt-level gross winner >1R pooled and median group;
- pooled and median-group attempt-level net EV >0;
- attempt-level net EV >0 in >=18/24 adequate groups;
- setup-cycle net EV >0 pooled and median group;
- re-entry increases setup-cycle EV versus V5-020A first-attempt-only in >=18/24 adequate groups;
- no single market/year necessary;
- neighboring timeframe no material sign reversal.

Failure closes source-corrected re-entry. No trigger/expiry/partial/EMA tuning.
