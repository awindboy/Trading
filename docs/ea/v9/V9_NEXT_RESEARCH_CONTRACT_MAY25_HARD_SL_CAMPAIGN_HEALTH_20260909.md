# V9 Next Research Contract — May 2025 Hard SL, Child Independence, and Campaign Health

Date: `2026-09-09`
Status: `ACTIVE NEXT V9 CONTRACT / FUTURE-HIDDEN / DISCRETIONARY`
Market: `GOLD# ONLY`
Start boundary: `2025-04-30 23:58`
Start position: `P038 SHORT OPEN`
Production authority: `NONE`
EA authority: `NONE`
Untouched reserve: `GOLD# 2021`

## 1. Purpose

Test three post-April revisions prospectively:

1. precommitted Hard SL makes risk bounded and R meaningful;
2. same-direction reattempts improve when they require genuinely new market information rather than another reaction inside the same auction;
3. H1 campaign-health review can reduce destructive winner giveback without converting the strategy into an exact-top predictor.

Do not use May to prove April right. Seek counterexamples.

---

## 2. Starting carry

P038:

```text
SHORT 3326.04
April legacy accounting reference 3331.29
April month-end 3288.42
April MFE 3266.86
```

P038 predates the new Hard-SL rule. At the May boundary, prospectively arm `3331.29` as a **grandfathered one-time protective stop** before any May reveal. It is not an initial Hard SL and supplies no stop-placement evidence for future entries. Preserve all April metrics as legacy accounting; do not retroactively call them hard-stop metrics.

---

## 3. Hard SL prospective test

For every new May position:

- Hard SL is stated before entry;
- 1R is entry-to-Hard-SL distance;
- stop is never widened;
- stop touch terminates the Child even if price later recovers;
- Parent is reassessed separately;
- manual structural exit may occur before Hard SL.

Research questions:

- Are stops placed where the Child is actually wrong, or merely at nearby noise?
- Does precommitment prevent April-style -2R/-4R review-latency overshoots?
- Does it accidentally over-tighten entries and increase ordinary-noise stops?
- If a stopped Parent-aligned Child later produces a new opportunity, is the new attempt causally independent?

No numeric stop-size optimization is authorized.

---

## 4. Same-side retry matched pairs

For each retry, freeze the following to make the difference auditable. This is not a minimum-maturity gate; an immediate retry is allowed when the newly revealed evidence genuinely changes the Child:

```text
PRIOR SAME-SIDE FAILURE
WHAT FAILED THEN?
WHAT NEW BUSINESS / INFORMATION EXISTS NOW?
IS THIS THE SAME AUCTION OR A RELOCATED ONE?
WHY IS THIS CHILD INDEPENDENT?
```

At month end compare:

- failed retry -> failed retry;
- failed retry -> eventual large winner;
- first attempt -> large winner;
- no-trade periods where waiting for new information avoided churn.

The goal is to discover functional differences, not an Nth-attempt rule.

---

## 5. Campaign-health prospective panel

For Parent-Journey positions, every completed H1 records:

```text
favorable extreme progression
settlement/value migration
counterflow business strength
repair success/failure
meaningful memory consumption
campaign status: PROGRESSING / DAMAGED-BUT-REPAIRING / DETERIORATING / UNCLEAR
```

These words are discretionary observations, not a score.

Manual exit may use price/structure evidence already authorized by the trader. Do not wait for a fixed indicator trigger.

---

## 6. H1 indicator shadow hypothesis

Record but do not trade from:

```text
Stochastic(14,3,3) K/D
cross direction
cross exact K/D values
cross location: BELOW_20 / BETWEEN_20_80 / ABOVE_80
post-cross new favorable extreme?
post-cross oscillator re-acceleration?
H1 close vs EMA9
EMA9 direction
```

Prospective question:

> Does cross **location** (including extreme versus mid-range) add information beyond price progression and H1 settlement, and if so under what contexts? One candidate hypothesis is that an adverse extreme-zone cross becomes more informative when price also fails to produce new favorable extremes and H1 settlement begins to migrate against the trade.

Mandatory counter-hypothesis:

> Strong trends can remain pinned in extreme zones, cross repeatedly, and continue. Therefore location alone may still be mostly a momentum-pullback descriptor.

No Stochastic/EMA trade authority during May.

---

## 7. Review cadence contract

Hard SL removes planned-loss dependence on discretionary review timing.

Nevertheless:

- inspect each completed H1 while a Parent-Journey trade is open;
- tighten to M15 after campaign warning;
- use M1 around exact Hard SL/manual exit;
- flat/candidate cadence follows the active pipeline.

If the user pauses a session, persist exact cutoff, open-position state, hard stop, and all frozen trade fields to GitHub before changing research stage.

---

## 8. Required May ledger

For every entry:

```text
trade id
exact decision timestamp
side
entry
Hard SL
initial risk points
S
Parent belief
Child thesis
what is new vs previous same-side attempt
auction context
new-business state
anchor authority
intended journey scale
journey maturity
first destination / OPEN ROUTE
uncertainty
```

During/after:

```text
first stop touch if any
manual exit evidence if earlier
MFE/MAE
captured R/points/S
H1 campaign-health history
H1 indicator shadow history
Parent status after Child resolution
```

---

## 9. Falsification populations to seek

Actively preserve examples where:

- a perfect-looking structural Hard SL is hit as ordinary noise and Parent continues;
- a wider-looking hard stop still loses cleanly;
- same-auction waiting misses a huge move;
- immediate retry is genuinely justified and wins;
- extreme-zone Stochastic warning is early and trend continues much farther;
- extreme-zone warning plus price deterioration correctly precedes exit;
- no indicator warning occurs before abrupt structural failure;
- campaign-health review exits too early and sacrifices a large journey;
- holding through damage is correct;
- holding through damage repeats P035/P036-style giveback.

---

## 10. Promotion gate

Do not formalize indicator or retry rules from May alone.

A successful May phase means the revised process is causally usable and produces interpretable counterexamples, not that May P/L is high.

Formalization gate remains closed.
