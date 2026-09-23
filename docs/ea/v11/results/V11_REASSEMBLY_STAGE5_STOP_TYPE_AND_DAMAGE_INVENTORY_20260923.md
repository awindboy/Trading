# V11 reassembly stage-5 stop-type and damage-inventory diagnostic

Date: `2026-09-23`

Status: `K1 TRANSITION LADDER RETAINED / DAMAGE-REPAIR SHADOW HYPOTHESIS / ONE-SLOT INTERPRETATION CORRECTED / CONSUMED DEVELOPMENT EVIDENCE / NO TRADE, RELEASE, SIZING, LEVERAGE, EA, OR PRODUCTION AUTHORITY`

## Corrected question

Stage 4 was initially judged mainly by total R retention. That was incomplete. Lower exposure must mechanically reduce both loss and profit. The relevant question is whether the removed capital was concentrated in back-and-forth or repeated loss, or whether the policy indiscriminately removed profitable mature-journey exposure.

## What the one-slot policy actually removed

Under new-Child priority, one shared journey slot blocked `550/970` extra-capital requests:

| Extra-capital requests | Requests | Stopped | Stop rate | Candidate R |
| --- | ---: | ---: | ---: | ---: |
| funded | 420 | 50 | 11.90% | +154.76R |
| blocked by occupied slot | 550 | 29 | 5.27% | +243.02R |

The blocked requests were safer and more profitable than the funded requests. Most were later-k additions inside an already persistent FAST run. Therefore the one-slot policy did **not** identify rotation. It reduced exposure by suppressing the mature journey additions that produce much of R7G's right tail. The fixed one-slot architecture remains rejected, now for a stronger selectivity reason rather than merely because only 59% of R remained.

## What the k1 capital ladder actually changed

The complete portfolio contains `20` adjacent pairs of three-unit full-stop Children under original R7G:

| Full-size stop-chain metric | Original R7G | k1 FAST-k2 ladder |
| --- | ---: | ---: |
| adjacent three-unit stop pairs | 20 | 9 |
| cross-run pairs | 13 | 2 |
| same-run pairs | 7 | 7 |
| alternating-direction pairs | 9 | 0 |
| pair where prior stop was already known | 14 | 3 |
| pair funded before prior stop became known | 6 | 6 |

This is the first evidence that distinguishes *which* loss burden was reduced. The k1 ladder retains all `1,649` resolved Children and `92.06%` of combined R while removing all adjacent alternating-direction full-size stop pairs and `11/13` cross-run full-size pairs. It does not predict a reversal. It recognizes that a newly flipped FAST run is not yet an established journey: k1 receives one participation unit and conviction capital appears only after same-direction continuation into k2.

Among `73` original three-unit k1 stops, the ladder prevents full-size exposure on `48`. Twenty belong to adjacent k1 stop chains and 28 are isolated. The effect is therefore transition-risk control, not a perfect chop classifier.

## Damage-responsive elastic inventory

A second fixed mechanism was tested only on additional capital:

```text
every selected Child -> one participation unit
k1 conviction capital -> causal FAST-k2 release comparator
known Hard SL in the same FAST run -> extra inventory DAMAGED
while damaged -> later Children still enter one unit; extra request is blocked
repair -> a post-damage Child remains alive into a later selected-Child decision
```

| Metric | k1 ladder | damage/repair inventory |
| --- | ---: | ---: |
| selected Children | 1,649 | 1,649 |
| Hard-SL Children | 232 | 232 |
| stopped loss-units | 390 | 384 |
| three-unit full stops | 79 | 76 |
| adjacent full-size stop pairs | 9 | 8 |
| combined R | +682.15R | +684.45R |
| original-R retention | 92.06% | 92.37% |
| 1%-unit max drawdown | 42.47% | 41.81% |
| equal-original-DD ending equity | 211.25x | 233.98x |

The mechanism blocks only `11/970` extra requests. Three stop (`27.27%`) versus `76/959` funded requests (`7.92%`). The blocked requests total `-2.30R`, so the policy both removes six stopped units and adds `2.30R` arithmetically.

This is selective in the intended direction, but the sample is too small and time-unstable for authority. All three blocked stops and the entire positive economic effect occur in 2025. In 2024 and partial 2026, the blocked requests are positive and no stop is prevented. SHORT R also worsens while LONG improves. The finding is a frozen shadow hypothesis only.

The same-timestamp conservative and permissive conventions produce identical results. No exact tick order was invented.

## Remaining loss structure

After damage/repair, eight adjacent full-size stop pairs remain:

- six were already simultaneously funded before the prior stop became known;
- two had a known prior stop;
- six are inside the same FAST run and two cross a run boundary.

Post-stop cooldown logic cannot prevent the six overlapping pairs causally. They require a separate concurrent-inventory question at funding time. This must not be disguised as a stronger post-stop threshold.

## Decision

1. Correct the Stage-4 interpretation: fixed one-slot capital is rejected because it is anti-selective, not simply because its absolute R is lower.
2. Retain the k1 one-unit-to-FAST-k2 ladder as the strongest structural lead for reducing full-size cross-run and alternating stop chains while preserving participation and most right-tail R.
3. Freeze same-run Hard-SL damage and one-surviving-Child repair as a future shadow hypothesis. Do not promote it from 11 consumed actions.
4. Keep overlapping pre-stop pairs as a separate open problem. A post-stop rule cannot solve risk that was already committed.

## Reproduction

- script: `research/v11/analyze_v11_reassembly_stage5_damage_inventory.py`;
- ignored output: `output/v11_reassembly_stage5_20260923/`;
- summary SHA-256: `2f7e27c36cb920662315ced89bdf2d8fbf2dfbe7a526949dce317b13f38b2e2d`;
- request-selectivity SHA-256: `f6aa9d35c897ed93a0ff1210f3719e33776c2ad181898a485a22ca9e8c567476`;
- allocation ledger SHA-256: `c014d0848271521cfb64db19219fb0f7807115cd84bcf4132a52c4eddae4e7ee`.
