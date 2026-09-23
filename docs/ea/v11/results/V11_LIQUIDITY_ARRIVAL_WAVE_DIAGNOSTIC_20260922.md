# V11 liquidity-arrival Wave diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / LIQUIDITY SCALE IS DESCRIPTIVE / NO ADMISSION GATE / NO TRADE AUTHORITY`

## Question

Instead of asking whether one HA candle resembles another, can V11 explain what pre-existing liquidity the completed participation H4 reached, whether a farther route remained, and whether M5 settlement accepted or rejected that consumed boundary?

The fixed comparison was:

1. outer H4/FAST-HA shell;
2. outer shell plus causal H1/H4 arrival and remaining-destination topology;
3. layer 2 plus Wave settlement relative to the consumed liquidity boundary.

## Causal reconstruction

- raw M1 SHA-256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- R3 universe SHA-256: `f352a99c746752ca259da33dbdaee9d8f0cb874bd01cf520a487fe1bdbf82609`;
- MT5 R7G event export SHA-256: `c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7`;
- H1/H4 liquidity object: fixed 2-left/2-right completed swing;
- object birth: only after both right bars completed;
- consumption: first strict raw-M1 penetration;
- topology snapshot: before the decision's first available M1 is revealed;
- Wave boundary: terminal same-side H4 boundary when present, otherwise terminal same-side H1 boundary.

The chronological replay created 9,397 objects, recorded 8,959 first consumptions, and matched all 1,649 resolved positive-weight R7G Children. There were zero direction, stage, or FAST-HA direction mismatches. Of 1,649 snapshots, 220 midnight decisions used the first available 01:00-01:02 M1 before revealing its price; this equals the recorded entry time and does not invent a closed-market price.

## Main result

Same-side H4 arrival was a meaningful descriptive distinction:

| Period | H4 arrival n | H4 arrival stops | Stop rate | No H4 arrival n | No H4 arrival stops | Stop rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pooled | 367 | 30 | 8.2% | 1,282 | 202 | 15.8% |
| 2025 | 188 | 16 | 8.5% | 678 | 97 | 14.3% |
| 2026 | 134 | 9 | 6.7% | 413 | 70 | 16.9% |

The post-2024 relation appeared in both directions, but 2024 SHORT was an exception. This is therefore a useful semantic coordinate, not proof of a stable rule.

Wave settlement did not explain the H4-arrival advantage. Within H4 arrivals, pooled stop rates were `4.9%` after accepted settlement, `8.8%` after returned settlement, and `9.5%` after split settlement: the whole H4-arrival group was already low-risk. H1-only returned settlement was worse descriptively (`23.4%` stops versus `9.6%` accepted), but the split was unstable across year and direction.

Fixed temporal model comparisons confirmed the limitation:

| Test | Outer shell | + liquidity topology | + liquidity-relative Wave |
| --- | ---: | ---: | ---: |
| 2025 STOP AUC | 0.697 | 0.702 | 0.681 |
| 2026 STOP AUC | 0.772 | 0.771 | 0.771 |

Liquidity topology added only `+0.005` AUC in 2025 and none in 2026. Adding the Wave coordinates reduced 2025 discrimination and did not improve 2026.

## Economic constraint

Using H4 arrival alone as admission would cut stop frequency, but it would also retain only 188/866 Children in 2025 and 134/547 in 2026. It retained just `28.0%` and `18.1%` of baseline weighted R, and `23.4%` and `19.9%` of L6+ positive weighted R. It deletes the right tail that pays for V10.

The fixed q90 topology-model tail changed weighted R by `+15.48R` in 2025 and `-6.45R` in 2026. Adding liquidity-relative Wave changed it by `-11.71R` and `-5.90R`. These tails are diagnostics, not candidate thresholds.

## Decision

- Keep the distinction between H1 arrival, H4 arrival, and no same-side arrival as observation semantics.
- Do not admit only H4-arrival Children; the right-tail deletion is unacceptable.
- Do not use accepted/returned/split Wave settlement as a broad entry veto.
- Do not rescan swing widths, distance ratios, KDE bandwidths, score thresholds, or direction exclusions on consumed history to rescue this result.
- The next liquidity hypothesis must represent the arrival as an event process—source age, multiple-level sequence, farther same-side H4 route, opposing route, and departure/return chronology—rather than another static scalar gate. It still requires a future-only efficacy boundary.

## Reproduction

- script: `research/v11/analyze_v11_liquidity_arrival_wave.py`;
- script SHA-256: `a00446b3871ec442f2a3131cae05b16b86ecb49d28633b8151840b9196da3c66`;
- script size: `34,876` bytes;
- local output: ignored `output/v11_liquidity_arrival_wave_20260922/`;
- child-ledger SHA-256: `0dcb4463892de74cee9d9bb45190a855a4f8ab507de780d084685be2f1e64c28`;
- model-comparison SHA-256: `58fbc9b59a69878266e71ac713616d42871d21593a07e565524a7fde0d06178a`;
- H1/H4 liquidity, completed H4/M5, ATR180, and FAST HA were all rebuilt in the same chronological M1 reveal; Python compile and causal ledger audits passed.
