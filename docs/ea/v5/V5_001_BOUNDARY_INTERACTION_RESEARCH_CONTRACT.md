# V5-001 — Boundary Interaction Event-Ledger Research Contract

Status: `PRE-REGISTERED DISCOVERY DESIGN`
Date: `2026-08-27`
Trading authority: `NONE`

## 1. Research question

When price interacts with a **pre-existing, causally known market boundary**, what causal context and interaction
path distinguish:

```text
acceptance / continuation
rejection / failure
unresolved / two-sided behavior
```

?

The first study does NOT attempt to predict every 15-minute return.

## 2. Why this question is first

It is the strongest convergence across the Success-First corpus:
- Brandt: pattern completion resolves prior balance/distribution;
- Raschke: context + behavior at pre-planned levels;
- Crabel: breakout success/failure as foundational behavior;
- Turtles: wait for breakout evidence;
- Osler: actual order clusters can explain both reversal near technical levels and acceleration after crossing.

## 3. Stage 1 is a ledger, not a classifier

Before defining a Boolean target, record the complete path.

For every eligible event, preserve:

### Identity
- symbol;
- decision/event timestamp;
- direction;
- reference type;
- reference price;
- reference creation timestamp;
- age of reference.

### Pre-event state
- causal volatility;
- recent directional efficiency;
- recent range compression/expansion;
- bar/wave overlap proxies;
- approach distance over time;
- number of prior tests;
- time since last interaction;
- spread;
- tick-volume activity proxy;
- time-of-day/day-of-week.

### Interaction path
- first penetration;
- penetration distance normalized by causal volatility;
- close position relative to boundary;
- time beyond boundary;
- number/fraction of closes beyond;
- first re-entry time;
- maximum extension before re-entry;
- post-reentry retest behavior;
- spread/activity changes.

### Post-event path — descriptive, not yet a trade label
At fixed causal horizons record:
- 5m / 15m / 30m / 60m / 240m signed return relative to break direction;
- MFE/MAE relative to boundary;
- realized volatility;
- directional efficiency;
- whether/when prior range is re-entered;
- censoring / missing session data.

Right-censoring remains explicit.

## 4. Boundary population

V5-001A begins with **objective, pre-existing reference families**.

Do not choose a winner after observing outcomes and call it validation.

Initial descriptive families may include:
- previous broker-day high/low;
- previous completed session/range boundaries if an unambiguous session definition already exists;
- pre-existing confirmed swing extremes only if confirmation time is causally enforced.

Every reference type must be tagged in the ledger.

If several reference families are explored, they are all discovery.
A later candidate must be frozen and validated independently.

## 5. No premature acceptance threshold

Forbidden in Stage 1:

```text
3 closes beyond = accepted
0.2 ATR = valid breakout
15 minutes outside = success
```

unless used only as clearly labeled descriptive slices.

First inspect continuous relationships:
- dwell;
- extension;
- re-entry latency;
- progress efficiency;
- context.

The discrete transition definition is a later pre-registration step.

## 6. Data roles

Allowed discovery:
- GOLD# 2023-2025
- BTCUSD# 2023-2025
- XAUEUR# 2023-2025
- USDJPY# 2023-2025

Not allowed now:
- V4 external validation vault;
- GOLD# 2021.

GOLD# 2022 remains consumed.

## 7. Required analyses before a strategy idea

At minimum:
- event counts by market/year/direction/reference type;
- continuous distributions, not only win rate;
- market/year stability;
- relationship between pre-state and interaction path;
- relationship between interaction path and later path;
- bootstrap uncertainty;
- censoring report;
- spread/activity conditioning;
- test whether one market/year carries the effect.

## 8. Falsification outcomes

The research can end with:

### A. MECHANISM SUPPORTED
Stable conditional transition structure exists.

Then freeze a semantic state definition before strategy testing.

### B. OBSERVABLE PROXY INSUFFICIENT
The hypothesis is plausible but MT5 price/tick-volume data cannot distinguish it.

Then obtain better data rather than invent more chart thresholds.

### C. MECHANISM NOT SUPPORTED
No stable relationship.

Close the hypothesis. Do not rescue by adding post-hoc pattern names.

## 9. No-trade boundary

V5-001A instrumentation must not modify:
- EA entry;
- SL;
- TP;
- sizing;
- portfolio exposure;
- scenario lifecycle.

No production or paper trading.
