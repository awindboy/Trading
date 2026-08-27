# V5-024A — Raschke/Connors 80-20 Core Geometry Pre-registration

Status: `PRE-REGISTERED BEFORE V5-024A OUTCOME ANALYSIS`
Date: `2026-08-27`
Strategy authority: `NONE`

Primary source: Raschke/Connors, Street Smarts, `80-20's`.

## Source mechanism

The setup day opens in one extreme 20% of its day range and closes in the opposite extreme 20%. On the next day,
price first extends beyond the setup-day extreme and then fails back through that extreme. The authors describe this
as a low-risk failure test and a day-trade setup.

## Broker-session adaptation

The book explicitly used day-session data and omitted night data. The current four MT5 historical sources do not carry
consistent exchange-session labels across gold, FX, and BTC. As in prior V5 broker-environment reproductions, one
broker-calendar date is therefore one session.

This is an environment adaptation, not a claim to reproduce 1995 pit-session statistics.

## Day-1 setup

Let `R = high-low` for the completed broker day.

LONG setup for Day 2:
- Day-1 open lies in the top 20% of R;
- Day-1 close lies in the bottom 20% of R.

SHORT setup is mirrored:
- open in bottom 20%; close in top 20%.

No minimum range/volume filter.

## Day-2 failure test and entry

The source states 5-15 ticks beyond the prior extreme as a guideline. Freeze and report both endpoints independently:
- `N=5 broker points`;
- `N=15 broker points`.

LONG:
1. Day 2 must trade at least `N` points below Day-1 low.
2. After that breach has occurred, place buy stop at Day-1 low.
3. If filled the same broker day, initial stop = one broker point below the lowest Day-2 low observed through the
   minute immediately before the fill.

SHORT is mirrored.

Entry order is Day-2 only. Same-M1 breach/reversal ordering is not assumed; the entry cannot occur until an M1 bar
strictly after the first bar that establishes the required breach. If that later bar crosses the prior extreme, it may
fill.

No re-entry in V5-024A.

## Day-trade opportunity diagnostic

The source does not specify a fixed profit target and says large profits are not the normal objective. Before inventing
an exit, measure from fill until the earlier of initial stop or Day-2 broker close:
- +1R reached before -1R;
- +2R reached before -1R;
- +3R reached before -1R;
- MFE/MAE in R;
- close-of-day gross R if neither stop nor fixed-R diagnostic target is treated as an exit;
- one recorded-spread Level-A cost_R.

Same-M1 stop/target ambiguity is pessimistic.

## Core support gate

A variant is strong enough for a separately frozen exit architecture only if BOTH 5-point and 15-point definitions
show, without choosing between them:
- P(+1R before -1R) >50% pooled and in >=18/24 adequate market-year-direction groups;
- P(+2R before -1R) >50% in >=16/24 adequate groups OR median MFE >2R with stable market-year signs;
- no one market/year necessary;
- cost_R does not consume the geometry.

Failure closes the 80-20 core for this broker-session environment. Do not tune 20%, breach distance, or session by
outcome.
