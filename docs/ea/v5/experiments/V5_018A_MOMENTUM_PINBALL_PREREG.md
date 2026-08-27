# V5-018A — Raschke Momentum Pinball Mechanical Lifecycle Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Strategy authority: NONE.

Primary source: Raschke/Connors, Street Smarts, Momentum Pinball.

Broker-session adaptation:
- one broker-calendar trading session = one daily bar;
- the first hour is the first 60 wall-clock minutes beginning at that session's first available M1 timestamp;
- this is a broker-environment study, not a reproduction of 1995 pit-session hours.

Indicator:
- daily one-period ROC = daily close_t - daily close_{t-1};
- 3-period Wilder RSI of that ROC.
Day-1 LONG setup: RSI<30. SHORT: RSI>70.

Day 2:
- after the first hour is fully observed, LONG buy-stop = first-hour high + one broker point;
  SHORT sell-stop = first-hour low - one point;
- initial stop = first-hour low - one point (LONG), high + one point (SHORT);
- order valid only Day 2.
- first-entry only in V5-018A; published re-entry is deferred unless core supports.

Lifecycle:
- if initial stop hits before Day-2 close: -1R.
- if still open at Day-2 close:
  - if trade is not gross-profitable, exit Day-2 close;
  - if gross-profitable, carry to Day 3 as published.
- Day 3:
  LONG objective = Day-2 high + one point; SHORT = Day-2 low - one point ("just above/below previous day");
  initial stop remains active;
  if objective is not hit, exit at Day-3 broker close.
- same-M1 stop/target ambiguity pessimistic.
- one-spread Level-A cost once at entry.

Report all four markets, 2023-2025, both directions.

Promotion gate:
- final net-positive WR >=50% pooled and in >=18/24 adequate market-year-direction groups;
- average gross winner >1R pooled and median group;
- pooled and median-group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no single market/year necessary.
No RSI, first-hour, session, or exit threshold tuning.
