# V5-009A — Turtle Soup Plus One Core Geometry Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-007A original Turtle Soup core geometry failed its support gate.
Strategy authority: NONE

Primary source: Raschke/Connors, Street Smarts, Turtle Soup Plus One.

Frozen published geometry, buys mirrored for sells:
1. Day 1 makes a new 20-completed-session low.
2. The previous 20-session low must have been established at least 3 completed trading sessions earlier.
3. Day-1 close is at or below that previous 20-session low.
4. On Day 2 only, buy stop = the earlier 20-session low. If not filled that day, cancel.
5. Initial stop = 1 broker tick below the lower of Day-1 low and Day-2 low observed causally through fill.
6. No extra trend/volatility/session filter.

Broker-calendar sessions are used because the current MT5 sources do not provide historical exchange day-session labels consistently across all four markets. This is a broker-environment reproduction, not a claim to reproduce 1995 pit sessions.

Mechanism diagnostic:
- From fill, record hit +1R / +2R / +3R before initial -1R stop.
- Record MFE before stop/censoring.
- Record one-spread Level-A cost in R.
- Same-minute stop/target ordering pessimistic.
- Right-censored outcomes explicit.

Support gate:
- P(+1R before -1R) >50% in >=18/24 adequate market-year-direction groups;
- P(+2R before -1R) >50% in >=16/24 adequate groups OR median MFE >2R with stable market-year signs;
- both conditions must not depend on a single market/year;
- spread cost must not consume the geometry.

If the core geometry fails, close it. Do not retune 20 sessions, 3-session age, entry level, or add filters.
