# V9 Development Handoff

Last updated: `2026-09-09`
Status: `ACTIVE V9 / APRIL COMPLETE / MAY HARD-SL + CAMPAIGN-HEALTH REVISION`
Current phase: `MAY 2025 FUTURE-HIDDEN REPLAY`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`
Expected Git base for this update: `087299c9351233fe9a9d8a8b72c4840a65b93a91`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Resume order

Start every new V9 session from GitHub, not conversation memory.

Read in this order:

1. latest Git HEAD;
2. root routing docs only as needed;
3. `docs/ea/v9/AGENTS_V9.md`;
4. this file;
5. `docs/ea/v9/RESEARCH_STATE_V9.md`;
6. `docs/ea/v9/DECISIONS_V9_APR25_PIPELINE_ADDENDUM_20260909.md`;
7. `docs/ea/v9/results/V9_MAR25_REPLAY_CORRECTION_AND_SUMMARY_20260909.md`;
8. `docs/ea/v9/results/V9_APR25_COMPLETION_AND_PIPELINE_POSTMORTEM_20260909.md`;
9. `docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_MAY25_20260909.md`;
10. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_MAY25_HARD_SL_CAMPAIGN_HEALTH_20260909.md`;
11. stable mindset/manual-replay docs only for retained language and historical evidence;
12. authoritative raw-data state before any new reveal.

Any older `V9_NEXT_RESEARCH_CONTRACT_*` file marked `SUPERSEDED` is historical only.
V10 is separate and not V9 authority.

---

## 2. What changed after March/April

### March correction

The first post-February pass became too restrictive by effectively requiring a local Child stop to also invalidate the Parent. That is no longer V9 authority.

Current principle:

```text
Child stop invalidates the current Child.
Parent survives or fails on its own evidence.
```

This correction restored repeated participation and produced large Parent-Journey captures. The earlier March one-trade pass is a **superseded diagnostic pass**, not the active March performance ledger. Read `results/V9_MAR25_REPLAY_CORRECTION_AND_SUMMARY_20260909.md` for the corrected March replay.

### April confirmation and new problems

April showed repeated large-winner architecture but also severe loss clusters and winner giveback.

Closed April ledger including March carry P006:

```text
32 closed
6 positive / 26 loss
+62.28R descriptive closed sum
+32.58R for April-new-entry closed trades
11-loss streak P018-P028 = -13.43R
```

This payoff shape is convex and baseball-like, but fragile if large winners are missed or given back.

---

## 3. April mandatory evidence

Major positives:

```text
P006 LONG +29.70R (carry from March)
P017 LONG +16.77R
P029 LONG +24.17R
P031 LONG +23.05R
P032 SHORT +10.58R
```

Critical negative/counterexample evidence:

```text
P009  ~+15.6R MFE -> +0.29R
P035  ~+4.1R MFE  -> -1.45R
P036  ~+11.4R MFE -> -4.39R
P019-P023 repeated same-auction attempts -> loss cluster
P024/P026/P028 failed LONGs before P029 large LONG
```

Do not hide either side.

---

## 4. Current diagnosis

Three active problems now dominate:

### A. Risk must be real before entry

April used accounting references that could be exceeded while waiting for structural confirmation. Review latency then changed realized loss materially.

From May, every new entry must have a **precommitted Hard SL**. Hard SL touch ends the trade and it is never widened.

### B. Independent Child vs same-auction reaction

Repeated attempts are allowed, but the trader must be able to causally distinguish the new Child from the prior failed attempt. The question is not `how many times have we tried?`; it is `what exists now that did not exist at the previous failure?`. This is **not** a requirement to wait N bars, demand a full hold/departure/return-test sequence, or impose a cooldown; immediate retry can be valid when genuinely new evidence appears immediately.

### C. Campaign-health recognition

The strategy can now hold very large winners. It still sometimes recognizes deterioration too late. Research must distinguish normal Parent pullback from loss of progression ability.

---

## 5. HTF indicator status

Retrospective April exploration found possible value in **H1** momentum location, not as a rule but as a review warning.

Keep shadow-only:

```text
H1 Stochastic(14,3,3) K/D
cross direction
exact cross location and 20/80 band
post-cross favorable-extreme behavior
re-acceleration or failure to re-accelerate
H1 close vs EMA9
EMA9 direction
settlement migration
```

Important counterexample: strong trends can produce multiple >80 dead crosses or <20 golden crosses and continue. Therefore no Stochastic/EMA exit rule is authorized.

H4 indicator crosses were generally too slow in consumed April discovery.

---

## 6. May causal start state

April completed at:

```text
2025-04-30 23:58
```

Position is **not flat**:

```text
P038 SHORT OPEN
Entry: 3326.04
Legacy April accounting reference: 3331.29
April month-end: 3288.42
April MTM on legacy reference: about +7.17R
April MFE: 3266.86, about +11.27R
```

P038 predates the new hard-SL rule. Do not rewrite its April history.

At the May boundary, prospectively arm `3331.29` as a **one-time protective stop for this grandfathered carry**, decided before any May reveal. This is not an initial Hard SL, is not evidence for future stop placement, and must not be used as a template for new trades. Preserve the old initial-R label as `legacy accounting R`; do not call the stop retroactively precommitted.

For every trade opened from May onward, Hard SL is mandatory **before entry**.

---

## 7. Exact operational pipeline

Use:

- `scripts/v9_causal_m1.py` to create/advance an exact revealed prefix;
- `scripts/v9_hard_stop_guard.py` to find the earliest Hard-SL touch inside the revealed prefix;
- completed uploaded higher-TF files only as optional speed aids; never read an unfinished bar containing future minutes.

While flat:

```text
H4/H1 Parent context
-> auction/value state
-> M15 Child candidate
-> exact M1 decision only when needed
```

Before entry:

```text
Parent belief
Child thesis
what is new since any prior same-side failure
Entry
Hard SL
Initial R
Intended Journey Scale
Destination/OPEN ROUTE
S
uncertainty
```

While open:

```text
Hard SL is binding
+ structural exit may occur earlier
+ H1 campaign health reviewed at every completed H1 for Parent-Journey positions
+ M15/M1 review when deterioration/stop ambiguity becomes relevant
```

---

## 8. What must not regress

Do not return to:

- requiring Child SL to equal Parent death;
- treating every local memory as full TP/full exit;
- chase after missed legs;
- interpreting one stopped Child as campaign death;
- same-auction rapid-fire re-entry without new information;
- passive hold because `Parent is still alive`;
- exact-top prediction;
- fixed indicator exits;
- fixed R/ATR trailing rules.

---

## 9. Immediate next task

Continue May 2025 future-hidden replay from the exact boundary above with P038 carried.

Primary research questions:

1. Does precommitted Hard SL keep losses bounded and R meaningful without making Child entries artificially narrow?
2. Does mandatory `WHAT IS NEW?` documentation distinguish P029-type eventual winner from P024/P026/P028-type failed attempts?
3. Can H1 campaign-health review reduce P009/P035/P036-style giveback while preserving P017/P029/P031/P032-style large winners?
4. Do H1 Stochastic cross **location** and re-acceleration add useful shadow information beyond price/settlement?
5. Does the same convex payoff shape recur in May without outcome-fitted rescue rules?

Formalization gate remains closed.
