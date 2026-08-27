# V5-014A — Holy Grail 50% Target + Ratcheting EMA20 Runner Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-006B first-entry Holy Grail.
Strategy authority: NONE.

Why:
The published Holy Grail repeatedly reached its prior-swing objective with >50% probability, but that objective often
lies below 1R. Street Smarts explicitly permits exiting part at the prior swing and tightening/trailing the balance.
V5-006C interpreted "tighten" as immediate breakeven and likely truncated the continuation leg.

This phase changes only the runner stop interpretation.

Base entry / setup / stop / target:
exact V5-006B.

Frozen position management:
- stop-first before prior target: entire position exits -1R.
- target-first: exit exactly 50% at the frozen prior-swing target.
- retain 50% as runner.
- runner initial stop remains the frozen original structural stop; it is NOT jumped to breakeven.
- after each completed signal-timeframe bar following target, update a one-way trailing stop to EMA20:
  LONG runner stop = max(previous runner stop, completed-bar EMA20);
  SHORT runner stop = min(previous runner stop, completed-bar EMA20).
- the updated stop becomes active only after that signal bar is complete.
- M1 touches of the currently active runner stop exit the runner.
- no fixed runner profit target.
- right-censoring explicit.
- same-minute target / stop ambiguity pessimistic.
- one-spread Level-A cost is subtracted once from the composite trade.

Gross resolved trade R:
- loss = -1R
- target winner = 0.5*target_R + 0.5*runner_R

Promotion gate at one timeframe:
- final positive-trade rate >=50% pooled and in >=18/24 adequate market-year-direction groups;
- average realized gross winner >1R pooled and median group;
- pooled net expectancy >0;
- median group net expectancy >0;
- net expectancy >0 in >=18/24 adequate groups;
- no single market/year necessary;
- outperform V5-006B target-only and V5-006C immediate-BE runner in pooled and median-group expectancy.
No partial-fraction, EMA-length, or timeframe threshold optimization.

Pre-execution clarification frozen before outcome analysis:
- if a completed-bar EMA update would place the new long stop at/above that completed bar close (short at/below close),
  the runner exits at that completed bar close instead of creating an impossible stop through the market.
- adverse M1 gaps through an already-active stop fill at the worse of stop/open for LONG and better-of? No: conservatively,
  LONG exit = min(active_stop, M1 open), SHORT exit = max(active_stop, M1 open).
