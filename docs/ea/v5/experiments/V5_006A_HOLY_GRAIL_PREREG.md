# V5-006A — Raschke Holy Grail Mechanism Reproduction Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Strategy authority: NONE

## Why this study

Previous V5 abstractions repeatedly failed to produce stable direction edge.
Success-first research therefore moves from inventing another abstraction to testing a published, long-lived trader
setup as a complete mechanism:

strong trend evidence -> first pullback -> objective trigger -> structural stop -> retest of prior extreme.

Primary source:
Linda Bradford Raschke / Street Smarts and her 2004 Active Trader interview.

Published core:
- ADX(14) > 30 and rising;
- first retracement to EMA(20);
- enter in trend direction above/below the previous bar;
- protective stop at newly formed pullback swing;
- objective = retest of most recent swing high/low.

## Timeframes

Report all:
15m / 30m / 60m / 120m.

No best-timeframe selection inside discovery.

## Operational trend direction

Because published prose assumes the existing trend direction visually, V5 must make it causal mechanically.

An arm bar requires:
- ADX(14) > 30;
- ADX current > ADX previous;
- LONG: +DI > -DI, close > EMA20, EMA20 rising;
- SHORT: -DI > +DI, close < EMA20, EMA20 falling.

This is explicitly a project operationalization, not a claim that Raschke published these extra direction clauses.

Once armed, update the pre-pullback trend extreme until the first EMA20 touch.

## First pullback

LONG touch: bar low <= EMA20.
SHORT touch: bar high >= EMA20.

Only the first touch after arming is eligible.

At that completed touch bar:
- fixed trigger = touch-bar high for LONG / touch-bar low for SHORT;
- target = highest high / lowest low observed from arm through the touch;
- initial structural stop anchor = pullback low/high known through the touch.

The order remains active causally until:
- trigger fills; or
- end of data.

Before fill, the swing stop anchor may extend with completed M1 price data.
No R:R filter is allowed.

## Entry and execution audit

Use underlying M1 data after the completed setup bar.
At fill:
- LONG enters when price trades through trigger; Level-A price includes recorded entry spread.
- SHORT enters at trigger; Level-A exit/stop checks include spread conservatively where required.
- structural stop uses only lows/highs from completed M1 bars before the fill minute;
- same-minute ambiguous stop/target sequencing is pessimistic (loss first).

## Exit

Primary frozen objective:
- target = most recent pre-pullback swing high/low;
- stop = newly formed pullback swing low/high.

No trailing-stop optimization in V5-006A.
No re-entry rule in V5-006A; that published extension may only be tested later if the first-entry mechanism is supported.

Right-censored trades are not wins/losses.

## Metrics

Every symbol/year/direction/timeframe:
- setup count;
- fill count;
- target-first / stop-first / censored;
- realized win rate;
- target R distribution;
- realized R expectancy;
- cost-adjusted R expectancy using recorded spread;
- trade duration;
- loss streak and concentration where sample permits.

## Promotion gate

A mechanism candidate survives only if at least one timeframe, without hidden market selection:
- realized WR >= 50% in at least 18/24 symbol-year-direction groups with adequate N;
- median target payoff > 1.0R;
- pooled and median-group cost-adjusted expectancy > 0;
- no one market/year carries the result;
- the same timeframe does not materially reverse at neighboring 15/30/60/120 scales.

If the published threshold/form fails, close it. Do not tune ADX 30, EMA20, or timeframe length.

No external validation vault opens from discovery alone.
