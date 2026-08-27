# V5-005A — Accepted Breakout -> First Boundary Retest Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent evidence:
- V5-002 balance descriptors did not predict breakout direction.
- V5-003 higher-timeframe trendability did not rescue immediate continuation.
- V5-004 re-entry/failure did not show stable economically meaningful reversal after the re-entry close.

Success-first hypothesis sources:
- Toby Crabel: mark-up/mark-down distinguishes initial breakout from later breakout pullback/retest continuation points.
- Linda Raschke: Holy Grail explicitly waits for momentum evidence, then enters the pullback rather than chasing the initial thrust.
- Peter Brandt: continuation/retest entries are secondary trade opportunities after a larger pattern has already completed.

These sources create a hypothesis, not authority.

## Population

For each symbol and scale W = 60m / 240m / 1440m:

1. Freeze causal rolling high/low over [t-W,t), excluding current M1 bar.
2. Use the first breakout attempt per boundary identity
   (symbol, scale, direction, boundary-establishment timestamp, boundary price).
3. Require the breakout M1 bar to COMPLETE outside the frozen boundary:
   - UP: close_t > upper boundary
   - DOWN: close_t < lower boundary
4. The breakout bar cannot itself be the retest.
5. Search the next W minutes for the FIRST later bar that trades back to the frozen boundary:
   - UP: low <= boundary
   - DOWN: high >= boundary
6. No retest-distance threshold and no EMA/ADX threshold.

At the moment the accepted breakout close is known, a passive limit at the old boundary is causal.

## Entry clock

Research entry price = frozen boundary price when first retest touches it.

No credit is given for the initial breakout or the move back to the retest.

## Outcomes

Signed continuation return in breakout direction from boundary entry to completed close after:
- 15m
- 60m
- 240m

Also record:
- retest latency;
- breakout distance at acceptance;
- retest-bar close relative to boundary;
- MFE/MAE after the retest;
- entry and horizon spread-return proxies;
- censoring.

## Required controls

1. Every market/year/direction/scale.
2. Compare with accepted-breakout market entry from breakout close.
3. Report retest incidence among accepted breakouts; no-retouch winners may not be hidden.
4. Test whether the retest advantage is just a better entry price while future direction is still random.
5. Cost screen using recorded spread before any promotion.
6. Means and medians; rare-tail gains cannot masquerade as >50% edge.
7. Block uncertainty by symbol x calendar week.
8. No best scale or threshold selection.

## Mechanism-support gate

A later strategy candidate can open only if:
- retest-entry 60m positive-return fraction > 50% in at least 18/24 symbol-year-direction groups for at least one pre-registered scale AND the same scale has no material reversal at 240m;
- median group gross return is positive;
- the effect is not dependent on one market/year;
- median gross move is comfortably larger than recorded spread proxy;
- the retest does not merely improve entry price while paired future continuation remains directionless.

If no scale satisfies the gate, close this implementation. Do not rescue with EMA/ADX thresholds.

No strategy authority.
