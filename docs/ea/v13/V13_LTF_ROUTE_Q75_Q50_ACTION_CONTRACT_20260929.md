# V13 LTF Route q75/q50 action contract

Date: `2026-09-29`
Status: `RESEARCH CANDIDATE / POLICY-REPLAY IMPLEMENTED / EMBEDDED MODEL NOT FROZEN / NO PRODUCTION AUTHORITY`

## 1. Why this branch exists

HA-9 and SA-1 improved the ordinary add-on stream, but they still treated each
same-color H4 as a new Child opportunity. The LTF branch instead asks whether a
still-alive H4 PHA has produced a causally observable pullback at a useful price
and whether a reachable strategic destination remains ahead.

This is not a CRT strategy bolted onto V13. CRT/liquidity language contributed
one transferable idea: **forward route and delivery matter more than a named
three-candle pattern**.

## 2. Frozen architecture

### Child #1

Child #1 remains the frozen Baseline-0 H4 standard-HA Journey seed. No LTF model
may veto, resize or prematurely exit it in this candidate.

### Replacement LTF Child lane

SA-1/HA-9 H4 add-ons are replaced, not overlaid, by this lane:

1. completed H4 standard HA PHA is still alive;
2. a raw M30 correction/pullback is known from completed bars;
3. the pullback interacts with a fresh causal M15 FVG or OB object;
4. only state known at the next executable timestamp is used;
5. active, causally confirmed M30/H1 swing destinations ahead are assembled
   into a forward route topology;
6. a chronological model estimates probability that the first strategic
   destination is delivered before structural failure;
7. hurdle EV combines that probability with remaining ATR-normalized room and
   prior no-delivery loss magnitude;
8. entry is admitted only above the **strict-prior OOF q75** hurdle-EV boundary;
9. admitted entries use one fixed `0.01` lot. q75 is admission, not 2x/3x
   sizing authority.

The fixed q75 rank was chosen before the final comparison. Post-hoc q65/q70
results may not replace it on this consumed sample.

## 3. Runtime state machine

The first strategic destination is a proof/delivery event, not a TP.

```text
ENTRY admitted by prior-OOF q75 hurdle EV
  -> hold through route toward first strategic destination
  -> if destination is not delivered, use the frozen policy failure exit
  -> if delivered, keep the runner
  -> observe the first completed-M30 correction after delivery
  -> if the prior correction envelope is not breached, continue
  -> if breached, evaluate strict-prior OOF repair score q50
       below q50: protective exit
       at/above q50: allow one repair attempt
         favorable rebreak: runner continues
         structural failure: exit
```

The q50 repair branch is permission to wait for one repair, not an additional
entry or size increase.

## 4. Causal/model requirements

- Pivot/swing destinations become visible only after their right-side
  confirmation bars complete.
- A destination already consumed before the decision timestamp is inactive.
- Model training rows must have labels fully resolved before the test fold.
- Test-year thresholds come only from earlier OOF scores.
- ATR180 is a coordinate/risk-normalization input, not a regime veto.
- The fixed development period `2022-01-03..2026-08-28 20:00` is consumed.
- No year/side exception, fitted cooldown, fitted absolute score, q65/q70 rescue,
  or post-hoc position-size multiplier is authorized.

## 5. Execution artifact boundary

`mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5` replays a frozen action
ledger. It deliberately does not embed or retrain ML. The ledger must contain:

```text
event_id,action_time,action_order,action,direction,volume,policy_lane,reason,expected_price
```

For equal timestamps `EXIT` must sort before `ENTRY`. Server time is the ledger
clock. One event id must have exactly one ENTRY and one EXIT.

The EA retries transient order failures, refuses expired-entry backfill,
requires hedging mode and fixed `0.01` volume, and halts on permanent execution
or reconciliation failure. Journal records use `V13Q75_EVENT|`.

## 6. Authority limit and completed reconstruction

The interrupted session's exact q50 event ledger remains absent, so its reported
economics are development evidence and cannot be called reproduced.

Reconstruction A regenerated the declared architecture without fitting to the
old result, froze and hashed 1,477 events, and passed 2,954/2,954 ordered
actual-tick action parity. This validates Reconstruction A execution only. It
was not promoted because its better payoff/net came with worse loss frequency,
win rate, loss streak and exposure than SA-1. See the actual-tick replay receipt.

The replay EA remains a research harness. Embedded-model, production and
capital-sizing authority are not granted.
