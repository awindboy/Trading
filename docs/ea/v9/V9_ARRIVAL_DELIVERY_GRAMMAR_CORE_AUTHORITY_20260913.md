# V9 Arrival / Delivery Grammar Core Authority

Date: `2026-09-13`
Status: `ACTIVE SEMANTIC RESEARCH AUTHORITY`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## 1. Purpose

This document freezes the **semantic research direction**, not a production trading strategy.

The project previously over-expanded local H1/H4 observations into many market states. Current consumed research supports a simpler destination-first representation.

## 2. Top-level Grammar

The market is represented at the top level as:

```text
MOVING
ARRIVAL
```

`MOVING` intentionally tolerates:

- acceleration / deceleration;
- pullback;
- temporary countertrend movement;
- H1 interrupt / realign;
- H4/H1 contextual state changes;
- local balance.

None of these facts alone creates a new top-level Grammar state.

## 3. ARRIVAL is factual and attributed

Every meaningful arrival carries attributes.

### Side

```text
UP
DOWN
OVERLAP / UNRESOLVED
```

Side means where the destination lay relative to price / which liquidity side was consumed. It is not itself trend authority.

### Role

```text
H4 LIQUIDITY ARRIVAL
-> DELIVERY / PROGRESSION evidence

H4 FVG / OB ARRIVAL
-> RESPONSE / INTERACTION evidence
```

Both are meaningful arrivals, but they do not carry equal semantic weight.

## 4. Slow route status

The current compact route-status vocabulary is:

```text
PRIMARY_ACTIVE(side)
CHALLENGED / UNRESOLVED
PRIMARY_CONTINUES
CHALLENGER_EARNED
```

Candidate causal transition logic:

```text
PRIMARY_ACTIVE(side A)
  + opposite H4 LIQ arrival(side B)
  -> CHALLENGED(A vs B)

CHALLENGED(A vs B)
  + next H4 LIQ side A
  -> PRIMARY_CONTINUES(A)

CHALLENGED(A vs B)
  + next H4 LIQ side B
  -> CHALLENGER_EARNED(B)
```

This is a semantic resolver earned from consumed research. It is not proof of certainty and may occasionally remap incorrectly or late.

## 5. Explicit uncertainty is part of the model

`CHALLENGED` is not an error state to be eliminated.

It means:

```text
old delivery still has a coherent claim;
challenger has produced meaningful opposite liquidity delivery;
current evidence is insufficient to force one side.
```

Current trading-research default:

```text
CHALLENGED -> NO NEW DIRECTIONAL EDGE ASSUMED
```

This does **not** yet define what to do with an already-open Child. Existing-position management remains a research question; Hard SL remains binding.

## 6. POI semantics

POI touch is not automatic route completion.

Consumed research found no stable direction classifier from POI-only touch/orientation sufficient to promote it to route authority.

Therefore:

```text
POI = response / interaction context
POI != automatic continuation
POI != automatic reversal
POI != automatic exit
```

AI/human analysis may use POI semantics to describe the journey, but exact geometry and lifecycle remain code-owned.

## 7. Dynamic destination set

A route is not one fixed origin-to-one-fixed-TP object.

Use:

```text
ACTIVE_DESTINATION_SET
CONSUMED_DESTINATIONS
NEWLY_OPENED_DESTINATIONS
RETIRED / INVALIDATED DESTINATIONS
```

The set may change while `PRIMARY_ACTIVE` remains the same.

Never infer:

```text
one destination consumed -> route complete
no currently known same-side liquidity -> route complete
```

## 8. H4/H1 state labels

Retain H4/H1 observations as context only:

```text
H4 authority / phase
H1 aligned / interrupt / unresolved
```

They may help describe risk/context but cannot silently override arrival/delivery Grammar.

In particular:

```text
H1_REALIGN != continuation proof
H1_INTERRUPT != counter-route proof
H4 macro flip != route-completion proof
```

## 9. No hidden thresholds

This authority does not contain:

- a required number of same-side arrivals;
- a minimum route duration;
- a maximum response duration;
- a cooldown;
- a retry limit;
- a minimum R;
- a fixed no-chase distance;
- an ATR gate;
- a forced direction balance;
- a trade quota.

If later research proposes one, it must be explicit, preregistered on consumed data, and must survive counterexample review before authority changes.

## 10. Trading extraction boundary

The semantic model is now compact enough to allow trading research, but trading policy is not frozen.

Permitted current questions:

```text
How should a Child enter during PRIMARY_ACTIVE?
What structural Hard SL contains ordinary route noise without becoming too wide?
How should nearest-known and newly-opened destinations affect TP/journey management?
Does CHALLENGER_EARNED justify different entry handling?
What happens to an already-open Child when the route becomes CHALLENGED?
```

Not permitted as silent assumptions:

```text
PRIMARY_ACTIVE -> always enter
CHALLENGED -> always exit
CHALLENGER_EARNED -> guaranteed reversal
POI touch -> entry
minimum-R filtering
```

## 11. Causal / execution authority

All runtime work remains subject to:

- authoritative raw M1;
- exact object IDs and known-at timing;
- dual clocks;
- deterministic event ordering;
- Hard-SL first-touch handling;
- no future-selected endpoint;
- no hindsight rescue.

Read the active causal/tooling documents after this semantic authority.
