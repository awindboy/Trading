# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-09`
Status: `ACTIVE / MARCH+APRIL CONSUMED / MAY HARD-SL + CAMPAIGN-HEALTH REPLAY`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched final temporal reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Authority and resume order

GitHub is permanent memory. Chat history is a workbench.

Every new V9 session must:

1. refresh latest GitHub HEAD;
2. read root `AGENTS.md` and `docs/ea/HANDOFF.md` only for routing/context;
3. read this file;
4. read `docs/ea/v9/HANDOFF_V9.md`;
5. read `docs/ea/v9/RESEARCH_STATE_V9.md`;
6. read `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md` for stable mindset;
7. read `docs/ea/v9/V9_MANUAL_CHART_REPLAY_MARKET_MEMORY_AND_DECISIONS_20260907.md` for retained vocabulary/history;
8. read `docs/ea/v9/DECISIONS_V9_APR25_PIPELINE_ADDENDUM_20260909.md`;
9. read `docs/ea/v9/results/V9_APR25_COMPLETION_AND_PIPELINE_POSTMORTEM_20260909.md`;
10. read `docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_MAY25_20260909.md`;
11. read `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_MAY25_HARD_SL_CAMPAIGN_HEALTH_20260909.md` before advancing May;
12. inspect authoritative raw data and causal replay state before revealing new future data.

Documents whose name begins `V9_NEXT_RESEARCH_CONTRACT_` but are explicitly marked `SUPERSEDED` are historical pointers only and have no current trading authority.

The separate V10 experiment is not V9 authority.

---

## 2. Permanent objective

V9 does not seek a market oracle.

```text
market understanding
!=
direction prediction
!=
good trade
```

The target trader:

```text
selects worthwhile pitches
+ enters with a precommitted bounded loss
+ lets a child thesis fail without automatically killing the parent story
+ distinguishes another Child attempt from the previous failure using contemporaneous market information
+ participates materially when a larger journey develops
+ recognizes campaign deterioration without pretending to know the final top/bottom
```

A good trade may lose. A losing trade is not automatically a bad decision.

---

## 3. Stable market language

Retain:

```text
Role > Pattern
reaction != rejection
destination != reversal
boundary crossing != value translation
direction correctness != trade quality
later same-direction movement cannot rescue an invalidated child thesis
invalidated child thesis != invalidated parent journey
winning child trade != proof of parent direction
high R != large market-scale capture
```

Core hierarchy:

```text
PARENT JOURNEY        H1/H4 strategic continuity
CHILD ROUTE           M15/H1 current attempt / repair / continuation
EXECUTION STRUCTURE   M5/M15/M1 precise decision and hard risk
```

H4 ATR remains distance-only:

```text
S(t) = previous fully completed H4 Wilder ATR14
```

Never derive fixed SL/TP/trend rules from S.

---

## 4. Critical March correction to old Scale Alignment wording

The February postmortem correctly diagnosed excessive local authority, but the first March pass over-corrected it.

**Current authority:**

```text
A Child hard SL must invalidate the current Child entry thesis.
It does NOT need to invalidate the entire Parent Journey.
```

A Parent can remain alive after a Child is stopped. If genuinely new market information later forms a new Child, another attempt is allowed.

For a `PARENT-JOURNEY PARTICIPATION` trade, scale alignment means:

- the Child is economically meaningful inside the larger context;
- local risk is real Child falsification, not an arbitrary candle low/high;
- there is materially larger room if the Child joins a continuing Parent;
- management does not silently promote every later micro anchor to campaign-stop authority.

Do not return to the superseded interpretation that every local stop must also kill the H1/H4 Parent.

---

## 5. Hard SL is mandatory from May onward

For every **new** trade, before entry freeze:

```text
Decision timestamp
Direction
Entry M1 reference
Hard SL price
Initial risk points = |Entry - Hard SL|
Initial R = that hard risk
Child thesis / structural falsification
Intended Journey Scale
Destination or OPEN ROUTE
S
```

Rules:

- the Hard SL must already exist before the position opens;
- touching the Hard SL ends the trade; review delay cannot enlarge the planned price loss;
- the Hard SL may never be widened to rescue a trade;
- no automatic BE, fixed-R trail, ATR trail, or fixed partial is authorized;
- a structure-based manual exit before the Hard SL remains allowed;
- a stopped Child does not automatically invalidate the Parent.

2025 M1 cannot provide exact broker fill/slippage/spread economics. Historical R is therefore descriptive price-risk accounting, not exact execution P/L.

P038 is a grandfathered April carry. Do not rewrite April history as if it had a hard SL at entry. The May contract specifies its prospective protective treatment.

---

## 6. Entry and repeated attempts

Before entry ask:

1. What is the Parent working belief and strongest counterevidence?
2. Is value migrating, or are both directions repairing inside the same broad auction?
3. What exactly is the current Child?
4. What new information makes this Child independent?
5. If this is another same-direction attempt, **what exists now that did not exist at the previous failure?**
6. What price invalidates this Child now?
7. Is that exact price acceptable as the precommitted Hard SL?
8. Is the intended journey `LOCAL BRIDGE` or `PARENT-JOURNEY PARTICIPATION`?

A new attempt is not justified by attempt count or by Parent survival alone.

`WHAT IS NEW?` is a reasoning requirement, **not** a minimum-maturity checklist or automatic veto. A valid new Child can form quickly if the market immediately supplies causally new evidence (for example a stop-out followed by a genuine reclaim/departure). No minimum number of bars, holds, retests, or elapsed time is required.

Useful descriptive evidence of genuinely new information includes:

```text
new business at a different area
repeated hold
hold + departure
hold + departure + meaningful return test
auction/value relocation
failed repair that changes the active route
```

Do not create an N-loss cooldown or retry limit.

---

## 7. Position management and campaign health

Manage the declared thesis, not unrealized P/L.

Separate:

```text
execution damage
child-route damage
parent/campaign damage
```

For Parent-Journey positions, inspect whether the campaign can still progress:

- are new favorable extremes still being produced?
- after counterflow, is prior route/value being repaired?
- is settlement migrating in the intended direction or against it?
- is counterflow forming stronger/longer-lived business?
- are important Parent/Child origins being consumed?

Do not wait for metaphysical proof that a trend has ended. The research question is whether **progression ability is materially deteriorating**.

---

## 8. HTF indicator instrumentation is SHADOW ONLY

April retrospective discovery suggests H1 momentum location may help identify moments worth closer review, but it is not validated.

Record on completed H1 bars while a Parent-Journey trade is open:

```text
Stochastic(14,3,3) K and D
cross direction, if any
exact K/D location at cross
band: BELOW_20 / BETWEEN_20_80 / ABOVE_80
whether price subsequently makes a new favorable extreme
whether oscillator re-accelerates with the trend
H1 close vs EMA9
EMA9 direction
H1 settlement migration
```

Interpretation for research only:

- LONG: an adverse dead cross above/around 80 can be an early warning, not an exit command;
- SHORT: an adverse golden cross below/around 20 can be an early warning, not an exit command;
- do not presume that a mid-range or extreme-zone cross is inherently stronger; May must test whether cross location adds information beyond price/settlement;
- strong trends can cross repeatedly in extreme zones and continue.

**Never enter or exit solely because of Stochastic/EMA.**
H4 indicator crosses were generally too slow in April discovery and have no current trade authority.

---

## 9. Review cadence is operational, not a market rule

Hard SL prevents review latency from increasing planned loss, but late review can still damage winner capture.

Operational cadence:

- flat/no candidate: H1 context is the default review granularity; coarser compression is allowed only when no candidate is being skipped intentionally;
- candidate forming: M15;
- new trade / hard-SL vicinity / ambiguity: M15 and M1/M5 as required;
- open Parent-Journey trade: inspect every completed H1 at minimum as an **operational monitoring cadence**, not as an entry veto or mechanical exit trigger; tighten to M15 on meaningful deterioration warning;
- open Local-Bridge trade: M15-centered lifecycle.

If a coarse reveal skips an opportunity, do not backfill it.

Use `scripts/v9_causal_m1.py` for exact future-hidden prefix control and `scripts/v9_hard_stop_guard.py` to detect the first stop touch inside an already-revealed prefix.

---

## 10. Data authority and causal integrity

Authoritative raw M1:

```text
SHA256 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

The causal helper must expose only an exact chronological prefix. No future bar may be consulted before its cutoff.

Uploaded M5/M15/M30/H1/H4 files may accelerate reading only when:

- the bar is fully completed at the current causal cutoff;
- no unfinished higher-TF bar leaks later minutes;
- ambiguous entry/exit decisions fall back to revealed M1.

2025 exact Bid/Ask tick is unavailable. Do not present M1 price accounting as exact broker execution.

---

## 11. Current consumed evidence and active start state

Consumed development evidence includes January through April 2025. Do not treat those months as independent validation after using them for research revisions.

April closed ledger (descriptive):

```text
32 closed trades including March carry P006
6 positive / 26 loss
closed sum = +62.28R
April-new-entry closed sum = +32.58R
longest loss streak = 11 trades / -13.43R
```

Major positive examples:

```text
P006 +29.70R  (March carry)
P017 +16.77R
P029 +24.17R
P031 +23.05R
P032 +10.58R
```

Critical counterexamples:

```text
P009 MFE ~+15.6R -> +0.29R
P035 MFE ~+4.1R  -> -1.45R
P036 MFE ~+11.4R -> -4.39R
P019-P023 same-auction churn cluster
```

May starts after:

```text
2025-04-30 23:58
P038 SHORT OPEN
entry 3326.04
legacy accounting reference 3331.29
month-end 3288.42
month-end MTM about +7.17R on the legacy reference
MFE through April about +11.27R
```

Read the May contract for prospective treatment.

---

## 12. Prohibited overfit

Do not add from the consumed March/April examples alone:

- N-loss stop/cooldown;
- retry limits;
- minimum 3R/5R entry filters;
- fixed ATR/point SL or TP;
- Stochastic cross exit rules;
- EMA cross exit rules;
- indicator entry gates;
- fixed auction width;
- numeric scale score;
- mandatory Parent direction filter;
- passive hold-until-parent-death;
- fixed partial percentages;
- fixed profit-lock thresholds.

---

## 13. Formalization gate remains closed

No production V9 EA yet.

Need multiple future-hidden periods showing that:

- hard-SL precommitment produces bounded comparable risk without destroying good Child entries;
- same-auction/new-information distinctions reduce churn without suppressing genuine repeated participation;
- campaign-health observations preserve large winners while reducing catastrophic MFE giveback;
- HTF indicator observations add information beyond price/settlement rather than merely restating hindsight;
- the payoff shape survives other periods and later other instruments;
- exact execution is separately validated before production claims.
