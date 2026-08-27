# V5-032A — First Cross Volatility-Adequacy Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-030A exact First Cross 240m half-off + EMA/slow runner
Strategy authority: NONE

## Source basis
Raschke's technical manual warns against oscillator use when the trading range is too narrow / volatility too low.
This study tests one outcome-blind causal interpretation only.

## Frozen population
Exact V5-030A 240m First Cross setup, trigger, structural stop, +1R half-off, runner-to-BE, EMA20/3-10-slow runner exit.
No entry/exit rule changes.

## Volatility adequacy
On the completed 240m setup/confirmation bar:
- compute True Range and Wilder ATR14 from completed 240m bars;
- compute median of ATR14 values over the 20 completed 240m bars immediately PRECEDING the setup bar (current ATR excluded from reference median);
- `VOL_ADEQUATE = ATR14_current > median(previous 20 ATR14)`.

No magnitude or percentile tuning.

## Primary gate
Compare frozen V5-030A population vs VOL_ADEQUATE subset.
A useful context condition must:
1. retain >= 240 resolved development trades overall;
2. pooled WR >=50%, avg positive net >1R, EV >0;
3. EV >0 in all 3 pooled years;
4. EV >0 in >=3/4 markets;
5. not worsen both WR and EV versus parent in a majority of market-years;
6. GOLD# 2022 consumed diagnostic is supportive or neutral (EV >= -0.05R), not authority.

Failure closes this exact condition. No ATR threshold rescue.
