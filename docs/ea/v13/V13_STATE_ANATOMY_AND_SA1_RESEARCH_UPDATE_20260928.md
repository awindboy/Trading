# V13 State-Anatomy and SA-1 research update

Date: `2026-09-28`
Base GitHub `main`: `652dcd070206f04a51eb5a7451a253393b60ee03`
Status: `HA-9 MANAGEMENT RETAINED / STATE-ANATOMY COMPLETE / SA-1 ADMISSION CANDIDATE IMPLEMENTED / FRESH TESTER VALIDATION NEXT`

## Why the branch was reopened

The earlier trade-mode program correctly rejected blanket timeout extension, generic H1/FAST/STD exits, re-arm gates and naive runner conversion. What it did **not** fully answer was the causal anatomy question: why one Child receives immediate directional acceptance while another consumes the same Journey without proof.

The reopened work therefore treated `<=1h winner`, `1-4h winner`, `4-8h loss` and longer survivors only as outcome labels, compared identical T0/T1/T2/T3/T4 timestamps, matched side/year/Child-age/volatility context, and inspected sequence/interactions rather than standalone indicators.

## Main State-Anatomy finding

The dominant post-entry axis is **actual directional progress**, not activity, HASTOC or MFE/MAE as isolated variables. H1/partial-H4 alignment and path sequence add secondary information. Initial opposition can be productive when it repairs; persistent opposition and deterioration are different states.

That result argues against another post-entry exit-horizon variant. Once T1 reveals a bad state, a loss trade already exists. To attack the active objective—loss count—the more direct lever is **pre-entry admission quality**.

## SA-1 mechanism

SA-1 therefore uses only information available at the completed signal H4 and asks whether that H4 is a clean internal continuation:

```text
favorable raw close versus H4 HA close
AND no opposite H4 HA wick
AND no opposite H1 HA color inside the signal H4
```

Child1 remains untouched. An admitted add-on then uses HA-9 unchanged.

## Evidence summary

Actual HA-9 report diagnostic:

```text
all losses: 1,734 -> 866 (-50.1%)
net:        $3,067.50 -> $2,904.62 (94.7% retained)
PF:         1.135 -> 1.228
DD:         $1,313.10 -> $862.38
loss streak 14 -> 10

add-on losses: 1,100 -> 232 (-78.9%)
add-on net:    $1,204.47 -> $1,041.59 (86.5% retained)
add-on PF:     1.099 -> 1.469
add-on DD:     $693.33 -> $140.04
```

Idealized causal M1 replay with rejected signals not consuming successful Child slots:

```text
losses: 1,685 -> 859 (-49.0%)
net:    3,946.06 -> 3,423.29 (86.8% retained)
PF:     1.176 -> 1.269
DD:     1,283.65 -> 948.70
streak: 14 -> 12
```

This agreement between the actual-ledger diagnostic and the causal max-10-successful replay is the reason an EA test is warranted.

## What is explicitly not part of SA-1

- Delta non-contraction: rejected as an extra gate because contracted cases inside the final clean state remained profitable.
- T1 delayed entry / runner conversion: not promoted; it introduced timing/lock-geometry and tail-concentration problems.
- T1 early exit: not promoted because it tends to shrink loss size rather than remove the losing trade and can turn winners into small losses.
- HASTOC, volume, ADX, ML, side/year exceptions, late-Child exceptions, cooldowns, minimum-R, ATR offsets and sizing: not authorized.

## Next authority-changing evidence

The next step is not another research feature search. Compile `V13SA1CleanContinuationEA.mq5`, run `Every tick based on real ticks`, preserve the full Journal, verify admission + HA-9 event parity, and produce the official actual-tick SA-1 receipt. Only after that may authority decide whether SA-1 replaces plain HA-9 as the active action candidate.
