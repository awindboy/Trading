# V9 Next Research Contract — Oracle Ledger Replication for Terminal HA

Date: `2026-09-15`
Status: `ACTIVE SHADOW STRATEGY-RESEARCH CONTRACT`
Production authority: `NONE`
Strategy authority change: `NONE`
Market: `GOLD# ONLY`

## 1. Objective

The terminal-stage program now has an explicit answer sheet:

```text
TRUE LAST ACCEPTED CHILD
-> first opposite completed H4 HA1
-> close every still-open Child in that route
```

The next research objective is:

> Reproduce as much of this oracle ledger as possible using only causally known information, while avoiding early exits that destroy normal multi-Child right-tail journeys.

The project is not trying to predict the literal market top or to identify the future last Child with certainty.
The required decision is whether an observed opposite HA deserves route-level termination authority.

## 2. Frozen BASE

Do not change during this contract:

- H1/H4 causal 2-left / 2-right liquidity;
- tick-native H4 Arrival chronology;
- PRIMARY_ACTIVE / CHALLENGED Grammar;
- nearest active opposite H1 structural Hard SL;
- previous-completed H4 Wilder ATR180;
- `ERA_RISK <= 4` entry eligibility;
- ANCHOR / CONTINUATION role definition;
- BASE Anchor `CHALLENGE_OPENS` exit;
- BASE Continuation next-H4-liquidity exit;
- no fixed TP, SHORT ban, Child-count cap, session/day/hour filter, or duration timeout.

BASE is the `0% recovery` comparator, not the research answer sheet.

## 3. Oracle reference

For labels and evaluation only:

```text
ORACLE_ARMED_AT = true final accepted Child entry of the route
ORACLE_EXIT = first completed opposite H4 HA1 after ORACLE_ARMED_AT
ORACLE_ACTION = close all route Children still open at that event
```

This future information must never enter causal features or runtime state.

Full deterministic reference:

```text
BASE   +8,530.74
ORACLE +13,863.22
Oracle improvement +5,332.48
```

## 4. Primary evaluation metric

Every result must use identical evaluation dates/routes for BASE, candidate, and ORACLE.

```text
ORACLE_IMPROVEMENT_RECOVERY
= (candidate PnL - BASE PnL)
  / (ORACLE PnL - BASE PnL)
```

Also report:

- `ORACLE_PNL_GAP = ORACLE PnL - candidate PnL`;
- route and Child `ORACLE_REGRET`;
- exact/same-event exit match rate;
- EARLY / LATE / MISS decomposition;
- right-tail P90/P95/max winner preservation;
- PF and DD gap to oracle;
- direction, role, year and single/multi-route diagnostics.

BASE delta and classification AUC are secondary only.

## 5. Error taxonomy

For every route with an oracle terminal HA event:

### MATCH

Candidate exits the relevant open exposure at the oracle HA event.

### EARLY

Candidate assigns terminal exit authority before the oracle terminal HA event.
This is the highest-risk error because it can cut a normal large Journey.

### LATE

Candidate exits after oracle HA1 and therefore surrenders additional value.

### MISS

Candidate never performs the oracle-style terminal exit before BASE resolution.

Measure errors in economic regret, not only counts.

## 6. First required deliverable — Oracle Gain Attribution

Before further feature expansion, create a route-by-route answer-sheet table containing at least:

```text
ROUTE_ID
DIRECTION
ENTRY_YEAR
ROUTE_CHILD_COUNT (answer-sheet diagnostic only)
BASE_ROUTE_PNL
ORACLE_ROUTE_PNL
ORACLE_GAIN
ORACLE_HA1_TS
open Children at oracle HA1
per-Child BASE vs oracle delta
Anchor contribution
Continuation contribution
largest favorable excursion / giveback diagnostics
```

Rank routes by `ORACLE_GAIN` and by unrecovered candidate regret.

The first research question is:

> Which routes produce the missing oracle gain, and why does the current causal candidate fail to intervene correctly on them?

## 7. Causal decision opportunities

Do not restrict the detector to the instant a Child enters.
The delayed-oracle study shows that causal evidence can be accumulated for several H4 bars after the final Child.

Primary event opportunities may include:

- accepted Child event;
- completed H4 bars after the latest accepted Child;
- H4 liquidity creation/consumption/replenishment changes;
- first opposite H4 HA event;
- subsequent causal structural state updates before BASE resolution.

The candidate must never inspect future bars.

## 8. Feature families to explore

### A. Heikin-Ashi state

- opposite body strength / ATR180;
- body/range and wick asymmetry;
- change versus previous HA bars;
- primary/opposite persistence;
- H1/H4 HA agreement as context only.

Do not assume HA morphology alone is sufficient.

### B. H4 liquidity / participation

- nearest same/opposite distances / ATR180;
- distance ratio;
- Child-relative distance changes;
- active counts/ages;
- depletion, replenishment, missing-target states;
- candidate next-Child structural risk / ERA context when causally available.

### C. Price location / structure

- H4/H1 Donchian location;
- H1/H4 Kijun/cloud coordinates;
- Bollinger location/bandwidth;
- EMA/MACD/DMI/RSI only as causal coordinates, not assumed authorities;
- recent H1/H4 range, overlap and efficiency.

### D. Journey realization

- Anchor current PnL/MFE/giveback / ATR180;
- realized expansion since latest Child;
- results of already resolved Continuations;
- route-relative changes from prior accepted Child.

Do not hand-convert Child count or elapsed time into fitted terminal thresholds.

## 9. Required research order

1. **Oracle gap decomposition.** Identify the largest missed economic opportunities first.
2. **Visual/causal reconstruction.** Rebuild H4/H1 charts for top missed-gain routes using only information available at each candidate event.
3. **Mechanical hypotheses.** Test interpretable liquidity + location + HA state combinations.
4. **Route-relative state.** Prefer depletion/replenishment and change-from-own-history coordinates over global thresholds where possible.
5. **Same-variable model controls.** Logistic, shallow Tree, HGB only after mechanical baselines.
6. **Sequential ledger replay.** Every candidate must produce a full chronological ledger and oracle-regret report.
7. **Year/direction/role diagnostics.** Do not turn slices into fitted side-specific rules.
8. **Actual-tick validation only after a causal candidate materially closes the oracle gap without destructive early errors.**

## 10. Cost-sensitive research principle

A single early exit on a very large right-tail Journey can cost more than many correct small exits earn.
Therefore optimize **economic oracle regret**, not balanced classification accuracy.

A model with higher AUC but worse oracle-regret is inferior.

Do not introduce an arbitrary fixed minimum recovery threshold. The goal is continuous improvement toward the answer sheet under causal constraints.

## 11. Current starting point

Current proof-of-concept on 2024-2026:

```text
BASE      +7,428.37
CANDIDATE +7,869.42
ORACLE    +11,625.62

Oracle improvement recovery = 10.51%
Remaining oracle gap = 3,756.20
```

This is the next session's starting benchmark.

## 12. Prohibited leakage / fitting

Do not use as features or live rules:

- `TRUE LAST CHILD`;
- final route Child count;
- future accepted Child count;
- later challenge timestamp;
- future PnL, MFE, giveback, or oracle exit;
- `Nth Child` thresholds;
- fixed elapsed-time terminal rules mined from outcomes;
- direction-specific terminal thresholds;
- SHORT-only HA;
- fitted HA wick/body micro-pattern proliferation;
- cooldown/retry/trade-quota repairs.

## 13. Promotion gate

No strategy authority changes under this contract.

A future promotion proposal requires:

- a fully causal chronological policy;
- meaningful same-period oracle-gap reduction without concentrated hindsight dependence;
- robustness across years and both directions;
- preserved right-tail capture;
- actual-tick executable-price replay for HA exits;
- forward-demo evidence.

Until then, BASE prototype exits remain authority and all terminal fields remain shadow-only.
