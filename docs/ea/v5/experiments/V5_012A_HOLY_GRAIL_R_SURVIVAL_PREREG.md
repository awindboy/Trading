# V5-012A — Holy Grail Risk-Unit Survival Geometry Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-006B first-entry Holy Grail population.
Strategy authority: NONE.

Question:
The published prior-swing target was reached on >50% of resolved setups, but often lay below 1R. Does the underlying
trend-pullback entry itself nevertheless reach meaningful R multiples before the frozen initial structural stop?

Population:
exact V5-006B fills, all 15/30/60/120m, no R:R selection.

Clock/geometry:
- entry reference = frozen V5-006B trigger;
- initial risk = frozen V5-006B `risk`;
- initial stop = entry - direction*risk;
- ignore the published prior-swing target for this diagnostic;
- from actual fill forward, record whether +1R / +2R / +3R is touched before the unchanged -1R initial stop;
- same-M1 target/stop ambiguity pessimistic;
- right-censored explicit;
- one-spread cost_R preserved.

Support gate:
- P(+1R before -1R) >50% pooled and in >=18/24 adequate market-year-direction groups at one timeframe;
- P(+2R before -1R) >35% pooled with positive/consistent market-year evidence (not yet a strategy gate);
- no single market/year carries +1R support;
- costs are small enough that a later partial+runner architecture can preserve positive expectancy.

If +1R support fails, do not design a 1R partial runner.
If it passes, freeze a separate exit architecture before testing realized expectancy.
No threshold tuning.
