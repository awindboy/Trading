# V11 HA-flip liquidity-reason diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / EVENT GRAMMAR RETAINED / NO TRADE AUTHORITY`

## Corrected question

The relevant question is not merely whether a completed PHA consumed liquidity. It is whether an opposite FAST HA has a causal role:

- response after arrival at meaningful liquidity;
- counterflow inside a journey that is still progressing toward farther liquidity;
- or rotation with no effective journey progress.

A distant active liquidity object is not enough to call a movement `in transit`. The journey must still have reduced distance to that object from the current FAST-run origin when the NHA completes.

## Fixed event grammar

At the PHA decision, before future price:

- `H4_ARRIVAL_WITH_FARTHER_ROUTE`: the PHA consumed same-side H4 liquidity and another H4 destination remains;
- `H4_ARRIVAL_NO_FARTHER_KNOWN`: H4 arrival with no farther known H4 destination;
- `TRANSIT_TO_H4`: no H4 arrival, but a same-side H4 destination remains;
- `LOCAL_H1_ONLY`: only local H1 arrival/route context exists;
- `NO_KNOWN_LIQUIDITY_CONTEXT`: no known same-side H1/H4 arrival or route.

After the immediate NHA completes, the outcome-only explanation is:

- `ARRIVAL_RESPONSE` after H4 arrival;
- `IN_TRANSIT_COUNTERFLOW` when the farther H4 route remains and the NHA close is still favorable relative to the original FAST-run open;
- `ROUTE_PRESENT_NO_NET_PROGRESS` when a target exists but journey-level progress has disappeared;
- `LOCAL_H1_ROTATION` or `UNANCHORED_ROTATION` otherwise.

The NHA close, run length, and next-run fields are answer-sheet fields. They do not exist at the earlier PHA decision. The explanation becomes causal input only for decisions made after that NHA has completed.

## Population

- full causal H4 opportunity universe: 6,770;
- immediate NHA/run-ending events: 2,066;
- matched R7G selected Children: 1,649;
- immediate NHA among selected Children: 366;
- short-run triplets using the existing V10 `run length <= 2` definition: 247 full-universe, 55 selected.

All liquidity objects, completed H4 bars, ATR180, and FAST HA observations were reconstructed from the chronological raw-M1 reveal. The source hashes remain those recorded by the preceding liquidity-arrival diagnostic.

## What the NHA events were

Across all 2,066 immediate NHA events:

| Explanation | Events | Prior-direction Child stop rate |
| --- | ---: | ---: |
| arrival response, farther route remains | 232 | 48.3% |
| arrival response, no farther known | 13 | 69.2% |
| in-transit counterflow | 1,016 | 29.0% |
| route present but no journey progress | 745 | 72.1% |
| local H1 rotation | 53 | 52.8% |
| unanchored rotation | 7 | 57.1% |

The selected R7G slice showed the same strong distinction: 178 in-transit NHA events had a `16.3%` prior-Child stop rate, while 128 route-present/no-progress events had a `56.3%` stop rate.

This establishes that `a target exists` is too weak. Journey-level progress relative to the run origin is the useful semantic distinction.

## What happened when the completed NHA became the new-direction k1 PHA

At that point the prior NHA explanation is causally known. The selected R7G k1 comparison was:

| Prior NHA explanation | k1 Children | Stops | Stop rate | Mean new run length | L6+ rate | Weighted R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| arrival response, farther route remains | 61 | 7 | 11.5% | 3.38 | 13.1% | +43.62R |
| in-transit counterflow | 277 | 72 | 26.0% | 3.14 | 12.3% | +26.62R |
| route present but no journey progress | 237 | 50 | 21.1% | 4.01 | 24.1% | +165.13R |
| local H1 rotation | 15 | 2 | 13.3% | 3.47 | 20.0% | +15.58R |

The economically dangerous interpretation is clear: when an NHA is only counterflow inside the still-progressing old journey, treating it as the start of a new opposite journey produces the highest k1 stop rate. But a broad veto still fails. Rejecting all 277 such selected k1 Children would prevent 72 stops while losing `26.62R`, retaining only `62.6%` of positive weighted R and `68.1%` of L6+ positive weighted R.

`ROUTE_PRESENT_NO_NET_PROGRESS` is not synonymous with chop. It contains both rotation and genuine transition; it produced the largest selected weighted R. Repeated short-run morphology alone did not cleanly separate those outcomes.

## Decision

- Retain the event grammar. It matches the intended distinction between arrival response, in-transit counterflow, and non-progressing rotation.
- Do not treat the mere existence of farther liquidity as a reason for HA continuation.
- Do not veto all k1 entries after in-transit NHA; the right-tail deletion remains too large.
- Do not call every no-progress NHA chop; genuine new journeys are mixed into that state.
- The next Wave hypothesis should be journey-relative: represent M5 settlement against the FAST-run origin and active H4 destination at the completed NHA, then ask whether the new direction has established independent settlement or remains counterflow. This must be frozen before new efficacy evidence.

## Reproduction

- liquidity/object builder: `research/v11/analyze_v11_liquidity_arrival_wave.py`;
- event diagnostic: `research/v11/analyze_v11_ha_flip_liquidity_reason.py`;
- event-diagnostic SHA-256: `a28a227f9d7cbce191454523bda5c09fe4b30d0be8b5fee5588f40820d96cc5c`;
- event-diagnostic size: `20,096` bytes;
- local output: ignored `output/v11_ha_flip_liquidity_reason_20260922/`;
- all-opportunity ledger SHA-256: `2258b4cd35f814bbd324d2a4207323ea89a555e3bbe15f2b8e313aa7168409a9`;
- k1-transfer summary SHA-256: `3c1d1c3ecf471b987f838aab7fed98169869b74511484c60255abece2e127c5c`;
- Python compile and row/hash assertions: passed.
