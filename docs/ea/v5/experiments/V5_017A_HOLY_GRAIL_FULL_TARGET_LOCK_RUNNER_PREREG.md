# V5-017A — Holy Grail Full Target-Locked Runner Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-016A.
Strategy authority: NONE.

Rationale:
The published Holy Grail objective is a retest of the prior swing, but the text explicitly distinguishes two outcomes:
a failed retest (small profit) versus a new continuation leg. V5-016A diluted continuation by exiting 50% at the prior
swing. This phase tests the other literal branch: once the prior swing has been reached, keep the position while making
the prior swing itself the profit-protecting floor.

Frozen management:
- V5-006B setup/entry/initial stop/target unchanged.
- stop-first before target = -1R.
- target-first: do not realize a partial.
- starting with the NEXT M1 bar after target hit, move the full-position stop to the target price.
- thereafter ratchet stop with completed signal-timeframe EMA20 exactly as V5-016A.
- no fixed profit target.
- same gap/through-market conservative execution as V5-016A.
- one-spread cost once.

This is not allowed to reduce a normal non-gap target winner below the original target_R; it tests only whether
continuation adds enough payoff to the already-supported target-first mechanism.

Promotion gate at one timeframe:
- final net-positive rate >=50% pooled and in >=18/24 adequate groups;
- average gross winner >1R pooled and median group;
- pooled net EV >0;
- median group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no single market/year necessary;
- neighboring timeframe no material sign reversal.
No EMA/timeframe/target tuning.
