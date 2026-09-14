# V9 Research State

Date: `2026-09-15`
Status: `PROTOTYPE FROZEN / ACTUAL-TICK VALIDATED / TERMINAL-ORACLE REPLICATION SHADOW RESEARCH ACTIVE`
Market: `GOLD# ONLY`

## 1. Current mechanical authority

The prototype remains:

```text
Arrival / Delivery Grammar
+ H1 structural invalidation
+ H4 ATR180 long-era normalization
+ ERA_RISK <= 4
+ ANCHOR / CONTINUATION role split
+ tick-native execution
```

No terminal-stage result changes current strategy authority.

## 2. Validated execution baseline

Actual MT5 real ticks remain higher authority for execution questions.

Reference through `2026-08-28`:

```text
1,316 closed
+5,028.62
PF 1.425
WR 60.18%
```

Full uploaded closed ledger through September:

```text
1,322 closed
+4,954.61
PF 1.412
WR 60.14%
```

The terminal-stage studies below are consumed-data M1/H4 screening, not production/forward evidence.

## 3. Terminal HA answer sheet

The current research oracle is:

```text
true last accepted Child
-> first opposite completed H4 HA1
-> close all still-open route Children
```

This uses future information only to define the answer sheet.

Full deterministic research population:

```text
BASE
N 1,139 / PnL +8,530.74 / PF 2.023 / WR 65.58% / DD 440.35

ORACLE
N 1,139 / PnL +13,863.22 / PF 3.475 / WR 70.41% / DD 288.75

full-history oracle improvement = +5,332.48
```

## 4. Evaluation authority for terminal research

The primary target is no longer `beat BASE`.
It is **oracle ledger replication without future leakage**.

For the same evaluated period:

```text
ORACLE_RECOVERY
= (candidate PnL - BASE PnL)
  / (ORACLE PnL - BASE PnL)
```

Also measure exact/near-exit matching, EARLY/LATE/MISS counts, route regret, right-tail preservation, PF gap, and DD gap.

Do not compare a partial-period candidate to the full-history oracle.

## 5. Timing result

Terminal detection has usable latency.
Delaying oracle activation by completed H4 bars after the true last Child gave:

```text
0 H4: +13,863.22 / PF 3.475
1 H4: +13,839.03 / PF 3.464
2 H4: +13,715.95 / PF 3.407
3 H4: +13,471.13 / PF 3.272
4 H4: +12,608.38 / PF 2.927
```

Therefore a causal detector can gather evidence after the final Child; it does not have to identify the final Child exactly at entry time.

## 6. Broad HA + indicator + structure exploration

Explored causal information at opposite-H4-HA events included:

- HA body/range/wick morphology and persistence;
- H1/H4 HA context;
- H4 remaining same/opposite liquidity geometry and Child-relative changes;
- H1/H4 range, efficiency and volatility context;
- RSI, EMA, MACD, DMI/ADX, Bollinger, Donchian;
- H1/H4 Ichimoku location;
- Anchor MFE/giveback and route state;
- prior movement-capacity context;
- Logistic, shallow Tree and HGB controls.

### Main qualitative findings

1. **HA alone is not enough.** HA body strength has some information, but HA is best interpreted as the momentum-reversal event, not the whole terminal-state detector.
2. **H4 liquidity geometry remains central.** Same/opposite distances and their Child-relative changes repeatedly survive across tests.
3. **Location matters.** H1/H4 range-location, Donchian, Kijun/cloud and similar coordinates contain information, but simple single-indicator exits usually over-trigger.
4. **Duration is weak.** `hours since Child` is not a useful standalone terminal rule.
5. **ML complexity is not currently an advantage.** On the same small feature set, mechanical combinations gave better sequential economics and fewer early interventions than Logistic/Tree/HGB in the current slice.

## 7. Current best proof-of-concept candidate

Current research candidate at the first opposite H4 HA uses a high-precision mechanical combination of:

```text
Child-relative opposite-H4-liquidity pressure
H4 Donchian primary-direction location
opposite HA body strength / ATR180
```

The operating point is exploratory and not strategy authority.

### Same-period 2024-2026 comparison

```text
BASE      +7,428.37
CANDIDATE +7,869.42
ORACLE    +11,625.62
```

Therefore:

```text
BASE -> candidate gain  = +441.05
BASE -> oracle gain     = +4,197.25
Oracle recovery        = 10.51%
Candidate -> oracle gap = 3,756.20
```

Selected route events: `12`.
Answer-sheet early events: `0`.
Positive route delta: `9`.
Unchanged route delta: `3`.

This result is **not close to the oracle**. It only proves that a precision-first causal mechanical filter can recover a small piece of the oracle value without observed early cuts in that consumed slice.

## 8. Mechanical versus ML on the same three variables

2024-2026 exploratory economic comparison at the fixed high-precision screen:

```text
MECH   delta +441.05 / early 0
LOGIT  delta +234.60 / early 4
TREE2  delta +110.20 / early 12
TREE3  delta +182.90 / early 4
HGB    delta +140.64 / early 3
```

AUCs were broadly similar for MECH / LOGIT / HGB, so classification AUC did not explain the economic difference. False-early cost is the key issue.

## 9. Natural mechanical rule evidence

A more literal semantic rule using:

```text
HA1
+ opposite liquidity closer than at Child entry
+ weak H4 Donchian primary location
+ current HA body stronger than recent HA bodies
```

produced `+268.90` BASE delta over 2024-2026 with `17` event routes and `0` answer-sheet early routes in that slice.

This is supporting evidence for the three-part decomposition, not a frozen rule or threshold.

## 10. Current interpretation

The most useful working decomposition is:

```text
LIQUIDITY / PARTICIPATION STATE
-> is the route exhausting viable additional participation?

LOCATION / STRUCTURE
-> has price lost favorable primary-side location?

HA REVERSAL
-> has H4 momentum actually reversed now?
```

The research problem is not `find a better indicator`.
It is to determine which causal combination best reproduces the oracle terminal HA ledger with minimal early regret.

## 11. Next research target

The next session must decompose the **remaining oracle gap**.

Primary work:

- Oracle Gain Attribution by route and Child.
- MATCH / EARLY / LATE / MISS decomposition.
- Oracle-regret ranking of missed journeys.
- Causal chart reconstruction of the largest missed oracle gains.
- Identify whether misses arise from missing variables, insufficient state history, or overly conservative intervention rate.
- Explore HA + H4 liquidity + range/location/Ichimoku/structure interactions mechanically before adding ML.
- Use route-relative depletion/replenishment and state transitions rather than fitted Nth-Child or duration rules.
- Re-run all candidates as chronological route policies against the same-period oracle.

## 12. Open risks

- every supplied historical period is consumed;
- current candidate feature selection is postmortem research, not untouched validation;
- actual-tick Bid/Ask fills and H4-close execution are not yet validated for a promoted HA candidate;
- an apparently strong terminal classifier can still be economically bad if a few false-early signals cut major right-tail journeys;
- forward/demo evidence remains mandatory before any authority change.
