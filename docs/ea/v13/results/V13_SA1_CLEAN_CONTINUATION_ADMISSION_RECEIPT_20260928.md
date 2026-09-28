# V13 SA-1 Clean Continuation Admission receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / ACTION CANDIDATE / FRESH ACTUAL-TICK TESTER RUN PENDING`
Base GitHub `main`: `652dcd070206f04a51eb5a7451a253393b60ee03`

## Candidate

Child #1 remains unchanged. An add-on is admitted only when the completed signal H4 has:

1. favorable raw-close acceptance versus its H4 HA close;
2. no opposite H4 HA wick;
3. no H1 HA opposition inside that signal H4.

After admission, HA-9 proof/timeout/breakout-lock management is unchanged.

## A. Actual HA-9 report diagnostic

This section filters the already reconstructed actual HA-9 Child ledger. It is valuable because it uses actual spread/execution P/L, but it is **not** the official SA-1 tester result: skipped HA-9 entries were already executed in the source report, so later opportunities cannot be replayed exactly with successful-entry backfill.

| Metric | Actual HA-9 | SA-1 filtered diagnostic |
| --- | ---: | ---: |
| Children | 3858 | **1719** |
| Wins | 2118 | 852 |
| Losses | 1734 | **866** |
| Flats | 6 | 1 |
| Net USD | 3067.50 | **2904.62** |
| PF | 1.135 | **1.228** |
| Realized DD | 1313.10 | **862.38** |
| Max loss streak | 14 | **10** |

All-Child losses fall by `868` (`50.1%`) while diagnostic net retains `94.7%` of actual HA-9 net.

### Add-ons only

| Metric | HA-9 add-ons | SA-1 admitted add-ons |
| --- | ---: | ---: |
| N | 2893 | **754** |
| Wins | 1787 | 521 |
| Losses | 1100 | **232** |
| Net USD | 1204.47 | **1041.59** |
| PF | 1.099 | **1.469** |
| DD | 693.33 | **140.04** |
| Max loss streak | 9 | **6** |

Add-on losses fall `78.9%` while retaining `86.5%` of the actual HA-9 add-on net.

## B. Selection sanity check

A 3,000-draw stratified random-selection diagnostic preserved year, side and Child-ordinal counts. Random selections of the same size averaged about `283.5` losses, `468.6` wins and `$365` net versus SA-1's `232` losses, `521` wins and `$1041.59` net. No random draw matched or beat the SA-1 loss or win count; about `3.4%` beat its net.

This does not prove out-of-sample edge, but it rejects the explanation that the result is merely caused by selecting fewer trades at the same year/side/ordinal composition.

## C. Interaction evidence

`raw-close acceptance + no opposite wick` alone selected 1033 add-ons at `$830.39` and PF `1.244`.

Within that population, requiring **no H1 opposition** reduced the set to 754 trades and raised net to `$1041.59` / PF `1.469`. The excluded H1-opposed subset was net negative in the actual diagnostic. This is the key State-Anatomy interaction: an H4 that looks favorable externally is not equivalent to an H4 whose internal H1 path stayed aligned throughout.

Delta contraction is explicitly **not** part of SA-1. Inside the final SA-1 population, the contracted subset remained profitable and had higher PF than the non-contracted subset, so adding `delta non-contract` would be an unsupported extra filter.

## D. Year and side diagnostics for admitted add-ons

| Slice | N | W | L | Net | PF |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | 283 | 189 | 93 | 25.70 | 1.053 |
| 2025 | 294 | 209 | 85 | 337.19 | 1.409 |
| 2026 | 177 | 123 | 54 | 678.70 | 1.743 |
| LONG | 480 | 340 | 139 | 352.56 | 1.293 |
| SHORT | 274 | 181 | 93 | 689.03 | 1.678 |

No side/year exception is authorized.

## E. Idealized M1 replay with max-10-successful-entry backfill

Unlike the actual filtered ledger, the idealized replay can correctly let later same-color signals become new opportunities after an SA-1 rejection.

| Metric | HA-9 idealized | SA-1 idealized |
| --- | ---: | ---: |
| Children | 3858 | **1783** |
| Wins | 2151 | 912 |
| Losses | 1685 | **859** |
| Net | 3946.06 | **3423.29** |
| PF | 1.176 | **1.269** |
| DD | 1283.65 | **948.70** |
| Max loss streak | 14 | **12** |

Idealized losses fall `49.0%`, net retention is `86.8%`, and all three year slices remain positive:

```text
2024 SA-1 +209.28
2025 SA-1 +1712.51
2026 SA-1 +1501.50
```

## F. Ordinary block / tail robustness on actual diagnostic

Actual filtered SA-1 improves typical block quality. For example 25-trade positive-block share moves from `52.6%` to `58.8%`, and median 25-trade block from `$7.06` to `$24.01`.

After removing the 10 most profitable Journeys, actual HA-9 is `$-845.68` versus SA-1 diagnostic `$-79.39`. Both are negative under actual execution, but SA-1 is substantially less dependent on the largest Journeys in this diagnostic.

## G. Limitations and decision

- The three-condition SA-1 rule was discovered on consumed 2024-2026 development history.
- The available `20260926.log` is not the HA-9 proof/lock Journal and therefore does not establish exact legacy event parity.
- Actual filtered economics do not reproduce skipped-entry backfill. Fresh tester execution is mandatory.
- MetaEditor compile proof is still missing.

**Decision:** promote SA-1 only to **fresh actual-tick tester candidate**. Freeze the three admission conditions. Do not optimize extra thresholds, Delta filters, side/year exceptions, Child ordinals, sizing, proof duration or lock distance before the tester receipt.
