# D-151 V2 Causal Research Platform

Date: 2026-08-22  
Status: **IMPLEMENTED PACKAGE / LOCAL COMPILE + NON-INTERFERENCE + MULTI-MARKET DATA PENDING**  
Target build: `2.01R0L1 / V2_CAUSAL_RESEARCH_PLATFORM_V1`  
Authority: `docs/ea/v2/AGENTS_V2.md`  
V1: **FROZEN HISTORICAL CONTROL**  
2021: **KEEP UNTOUCHED**

## 1. Why D-151 exists

V2 has removed reversal trading authority. GOLD and BTC now expose the same three continuation problems without reversal contamination:

```text
A. Fill -> +1R survival
B. +1R -> +2R+ runner discrimination
C. +2R+ profit preservation without killing the rare large-winner tail
```

D-151 does not add a new Entry filter or profit-lock rule. It upgrades the V2 research platform so the next strategy change can be justified causally rather than fitted from one equity curve.

## 2. New stretch objective

The project now pursues either of two increasingly difficult frontiers:

```text
TARGET A
cost-adjusted realized win rate >= 70%
while average winner remains > 1R and expectancy remains positive

TARGET B — extreme frontier
100% of accepted trades finish with final aggregate net R >= +1.0R
```

Target B mathematically implies no losing accepted trades and a minimum +1R net outcome on every accepted trade. It is an aspirational research frontier, not something the code can guarantee without future information.

The project must never claim either target by:

```text
counting partial deals as separate winners
removing losing trades after their outcomes are known
converting right-censored trades into wins
changing the R denominator after Fill
using future structure to reject an earlier trade
optimizing one market-year and calling it universal
```

## 3. Evidence entering D-151

### GOLD 2025 V2 SP+EM

Clean second run from the user-provided V2 ledger:

```text
42 closed continuation trades
22 winners
WR 52.38%
avg winner +1.515R
avg loser -1.039R
expectancy +0.299R/trade
total +12.550R
max closed-trade DD 6.05R
longest nonpositive streak 3
```

Runner split at first +1R:

```text
STRONG  -> +2R: 6/8 = 75.0%
DEFAULT -> +2R: 3/16 = 18.75%
```

The strongest unresolved leakage is inside STRONG:

```text
+1R but no +2R -> roughly -0.5R aggregate outcomes can remain
+2R reached -> cost-BE can still surrender most open profit
```

One GOLD stop gap realized about `-2.47R`, proving that portfolio/execution tail risk must remain separate from nominal 1R strategy geometry.

### BTCUSD 2025 inherited SP+EM diagnostic

Continuation closed cohort:

```text
63 closed
25 winners
WR 39.68%
avg winner +1.137R
avg loser -1.018R
expectancy -0.163R/trade
total -10.262R
```

BTC confirms that good post-+1R management cannot rescue a market where too many fills fail before +1R. It also confirms the +2R giveback problem. EM V2 remains non-promoted because its GOLD benefit did not cleanly generalize to BTC.

## 4. D-151 instrumentation contract

New input:

```text
InpV2D151CausalAudit = true/false
```

It is shadow-only. It may read price, map, Root and scenario state and write low-volume `D151_*` rows. It may not submit, cancel or modify an order or change Entry/SL/TP/position size/EM state.

### A. Fill snapshot

For every actual `EXTERNAL_CONTINUATION` fill record causally-known facts including:

```text
H1/M30 trend and owner
active map owner
Root identity/timeframe/alive state
frozen-owner alive state
PLAN -> Root contact time
Root contact -> Sweep time
Sweep -> CHoCH time
FVG -> Fill time
FVG width / original risk
Root width / original risk
structural TP R
```

These are research covariates only. No threshold is authorized.

### B. Fill -> +1R survival

Track exact executable-side price R until first +1R or original SL.

At +1R record:

```text
pre-1R MFE / MAE
current M30 protected/external geometry
M30 range progress
remaining room in original R
shadow STRONG/DEFAULT state under the existing structural boundary
```

At original-SL-first record:

```text
map support still same direction?
original Root still alive?
frozen map owner still alive?
pre-SL MFE / MAE
```

Then continue a lightweight counterfactual shadow with no arbitrary timeout until:

```text
original +1R recovers before map-support loss
or
current H1/M30 support is lost
or
tester ends -> right censor
```

This extends the D-148 causal taxonomy into V2 without giving the audit any strategy authority.

### C. Post-+2R price-path research

When a real position first reaches +2R, arm a price-path shadow that survives even if the actual SP position later exits at cost-BE.

Track:

```text
minimum R since +2R
peak R since +2R
minimum R before first +3R
minimum R before first +4R
minimum R before first +5R
```

Shadow terminal is the first of:

```text
original frozen structural TP
original normalized SL
right censor
```

This lets the analyzer answer the actual profit-floor question:

> How high could a +2R protective floor have been without stopping trades that later reached +3R/+4R/+5R/structural TP?

The measurement does not itself select a floor.

## 5. Ledger hygiene upgrade

D-150 exposed that two Strategy Tester runs could append into the same CSV. D-151 changes V2 logging to:

```text
one tester run = one event ledger
```

The configured V2 CSV is deleted/recreated on `OnInit` before the new header is written. Multiple `EA_START` rows therefore become an integrity failure rather than an analyzer-cleanup task.

## 6. Validation order

```text
1. Apply package.
2. MetaEditor compile = 0 errors.
3. Short GOLD control with D151 audit OFF.
4. Identical short GOLD control with D151 audit ON.
5. Require canonical non-D151 strategy-event parity.
6. Run GOLD 2025 continuation-only with SP V2 + EM OFF.
7. Run BTCUSD 2025 continuation-only with SP V2 + EM OFF and terminalize year-end cohort.
8. Expand to GOLD23/GOLD24, SILVER25, CADJPY25 before fitting any rule.
9. Only then design D-152 strategy variants.
```

## 7. What D-152 may study after D-151 data

Candidate solution families are intentionally separated:

```text
ENTRY SURVIVAL
- causal completion / reaction quality
- local-source failure and genuinely new-source re-entry
- map-premise failure avoidance
- exposure sizing/probe only after causal evidence

RUNNER DISCRIMINATION
- preserve the cross-market M30 maturity/room relation
- study structural refresh/deterioration after +1R

PROFIT PRESERVATION
- positive +2R profit floor only after post-+2R retracement evidence
- no blind resurrection of D147 step trailing
```

No D-151 measurement threshold automatically becomes a D-152 strategy rule.
