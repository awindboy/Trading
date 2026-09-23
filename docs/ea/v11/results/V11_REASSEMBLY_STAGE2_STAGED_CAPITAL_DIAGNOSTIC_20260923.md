# V11 reassembly stage-2 staged-capital diagnostic

Date: `2026-09-23`

Status: `RETAINED ARCHITECTURE LEAD / CONSUMED DEVELOPMENT EVIDENCE / NO TRADE, RELEASE, SIZING, EA, OR PRODUCTION AUTHORITY`

## Question

Can V10's useful parts be reassembled so that participation and conviction are not the same decision?

The Stage-2 architecture gives every frozen R7G-intended FAST-k1 Child one initial risk unit. A Child whose R7G ceiling is three units may receive the remaining two units later. The original k1 Hard SL remains frozen, and any pre-release touch kills the extra capital. This preserves candidate participation while asking a narrower question: when has the Child earned the right to carry large size?

## Event-based release

The retained mechanism probe is not a price target or a predicted next HA. It is the first same-direction FAST continuation event:

```text
valid selected FAST k1
-> fund one unit immediately
-> keep original k1 Hard SL as causal guard
-> if the completed FAST run survives into k2
   and an M1 entry exists at the k2 decision
   release the remaining two-unit R7G ceiling
-> otherwise never release it
```

The k2 release was replayed from the verified raw M1 in one timestamp-ordered pass. Among `392` three-unit-ceiling Children, `315` had a same-direction FAST k2, `5` touched the original guard before release, `246` obtained a valid k2 entry, and `64` had no M1 entry within 15 minutes because the k2 decision occurred during a market closure. Those 64 were not moved post hoc to k3.

## Complete 2024-partial-2026 scorecard

| Metric | Immediate full R7G | 1 now + rest at FAST k2 |
| --- | ---: | ---: |
| selected Children / participation | 626 / 100% | 626 / 100% |
| Children touching Hard SL | 133 | 133 |
| conventional win rate | 35.78% | 35.62% |
| stopped loss-units | 279 | 183 |
| three-unit full-stop Children | 73 | 25 |
| adjacent three-unit stop pairs | 10 | 1 |
| combined R-units | +279.65R | +220.79R |
| combined-R retention | 100% | 78.95% |
| L6 positive-R retention | 100% | 73.97% |
| 1% unit-risk max drawdown | 26.74% | 19.92% |
| 1% unit-risk ending equity | 10.47x | 7.30x |
| equal-26.74%-DD unit risk | 1.000% | 1.387% |
| equal-DD ending equity | 10.47x | 14.17x |

The event release removed `34.4%` of stopped loss-units and `65.8%` of three-unit full stops without deleting a Child. At the same per-unit risk it earned less because much less capital was deployed. At the immediate policy's observed drawdown it supported more unit risk and a larger descriptive ending multiple.

The effect was directionally healthier than the fixed +180m probe. On 2025-2026, FAST-k2 staged capital produced `+8.24R` on SHORT and `+186.18R` on LONG; the fixed +180m staged probe produced `-3.05R` on SHORT and `+222.82R` on LONG. The k2 release reduced stopped units in both 2025 (`131 -> 83`) and partial 2026 (`107 -> 73`).

## What this does not solve

- It does not reduce the number of k1 Children touching Hard SL: `133` remains `133` because one unit always participates.
- It does not raise conventional win rate.
- It retains only `79.0%` of combined R and `74.0%` of L6 positive R at the original unit size.
- The equal-drawdown illustration is cost-free and sequential. It omits spread, slippage, concurrent portfolio exposure, margin, and the fact that V10 may already open an independent k2 Child.
- Market-closure release failures remain execution work, not permission to backfill a later release.
- All chronology is consumed development evidence. This is not independent validation.

## Decision

Stage 2 changes the retained V11 direction.

The promising object is no longer a binary admission filter. It is a **capital ladder**:

1. candidate creation grants only participation permission;
2. one unit preserves the right to join the journey;
3. the R7G ceiling is dormant capital;
4. a later causal event must earn release of that capital;
5. Child death, opposite authorization, and campaign exit remain separate authorities.

FAST k2 is retained as the first event-based comparator because it materially reduced full-size loss clustering and improved the consumed equal-drawdown frontier. It has no release or sizing authority yet.

Before any future validation, the architecture must be replayed as a complete portfolio so k2 top-ups cannot silently duplicate existing k2 Children. The next mechanism question is whether STD/SLOW persistence, R5 stop/survival axes, prior feedback, and Wave/process evidence improve the *release amount or release time* beyond the simple FAST-k2 event—not whether they can resurrect binary entry filtering.

## Reproduction

- script: `research/v11/analyze_v11_reassembly_stage2.py`;
- ignored output: `output/v11_reassembly_stage2_20260923/`;
- raw M1 SHA-256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`;
- Stage-1 policy ledger SHA-256: `c02b750c27e5f6c32ed9fe8b974f574861c2e80988f1a86fb664144173d48821`;
- Stage-2 summary SHA-256: `92dabcd12283bb6255002dcd001820e3586f5c5d4df1c1a331bc253dc4f127e6`;
- Stage-2 causal ledger SHA-256: `6b736a77ef9e136d0f29b2e18d6af353a702b2b44782768d039787e57526dcc2`.
