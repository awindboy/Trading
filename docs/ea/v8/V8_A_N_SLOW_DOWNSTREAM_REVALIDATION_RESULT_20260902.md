# V8-A-N-SLOW Downstream Revalidation Result — 2026-09-02

Status: `DEVELOPMENT EVIDENCE / PARTIAL REVALIDATION / NO PRODUCTION AUTHORITY`
Market: `GOLD#`
Probability population: `Slow-N H4 0.25ATR Phase-0 + Phase-2 robustness`
Source years: `2022-2026 consumed development evidence`
Reserve: `GOLD# 2021 untouched`

## 1. Purpose

The legacy M5-A-N target semantics were replaced because the target distance moved every M5.

This study asks:

> which old direction/context hypotheses survive when the movement population is rebuilt using a slowly updated H4-scale target?

Old rules were rerun before new discovery wherever their definitions remained reproducible.

## 2. Probability population

Phase-0:

```text
2024 fresh75 N653 / hit15 78.10%
2025 fresh75 N535 / hit15 78.50%
2026 fresh75 N321 / hit15 76.01%
```

Phase-2:

```text
2024 fresh75 N733 / hit15 80.22%
2025 fresh75 N579 / hit15 76.34%
2026 fresh75 N292 / hit15 78.08%
```

Exact event identity is only moderately stable (`Jaccard 57.22%`), so cross-phase survival is informative.

## 3. Failure table

| Method | Result | Verdict |
|---|---|---|
| Deterministic 7-voter | ~52% pooled in both phases | FAIL |
| M5 Stoch standalone | 50.8% P0 / 50.0% P2 pooled | FAIL |
| Market-question panel | 51.3% pooled | FAIL |
| Immediate pressure | 50.0% pooled | FAIL |
| Oscillator transition | 51.1% pooled | FAIL |
| M15 structure | 52.5% pooled | FAIL |
| H1 structure | 50.9% pooled | FAIL |
| H4 structure | 51.9% pooled | FAIL |
| HTF regime | 51.7% pooled | FAIL |
| Volatility transition | 51.7% pooled | FAIL |
| Location/liquidity | 50.4% pooled | FAIL |
| M1 tape proxy | 51.4% pooled | FAIL |
| M1 recent direction | 50.2% pooled | FAIL |
| M1 pressure | 52.3% pooled | FAIL |
| M1 Stoch | 50.0% pooled | FAIL |
| M1 EMA3/8 | 51.5% pooled | FAIL |
| Old asymmetric MTF state | 36.4 / 50.0 / 63.6% | FAIL / reversal |
| BB-A | 52.9% pooled | FAIL |
| BB-C | 54.9% pooled, 2026 33.3% | FAIL / reversal |
| BB-D | 53.1% pooled | FAIL |
| Generic tick panel on overlap | 51.7% pooled | FAIL |

These results are now compressed negative evidence. Do not continue them by threshold rescue.

## 4. BB-B survives

Frozen semantic state:

```text
prior residence = MIDDLE
trigger = OUTSIDE UPPER
absolute normalized SMA-gap path = AWAY
predict UP
```

Phase-0 n=5:

```text
58.82 / 76.47 / 69.23%
pooled N64 65.63%
```

Phase-2 n=5:

```text
64.71 / 66.67 / 63.64%
pooled N63 65.08%
```

Across n=3/5/8 and both phases, every annual cell remained above 50%.

Interpretation:

This is not evidence that “upper Bollinger breakout is generally bullish.” The symmetric lower-side continuation did not establish a matching rule in legacy research.

The retained semantic hypothesis is narrower:

> after middle residence, a Slow-N high-movement trigger that escapes above the upper band while increasing distance from the SMA may represent accepted upside expansion.

Status: `additional research justified`.

## 5. Temporal re-synchronization remains plausible

Full Slow-N tick coverage is unavailable.

Within the old/new event overlap, predefined Stoch-relative `0001`:

```text
NET/MOVE/CLV = old/opposite flow
RUN = newest flow aligned with M5 Stoch
```

predicts M5 Stoch direction at:

```text
N45 / 66.67%
```

The shifted-placebo `0001` is:

```text
N40 / 45.00%
```

Adding M1 Stoch alignment produced high percentages on N14/N10 nested samples, which are explicitly too small for authority.

Interpretation:

The prior working mechanism remains coherent enough to justify a full new tick extraction:

```text
older flow opposite
-> M1 oscillator re-aligns
-> last quote run flips
-> direction follows newly synchronized state
```

Status: `promising but unverified on full Slow-N`.

## 6. Important reproducibility finding

The exact old M1 confirmed-swing state cannot currently be regenerated from the retained implementation artifacts with sufficient parity.

This blocks any claim that old M1-structure conditioning has transferred.

The project should prefer:

- source-code-preserved state generators;
- parity tables before state reuse;
- explicit replacement definitions when old implementations cannot be recovered.

## 7. Research decision

Continue only:

1. full raw tick extraction + predefined temporal transition;
2. BB-B as context;
3. native Path Clearance reconstruction;
4. confirmed M1 structure recovery/redefinition.

Stop expanding generic technical-voter families.

Do not reopen exit/payoff research yet.
