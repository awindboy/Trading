# D-154N — Pending-to-Fill Quote-Side Delay / Depth Audit

Status: NEXT RESEARCH CONTRACT / SHADOW-ONLY  
Date: 2026-08-23

## Why this phase

D154M proved that post-Fill executable quote-side friction directly flips many CADJPY and some BTC outcomes, but it explains none of SILVER25's failures.

Spread can also act **before Fill**.

For a pending Entry price, one quote side can cross the price before the executable Entry quote crosses it. The actual Fill therefore may occur later in the retracement, after the market has moved farther through the setup.

D154N tests this remaining execution pathway before returning to broader market-regime research.

## Unit

Actual filled `EXTERNAL_CONTINUATION` scenario.

## Frozen anchors

At accepted pending placement freeze:
- scenario id and direction;
- intended pending Entry price;
- selected FVG bounds/width;
- Root bounds/width;
- normalized SL;
- active map;
- pending accepted time/tick.

Track both BID and ASK until actual Fill.

## Primary causal observations

For LONG buy pending:
```text
first BID cross/touch of Entry price
first ASK executable cross/touch of Entry price
actual Fill
```

For SHORT sell pending:
```text
first ASK cross/touch of Entry price
first BID executable cross/touch of Entry price
actual Fill
```

Record:
- whether the opposite quote touched first;
- milliseconds/seconds from opposite-quote touch to executable-quote touch / Fill;
- quote displacement during that interval;
- maximum adverse excursion of the executable quote before Fill;
- spread at pending placement, first opposite-quote touch, and Fill;
- delay/depth normalized by FVG width and initial risk once Fill freezes risk.

## Primary question

Does the low-survival market group enter materially later/deeper after the setup has already reached the intended structural price on the opposite quote?

This is a market/execution-mechanism audit, not an Entry filter.

## Required reporting

Compare:
```text
GOLD25
BTC25
SILVER25
CADJPY25
```

Keep LONG/SHORT separate because entry quote asymmetry may matter.

Use GOLD23/GOLD24 only as temporal context after the 2025 cross-market contrast is understood.

## Prohibited inference

No:
- pending-price offset;
- spread threshold;
- symbol exclusion;
- SL widening;
- FVG widening;
- market-order substitution;
- direction-specific strategy rule.

If pre-Fill delay/depth also fails to explain SILVER/CADJPY residual weakness, stop expanding execution-cost explanations and return to underlying regime/path-quality research.
