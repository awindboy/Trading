# V13 LTF route q75/q50 research receipt

Date: `2026-09-29`
Status: `CONSUMED DEVELOPMENT / SESSION RESULT PRESERVED / RECONSTRUCTION A ACTUAL-TICK VERIFIED`

## Executive result

The research did not find a universal price-action filter that simply deletes
bad HA trades. Its useful result was architectural:

- keep H4 standard HA as the low-noise Parent/Journey container;
- leave Child #1 alone;
- replace repeated H4 add-ons with location-aware M30/M15 pullback Children;
- model **delivery of a first strategic destination**, not the next candle or
  eventual total profit;
- use delivery as proof, not TP;
- after delivery, use a separate q50 repair decision for the first damaged
  M30 correction.

## Research lineage and decisions

| Branch | Main finding | Decision |
| --- | --- | --- |
| HA morphology/FAST-STD-SLOW/MTF | HA contains transition information beyond color, but warning states also occur inside valuable Journeys | observation only |
| HA-7/8 admission and economic ML | modest ranking, insufficient separation of repetitive losses from valuable continuation | rejected as primary solution |
| HA-9 proof/lock/one-H4 timeout | idealized losses `2,427 -> 1,685`, WR `37.08% -> 56.07%`, DD `3,756.99 -> 1,283.65`, but net tail reduced | breakthrough historical candidate |
| SA-1 clean H4 continuation | actual ticks: 1,783 trades, `+$2,791.87`, PF `1.215`, DD `$971.77`; add-ons had 69.03% WR but payoff only `0.62` | actual-tick reference, not final architecture |
| Timeout extension, H1/FAST/STD exits, re-arm, runner split | either failed post-cutoff checks or traded more losses for a right tail | rejected; do not relabel |
| Broad M30/M15 POI pullback lane | improved payoff, but too many ordinary losses and worse block smoothness | useful new Child clock, incomplete |
| M30 rebreak staged funding K1/K2 | larger 2024-26 dollars, but failed 2022/23 stress and increased exposure/DD | rejected |
| True all-M30 correction envelope | 7,389 episodes / 2,435 breaches; worse than POI-linked envelope (`+$1,508`, PF `1.115` versus `+$3,319`, PF `1.210`) | rejected; POI link is useful noise filter |
| Healthy versus already-breached envelope | healthy/no-prior: 1,628, `+$3,728`, PF `1.289`; breached: 411, `-$409`, PF `0.862`; WR nearly equal, payoff differed | important payoff-state evidence; no hard veto because 2023 failed |
| Breach-rescue Ridge q75 | pooled `+$356`, 97.4th percentile of random same-count control; promising but not standalone authority | retained only as supporting evidence |
| ATR180/liquidity normalization | era volatility changed sharply; normalization reduced exposure/DD but did not solve intermittency | coordinate/risk scaling only |
| Simple nearest liquidity, target count, H1 label, route gap | no stable monotonic relationship | rejected |
| First strategic-destination delivery | not reached: 976, `-$9,093`, PF `0.11`; reached: 811, `+$13,026`, PF `4.75` | strongest explanatory state; confirmation, not TP |
| TP at first destination | collapsed payoff and net | rejected |
| Add at first/second/third destination | worked in 2024-26, failed 2022/23 | rejected |
| Post-delivery tail prediction | AUC about `0.47..0.54` | random; rejected |
| Destination-delivery prediction | combined LTF state + route AUC: 2023 `.724`, 2024 `.761`, 2025 `.744`, 2026 `.737` | stable enough for admission research |
| Hurdle EV | probability alone was not money; combining probability, remaining room and historical failure loss improved selection | retained |
| q75 2x sizing | raised DD without sufficient quality gain | rejected; admission only |
| Child #1 early-exit/route-failure ML | Child #1 net/payoff collapsed; rescue AUC random | Child #1 stays unchanged |

## Final session-reported candidate

These figures were reported in the interrupted research session. They have not
been independently regenerated from a saved final policy ledger in this
workspace and therefore are not actual-tick authority.

```text
period                         2024-01-01..2026-08-28 20:00
combined trades               1,477
wins / losses                 548 / 929
non-flat WR                   37.10%
net                           +$4,173.10
PF                            1.289
average winner / loser        +$33.95 / -$15.53
payoff                        2.19
expectancy                    +$2.83 per trade
realized trade-sequence DD    $916.92
maximum loss streak           13

q75 LTF lane alone            512 trades
                               +$2,310.59 / PF 1.59
                               payoff 2.15 / DD $363.51 / streak 8

10-trade blocks               median +$9.60 / 54.7% positive
25-trade blocks               median +$34.11 / 62.0% positive
50-trade median               +$74.21
100-trade median              +$188.51
high-WR negative blocks       about 0.14% at 25; approximately zero at 50/100
```

Floating exposure remained a cost: about `$1,792` floating DD and six maximum
concurrent positions versus SA-1 about `$1,325` and three. Net/floating-DD was
reported as `2.33` versus SA-1 `2.11`.

The 2023 stress slice was only about `+$143`, PF `1.086`, payoff `2.13`, with
negative 25/50-trade medians. It is not independent validation and prevents a
claim of uniformly smooth performance.

## What is actually saved now

- earlier LTF datasets, OOF files, hurdle experiments and variant summaries;
- the complete research conversation result summarized above;
- the frozen action contract;
- Reconstruction A source, OOF outputs, q75/q50 thresholds and manifests;
- hashed 512-LTF and 1,477-combined event ledgers;
- a compiled policy-ledger replay EA (`0 errors, 0 warnings`);
- 2,954/2,954 ordered actual-tick Journal parity and parsed per-event economics.

The original interrupted session's exact event-by-event q50 ledger and fitted
fold artifacts remain absent. Reconstruction A must therefore remain distinct
from the session-reported result even though it recovered the same 512 LTF and
1,477 combined trade counts.

Reconstruction A actual ticks produced `+$4,461.37`, PF `1.301`, 554 wins / 922
losses / 1 flat, realized DD `$1,018.77`, exact-tick equity DD `$1,787.36` and
maximum loss streak 15. See
`V13_LTF_ROUTE_Q75_Q50_ACTUAL_TICK_REPLAY_RECEIPT_20260929.md` for the parity,
year, block, tail and SA-1 comparison. It is not promoted because its payoff
improves while ordinary loss frequency, win rate, streak and exposure are worse
than SA-1.
