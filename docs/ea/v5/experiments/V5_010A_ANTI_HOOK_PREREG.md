# V5-010A — Raschke Anti Hook Core Geometry Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Strategy authority: NONE

Primary source: Raschke/Connors, Street Smarts, "The Anti".

Published mechanism:
- slow momentum trend and short-term momentum correction create opposing cycles;
- when the fast stochastic hooks back in the direction of the slow stochastic, the two cycles enter positive feedback;
- the best trades occur after at least a 2-3 bar fast-line correction;
- average holding time is about 2-4 bars;
- initial stop belongs below/above the recent retracement or entry risk point.

Frozen oscillator:
- raw stochastic %K over 7 completed signal bars;
- smooth %K with 4-period simple average;
- slow %D = 10-period simple average of smoothed %K.

Signal timeframes:
15 / 30 / 60 / 120 minutes. Report all.

Mechanical hook operationalization, LONG (SHORT mirrored):
- for the three completed bars immediately before hook bar t:
  slow %D slope is positive on every transition;
  fast %K slope is negative on every transition;
- on completed hook bar t:
  slow %D slope remains positive;
  fast %K slope turns positive.
This is the source's explicit "opposing slopes for at least three bars" plus hook, without a threshold.

Entry:
- next completed signal bar's OPEN after the hook (source's conservative next-opening entry).
- no price filter.

Initial stop:
- LONG: one broker point below the minimum low from the three correction bars plus hook bar.
- SHORT: one broker point above the maximum high from the same four bars.
- if next-bar open gaps beyond the stop, mark invalid/no trade.
This is a causal recent-retracement risk point.

Mechanism diagnostic:
- starting from next-bar open, record +1R / +2R / +3R before initial -1R stop over the next 4 completed signal bars;
- also record MFE/MAE in R and one-spread Level-A cost_R;
- same-bar stop/target ambiguity pessimistic.
- primary time horizon fixed at 4 bars because the source states the normal holding window is 2-4 bars; 2-bar results are descriptive only, not selectable.

Support gate:
- P(+1R before -1R) >50% in >=18/24 adequate market-year-direction groups at one timeframe;
- P(+2R before -1R) >50% in >=16/24 adequate groups OR median 4-bar MFE >2R with stable signs;
- average realized winner under a later frozen exit must be >1R and cost-adjusted expectancy positive before strategy promotion;
- neighboring timeframes may not materially reverse.
No stochastic threshold or timeframe rescue.
