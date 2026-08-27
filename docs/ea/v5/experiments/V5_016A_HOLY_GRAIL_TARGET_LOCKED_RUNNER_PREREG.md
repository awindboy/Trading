# V5-016A — Holy Grail Target-Locked Runner Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-006B / V5-014A.
Strategy authority: NONE.

Source logic:
Street Smarts says the prior swing retest can either end the move or begin a new continuation leg; at the prior swing
the trader may exit part and tighten stops on the balance.

Frozen management:
- V5-006B entry, original stop and prior-swing target unchanged.
- stop-first: -1R entire trade.
- target-first: exit 50% at the prior-swing target.
- on remaining 50%, beginning with the NEXT M1 bar after target hit, ratchet the runner stop immediately to the prior
  swing target itself. This locks the published objective on the runner without assuming intrabar ordering in the
  target-hit minute.
- thereafter ratchet the runner stop with completed signal-timeframe EMA20 exactly as V5-014A:
  LONG max(previous stop, EMA20); SHORT min(previous stop, EMA20).
- if a completed-bar update would cross the market, exit at that completed close.
- adverse M1 gaps through active stop fill conservatively at the M1 open.
- no runner profit target.
- one-spread cost once.

This architecture has a gross payoff floor equal to the published target_R on every target-first trade except adverse
gaps after target. It therefore tests continuation without sacrificing the base setup's successful retest payoff.

Promotion gate at one timeframe:
- final net-positive rate >=50% pooled and in >=18/24 adequate groups;
- average gross winner >1R pooled and median group;
- pooled net EV >0;
- median group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no single market/year necessary;
- neighboring timeframe does not materially reverse.
No partial-fraction or EMA tuning.
