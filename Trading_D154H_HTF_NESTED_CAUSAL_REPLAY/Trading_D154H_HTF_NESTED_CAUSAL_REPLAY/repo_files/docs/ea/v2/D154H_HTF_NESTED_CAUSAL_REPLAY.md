# D-154H HTF Nested Causal Replay

Status: `RESEARCH / SHADOW-ONLY`  
Date: `2026-08-22`
Target build: `2.08R0L8 / V2_D154H_HTF_NESTED_CAUSAL_REPLAY`

## 1. Research question

D-154H does not introduce another HTF filter. It asks a more basic representation question:

> What ordered H1/M30 structural state-transition path actually led from PLAN to each Fill?

The current EA compresses HTF context into current trend/owner/protected/external snapshots. D-154H preserves the event history that produced those snapshots.

## 2. Population and unit

```text
actual filled EXTERNAL_CONTINUATION only
unit = actual execution Fill
merged contributors remain contributors to one Fill
```

Primary outcome reference remains exact D151 `PLUS_1R` vs `SL_FIRST`; tester-end unresolved cases remain `RIGHT_CENSORED`.

## 3. Causal observation window

For every contributor that reaches an actual Fill, replay only causally observed structure from:

```text
contributor PLAN
-> Root contact
-> accepted M1 sweep
-> accepted M1 CHoCH
-> master pending acceptance
-> actual Fill
```

No event after Fill may be used to characterize Entry quality.

## 4. HTF event ledger

D-154H records every causally observed H1/M30:

```text
INITIAL_BOS
BOS
PROTECTED_BREAK
```

Each event receives a monotonic research sequence number. Same-timestamp processing order remains the strategy's frozen `H1 -> M30` order.

The event row records current H1/M30 owner, protected/external references and the deterministic post-event interpretation. A `PROTECTED_BREAK` callback occurs before `EnterTransition`, so D-154H explicitly records its inferred post-event state as `TRANSITION / owner=NA`; it does not backfill future bars.

## 5. Stage anchors

Research-only snapshots are emitted at:

```text
PLAN
ROOT_CONTACT
SWEEP
CHOCH
PENDING
FILL
```

Each stage stores the current HTF event sequence number. The analyzer can therefore reconstruct exact ordered events in every stage interval without using elapsed-time thresholds.

## 6. Discovery governance

D-154H is a sequence census, not a gate test.

Discovery: `GOLD23 2023-01-01 .. 2023-12-21` after non-interference parity.

Allowed discovery outputs:

- frequent exact H1/M30 transition signatures;
- where in PLAN->contact->sweep->CHOCH->pending->Fill the transitions occur;
- outcome counts for those signatures;
- LONG/SHORT and active-map/source-TF descriptive breakdowns.

Forbidden in D-154H:

- threshold fitting;
- quality score construction;
- automatic promotion of a sequence discovered on GOLD23;
- changing Entry/SL/TP/order/sizing/SP/EM;
- collapsing a discovered sequence into a veto before an independently preregistered validation phase.

If a coherent causal sequence family emerges, freeze its definition in a later phase before testing GOLD24/GOLD25/BTCUSD25/SILVER25/CADJPY25. If no coherent family emerges, do not mine increasingly specific signatures.

## 7. Test order

```text
1. compile 2.08R0L8 with 0 errors
2. GOLD23 Q1 D154H OFF/ON parity
3. comparator PASS
4. GOLD23 clean discovery through 2023-12-21
5. summarize replay integrity and sequence census
6. formulate at most a small causal hypothesis set for a new validation phase
```
