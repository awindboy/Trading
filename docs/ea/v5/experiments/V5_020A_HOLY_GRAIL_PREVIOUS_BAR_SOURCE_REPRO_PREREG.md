# V5-020A — Holy Grail Previous-Bar Trigger Source Reproduction Pre-registration

Status: `PRE-REGISTERED BEFORE V5-020A OUTCOME ANALYSIS`
Date: `2026-08-27`
Parent: `V5-006B Holy Grail reproduction / V5-019A +1R lifecycle`
Strategy authority: `NONE`

## Source correction

Street Smarts rule 3 states that when price touches the 20-period EMA, the buy stop is placed above the HIGH of the
**previous bar** (sells reversed). The original V5-006A/B implementation used the EMA-touch bar's own high/low as the
trigger. Therefore V5-006A/B is not an exact source reproduction on this point.

Primary source wording verified before outcomes:
- ADX(14) >30 and rising;
- retracement to EMA20;
- when price touches EMA20, buy stop above previous bar high (sell below previous bar low);
- stop at newly formed pullback swing;
- objective retest of recent swing high/low;
- re-entry only if stopped, deferred from this first-entry reproduction.

## Setup population

Reuse the exact V5-006B arm/touch population, direction operationalization, target, and fresh-arm expiry.
This isolates only the source-correction to the trigger.

At completed EMA-touch signal bar `t`:
- LONG trigger = high of completed signal bar immediately preceding `t`;
- SHORT trigger = low of completed signal bar immediately preceding `t`.

No extra tick offset is added because the frozen V5 Level-A crossing convention already treats trading through that
price as stop-entry activation.

## Pending order and structural stop

Reuse V5-006B lifecycle:
- order begins only after touch bar completion;
- remains active until the frozen V5-006B fresh-arm expiry;
- before fill, newly formed pullback stop anchor may extend using completed M1 prices;
- LONG stop = lowest completed M1 low from touch completion through the minute before/at fill;
- SHORT mirrored;
- gap-through stop-entry fills conservatively at M1 open if worse than trigger;
- same-M1 entry/stop ambiguity is pessimistic.

Target remains the frozen pre-pullback swing objective from V5-006B.

## Primary source-reproduction exit

First report target-first vs structural-stop results exactly as V5-006B:
- target-first gross R = target distance / initial risk;
- stop-first = -1R;
- one recorded-spread Level-A cost in R.

## Risk-unit diagnostic

Independently of the prior-swing target, record +1R / +2R / +3R before unchanged initial -1R stop, exactly as V5-012A.

## Frozen lifecycle diagnostic

If and only if +1R occurs before -1R, also compute the already-frozen V5-019A lifecycle:
- 50% at +1R;
- remaining 50% stop to entry starting next M1;
- one-way completed signal-timeframe EMA20 ratchet.

This is not a new lifecycle search; it is used unchanged to test whether the corrected source entry changes the
win-rate/payoff trade-off.

## Required reporting

All 15/30/60/120m, every symbol/year/direction.

## Promotion gate

A timeframe becomes a `SUCCESSFUL DEVELOPMENT CANDIDATE` only if the corrected entry + frozen V5-019A lifecycle has:
- net-positive WR >=50% pooled and in >=18/24 adequate market-year-direction groups;
- average gross winner >1R pooled and median group;
- pooled net EV >0;
- median group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no single market/year necessary;
- neighboring timeframe no material expectancy sign reversal.

If it fails, do not tune trigger offset, expiry, ADX, EMA, timeframe, or partial fraction.
