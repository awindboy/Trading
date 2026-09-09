# V9 Discretionary Trading Pipeline — June 2025 Auditable Discretion Authority

Date: `2026-09-09`
Status: `ACTIVE TRADING PIPELINE / FUTURE-HIDDEN JUNE / AUDITABLE DISCRETION`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Purpose of this pipeline

This pipeline does **not** make V9 mechanical.

It exists so another session can inspect whether the discretionary trader actually followed V9.

Keep separate:

```text
MARKET STRATEGY
= what the market evidence means and what opportunity is being traded

COMPLIANCE HARNESS
= questions and records required to prove the strategy was applied consistently
```

The harness must expose hidden drift without converting examples into numeric rules.

---

## 1A. Canonical tooling / market representation

Read and obey `V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260909.md`.

The official decision input is numeric OHLC reconstructed from the verified raw-M1 causal prefix. Chart images are optional visualization only and have no image-only authority.

Do not preload the full future file into the active discretionary dataframe. Use monotonic prefix streaming.

Timeframe state machine:

```text
flat/no candidate -> H1 default
serious candidate -> M15
exact ambiguity -> M5/M1
Parent-Journey -> H1; M15 on warning
Local Bridge -> M15
```

Once candidate mode begins, do not reveal the remainder of the H1. A cadence violation contaminates the exposed interval and forbids backfill.

## 2. Session bootstrap — mandatory before any new future reveal

1. Refresh latest GitHub HEAD.
2. Read current V9 authority/resume order.
3. Verify authoritative M1 SHA256 `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`.
4. Verify exact chronological cutoff and position state.
5. Audit current authority documents for any already-known June outcome/date references and record contamination before revealing June prices.
6. State that the June harness is frozen for the month. New process ideas go to `HARNESS SHADOW ISSUE`; do not silently change live rules from P/L.

Do not reveal the first June price until this bootstrap is complete.

---

## 3. Flat H4/H1 read — two-sided by construction

Default hierarchy:

```text
H4/H1: Parent Journey, value/settlement migration, major active memories
H1/M15: Child route, repair/failure, auction context
M15/M5/M1: exact execution and Hard SL
```

At each meaningful H1 context change, record:

```text
CURRENT PARENT WORKING BELIEF
EVIDENCE THAT SUPPORTS IT
STRONGEST DAMAGE TO IT
OPPOSITE / INVERSION CASE
AUCTION: NEW / SAME / AMBIGUOUS
ACTIVE MEMORIES BY ROLE
```

Parent is never a mandatory direction filter.

Do not force both sides to be tradable. The point is to **evaluate both sides by the same standard**.

---

## 4. Serious candidate definition and audit

A `SERIOUS CANDIDATE` begins when the trader tightens from ordinary H1 context review to M15 because an entry may plausibly be forming.

For every serious candidate, freeze before the next decision:

```text
SIDE
CURRENT CHILD ROLE
WHY THIS MAY BE A REAL OPPORTUNITY NOW
STRONGEST COUNTEREVIDENCE
WHY NOT THE OPPOSITE SIDE NOW?
PRIOR SAME-SIDE FAILURE, IF ANY
WHAT IS NEW NOW, IF RETRY?
```

Then decide:

```text
TRADE
or
NO TRADE + explicit authority-grounded reason
```

Do not backfill rejected or skipped candidates later.

---

## 5. Child independence and pitch quality are separate gates

### Gate A — Child independence

Ask:

> Is this current Child causally distinct from the previous failed attempt or unresolved same auction?

Possible evidence includes new business, repeated hold, departure, meaningful return/reuse, auction/value relocation, or a failed repair that changes route authority.

No example is mandatory. No minimum bars or retests are required.

### Gate B — Worthwhile pitch

Ask:

> Even if the Child is distinct, why is this a good enough pitch to risk on here?

The answer should connect:

- current Child role;
- Parent/opposite context;
- actual structural falsification;
- intended journey scale;
- whether the market is demonstrating decision sufficiency rather than merely movement.

`It is new`, `Parent is alive`, `price is moving`, or `this looks like the next leg` are insufficient alone.

---

## 6. No-chase and route-room interpretation

Prohibited hidden rules:

```text
already moved => automatic no trade
nearest memory too close => automatic no trade
immediate known-room < stop distance => automatic no trade
overbought/oversold => automatic no trade
```

Prior movement, journey maturity, nearest memory, and route room remain relevant context.

But the trader must translate them into the actual thesis:

- Does this current Child still provide meaningful falsification?
- Is the Parent progression still live?
- Is the nearest memory the end of this trade, or only a checkpoint?
- Is `OPEN ROUTE` justified by current market behavior rather than desire for a large winner?

No numeric minimum R is authorized.

---

## 7. Pre-entry freeze — mandatory

No position opens until all fields are stated:

```text
TRADE ID
DECISION TIME
DIRECTION
ENTRY M1 REFERENCE

PARENT WORKING BELIEF
PARENT SUPPORT
PARENT DAMAGE / STRONGEST COUNTEREVIDENCE
OPPOSITE-SIDE CASE

CURRENT CHILD THESIS
CHILD ROLE / WHY IT IS MEANINGFUL
WHAT IS NEW, IF RETRY
WHY THIS IS A WORTHWHILE PITCH
WHY THIS SIDE NOW
WHY NOT OPPOSITE SIDE NOW

CHILD STRUCTURAL FALSIFICATION
HARD SL PRICE
INITIAL RISK POINTS

INTENDED JOURNEY SCALE
DESTINATION / CHECKPOINT / OPEN ROUTE
S
JOURNEY MATURITY

MIRROR CHECK RESULT
HIDDEN-VETO CHECK RESULT
```

### Hard SL

- real precommitted maximum price-risk boundary;
- frozen before entry;
- touch ends the Child;
- never widen;
- manual structural exit may occur earlier;
- exact 2025 broker fill is not claimed from M1.

If the audit exposes inconsistent reasoning, fix the reasoning before entering. Do not fill missing fields after the trade is open.

---

## 8. Mirror and hidden-veto checks

### Mirror check

Ask:

> If equivalent evidence appeared in the opposite direction, would I apply the same standard?

This is not a demand to take the opposite trade. It is a bias detector.

### Hidden-veto check

Explicitly reject any undocumented gate such as:

- implicit minimum R;
- automatic `already moved too much`;
- Parent-direction-only permission;
- Stochastic/EMA permission;
- attempt-count logic;
- desire to make back losses;
- desire to avoid missing a move.

If a phrase such as `too late`, `too close`, `extended`, or `not enough room` is used, state the **structural meaning** that makes it relevant.

---

## 9. Intended journey scale

Freeze one:

```text
LOCAL BRIDGE
PARENT-JOURNEY PARTICIPATION
```

`LOCAL BRIDGE` means the thesis itself is local and is expected to resolve at a known nearby route/destination.

It must not be used simply because a Parent is uncertain or because holding a larger move is uncomfortable.

If a coherent Parent and meaningful Child exist, explicitly consider Parent-Journey participation.

Do not force Parent trades when the actual thesis is local.

---

## 10. Position lifecycle — keep damage layers separate

At every review keep separate:

```text
EXECUTION DAMAGE
CHILD-ROUTE DAMAGE
PARENT/CAMPAIGN DAMAGE
```

A micro anchor does not automatically become full-position exit authority.

A Child stop does not automatically kill the Parent.

A Parent belief does not rescue a Child whose Hard SL was touched.

---

## 11. Campaign-health review for Parent-Journey positions

At every completed H1 record:

```text
NEW FAVORABLE EXTREME? YES / NO
SETTLEMENT / VALUE MIGRATION
COUNTERFLOW BUSINESS STRENGTH
ROUTE REPAIR AFTER DAMAGE
IMPORTANT MEMORY CONSUMPTION
CAMPAIGN STATUS: PROGRESSING / DAMAGED-REPAIRING / DETERIORATING / UNCLEAR
```

If warning becomes material, tighten to M15/M1.

Before a full manual exit state:

```text
WHICH LAYER IS FAILING?
WHAT SPECIFIC PRICE/SETTLEMENT EVIDENCE SHOWS LOSS OF PROGRESSION?
WHY IS THIS MORE THAN A NORMAL PULLBACK / MICRO REACTION?
```

Do not exit solely from P/L, Stochastic, EMA, fixed R, or fear of giveback.

---

## 12. Local-Bridge lifecycle

M15-centered.

Resolve according to the declared local thesis/destination unless:

- Hard SL is touched; or
- causal structure invalidates the local bridge earlier.

Do not convert a Local Bridge into a Parent trade after the move becomes profitable unless a **new trade decision** is explicitly made under the full Parent-Journey audit. No hindsight relabeling.

---

## 13. Indicator shadow panel — unchanged

On completed H1, record as useful:

```text
Stochastic(14,3,3) K/D
cross direction and K/D
20/80 band
post-cross favorable-extreme behavior
re-acceleration behavior
H1 close vs EMA9
EMA9 direction
```

No indicator has trade authority.

---

## 14. Review cadence

### Flat/no candidate

H1 default. Context compression is allowed only when no serious candidate is being skipped.

### Serious candidate

M15. Use M5/M1 when exact entry/falsification matters.

### Parent-Journey position

Every completed H1 minimum. Tighten to M15 on meaningful warning and M1/M5 near exact stop/manual-exit ambiguity.

### Local Bridge

M15-centered.

Any skipped opportunity remains missed. Never backfill.

---

## 15. End-of-trade freeze

Record before interpreting later recovery/continuation:

```text
EXIT TYPE
EXIT TRIGGER TIME
EXIT M1 REFERENCE
EXIT LAYER: EXECUTION / CHILD / PARENT-CAMPAIGN
MFE
MAE
CAPTURED POINTS / R / S
PARENT STATUS AFTER CHILD EXIT
WHAT WOULD BE NEEDED FOR A NEW SAME-SIDE CHILD?
```

Later same-direction price cannot rescue an invalidated Child.

---

## 16. Session-level compliance audit

At pause/end of work, record:

```text
LONG TRADES / SHORT TRADES
LONG SERIOUS CANDIDATES / SHORT SERIOUS CANDIDATES
ANY STRONG SIDE IMBALANCE + MARKET REASON
CANDIDATES REJECTED FOR NO-CHASE / ROOM / PARENT REASONS
ANY HIDDEN RULE DISCOVERED?
ANY LOCAL BRIDGE USED WHERE PARENT-JOURNEY WAS PLAUSIBLE?
ANY RULE CHANGED MID-SESSION?
ANY CAUSAL-INTEGRITY INCIDENT?
```

Trade-count symmetry is not required. The audit detects bias; it does not create trades.

---

## 17. Frozen-harness rule for June

The June process above is frozen once the first June price is revealed.

By explicit user instruction, a tooling/observation parity amendment was added at causal cutoff `2025-06-12 07:59`. That amendment is documented separately and does not authorize a new market edge. From that boundary onward, the tooling protocol is also frozen.

New possible improvements must be logged as:

```text
HARNESS SHADOW ISSUE
```

Do not change live June entry/exit interpretation from emerging P/L or a small number of examples.

Exceptions require explicit user instruction or a causal/safety failure.

---

## 18. Prohibited behavior

- widening Hard SL;
- Parent as mandatory direction veto;
- treating Child independence as sufficient entry permission;
- implicit minimum-R or nearest-memory gate;
- undocumented `already moved too much` veto;
- forcing equal LONG/SHORT counts;
- automatic BE/partial/trail;
- indicator mechanical entries/exits;
- N-loss cooldown/retry limits;
- same-auction rapid-fire relabeling;
- backfilling missed trades;
- rescuing stopped trades;
- changing definitions after outcomes;
- changing the June harness mid-month from P/L.
