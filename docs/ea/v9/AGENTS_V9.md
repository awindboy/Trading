# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-09`
Status: `ACTIVE / MAY CONSUMED / JUNE AUDITABLE-DISCRETION REPLAY NEXT`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched final temporal reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Authority and resume order

GitHub is permanent memory. Chat history is a workbench.

Every new V9 session must:

1. refresh latest GitHub HEAD;
2. read root `AGENTS.md` / `docs/ea/HANDOFF.md` only for routing/context;
3. read this file;
4. read `docs/ea/v9/HANDOFF_V9.md`;
5. read `docs/ea/v9/RESEARCH_STATE_V9.md`;
6. read `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md` for stable mindset;
7. read `docs/ea/v9/DECISIONS_V9_APR25_PIPELINE_ADDENDUM_20260909.md`;
8. read `docs/ea/v9/DECISIONS_V9_MAY25_HARNESS_ADDENDUM_20260909.md`;
9. read `docs/ea/v9/DECISIONS_V9_JUN25_CAUSAL_TOOLING_STANDARD_ADDENDUM_20260909.md`;
10. read `docs/ea/v9/results/V9_APR25_COMPLETION_AND_PIPELINE_POSTMORTEM_20260909.md`;
11. read `docs/ea/v9/results/V9_MAY25_COMPLETION_AND_HARNESS_POSTMORTEM_20260909.md`;
12. read `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260909.md`;
13. read `docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_JUN25_20260909.md`;
14. read `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_JUN25_AUDITABLE_DISCRETION_20260909.md` before advancing future-hidden June data;
15. inspect authoritative raw-data/cutoff state before advancing future-hidden replay.

Older `V9_NEXT_RESEARCH_CONTRACT_*` files marked `SUPERSEDED` or `CONSUMED` are historical only.

V10 is separate and not V9 authority.

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
+ lets a Child fail without automatically killing the Parent
+ remains available for genuinely new Child attempts
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
later same-direction movement cannot rescue an invalidated Child
invalid Child != invalid Parent
winning Child != proof of Parent direction
high R != large market-scale capture
independent Child != worthwhile pitch
```

Core hierarchy:

```text
PARENT JOURNEY        H1/H4 strategic continuity
CHILD ROUTE           M15/H1 current attempt / repair / continuation
EXECUTION STRUCTURE   M5/M15/M1 exact decision and hard risk
```

H4 ATR is distance-only:

```text
S(t) = previous fully completed H4 Wilder ATR14
```

Never derive fixed SL/TP/trend rules from S.

---

## 4. Strategy authority and compliance harness are separate

May proved that reading the same strategy documents does not guarantee equivalent execution.

Permanent separation:

```text
STRATEGY AUTHORITY
= market hierarchy, opportunity, falsification, risk, lifecycle

COMPLIANCE HARNESS
= required questions and records proving the strategy was applied consistently
```

The harness may constrain **how reasoning is performed and recorded**.
It must not invent a new market edge, score, threshold, or pattern checklist.

A session must not claim compliance merely because it read these files. It must complete the active pipeline's decision packet and self-audits contemporaneously.

---

## 4A. Canonical tooling / observation authority

Official V9 discretionary replay must use `V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260909.md`.

Canonical representation:

```text
verified raw M1 chronological prefix
-> raw-M1-derived completed H4/H1/M15
-> numeric OHLC as primary perceptual input
```

Chart images are optional visualization only. Image zoom, y-axis scale, candle pixel size, or visual slope has no independent trade authority. Any material visual claim must be restated in exact causal price/settlement terms.

Canonical observation state machine:

```text
FLAT / NO CANDIDATE     -> H1 default, H4 context
SERIOUS CANDIDATE       -> M15
EXACT EXECUTION ISSUE   -> M5/M1 as needed
OPEN PARENT-JOURNEY     -> completed H1; M15 on material warning
OPEN LOCAL BRIDGE       -> M15-centered
```

Do not preload the complete future price file into the official discretionary analysis dataframe. Use monotonic prefix streaming / guarded advance.

Tooling parity is part of session compliance. If another AI cannot reproduce the canonical numeric observation contract, label its replay `TOOLING NON-PARITY` rather than merging it with equivalent V9 execution evidence.

## 5. Child and Parent authority

A Child hard SL must invalidate the current Child thesis.
It does **not** need to invalidate the entire Parent Journey.

A stopped Child is finished. Later same-direction movement never rescues it.

A Parent may survive, but Parent survival alone does not authorize another trade.
A new attempt requires causally new current information.

Critical May addition:

```text
NEW / INDEPENDENT CHILD
!=
GOOD PITCH
```

Before entry the trader must explain both:

1. why the current Child is distinct from a prior failed attempt / same auction;
2. why this Child is worth risking on **now** inside current Parent/opposite context.

Examples such as repeated hold, departure, return/reuse, failed repair, or value relocation are descriptive only. No minimum sequence or bar count is authorized.

---

## 6. Parent is a working belief, never a directional veto

While flat, the trader must evaluate:

```text
CURRENT PARENT CONTINUATION CASE
+
STRONGEST OPPOSITE / INVERSION CASE
```

Before entry state:

```text
WHY THIS SIDE NOW?
WHY NOT THE OPPOSITE SIDE NOW?
```

Run a mirror check:

> If equivalent evidence appeared in the opposite direction, would I judge it by the same standard?

This does not force equal LONG/SHORT counts. It prevents a previous Parent narrative from receiving unexplained privilege.

After every Child resolution, explicitly reassess Parent status from current evidence rather than carrying it forward by inertia.

---

## 7. Hard SL remains mandatory

For every new trade, freeze before entry:

```text
Decision timestamp
Direction
Entry M1 reference
Child thesis / structural falsification
Hard SL price
Initial risk points = |Entry - Hard SL|
Initial R = that hard risk
Intended Journey Scale
Destination / checkpoint / OPEN ROUTE
S
```

Rules:

- Hard SL exists before entry;
- touch ends the Child;
- never widen;
- manual structural exit may occur earlier;
- no automatic BE, fixed-R trail, ATR trail, or fixed partial;
- Child stop does not imply Parent death.

2025 M1 provides descriptive price-risk accounting, not exact broker execution economics.

---

## 8. `NO CHASE` must not become a hidden filter

Permanent interpretation:

```text
already moved != automatic no-trade
nearest memory != automatic TP
nearest-memory R != automatic entry gate
OPEN ROUTE != permission to ignore structure
```

`NO CHASE` means do not enter merely from fear of missing an already-moving market.
It does not prohibit a Parent-Journey entry after meaningful prior movement if a current Child still provides real falsification inside a live larger route.

If the trader uses words such as:

```text
too late
too extended
not enough room
nearest memory too close
```

it must state the **structural meaning** that makes that context relevant.

No fixed minimum-R, ATR, point, or journey-age gate is authorized.

---

## 9. Intended journey scale must change actual behavior

Freeze:

```text
LOCAL BRIDGE
or
PARENT-JOURNEY PARTICIPATION
```

`LOCAL BRIDGE` is valid when the trade thesis itself is local and resolves at a local route/destination.

It must not be used simply because Parent continuation is uncertain, the trader fears giveback, or the nearest memory is visible.

When a coherent Parent and meaningful Child exist, explicitly consider Parent-Journey participation.

The main V9 research ambition remains material participation in larger market journeys.

---

## 10. Serious candidate audit is mandatory

A `SERIOUS CANDIDATE` starts when the trader tightens from ordinary H1 context to M15 because an entry may plausibly form.

Every serious candidate must end in either:

```text
TRADE
or
NO TRADE + explicit authority-grounded reason
```

Before decision record at minimum:

```text
side
Parent support / damage
opposite-side case
Child role
why independent, if retry
why worthwhile pitch
strongest counterevidence
why this side / why not opposite
mirror check
hidden-veto check
```

This exposes missed Parent opportunities and undocumented filters.

Do not backfill a rejected/skipped candidate after outcome reveal.

---

## 11. Position management and campaign health

Always separate:

```text
EXECUTION DAMAGE
CHILD-ROUTE DAMAGE
PARENT/CAMPAIGN DAMAGE
```

For Parent-Journey positions, inspect every completed H1 at minimum:

- new favorable extreme?
- settlement/value migration?
- counterflow business strength/longevity?
- route repair after damage?
- important memory consumed?
- progression alive, repairing, unclear, or materially deteriorating?

A full manual Parent-Journey exit must name which layer is failing and the actual price/settlement evidence showing loss of progression ability.

Do not wait for metaphysical Parent death, but do not promote a micro reaction into Parent failure either.

---

## 12. HTF indicators remain shadow-only

May did not earn indicator authority.

H1 shadow observations may include:

```text
Stochastic(14,3,3) K/D and cross
20/80 location
post-cross favorable-extreme behavior
re-acceleration
H1 close vs EMA9
EMA9 direction
settlement migration
```

Never enter or exit solely from Stochastic/EMA.
Strong trends can cross repeatedly in extreme zones and continue.

---

## 13. Session-level compliance self-audit

At every pause/end of session record:

- LONG/SHORT trades and serious candidates;
- any strong directional imbalance and the current market reason;
- candidates rejected using no-chase/room/Parent language;
- whether any hidden rule not in authority was used;
- whether Local Bridge was chosen where a coherent Parent-Journey thesis was available;
- whether any definition/process changed after seeing P/L;
- any causal-integrity incident.

Do not force balanced trade counts.

---

## 14. June frozen-harness rule

Before the first June price reveal, complete the contamination preflight in the June contract.

Once June begins, the active June pipeline is frozen for the month.

At causal cutoff `2025-06-12 07:59`, the user explicitly standardized cross-AI tooling/observation. This is an allowed user-directed contract amendment, documented in `DECISIONS_V9_JUN25_CAUSAL_TOOLING_STANDARD_ADDENDUM_20260909.md`. From that boundary forward, the causal numeric tooling protocol is frozen unless the user explicitly changes it or causal/safety integrity is compromised.

New possible process improvements are `HARNESS SHADOW ISSUE` only. Do not repair the live harness from emerging P/L unless the user explicitly changes the contract or causal/safety integrity is compromised.

---

## 15. Data and causal integrity

Authoritative M1 SHA256:

`626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

Use an exact chronological prefix. Never inspect a future price row before its cutoff.

Raw-M1-derived higher-timeframe aggregation is the canonical/default representation. Uploaded higher-TF data is usable only as a parity/acceleration aid when the complete bar is behind the current cutoff. Any disagreement or ambiguity falls back to the revealed raw M1 prefix.

Any accidental reveal is recorded and no hindsight trade is inserted into the exposed interval.

---

## 16. Consumed evidence status

January-May 2025 are consumed development evidence.

April remains promising convex Parent-Journey evidence with concentrated large winners, but not validation.

May first pass is retained as **discretionary execution/process-drift evidence**.

May second pass is retained as **retrospective outcome-contaminated harness audit**, not performance evidence.

The large first/second-pass divergence is itself evidence that cross-session compliance must be tested prospectively.

---

## 17. Prohibited overfit / process drift

Do not add or use:

- N-loss stop/cooldown;
- retry limits;
- fixed minimum R;
- fixed ATR/point SL or TP;
- Stochastic/EMA entry or exit rules;
- fixed profit lock/partial/trailing multiple;
- mandatory Parent direction filter;
- forced LONG/SHORT balance;
- mandatory hold/retest counts;
- fixed auction-width classifier;
- `already moved too much` as undocumented veto;
- Child independence as sufficient entry permission;
- silent mid-June harness revision from P/L;
- passive hold-until-parent-death.

---

## 18. Formalization gate remains closed

No production V9 EA yet.

Need future-hidden evidence showing both:

1. the strategy itself retains useful Parent-Journey opportunity/risk behavior; and
2. the auditable harness makes discretionary execution inspectable and more reproducible across sessions without becoming a rigid threshold system.

June is the next prospective test.
