# V5-030A First Cross — 1R Half + EMA20 Runner
Status: FROZEN BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent setup: V5-028A exact 240m First Cross.

Source basis: Raschke explicitly recommends taking half off and “pushing” the other half, protecting profitable trades, and using 20EMA/3-10 oscillator as trend-state tools. V5-029A showed that terminating the runner at the first structural retest converts too many trades into small winners.

Frozen management:
- initial structural stop unchanged;
- at first +1R, exit 50% and move runner stop to entry;
- do NOT exit runner at prior impulse high;
- runner exits at first completed 240m close across EMA20 against position, or slow 3/10 trend line crosses zero against position, whichever occurs first; execute next available M1 open;
- hard BE runner stop remains active intrabar after partial;
- before +1R, original stop remains;
- no target-room filter, no timeframe/filter change;
- conservative M1 ambiguity exclusion;
- full round-trip spread proxy once on original unit.

Final metrics unchanged: WR>=50%, avg positive net R >1R, positive cost-adjusted EV, broad market/year stability.
