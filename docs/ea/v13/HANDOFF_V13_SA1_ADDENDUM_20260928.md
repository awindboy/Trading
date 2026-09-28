# V13 handoff addendum — State-Anatomy / SA-1

Date: `2026-09-28`
Applies after GitHub `main` `652dcd070206f04a51eb5a7451a253393b60ee03`.

## Resume point

The old HA-9 timeout/re-arm/runner branch remains closed. Do not reopen it under a new name.

A separate State-Anatomy pass was completed because the previous branch moved from descriptive states to action tests before fully comparing winners and timeout losses at identical causal checkpoints. That pass found a strong directional-acceptance axis and led to one new pre-entry mechanism: `SA-1 Clean Continuation Admission`.

## Current candidate stack

```text
Baseline-0: frozen comparator
HA-9:      retained add-on management mechanism
SA-1:      new add-on admission overlay, tester candidate only
```

SA-1 does **not** replace HA-9 management. It decides whether a same-color add-on signal may instantiate a Child; if admitted, HA-9 takes over.

## Exact SA-1 gate

```text
raw close favorable vs signal-H4 HA close
AND opposite H4 HA wick absent
AND all observed completed H1 HA inside the signal H4 aligned with Journey
```

No thresholds beyond strict/equality price semantics. No Delta condition.

## Evidence to remember

- Actual filtered diagnostic: 1,734 -> 866 all losses, $3,067.50 -> $2,904.62 net, DD $1,313.10 -> $862.38.
- Actual add-ons: 1,100 -> 232 losses, $1,204.47 -> $1,041.59 net, PF 1.099 -> 1.469.
- Idealized max-10-successful replay: 1,685 -> 859 losses, net 3,946.06 -> 3,423.29, DD 1,283.65 -> 948.70.
- The rule was discovered on consumed history. These numbers authorize a tester candidate, not production use.

## Immediate next work

1. Compile `mt5/experts/V13SA1CleanContinuationEA.mq5` in MetaEditor.
2. Run the canonical GOLD# `Every tick based on real ticks` test with fixed 0.01 lots and verbose Journal.
3. Parse `V13SA1_EVENT|ADMISSION` and verify the three gate components exactly against Python.
4. Verify admitted Children keep HA-9 proof/timeout/lock event parity.
5. Verify skipped signal H4s do not consume successful Child count and later same-color H4s can fill later successful slots causally.
6. Produce official actual-tick SA-1 economics and the same ordinary-equity metrics used by V13.
7. Do not change the gate if the first tester result is disappointing; first explain execution/event divergence.

## Do not resume with

- additional thresholds on raw-close distance, wick size or Delta;
- `Delta non-contract` as a fourth gate;
- side/year/Child-ordinal exceptions;
- T1 delayed-entry rescue, timeout extension, runner conversion or re-arm;
- HASTOC/ADX/volume/ML stack;
- sizing before tester parity.
