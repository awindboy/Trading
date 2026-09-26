# V12 Phase 1U — multi-speed HA ownership result

Status: **complete and byte-reproduced / primary failed / no action authority**
Date: `2026-09-26`

## Question and method

Phase 1U tests the user's original multi-speed HA hypothesis without replacing
the H4 base with STD and without treating simple three-speed alignment as a
signal. FAST remains the event sensor. The most recent strictly prior H4 where
STD and SLOW agree defines chronological ownership memory. A new FAST direction
is then classified as a challenge, STD-led developing transfer, conflicted
challenge, confirmed transfer, or return/continuation with memory.

The official input is the verified `1,648,545`-row raw-M1 prefix, streamed
chronologically and rebuilt into `7,199` H4 states. It joins exactly to all
`2,839` economic-window V10 opportunities and the supplied MT5 ledger. The
comparison population is the exact `1,649` MT5 R7G-selected Children from
`2024-10-01` through `2026-08-28 12:00`. There are no missing states, duplicate
signals, FAST-direction mismatches, FAST-k mismatches, or post-cutoff reads.

The frozen primary retains a Child only when FAST is with remembered ownership
or STD and SLOW have both transferred to FAST. No threshold was fitted.

## Count-first result

| Policy | Children | Hard-SL Children | Positive Children | >=3R | >=5R | Win rate | Max stop streak | Weighted R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V10 control | 1,649 | 232 | 635 | 58 | 16 | 38.51% | 5 | 741.01R |
| Ownership authorized | 1,331 | 158 | 528 | 42 | 9 | 39.67% | 4 | 630.34R |
| k1 ownership only | 1,363 | 167 | 538 | 44 | 10 | 39.47% | 4 | 635.60R |

The primary prevents `74` Hard-SL Children (`31.90%`) and raises win rate by
`1.16` percentage points. It also lowers the maximum stop streak from five to
four, and Hard-SL rate improves on both sides and in 2024, 2025, and 2026.

But it removes `318` Children in total, including `107` positive Children,
`16` >=3R Children, and `7` of the `16` >=5R Children. Positive-Child retention
is only `83.15%`, >=3R retention `72.41%`, and >=5R retention `56.25%`. Each
lost positive Child buys only `0.69` avoided Hard SL. The primary therefore
passes five of nine frozen gates and fails the count-quality and tail gates.

This is materially better stop separation than a random-looking broad frequency
cut, but it is not selective enough to justify larger sizing.

## What the interaction actually explains

At k1, confirmed ownership transfer is the cleanest named state: `23 / 175`
Children stop (`13.14%`). However, the other states are not disposable:

- FAST-only challenge: `34 / 138` stops, but `49` positive and four >=5R
  Children;
- FAST with remembered ownership: `45 / 165` stops (`27.27%`), yet `62`
  positive and four >=5R Children;
- STD-led transfer: `26 / 130` stops and `44` positive Children;
- confirmed transfer: `23 / 175` stops and `65` positive Children, but only two
  >=5R Children.

The threshold-free transition decomposition supports the same conclusion. A
selected k1 where STD and SLOW move from both opposing the new FAST direction
to both joining it (`00_TO_11`) has `23 / 170` stops (`13.53%`). Yet persistent
opposition (`00_TO_00`) still contains four >=5R Children and `108.48R`.

Thus FAST/STD/SLOW are not redundant. Their sequence describes whether a FAST
flip is isolated or receives slower-clock acceptance. The failure is in using
that description as a binary admission gate: the large right tail begins before
slow ownership is safely observable, while a return to remembered ownership is
not automatically low risk.

## Decision

Do not restore FAST/STD/SLOW by requiring current alignment, waiting for both
slower speeds, or vetoing challenges. Do not increase size from the consumed
confirmed-transfer cell. Phase 1U shows a real multi-speed state mechanism but
rejects its frozen broad ownership gate.

Any later use should make the speeds perform different roles inside a separately
created Parent/Child hypothesis: FAST detects a local event, STD records whether
acceptance is developing, and SLOW records whether ownership has transferred.
That is a state machine, not three votes. It still requires untouched evidence
before it can influence admission or sizing.

Two independent ten-file packs are byte-identical. The regression tests and
pack validators pass. All observations are consumed development evidence; no
Phase-1U state, transition, policy, or count has veto, sizing, entry, EA,
production, or trade authority.
