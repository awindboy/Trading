# V9 Decisions Addendum — April 2025 Completion and May Pipeline

Date: `2026-09-09`
Status: `ACTIVE DECISION AUTHORITY`
Production authority: `NONE`
EA authority: `NONE`

## D1. Child failure and Parent failure are separate

Accepted:

```text
Child hard SL = current Child entry thesis invalidation.
Child hard SL does not need to equal Parent Journey invalidation.
```

Reason: the first March pass applied post-February Scale Alignment too strictly and nearly eliminated trading. Replaying March with Parent/Child separation restored repeated participation and large winners.

This decision supersedes any older wording that requires a local stop to materially invalidate the entire H1/H4 Parent.

---

## D2. Hard SL is mandatory before every new entry from May onward

Accepted immediately:

- exact Hard SL price is frozen before entry;
- initial R is the entry-to-Hard-SL price distance;
- Hard SL touch ends the trade regardless of review timing;
- Hard SL can never be widened;
- a structural/manual exit may happen before Hard SL;
- no fixed ATR/point stop formula is introduced;
- no automatic BE/trail/partial is introduced.

Reason: April replay showed that delayed review could turn a nominal ~1R structural reference into much larger realized price loss. Risk must be precommitted if R is to be meaningful.

P038 predates this decision. Do not rewrite April. Prospectively arm its legacy 3331.29 reference as a one-time protective stop at the May boundary before any May reveal; do not treat this grandfathered action as an example of valid initial stop placement.

---

## D3. Retry permission comes from new market information, not attempt count

Accepted as discretionary **reasoning discipline**, not a mechanical permission gate:

Before another same-direction attempt, explicitly state:

> What exists now that did not exist when the previous same-direction Child failed?

Potential answers can include new business, repeated hold, departure, meaningful return test, auction/value relocation, a newly failed repair, or an immediate reclaim/route change after the prior stop. None of these specific forms is mandatory.

`Another bounce`, `Parent still alive`, `this is the third attempt`, or `it looks ready now` are insufficient **without explaining what current market behavior makes the new Child distinct**. No cooldown, minimum bar count, or full maturation sequence is required.

No N-loss stop, cooldown, or retry limit is authorized.

---

## D4. Same-auction churn remains a primary failure mode

April P019-P023 and prior February clusters remain mandatory counterexamples.

Do not relabel every interior reaction/failed repair as a new independent Child when both routes are repeatedly repairing inside the same broad auction.

`NEW / SAME / AMBIGUOUS AUCTION` remains descriptive; no numeric regime classifier is authorized.

---

## D5. Campaign-health research is promoted in priority, not formalized as an exit rule

April confirmed that V9 can participate in large journeys, but also showed severe giveback:

```text
P009 ~+15.6R MFE -> +0.29R
P035 ~+4.1R MFE  -> -1.45R
P036 ~+11.4R MFE -> -4.39R
```

Therefore open Parent-Journey positions must explicitly assess progression ability on completed H1 bars.

Price/structure questions include favorable-extreme progression, settlement migration, repair success/failure, counterflow business, and memory consumption.

No fixed profit-lock threshold is authorized.

---

## D6. H1 Stochastic location / EMA observations are shadow-only

Retrospective April exploration suggests that H1 Stochastic cross **location** may be worth recording, especially alongside price progression. It is not yet established that extreme-zone crosses are more informative than mid-range crosses. Strong trends can also produce multiple extreme-zone crosses and continue.

Record:

- Stochastic(14,3,3) K/D;
- cross direction;
- exact K/D at cross;
- location band relative to 20/80;
- subsequent favorable-extreme and re-acceleration behavior;
- H1 close vs EMA9 and EMA9 direction.

Rejected for now:

```text
Stochastic cross = exit
80 dead cross = top
20 golden cross = bottom
EMA9 break = automatic exit
indicator = entry gate
```

H4 indicator crosses have no current authority; April discovery suggested they were generally too delayed for this question.

---

## D7. Review cadence is still required even with Hard SL

Hard SL solves maximum planned loss drift, not winner capture.

For Parent-Journey positions, every completed H1 must be reviewed at minimum. Tighten to M15 when deterioration or stop ambiguity becomes material.

This is an operational discipline, not a market filter.

---

## D8. Formalization remains closed

The May replay is a future-hidden test of the revised discretionary pipeline. Do not code an EA or convert shadow fields into scores/thresholds until repeated independent evidence exists.
