# V8 Development Handoff

Last updated: `2026-09-04`  
Current phase: `GOLD P15 -> ATR GRID -> STATIC SIZING / SIMPLE DEEP ACTION COMPLETE -> NEXT PAYOFF TRANSFORMATION`  
Production authority: `NONE`  
Market: `GOLD# ONLY`  
Untouched reserve: `GOLD# 2021`  
Expected Git HEAD before applying this package: `ba28a16be6751178549eab5a623f14b5ded38778`

## 1. Resume order

On the next session:

1. refresh Git HEAD;
2. read `AGENTS_V8.md`;
3. read this file;
4. read `RESEARCH_STATE_V8.md`;
5. read `V8_GRID_SIZING_DEEP_ACTION_RESULT_20260904.md`;
6. read `DECISIONS_V8_GRID_SIZING_DEEP_ACTION_ADDENDUM_20260904.md`;
7. use older ATR-grid documents only for preserved background/history.

Do not immediately rerun the completed sizing or HOLD/REDUCE/EXIT/FLIP tournament.

## 2. Population authority for the latest exact-execution study

The latest exact-execution study uses reproducible old P0 2024 fresh75 `N=648`.

Prior synchronized docs contained `653`. The user explained that 653 had been promoted after old P0 failed reproduction in the previous session; old P0 has now been reproduced with near-exact P15 parity, so the user explicitly authorized proceeding with 648.

This mismatch must remain documented. Do not silently mix the populations.

## 3. Data authority

- authoritative M1 source SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- 2024 exact tick = current execution-development data;
- known active-coverage gaps exist and are censored when M1 shows trading through the missing tick interval;
- 2025 exact tick is incomplete/sparse and must be treated as unavailable;
- 2025 M1 is descriptive only;
- GOLD# 2021 remains locked.

## 4. Preserved upstream V8 conclusions

- P15 predicts near-term movement opportunity better than direction.
- ACCEPTANCE is structural, not an automatic trade permission.
- High-Q is sparse positive continuation evidence.
- t10 positive continuation state is too sparse to solve the broad campaign problem.
- generic direction classifiers, reveal FOLLOW/FADE, every-M1 EV, micro first-touch, entry-time straddles, stop-and-reverse and continuous trend-follow remain failed/downgraded branches.
- exact tick and Bid/Ask are mandatory for grid economics.

## 5. Latest static sizing result

Primary execution-control geometry:

- direction = fixed causal 30m momentum;
- entries = `0 / -0.4S / -0.8S`;
- boundary = `-1.2S`;
- sizing candidates = fixed/decreasing/martingale;
- +1S immediate exit used only to isolate sizing because the historical exact runner-protection stop was not preserved sufficiently for parity.

2024 exact tick completed-campaign means:

- `1:1:1`: `+$0.053`, PF ~1.015;
- `1:0.5:0.25`: `-$0.307`;
- `1:0.5:0.5`: `-$0.237`;
- `1:0.25:0.25`: `-$0.515`;
- `1:2:4`: `-$0.331`, worst ~`-$94.23`.

Decision:

> Fixed remains the best tested static control. No alternative sizing is promoted.

## 6. Why decreasing sizing failed

It reduced individual hard-loss magnitude but moved weighted BE farther away and converted too many former rescues into hard losses.

An equal-risk wider-boundary extension was also checked. Pairwise complete-event economics still favored fixed, while wider boundaries risk multi-hour drift.

Do not rescue decreasing size by further boundary tuning on 2024.

## 7. Why martingale failed

It pulled BE closer and increased rescues, but the remaining hard losses became too large.

Do not deepen or tune martingale from this sample.

## 8. Deep-state action result

Third fill / ~-0.8S remains informative but is not automatic evidence the initial direction is wrong enough to abandon.

On common action-complete deep events:

- HOLD recovered about `+$5.02/event` from current mark-to-market state;
- REDUCE_LATEST recovered about `+$1.28`;
- REDUCE_HALF_ALL about `+$2.51`;
- EXIT gives 0 future Q by definition;
- simple FLIP about `-$1.39`.

Unconditional HOLD was best.

## 9. Five-minute model correction

A first 5-minute model accidentally allowed xmin/xmax to keep updating after the decision boundary, producing false ~0.98 AUC. It was invalidated immediately.

Corrected causal discrimination was only moderate and expanding-quarter action value was unstable/negative.

Never reuse the invalid run.

## 10. Adverse thresholds and hedge

Automatic actions at -0.9/-1.0/-1.1S all worsened mean dollar EV versus HOLD.

A single-use one-unit opposite hedge at -1.0S, closed at -1.2S or -0.8S, had small positive ideal zero-spread value but actual Bid/Ask P/L `-$9.82` total.

Do not optimize this hedge from the same 2024 outcomes.

## 11. Central economic lesson

Deep-state hard-loss probability is not enough.

Even when EXIT helps most individual paths, the minority of sacrificed BE recoveries can carry more economic value than the saved hard-loss increments.

The next mechanism must improve the payoff shape, not merely improve hard-loss classification.

## 12. Immediate next research

Before opening outcomes, preregister a new state-contingent exposure-transformation mechanism that:

- preserves most normal-rotation BE-recovery value;
- creates materially stronger convex protection against genuine opposite continuation than the failed one-unit hedge;
- does not use martingale growth;
- remains near-term and causally aligned with P15;
- reports same-path zero-cost and actual Bid/Ask results separately.

Do not touch GOLD# 2021.

## 13. Production status

`NONE`
