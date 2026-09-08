# V9 Research State

Date: `2026-09-09`
Status: `ACTIVE / APRIL COMPLETE / MAY HARD-SL + CAMPAIGN-HEALTH RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Expected Git base: `087299c9351233fe9a9d8a8b72c4840a65b93a91`
Untouched reserve: `GOLD# 2021`

## 1. Current research objective

V9 asks whether a discretionary trader can:

```text
enter a genuinely independent Child with bounded precommitted risk
+ allow Child failure without automatically killing the Parent
+ reattempt only when new market information exists
+ hold materially when a Parent Journey develops
+ detect deterioration early enough to protect meaningful participation
```

This remains decision research, not direction-oracle research.

---

## 2. Data authority

Authoritative M1 SHA256:

```text
626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

2025 exact Bid/Ask tick is unavailable. M1 is causal/descriptive price authority, not exact execution authority where spread, slippage, gaps, or intraminute fill ordering matter.

`GOLD# 2021` remains untouched final temporal reserve.
January-April 2025 are consumed development evidence. March includes a superseded one-trade diagnostic pass and a later corrected full replay; only the corrected replay is the active March ledger. See `results/V9_MAR25_REPLAY_CORRECTION_AND_SUMMARY_20260909.md`.

---

## 3. Retained findings

Retain:

- `Role > Pattern`;
- Parent is a working belief, not a direction oracle;
- invalid Child != invalid Parent;
- winning Child != proof of Parent direction;
- later movement cannot rescue an already invalidated Child;
- high R != large market-scale capture;
- nearest memory != automatic full TP/full-position stop;
- OPEN ROUTE requires context/maturity, not price discovery alone;
- same-auction churn is real;
- capture latency is real;
- no hindsight rescue.

Critical March correction:

```text
Child local invalidation only needs to invalidate the current Child entry thesis.
It does not need to kill the entire Parent Journey.
```

This supersedes the overly strict first formulation of Scale Alignment.

---

## 4. April completed evidence

Causal April boundary:

```text
2025-04-30 23:58
```

Closed trades including March carry P006:

```text
32 closed
6 positive
26 loss
+62.28R descriptive closed sum
+104.56R gross positive
-42.28R gross loss
April-new-entry closed sum = +32.58R
longest loss streak P018-P028 = 11 / -13.43R
```

Open carry:

```text
P038 SHORT
entry 3326.04
legacy accounting ref 3331.29
month-end 3288.42
MTM ~+7.17R
MFE ~+11.27R
```

This is not an execution-valid PF/expectancy claim.

---

## 5. April diagnosis

### H1 — Convex Parent-Journey payoff exists in consumed evidence

Large outcomes were not confined to one month:

```text
P006 +29.70R
P017 +16.77R
P029 +24.17R
P031 +23.05R
P032 +10.58R
```

Status: `PROMISING / NOT VALIDATED`.

The result remains highly concentrated in a small number of large winners. Missing or mishandling them can destroy the profile.

### H2 — Same-auction relabeling creates avoidable churn

P019-P023 and other clusters show repeated Child creation inside unresolved two-way business.

Status: `ACTIVE / SUPPORTED BY COUNTEREXAMPLES / NOT FORMALIZED`.

### H3 — New information, not retry count, may separate failed attempts from eventual launch

P024/P026/P028 failed before P029 large LONG. P029 differed by hours of new business, hold, departure, and reuse rather than by being the Nth attempt.

Status: `ACTIVE / PROMISING / NEEDS FUTURE-HIDDEN MATCHED PAIRS`.

### H4 — Campaign-health recognition is the largest open winner-management problem

Critical giveback examples:

```text
P009 ~+15.6R MFE -> +0.29R
P035 ~+4.1R MFE  -> -1.45R
P036 ~+11.4R MFE -> -4.39R
```

Status: `ACTIVE / HIGH PRIORITY`.

### H5 — H1 Stochastic cross location may be useful as a warning, not an exit rule

Retrospective examples include adverse SHORT golden crosses in/near oversold territory before major giveback, but strong trends also produced repeated extreme-zone crosses and continued.

Status: `SHADOW DISCOVERY ONLY / NOT VALIDATED / NO TRADE AUTHORITY`.

H4 indicator crosses appeared too slow in April discovery.

---

## 6. Hard SL decision

From May onward every new trade has a binding pre-entry Hard SL.

Purpose:

```text
review latency must not change maximum planned price risk
+
Initial R must mean actual precommitted price risk
```

Hard SL rules:

- frozen before entry;
- never widened;
- touch ends trade;
- structural/manual exit may occur earlier;
- no fixed point/ATR formula;
- no automatic BE/trailing/partial rule;
- Child stop does not imply Parent death.

This is an **active execution contract**, not shadow instrumentation.

P038 is grandfathered; its April history is not rewritten. The May boundary prospectively arms 3331.29 as a protective stop.

---

## 7. Active shadow instrumentation for May

### Auction / independence

```text
AUCTION: NEW / SAME / AMBIGUOUS
NEW BUSINESS: CLEAR / TENTATIVE / NONE
ANCHOR AUTHORITY: REACTION / REPEATED HOLD / HOLD+DEPARTURE / HOLD+DEPARTURE+RETURN TEST
WHAT IS NEW SINCE PRIOR SAME-SIDE FAILURE?
```

### Journey

```text
INTENDED SCALE: LOCAL BRIDGE / PARENT-JOURNEY PARTICIPATION
JOURNEY MATURITY: FRESH / ESTABLISHED / LATE / DAMAGED-REPAIR
```

### Campaign health on completed H1

```text
new favorable extreme? yes/no
settlement migration direction
counterflow business strength
repair success/failure
important memory consumption
```

### Indicator shadow

```text
H1 Stochastic(14,3,3) K/D
cross direction
exact cross K/D
cross band BELOW_20 / BETWEEN_20_80 / ABOVE_80
post-cross favorable-extreme behavior
re-acceleration behavior
H1 close vs EMA9
EMA9 direction
```

No indicator field has entry/exit permission authority.

---

## 8. Mandatory contemporaneous ledger from May

Before every new entry:

- decision timestamp;
- exact M1 entry reference;
- direction;
- Parent belief and strongest counterevidence;
- current Child;
- what is genuinely new vs prior same-side failure;
- Hard SL price;
- initial risk points;
- intended journey scale;
- destination/OPEN ROUTE;
- S;
- uncertainty.

During/after:

- first Hard SL touch if any;
- manual structural exit trigger if earlier;
- exit reference;
- MFE/MAE;
- initial-risk R;
- captured points/S;
- campaign-health observations;
- indicator shadows.

---

## 9. What is explicitly NOT promoted

Do not add:

- N-loss cooldown/stop;
- retry limits;
- fixed minimum R filter;
- fixed point/ATR stop size;
- Stochastic or EMA entry/exit rules;
- fixed profit lock;
- fixed partial;
- fixed trailing multiple;
- Parent direction veto;
- passive hold-until-parent-death.

---

## 10. Current start state

May replay begins after `2025-04-30 23:58` with P038 SHORT open. Read the active May contract before advancing.

Formalization gate remains closed.
