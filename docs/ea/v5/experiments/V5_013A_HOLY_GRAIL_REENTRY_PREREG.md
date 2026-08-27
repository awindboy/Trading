# V5-013A — Holy Grail Published Re-entry Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-006B / V5-012A.
Strategy authority: NONE.

Primary source: Street Smarts Holy Grail rule 5:
"If stopped out, re-enter this trade by placing a new buy stop at the original entry price" (sells mirrored).

Population:
Only V5-006B first attempts that were actually filled and stopped before the frozen prior-swing target.

Re-entry:
- activate original trigger again beginning with the first M1 bar AFTER the first stop bar;
- keep it active only until the same V5-006B fresh-ADX-arm expiry that bounded the original setup cycle;
- no same-M1 stop/re-entry assumption because intrabar order is unavailable;
- if trigger is not crossed before expiry, no re-entry trade.

New structural stop:
- LONG: lowest M1 low observed from the first stop bar through re-entry fill;
- SHORT: highest M1 high over the same causal interval.
This is the newly formed pullback swing at re-entry.
No stop-width filter.

Target:
unchanged frozen prior-swing target from the original Holy Grail setup.

Execution:
- M1 target/stop same-bar ambiguity pessimistic;
- one-spread Level-A cost in R at re-entry;
- no runner in V5-013A.

Primary questions:
1. Does the re-entry trade itself have >=50% target-first WR with average target winner >1R and positive cost-adjusted EV?
2. Does adding the published re-entry improve cycle expectancy relative to the first attempt alone?
3. Does the result hold across symbol/year/direction/timeframe rather than one market?

Promotion gate at one timeframe:
- >=18/24 adequate market-year-direction groups;
- re-entry WR >=50% pooled and in >=18/24 adequate groups;
- average re-entry winner >1R pooled and median group;
- pooled and median-group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- combined first-attempt + re-entry cycle net EV > first-attempt-only in >=18/24 groups.
Failure closes the published re-entry as an economic rescue. No threshold tuning.
