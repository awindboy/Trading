# V9 Discretionary Trading Pipeline — May 2025 Authority

Date: `2026-09-09`
Status: `ACTIVE TRADING PIPELINE / DISCRETIONARY / FUTURE-HIDDEN`
Market: `GOLD# ONLY`
Production authority: `NONE`

## 1. Session bootstrap

1. Verify latest GitHub authority/resume order.
2. Verify authoritative M1 source hash `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2` when initializing a new causal replay state.
3. Resume only from the exact stored cutoff. Never expose a future row to speed up interpretation.
4. Completed H4/H1/M30/M15/M5 files may be used as speed aids only when the entire bar is already behind the causal cutoff.
5. Current/incomplete higher-TF bars must be reconstructed from revealed M1, never read from a full future-containing higher-TF row.

---

## 2. Flat market read

Default hierarchy:

```text
H4/H1: Parent Journey, major active memories, settlement/value migration
H1/M15: current Child route, repair/failed repair, auction context
M15/M5/M1: precise entry and Hard SL
```

Before searching for an entry, state:

- Parent working belief;
- strongest supporting evidence;
- strongest damage/counterflow;
- `NEW / SAME / AMBIGUOUS AUCTION`;
- current Child, if any;
- active memories by role;
- whether a prior same-side Child recently failed.

---

## 3. New-Child test

If there was a prior same-direction failure, answer before re-entry:

```text
WHAT IS NEW NOW?
```

Good evidence can be:

- actual new business at a distinct area;
- repeated hold after failure;
- hold followed by departure;
- meaningful return test and renewed hold;
- auction/value relocation;
- failed repair that changes route authority.

Insufficient by itself:

- another candle pattern;
- another bounce at the same area;
- Parent still alive;
- Nth attempt logic;
- desire to avoid missing the move.

No fixed time delay or retry count is used.

---

## 4. Pre-entry freeze — mandatory

No position opens until all fields are stated:

```text
DECISION TIME
DIRECTION
ENTRY M1 REFERENCE
PARENT BELIEF
CURRENT CHILD THESIS
WHAT IS NEW (if retry)
CHILD STRUCTURAL FALSIFICATION
HARD SL PRICE
INITIAL RISK POINTS
INTENDED JOURNEY SCALE
DESTINATION or OPEN ROUTE
S
UNCERTAINTY / STRONGEST COUNTEREVIDENCE
```

### Hard SL rule

The Hard SL is a real precommitted maximum price-risk boundary for replay accounting.

- LONG: future revealed M1 low touching/breaching SL => stopped.
- SHORT: future revealed M1 high touching/breaching SL => stopped.
- stop cannot be widened;
- no later structural story can rescue a touched stop;
- exact broker fill is not claimed from 2025 M1.

The Hard SL invalidates the **current Child**, not necessarily the Parent.

---

## 5. Position lifecycle

Immediately after entry, preserve three separate layers:

```text
EXECUTION DAMAGE
CHILD-ROUTE DAMAGE
PARENT/CAMPAIGN DAMAGE
```

A new micro anchor does not automatically become the full-position stop.
A nearby Child transit memory does not automatically become full TP.

### Hard-risk check

At every later review, first run/check the Hard SL over all newly revealed M1 rows. If it was touched earlier, the trade ended at that first touch; later recovery does not rescue it.

Use `scripts/v9_hard_stop_guard.py` for this purpose.

### Manual exit before Hard SL

Allowed when the causal chart already shows meaningful thesis deterioration before the stop.

This can reduce loss or protect a winner, but must be justified by market evidence, not P/L discomfort.

---

## 6. Campaign-health review for Parent-Journey trades

At every completed H1, record the following as a monitoring discipline. This cadence does not itself deny entries or force exits:

```text
1. Did price make a new favorable extreme since the prior review?
2. Where did H1 settlement/value move?
3. Did counterflow create stronger or longer-lived business?
4. Did the intended route repair after damage?
5. Did a meaningful Child/Parent origin get consumed?
6. Is progression alive, slowing, or materially deteriorating?
```

Do not ask `has the final top/bottom happened?`.
Ask `does this campaign still demonstrate the ability to progress?`.

If deterioration becomes meaningful, tighten review to M15/M1 and decide whether a manual structural exit is justified.

---

## 7. HTF indicator shadow panel — no trade authority

On completed H1 only, calculate/record:

```text
Stochastic(14,3,3) K
Stochastic(14,3,3) D
new cross? GOLDEN / DEAD / NONE
cross exact K/D
cross band: BELOW_20 / BETWEEN_20_80 / ABOVE_80
post-cross favorable extreme? yes/no
post-cross stochastic re-acceleration? yes/no/unclear
H1 close vs EMA9
EMA9 rising/falling/flat
```

Research interpretation only:

- LONG + adverse dead cross near/above 80 => attention increases;
- SHORT + adverse golden cross near/below 20 => attention increases;
- a mid-range cross alone is weak evidence;
- repeated extreme-zone crosses may simply accompany a strong trend.

Never exit or enter solely from this panel.

---

## 8. Review cadence

### Flat

Default to completed H1 review. If no candidate is remotely near, contextual compression is allowed. Any skipped trade remains missed; never backfill.

### Candidate

M15. Use M5/M1 only where exact entry/falsification matters.

### Parent-Journey position

- every completed H1 is mandatory;
- M15 after a meaningful campaign-health warning;
- M1/M5 around exact Hard SL/manual-exit ambiguity.

### Local-Bridge position

M15-centered lifecycle unless exact stop/execution requires M1.

Hard SL means a late discretionary review must never increase planned stop loss.

---

## 9. R accounting

For new May trades:

```text
Initial 1R = |Entry - precommitted Hard SL|
```

All MFE/MAE/captured-R values use that frozen denominator.
Do not change R after moving through the trade.

For the grandfathered P038 carry, April metrics retain the old `legacy accounting R`; do not relabel them as hard-SL R.

---

## 10. P038 transition

Start boundary:

```text
2025-04-30 23:58
P038 SHORT OPEN
entry 3326.04
legacy ref 3331.29
current 3288.42
```

At the May boundary, **prospectively** arm `3331.29` as a one-time protective stop for the remaining grandfathered position before any May reveal. This is not an initial Hard SL and is not a stop-placement template for future trades.

This does not rewrite the April entry decision. It only prevents review latency from creating an unbounded loss if the carried trade violently reverses after May begins.

Continue campaign-health management normally and allow manual exit before that stop if deterioration becomes sufficient.

---

## 11. End-of-trade record

Freeze:

```text
EXIT TYPE: HARD SL / MANUAL STRUCTURAL / DESTINATION-RESOLUTION / OTHER EXPLICIT
EXIT TRIGGER TIME
EXIT M1 REFERENCE
MFE
MAE
CAPTURED POINTS
CAPTURED R
CAPTURED S
PARENT STATUS AFTER CHILD EXIT
```

If the Parent survives, remain available for another Child only after explicitly identifying genuinely new information.

---

## 12. Prohibited behavior

- widening Hard SL;
- turning Parent into mandatory direction filter;
- automatic BE/partial/trail;
- Stochastic/EMA mechanical exits;
- N-loss cooldown/retry limit;
- backfilling missed trades;
- rescuing stopped trades with later same-direction movement;
- changing definitions after seeing the outcome.
